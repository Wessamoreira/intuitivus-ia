# 🚀 AI Agents Platform - Guia de Deploy

Este guia contém instruções completas para fazer o deploy da plataforma em produção.

## 📋 Pré-requisitos

### Infraestrutura Necessária
- **Servidor**: VPS/Cloud com mínimo 2GB RAM, 2 vCPUs
- **Banco de Dados**: PostgreSQL 12+
- **Redis**: Para cache e filas (opcional)
- **Domínio**: Para HTTPS e webhooks
- **SSL**: Certificado válido (Let's Encrypt recomendado)

### Contas e APIs Necessárias
- **Meta WhatsApp Business**: Para integração WhatsApp
- **OpenAI/Anthropic/Google**: Chaves de API dos LLMs
- **Resend/SendGrid**: Para envio de emails
- **Kiwify/Hotmart**: Para webhooks de licenciamento

## 🔧 Configuração do Ambiente

### 1. Preparar Servidor

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências
sudo apt install -y python3.9 python3.9-venv python3-pip postgresql postgresql-contrib nginx redis-server

# Instalar Node.js (para frontend)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### 2. Configurar PostgreSQL

```bash
# Acessar PostgreSQL
sudo -u postgres psql

# Criar banco e usuário
CREATE DATABASE ai_agents_platform;
CREATE USER ai_agents_user WITH PASSWORD 'sua_senha_super_segura';
GRANT ALL PRIVILEGES ON DATABASE ai_agents_platform TO ai_agents_user;
\q
```

### 3. Configurar Aplicação

```bash
# Clonar repositório
git clone <seu-repositorio> /var/www/ai-agents-platform
cd /var/www/ai-agents-platform

# Backend
cd backend
python3.9 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
npm run build
```

### 4. Configurar Variáveis de Ambiente

```bash
# Criar arquivo de produção
sudo nano /var/www/ai-agents-platform/backend/.env
```

```env
# Produção
DEBUG=false
APP_NAME=AI Agents Platform
VERSION=1.0.0

# Servidor
HOST=0.0.0.0
PORT=8000

# Banco de dados
DATABASE_URL=postgresql://ai_agents_user:sua_senha@localhost:5432/ai_agents_platform

# Segurança (GERE CHAVES SEGURAS!)
SECRET_KEY=sua-chave-jwt-super-secreta-256-bits
ENCRYPTION_KEY=sua-chave-criptografia-fernet

# CORS
BACKEND_CORS_ORIGINS=["https://seudominio.com"]

# WhatsApp Business
META_WHATSAPP_TOKEN=seu_token_meta
META_WHATSAPP_PHONE_ID=seu_phone_id
META_WHATSAPP_VERIFY_TOKEN=seu_verify_token

# Email
RESEND_API_KEY=seu_resend_key
FROM_EMAIL=noreply@seudominio.com

# Webhooks
KIWIFY_WEBHOOK_SECRET=seu_secret_kiwify
HOTMART_WEBHOOK_SECRET=seu_secret_hotmart

# Redis
REDIS_URL=redis://localhost:6379
```

## 🗄️ Configurar Banco de Dados

```bash
cd /var/www/ai-agents-platform/backend
source venv/bin/activate

# Executar migrações
alembic upgrade head

# Gerar licenças de teste
python scripts/generate_test_license.py 10
```

## 🌐 Configurar Nginx

```bash
sudo nano /etc/nginx/sites-available/ai-agents-platform
```

```nginx
server {
    listen 80;
    server_name seudominio.com www.seudominio.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name seudominio.com www.seudominio.com;

    ssl_certificate /etc/letsencrypt/live/seudominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/seudominio.com/privkey.pem;

    # Frontend (React)
    location / {
        root /var/www/ai-agents-platform/frontend/dist;
        try_files $uri $uri/ /index.html;
        
        # Cache estático
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Docs
    location /docs {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Ativar site
sudo ln -s /etc/nginx/sites-available/ai-agents-platform /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 🔒 Configurar SSL (Let's Encrypt)

```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx

# Obter certificado
sudo certbot --nginx -d seudominio.com -d www.seudominio.com

# Renovação automática
sudo crontab -e
# Adicionar: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 🚀 Configurar Serviços Systemd

### Backend Service

```bash
sudo nano /etc/systemd/system/ai-agents-backend.service
```

```ini
[Unit]
Description=AI Agents Platform Backend
After=network.target postgresql.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/var/www/ai-agents-platform/backend
Environment=PATH=/var/www/ai-agents-platform/backend/venv/bin
ExecStart=/var/www/ai-agents-platform/backend/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 127.0.0.1:8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

### Celery Worker (para tarefas em background)

```bash
sudo nano /etc/systemd/system/ai-agents-worker.service
```

```ini
[Unit]
Description=AI Agents Platform Worker
After=network.target redis.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/var/www/ai-agents-platform/backend
Environment=PATH=/var/www/ai-agents-platform/backend/venv/bin
ExecStart=/var/www/ai-agents-platform/backend/venv/bin/celery -A app.worker worker --loglevel=info
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
# Ativar e iniciar serviços
sudo systemctl enable ai-agents-backend ai-agents-worker
sudo systemctl start ai-agents-backend ai-agents-worker

# Verificar status
sudo systemctl status ai-agents-backend
sudo systemctl status ai-agents-worker
```

## 📱 Configurar WhatsApp Business

### 1. Meta Business Account
1. Acesse [Meta Business](https://business.facebook.com)
2. Crie uma conta business
3. Configure WhatsApp Business API
4. Obtenha: `access_token`, `phone_number_id`, `verify_token`

### 2. Configurar Webhook
- **URL**: `https://seudominio.com/api/v1/whatsapp/webhook`
- **Verify Token**: O mesmo configurado no `.env`
- **Campos**: `messages`, `message_deliveries`, `message_reads`

### 3. Testar Integração
```bash
# Verificar webhook
curl "https://seudominio.com/api/v1/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=seu_verify_token&hub.challenge=123"

# Deve retornar: 123
```

## 🔍 Monitoramento e Logs

### Configurar Logs

```bash
# Criar diretório de logs
sudo mkdir -p /var/log/ai-agents-platform
sudo chown www-data:www-data /var/log/ai-agents-platform

# Configurar logrotate
sudo nano /etc/logrotate.d/ai-agents-platform
```

```
/var/log/ai-agents-platform/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
}
```

### Scripts de Monitoramento

```bash
# Script de health check
sudo nano /usr/local/bin/ai-agents-health.sh
```

```bash
#!/bin/bash
# Health check script

API_URL="https://seudominio.com/api/v1/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $API_URL)

if [ $RESPONSE -eq 200 ]; then
    echo "✅ API is healthy"
    exit 0
else
    echo "❌ API is down (HTTP $RESPONSE)"
    # Reiniciar serviço se necessário
    sudo systemctl restart ai-agents-backend
    exit 1
fi
```

```bash
chmod +x /usr/local/bin/ai-agents-health.sh

# Adicionar ao crontab para verificar a cada 5 minutos
sudo crontab -e
# Adicionar: */5 * * * * /usr/local/bin/ai-agents-health.sh >> /var/log/ai-agents-platform/health.log 2>&1
```

## 🔐 Segurança

### Firewall
```bash
# Configurar UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### Backup Automático
```bash
# Script de backup
sudo nano /usr/local/bin/ai-agents-backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/ai-agents-platform"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup do banco
pg_dump -h localhost -U ai_agents_user ai_agents_platform | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Backup dos arquivos
tar -czf $BACKUP_DIR/files_$DATE.tar.gz /var/www/ai-agents-platform

# Manter apenas últimos 7 backups
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

```bash
chmod +x /usr/local/bin/ai-agents-backup.sh

# Backup diário às 2h
sudo crontab -e
# Adicionar: 0 2 * * * /usr/local/bin/ai-agents-backup.sh >> /var/log/ai-agents-platform/backup.log 2>&1
```

## 🧪 Testes de Produção

### 1. Testar API
```bash
# Health check
curl https://seudominio.com/api/v1/health

# Registro de usuário
curl -X POST "https://seudominio.com/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Teste User",
    "email": "teste@exemplo.com",
    "password": "senha123456",
    "license_key": "AIPL-2024-XXXX-XXXX"
  }'
```

### 2. Testar Frontend
- Acesse `https://seudominio.com`
- Teste registro e login
- Verifique todas as páginas
- Teste responsividade

### 3. Testar WhatsApp
- Envie mensagem para o número configurado
- Verifique se agente responde automaticamente
- Teste diferentes tipos de mensagem

## 📊 Monitoramento de Performance

### Métricas Importantes
- **CPU/RAM**: Manter < 80%
- **Banco de Dados**: Conexões, queries lentas
- **API**: Response time, error rate
- **WhatsApp**: Taxa de resposta, tempo de resposta

### Alertas Recomendados
- API down > 5 minutos
- CPU > 90% por 10 minutos
- Disco > 85%
- Erro rate > 5%

## 🔄 Atualizações

### Deploy de Atualizações
```bash
#!/bin/bash
# Script de deploy
cd /var/www/ai-agents-platform

# Backup antes da atualização
/usr/local/bin/ai-agents-backup.sh

# Atualizar código
git pull origin main

# Backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head

# Frontend
cd ../frontend
npm install
npm run build

# Reiniciar serviços
sudo systemctl restart ai-agents-backend ai-agents-worker
sudo systemctl reload nginx

echo "Deploy completed successfully!"
```

## 📞 Suporte

### Logs Importantes
- **API**: `/var/log/ai-agents-platform/api.log`
- **Worker**: `/var/log/ai-agents-platform/worker.log`
- **Nginx**: `/var/log/nginx/access.log`, `/var/log/nginx/error.log`
- **PostgreSQL**: `/var/log/postgresql/`

### Comandos Úteis
```bash
# Status dos serviços
sudo systemctl status ai-agents-backend ai-agents-worker nginx postgresql

# Logs em tempo real
sudo journalctl -u ai-agents-backend -f

# Reiniciar tudo
sudo systemctl restart ai-agents-backend ai-agents-worker nginx

# Verificar conexões do banco
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity WHERE datname='ai_agents_platform';"
```

---

## ✅ Checklist de Deploy

- [ ] Servidor configurado e atualizado
- [ ] PostgreSQL instalado e configurado
- [ ] Aplicação clonada e dependências instaladas
- [ ] Variáveis de ambiente configuradas
- [ ] Migrações do banco executadas
- [ ] Nginx configurado
- [ ] SSL configurado (Let's Encrypt)
- [ ] Serviços systemd criados e ativos
- [ ] WhatsApp webhook configurado
- [ ] Firewall configurado
- [ ] Backup automático configurado
- [ ] Monitoramento configurado
- [ ] Testes de produção executados
- [ ] Documentação atualizada

**🎉 Parabéns! Sua plataforma AI Agents está em produção!**
