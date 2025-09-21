from fastapi import APIRouter, Depends, HTTPException, status, Request, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.infrastructure.db.database import get_db
from app.infrastructure.repositories.conversation_repository import ConversationRepository
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.security.dependencies import get_current_active_user
from app.infrastructure.services.meta_whatsapp_service import meta_whatsapp_service
from app.infrastructure.services.whatsapp_ai_service import whatsapp_ai_service
from app.api.v1.schemas.user import User
from app.api.v1.schemas.whatsapp import (
    SendMessage, SendTemplate, EscalateConversation, UpdateConversationStatus,
    Conversation, ConversationWithMessages, Message, ConversationStats,
    WhatsAppConfig, WebhookValidation, ConversationStatusEnum
)
from app.domain.models.conversation import ConversationStatus, ConversationChannel

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/webhook")
async def whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Webhook para receber mensagens do WhatsApp.
    Este endpoint é chamado pelo Meta quando há novas mensagens.
    """
    try:
        # Obter dados do webhook
        webhook_data = await request.json()
        logger.info(f"Received WhatsApp webhook: {webhook_data}")
        
        # Processar mensagens
        messages = meta_whatsapp_service.process_webhook(webhook_data)
        
        if messages:
            # Processar cada mensagem em background
            for message in messages:
                background_tasks.add_task(
                    _process_whatsapp_message,
                    message,
                    db
                )
        
        return {"status": "success", "messages_processed": len(messages)}
        
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/webhook")
async def verify_webhook(
    request: Request
):
    """
    Verificação do webhook do WhatsApp.
    Usado pelo Meta para validar o endpoint.
    """
    try:
        # Obter parâmetros de query
        mode = request.query_params.get("hub.mode")
        token = request.query_params.get("hub.verify_token")
        challenge = request.query_params.get("hub.challenge")
        
        if mode and token and challenge:
            # Validar token
            validated_challenge = await meta_whatsapp_service.validate_webhook(token, challenge)
            
            if validated_challenge:
                return int(challenge)
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid verify token"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required parameters"
            )
            
    except Exception as e:
        logger.error(f"Error verifying webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook verification failed"
        )

@router.post("/send-message", response_model=dict)
async def send_message(
    message_data: SendMessage,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Envia uma mensagem via WhatsApp.
    
    - **phone_number**: Número do destinatário
    - **message**: Conteúdo da mensagem
    - **message_type**: Tipo da mensagem (text, image, etc.)
    - **media_url**: URL da mídia (se aplicável)
    """
    try:
        # Enviar mensagem
        whatsapp_response = await meta_whatsapp_service.send_message(
            to_number=message_data.phone_number,
            message=message_data.message,
            message_type=message_data.message_type,
            media_url=message_data.media_url
        )
        
        # Salvar no banco
        conversation_repo = ConversationRepository(db)
        
        # Buscar ou criar conversa
        conversation = conversation_repo.get_conversation_by_phone(
            user_id=current_user.id,
            phone_number=message_data.phone_number
        )
        
        if not conversation:
            conversation_data = {
                "customer_phone": message_data.phone_number,
                "channel": ConversationChannel.WHATSAPP,
                "status": ConversationStatus.ACTIVE,
                "user_id": current_user.id,
                "is_ai_handled": False  # Mensagem manual
            }
            conversation = conversation_repo.create_conversation(conversation_data)
        
        # Adicionar mensagem
        conversation_repo.add_message({
            "conversation_id": conversation.id,
            "content": message_data.message,
            "role": "agent",
            "message_type": message_data.message_type.value,
            "external_id": whatsapp_response.id
        })
        
        return {
            "success": True,
            "message_id": whatsapp_response.id,
            "conversation_id": conversation.id,
            "message": "Message sent successfully"
        }
        
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}"
        )

@router.post("/send-template", response_model=dict)
async def send_template(
    template_data: SendTemplate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Envia uma mensagem de template via WhatsApp.
    
    - **phone_number**: Número do destinatário
    - **template_name**: Nome do template aprovado
    - **language_code**: Código do idioma (ex: pt_BR)
    - **parameters**: Parâmetros do template
    """
    try:
        whatsapp_response = await meta_whatsapp_service.send_template_message(
            to_number=template_data.phone_number,
            template_name=template_data.template_name,
            language_code=template_data.language_code,
            parameters=template_data.parameters
        )
        
        return {
            "success": True,
            "message_id": whatsapp_response.id,
            "message": "Template message sent successfully"
        }
        
    except Exception as e:
        logger.error(f"Error sending template message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send template: {str(e)}"
        )

@router.get("/conversations", response_model=List[Conversation])
async def list_conversations(
    status: Optional[ConversationStatusEnum] = Query(None, description="Filtrar por status"),
    skip: int = Query(0, ge=0, description="Número de registros para pular"),
    limit: int = Query(50, ge=1, le=100, description="Número máximo de registros"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Lista as conversas do WhatsApp do usuário.
    
    - **status**: Filtrar por status (opcional)
    - **skip**: Paginação - registros para pular
    - **limit**: Paginação - máximo de registros
    """
    conversation_repo = ConversationRepository(db)
    
    # Converter enum para model enum se fornecido
    status_filter = None
    if status:
        status_filter = ConversationStatus(status.value)
    
    conversations = conversation_repo.get_user_conversations(
        user_id=current_user.id,
        status=status_filter,
        channel=ConversationChannel.WHATSAPP,
        skip=skip,
        limit=limit
    )
    
    # Enriquecer com dados adicionais
    result = []
    for conv in conversations:
        conv_dict = {
            "id": conv.id,
            "customer_name": conv.customer_name,
            "customer_phone": conv.customer_phone,
            "customer_email": conv.customer_email,
            "status": conv.status.value,
            "is_ai_handled": conv.is_ai_handled,
            "requires_human": conv.requires_human,
            "created_at": conv.created_at,
            "last_message_at": conv.last_message_at,
            "agent_id": conv.agent_id,
            "agent_name": conv.agent.name if conv.agent else None,
            "metadata": conv.metadata or {},
            "unread_count": conversation_repo.count_unread_messages(conv.id)
        }
        result.append(Conversation(**conv_dict))
    
    return result

@router.get("/conversations/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Obtém detalhes de uma conversa específica com suas mensagens.
    """
    conversation_repo = ConversationRepository(db)
    
    conversation = conversation_repo.get_conversation_by_id(conversation_id)
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Verificar se a conversa pertence ao usuário
    if conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Obter mensagens
    messages = conversation_repo.get_conversation_messages(conversation_id)
    
    # Montar resposta
    conv_dict = {
        "id": conversation.id,
        "customer_name": conversation.customer_name,
        "customer_phone": conversation.customer_phone,
        "customer_email": conversation.customer_email,
        "status": conversation.status.value,
        "is_ai_handled": conversation.is_ai_handled,
        "requires_human": conversation.requires_human,
        "created_at": conversation.created_at,
        "last_message_at": conversation.last_message_at,
        "agent_id": conversation.agent_id,
        "agent_name": conversation.agent.name if conversation.agent else None,
        "metadata": conversation.metadata or {},
        "unread_count": conversation_repo.count_unread_messages(conversation.id),
        "messages": [
            {
                "id": msg.id,
                "content": msg.content,
                "role": msg.role.value,
                "message_type": msg.message_type,
                "created_at": msg.created_at,
                "external_id": msg.external_id,
                "metadata": msg.metadata or {}
            }
            for msg in messages
        ]
    }
    
    return ConversationWithMessages(**conv_dict)

@router.patch("/conversations/{conversation_id}/status", response_model=Conversation)
async def update_conversation_status(
    conversation_id: int,
    status_data: UpdateConversationStatus,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Atualiza o status de uma conversa.
    """
    conversation_repo = ConversationRepository(db)
    
    conversation = conversation_repo.get_conversation_by_id(conversation_id)
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    if conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Atualizar status
    update_data = {"status": ConversationStatus(status_data.status.value)}
    
    if status_data.notes:
        # Adicionar nota como mensagem do sistema
        conversation_repo.add_message({
            "conversation_id": conversation_id,
            "content": f"Nota: {status_data.notes}",
            "role": "system",
            "message_type": "text"
        })
    
    updated_conversation = conversation_repo.update_conversation(conversation_id, update_data)
    
    return Conversation(**{
        "id": updated_conversation.id,
        "customer_name": updated_conversation.customer_name,
        "customer_phone": updated_conversation.customer_phone,
        "customer_email": updated_conversation.customer_email,
        "status": updated_conversation.status.value,
        "is_ai_handled": updated_conversation.is_ai_handled,
        "requires_human": updated_conversation.requires_human,
        "created_at": updated_conversation.created_at,
        "last_message_at": updated_conversation.last_message_at,
        "agent_id": updated_conversation.agent_id,
        "agent_name": updated_conversation.agent.name if updated_conversation.agent else None,
        "metadata": updated_conversation.metadata or {},
        "unread_count": conversation_repo.count_unread_messages(updated_conversation.id)
    })

@router.post("/conversations/{conversation_id}/escalate")
async def escalate_conversation(
    conversation_id: int,
    escalate_data: EscalateConversation,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Escala uma conversa para atendimento humano.
    """
    conversation_repo = ConversationRepository(db)
    
    conversation = conversation_repo.get_conversation_by_id(conversation_id)
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    if conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Escalar conversa
    success = await whatsapp_ai_service.escalate_to_human(
        conversation_id=conversation_id,
        reason=escalate_data.reason,
        db=db
    )
    
    if success:
        return {"message": "Conversation escalated to human successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to escalate conversation"
        )

@router.get("/stats", response_model=ConversationStats)
async def get_conversation_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Obtém estatísticas das conversas do WhatsApp.
    """
    conversation_repo = ConversationRepository(db)
    stats = conversation_repo.get_conversation_stats(current_user.id)
    
    return ConversationStats(**stats)

@router.get("/config", response_model=WhatsAppConfig)
async def get_whatsapp_config(
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtém configuração atual do WhatsApp.
    """
    from app.core.config import settings
    
    return WhatsAppConfig(
        phone_number_id=settings.META_WHATSAPP_PHONE_ID,
        is_configured=bool(
            settings.META_WHATSAPP_TOKEN and 
            settings.META_WHATSAPP_PHONE_ID and 
            settings.META_WHATSAPP_VERIFY_TOKEN
        ),
        webhook_url=f"{settings.API_V1_STR}/whatsapp/webhook"
    )

# Função auxiliar para processar mensagens em background
async def _process_whatsapp_message(whatsapp_message, db: Session):
    """Processa mensagem do WhatsApp em background"""
    try:
        # Por enquanto, vamos assumir que todas as mensagens são para o primeiro usuário
        # Em produção, você precisaria implementar lógica para determinar o usuário correto
        # baseado no número de telefone de destino ou outras informações
        
        user_repo = UserRepository(db)
        users = user_repo.get_all(limit=1)  # Pegar primeiro usuário para demo
        
        if users:
            user = users[0]
            await whatsapp_ai_service.process_incoming_message(
                whatsapp_message=whatsapp_message,
                user_id=user.id,
                db=db
            )
        else:
            logger.warning("No users found to process WhatsApp message")
            
    except Exception as e:
        logger.error(f"Error processing WhatsApp message in background: {e}")
