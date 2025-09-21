from pydantic_settings import BaseSettings
from typing import Optional, List
import os
import secrets
from pathlib import Path
from pydantic import validator, Field

class Settings(BaseSettings):
    # Aplicação
    APP_NAME: str = "AI Agents Platform"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"
    
    # Servidor
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Banco de dados
    DATABASE_URL: Optional[str] = None
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "ai_agents_platform"
    POSTGRES_PORT: int = 5432
    
    # Segurança - OBRIGATÓRIAS em produção
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Criptografia para chaves de API
    ENCRYPTION_KEY: Optional[str] = None
    
    # CORS - Configuração segura
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ]
    
    # Domínios de produção (adicionar conforme necessário)
    PRODUCTION_CORS_ORIGINS: List[str] = []
    
    # Configurações CORS adicionais
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Email
    RESEND_API_KEY: Optional[str] = None
    FROM_EMAIL: str = "noreply@aiagents.com"
    
    # Webhooks de licenciamento
    KIWIFY_WEBHOOK_SECRET: Optional[str] = None
    HOTMART_WEBHOOK_SECRET: Optional[str] = None
    
    # Redis (para cache e filas)
    REDIS_URL: str = "redis://localhost:6379"
    
    # Provedores de LLM - OpenAI
    OPENAI_API_KEY: Optional[str] = None
    
    # Provedores de LLM - Anthropic
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # Provedores de LLM - Google
    GOOGLE_API_KEY: Optional[str] = None
    
    # WhatsApp
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_WHATSAPP_NUMBER: Optional[str] = None
    
    # Meta WhatsApp Cloud API
    META_WHATSAPP_TOKEN: Optional[str] = None
    META_WHATSAPP_PHONE_ID: Optional[str] = None
    META_WHATSAPP_VERIFY_TOKEN: Optional[str] = None
    
    # Google Ads
    GOOGLE_ADS_DEVELOPER_TOKEN: Optional[str] = None
    GOOGLE_ADS_CLIENT_ID: Optional[str] = None
    GOOGLE_ADS_CLIENT_SECRET: Optional[str] = None
    
    # Meta Ads
    META_ADS_APP_ID: Optional[str] = None
    META_ADS_APP_SECRET: Optional[str] = None
    
    # TikTok Ads
    TIKTOK_ADS_APP_ID: Optional[str] = None
    TIKTOK_ADS_SECRET: Optional[str] = None
    
    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        # Fallback para SQLite em desenvolvimento
        if self.DEBUG:
            return "sqlite:///./ai_agents_platform.db"
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @validator("SECRET_KEY")
    def validate_secret_key(cls, v):
        if v == "your-super-secret-key-change-in-production":
            raise ValueError("SECRET_KEY deve ser alterada em produção!")
        if len(v) < 32:
            raise ValueError("SECRET_KEY deve ter pelo menos 32 caracteres")
        return v
    
    @validator("BACKEND_CORS_ORIGINS", "PRODUCTION_CORS_ORIGINS")
    def validate_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @property
    def cors_origins(self) -> List[str]:
        """Retorna as origens CORS baseadas no ambiente"""
        if self.DEBUG:
            return self.BACKEND_CORS_ORIGINS
        return self.PRODUCTION_CORS_ORIGINS or self.BACKEND_CORS_ORIGINS
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        validate_assignment = True

# Instância global das configurações
settings = Settings()

# Função para gerar chave de criptografia segura
def get_encryption_key() -> bytes:
    """Gera ou recupera chave de criptografia de forma segura"""
    if settings.ENCRYPTION_KEY:
        return settings.ENCRYPTION_KEY.encode()
    
    # Em produção, a chave DEVE estar no .env
    if not settings.DEBUG:
        raise ValueError(
            "ENCRYPTION_KEY é obrigatória em produção! "
            "Defina no arquivo .env ou variável de ambiente."
        )
    
    # Apenas em desenvolvimento, gerar chave temporária
    from cryptography.fernet import Fernet
    key = Fernet.generate_key()
    
    # Tentar salvar no .env para desenvolvimento
    env_path = Path(".env")
    try:
        if env_path.exists():
            # Verificar se já existe
            with open(env_path, "r") as f:
                content = f.read()
            if "ENCRYPTION_KEY" not in content:
                with open(env_path, "a") as f:
                    f.write(f"\n# Chave de criptografia (gerada automaticamente)\n")
                    f.write(f"ENCRYPTION_KEY={key.decode()}\n")
    except Exception:
        pass  # Falha silenciosa em desenvolvimento
    
    return key


# Validação adicional de configurações críticas
def validate_critical_settings():
    """Valida configurações críticas na inicialização"""
    errors = []
    
    # Validar SECRET_KEY
    if settings.SECRET_KEY == "your-super-secret-key-change-in-production":
        errors.append("SECRET_KEY deve ser alterada!")
    
    # Validar configurações de produção
    if not settings.DEBUG:
        if not settings.ENCRYPTION_KEY:
            errors.append("ENCRYPTION_KEY é obrigatória em produção")
        
        if not settings.PRODUCTION_CORS_ORIGINS:
            errors.append("PRODUCTION_CORS_ORIGINS deve ser definida em produção")
    
    if errors:
        raise ValueError(f"Configurações críticas inválidas: {'; '.join(errors)}")


# Validar na importação
try:
    validate_critical_settings()
except ValueError as e:
    if not settings.DEBUG:
        raise e
    # Em desenvolvimento, apenas avisar
    print(f"⚠️  AVISO: {e}")
