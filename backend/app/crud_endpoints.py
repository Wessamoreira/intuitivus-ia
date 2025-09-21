"""
CRUD Endpoints para o sistema completo
"""

from fastapi import HTTPException, Depends
from typing import Dict, Any
import time
import logging

logger = logging.getLogger(__name__)

# Importar dependências do main_complete
from .main_complete import app, get_current_user, agents_db, campaigns_db, tasks_db, whatsapp_configs_db
from .main_complete import AgentCreate, AgentUpdate, CampaignCreate, TaskCreate, WhatsAppConfig

# CRUD de Agentes
@app.get("/api/v1/agents")
async def get_agents(current_user: dict = Depends(get_current_user)):
    """Listar todos os agentes do usuário"""
    user_agents = [agent for agent in agents_db.values() if agent["user_id"] == current_user["id"]]
    return {"agents": user_agents, "total": len(user_agents)}

@app.post("/api/v1/agents")
async def create_agent(agent: AgentCreate, current_user: dict = Depends(get_current_user)):
    """Criar novo agente"""
    agent_id = len(agents_db) + 1
    agent_data = {
        "id": agent_id,
        "user_id": current_user["id"],
        "name": agent.name,
        "description": agent.description,
        "type": agent.type,
        "status": agent.status,
        "config": agent.config,
        "created_at": time.time(),
        "updated_at": time.time()
    }
    
    agents_db[agent_id] = agent_data
    logger.info(f"Agente criado: {agent.name} por {current_user['email']}")
    
    return {"message": "Agente criado com sucesso", "agent": agent_data}

@app.get("/api/v1/agents/{agent_id}")
async def get_agent(agent_id: int, current_user: dict = Depends(get_current_user)):
    """Obter agente específico"""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agente não encontrado")
    
    agent = agents_db[agent_id]
    if agent["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    return {"agent": agent}

@app.put("/api/v1/agents/{agent_id}")
async def update_agent(agent_id: int, agent_update: AgentUpdate, current_user: dict = Depends(get_current_user)):
    """Atualizar agente"""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agente não encontrado")
    
    agent = agents_db[agent_id]
    if agent["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    # Atualizar campos fornecidos
    update_data = agent_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        agent[field] = value
    
    agent["updated_at"] = time.time()
    
    logger.info(f"Agente {agent_id} atualizado por {current_user['email']}")
    return {"message": "Agente atualizado com sucesso", "agent": agent}

@app.delete("/api/v1/agents/{agent_id}")
async def delete_agent(agent_id: int, current_user: dict = Depends(get_current_user)):
    """Deletar agente"""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agente não encontrado")
    
    agent = agents_db[agent_id]
    if agent["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    del agents_db[agent_id]
    
    logger.info(f"Agente {agent_id} deletado por {current_user['email']}")
    return {"message": "Agente deletado com sucesso"}

# CRUD de Campanhas
@app.get("/api/v1/campaigns")
async def get_campaigns(current_user: dict = Depends(get_current_user)):
    """Listar todas as campanhas do usuário"""
    user_campaigns = [campaign for campaign in campaigns_db.values() if campaign["user_id"] == current_user["id"]]
    return {"campaigns": user_campaigns, "total": len(user_campaigns)}

@app.post("/api/v1/campaigns")
async def create_campaign(campaign: CampaignCreate, current_user: dict = Depends(get_current_user)):
    """Criar nova campanha"""
    # Verificar se o agente existe e pertence ao usuário
    if campaign.agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agente não encontrado")
    
    agent = agents_db[campaign.agent_id]
    if agent["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Agente não pertence ao usuário")
    
    campaign_id = len(campaigns_db) + 1
    campaign_data = {
        "id": campaign_id,
        "user_id": current_user["id"],
        "agent_id": campaign.agent_id,
        "name": campaign.name,
        "description": campaign.description,
        "platform": campaign.platform,
        "status": campaign.status,
        "config": campaign.config,
        "created_at": time.time(),
        "updated_at": time.time()
    }
    
    campaigns_db[campaign_id] = campaign_data
    logger.info(f"Campanha criada: {campaign.name} por {current_user['email']}")
    
    return {"message": "Campanha criada com sucesso", "campaign": campaign_data}

@app.get("/api/v1/campaigns/{campaign_id}")
async def get_campaign(campaign_id: int, current_user: dict = Depends(get_current_user)):
    """Obter campanha específica"""
    if campaign_id not in campaigns_db:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")
    
    campaign = campaigns_db[campaign_id]
    if campaign["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    return {"campaign": campaign}

@app.put("/api/v1/campaigns/{campaign_id}")
async def update_campaign(campaign_id: int, campaign_update: dict, current_user: dict = Depends(get_current_user)):
    """Atualizar campanha"""
    if campaign_id not in campaigns_db:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")
    
    campaign = campaigns_db[campaign_id]
    if campaign["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    # Atualizar campos fornecidos
    for field, value in campaign_update.items():
        if field in ["name", "description", "platform", "status", "config"]:
            campaign[field] = value
    
    campaign["updated_at"] = time.time()
    
    logger.info(f"Campanha {campaign_id} atualizada por {current_user['email']}")
    return {"message": "Campanha atualizada com sucesso", "campaign": campaign}

@app.delete("/api/v1/campaigns/{campaign_id}")
async def delete_campaign(campaign_id: int, current_user: dict = Depends(get_current_user)):
    """Deletar campanha"""
    if campaign_id not in campaigns_db:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")
    
    campaign = campaigns_db[campaign_id]
    if campaign["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    del campaigns_db[campaign_id]
    
    logger.info(f"Campanha {campaign_id} deletada por {current_user['email']}")
    return {"message": "Campanha deletada com sucesso"}

# CRUD de Tarefas
@app.get("/api/v1/tasks")
async def get_tasks(current_user: dict = Depends(get_current_user)):
    """Listar todas as tarefas do usuário"""
    user_tasks = [task for task in tasks_db.values() if task["user_id"] == current_user["id"]]
    return {"tasks": user_tasks, "total": len(user_tasks)}

@app.post("/api/v1/tasks")
async def create_task(task: TaskCreate, current_user: dict = Depends(get_current_user)):
    """Criar nova tarefa"""
    # Verificar se o agente existe e pertence ao usuário
    if task.agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agente não encontrado")
    
    agent = agents_db[task.agent_id]
    if agent["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Agente não pertence ao usuário")
    
    task_id = len(tasks_db) + 1
    task_data = {
        "id": task_id,
        "user_id": current_user["id"],
        "agent_id": task.agent_id,
        "title": task.title,
        "description": task.description,
        "priority": task.priority,
        "status": task.status,
        "created_at": time.time(),
        "updated_at": time.time()
    }
    
    tasks_db[task_id] = task_data
    logger.info(f"Tarefa criada: {task.title} por {current_user['email']}")
    
    return {"message": "Tarefa criada com sucesso", "task": task_data}

@app.get("/api/v1/tasks/{task_id}")
async def get_task(task_id: int, current_user: dict = Depends(get_current_user)):
    """Obter tarefa específica"""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    
    task = tasks_db[task_id]
    if task["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    return {"task": task}

@app.put("/api/v1/tasks/{task_id}")
async def update_task(task_id: int, task_update: dict, current_user: dict = Depends(get_current_user)):
    """Atualizar tarefa"""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    
    task = tasks_db[task_id]
    if task["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    # Atualizar campos fornecidos
    for field, value in task_update.items():
        if field in ["title", "description", "priority", "status"]:
            task[field] = value
    
    task["updated_at"] = time.time()
    
    logger.info(f"Tarefa {task_id} atualizada por {current_user['email']}")
    return {"message": "Tarefa atualizada com sucesso", "task": task}

@app.delete("/api/v1/tasks/{task_id}")
async def delete_task(task_id: int, current_user: dict = Depends(get_current_user)):
    """Deletar tarefa"""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    
    task = tasks_db[task_id]
    if task["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    del tasks_db[task_id]
    
    logger.info(f"Tarefa {task_id} deletada por {current_user['email']}")
    return {"message": "Tarefa deletada com sucesso"}

# WhatsApp Integration
@app.get("/api/v1/whatsapp/config")
async def get_whatsapp_config(current_user: dict = Depends(get_current_user)):
    """Obter configuração do WhatsApp"""
    config = whatsapp_configs_db.get(current_user["id"])
    if not config:
        return {"config": None, "message": "Configuração não encontrada"}
    
    return {"config": config}

@app.post("/api/v1/whatsapp/config")
async def create_whatsapp_config(config: WhatsAppConfig, current_user: dict = Depends(get_current_user)):
    """Criar/atualizar configuração do WhatsApp"""
    config_data = {
        "user_id": current_user["id"],
        "phone_number": config.phone_number,
        "api_key": config.api_key,
        "webhook_url": config.webhook_url,
        "enabled": config.enabled,
        "created_at": time.time(),
        "updated_at": time.time()
    }
    
    whatsapp_configs_db[current_user["id"]] = config_data
    logger.info(f"Configuração WhatsApp criada/atualizada por {current_user['email']}")
    
    return {"message": "Configuração WhatsApp salva com sucesso", "config": config_data}

@app.post("/api/v1/whatsapp/send")
async def send_whatsapp_message(message_data: dict, current_user: dict = Depends(get_current_user)):
    """Enviar mensagem via WhatsApp"""
    config = whatsapp_configs_db.get(current_user["id"])
    if not config or not config["enabled"]:
        raise HTTPException(status_code=400, detail="Configuração WhatsApp não encontrada ou desabilitada")
    
    # Simular envio de mensagem
    import uuid
    logger.info(f"Mensagem WhatsApp enviada por {current_user['email']}: {message_data}")
    
    return {
        "message": "Mensagem enviada com sucesso",
        "message_id": str(uuid.uuid4()),
        "status": "sent",
        "timestamp": time.time()
    }

# Relatórios e Analytics
@app.get("/api/v1/reports/dashboard")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    """Obter estatísticas do dashboard"""
    user_agents = [agent for agent in agents_db.values() if agent["user_id"] == current_user["id"]]
    user_campaigns = [campaign for campaign in campaigns_db.values() if campaign["user_id"] == current_user["id"]]
    user_tasks = [task for task in tasks_db.values() if task["user_id"] == current_user["id"]]
    
    stats = {
        "total_agents": len(user_agents),
        "active_agents": len([a for a in user_agents if a["status"] == "active"]),
        "total_campaigns": len(user_campaigns),
        "active_campaigns": len([c for c in user_campaigns if c["status"] == "active"]),
        "total_tasks": len(user_tasks),
        "completed_tasks": len([t for t in user_tasks if t["status"] == "completed"]),
        "pending_tasks": len([t for t in user_tasks if t["status"] == "pending"]),
        "user_info": {
            "name": current_user["name"],
            "email": current_user["email"],
            "license_type": current_user["license_type"],
            "company": current_user["company"]
        }
    }
    
    return {"stats": stats}
