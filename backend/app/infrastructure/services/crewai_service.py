import asyncio
import time
import uuid
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
import logging

from crewai import Agent as CrewAgent, Task as CrewTask, Crew
from crewai.llm import LLM

from app.application.interfaces.agent_service import IAgentService, AgentTask, TaskResult, CrewExecution, TaskStatus
from app.infrastructure.repositories.agent_repository import AgentRepository
from app.infrastructure.services.llm_registry import llm_registry
from app.application.interfaces.llm_service import LLMMessage
from app.domain.models.agent import AgentStatus

logger = logging.getLogger(__name__)

class CrewAIService(IAgentService):
    """Implementação do serviço de agentes usando CrewAI"""
    
    def __init__(self):
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.task_results: Dict[str, TaskResult] = {}
    
    async def execute_task(
        self,
        task: AgentTask,
        user_id: int,
        db: Session
    ) -> TaskResult:
        """Executa uma tarefa individual usando CrewAI"""
        start_time = time.time()
        
        try:
            # Buscar agente no banco
            agent_repo = AgentRepository(db)
            agent = agent_repo.get_by_id(task.agent_id)
            
            if not agent or agent.user_id != user_id:
                raise ValueError(f"Agent {task.agent_id} not found or not owned by user")
            
            if not agent.is_available:
                raise ValueError(f"Agent {task.agent_id} is not available")
            
            # Marcar agente como ativo
            agent_repo.update(task.agent_id, {"status": AgentStatus.ACTIVE})
            
            # Criar LLM personalizado que usa nosso registry
            custom_llm = CustomLLM(
                user_id=user_id,
                agent=agent,
                db=db
            )
            
            # Criar agente CrewAI
            crew_agent = CrewAgent(
                role=agent.role,
                goal=f"Execute the task: {task.title}",
                backstory=agent.description or f"You are a {agent.role} specialized in {agent.category.value}",
                llm=custom_llm,
                verbose=True,
                allow_delegation=False
            )
            
            # Criar tarefa CrewAI
            crew_task = CrewTask(
                description=task.description,
                expected_output=task.expected_output or "A detailed response addressing the task requirements",
                agent=crew_agent
            )
            
            # Criar crew com um único agente
            crew = Crew(
                agents=[crew_agent],
                tasks=[crew_task],
                verbose=True
            )
            
            # Executar crew
            logger.info(f"Starting task execution for agent {agent.id}")
            result = crew.kickoff()
            
            execution_time = time.time() - start_time
            
            # Atualizar métricas do agente
            agent_repo.update_metrics(
                agent_id=task.agent_id,
                task_completed=True,
                tokens_used=custom_llm.total_tokens_used,
                cost=custom_llm.total_cost
            )
            
            # Marcar agente como idle
            agent_repo.update(task.agent_id, {"status": AgentStatus.IDLE})
            
            task_result = TaskResult(
                task_id=task.id,
                agent_id=task.agent_id,
                status=TaskStatus.COMPLETED,
                output=str(result),
                tokens_used=custom_llm.total_tokens_used,
                execution_time=execution_time,
                cost=custom_llm.total_cost,
                metadata={
                    "agent_role": agent.role,
                    "llm_provider": agent.llm_provider,
                    "llm_model": agent.llm_model
                }
            )
            
            logger.info(f"Task {task.id} completed successfully")
            return task_result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Marcar agente como idle em caso de erro
            try:
                agent_repo.update_metrics(
                    agent_id=task.agent_id,
                    task_completed=False,
                    tokens_used=0,
                    cost=0.0
                )
                agent_repo.update(task.agent_id, {"status": AgentStatus.IDLE})
            except:
                pass
            
            error_msg = str(e)
            logger.error(f"Task {task.id} failed: {error_msg}")
            
            return TaskResult(
                task_id=task.id,
                agent_id=task.agent_id,
                status=TaskStatus.FAILED,
                error_message=error_msg,
                execution_time=execution_time
            )
    
    async def execute_crew(
        self,
        crew_execution: CrewExecution,
        user_id: int,
        db: Session
    ) -> CrewExecution:
        """Executa uma crew (equipe) de agentes"""
        start_time = time.time()
        
        try:
            agent_repo = AgentRepository(db)
            
            # Verificar se todos os agentes existem e pertencem ao usuário
            crew_agents = []
            custom_llms = []
            
            for agent_id in crew_execution.agents:
                agent = agent_repo.get_by_id(agent_id)
                if not agent or agent.user_id != user_id:
                    raise ValueError(f"Agent {agent_id} not found or not owned by user")
                
                if not agent.is_available:
                    raise ValueError(f"Agent {agent_id} is not available")
                
                # Marcar agente como ativo
                agent_repo.update(agent_id, {"status": AgentStatus.ACTIVE})
                
                # Criar LLM personalizado
                custom_llm = CustomLLM(
                    user_id=user_id,
                    agent=agent,
                    db=db
                )
                custom_llms.append(custom_llm)
                
                # Criar agente CrewAI
                crew_agent = CrewAgent(
                    role=agent.role,
                    goal=f"Work collaboratively to complete assigned tasks",
                    backstory=agent.description or f"You are a {agent.role} specialized in {agent.category.value}",
                    llm=custom_llm,
                    verbose=True,
                    allow_delegation=True
                )
                crew_agents.append(crew_agent)
            
            # Criar tarefas CrewAI
            crew_tasks = []
            for i, task in enumerate(crew_execution.tasks):
                # Atribuir agente à tarefa (ou deixar o CrewAI decidir)
                assigned_agent = None
                if i < len(crew_agents):
                    assigned_agent = crew_agents[i]
                
                crew_task = CrewTask(
                    description=task.description,
                    expected_output=task.expected_output or "A detailed response addressing the task requirements",
                    agent=assigned_agent
                )
                crew_tasks.append(crew_task)
            
            # Criar e executar crew
            crew = Crew(
                agents=crew_agents,
                tasks=crew_tasks,
                verbose=True,
                process="sequential"  # Ou "hierarchical" para estrutura mais complexa
            )
            
            logger.info(f"Starting crew execution with {len(crew_agents)} agents")
            result = crew.kickoff()
            
            execution_time = time.time() - start_time
            total_tokens = sum(llm.total_tokens_used for llm in custom_llms)
            total_cost = sum(llm.total_cost for llm in custom_llms)
            
            # Atualizar métricas de todos os agentes
            for i, agent_id in enumerate(crew_execution.agents):
                if i < len(custom_llms):
                    agent_repo.update_metrics(
                        agent_id=agent_id,
                        task_completed=True,
                        tokens_used=custom_llms[i].total_tokens_used,
                        cost=custom_llms[i].total_cost
                    )
                agent_repo.update(agent_id, {"status": AgentStatus.IDLE})
            
            # Criar resultados das tarefas
            task_results = []
            for i, task in enumerate(crew_execution.tasks):
                task_result = TaskResult(
                    task_id=task.id,
                    agent_id=task.agent_id,
                    status=TaskStatus.COMPLETED,
                    output=str(result) if i == len(crew_execution.tasks) - 1 else f"Completed task {i+1}",
                    tokens_used=custom_llms[i].total_tokens_used if i < len(custom_llms) else 0,
                    execution_time=execution_time / len(crew_execution.tasks),
                    cost=custom_llms[i].total_cost if i < len(custom_llms) else 0.0
                )
                task_results.append(task_result)
            
            crew_execution.status = TaskStatus.COMPLETED
            crew_execution.results = task_results
            crew_execution.total_cost = total_cost
            crew_execution.total_time = execution_time
            
            logger.info(f"Crew execution completed successfully")
            return crew_execution
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Marcar todos os agentes como idle em caso de erro
            for agent_id in crew_execution.agents:
                try:
                    agent_repo.update(agent_id, {"status": AgentStatus.IDLE})
                except:
                    pass
            
            error_msg = str(e)
            logger.error(f"Crew execution failed: {error_msg}")
            
            crew_execution.status = TaskStatus.FAILED
            crew_execution.total_time = execution_time
            
            return crew_execution
    
    async def get_task_status(self, task_id: str) -> TaskStatus:
        """Obtém status de uma tarefa"""
        if task_id in self.task_results:
            return self.task_results[task_id].status
        elif task_id in self.running_tasks:
            return TaskStatus.RUNNING
        else:
            return TaskStatus.PENDING
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancela uma tarefa em execução"""
        if task_id in self.running_tasks:
            task = self.running_tasks[task_id]
            task.cancel()
            del self.running_tasks[task_id]
            
            self.task_results[task_id] = TaskResult(
                task_id=task_id,
                agent_id=0,
                status=TaskStatus.CANCELLED
            )
            return True
        return False

class CustomLLM(LLM):
    """LLM personalizado que usa nosso registry multi-LLM"""
    
    def __init__(self, user_id: int, agent, db: Session):
        self.user_id = user_id
        self.agent = agent
        self.db = db
        self.total_tokens_used = 0
        self.total_cost = 0.0
        
        # Configurar modelo baseado no agente
        super().__init__(
            model=agent.llm_model,
            temperature=agent.settings.get("temperature", 0.7) if agent.settings else 0.7,
            max_tokens=agent.settings.get("max_tokens", 2000) if agent.settings else 2000
        )
    
    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs) -> str:
        """Método chamado pelo CrewAI para gerar resposta"""
        try:
            # Converter prompt para formato de mensagens
            messages = [
                LLMMessage(role="system", content=self.agent.system_prompt),
                LLMMessage(role="user", content=prompt)
            ]
            
            # Usar nosso registry para fazer a chamada
            import asyncio
            loop = asyncio.get_event_loop()
            
            response = loop.run_until_complete(
                llm_registry.chat_completion(
                    user_id=self.user_id,
                    messages=messages,
                    preferred_provider=self.agent.llm_provider,
                    preferred_model=self.agent.llm_model,
                    db=self.db,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    **kwargs
                )
            )
            
            # Atualizar métricas
            self.total_tokens_used += response.tokens_used
            self.total_cost += response.cost
            
            return response.content
            
        except Exception as e:
            logger.error(f"CustomLLM error: {e}")
            return f"Error generating response: {str(e)}"
    
    @property
    def _llm_type(self) -> str:
        return "custom_multi_llm"

# Instância global do serviço
crewai_service = CrewAIService()
