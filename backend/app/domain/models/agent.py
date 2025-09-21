from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.infrastructure.db.database import Base

class AgentStatus(str, enum.Enum):
    """Status do agente"""
    ACTIVE = "active"      # Ativo e processando tarefas
    IDLE = "idle"          # Inativo mas disponível
    PAUSED = "paused"      # Pausado pelo usuário
    ERROR = "error"        # Com erro
    TRAINING = "training"  # Em treinamento

class AgentCategory(str, enum.Enum):
    """Categoria do agente"""
    MARKETING = "marketing"
    SUPPORT = "support"
    CONTENT = "content"
    ANALYTICS = "analytics"
    SALES = "sales"
    GENERAL = "general"

class Agent(Base):
    """Modelo de agente de IA"""
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    role = Column(String(255), nullable=False)  # Ex: "Marketing Specialist"
    
    # Configurações
    category = Column(Enum(AgentCategory), default=AgentCategory.GENERAL)
    status = Column(Enum(AgentStatus), default=AgentStatus.IDLE)
    
    # Configurações de IA
    llm_provider = Column(String(50), nullable=False)  # openai, anthropic, google, etc
    llm_model = Column(String(100), nullable=False)    # gpt-4, claude-3, gemini-pro, etc
    
    # Instruções e comportamento
    system_prompt = Column(Text, nullable=False)
    instructions = Column(Text, nullable=True)
    
    # Configurações avançadas (JSON)
    settings = Column(JSON, nullable=True)  # temperature, max_tokens, etc
    
    # Métricas
    tasks_completed = Column(Integer, default=0)
    tasks_failed = Column(Integer, default=0)
    total_tokens_used = Column(Integer, default=0)
    total_cost = Column(String(20), default="0.00")  # Em formato decimal string
    
    # Relacionamentos
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="agents")
    
    tasks = relationship("Task", back_populates="agent")
    conversations = relationship("Conversation", back_populates="agent")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_active = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<Agent(id={self.id}, name='{self.name}', status='{self.status}')>"
    
    @property
    def success_rate(self) -> float:
        """Calcula a taxa de sucesso do agente"""
        total_tasks = self.tasks_completed + self.tasks_failed
        if total_tasks == 0:
            return 0.0
        return (self.tasks_completed / total_tasks) * 100
    
    @property
    def is_available(self) -> bool:
        """Verifica se o agente está disponível para tarefas"""
        return self.status in [AgentStatus.ACTIVE, AgentStatus.IDLE]
