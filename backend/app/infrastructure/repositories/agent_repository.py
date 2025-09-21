from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.domain.models.agent import Agent, AgentStatus, AgentCategory

class AgentRepository:
    """Repository para operações com agentes"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, agent_data: dict) -> Agent:
        """Cria um novo agente"""
        agent = Agent(**agent_data)
        self.db.add(agent)
        self.db.commit()
        self.db.refresh(agent)
        return agent
    
    def get_by_id(self, agent_id: int) -> Optional[Agent]:
        """Busca agente por ID"""
        return self.db.query(Agent).filter(Agent.id == agent_id).first()
    
    def get_by_user_id(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Agent]:
        """Lista agentes de um usuário"""
        return self.db.query(Agent).filter(
            Agent.user_id == user_id
        ).order_by(desc(Agent.created_at)).offset(skip).limit(limit).all()
    
    def get_by_status(self, user_id: int, status: AgentStatus) -> List[Agent]:
        """Lista agentes por status"""
        return self.db.query(Agent).filter(
            and_(Agent.user_id == user_id, Agent.status == status)
        ).all()
    
    def get_by_category(self, user_id: int, category: AgentCategory) -> List[Agent]:
        """Lista agentes por categoria"""
        return self.db.query(Agent).filter(
            and_(Agent.user_id == user_id, Agent.category == category)
        ).all()
    
    def get_active_agents(self, user_id: int) -> List[Agent]:
        """Lista agentes ativos de um usuário"""
        return self.get_by_status(user_id, AgentStatus.ACTIVE)
    
    def get_available_agents(self, user_id: int) -> List[Agent]:
        """Lista agentes disponíveis (ativos ou inativos)"""
        return self.db.query(Agent).filter(
            and_(
                Agent.user_id == user_id,
                Agent.status.in_([AgentStatus.ACTIVE, AgentStatus.IDLE])
            )
        ).all()
    
    def update(self, agent_id: int, agent_data: dict) -> Optional[Agent]:
        """Atualiza um agente"""
        agent = self.get_by_id(agent_id)
        if not agent:
            return None
        
        for field, value in agent_data.items():
            setattr(agent, field, value)
        
        self.db.commit()
        self.db.refresh(agent)
        return agent
    
    def delete(self, agent_id: int) -> bool:
        """Deleta um agente"""
        agent = self.get_by_id(agent_id)
        if not agent:
            return False
        
        self.db.delete(agent)
        self.db.commit()
        return True
    
    def activate(self, agent_id: int) -> Optional[Agent]:
        """Ativa um agente"""
        from datetime import datetime
        return self.update(agent_id, {
            "status": AgentStatus.ACTIVE,
            "last_active": datetime.utcnow()
        })
    
    def deactivate(self, agent_id: int) -> Optional[Agent]:
        """Desativa um agente"""
        return self.update(agent_id, {"status": AgentStatus.IDLE})
    
    def pause(self, agent_id: int) -> Optional[Agent]:
        """Pausa um agente"""
        return self.update(agent_id, {"status": AgentStatus.PAUSED})
    
    def update_metrics(self, agent_id: int, task_completed: bool, tokens_used: int, cost: float) -> Optional[Agent]:
        """Atualiza métricas do agente após execução de tarefa"""
        agent = self.get_by_id(agent_id)
        if not agent:
            return None
        
        if task_completed:
            agent.tasks_completed += 1
        else:
            agent.tasks_failed += 1
        
        agent.total_tokens_used += tokens_used
        agent.total_cost = str(float(agent.total_cost) + cost)
        
        from datetime import datetime
        agent.last_active = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(agent)
        return agent
    
    def get_user_stats(self, user_id: int) -> dict:
        """Obtém estatísticas dos agentes do usuário"""
        agents = self.get_by_user_id(user_id)
        
        total_agents = len(agents)
        active_agents = len([a for a in agents if a.status == AgentStatus.ACTIVE])
        total_tasks = sum(a.tasks_completed for a in agents)
        total_failed = sum(a.tasks_failed for a in agents)
        
        success_rate = 0
        if total_tasks + total_failed > 0:
            success_rate = (total_tasks / (total_tasks + total_failed)) * 100
        
        return {
            "total_agents": total_agents,
            "active_agents": active_agents,
            "idle_agents": len([a for a in agents if a.status == AgentStatus.IDLE]),
            "paused_agents": len([a for a in agents if a.status == AgentStatus.PAUSED]),
            "total_tasks_completed": total_tasks,
            "total_tasks_failed": total_failed,
            "overall_success_rate": round(success_rate, 2),
            "total_tokens_used": sum(a.total_tokens_used for a in agents),
            "total_cost": sum(float(a.total_cost) for a in agents)
        }
