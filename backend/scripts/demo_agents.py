#!/usr/bin/env python3
"""
Script de demonstração do sistema de agentes.
Mostra como criar agentes, adicionar chaves de API e executar tarefas.
"""

import asyncio
import httpx
import json
from typing import Dict, Any

# Configurações da API
API_BASE_URL = "http://localhost:8000/api/v1"

class AIAgentsDemo:
    def __init__(self):
        self.access_token = None
        self.client = httpx.AsyncClient()
    
    async def register_user(self, license_key: str) -> Dict[str, Any]:
        """Registra um novo usuário"""
        print("🔐 Registrando usuário...")
        
        user_data = {
            "name": "Demo User",
            "email": "demo@aiagents.com",
            "password": "demo123456",
            "license_key": license_key,
            "company": "AI Agents Demo"
        }
        
        response = await self.client.post(
            f"{API_BASE_URL}/auth/register",
            json=user_data
        )
        
        if response.status_code == 201:
            result = response.json()
            self.access_token = result["access_token"]
            print("✅ Usuário registrado com sucesso!")
            return result
        else:
            print(f"❌ Erro no registro: {response.text}")
            return None
    
    async def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """Faz login do usuário"""
        print("🔑 Fazendo login...")
        
        login_data = {
            "email": email,
            "password": password
        }
        
        response = await self.client.post(
            f"{API_BASE_URL}/auth/login",
            json=login_data
        )
        
        if response.status_code == 200:
            result = response.json()
            self.access_token = result["access_token"]
            print("✅ Login realizado com sucesso!")
            return result
        else:
            print(f"❌ Erro no login: {response.text}")
            return None
    
    def _get_headers(self) -> Dict[str, str]:
        """Retorna headers com token de autenticação"""
        return {"Authorization": f"Bearer {self.access_token}"}
    
    async def add_api_key(self, provider: str, api_key: str, name: str) -> Dict[str, Any]:
        """Adiciona uma chave de API"""
        print(f"🔑 Adicionando chave de API para {provider}...")
        
        api_key_data = {
            "name": name,
            "provider": provider,
            "api_key": api_key,
            "priority": 1,
            "monthly_limit": "100.00"
        }
        
        response = await self.client.post(
            f"{API_BASE_URL}/api-keys/",
            json=api_key_data,
            headers=self._get_headers()
        )
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Chave de API {provider} adicionada com sucesso!")
            return result
        else:
            print(f"❌ Erro ao adicionar chave: {response.text}")
            return None
    
    async def create_agent(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria um novo agente"""
        print(f"🤖 Criando agente: {agent_data['name']}...")
        
        response = await self.client.post(
            f"{API_BASE_URL}/agents/",
            json=agent_data,
            headers=self._get_headers()
        )
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Agente '{result['name']}' criado com sucesso!")
            return result
        else:
            print(f"❌ Erro ao criar agente: {response.text}")
            return None
    
    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Executa uma tarefa"""
        print(f"⚡ Executando tarefa: {task_data['title']}...")
        
        response = await self.client.post(
            f"{API_BASE_URL}/tasks/execute",
            json=task_data,
            headers=self._get_headers()
        )
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Tarefa '{result['title']}' iniciada!")
            return result
        else:
            print(f"❌ Erro ao executar tarefa: {response.text}")
            return None
    
    async def execute_crew(self, crew_data: Dict[str, Any]) -> Dict[str, Any]:
        """Executa uma crew de agentes"""
        print(f"👥 Executando crew: {crew_data['name']}...")
        
        response = await self.client.post(
            f"{API_BASE_URL}/tasks/execute-crew",
            json=crew_data,
            headers=self._get_headers()
        )
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Crew '{result['name']}' iniciada!")
            return result
        else:
            print(f"❌ Erro ao executar crew: {response.text}")
            return None
    
    async def check_task_status(self, task_id: str) -> Dict[str, Any]:
        """Verifica status de uma tarefa"""
        response = await self.client.get(
            f"{API_BASE_URL}/tasks/status/{task_id}",
            headers=self._get_headers()
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Erro ao verificar status: {response.text}")
            return None
    
    async def get_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas"""
        print("📊 Obtendo estatísticas...")
        
        # Stats de agentes
        agents_response = await self.client.get(
            f"{API_BASE_URL}/agents/stats",
            headers=self._get_headers()
        )
        
        # Stats de tarefas
        tasks_response = await self.client.get(
            f"{API_BASE_URL}/tasks/stats",
            headers=self._get_headers()
        )
        
        # Stats de API keys
        keys_response = await self.client.get(
            f"{API_BASE_URL}/api-keys/stats",
            headers=self._get_headers()
        )
        
        return {
            "agents": agents_response.json() if agents_response.status_code == 200 else None,
            "tasks": tasks_response.json() if tasks_response.status_code == 200 else None,
            "api_keys": keys_response.json() if keys_response.status_code == 200 else None
        }
    
    async def run_demo(self, license_key: str, openai_key: str = None):
        """Executa demonstração completa"""
        print("🚀 Iniciando demonstração do AI Agents Platform!")
        print("=" * 50)
        
        # 1. Registrar usuário
        await self.register_user(license_key)
        
        # 2. Adicionar chave de API (se fornecida)
        if openai_key:
            await self.add_api_key("openai", openai_key, "Demo OpenAI Key")
        
        # 3. Criar agentes
        marketing_agent = await self.create_agent({
            "name": "Marketing Expert",
            "description": "Especialista em marketing digital e criação de campanhas",
            "role": "Marketing Specialist",
            "category": "marketing",
            "llm_provider": "openai",
            "llm_model": "gpt-4",
            "system_prompt": "Você é um especialista em marketing digital com foco em ROI e conversões. Sempre forneça estratégias práticas e baseadas em dados.",
            "instructions": "Foque em métricas, KPIs e resultados mensuráveis.",
            "settings": {
                "temperature": 0.7,
                "max_tokens": 2000
            }
        })
        
        content_agent = await self.create_agent({
            "name": "Content Creator",
            "description": "Criador de conteúdo para redes sociais e blogs",
            "role": "Content Writer",
            "category": "content",
            "llm_provider": "openai",
            "llm_model": "gpt-4",
            "system_prompt": "Você é um criador de conteúdo criativo e engajante. Crie textos que conectem com a audiência e gerem engajamento.",
            "instructions": "Use linguagem acessível e inclua call-to-actions quando apropriado.",
            "settings": {
                "temperature": 0.8,
                "max_tokens": 1500
            }
        })
        
        # 4. Executar tarefa individual
        if marketing_agent:
            task_result = await self.execute_task({
                "agent_id": marketing_agent["id"],
                "title": "Estratégia de Marketing para E-commerce",
                "description": "Crie uma estratégia completa de marketing digital para um e-commerce de roupas fitness, incluindo canais, orçamento e métricas de sucesso.",
                "input_data": {
                    "business_type": "e-commerce",
                    "niche": "roupas fitness",
                    "budget": "R$ 10.000/mês",
                    "target_audience": "mulheres 25-40 anos"
                },
                "priority": "high",
                "expected_output": "Estratégia detalhada com canais, táticas, orçamento e KPIs"
            })
            
            if task_result:
                # Aguardar um pouco e verificar status
                await asyncio.sleep(5)
                status = await self.check_task_status(task_result["id"])
                print(f"📋 Status da tarefa: {status}")
        
        # 5. Executar crew (se ambos agentes foram criados)
        if marketing_agent and content_agent:
            crew_result = await self.execute_crew({
                "name": "Campanha de Lançamento",
                "description": "Criar campanha completa de lançamento de produto",
                "agent_ids": [marketing_agent["id"], content_agent["id"]],
                "process_type": "sequential",
                "tasks": [
                    {
                        "agent_id": marketing_agent["id"],
                        "title": "Estratégia da Campanha",
                        "description": "Definir estratégia geral da campanha de lançamento",
                        "input_data": {"product": "Tênis de corrida premium"},
                        "priority": "high",
                        "expected_output": "Estratégia completa com canais e táticas"
                    },
                    {
                        "agent_id": content_agent["id"],
                        "title": "Conteúdo da Campanha",
                        "description": "Criar conteúdo para a campanha baseado na estratégia",
                        "input_data": {"product": "Tênis de corrida premium"},
                        "priority": "high",
                        "expected_output": "Posts para redes sociais e copy para anúncios"
                    }
                ]
            })
            
            if crew_result:
                print(f"👥 Crew executando com {len(crew_result['tasks'])} tarefas")
        
        # 6. Mostrar estatísticas
        await asyncio.sleep(3)
        stats = await self.get_stats()
        
        print("\n📊 ESTATÍSTICAS FINAIS:")
        print("=" * 30)
        
        if stats["agents"]:
            print(f"🤖 Agentes: {stats['agents']['total_agents']} total, {stats['agents']['active_agents']} ativos")
        
        if stats["tasks"]:
            print(f"⚡ Tarefas: {stats['tasks']['total_tasks']} total, {stats['tasks']['completed_tasks']} concluídas")
            print(f"💰 Custo total: ${stats['tasks']['total_cost']:.4f}")
        
        if stats["api_keys"]:
            print(f"🔑 Chaves API: {stats['api_keys']['total_keys']} total, {stats['api_keys']['active_keys']} ativas")
        
        print("\n🎉 Demonstração concluída!")
        
        await self.client.aclose()

async def main():
    """Função principal"""
    print("🤖 AI Agents Platform - Demonstração")
    print("Certifique-se de que o backend está rodando em http://localhost:8000")
    print()
    
    # Solicitar dados do usuário
    license_key = input("Digite uma chave de licença válida: ").strip()
    openai_key = input("Digite sua chave OpenAI (opcional): ").strip()
    
    if not license_key:
        print("❌ Chave de licença é obrigatória!")
        return
    
    # Executar demonstração
    demo = AIAgentsDemo()
    await demo.run_demo(license_key, openai_key if openai_key else None)

if __name__ == "__main__":
    asyncio.run(main())
