from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

# Enums
class AgentStatusEnum(str, Enum):
    ACTIVE = "active"
    IDLE = "idle"
    PAUSED = "paused"
    ERROR = "error"
    TRAINING = "training"

class AgentCategoryEnum(str, Enum):
    MARKETING = "marketing"
    SUPPORT = "support"
    CONTENT = "content"
    ANALYTICS = "analytics"
    SALES = "sales"
    GENERAL = "general"

# Schemas de entrada
class AgentCreate(BaseModel):
    """Schema para criação de agente"""
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    role: str = Field(..., min_length=2, max_length=255)
    category: AgentCategoryEnum = AgentCategoryEnum.GENERAL
    llm_provider: str = Field(..., min_length=2, max_length=50)
    llm_model: str = Field(..., min_length=2, max_length=100)
    system_prompt: str = Field(..., min_length=10)
    instructions: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None

class AgentUpdate(BaseModel):
    """Schema para atualização de agente"""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    role: Optional[str] = Field(None, min_length=2, max_length=255)
    category: Optional[AgentCategoryEnum] = None
    llm_provider: Optional[str] = Field(None, min_length=2, max_length=50)
    llm_model: Optional[str] = Field(None, min_length=2, max_length=100)
    system_prompt: Optional[str] = Field(None, min_length=10)
    instructions: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None

class AgentStatusUpdate(BaseModel):
    """Schema para atualização de status do agente"""
    status: AgentStatusEnum

# Schemas de saída
class AgentBase(BaseModel):
    """Schema base do agente"""
    id: int
    name: str
    description: Optional[str] = None
    role: str
    category: AgentCategoryEnum
    status: AgentStatusEnum
    llm_provider: str
    llm_model: str
    tasks_completed: int
    tasks_failed: int
    total_tokens_used: int
    total_cost: str
    created_at: datetime
    last_active: Optional[datetime] = None

    class Config:
        from_attributes = True

class Agent(AgentBase):
    """Schema completo do agente"""
    system_prompt: str
    instructions: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    updated_at: Optional[datetime] = None

class AgentSummary(AgentBase):
    """Schema resumido do agente (sem prompts)"""
    success_rate: float

class AgentStats(BaseModel):
    """Schema para estatísticas de agentes"""
    total_agents: int
    active_agents: int
    idle_agents: int
    paused_agents: int
    total_tasks_completed: int
    total_tasks_failed: int
    overall_success_rate: float
    total_tokens_used: int
    total_cost: float

class AgentExecution(BaseModel):
    """Schema para execução de agente"""
    agent_id: int
    input_data: Dict[str, Any]
    priority: Optional[str] = "medium"
