#!/bin/bash

# 🛑 Script para Parar Serviços - Intuitivus Flow Studio

echo "🛑 PARANDO INTUITIVUS FLOW STUDIO"
echo "================================"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parar Backend (porta 8000)
echo -e "${BLUE}🔧 Parando Backend...${NC}"
if pgrep -f "uvicorn.*8000" > /dev/null; then
    pkill -f "uvicorn.*8000"
    echo -e "${GREEN}✅ Backend parado${NC}"
else
    echo -e "${YELLOW}⚠️  Backend não estava rodando${NC}"
fi

# Parar Frontend (porta 5173)
echo -e "${BLUE}⚛️  Parando Frontend...${NC}"
if pgrep -f "vite.*5173" > /dev/null; then
    pkill -f "vite.*5173"
    echo -e "${GREEN}✅ Frontend parado${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend não estava rodando${NC}"
fi

# Verificar se as portas foram liberadas
sleep 2

if ! lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null; then
    echo -e "${GREEN}✅ Porta 8000 liberada${NC}"
else
    echo -e "${RED}❌ Porta 8000 ainda em uso${NC}"
fi

if ! lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null; then
    echo -e "${GREEN}✅ Porta 5173 liberada${NC}"
else
    echo -e "${RED}❌ Porta 5173 ainda em uso${NC}"
fi

echo ""
echo -e "${GREEN}🎉 SERVIÇOS PARADOS COM SUCESSO!${NC}"
echo ""
