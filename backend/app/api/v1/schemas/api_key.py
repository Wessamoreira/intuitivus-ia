from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

# Enums
class APIKeyProviderEnum(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    GROQ = "groq"
    COHERE = "cohere"
    MISTRAL = "mistral"
    TOGETHER = "together"
    OLLAMA = "ollama"

class APIKeyStatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    INVALID = "invalid"
    QUOTA_EXCEEDED = "quota_exceeded"

# Schemas de entrada
class APIKeyCreate(BaseModel):
    """Schema para criação de chave de API"""
    name: str = Field(..., min_length=2, max_length=255)
    provider: APIKeyProviderEnum
    api_key: str = Field(..., min_length=10)
    priority: int = Field(1, ge=1, le=100)
    monthly_limit: Optional[str] = Field(None, description="Limite mensal em dólares")

class APIKeyUpdate(BaseModel):
    """Schema para atualização de chave de API"""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    priority: Optional[int] = Field(None, ge=1, le=100)
    monthly_limit: Optional[str] = None
    status: Optional[APIKeyStatusEnum] = None

class APIKeyTest(BaseModel):
    """Schema para teste de chave de API"""
    provider: APIKeyProviderEnum
    api_key: str = Field(..., min_length=10)

# Schemas de saída
class APIKeyBase(BaseModel):
    """Schema base da chave de API"""
    id: int
    name: str
    provider: APIKeyProviderEnum
    status: APIKeyStatusEnum
    priority: int
    monthly_limit: Optional[str] = None
    current_usage: str
    created_at: datetime
    last_used: Optional[datetime] = None
    last_validated: Optional[datetime] = None

    class Config:
        from_attributes = True

class APIKey(APIKeyBase):
    """Schema completo da chave de API (sem mostrar a chave real)"""
    key_preview: str  # Apenas primeiros e últimos caracteres

class APIKeyWithModels(APIKey):
    """Schema da chave com modelos disponíveis"""
    available_models: list[str]

class APIKeyStats(BaseModel):
    """Schema para estatísticas de chaves de API"""
    total_keys: int
    active_keys: int
    inactive_keys: int
    quota_exceeded_keys: int
    total_usage_usd: float
    providers_count: dict[str, int]
