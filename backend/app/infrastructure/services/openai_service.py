import openai
from typing import List, Dict, Any
import logging

from app.application.interfaces.llm_service import ILLMService, LLMResponse, LLMMessage

logger = logging.getLogger(__name__)

class OpenAIService(ILLMService):
    """Implementação do serviço OpenAI"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = openai.AsyncOpenAI(api_key=api_key)
        
        # Preços por 1K tokens (input/output) em USD
        self.pricing = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
            "gpt-3.5-turbo-16k": {"input": 0.003, "output": 0.004},
        }
    
    async def chat_completion(
        self,
        messages: List[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> LLMResponse:
        """Gera uma resposta de chat usando OpenAI"""
        try:
            # Converter mensagens para formato OpenAI
            openai_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
            
            # Fazer requisição
            response = await self.client.chat.completions.create(
                model=model,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            # Extrair dados da resposta
            choice = response.choices[0]
            content = choice.message.content
            finish_reason = choice.finish_reason
            
            # Calcular tokens e custo
            tokens_used = response.usage.total_tokens
            cost = self.estimate_cost(tokens_used, model)
            
            return LLMResponse(
                content=content,
                tokens_used=tokens_used,
                cost=cost,
                model=model,
                provider="openai",
                finish_reason=finish_reason,
                metadata={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "response_id": response.id
                }
            )
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise Exception(f"OpenAI API error: {str(e)}")
    
    async def validate_api_key(self, api_key: str) -> bool:
        """Valida uma chave de API OpenAI"""
        try:
            client = openai.AsyncOpenAI(api_key=api_key)
            # Fazer uma requisição simples para testar
            await client.models.list()
            return True
        except Exception as e:
            logger.warning(f"Invalid OpenAI API key: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Retorna lista de modelos OpenAI disponíveis"""
        return [
            "gpt-4",
            "gpt-4-turbo",
            "gpt-4-turbo-preview",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k"
        ]
    
    def estimate_cost(self, tokens: int, model: str) -> float:
        """Estima o custo de uma requisição OpenAI"""
        if model not in self.pricing:
            # Usar preço padrão do GPT-4 se modelo não encontrado
            model = "gpt-4"
        
        # Assumir 75% input tokens, 25% output tokens
        input_tokens = int(tokens * 0.75)
        output_tokens = int(tokens * 0.25)
        
        pricing = self.pricing[model]
        cost = (input_tokens / 1000 * pricing["input"]) + (output_tokens / 1000 * pricing["output"])
        
        return round(cost, 6)
    
    def get_provider_name(self) -> str:
        """Retorna o nome do provedor"""
        return "openai"
