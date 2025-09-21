from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

@dataclass
class LLMResponse:
    """Resposta de um LLM"""
    content: str
    tokens_used: int
    cost: float
    model: str
    provider: str
    finish_reason: str
    metadata: Dict[str, Any] = None

@dataclass
class LLMMessage:
    """Mensagem para o LLM"""
    role: str  # system, user, assistant
    content: str

class ILLMService(ABC):
    """Interface para serviços de LLM"""
    
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> LLMResponse:
        """Gera uma resposta de chat"""
        pass
    
    @abstractmethod
    async def validate_api_key(self, api_key: str) -> bool:
        """Valida uma chave de API"""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Retorna lista de modelos disponíveis"""
        pass
    
    @abstractmethod
    def estimate_cost(self, tokens: int, model: str) -> float:
        """Estima o custo de uma requisição"""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Retorna o nome do provedor"""
        pass
