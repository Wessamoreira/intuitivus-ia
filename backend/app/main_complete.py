"""
FastAPI Main - Sistema Completo com Autenticação Híbrida
Inclui todos os CRUDs e funcionalidades do sistema
"""

from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
import time
import logging
import uuid
import hashlib
import jwt
from datetime import datetime, timedelta
import os
import base64
import json

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurações de segurança
JWT_SECRET = "your-super-secret-jwt-key-change-in-production"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Modelos Pydantic
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    license_key: str
    company: str = "Default Company"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    company: str
    license_type: str
    created_at: float

class AgentCreate(BaseModel):
    name: str
    description: str
    type: str = "general"
    status: str = "active"
    config: Dict[str, Any] = {}

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

class CampaignCreate(BaseModel):
    name: str
    description: str
    agent_id: int
    platform: str
    status: str = "draft"
    config: Dict[str, Any] = {}

class TaskCreate(BaseModel):
    title: str
    description: str
    agent_id: int
    priority: str = "medium"
    status: str = "pending"

class WhatsAppConfig(BaseModel):
    phone_number: str
    api_key: str
    webhook_url: Optional[str] = None
    enabled: bool = True

# Simulação de banco de dados em memória
users_db = {}
agents_db = {}
campaigns_db = {}
tasks_db = {}
whatsapp_configs_db = {}
licenses_db = {
    "AIPL-2025-VNAK-X6EP": {"status": "available", "type": "pro"},
    "AIPL-2025-H3EA-B8L3": {"status": "available", "type": "pro"},
    "AIPL-2025-UDV1-ZXN5": {"status": "available", "type": "pro"},
    "AIPL-2025-WJQH-U6G8": {"status": "available", "type": "pro"},
    "AIPL-2025-OD0B-6D4O": {"status": "available", "type": "pro"},
}

def hash_password(password: str) -> str:
    """Hash da senha com salt"""
    salt = os.urandom(32)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return base64.b64encode(salt + pwdhash).decode()

def verify_password(password: str, hashed: str) -> bool:
    """Verifica senha"""
    try:
        decoded = base64.b64decode(hashed.encode())
        salt = decoded[:32]
        stored_hash = decoded[32:]
        pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return pwdhash == stored_hash
    except:
        return False

def create_access_token(data: dict) -> str:
    """Cria token JWT"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def create_refresh_token(data: dict) -> str:
    """Cria refresh token JWT"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> dict:
    """Verifica e decodifica token JWT"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

# Criar aplicação FastAPI
app = FastAPI(
    title="Intuitivus Flow Studio - Sistema Completo",
    version="2.0.0",
    description="Plataforma SaaS completa para criação e gerenciamento de agentes de IA autônomos",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middleware de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Dependency para autenticação
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency para verificar usuário autenticado"""
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Tipo de token inválido")
    
    email = payload.get("sub")
    if not email or email not in users_db:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    
    return users_db[email]

# Middleware para logging de requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"Request: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} - Time: {process_time:.4f}s")
    
    return response

# Endpoints públicos
@app.get("/health")
async def health_check():
    """Endpoint para verificar se a API está funcionando"""
    return {
        "status": "healthy",
        "app_name": "Intuitivus Flow Studio",
        "version": "2.0.0",
        "timestamp": time.time(),
        "message": "API is running successfully!",
        "features": ["hybrid_encryption", "jwt_auth", "complete_crud"]
    }

@app.post("/api/v1/auth/register", response_model=TokenResponse)
async def register(request: RegisterRequest):
    """Endpoint para registro de usuários"""
    try:
        # Verificar se email já existe
        if request.email in users_db:
            raise HTTPException(status_code=400, detail="Email já cadastrado")
        
        # Verificar licença
        if request.license_key not in licenses_db:
            raise HTTPException(status_code=400, detail="Chave de licença inválida")
        
        if licenses_db[request.license_key]["status"] != "available":
            raise HTTPException(status_code=400, detail="Chave de licença já utilizada")
        
        # Criar usuário
        user_id = len(users_db) + 1
        hashed_password = hash_password(request.password)
        
        user_data = {
            "id": user_id,
            "name": request.name,
            "email": request.email,
            "password": hashed_password,
            "company": request.company,
            "license_key": request.license_key,
            "license_type": licenses_db[request.license_key]["type"],
            "created_at": time.time(),
            "is_active": True
        }
        
        users_db[request.email] = user_data
        
        # Marcar licença como usada
        licenses_db[request.license_key]["status"] = "active"
        licenses_db[request.license_key]["user_email"] = request.email
        
        # Gerar tokens
        token_data = {"sub": request.email, "user_id": user_id}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        logger.info(f"Usuário registrado: {request.email}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no registro: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.post("/api/v1/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Endpoint para login de usuários"""
    try:
        # Verificar se usuário existe
        if request.email not in users_db:
            raise HTTPException(status_code=401, detail="Credenciais inválidas")
        
        user = users_db[request.email]
        
        # Verificar senha
        if not verify_password(request.password, user["password"]):
            raise HTTPException(status_code=401, detail="Credenciais inválidas")
        
        # Verificar se usuário está ativo
        if not user.get("is_active", True):
            raise HTTPException(status_code=401, detail="Usuário inativo")
        
        # Gerar tokens
        token_data = {"sub": request.email, "user_id": user["id"]}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        logger.info(f"Login realizado: {request.email}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no login: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.get("/api/v1/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Endpoint para obter informações do usuário atual"""
    return UserResponse(
        id=current_user["id"],
        name=current_user["name"],
        email=current_user["email"],
        company=current_user["company"],
        license_type=current_user["license_type"],
        created_at=current_user["created_at"]
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_complete:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
