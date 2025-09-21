from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

# Enums
class ConversationStatusEnum(str, Enum):
    ACTIVE = "active"
    PENDING = "pending"
    RESOLVED = "resolved"
    ESCALATED = "escalated"

class MessageRoleEnum(str, Enum):
    CUSTOMER = "customer"
    AGENT = "agent"
    SYSTEM = "system"

class MessageTypeEnum(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    LOCATION = "location"

# Schemas de entrada
class SendMessage(BaseModel):
    """Schema para enviar mensagem"""
    phone_number: str = Field(..., min_length=10, max_length=20)
    message: str = Field(..., min_length=1, max_length=4096)
    message_type: MessageTypeEnum = MessageTypeEnum.TEXT
    media_url: Optional[str] = None

class SendTemplate(BaseModel):
    """Schema para enviar template"""
    phone_number: str = Field(..., min_length=10, max_length=20)
    template_name: str = Field(..., min_length=1, max_length=100)
    language_code: str = Field("pt_BR", max_length=10)
    parameters: List[str] = []

class EscalateConversation(BaseModel):
    """Schema para escalar conversa"""
    reason: str = Field(..., min_length=1, max_length=500)

class UpdateConversationStatus(BaseModel):
    """Schema para atualizar status da conversa"""
    status: ConversationStatusEnum
    notes: Optional[str] = None

# Schemas de saída
class MessageBase(BaseModel):
    """Schema base da mensagem"""
    id: int
    content: str
    role: MessageRoleEnum
    message_type: str
    created_at: datetime
    external_id: Optional[str] = None
    metadata: Dict[str, Any] = {}

    class Config:
        from_attributes = True

class Message(MessageBase):
    """Schema completo da mensagem"""
    pass

class ConversationBase(BaseModel):
    """Schema base da conversa"""
    id: int
    customer_name: Optional[str] = None
    customer_phone: str
    customer_email: Optional[str] = None
    status: ConversationStatusEnum
    is_ai_handled: bool
    requires_human: bool
    created_at: datetime
    last_message_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class Conversation(ConversationBase):
    """Schema completo da conversa"""
    agent_id: Optional[int] = None
    agent_name: Optional[str] = None
    metadata: Dict[str, Any] = {}
    unread_count: int = 0

class ConversationWithMessages(Conversation):
    """Schema da conversa com mensagens"""
    messages: List[Message] = []

class ConversationStats(BaseModel):
    """Schema para estatísticas de conversas"""
    total_conversations: int
    active_conversations: int
    pending_conversations: int
    resolved_conversations: int
    whatsapp_conversations: int
    ai_handled_conversations: int
    human_required_conversations: int
    ai_automation_rate: float

class WhatsAppConfig(BaseModel):
    """Schema para configuração do WhatsApp"""
    phone_number_id: Optional[str] = None
    access_token: Optional[str] = None
    verify_token: Optional[str] = None
    webhook_url: Optional[str] = None
    is_configured: bool = False

class WebhookValidation(BaseModel):
    """Schema para validação de webhook"""
    hub_mode: str = Field(alias="hub.mode")
    hub_verify_token: str = Field(alias="hub.verify_token")
    hub_challenge: str = Field(alias="hub.challenge")

    class Config:
        allow_population_by_field_name = True
