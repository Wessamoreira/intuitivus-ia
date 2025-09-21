from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.infrastructure.db.database import Base

class LicenseStatus(str, enum.Enum):
    """Status da licença"""
    AVAILABLE = "available"  # Disponível para uso
    ACTIVE = "active"       # Ativa e em uso
    EXPIRED = "expired"     # Expirada
    REVOKED = "revoked"     # Revogada

class LicenseType(str, enum.Enum):
    """Tipo de licença"""
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class License(Base):
    """Modelo de licença do sistema"""
    __tablename__ = "licenses"

    id = Column(Integer, primary_key=True, index=True)
    license_key = Column(String(255), unique=True, index=True, nullable=False)
    status = Column(Enum(LicenseStatus), default=LicenseStatus.AVAILABLE)
    license_type = Column(Enum(LicenseType), default=LicenseType.PRO)
    
    # Relacionamento com usuário
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="license")
    
    # Informações de validade
    expires_at = Column(DateTime(timezone=True), nullable=True)
    activated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Informações de compra (webhook)
    purchase_email = Column(String(255), nullable=True)
    purchase_platform = Column(String(50), nullable=True)  # kiwify, hotmart, etc
    purchase_transaction_id = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<License(id={self.id}, key='{self.license_key}', status='{self.status}')>"
    
    @property
    def is_valid(self) -> bool:
        """Verifica se a licença é válida"""
        if self.status != LicenseStatus.ACTIVE:
            return False
        
        if self.expires_at and self.expires_at < func.now():
            return False
            
        return True
