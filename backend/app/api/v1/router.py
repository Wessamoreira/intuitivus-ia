from fastapi import APIRouter

from app.api.v1.endpoints import auth, agents, api_keys, tasks, whatsapp

api_router = APIRouter()

# Incluir routers dos endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(agents.router, prefix="/agents", tags=["Agents"])
api_router.include_router(api_keys.router, prefix="/api-keys", tags=["API Keys"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["Task Execution"])
api_router.include_router(whatsapp.router, prefix="/whatsapp", tags=["WhatsApp Business"])

# Health check específico da API
@api_router.get("/health")
async def api_health():
    """Health check da API v1"""
    return {
        "status": "healthy",
        "version": "v1",
        "message": "AI Agents Platform API is running"
    }
