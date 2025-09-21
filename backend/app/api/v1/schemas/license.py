from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

# Enums
class LicenseStatusEnum(str, Enum):
    AVAILABLE = "available"
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"

class LicenseTypeEnum(str, Enum):
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"

# Schemas de entrada
class LicenseCreate(BaseModel):
    """Schema para criação de licença"""
    license_type: LicenseTypeEnum = LicenseTypeEnum.PRO
    expires_at: Optional[datetime] = None
    purchase_email: Optional[str] = None
    purchase_platform: Optional[str] = None
    purchase_transaction_id: Optional[str] = None

class LicenseValidate(BaseModel):
    """Schema para validação de licença"""
    license_key: str = Field(..., min_length=10)

class WebhookData(BaseModel):
    """Schema para dados de webhook de compra"""
    email: str
    platform: str
    transaction_id: str
    license_type: LicenseTypeEnum = LicenseTypeEnum.PRO
    expires_at: Optional[datetime] = None

# Schemas de saída
class LicenseBase(BaseModel):
    """Schema base da licença"""
    id: int
    license_key: str
    status: LicenseStatusEnum
    license_type: LicenseTypeEnum
    expires_at: Optional[datetime] = None
    activated_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class License(LicenseBase):
    """Schema completo da licença"""
    purchase_email: Optional[str] = None
    purchase_platform: Optional[str] = None
    purchase_transaction_id: Optional[str] = None
    updated_at: Optional[datetime] = None

class LicenseStats(BaseModel):
    """Schema para estatísticas de licenças"""
    total_licenses: int
    active_licenses: int
    available_licenses: int
    expired_licenses: int
    revoked_licenses: int
