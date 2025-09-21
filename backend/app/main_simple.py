"""
FastAPI Main - Versão Simplificada para Teste
Apenas com health check para testar comunicação frontend-backend
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import time
import logging
import uuid
import hashlib

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Modelos Pydantic para autenticação
class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    license_key: str
    company: str = "Default Company"

class LoginRequest(BaseModel):
    email: str
    password: str

# Simulação de banco de dados em memória
users_db = {}
licenses_db = {
    "AIPL-2025-VNAK-X6EP": {"status": "available", "type": "pro"},
    "AIPL-2025-H3EA-B8L3": {"status": "available", "type": "pro"},
    "AIPL-2025-UDV1-ZXN5": {"status": "available", "type": "pro"},
    "AIPL-2025-WJQH-U6G8": {"status": "available", "type": "pro"},
    "AIPL-2025-OD0B-6D4O": {"status": "available", "type": "pro"},
}

def hash_password(password: str) -> str:
    """Hash simples da senha"""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token() -> str:
    """Gera token simples"""
    return str(uuid.uuid4())

# Criar aplicação FastAPI
app = FastAPI(
    title="Intuitivus Flow Studio",
    version="1.0.0",
    description="Plataforma SaaS para criação e gerenciamento de agentes de IA autônomos",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middleware de CORS - Configuração permissiva para desenvolvimento
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em desenvolvimento
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware para logging de requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log da requisição
    logger.info(f"Request: {request.method} {request.url.path}")
    
    # Processar requisição
    response = await call_next(request)
    
    # Log da resposta
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} - Time: {process_time:.4f}s")
    
    return response

# Endpoint de health check
@app.get("/health")
async def health_check():
    """Endpoint para verificar se a API está funcionando"""
    return {
        "status": "healthy",
        "app_name": "Intuitivus Flow Studio",
        "version": "1.0.0",
        "timestamp": time.time(),
        "message": "API is running successfully!"
    }

# Endpoints básicos da API
@app.get("/api/v1/users")
async def get_users():
    """Endpoint básico para listar usuários"""
    return {
        "users": [
            {"id": 1, "name": "Admin User", "email": "admin@example.com"},
            {"id": 2, "name": "Test User", "email": "test@example.com"}
        ],
        "total": 2
    }

@app.get("/api/v1/agents")
async def get_agents():
    """Endpoint básico para listar agentes"""
    return {
        "agents": [
            {"id": 1, "name": "Marketing Agent", "status": "active"},
            {"id": 2, "name": "Support Agent", "status": "active"},
            {"id": 3, "name": "Content Agent", "status": "paused"}
        ],
        "total": 3
    }

@app.get("/api/v1/tasks")
async def get_tasks():
    """Endpoint básico para listar tarefas"""
    return {
        "tasks": [
            {"id": 1, "title": "Create campaign", "status": "completed"},
            {"id": 2, "title": "Generate content", "status": "in_progress"},
            {"id": 3, "title": "Analyze metrics", "status": "pending"}
        ],
        "total": 3
    }

@app.get("/api/v1/campaigns")
async def get_campaigns():
    """Endpoint básico para listar campanhas"""
    return {
        "campaigns": [
            {"id": 1, "name": "Google Ads Campaign", "status": "active"},
            {"id": 2, "name": "Meta Ads Campaign", "status": "active"},
            {"id": 3, "name": "TikTok Ads Campaign", "status": "paused"}
        ],
        "total": 3
    }

# Endpoints de autenticação
@app.post("/api/v1/auth/register")
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
        
        users_db[request.email] = {
            "id": user_id,
            "name": request.name,
            "email": request.email,
            "password": hashed_password,
            "company": request.company,
            "license_key": request.license_key,
            "created_at": time.time()
        }
        
        # Marcar licença como usada
        licenses_db[request.license_key]["status"] = "active"
        licenses_db[request.license_key]["user_email"] = request.email
        
        # Gerar tokens
        access_token = generate_token()
        refresh_token = generate_token()
        
        logger.info(f"Usuário registrado: {request.email}")
        
        return {
            "message": "Usuário criado com sucesso",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": user_id,
                "name": request.name,
                "email": request.email,
                "company": request.company
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no registro: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.post("/api/v1/auth/login")
async def login(request: LoginRequest):
    """Endpoint para login de usuários"""
    try:
        # Verificar se usuário existe
        if request.email not in users_db:
            raise HTTPException(status_code=401, detail="Credenciais inválidas")
        
        user = users_db[request.email]
        hashed_password = hash_password(request.password)
        
        # Verificar senha
        if user["password"] != hashed_password:
            raise HTTPException(status_code=401, detail="Credenciais inválidas")
        
        # Gerar tokens
        access_token = generate_token()
        refresh_token = generate_token()
        
        logger.info(f"Login realizado: {request.email}")
        
        return {
            "message": "Login realizado com sucesso",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "company": user["company"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no login: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

# Handler de exceções globais
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc),
            "path": str(request.url.path)
        }
    )

# Evento de startup
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Intuitivus Flow Studio API v1.0.0")
    logger.info("Environment: development")
    logger.info("CORS: Permissive (development mode)")

# Evento de shutdown
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Intuitivus Flow Studio API")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
