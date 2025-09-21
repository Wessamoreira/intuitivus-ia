from typing import Dict, List, Optional, Type
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.application.interfaces.llm_service import ILLMService, LLMResponse, LLMMessage
from app.infrastructure.services.openai_service import OpenAIService
from app.infrastructure.services.anthropic_service import AnthropicService
from app.infrastructure.services.google_service import GoogleService
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.security.auth import AuthService
from app.domain.models.api_key import APIKeyProvider, APIKeyStatus

logger = logging.getLogger(__name__)

class LLMRegistry:
    """Registry para gerenciar múltiplos provedores de LLM com fallback automático"""
    
    def __init__(self):
        # Mapeamento de provedores para suas classes de serviço
        self.provider_classes: Dict[str, Type[ILLMService]] = {
            "openai": OpenAIService,
            "anthropic": AnthropicService,
            "google": GoogleService,
        }
        
        # Cache de instâncias de serviços
        self.service_cache: Dict[str, ILLMService] = {}
    
    def _get_service_instance(self, provider: str, api_key: str) -> ILLMService:
        """Obtém ou cria uma instância do serviço"""
        cache_key = f"{provider}:{api_key[:10]}"  # Usar apenas parte da chave para cache
        
        if cache_key not in self.service_cache:
            if provider not in self.provider_classes:
                raise ValueError(f"Unsupported provider: {provider}")
            
            service_class = self.provider_classes[provider]
            self.service_cache[cache_key] = service_class(api_key)
        
        return self.service_cache[cache_key]
    
    async def chat_completion(
        self,
        user_id: int,
        messages: List[LLMMessage],
        preferred_provider: str,
        preferred_model: str,
        db: Session,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> LLMResponse:
        """
        Executa chat completion com fallback automático.
        
        1. Tenta usar o provedor preferido
        2. Se falhar, tenta outros provedores por ordem de prioridade
        3. Atualiza status das chaves conforme necessário
        """
        user_repo = UserRepository(db)
        user = user_repo.get_by_id(user_id)
        
        if not user:
            raise ValueError("User not found")
        
        # Obter chaves do usuário ordenadas por prioridade
        user_api_keys = sorted(
            [key for key in user.api_keys if key.status == APIKeyStatus.ACTIVE],
            key=lambda x: x.priority
        )
        
        # Filtrar chaves do provedor preferido primeiro
        preferred_keys = [key for key in user_api_keys if key.provider.value == preferred_provider]
        other_keys = [key for key in user_api_keys if key.provider.value != preferred_provider]
        
        # Tentar chaves do provedor preferido primeiro
        for api_key_record in preferred_keys:
            try:
                decrypted_key = AuthService.decrypt_api_key(api_key_record.encrypted_key)
                service = self._get_service_instance(preferred_provider, decrypted_key)
                
                # Verificar se o modelo está disponível para este provedor
                available_models = service.get_available_models()
                model_to_use = preferred_model if preferred_model in available_models else available_models[0]
                
                response = await service.chat_completion(
                    messages=messages,
                    model=model_to_use,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
                
                # Atualizar última utilização
                api_key_record.last_used = datetime.utcnow()
                db.commit()
                
                logger.info(f"Successfully used {preferred_provider} with model {model_to_use}")
                return response
                
            except Exception as e:
                logger.warning(f"Failed to use {preferred_provider} key {api_key_record.id}: {e}")
                
                # Se erro de quota, marcar chave como esgotada
                if "quota" in str(e).lower() or "limit" in str(e).lower():
                    api_key_record.status = APIKeyStatus.QUOTA_EXCEEDED
                    db.commit()
                    logger.info(f"Marked key {api_key_record.id} as quota exceeded")
                
                continue
        
        # Se falhou com provedor preferido, tentar outros provedores
        logger.info(f"Fallback: trying other providers after {preferred_provider} failed")
        
        for api_key_record in other_keys:
            try:
                provider = api_key_record.provider.value
                decrypted_key = AuthService.decrypt_api_key(api_key_record.encrypted_key)
                service = self._get_service_instance(provider, decrypted_key)
                
                # Usar primeiro modelo disponível do provedor
                available_models = service.get_available_models()
                model_to_use = available_models[0]
                
                response = await service.chat_completion(
                    messages=messages,
                    model=model_to_use,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
                
                # Atualizar última utilização
                api_key_record.last_used = datetime.utcnow()
                db.commit()
                
                logger.info(f"Fallback successful: used {provider} with model {model_to_use}")
                return response
                
            except Exception as e:
                logger.warning(f"Fallback failed for {provider} key {api_key_record.id}: {e}")
                
                # Se erro de quota, marcar chave como esgotada
                if "quota" in str(e).lower() or "limit" in str(e).lower():
                    api_key_record.status = APIKeyStatus.QUOTA_EXCEEDED
                    db.commit()
                
                continue
        
        # Se chegou aqui, todas as chaves falharam
        raise Exception("All available LLM providers failed. Please check your API keys and quotas.")
    
    async def validate_api_key(self, provider: str, api_key: str) -> bool:
        """Valida uma chave de API para um provedor específico"""
        try:
            service = self._get_service_instance(provider, api_key)
            return await service.validate_api_key(api_key)
        except Exception as e:
            logger.error(f"Error validating {provider} API key: {e}")
            return False
    
    def get_available_providers(self) -> List[str]:
        """Retorna lista de provedores disponíveis"""
        return list(self.provider_classes.keys())
    
    def get_available_models(self, provider: str) -> List[str]:
        """Retorna modelos disponíveis para um provedor"""
        if provider not in self.provider_classes:
            return []
        
        # Criar instância temporária para obter modelos
        try:
            service_class = self.provider_classes[provider]
            temp_service = service_class("dummy_key")  # Chave temporária
            return temp_service.get_available_models()
        except Exception:
            return []
    
    def estimate_cost(self, provider: str, tokens: int, model: str) -> float:
        """Estima custo para um provedor e modelo específicos"""
        if provider not in self.provider_classes:
            return 0.0
        
        try:
            service_class = self.provider_classes[provider]
            temp_service = service_class("dummy_key")
            return temp_service.estimate_cost(tokens, model)
        except Exception:
            return 0.0

# Instância global do registry
llm_registry = LLMRegistry()
