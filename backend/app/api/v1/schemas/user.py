from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# Schemas de entrada (request)
class UserCreate(BaseModel):
    """Schema para criação de usuário"""
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8)
    license_key: str = Field(..., min_length=10)
    company: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)

class UserLogin(BaseModel):
    """Schema para login"""
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    """Schema para atualização de usuário"""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    company: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    bio: Optional[str] = None

class UserChangePassword(BaseModel):
    """Schema para mudança de senha"""
    current_password: str
    new_password: str = Field(..., min_length=8)

# Schemas de saída (response)
class UserBase(BaseModel):
    """Schema base do usuário"""
    id: int
    email: str
    name: str
    company: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

class User(UserBase):
    """Schema completo do usuário"""
    pass

class UserWithLicense(UserBase):
    """Schema do usuário com informações de licença"""
    license: Optional["LicenseBase"] = None

# Schemas de token
class Token(BaseModel):
    """Schema de token de acesso"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenRefresh(BaseModel):
    """Schema para refresh de token"""
    refresh_token: str

# Import circular fix
from .license import LicenseBase
UserWithLicense.model_rebuild()
