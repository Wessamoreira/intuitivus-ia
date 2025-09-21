# 🚀 Intuitivus Flow Studio

**Plataforma SaaS para Criação e Gerenciamento de Agentes de IA Autônomos**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/react-18.0+-61dafb.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-00a393.svg)](https://fastapi.tiangolo.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178c6.svg)](https://www.typescriptlang.org/)

Uma plataforma moderna para criar, configurar e gerenciar agentes de IA autônomos com recursos avançados de automação de campanhas de marketing.

## 🌟 Funcionalidades

- ✅ **Agentes de IA Autônomos**: Criação e configuração de agentes inteligentes
- ✅ **Automação de Campanhas**: Integração com Google Ads, Meta Ads, TikTok Ads
- ✅ **Dashboard Analytics**: Métricas em tempo real e relatórios detalhados
- ✅ **API RESTful**: Backend robusto com FastAPI
- ✅ **Interface Moderna**: Frontend React com TypeScript e Tailwind CSS
- ✅ **Testes Automatizados**: Cobertura > 80% com pytest e Vitest
- ✅ **Monitoramento**: Observabilidade completa com OpenTelemetry
- ✅ **CI/CD**: Pipeline automatizado com GitHub Actions
- ✅ **Segurança**: Autenticação JWT, HTTPS, CORS configurado

## 🏗️ Arquitetura

### Backend (Python/FastAPI)
- **Framework**: FastAPI com async/await
- **Banco de Dados**: PostgreSQL com SQLAlchemy
- **Cache**: Redis para performance
- **Testes**: pytest com cobertura completa
- **Monitoramento**: Métricas, logs estruturados, health checks

### Frontend (React/TypeScript)
- **Framework**: React 18 com TypeScript
- **Build Tool**: Vite para desenvolvimento rápido
- **UI Components**: Radix UI + Tailwind CSS
- **Estado**: Zustand para gerenciamento de estado
- **Testes**: Vitest + React Testing Library + Playwright

## 🚀 URLs de Acesso

### 🖥️ **Desenvolvimento Local**
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### 🌐 **Produção** (Configurar após deploy)
- **Frontend**: https://app.intuitivus-flow.com
- **Backend API**: https://api.intuitivus-flow.com
- **Status Page**: https://status.intuitivus-flow.com

## ⚡ Início Rápido

### 1️⃣ **Método Automático (Recomendado)**
```bash
# Clone o repositório
git clone <YOUR_GIT_URL>
cd intuitivus-flow-studio-main

# Inicie tudo automaticamente
./start-services.sh
```

### 2️⃣ **Método Manual**
```bash
# Backend (Terminal 1)
cd backend
python3 -m uvicorn app.main_simple:app --host 0.0.0.0 --port 8000 --reload

# Frontend (Terminal 2)
npm install
npm run dev
```

### 3️⃣ **Parar Serviços**
```bash
# Automático
./stop-services.sh

# Manual
# Ctrl+C em cada terminal
```

## 🧪 Executar Testes

### **Frontend**
```bash
# Testes unitários
npm run test

# Testes E2E
npm run test:e2e

# Cobertura
npm run test:coverage
```

### **Backend**
```bash
cd backend
pip install -r requirements-test.txt
pytest tests/ -v --cov=app
```

### **Teste de Comunicação**
```bash
# Teste direto (mais rápido)
node test-communication.js
```

## 📋 Licenças e Termos

- **Licença**: MIT License (ver [LICENSE](./LICENSE))
- **Termos de Serviço**: [TERMS_OF_SERVICE.md](./TERMS_OF_SERVICE.md)
- **Política de Privacidade**: [PRIVACY_POLICY.md](./PRIVACY_POLICY.md)

## 📖 Documentação Técnica

- **Fase 4 Concluída**: [FASE_4_CONCLUIDA.md](./FASE_4_CONCLUIDA.md)
- **Próximos Passos**: [PLANO_IMPLEMENTACAO_PROXIMOS_PASSOS.md](./PLANO_IMPLEMENTACAO_PROXIMOS_PASSOS.md)
- **Frameworks de Teste**: [FRAMEWORKS_TESTE_IMPLEMENTADOS.md](./FRAMEWORKS_TESTE_IMPLEMENTADOS.md)

## 🛠️ Como Editar o Código

There are several ways of editing your application.

**Use Lovable**

Simply visit the [Lovable Project](https://lovable.dev/projects/425767af-f57e-4e04-b991-f637e9a7a29e) and start prompting.

Changes made via Lovable will be committed automatically to this repo.

**Use your preferred IDE**

If you want to work locally using your own IDE, you can clone this repo and push changes. Pushed changes will also be reflected in Lovable.

The only requirement is having Node.js & npm installed - [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating)

Follow these steps:

```sh
# Step 1: Clone the repository using the project's Git URL.
git clone <YOUR_GIT_URL>

# Step 2: Navigate to the project directory.
cd <YOUR_PROJECT_NAME>

# Step 3: Install the necessary dependencies.
npm i

# Step 4: Start the development server with auto-reloading and an instant preview.
npm run dev
```

**Edit a file directly in GitHub**

- Navigate to the desired file(s).
- Click the "Edit" button (pencil icon) at the top right of the file view.
- Make your changes and commit the changes.

**Use GitHub Codespaces**

- Navigate to the main page of your repository.
- Click on the "Code" button (green button) near the top right.
- Select the "Codespaces" tab.
- Click on "New codespace" to launch a new Codespace environment.
- Edit files directly within the Codespace and commit and push your changes once you're done.

## What technologies are used for this project?

This project is built with:

- Vite
- TypeScript
- React
- shadcn-ui
- Tailwind CSS

## How can I deploy this project?

Simply open [Lovable](https://lovable.dev/projects/425767af-f57e-4e04-b991-f637e9a7a29e) and click on Share -> Publish.

## Can I connect a custom domain to my Lovable project?

Yes, you can!

To connect a domain, navigate to Project > Settings > Domains and click Connect Domain.

Read more here: [Setting up a custom domain](https://docs.lovable.dev/features/custom-domain#custom-domain)
