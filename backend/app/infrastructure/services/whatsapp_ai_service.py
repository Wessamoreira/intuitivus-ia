import asyncio
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from app.application.interfaces.whatsapp_service import WhatsAppMessage, MessageType
from app.application.interfaces.llm_service import LLMMessage
from app.infrastructure.services.meta_whatsapp_service import meta_whatsapp_service
from app.infrastructure.services.llm_registry import llm_registry
from app.infrastructure.repositories.conversation_repository import ConversationRepository
from app.infrastructure.repositories.agent_repository import AgentRepository
from app.infrastructure.repositories.user_repository import UserRepository
from app.domain.models.conversation import ConversationStatus, ConversationChannel, MessageRole
from app.domain.models.agent import AgentCategory, AgentStatus

logger = logging.getLogger(__name__)

class WhatsAppAIService:
    """Serviço que integra WhatsApp com agentes de IA"""
    
    def __init__(self):
        self.processing_messages = set()  # Para evitar processamento duplicado
    
    async def process_incoming_message(
        self,
        whatsapp_message: WhatsAppMessage,
        user_id: int,
        db: Session
    ) -> Optional[WhatsAppMessage]:
        """Processa mensagem recebida e gera resposta com IA"""
        
        # Evitar processamento duplicado
        if whatsapp_message.id in self.processing_messages:
            logger.info(f"Message {whatsapp_message.id} already being processed")
            return None
        
        self.processing_messages.add(whatsapp_message.id)
        
        try:
            conversation_repo = ConversationRepository(db)
            agent_repo = AgentRepository(db)
            
            # Buscar ou criar conversa
            conversation = conversation_repo.get_conversation_by_phone(
                user_id=user_id,
                phone_number=whatsapp_message.from_number
            )
            
            if not conversation:
                # Criar nova conversa
                conversation_data = {
                    "customer_phone": whatsapp_message.from_number,
                    "customer_name": whatsapp_message.metadata.get("contact_name") if whatsapp_message.metadata else None,
                    "channel": ConversationChannel.WHATSAPP,
                    "status": ConversationStatus.ACTIVE,
                    "external_id": whatsapp_message.from_number,
                    "user_id": user_id,
                    "is_ai_handled": True,
                    "metadata": whatsapp_message.metadata or {}
                }
                conversation = conversation_repo.create_conversation(conversation_data)
                logger.info(f"Created new conversation {conversation.id} for {whatsapp_message.from_number}")
            
            # Adicionar mensagem do cliente
            customer_message = conversation_repo.add_message({
                "conversation_id": conversation.id,
                "content": whatsapp_message.content,
                "role": MessageRole.CUSTOMER,
                "message_type": whatsapp_message.message_type.value,
                "external_id": whatsapp_message.id,
                "metadata": whatsapp_message.metadata or {}
            })
            
            # Verificar se conversa requer intervenção humana
            if conversation.requires_human or conversation.status == ConversationStatus.ESCALATED:
                logger.info(f"Conversation {conversation.id} requires human intervention")
                return None
            
            # Buscar agente de atendimento adequado
            agent = await self._find_suitable_agent(user_id, conversation, agent_repo)
            
            if not agent:
                logger.warning(f"No suitable agent found for user {user_id}")
                # Marcar como pendente para intervenção humana
                conversation_repo.update_conversation(conversation.id, {
                    "status": ConversationStatus.PENDING,
                    "requires_human": True
                })
                return None
            
            # Atribuir agente à conversa se não estiver atribuído
            if not conversation.agent_id:
                conversation_repo.assign_agent(conversation.id, agent.id)
                conversation.agent_id = agent.id
            
            # Gerar resposta com IA
            ai_response = await self._generate_ai_response(
                conversation=conversation,
                customer_message=customer_message.content,
                agent=agent,
                user_id=user_id,
                db=db
            )
            
            if ai_response:
                # Salvar resposta da IA no banco
                conversation_repo.add_message({
                    "conversation_id": conversation.id,
                    "content": ai_response,
                    "role": MessageRole.AGENT,
                    "message_type": "text"
                })
                
                # Enviar resposta via WhatsApp
                response_message = await meta_whatsapp_service.send_message(
                    to_number=whatsapp_message.from_number,
                    message=ai_response,
                    message_type=MessageType.TEXT
                )
                
                logger.info(f"AI response sent to {whatsapp_message.from_number}")
                return response_message
            
            return None
            
        except Exception as e:
            logger.error(f"Error processing WhatsApp message: {e}")
            return None
        
        finally:
            # Remover da lista de processamento
            self.processing_messages.discard(whatsapp_message.id)
    
    async def _find_suitable_agent(
        self,
        user_id: int,
        conversation,
        agent_repo: AgentRepository
    ) -> Optional:
        """Encontra o agente mais adequado para a conversa"""
        
        # Buscar agentes de atendimento disponíveis
        available_agents = agent_repo.get_available_agents(user_id)
        
        # Filtrar por categoria de suporte/atendimento
        support_agents = [
            agent for agent in available_agents 
            if agent.category in [AgentCategory.SUPPORT, AgentCategory.GENERAL]
        ]
        
        if not support_agents:
            # Se não há agentes de suporte, usar qualquer agente disponível
            support_agents = available_agents
        
        if not support_agents:
            return None
        
        # Se a conversa já tem um agente atribuído, verificar se ainda está disponível
        if conversation.agent_id:
            current_agent = agent_repo.get_by_id(conversation.agent_id)
            if current_agent and current_agent.is_available:
                return current_agent
        
        # Escolher agente com menor carga de trabalho (menos tarefas ativas)
        best_agent = min(support_agents, key=lambda a: a.tasks_completed + a.tasks_failed)
        
        return best_agent
    
    async def _generate_ai_response(
        self,
        conversation,
        customer_message: str,
        agent,
        user_id: int,
        db: Session
    ) -> Optional[str]:
        """Gera resposta usando agente de IA"""
        
        try:
            conversation_repo = ConversationRepository(db)
            
            # Obter histórico de mensagens recentes
            recent_messages = conversation_repo.get_recent_messages(
                conversation.id, 
                limit=10
            )
            
            # Construir contexto da conversa
            context_messages = []
            
            # System prompt do agente
            system_prompt = self._build_system_prompt(agent, conversation)
            context_messages.append(LLMMessage(role="system", content=system_prompt))
            
            # Adicionar histórico de mensagens
            for msg in reversed(recent_messages[:-1]):  # Excluir a última (atual)
                role = "user" if msg.role == MessageRole.CUSTOMER else "assistant"
                context_messages.append(LLMMessage(role=role, content=msg.content))
            
            # Adicionar mensagem atual do cliente
            context_messages.append(LLMMessage(role="user", content=customer_message))
            
            # Gerar resposta usando o registry multi-LLM
            response = await llm_registry.chat_completion(
                user_id=user_id,
                messages=context_messages,
                preferred_provider=agent.llm_provider,
                preferred_model=agent.llm_model,
                db=db,
                temperature=agent.settings.get("temperature", 0.7) if agent.settings else 0.7,
                max_tokens=agent.settings.get("max_tokens", 1000) if agent.settings else 1000
            )
            
            # Atualizar métricas do agente
            agent_repo = AgentRepository(db)
            agent_repo.update_metrics(
                agent_id=agent.id,
                task_completed=True,
                tokens_used=response.tokens_used,
                cost=response.cost
            )
            
            return response.content
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            
            # Atualizar métricas de falha
            try:
                agent_repo = AgentRepository(db)
                agent_repo.update_metrics(
                    agent_id=agent.id,
                    task_completed=False,
                    tokens_used=0,
                    cost=0.0
                )
            except:
                pass
            
            return None
    
    def _build_system_prompt(self, agent, conversation) -> str:
        """Constrói prompt do sistema para o agente"""
        
        base_prompt = agent.system_prompt
        
        # Adicionar contexto específico do WhatsApp
        whatsapp_context = f"""

CONTEXTO DO ATENDIMENTO:
- Você está atendendo via WhatsApp
- Cliente: {conversation.customer_name or 'Cliente'}
- Telefone: {conversation.customer_phone}
- Canal: WhatsApp Business

DIRETRIZES ESPECÍFICAS:
1. Seja cordial, profissional e empático
2. Responda de forma concisa (máximo 2-3 parágrafos)
3. Use emojis moderadamente quando apropriado
4. Se não souber algo, seja honesto e ofereça alternativas
5. Sempre pergunte se pode ajudar em mais alguma coisa
6. Se o problema for complexo, sugira escalação para humano

INSTRUÇÕES ADICIONAIS:
{agent.instructions or "Foque em resolver a dúvida do cliente de forma eficiente."}
"""
        
        return base_prompt + whatsapp_context
    
    async def send_proactive_message(
        self,
        user_id: int,
        phone_number: str,
        message: str,
        db: Session
    ) -> Optional[WhatsAppMessage]:
        """Envia mensagem proativa para um cliente"""
        
        try:
            conversation_repo = ConversationRepository(db)
            
            # Buscar conversa existente
            conversation = conversation_repo.get_conversation_by_phone(user_id, phone_number)
            
            if not conversation:
                # Criar nova conversa
                conversation_data = {
                    "customer_phone": phone_number,
                    "channel": ConversationChannel.WHATSAPP,
                    "status": ConversationStatus.ACTIVE,
                    "external_id": phone_number,
                    "user_id": user_id,
                    "is_ai_handled": True
                }
                conversation = conversation_repo.create_conversation(conversation_data)
            
            # Enviar mensagem
            whatsapp_response = await meta_whatsapp_service.send_message(
                to_number=phone_number,
                message=message,
                message_type=MessageType.TEXT
            )
            
            # Salvar no banco
            conversation_repo.add_message({
                "conversation_id": conversation.id,
                "content": message,
                "role": MessageRole.AGENT,
                "message_type": "text",
                "external_id": whatsapp_response.id
            })
            
            logger.info(f"Proactive message sent to {phone_number}")
            return whatsapp_response
            
        except Exception as e:
            logger.error(f"Error sending proactive message: {e}")
            return None
    
    async def escalate_to_human(
        self,
        conversation_id: int,
        reason: str,
        db: Session
    ) -> bool:
        """Escala conversa para atendimento humano"""
        
        try:
            conversation_repo = ConversationRepository(db)
            
            # Marcar como escalada
            conversation_repo.mark_as_escalated(conversation_id)
            
            # Adicionar mensagem de sistema
            conversation_repo.add_message({
                "conversation_id": conversation_id,
                "content": f"Conversa escalada para atendimento humano. Motivo: {reason}",
                "role": MessageRole.SYSTEM,
                "message_type": "text"
            })
            
            logger.info(f"Conversation {conversation_id} escalated to human: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Error escalating conversation: {e}")
            return False

# Instância global do serviço
whatsapp_ai_service = WhatsAppAIService()
