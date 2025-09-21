from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class AgentTask:
    """Tarefa para ser executada por um agente"""
    id: str
    title: str
    description: str
    input_data: Dict[str, Any]
    agent_id: int
    priority: str = "medium"
    expected_output: Optional[str] = None
    tools: List[str] = None
    context: Dict[str, Any] = None

@dataclass
class TaskResult:
    """Resultado da execução de uma tarefa"""
    task_id: str
    agent_id: int
    status: TaskStatus
    output: Optional[str] = None
    error_message: Optional[str] = None
    tokens_used: int = 0
    execution_time: float = 0.0
    cost: float = 0.0
    metadata: Dict[str, Any] = None

@dataclass
class CrewExecution:
    """Execução de uma crew (equipe de agentes)"""
    crew_id: str
    tasks: List[AgentTask]
    agents: List[int]  # IDs dos agentes
    status: TaskStatus
    results: List[TaskResult] = None
    total_cost: float = 0.0
    total_time: float = 0.0

class IAgentService(ABC):
    """Interface para serviços de execução de agentes"""
    
    @abstractmethod
    async def execute_task(
        self,
        task: AgentTask,
        user_id: int
    ) -> TaskResult:
        """Executa uma tarefa individual"""
        pass
    
    @abstractmethod
    async def execute_crew(
        self,
        crew_execution: CrewExecution,
        user_id: int
    ) -> CrewExecution:
        """Executa uma crew (equipe) de agentes"""
        pass
    
    @abstractmethod
    async def get_task_status(
        self,
        task_id: str
    ) -> TaskStatus:
        """Obtém status de uma tarefa"""
        pass
    
    @abstractmethod
    async def cancel_task(
        self,
        task_id: str
    ) -> bool:
        """Cancela uma tarefa em execução"""
        pass
