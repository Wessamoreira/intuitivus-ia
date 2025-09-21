from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

# Enums
class TaskStatusEnum(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriorityEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

# Schemas de entrada
class TaskExecute(BaseModel):
    """Schema para execução de tarefa individual"""
    agent_id: int
    title: str = Field(..., min_length=2, max_length=255)
    description: str = Field(..., min_length=10)
    input_data: Dict[str, Any] = {}
    priority: TaskPriorityEnum = TaskPriorityEnum.MEDIUM
    expected_output: Optional[str] = None
    tools: List[str] = []
    context: Dict[str, Any] = {}

class CrewExecute(BaseModel):
    """Schema para execução de crew (equipe)"""
    name: str = Field(..., min_length=2, max_length=255)
    description: str = Field(..., min_length=10)
    agent_ids: List[int] = Field(..., min_items=1, max_items=10)
    tasks: List[TaskExecute]
    process_type: str = Field("sequential", regex="^(sequential|hierarchical)$")

class TaskCancel(BaseModel):
    """Schema para cancelamento de tarefa"""
    reason: Optional[str] = None

# Schemas de saída
class TaskResult(BaseModel):
    """Schema do resultado de uma tarefa"""
    task_id: str
    agent_id: int
    status: TaskStatusEnum
    output: Optional[str] = None
    error_message: Optional[str] = None
    tokens_used: int = 0
    execution_time: float = 0.0
    cost: float = 0.0
    metadata: Dict[str, Any] = {}
    created_at: datetime
    completed_at: Optional[datetime] = None

class TaskExecution(BaseModel):
    """Schema de execução de tarefa"""
    id: str
    title: str
    description: str
    agent_id: int
    agent_name: str
    status: TaskStatusEnum
    priority: TaskPriorityEnum
    input_data: Dict[str, Any]
    result: Optional[TaskResult] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class CrewExecution(BaseModel):
    """Schema de execução de crew"""
    id: str
    name: str
    description: str
    agent_ids: List[int]
    agent_names: List[str]
    status: TaskStatusEnum
    process_type: str
    tasks: List[TaskExecution]
    total_cost: float = 0.0
    total_time: float = 0.0
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class TaskStats(BaseModel):
    """Schema para estatísticas de tarefas"""
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    running_tasks: int
    total_tokens_used: int
    total_cost: float
    average_execution_time: float
    success_rate: float

class AgentPerformance(BaseModel):
    """Schema para performance de agente"""
    agent_id: int
    agent_name: str
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    success_rate: float
    total_tokens: int
    total_cost: float
    average_time: float
