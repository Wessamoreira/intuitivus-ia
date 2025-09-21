from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.infrastructure.db.database import Base

class APIKeyProvider(str, enum.Enum):
    """Provedores de API suportados"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    GROQ = "groq"
    COHERE = "cohere"
    MISTRAL = "mistral"
    TOGETHER = "together"
    OLLAMA = "ollama"

class APIKeyStatus(str, enum.Enum):
    """Status da chave de API"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    INVALID = "invalid"
    QUOTA_EXCEEDED = "quota_exceeded"

class APIKey(Base):
    """Modelo para chaves de API dos usuários"""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)  # Nome amigável dado pelo usuário
    provider = Column(Enum(APIKeyProvider), nullable=False)
    
    # Chave criptografada
    encrypted_key = Column(Text, nullable=False)
    
    # Status e configurações
    status = Column(Enum(APIKeyStatus), default=APIKeyStatus.ACTIVE)
    priority = Column(Integer, default=1)  # Prioridade de uso (1 = maior prioridade)
    
    # Limites e uso
    monthly_limit = Column(String(20), nullable=True)  # Limite mensal em dólares
    current_usage = Column(String(20), default="0.00")  # Uso atual
    
    # Relacionamentos
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="api_keys")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_used = Column(DateTime(timezone=True), nullable=True)
    last_validated = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<APIKey(id={self.id}, name='{self.name}', provider='{self.provider}')>"
    
    @property
    def is_available(self) -> bool:
        """Verifica se a chave está disponível para uso"""
        return self.status == APIKeyStatus.ACTIVE
