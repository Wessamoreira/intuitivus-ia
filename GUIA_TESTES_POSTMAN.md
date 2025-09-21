# 🚀 GUIA COMPLETO DE TESTES - POSTMAN
## Intuitivus Flow Studio - Sistema de Autenticação e APIs

---

## 📋 **CONFIGURAÇÃO INICIAL**

### **Base URL:** `http://localhost:8000`
### **Licenças de Teste Disponíveis:**
- `AIPL-2025-VNAK-X6EP`
- `AIPL-2025-H3EA-B8L3`
- `AIPL-2025-UDV1-ZXN5`
- `AIPL-2025-WJQH-U6G8`
- `AIPL-2025-OD0B-6D4O`

---

## 🔥 **PASSO A PASSO COMPLETO**

### **PASSO 1: VERIFICAR SAÚDE DA API**
```http
GET http://localhost:8000/health
```
**Resposta Esperada:**
```json
{
  "status": "healthy",
  "app_name": "Intuitivus Flow Studio",
  "version": "1.0.0",
  "timestamp": 1758464680.19995,
  "message": "API is running successfully!"
}
```

---

### **PASSO 2: REGISTRAR USUÁRIO**
```http
POST http://localhost:8000/api/v1/auth/register
Content-Type: application/json

{
  "name": "Seu Nome",
  "email": "seu@email.com",
  "password": "suasenha123",
  "license_key": "AIPL-2025-VNAK-X6EP",
  "company": "Sua Empresa"
}
```

**Resposta Esperada:**
```json
{
  "access_token": "299c5059-1904-4a3f-bf7d-ff638cd53b02",
  "refresh_token": "e524ea72-0c85-4477-ba75-aaf7b6a969e9",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 1,
    "name": "Seu Nome",
    "email": "seu@email.com",
    "company": "Sua Empresa"
  }
}
```

**⚠️ IMPORTANTE:** Copie o `access_token` para usar nos próximos testes!

---

### **PASSO 3: FAZER LOGIN**
```http
POST http://localhost:8000/api/v1/auth/login
Content-Type: application/json

{
  "email": "seu@email.com",
  "password": "suasenha123"
}
```

---

### **PASSO 4: OBTER INFORMAÇÕES DO USUÁRIO**
```http
GET http://localhost:8000/api/v1/auth/me
Authorization: Bearer SEU_ACCESS_TOKEN_AQUI
```

---

## 🤖 **TESTES DE AGENTES (CRUD COMPLETO)**

### **LISTAR AGENTES**
```http
GET http://localhost:8000/api/v1/agents
Authorization: Bearer SEU_ACCESS_TOKEN_AQUI
```

### **CRIAR AGENTE**
```http
POST http://localhost:8000/api/v1/agents
Authorization: Bearer SEU_ACCESS_TOKEN_AQUI
Content-Type: application/json

{
  "name": "Agente de Marketing",
  "description": "Agente especializado em campanhas de marketing digital",
  "type": "marketing",
  "status": "active",
  "config": {
    "platform": "google_ads",
    "budget": 1000,
    "target_audience": "jovens_adultos"
  }
}
```

### **OBTER AGENTE ESPECÍFICO**
```http
GET http://localhost:8000/api/v1/agents/1
Authorization: Bearer SEU_ACCESS_TOKEN_AQUI
```

### **ATUALIZAR AGENTE**
```http
PUT http://localhost:8000/api/v1/agents/1
Authorization: Bearer SEU_ACCESS_TOKEN_AQUI
Content-Type: application/json

{
  "name": "Agente de Marketing Avançado",
  "status": "paused",
  "config": {
    "platform": "meta_ads",
    "budget": 2000
  }
}
```

### **DELETAR AGENTE**
```http
DELETE http://localhost:8000/api/v1/agents/1
Authorization: Bearer SEU_ACCESS_TOKEN_AQUI
```

---

## 📢 **TESTES DE CAMPANHAS (CRUD COMPLETO)**

### **LISTAR CAMPANHAS**
```http
GET http://localhost:8000/api/v1/campaigns
Authorization: Bearer SEU_ACCESS_TOKEN_AQUI
```

### **CRIAR CAMPANHA**
```http
POST http://localhost:8000/api/v1/campaigns
Authorization: Bearer SEU_ACCESS_TOKEN_AQUI
Content-Type: application/json

{
  "name": "Campanha Black Friday",
  "description": "Campanha promocional para Black Friday",
  "agent_id": 1,
  "platform": "google_ads",
  "status": "active",
  "config": {
    "budget_daily": 500,
    "target_keywords": ["black friday", "promoção", "desconto"],
    "duration_days": 7
  }
}
```

### **OBTER CAMPANHA ESPECÍFICA**
```http
GET http://localhost:8000/api/v1/campaigns/1
Authorization: Bearer SEU_ACCESS_TOKEN_AQUI
```

### **ATUALIZAR CAMPANHA**
```http
PUT http://localhost:8000/api/v1/campaigns/1
Authorization: Bearer SEU_ACCESS_TOKEN_AQUI
Content-Type: application/json

{
  "status": "paused",
  "config": {
    "budget_daily": 800
  }
}
```

### **DELETAR CAMPANHA**
```http
DELETE http://localhost:8000/api/v1/campaigns/1
Authorization: Bearer SEU_ACCESS_TOKEN_AQUI
```

---

## ✅ **TESTES DE TAREFAS (CRUD COMPLETO)**

### **LISTAR TAREFAS**
```http
GET http://localhost:8000/api/v1/tasks
Authorization: Bearer SEU_ACCESS_TOKEN_AQUI
```

### **CRIAR TAREFA**
```http
POST http://localhost:8000/api/v1/tasks
Authorization: Bearer SEU_ACCESS_TOKEN_AQUI
Content-Type: application/json

{
  "title": "Criar conteúdo para redes sociais",
  "description": "Desenvolver posts para Instagram e Facebook da campanha Black Friday",
  "agent_id": 1,
  "priority": "high",
  "status": "pending"
}
```

### **OBTER TAREFA ESPECÍFICA**
```http
GET http://localhost:8000/api/v1/tasks/1
Authorization: Bearer SEU_ACCESS_TOKEN_AQUI
```

### **ATUALIZAR TAREFA**
```http
PUT http://localhost:8000/api/v1/tasks/1
Authorization: Bearer SEU_ACCESS_TOKEN_AQUI
Content-Type: application/json

{
  "status": "in_progress",
  "priority": "medium"
}
```

### **DELETAR TAREFA**
```http
DELETE http://localhost:8000/api/v1/tasks/1
Authorization: Bearer SEU_ACCESS_TOKEN_AQUI
```

---

## 📱 **TESTES DE WHATSAPP**

### **OBTER CONFIGURAÇÃO WHATSAPP**
```http
GET http://localhost:8000/api/v1/whatsapp/config
Authorization: Bearer SEU_ACCESS_TOKEN_AQUI
```

### **CONFIGURAR WHATSAPP**
```http
POST http://localhost:8000/api/v1/whatsapp/config
Authorization: Bearer SEU_ACCESS_TOKEN_AQUI
Content-Type: application/json

{
  "phone_number": "+5511999999999",
  "api_key": "sua_api_key_whatsapp",
  "webhook_url": "https://seu-webhook.com/whatsapp",
  "enabled": true
}
```

### **ENVIAR MENSAGEM WHATSAPP**
```http
POST http://localhost:8000/api/v1/whatsapp/send
Authorization: Bearer SEU_ACCESS_TOKEN_AQUI
Content-Type: application/json

{
  "to": "+5511888888888",
  "message": "Olá! Esta é uma mensagem de teste do sistema.",
  "type": "text"
}
```

---

## 📊 **TESTES DE RELATÓRIOS**

### **DASHBOARD ESTATÍSTICAS**
```http
GET http://localhost:8000/api/v1/reports/dashboard
Authorization: Bearer SEU_ACCESS_TOKEN_AQUI
```

**Resposta Esperada:**
```json
{
  "stats": {
    "total_agents": 2,
    "active_agents": 1,
    "total_campaigns": 3,
    "active_campaigns": 2,
    "total_tasks": 5,
    "completed_tasks": 2,
    "pending_tasks": 3,
    "user_info": {
      "name": "Seu Nome",
      "email": "seu@email.com",
      "license_type": "pro",
      "company": "Sua Empresa"
    }
  }
}
```

---

## 🔧 **COMANDOS PARA INICIAR O SISTEMA**

### **Backend:**
```bash
cd backend
python3 app/main_simple.py
```

### **Frontend:**
```bash
npm run dev
```

### **Verificar Status:**
```bash
# Backend
curl http://localhost:8000/health

# Frontend
curl http://localhost:3000
```

---

## 🎯 **SEQUÊNCIA RECOMENDADA DE TESTES**

1. **✅ Verificar saúde da API**
2. **👤 Registrar usuário**
3. **🔐 Fazer login**
4. **📋 Obter info do usuário**
5. **🤖 Criar agente**
6. **📢 Criar campanha (usando ID do agente)**
7. **✅ Criar tarefa (usando ID do agente)**
8. **📱 Configurar WhatsApp**
9. **📊 Verificar dashboard**
10. **🔄 Testar atualizações (PUT)**
11. **🗑️ Testar exclusões (DELETE)**

---

## ⚠️ **CÓDIGOS DE ERRO COMUNS**

- **401 Unauthorized:** Token inválido ou expirado
- **403 Forbidden:** Acesso negado (recurso não pertence ao usuário)
- **404 Not Found:** Recurso não encontrado
- **400 Bad Request:** Dados inválidos no request

---

## 🔑 **DICAS IMPORTANTES**

1. **Sempre use o token** nos headers de autenticação
2. **Tokens expiram em 30 minutos** - faça login novamente se necessário
3. **Cada usuário só vê seus próprios recursos** (agentes, campanhas, tarefas)
4. **Use diferentes licenças** para criar múltiplos usuários de teste
5. **IDs são sequenciais** - use 1, 2, 3... para testes

---

## 🚀 **SISTEMA TOTALMENTE FUNCIONAL!**

✅ **Autenticação JWT**
✅ **CRUD Completo de Agentes**
✅ **CRUD Completo de Campanhas**
✅ **CRUD Completo de Tarefas**
✅ **Integração WhatsApp**
✅ **Relatórios e Analytics**
✅ **Segurança por Usuário**
✅ **Validação de Licenças**
