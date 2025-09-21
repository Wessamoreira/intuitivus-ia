from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime

from app.infrastructure.db.database import get_db
from app.infrastructure.repositories.agent_repository import AgentRepository
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.security.dependencies import get_current_active_user
from app.infrastructure.services.crewai_service import crewai_service
from app.application.interfaces.agent_service import AgentTask, CrewExecution as CrewExecutionInterface, TaskStatus
from app.api.v1.schemas.user import User
from app.api.v1.schemas.task import (
    TaskExecute, CrewExecute, TaskResult, TaskExecution, 
    CrewExecution, TaskStats, AgentPerformance, TaskCancel,
    TaskStatusEnum
)
from app.domain.models.task import Task as TaskModel, TaskStatus as TaskStatusModel, TaskPriority

router = APIRouter()

@router.post("/execute", response_model=TaskExecution, status_code=status.HTTP_201_CREATED)
async def execute_task(
    task_data: TaskExecute,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Executa uma tarefa individual com um agente específico.
    
    - **agent_id**: ID do agente que executará a tarefa
    - **title**: Título da tarefa
    - **description**: Descrição detalhada do que deve ser feito
    - **input_data**: Dados de entrada para a tarefa
    - **priority**: Prioridade da execução
    - **expected_output**: Descrição do resultado esperado
    """
    agent_repo = AgentRepository(db)
    
    # Verificar se o agente existe e pertence ao usuário
    agent = agent_repo.get_by_id(task_data.agent_id)
    if not agent or agent.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found or not owned by user"
        )
    
    if not agent.is_available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent is not available. Current status: {agent.status}"
        )
    
    # Criar ID único para a tarefa
    task_id = str(uuid.uuid4())
    
    # Criar registro da tarefa no banco
    task_record = TaskModel(
        title=task_data.title,
        description=task_data.description,
        priority=TaskPriority(task_data.priority.value),
        status=TaskStatusModel.PENDING,
        input_data=task_data.input_data,
        agent_id=task_data.agent_id
    )
    
    db.add(task_record)
    db.commit()
    db.refresh(task_record)
    
    # Criar tarefa para o CrewAI
    agent_task = AgentTask(
        id=task_id,
        title=task_data.title,
        description=task_data.description,
        input_data=task_data.input_data,
        agent_id=task_data.agent_id,
        priority=task_data.priority.value,
        expected_output=task_data.expected_output,
        tools=task_data.tools,
        context=task_data.context
    )
    
    # Executar tarefa em background
    background_tasks.add_task(
        _execute_task_background,
        agent_task,
        current_user.id,
        task_record.id,
        db
    )
    
    # Retornar informações da execução
    return TaskExecution(
        id=task_id,
        title=task_data.title,
        description=task_data.description,
        agent_id=task_data.agent_id,
        agent_name=agent.name,
        status=TaskStatusEnum.PENDING,
        priority=task_data.priority,
        input_data=task_data.input_data,
        created_at=datetime.utcnow()
    )

@router.post("/execute-crew", response_model=CrewExecution, status_code=status.HTTP_201_CREATED)
async def execute_crew(
    crew_data: CrewExecute,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Executa uma crew (equipe) de agentes trabalhando em colaboração.
    
    - **name**: Nome da crew
    - **description**: Descrição do objetivo da crew
    - **agent_ids**: Lista de IDs dos agentes participantes
    - **tasks**: Lista de tarefas para a crew executar
    - **process_type**: Tipo de processo (sequential ou hierarchical)
    """
    agent_repo = AgentRepository(db)
    
    # Verificar se todos os agentes existem e pertencem ao usuário
    agents = []
    for agent_id in crew_data.agent_ids:
        agent = agent_repo.get_by_id(agent_id)
        if not agent or agent.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found or not owned by user"
            )
        
        if not agent.is_available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Agent {agent.name} is not available. Status: {agent.status}"
            )
        
        agents.append(agent)
    
    # Criar ID único para a crew
    crew_id = str(uuid.uuid4())
    
    # Criar tarefas para o CrewAI
    agent_tasks = []
    task_executions = []
    
    for i, task_data in enumerate(crew_data.tasks):
        task_id = str(uuid.uuid4())
        
        # Criar registro da tarefa no banco
        task_record = TaskModel(
            title=task_data.title,
            description=task_data.description,
            priority=TaskPriority(task_data.priority.value),
            status=TaskStatusModel.PENDING,
            input_data=task_data.input_data,
            agent_id=task_data.agent_id if task_data.agent_id in crew_data.agent_ids else crew_data.agent_ids[0]
        )
        
        db.add(task_record)
        db.commit()
        db.refresh(task_record)
        
        agent_task = AgentTask(
            id=task_id,
            title=task_data.title,
            description=task_data.description,
            input_data=task_data.input_data,
            agent_id=task_data.agent_id if task_data.agent_id in crew_data.agent_ids else crew_data.agent_ids[0],
            priority=task_data.priority.value,
            expected_output=task_data.expected_output,
            tools=task_data.tools,
            context=task_data.context
        )
        
        agent_tasks.append(agent_task)
        
        # Criar execução da tarefa
        task_execution = TaskExecution(
            id=task_id,
            title=task_data.title,
            description=task_data.description,
            agent_id=agent_task.agent_id,
            agent_name=next(a.name for a in agents if a.id == agent_task.agent_id),
            status=TaskStatusEnum.PENDING,
            priority=task_data.priority,
            input_data=task_data.input_data,
            created_at=datetime.utcnow()
        )
        
        task_executions.append(task_execution)
    
    # Criar crew execution
    crew_execution = CrewExecutionInterface(
        crew_id=crew_id,
        tasks=agent_tasks,
        agents=crew_data.agent_ids,
        status=TaskStatus.PENDING
    )
    
    # Executar crew em background
    background_tasks.add_task(
        _execute_crew_background,
        crew_execution,
        current_user.id,
        db
    )
    
    # Retornar informações da execução
    return CrewExecution(
        id=crew_id,
        name=crew_data.name,
        description=crew_data.description,
        agent_ids=crew_data.agent_ids,
        agent_names=[agent.name for agent in agents],
        status=TaskStatusEnum.PENDING,
        process_type=crew_data.process_type,
        tasks=task_executions,
        created_at=datetime.utcnow()
    )

@router.get("/status/{task_id}", response_model=dict)
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Obtém o status atual de uma tarefa.
    """
    # Buscar no banco de dados
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    
    if not task:
        # Tentar buscar no serviço CrewAI
        status = await crewai_service.get_task_status(task_id)
        return {
            "task_id": task_id,
            "status": status.value,
            "message": "Task status from CrewAI service"
        }
    
    # Verificar se a tarefa pertence ao usuário (através do agente)
    if task.agent.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return {
        "task_id": task_id,
        "status": task.status.value,
        "title": task.title,
        "agent_name": task.agent.name,
        "created_at": task.created_at,
        "started_at": task.started_at,
        "completed_at": task.completed_at,
        "tokens_used": task.tokens_used,
        "cost": task.cost,
        "execution_time": task.execution_time
    }

@router.post("/cancel/{task_id}")
async def cancel_task(
    task_id: str,
    cancel_data: TaskCancel,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Cancela uma tarefa em execução.
    """
    # Buscar tarefa no banco
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Verificar se a tarefa pertence ao usuário
    if task.agent.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Verificar se a tarefa pode ser cancelada
    if task.status not in [TaskStatusModel.PENDING, TaskStatusModel.RUNNING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel task with status: {task.status}"
        )
    
    # Tentar cancelar no CrewAI
    cancelled = await crewai_service.cancel_task(task_id)
    
    # Atualizar status no banco
    task.status = TaskStatusModel.CANCELLED
    db.commit()
    
    return {
        "message": "Task cancelled successfully",
        "task_id": task_id,
        "cancelled_in_service": cancelled,
        "reason": cancel_data.reason
    }

@router.get("/stats", response_model=TaskStats)
async def get_task_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Obtém estatísticas das tarefas do usuário.
    """
    # Buscar todas as tarefas dos agentes do usuário
    tasks = db.query(TaskModel).join(TaskModel.agent).filter(
        TaskModel.agent.has(user_id=current_user.id)
    ).all()
    
    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t.status == TaskStatusModel.COMPLETED])
    failed_tasks = len([t for t in tasks if t.status == TaskStatusModel.FAILED])
    running_tasks = len([t for t in tasks if t.status == TaskStatusModel.RUNNING])
    
    total_tokens = sum(t.tokens_used for t in tasks)
    total_cost = sum(float(t.cost) for t in tasks)
    
    # Calcular tempo médio de execução
    completed_with_time = [t for t in tasks if t.execution_time and t.execution_time > 0]
    avg_time = sum(t.execution_time for t in completed_with_time) / len(completed_with_time) if completed_with_time else 0
    
    success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    return TaskStats(
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        failed_tasks=failed_tasks,
        running_tasks=running_tasks,
        total_tokens_used=total_tokens,
        total_cost=total_cost,
        average_execution_time=avg_time,
        success_rate=round(success_rate, 2)
    )

@router.get("/performance", response_model=List[AgentPerformance])
async def get_agent_performance(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Obtém performance individual de cada agente.
    """
    agent_repo = AgentRepository(db)
    agents = agent_repo.get_by_user_id(current_user.id)
    
    performance_list = []
    
    for agent in agents:
        # Buscar tarefas do agente
        tasks = db.query(TaskModel).filter(TaskModel.agent_id == agent.id).all()
        
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status == TaskStatusModel.COMPLETED])
        failed_tasks = len([t for t in tasks if t.status == TaskStatusModel.FAILED])
        
        success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        total_tokens = sum(t.tokens_used for t in tasks)
        total_cost = sum(float(t.cost) for t in tasks)
        
        # Tempo médio
        completed_with_time = [t for t in tasks if t.execution_time and t.execution_time > 0]
        avg_time = sum(t.execution_time for t in completed_with_time) / len(completed_with_time) if completed_with_time else 0
        
        performance = AgentPerformance(
            agent_id=agent.id,
            agent_name=agent.name,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            success_rate=round(success_rate, 2),
            total_tokens=total_tokens,
            total_cost=total_cost,
            average_time=avg_time
        )
        
        performance_list.append(performance)
    
    return performance_list

# Funções auxiliares para execução em background
async def _execute_task_background(
    agent_task: AgentTask,
    user_id: int,
    task_record_id: int,
    db: Session
):
    """Executa tarefa em background"""
    try:
        # Atualizar status para RUNNING
        task_record = db.query(TaskModel).filter(TaskModel.id == task_record_id).first()
        if task_record:
            task_record.status = TaskStatusModel.RUNNING
            task_record.started_at = datetime.utcnow()
            db.commit()
        
        # Executar tarefa
        result = await crewai_service.execute_task(agent_task, user_id, db)
        
        # Atualizar resultado no banco
        if task_record:
            task_record.status = TaskStatusModel(result.status.value)
            task_record.output_data = {"output": result.output}
            task_record.error_message = result.error_message
            task_record.tokens_used = result.tokens_used
            task_record.execution_time = result.execution_time
            task_record.cost = str(result.cost)
            task_record.completed_at = datetime.utcnow()
            db.commit()
            
    except Exception as e:
        # Atualizar erro no banco
        if task_record:
            task_record.status = TaskStatusModel.FAILED
            task_record.error_message = str(e)
            task_record.completed_at = datetime.utcnow()
            db.commit()

async def _execute_crew_background(
    crew_execution: CrewExecutionInterface,
    user_id: int,
    db: Session
):
    """Executa crew em background"""
    try:
        result = await crewai_service.execute_crew(crew_execution, user_id, db)
        # Resultado já é atualizado pelo serviço
    except Exception as e:
        # Log do erro
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Crew execution failed: {e}")
