from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from datetime import datetime, timedelta

from app.domain.models.conversation import Conversation, Message, ConversationStatus, ConversationChannel, MessageRole
from app.domain.models.user import User

class ConversationRepository:
    """Repository para operações com conversas"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_conversation(self, conversation_data: dict) -> Conversation:
        """Cria uma nova conversa"""
        conversation = Conversation(**conversation_data)
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation
    
    def get_conversation_by_id(self, conversation_id: int) -> Optional[Conversation]:
        """Busca conversa por ID"""
        return self.db.query(Conversation).filter(Conversation.id == conversation_id).first()
    
    def get_conversation_by_phone(self, user_id: int, phone_number: str) -> Optional[Conversation]:
        """Busca conversa por número de telefone"""
        return self.db.query(Conversation).filter(
            and_(
                Conversation.user_id == user_id,
                Conversation.customer_phone == phone_number
            )
        ).first()
    
    def get_conversation_by_external_id(self, external_id: str, channel: ConversationChannel) -> Optional[Conversation]:
        """Busca conversa por ID externo"""
        return self.db.query(Conversation).filter(
            and_(
                Conversation.external_id == external_id,
                Conversation.channel == channel
            )
        ).first()
    
    def get_user_conversations(
        self, 
        user_id: int, 
        status: Optional[ConversationStatus] = None,
        channel: Optional[ConversationChannel] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Conversation]:
        """Lista conversas de um usuário"""
        query = self.db.query(Conversation).filter(Conversation.user_id == user_id)
        
        if status:
            query = query.filter(Conversation.status == status)
        
        if channel:
            query = query.filter(Conversation.channel == channel)
        
        return query.order_by(desc(Conversation.last_message_at)).offset(skip).limit(limit).all()
    
    def get_active_conversations(self, user_id: int) -> List[Conversation]:
        """Lista conversas ativas de um usuário"""
        return self.get_user_conversations(
            user_id=user_id,
            status=ConversationStatus.ACTIVE
        )
    
    def get_pending_conversations(self, user_id: int) -> List[Conversation]:
        """Lista conversas pendentes de um usuário"""
        return self.get_user_conversations(
            user_id=user_id,
            status=ConversationStatus.PENDING
        )
    
    def update_conversation(self, conversation_id: int, conversation_data: dict) -> Optional[Conversation]:
        """Atualiza uma conversa"""
        conversation = self.get_conversation_by_id(conversation_id)
        if not conversation:
            return None
        
        for field, value in conversation_data.items():
            setattr(conversation, field, value)
        
        self.db.commit()
        self.db.refresh(conversation)
        return conversation
    
    def update_last_message_time(self, conversation_id: int) -> Optional[Conversation]:
        """Atualiza timestamp da última mensagem"""
        return self.update_conversation(conversation_id, {
            "last_message_at": datetime.utcnow()
        })
    
    def mark_as_resolved(self, conversation_id: int) -> Optional[Conversation]:
        """Marca conversa como resolvida"""
        return self.update_conversation(conversation_id, {
            "status": ConversationStatus.RESOLVED
        })
    
    def mark_as_escalated(self, conversation_id: int) -> Optional[Conversation]:
        """Marca conversa como escalada para humano"""
        return self.update_conversation(conversation_id, {
            "status": ConversationStatus.ESCALATED,
            "requires_human": True
        })
    
    def assign_agent(self, conversation_id: int, agent_id: int) -> Optional[Conversation]:
        """Atribui um agente à conversa"""
        return self.update_conversation(conversation_id, {
            "agent_id": agent_id,
            "is_ai_handled": True
        })
    
    def add_message(self, message_data: dict) -> Message:
        """Adiciona uma mensagem à conversa"""
        message = Message(**message_data)
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        
        # Atualizar timestamp da conversa
        self.update_last_message_time(message.conversation_id)
        
        return message
    
    def get_conversation_messages(
        self, 
        conversation_id: int, 
        skip: int = 0, 
        limit: int = 50
    ) -> List[Message]:
        """Obtém mensagens de uma conversa"""
        return self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at).offset(skip).limit(limit).all()
    
    def get_recent_messages(
        self, 
        conversation_id: int, 
        limit: int = 10
    ) -> List[Message]:
        """Obtém mensagens recentes de uma conversa"""
        return self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(desc(Message.created_at)).limit(limit).all()
    
    def get_message_by_external_id(self, external_id: str) -> Optional[Message]:
        """Busca mensagem por ID externo"""
        return self.db.query(Message).filter(Message.external_id == external_id).first()
    
    def count_unread_messages(self, conversation_id: int) -> int:
        """Conta mensagens não lidas de clientes"""
        # Considera não lidas as mensagens de clientes após a última mensagem do agente
        last_agent_message = self.db.query(Message).filter(
            and_(
                Message.conversation_id == conversation_id,
                Message.role == MessageRole.AGENT
            )
        ).order_by(desc(Message.created_at)).first()
        
        if last_agent_message:
            return self.db.query(Message).filter(
                and_(
                    Message.conversation_id == conversation_id,
                    Message.role == MessageRole.CUSTOMER,
                    Message.created_at > last_agent_message.created_at
                )
            ).count()
        else:
            # Se não há mensagens do agente, contar todas as mensagens do cliente
            return self.db.query(Message).filter(
                and_(
                    Message.conversation_id == conversation_id,
                    Message.role == MessageRole.CUSTOMER
                )
            ).count()
    
    def get_conversation_stats(self, user_id: int) -> dict:
        """Obtém estatísticas das conversas do usuário"""
        conversations = self.get_user_conversations(user_id)
        
        total_conversations = len(conversations)
        active_conversations = len([c for c in conversations if c.status == ConversationStatus.ACTIVE])
        pending_conversations = len([c for c in conversations if c.status == ConversationStatus.PENDING])
        resolved_conversations = len([c for c in conversations if c.status == ConversationStatus.RESOLVED])
        
        # Conversas por canal
        whatsapp_conversations = len([c for c in conversations if c.channel == ConversationChannel.WHATSAPP])
        
        # Conversas com IA vs humano
        ai_handled = len([c for c in conversations if c.is_ai_handled])
        human_required = len([c for c in conversations if c.requires_human])
        
        return {
            "total_conversations": total_conversations,
            "active_conversations": active_conversations,
            "pending_conversations": pending_conversations,
            "resolved_conversations": resolved_conversations,
            "whatsapp_conversations": whatsapp_conversations,
            "ai_handled_conversations": ai_handled,
            "human_required_conversations": human_required,
            "ai_automation_rate": (ai_handled / total_conversations * 100) if total_conversations > 0 else 0
        }
    
    def get_conversations_needing_attention(self, user_id: int, hours: int = 24) -> List[Conversation]:
        """Obtém conversas que precisam de atenção (sem resposta há X horas)"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        return self.db.query(Conversation).filter(
            and_(
                Conversation.user_id == user_id,
                Conversation.status.in_([ConversationStatus.ACTIVE, ConversationStatus.PENDING]),
                Conversation.last_message_at < cutoff_time
            )
        ).order_by(Conversation.last_message_at).all()
    
    def search_conversations(
        self, 
        user_id: int, 
        query: str, 
        limit: int = 20
    ) -> List[Conversation]:
        """Busca conversas por nome do cliente ou conteúdo"""
        return self.db.query(Conversation).filter(
            and_(
                Conversation.user_id == user_id,
                func.lower(Conversation.customer_name).contains(query.lower())
            )
        ).order_by(desc(Conversation.last_message_at)).limit(limit).all()
    
    def delete_conversation(self, conversation_id: int) -> bool:
        """Deleta uma conversa e suas mensagens"""
        conversation = self.get_conversation_by_id(conversation_id)
        if not conversation:
            return False
        
        # Deletar mensagens primeiro
        self.db.query(Message).filter(Message.conversation_id == conversation_id).delete()
        
        # Deletar conversa
        self.db.delete(conversation)
        self.db.commit()
        return True
