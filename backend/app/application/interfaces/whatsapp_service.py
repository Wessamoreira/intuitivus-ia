from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    LOCATION = "location"
    CONTACT = "contact"
    STICKER = "sticker"

class MessageStatus(str, Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"

@dataclass
class WhatsAppMessage:
    """Mensagem do WhatsApp"""
    id: Optional[str] = None
    from_number: str = ""
    to_number: str = ""
    message_type: MessageType = MessageType.TEXT
    content: str = ""
    timestamp: Optional[str] = None
    status: MessageStatus = MessageStatus.SENT
    metadata: Dict[str, Any] = None
    media_url: Optional[str] = None
    media_id: Optional[str] = None

@dataclass
class WhatsAppContact:
    """Contato do WhatsApp"""
    phone_number: str
    name: Optional[str] = None
    profile_name: Optional[str] = None
    wa_id: Optional[str] = None

@dataclass
class WebhookData:
    """Dados do webhook do WhatsApp"""
    entry: List[Dict[str, Any]]
    object: str

class IWhatsAppService(ABC):
    """Interface para serviços de WhatsApp"""
    
    @abstractmethod
    async def send_message(
        self,
        to_number: str,
        message: str,
        message_type: MessageType = MessageType.TEXT,
        media_url: Optional[str] = None
    ) -> WhatsAppMessage:
        """Envia uma mensagem"""
        pass
    
    @abstractmethod
    async def send_template_message(
        self,
        to_number: str,
        template_name: str,
        language_code: str = "pt_BR",
        parameters: List[str] = None
    ) -> WhatsAppMessage:
        """Envia uma mensagem de template"""
        pass
    
    @abstractmethod
    async def get_media_url(self, media_id: str) -> Optional[str]:
        """Obtém URL de mídia"""
        pass
    
    @abstractmethod
    async def mark_as_read(self, message_id: str) -> bool:
        """Marca mensagem como lida"""
        pass
    
    @abstractmethod
    def process_webhook(self, webhook_data: Dict[str, Any]) -> List[WhatsAppMessage]:
        """Processa webhook do WhatsApp"""
        pass
    
    @abstractmethod
    async def validate_webhook(self, verify_token: str, challenge: str) -> Optional[str]:
        """Valida webhook do WhatsApp"""
        pass
