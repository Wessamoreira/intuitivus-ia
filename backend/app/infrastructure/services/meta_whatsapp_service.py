import httpx
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.application.interfaces.whatsapp_service import (
    IWhatsAppService, WhatsAppMessage, WhatsAppContact, 
    MessageType, MessageStatus, WebhookData
)
from app.core.config import settings

logger = logging.getLogger(__name__)

class MetaWhatsAppService(IWhatsAppService):
    """Implementação do serviço WhatsApp usando Meta Cloud API"""
    
    def __init__(self):
        self.access_token = settings.META_WHATSAPP_TOKEN
        self.phone_number_id = settings.META_WHATSAPP_PHONE_ID
        self.verify_token = settings.META_WHATSAPP_VERIFY_TOKEN
        self.base_url = f"https://graph.facebook.com/v18.0/{self.phone_number_id}"
        
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    async def send_message(
        self,
        to_number: str,
        message: str,
        message_type: MessageType = MessageType.TEXT,
        media_url: Optional[str] = None
    ) -> WhatsAppMessage:
        """Envia uma mensagem via Meta WhatsApp Cloud API"""
        try:
            # Limpar número de telefone (remover caracteres especiais)
            clean_number = self._clean_phone_number(to_number)
            
            # Preparar payload baseado no tipo de mensagem
            if message_type == MessageType.TEXT:
                payload = {
                    "messaging_product": "whatsapp",
                    "to": clean_number,
                    "type": "text",
                    "text": {"body": message}
                }
            elif message_type == MessageType.IMAGE and media_url:
                payload = {
                    "messaging_product": "whatsapp",
                    "to": clean_number,
                    "type": "image",
                    "image": {
                        "link": media_url,
                        "caption": message if message else ""
                    }
                }
            elif message_type == MessageType.DOCUMENT and media_url:
                payload = {
                    "messaging_product": "whatsapp",
                    "to": clean_number,
                    "type": "document",
                    "document": {
                        "link": media_url,
                        "caption": message if message else ""
                    }
                }
            else:
                raise ValueError(f"Unsupported message type: {message_type}")
            
            # Fazer requisição para API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers=self.headers,
                    json=payload,
                    timeout=30.0
                )
            
            if response.status_code == 200:
                result = response.json()
                message_id = result.get("messages", [{}])[0].get("id")
                
                logger.info(f"Message sent successfully to {clean_number}, ID: {message_id}")
                
                return WhatsAppMessage(
                    id=message_id,
                    from_number=self.phone_number_id,
                    to_number=clean_number,
                    message_type=message_type,
                    content=message,
                    timestamp=datetime.utcnow().isoformat(),
                    status=MessageStatus.SENT,
                    media_url=media_url
                )
            else:
                error_msg = f"Failed to send message: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            raise
    
    async def send_template_message(
        self,
        to_number: str,
        template_name: str,
        language_code: str = "pt_BR",
        parameters: List[str] = None
    ) -> WhatsAppMessage:
        """Envia uma mensagem de template"""
        try:
            clean_number = self._clean_phone_number(to_number)
            
            # Preparar componentes do template
            components = []
            if parameters:
                components.append({
                    "type": "body",
                    "parameters": [{"type": "text", "text": param} for param in parameters]
                })
            
            payload = {
                "messaging_product": "whatsapp",
                "to": clean_number,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {"code": language_code},
                    "components": components
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers=self.headers,
                    json=payload,
                    timeout=30.0
                )
            
            if response.status_code == 200:
                result = response.json()
                message_id = result.get("messages", [{}])[0].get("id")
                
                logger.info(f"Template message sent to {clean_number}, ID: {message_id}")
                
                return WhatsAppMessage(
                    id=message_id,
                    from_number=self.phone_number_id,
                    to_number=clean_number,
                    message_type=MessageType.TEXT,
                    content=f"Template: {template_name}",
                    timestamp=datetime.utcnow().isoformat(),
                    status=MessageStatus.SENT
                )
            else:
                error_msg = f"Failed to send template: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            logger.error(f"Error sending template message: {e}")
            raise
    
    async def get_media_url(self, media_id: str) -> Optional[str]:
        """Obtém URL de mídia do WhatsApp"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://graph.facebook.com/v18.0/{media_id}",
                    headers=self.headers,
                    timeout=30.0
                )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("url")
            else:
                logger.error(f"Failed to get media URL: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting media URL: {e}")
            return None
    
    async def mark_as_read(self, message_id: str) -> bool:
        """Marca mensagem como lida"""
        try:
            payload = {
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message_id
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers=self.headers,
                    json=payload,
                    timeout=30.0
                )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error marking message as read: {e}")
            return False
    
    def process_webhook(self, webhook_data: Dict[str, Any]) -> List[WhatsAppMessage]:
        """Processa webhook do WhatsApp"""
        messages = []
        
        try:
            entry = webhook_data.get("entry", [])
            
            for entry_item in entry:
                changes = entry_item.get("changes", [])
                
                for change in changes:
                    value = change.get("value", {})
                    
                    # Processar mensagens recebidas
                    if "messages" in value:
                        for msg in value["messages"]:
                            message = self._parse_incoming_message(msg, value)
                            if message:
                                messages.append(message)
                    
                    # Processar status de mensagens
                    if "statuses" in value:
                        for status in value["statuses"]:
                            self._process_message_status(status)
            
            logger.info(f"Processed webhook with {len(messages)} messages")
            return messages
            
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return []
    
    def _parse_incoming_message(self, msg: Dict[str, Any], value: Dict[str, Any]) -> Optional[WhatsAppMessage]:
        """Parseia mensagem recebida"""
        try:
            message_id = msg.get("id")
            from_number = msg.get("from")
            timestamp = msg.get("timestamp")
            message_type = msg.get("type")
            
            # Obter contato
            contacts = value.get("contacts", [])
            contact_name = None
            if contacts:
                contact = contacts[0]
                contact_name = contact.get("profile", {}).get("name")
            
            # Extrair conteúdo baseado no tipo
            content = ""
            media_url = None
            media_id = None
            
            if message_type == "text":
                content = msg.get("text", {}).get("body", "")
            elif message_type == "image":
                image_data = msg.get("image", {})
                content = image_data.get("caption", "")
                media_id = image_data.get("id")
            elif message_type == "audio":
                audio_data = msg.get("audio", {})
                media_id = audio_data.get("id")
                content = "[Áudio]"
            elif message_type == "video":
                video_data = msg.get("video", {})
                content = video_data.get("caption", "[Vídeo]")
                media_id = video_data.get("id")
            elif message_type == "document":
                doc_data = msg.get("document", {})
                content = doc_data.get("caption", doc_data.get("filename", "[Documento]"))
                media_id = doc_data.get("id")
            elif message_type == "location":
                location = msg.get("location", {})
                content = f"📍 Localização: {location.get('latitude')}, {location.get('longitude')}"
            else:
                content = f"[{message_type.title()}]"
            
            return WhatsAppMessage(
                id=message_id,
                from_number=from_number,
                to_number=self.phone_number_id,
                message_type=MessageType(message_type) if message_type in [t.value for t in MessageType] else MessageType.TEXT,
                content=content,
                timestamp=timestamp,
                status=MessageStatus.DELIVERED,
                metadata={
                    "contact_name": contact_name,
                    "profile_name": contact_name
                },
                media_id=media_id
            )
            
        except Exception as e:
            logger.error(f"Error parsing incoming message: {e}")
            return None
    
    def _process_message_status(self, status: Dict[str, Any]):
        """Processa status de mensagem"""
        try:
            message_id = status.get("id")
            status_value = status.get("status")
            timestamp = status.get("timestamp")
            
            logger.info(f"Message {message_id} status: {status_value} at {timestamp}")
            
        except Exception as e:
            logger.error(f"Error processing message status: {e}")
    
    def _clean_phone_number(self, phone_number: str) -> str:
        """Limpa número de telefone removendo caracteres especiais"""
        # Remover todos os caracteres não numéricos
        clean = ''.join(filter(str.isdigit, phone_number))
        
        # Se não começar com código do país, adicionar 55 (Brasil)
        if not clean.startswith('55') and len(clean) >= 10:
            clean = '55' + clean
        
        return clean
    
    async def validate_webhook(self, verify_token: str, challenge: str) -> Optional[str]:
        """Valida webhook do WhatsApp"""
        if verify_token == self.verify_token:
            logger.info("Webhook validated successfully")
            return challenge
        else:
            logger.warning("Invalid webhook verification token")
            return None

# Instância global do serviço
meta_whatsapp_service = MetaWhatsAppService()
