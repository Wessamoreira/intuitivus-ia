"""
Modelos de domínio da aplicação.
Importa todos os modelos para facilitar o uso.
"""

from .user import User
from .license import License, LicenseStatus, LicenseType
from .agent import Agent, AgentStatus, AgentCategory
from .api_key import APIKey, APIKeyProvider, APIKeyStatus
from .task import Task, TaskStatus, TaskPriority
from .conversation import Conversation, Message, ConversationStatus, ConversationChannel, MessageRole
from .campaign import Campaign, CampaignStatus, CampaignPlatform

__all__ = [
    # User models
    "User",
    
    # License models
    "License",
    "LicenseStatus", 
    "LicenseType",
    
    # Agent models
    "Agent",
    "AgentStatus",
    "AgentCategory",
    
    # API Key models
    "APIKey",
    "APIKeyProvider",
    "APIKeyStatus",
    
    # Task models
    "Task",
    "TaskStatus",
    "TaskPriority",
    
    # Conversation models
    "Conversation",
    "Message",
    "ConversationStatus",
    "ConversationChannel",
    "MessageRole",
    
    # Campaign models
    "Campaign",
    "CampaignStatus",
    "CampaignPlatform",
]