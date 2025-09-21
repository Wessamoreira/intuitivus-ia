#!/bin/bash

# 🚀 Script de Inicialização - Intuitivus Flow Studio
# Inicia backend e frontend automaticamente

echo "🚀 INICIANDO INTUITIVUS FLOW STUDIO"
echo "=================================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para verificar se porta está em uso
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        return 0
    else
        return 1
    fi
}

# Verificar dependências
echo -e "${BLUE}📋 Verificando dependências...${NC}"

# Verificar Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js não encontrado. Instale Node.js primeiro.${NC}"
    exit 1
fi

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 não encontrado. Instale Python3 primeiro.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Dependências verificadas${NC}"

# Verificar se as portas estão livres
echo -e "${BLUE}🔍 Verificando portas...${NC}"

if check_port 8000; then
    echo -e "${YELLOW}⚠️  Porta 8000 já está em uso (Backend)${NC}"
    echo -e "${YELLOW}   Parando processo existente...${NC}"
    pkill -f "uvicorn.*8000" || true
    sleep 2
fi

if check_port 5173; then
    echo -e "${YELLOW}⚠️  Porta 5173 já está em uso (Frontend)${NC}"
    echo -e "${YELLOW}   Parando processo existente...${NC}"
    pkill -f "vite.*5173" || true
    sleep 2
fi

echo -e "${GREEN}✅ Portas liberadas${NC}"

# Instalar dependências se necessário
echo -e "${BLUE}📦 Verificando dependências do projeto...${NC}"

if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 Instalando dependências do frontend...${NC}"
    npm install
fi

if [ ! -d "backend/venv" ]; then
    echo -e "${YELLOW}🐍 Criando ambiente virtual Python...${NC}"
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements-base.txt
    cd ..
fi

echo -e "${GREEN}✅ Dependências instaladas${NC}"

# Iniciar Backend
echo -e "${BLUE}🔧 Iniciando Backend (FastAPI)...${NC}"
cd backend
python3 -m uvicorn app.main_simple:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Aguardar backend inicializar
echo -e "${YELLOW}⏳ Aguardando backend inicializar...${NC}"
sleep 5

# Verificar se backend está rodando
if check_port 8000; then
    echo -e "${GREEN}✅ Backend rodando na porta 8000${NC}"
else
    echo -e "${RED}❌ Falha ao iniciar backend${NC}"
    exit 1
fi

# Iniciar Frontend
echo -e "${BLUE}⚛️  Iniciando Frontend (React)...${NC}"
npm run dev &
FRONTEND_PID=$!

# Aguardar frontend inicializar
echo -e "${YELLOW}⏳ Aguardando frontend inicializar...${NC}"
sleep 8

# Verificar se frontend está rodando
if check_port 5173; then
    echo -e "${GREEN}✅ Frontend rodando na porta 5173${NC}"
else
    echo -e "${RED}❌ Falha ao iniciar frontend${NC}"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Testar comunicação
echo -e "${BLUE}🧪 Testando comunicação...${NC}"
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✅ Backend respondendo${NC}"
else
    echo -e "${RED}❌ Backend não está respondendo${NC}"
fi

# Sucesso!
echo ""
echo -e "${GREEN}🎉 INTUITIVUS FLOW STUDIO INICIADO COM SUCESSO!${NC}"
echo "=============================================="
echo ""
echo -e "${BLUE}📱 URLs de Acesso:${NC}"
echo -e "   Frontend: ${GREEN}http://localhost:5173${NC}"
echo -e "   Backend:  ${GREEN}http://localhost:8000${NC}"
echo -e "   API Docs: ${GREEN}http://localhost:8000/docs${NC}"
echo -e "   Health:   ${GREEN}http://localhost:8000/health${NC}"
echo ""
echo -e "${BLUE}🔧 Processos:${NC}"
echo -e "   Backend PID:  ${BACKEND_PID}"
echo -e "   Frontend PID: ${FRONTEND_PID}"
echo ""
echo -e "${YELLOW}💡 Para parar os serviços:${NC}"
echo -e "   ${BLUE}./stop-services.sh${NC} ou ${BLUE}Ctrl+C${NC}"
echo ""
echo -e "${BLUE}🌐 Abrindo navegador...${NC}"

# Abrir navegador (macOS)
if command -v open &> /dev/null; then
    sleep 2
    open http://localhost:5173
fi

# Aguardar interrupção
echo -e "${YELLOW}⏳ Serviços rodando... Pressione Ctrl+C para parar${NC}"

# Trap para capturar Ctrl+C
trap 'echo -e "\n${YELLOW}🛑 Parando serviços...${NC}"; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo -e "${GREEN}✅ Serviços parados${NC}"; exit 0' INT

# Manter script rodando
wait
