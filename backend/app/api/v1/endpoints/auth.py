from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import timedelta

from app.infrastructure.db.database import get_db
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.repositories.license_repository import LicenseRepository
from app.infrastructure.security.auth import AuthService, validate_license_key
from app.infrastructure.security.dependencies import get_current_user
from app.api.v1.schemas.user import UserCreate, UserLogin, Token, TokenRefresh, User, UserChangePassword
from app.core.config import settings

router = APIRouter()
security = HTTPBearer()

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Registra um novo usuário com chave de licença.
    
    - **name**: Nome completo do usuário
    - **email**: Email único do usuário
    - **password**: Senha (mínimo 8 caracteres)
    - **license_key**: Chave de licença válida
    - **company**: Nome da empresa (opcional)
    - **phone**: Telefone (opcional)
    """
    user_repo = UserRepository(db)
    license_repo = LicenseRepository(db)
    
    # Verificar se email já existe
    if user_repo.get_by_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validar formato da chave de licença
    if not validate_license_key(user_data.license_key):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid license key format"
        )
    
    # Verificar se licença existe e está disponível
    if not license_repo.validate_license_key(user_data.license_key):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already used license key"
        )
    
    # Criar usuário
    user_dict = user_data.dict(exclude={'license_key'})
    user = user_repo.create(user_dict)
    
    # Ativar licença para o usuário
    license_repo.activate_license(user_data.license_key, user.id)
    
    # Gerar tokens
    access_token = AuthService.create_access_token(data={"sub": str(user.id)})
    refresh_token = AuthService.create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.post("/login", response_model=Token)
async def login(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Autentica um usuário existente.
    
    - **email**: Email do usuário
    - **password**: Senha do usuário
    """
    user_repo = UserRepository(db)
    
    # Autenticar usuário
    user = user_repo.authenticate(user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Verificar licença
    if not user.license or not user.license.is_valid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired license"
        )
    
    # Atualizar último login
    user_repo.update_last_login(user.id)
    
    # Gerar tokens
    access_token = AuthService.create_access_token(data={"sub": str(user.id)})
    refresh_token = AuthService.create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    db: Session = Depends(get_db)
):
    """
    Renova o token de acesso usando o refresh token.
    
    - **refresh_token**: Token de refresh válido
    """
    # Verificar refresh token
    payload = AuthService.verify_token(token_data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Verificar se usuário ainda existe e está ativo
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(int(user_id))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Gerar novos tokens
    access_token = AuthService.create_access_token(data={"sub": str(user.id)})
    new_refresh_token = AuthService.create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Obtém informações do usuário atual autenticado.
    """
    return current_user

@router.put("/change-password")
async def change_password(
    password_data: UserChangePassword,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Altera a senha do usuário atual.
    
    - **current_password**: Senha atual
    - **new_password**: Nova senha (mínimo 8 caracteres)
    """
    user_repo = UserRepository(db)
    
    # Verificar senha atual
    if not AuthService.verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Atualizar senha
    user_repo.update(current_user.id, {"password": password_data.new_password})
    
    return {"message": "Password updated successfully"}

@router.post("/logout")
async def logout():
    """
    Logout do usuário (invalidação do token deve ser feita no frontend).
    """
    return {"message": "Logged out successfully"}
