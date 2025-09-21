from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.infrastructure.db.database import Base

class TaskStatus(str, enum.Enum):
    """Status da tarefa"""
    PENDING = "pending"      # Aguardando execução
    RUNNING = "running"      # Em execução
    COMPLETED = "completed"  # Concluída com sucesso
    FAILED = "failed"        # Falhou
    CANCELLED = "cancelled"  # Cancelada

class TaskPriority(str, enum.Enum):
    """Prioridade da tarefa"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class Task(Base):
    """Modelo de tarefa executada por agentes"""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Configurações da tarefa
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    
    # Input e output
    input_data = Column(JSON, nullable=True)    # Dados de entrada
    output_data = Column(JSON, nullable=True)   # Resultado da execução
    error_message = Column(Text, nullable=True) # Mensagem de erro se falhou
    
    # Métricas
    tokens_used = Column(Integer, default=0)
    execution_time = Column(Integer, nullable=True)  # Tempo em segundos
    cost = Column(String(20), default="0.00")
    
    # Relacionamentos
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    agent = relationship("Agent", back_populates="tasks")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status}')>"
