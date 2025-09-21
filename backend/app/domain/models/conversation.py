from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum, JSON, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.infrastructure.db.database import Base

class ConversationStatus(str, enum.Enum):
    """Status da conversa"""
    ACTIVE = "active"        # Conversa ativa
    PENDING = "pending"      # Aguardando resposta
    RESOLVED = "resolved"    # Resolvida
    ESCALATED = "escalated"  # Escalada para humano

class ConversationChannel(str, enum.Enum):
    """Canal da conversa"""
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    WEBCHAT = "webchat"
    EMAIL = "email"

class Conversation(Base):
    """Modelo de conversa com clientes"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    
    # Informações do cliente
    customer_name = Column(String(255), nullable=True)
    customer_phone = Column(String(50), nullable=True)
    customer_email = Column(String(255), nullable=True)
    
    # Configurações da conversa
    channel = Column(Enum(ConversationChannel), nullable=False)
    status = Column(Enum(ConversationStatus), default=ConversationStatus.ACTIVE)
    
    # Metadados
    external_id = Column(String(255), nullable=True)  # ID externo (WhatsApp, etc)
    extra_data = Column(JSON, nullable=True)            # Dados adicionais
    
    # Flags
    is_ai_handled = Column(Boolean, default=True)
    requires_human = Column(Boolean, default=False)
    
    # Relacionamentos
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="conversations")
    
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    agent = relationship("Agent", back_populates="conversations")
    
    messages = relationship("Message", back_populates="conversation")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, customer='{self.customer_name}', status='{self.status}')>"

class MessageRole(str, enum.Enum):
    """Papel do remetente da mensagem"""
    CUSTOMER = "customer"
    AGENT = "agent"
    SYSTEM = "system"

class Message(Base):
    """Modelo de mensagem dentro de uma conversa"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    role = Column(Enum(MessageRole), nullable=False)
    
    # Metadados
    message_type = Column(String(50), default="text")  # text, image, audio, etc
    external_id = Column(String(255), nullable=True)   # ID da mensagem no sistema externo
    extra_data = Column(JSON, nullable=True)
    
    # Relacionamentos
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    conversation = relationship("Conversation", back_populates="messages")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Message(id={self.id}, role='{self.role}', content='{self.content[:50]}...')>"
