import anthropic
from typing import List, Dict, Any
import logging

from app.application.interfaces.llm_service import ILLMService, LLMResponse, LLMMessage

logger = logging.getLogger(__name__)

class AnthropicService(ILLMService):
    """Implementação do serviço Anthropic (Claude)"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        
        # Preços por 1K tokens (input/output) em USD
        self.pricing = {
            "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
            "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
            "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
        }
    
    async def chat_completion(
        self,
        messages: List[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> LLMResponse:
        """Gera uma resposta de chat usando Anthropic"""
        try:
            # Separar system message das outras mensagens
            system_message = ""
            chat_messages = []
            
            for msg in messages:
                if msg.role == "system":
                    system_message = msg.content
                else:
                    chat_messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
            
            # Fazer requisição
            response = await self.client.messages.create(
                model=model,
                system=system_message if system_message else None,
                messages=chat_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            # Extrair dados da resposta
            content = response.content[0].text
            finish_reason = response.stop_reason
            
            # Calcular tokens e custo
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            total_tokens = input_tokens + output_tokens
            
            cost = self._calculate_cost(input_tokens, output_tokens, model)
            
            return LLMResponse(
                content=content,
                tokens_used=total_tokens,
                cost=cost,
                model=model,
                provider="anthropic",
                finish_reason=finish_reason,
                metadata={
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "response_id": response.id
                }
            )
            
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise Exception(f"Anthropic API error: {str(e)}")
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        """Calcula o custo exato baseado em tokens de input e output"""
        if model not in self.pricing:
            # Usar preço padrão do Claude 3 Sonnet se modelo não encontrado
            model = "claude-3-sonnet-20240229"
        
        pricing = self.pricing[model]
        cost = (input_tokens / 1000 * pricing["input"]) + (output_tokens / 1000 * pricing["output"])
        
        return round(cost, 6)
    
    async def validate_api_key(self, api_key: str) -> bool:
        """Valida uma chave de API Anthropic"""
        try:
            client = anthropic.AsyncAnthropic(api_key=api_key)
            # Fazer uma requisição simples para testar
            await client.messages.create(
                model="claude-3-haiku-20240307",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=10
            )
            return True
        except Exception as e:
            logger.warning(f"Invalid Anthropic API key: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Retorna lista de modelos Anthropic disponíveis"""
        return [
            "claude-3-5-sonnet-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307"
        ]
    
    def estimate_cost(self, tokens: int, model: str) -> float:
        """Estima o custo de uma requisição Anthropic"""
        # Assumir 75% input tokens, 25% output tokens
        input_tokens = int(tokens * 0.75)
        output_tokens = int(tokens * 0.25)
        
        return self._calculate_cost(input_tokens, output_tokens, model)
    
    def get_provider_name(self) -> str:
        """Retorna o nome do provedor"""
        return "anthropic"
