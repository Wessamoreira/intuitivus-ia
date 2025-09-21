import google.generativeai as genai
from typing import List, Dict, Any
import logging

from app.application.interfaces.llm_service import ILLMService, LLMResponse, LLMMessage

logger = logging.getLogger(__name__)

class GoogleService(ILLMService):
    """Implementação do serviço Google (Gemini)"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=api_key)
        
        # Preços por 1K tokens em USD (Gemini tem preço único para input/output)
        self.pricing = {
            "gemini-pro": {"input": 0.0005, "output": 0.0015},
            "gemini-pro-vision": {"input": 0.0005, "output": 0.0015},
            "gemini-1.5-pro": {"input": 0.0035, "output": 0.0105},
            "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
        }
    
    async def chat_completion(
        self,
        messages: List[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> LLMResponse:
        """Gera uma resposta de chat usando Google Gemini"""
        try:
            # Configurar modelo
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                **kwargs
            )
            
            model_instance = genai.GenerativeModel(
                model_name=model,
                generation_config=generation_config
            )
            
            # Converter mensagens para formato Gemini
            chat_history = []
            system_instruction = ""
            
            for msg in messages[:-1]:  # Todas exceto a última
                if msg.role == "system":
                    system_instruction = msg.content
                elif msg.role == "user":
                    chat_history.append({"role": "user", "parts": [msg.content]})
                elif msg.role == "assistant":
                    chat_history.append({"role": "model", "parts": [msg.content]})
            
            # Última mensagem (atual)
            last_message = messages[-1]
            
            # Iniciar chat com histórico
            if chat_history:
                chat = model_instance.start_chat(history=chat_history)
                response = await chat.send_message_async(last_message.content)
            else:
                # Se não há histórico, usar generate_content
                prompt = f"{system_instruction}\n\n{last_message.content}" if system_instruction else last_message.content
                response = await model_instance.generate_content_async(prompt)
            
            # Extrair dados da resposta
            content = response.text
            finish_reason = "stop"  # Gemini não fornece finish_reason detalhado
            
            # Estimar tokens (Gemini não fornece contagem exata)
            estimated_tokens = self._estimate_tokens(content, last_message.content)
            cost = self.estimate_cost(estimated_tokens, model)
            
            return LLMResponse(
                content=content,
                tokens_used=estimated_tokens,
                cost=cost,
                model=model,
                provider="google",
                finish_reason=finish_reason,
                metadata={
                    "estimated_tokens": True,
                    "safety_ratings": getattr(response, 'safety_ratings', [])
                }
            )
            
        except Exception as e:
            logger.error(f"Google API error: {e}")
            raise Exception(f"Google API error: {str(e)}")
    
    def _estimate_tokens(self, response_text: str, input_text: str) -> int:
        """Estima tokens baseado no comprimento do texto"""
        # Estimativa aproximada: 1 token ≈ 4 caracteres
        input_tokens = len(input_text) // 4
        output_tokens = len(response_text) // 4
        return input_tokens + output_tokens
    
    async def validate_api_key(self, api_key: str) -> bool:
        """Valida uma chave de API Google"""
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-pro')
            response = await model.generate_content_async("Hi")
            return True
        except Exception as e:
            logger.warning(f"Invalid Google API key: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Retorna lista de modelos Google disponíveis"""
        return [
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-pro",
            "gemini-pro-vision"
        ]
    
    def estimate_cost(self, tokens: int, model: str) -> float:
        """Estima o custo de uma requisição Google"""
        if model not in self.pricing:
            # Usar preço padrão do Gemini Pro se modelo não encontrado
            model = "gemini-pro"
        
        # Assumir 75% input tokens, 25% output tokens
        input_tokens = int(tokens * 0.75)
        output_tokens = int(tokens * 0.25)
        
        pricing = self.pricing[model]
        cost = (input_tokens / 1000 * pricing["input"]) + (output_tokens / 1000 * pricing["output"])
        
        return round(cost, 6)
    
    def get_provider_name(self) -> str:
        """Retorna o nome do provedor"""
        return "google"
