from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.infrastructure.db.database import get_db
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.security.dependencies import get_current_active_user
from app.infrastructure.security.auth import AuthService
from app.infrastructure.services.llm_registry import llm_registry
from app.api.v1.schemas.user import User
from app.api.v1.schemas.api_key import (
    APIKeyCreate, APIKeyUpdate, APIKey, APIKeyWithModels, 
    APIKeyTest, APIKeyStats, APIKeyProviderEnum
)
from app.domain.models.api_key import APIKey as APIKeyModel, APIKeyProvider, APIKeyStatus

router = APIRouter()

@router.post("/", response_model=APIKey, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    api_key_data: APIKeyCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Adiciona uma nova chave de API.
    
    - **name**: Nome amigável para a chave
    - **provider**: Provedor (openai, anthropic, google, etc.)
    - **api_key**: A chave de API real
    - **priority**: Prioridade de uso (1 = maior prioridade)
    - **monthly_limit**: Limite mensal em dólares (opcional)
    """
    # Validar chave de API
    is_valid = await llm_registry.validate_api_key(
        api_key_data.provider.value, 
        api_key_data.api_key
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid API key for the specified provider"
        )
    
    # Criptografar chave
    encrypted_key = AuthService.encrypt_api_key(api_key_data.api_key)
    
    # Criar registro no banco
    api_key_record = APIKeyModel(
        name=api_key_data.name,
        provider=APIKeyProvider(api_key_data.provider.value),
        encrypted_key=encrypted_key,
        priority=api_key_data.priority,
        monthly_limit=api_key_data.monthly_limit,
        user_id=current_user.id,
        status=APIKeyStatus.ACTIVE
    )
    
    db.add(api_key_record)
    db.commit()
    db.refresh(api_key_record)
    
    # Retornar sem a chave real
    return _format_api_key_response(api_key_record, api_key_data.api_key)

@router.get("/", response_model=List[APIKeyWithModels])
async def list_api_keys(
    provider: Optional[APIKeyProviderEnum] = Query(None, description="Filtrar por provedor"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Lista as chaves de API do usuário.
    
    - **provider**: Filtrar por provedor específico (opcional)
    """
    query = db.query(APIKeyModel).filter(APIKeyModel.user_id == current_user.id)
    
    if provider:
        query = query.filter(APIKeyModel.provider == APIKeyProvider(provider.value))
    
    api_keys = query.order_by(APIKeyModel.priority).all()
    
    # Formatar resposta com modelos disponíveis
    result = []
    for api_key in api_keys:
        formatted_key = _format_api_key_response(api_key)
        
        # Adicionar modelos disponíveis
        available_models = llm_registry.get_available_models(api_key.provider.value)
        formatted_key["available_models"] = available_models
        
        result.append(APIKeyWithModels(**formatted_key))
    
    return result

@router.get("/stats", response_model=APIKeyStats)
async def get_api_key_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Obtém estatísticas das chaves de API do usuário.
    """
    api_keys = db.query(APIKeyModel).filter(APIKeyModel.user_id == current_user.id).all()
    
    total_keys = len(api_keys)
    active_keys = len([k for k in api_keys if k.status == APIKeyStatus.ACTIVE])
    inactive_keys = len([k for k in api_keys if k.status == APIKeyStatus.INACTIVE])
    quota_exceeded = len([k for k in api_keys if k.status == APIKeyStatus.QUOTA_EXCEEDED])
    
    # Calcular uso total
    total_usage = sum(float(k.current_usage) for k in api_keys)
    
    # Contar por provedor
    providers_count = {}
    for key in api_keys:
        provider = key.provider.value
        providers_count[provider] = providers_count.get(provider, 0) + 1
    
    return APIKeyStats(
        total_keys=total_keys,
        active_keys=active_keys,
        inactive_keys=inactive_keys,
        quota_exceeded_keys=quota_exceeded,
        total_usage_usd=total_usage,
        providers_count=providers_count
    )

@router.get("/{key_id}", response_model=APIKey)
async def get_api_key(
    key_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Obtém detalhes de uma chave de API específica.
    """
    api_key = db.query(APIKeyModel).filter(
        APIKeyModel.id == key_id,
        APIKeyModel.user_id == current_user.id
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    return _format_api_key_response(api_key)

@router.put("/{key_id}", response_model=APIKey)
async def update_api_key(
    key_id: int,
    api_key_data: APIKeyUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Atualiza uma chave de API existente.
    """
    api_key = db.query(APIKeyModel).filter(
        APIKeyModel.id == key_id,
        APIKeyModel.user_id == current_user.id
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    # Atualizar campos fornecidos
    update_data = api_key_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "status" and value:
            setattr(api_key, field, APIKeyStatus(value.value))
        else:
            setattr(api_key, field, value)
    
    db.commit()
    db.refresh(api_key)
    
    return _format_api_key_response(api_key)

@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Deleta uma chave de API.
    """
    api_key = db.query(APIKeyModel).filter(
        APIKeyModel.id == key_id,
        APIKeyModel.user_id == current_user.id
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    db.delete(api_key)
    db.commit()

@router.post("/test", response_model=dict)
async def test_api_key(
    test_data: APIKeyTest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Testa uma chave de API antes de salvá-la.
    
    - **provider**: Provedor da chave
    - **api_key**: Chave para testar
    """
    is_valid = await llm_registry.validate_api_key(
        test_data.provider.value,
        test_data.api_key
    )
    
    if is_valid:
        # Obter modelos disponíveis
        available_models = llm_registry.get_available_models(test_data.provider.value)
        
        return {
            "valid": True,
            "provider": test_data.provider.value,
            "available_models": available_models,
            "message": "API key is valid and working"
        }
    else:
        return {
            "valid": False,
            "provider": test_data.provider.value,
            "message": "API key is invalid or not working"
        }

@router.get("/providers/available", response_model=dict)
async def get_available_providers():
    """
    Lista todos os provedores de LLM disponíveis.
    """
    providers = llm_registry.get_available_providers()
    
    provider_info = {}
    for provider in providers:
        models = llm_registry.get_available_models(provider)
        provider_info[provider] = {
            "name": provider.title(),
            "models": models,
            "supported": True
        }
    
    return {
        "providers": provider_info,
        "total_providers": len(providers)
    }

def _format_api_key_response(api_key: APIKeyModel, original_key: str = None) -> dict:
    """Formata resposta da chave de API ocultando a chave real"""
    
    # Criar preview da chave (primeiros 4 + últimos 4 caracteres)
    if original_key:
        key_preview = f"{original_key[:4]}...{original_key[-4:]}"
    else:
        # Se não temos a chave original, usar placeholder
        key_preview = "****...****"
    
    return {
        "id": api_key.id,
        "name": api_key.name,
        "provider": api_key.provider.value,
        "status": api_key.status.value,
        "priority": api_key.priority,
        "monthly_limit": api_key.monthly_limit,
        "current_usage": api_key.current_usage,
        "created_at": api_key.created_at,
        "last_used": api_key.last_used,
        "last_validated": api_key.last_validated,
        "key_preview": key_preview
    }
