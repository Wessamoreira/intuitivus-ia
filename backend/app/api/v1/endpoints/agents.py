from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.infrastructure.db.database import get_db
from app.infrastructure.repositories.agent_repository import AgentRepository
from app.infrastructure.security.dependencies import get_current_active_user
from app.api.v1.schemas.agent import (
    AgentCreate, AgentUpdate, Agent, AgentSummary, AgentStats, 
    AgentStatusUpdate, AgentStatusEnum, AgentCategoryEnum
)
from app.api.v1.schemas.user import User

router = APIRouter()

@router.post("/", response_model=Agent, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_data: AgentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Cria um novo agente de IA.
    
    - **name**: Nome do agente
    - **description**: Descrição do agente (opcional)
    - **role**: Função do agente (ex: "Marketing Specialist")
    - **category**: Categoria do agente
    - **llm_provider**: Provedor do LLM (openai, anthropic, google, etc.)
    - **llm_model**: Modelo específico (gpt-4, claude-3, gemini-pro, etc.)
    - **system_prompt**: Prompt do sistema que define o comportamento
    - **instructions**: Instruções adicionais (opcional)
    - **settings**: Configurações avançadas como temperature, max_tokens (opcional)
    """
    agent_repo = AgentRepository(db)
    
    # Adicionar user_id aos dados
    agent_dict = agent_data.dict()
    agent_dict["user_id"] = current_user.id
    
    # Criar agente
    agent = agent_repo.create(agent_dict)
    
    return agent

@router.get("/", response_model=List[AgentSummary])
async def list_agents(
    status: Optional[AgentStatusEnum] = Query(None, description="Filtrar por status"),
    category: Optional[AgentCategoryEnum] = Query(None, description="Filtrar por categoria"),
    skip: int = Query(0, ge=0, description="Número de registros para pular"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Lista os agentes do usuário atual.
    
    - **status**: Filtrar por status (opcional)
    - **category**: Filtrar por categoria (opcional)
    - **skip**: Paginação - registros para pular
    - **limit**: Paginação - máximo de registros
    """
    agent_repo = AgentRepository(db)
    
    if status:
        agents = agent_repo.get_by_status(current_user.id, status)
    elif category:
        agents = agent_repo.get_by_category(current_user.id, category)
    else:
        agents = agent_repo.get_by_user_id(current_user.id, skip, limit)
    
    # Adicionar success_rate calculado
    agents_with_rate = []
    for agent in agents:
        agent_dict = agent.__dict__.copy()
        agent_dict["success_rate"] = agent.success_rate
        agents_with_rate.append(AgentSummary(**agent_dict))
    
    return agents_with_rate

@router.get("/stats", response_model=AgentStats)
async def get_agent_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Obtém estatísticas dos agentes do usuário.
    """
    agent_repo = AgentRepository(db)
    stats = agent_repo.get_user_stats(current_user.id)
    return stats

@router.get("/{agent_id}", response_model=Agent)
async def get_agent(
    agent_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Obtém detalhes de um agente específico.
    """
    agent_repo = AgentRepository(db)
    agent = agent_repo.get_by_id(agent_id)
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Verificar se o agente pertence ao usuário
    if agent.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return agent

@router.put("/{agent_id}", response_model=Agent)
async def update_agent(
    agent_id: int,
    agent_data: AgentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Atualiza um agente existente.
    """
    agent_repo = AgentRepository(db)
    agent = agent_repo.get_by_id(agent_id)
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Verificar se o agente pertence ao usuário
    if agent.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Atualizar apenas campos fornecidos
    update_data = agent_data.dict(exclude_unset=True)
    updated_agent = agent_repo.update(agent_id, update_data)
    
    return updated_agent

@router.patch("/{agent_id}/status", response_model=Agent)
async def update_agent_status(
    agent_id: int,
    status_data: AgentStatusUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Atualiza o status de um agente (ativar, pausar, etc.).
    """
    agent_repo = AgentRepository(db)
    agent = agent_repo.get_by_id(agent_id)
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Verificar se o agente pertence ao usuário
    if agent.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Atualizar status usando métodos específicos
    if status_data.status == AgentStatusEnum.ACTIVE:
        updated_agent = agent_repo.activate(agent_id)
    elif status_data.status == AgentStatusEnum.PAUSED:
        updated_agent = agent_repo.pause(agent_id)
    elif status_data.status == AgentStatusEnum.IDLE:
        updated_agent = agent_repo.deactivate(agent_id)
    else:
        updated_agent = agent_repo.update(agent_id, {"status": status_data.status})
    
    return updated_agent

@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Deleta um agente.
    """
    agent_repo = AgentRepository(db)
    agent = agent_repo.get_by_id(agent_id)
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Verificar se o agente pertence ao usuário
    if agent.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Verificar se o agente não está ativo
    if agent.status == AgentStatusEnum.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete active agent. Please pause it first."
        )
    
    agent_repo.delete(agent_id)

@router.post("/{agent_id}/clone", response_model=Agent, status_code=status.HTTP_201_CREATED)
async def clone_agent(
    agent_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Clona um agente existente.
    """
    agent_repo = AgentRepository(db)
    agent = agent_repo.get_by_id(agent_id)
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Verificar se o agente pertence ao usuário
    if agent.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Criar dados para o clone
    clone_data = {
        "name": f"{agent.name} - Cópia",
        "description": agent.description,
        "role": agent.role,
        "category": agent.category,
        "llm_provider": agent.llm_provider,
        "llm_model": agent.llm_model,
        "system_prompt": agent.system_prompt,
        "instructions": agent.instructions,
        "settings": agent.settings,
        "user_id": current_user.id,
        "status": AgentStatusEnum.IDLE  # Clone sempre inicia inativo
    }
    
    cloned_agent = agent_repo.create(clone_data)
    return cloned_agent
