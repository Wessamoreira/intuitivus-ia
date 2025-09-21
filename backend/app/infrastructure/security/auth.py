from datetime import datetime, timedelta
from typing import Optional, Union
import secrets
import string
import re
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from cryptography.fernet import Fernet

from app.core.config import settings, get_encryption_key

# Configuração do hash de senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuração da criptografia para chaves de API
fernet = Fernet(get_encryption_key())

class AuthService:
    """Serviço de autenticação e segurança"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verifica se a senha está correta"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Gera hash da senha"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Cria token de acesso JWT"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Cria token de refresh"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """Verifica e decodifica token JWT"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except JWTError:
            return None
    
    @staticmethod
    def encrypt_api_key(api_key: str) -> str:
        """Criptografa uma chave de API"""
        return fernet.encrypt(api_key.encode()).decode()
    
    @staticmethod
    def decrypt_api_key(encrypted_key: str) -> str:
        """Descriptografa uma chave de API"""
        try:
            return fernet.decrypt(encrypted_key.encode()).decode()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to decrypt API key"
            )

class TokenData:
    """Dados do token JWT"""
    def __init__(self, user_id: Optional[int] = None, email: Optional[str] = None):
        self.user_id = user_id
        self.email = email

def generate_license_key() -> str:
    """Gera uma chave de licença única"""
    
    # Formato: AIPL-YYYY-XXXX-XXXX
    year = datetime.now().year
    
    # Gerar 8 caracteres aleatórios
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(secrets.choice(chars) for _ in range(8))
    
    # Formar a chave
    license_key = f"AIPL-{year}-{random_part[:4]}-{random_part[4:]}"
    
    return license_key

def validate_license_key(license_key: str) -> bool:
    """Valida o formato de uma chave de licença"""
    
    # Padrão: AIPL-YYYY-XXXX-XXXX
    pattern = r"^AIPL-\d{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$"
    return bool(re.match(pattern, license_key))
