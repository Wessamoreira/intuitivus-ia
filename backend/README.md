# AI Agents Platform - Backend

Backend da plataforma SaaS para criação e gerenciamento de agentes de IA autônomos, desenvolvido com FastAPI seguindo a arquitetura Ports & Adapters (Hexagonal).

## 🏗️ Arquitetura

```
app/
├── api/v1/                 # Camada de Interface (API)
│   ├── endpoints/          # Endpoints da API
│   ├── schemas/            # Schemas Pydantic
│   └── router.py           # Router principal
├── application/            # Camada de Aplicação
│   ├── interfaces/         # Ports (interfaces)
│   └── use_cases/          # Use Cases
├── domain/                 # Camada de Domínio
│   └── models/             # Entidades do negócio
├── infrastructure/         # Camada de Infraestrutura
│   ├── db/                 # Configuração do banco
│   ├── repositories/       # Repositories (adapters)
│   ├── services/           # Serviços externos
│   └── security/           # Autenticação e segurança
├── core/                   # Configurações centrais
└── main.py                 # Ponto de entrada
```

## 🚀 Configuração do Ambiente

### 1. Pré-requisitos

- Python 3.9+
- PostgreSQL 12+
- Redis (opcional, para cache)

### 2. Instalação

```bash
# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas configurações
```

### 3. Configuração do Banco de Dados

```bash
# Criar banco PostgreSQL
createdb ai_agents_platform

# Executar migrações
alembic upgrade head
```

### 4. Gerar Licenças de Teste

```bash
# Gerar uma licença
python scripts/generate_test_license.py

# Gerar múltiplas licenças
python scripts/generate_test_license.py 5
```

## 🔧 Execução

### Desenvolvimento

```bash
# Executar servidor de desenvolvimento
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Ou usando o script principal
python app/main.py
```

### Produção

```bash
# Executar com Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 📚 API Documentation

Após iniciar o servidor, acesse:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/api/v1/openapi.json

## 🔐 Autenticação

A API usa JWT (JSON Web Tokens) para autenticação:

1. **Registro**: `POST /api/v1/auth/register` - Requer chave de licença válida
2. **Login**: `POST /api/v1/auth/login` - Retorna access_token e refresh_token
3. **Refresh**: `POST /api/v1/auth/refresh` - Renova o access_token
4. **Perfil**: `GET /api/v1/auth/me` - Informações do usuário atual

### Exemplo de Uso

```bash
# Registro
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "João Silva",
    "email": "joao@exemplo.com",
    "password": "senha123456",
    "license_key": "AIPL-2024-XXXX-XXXX"
  }'

# Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "joao@exemplo.com",
    "password": "senha123456"
  }'

# Usar token nas requisições
curl -X GET "http://localhost:8000/api/v1/agents/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🤖 Endpoints de Agentes

### Principais Endpoints

- `GET /api/v1/agents/` - Listar agentes
- `POST /api/v1/agents/` - Criar agente
- `GET /api/v1/agents/{id}` - Obter agente
- `PUT /api/v1/agents/{id}` - Atualizar agente
- `DELETE /api/v1/agents/{id}` - Deletar agente
- `PATCH /api/v1/agents/{id}/status` - Alterar status
- `POST /api/v1/agents/{id}/clone` - Clonar agente
- `GET /api/v1/agents/stats` - Estatísticas

### Exemplo de Criação de Agente

```json
{
  "name": "Marketing Expert",
  "description": "Especialista em marketing digital",
  "role": "Marketing Specialist",
  "category": "marketing",
  "llm_provider": "openai",
  "llm_model": "gpt-4",
  "system_prompt": "Você é um especialista em marketing digital...",
  "instructions": "Sempre foque em ROI e métricas...",
  "settings": {
    "temperature": 0.7,
    "max_tokens": 2000
  }
}
```

## 🗄️ Banco de Dados

### Modelos Principais

- **User**: Usuários da plataforma
- **License**: Licenças de acesso
- **Agent**: Agentes de IA
- **APIKey**: Chaves de API dos usuários
- **Task**: Tarefas executadas pelos agentes
- **Conversation**: Conversas do WhatsApp
- **Message**: Mensagens das conversas
- **Campaign**: Campanhas de marketing

### Migrações

```bash
# Criar nova migração
alembic revision --autogenerate -m "Descrição da mudança"

# Aplicar migrações
alembic upgrade head

# Reverter migração
alembic downgrade -1
```

## 🔒 Segurança

### Recursos Implementados

- **JWT Authentication**: Tokens de acesso e refresh
- **Password Hashing**: Bcrypt para senhas
- **API Key Encryption**: Fernet para chaves de API
- **CORS**: Configurado para frontend
- **Rate Limiting**: (TODO)
- **Input Validation**: Pydantic schemas

### Variáveis de Ambiente Críticas

```env
SECRET_KEY=sua-chave-super-secreta-muito-longa
ENCRYPTION_KEY=chave-para-criptografar-apis
DATABASE_URL=postgresql://user:pass@host:port/db
```

## 🧪 Testes

```bash
# Executar testes
pytest

# Executar com cobertura
pytest --cov=app tests/

# Executar testes específicos
pytest tests/test_auth.py -v
```

## 📦 Deploy

### Usando Docker

```dockerfile
# TODO: Criar Dockerfile
```

### Variáveis de Ambiente para Produção

```env
DEBUG=false
SECRET_KEY=chave-super-secreta-producao
DATABASE_URL=postgresql://user:pass@host:port/db
REDIS_URL=redis://host:port
```

## 🔧 Desenvolvimento

### Estrutura de Commits

```bash
git commit -m "feat: adicionar endpoint de agentes"
git commit -m "fix: corrigir validação de licença"
git commit -m "docs: atualizar README"
```

### Linting e Formatação

```bash
# Formatar código
black app/
isort app/

# Verificar linting
flake8 app/
```

## 📈 Monitoramento

### Health Checks

- `GET /health` - Status geral da aplicação
- `GET /api/v1/health` - Status da API v1

### Logs

Os logs são configurados automaticamente e incluem:
- Requisições HTTP
- Erros de aplicação
- Queries do banco de dados (em modo debug)

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para detalhes.
