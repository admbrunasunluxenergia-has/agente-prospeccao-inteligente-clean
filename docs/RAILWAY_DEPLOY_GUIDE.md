# 🚀 Guia Completo de Deploy no Railway

**Agente de Prospecção Inteligente - Bruna Paz | Sonlux Energia**

Este guia mostra como fazer deploy do agente no Railway com banco de dados persistente, logs em tempo real e alertas de erro.

---

## 📋 Pré-requisitos

- ✅ Conta no Railway (https://railway.app)
- ✅ Repositório GitHub com o código
- ✅ Chaves de API (OpenAI, ZAPI)
- ✅ Git instalado no seu computador

---

## 🎯 Passo 1: Preparar o Repositório

### 1.1 Estrutura de Pastas

Seu repositório deve ter esta estrutura:

```
meu_agente_ia/
├── prospecting_agent_main.py
├── whatsapp_extractor.py
├── client_identifier.py
├── openai_handler.py
├── scheduler.py
├── database.py
├── logging_alerts.py
├── dashboard.html
├── requirements_prospecting.txt
├── Procfile
├── .env.example
├── .gitignore
└── README.md
```

### 1.2 Arquivo .gitignore

Crie arquivo `.gitignore` com:

```
.env
*.pyc
__pycache__/
*.log
*.db
.DS_Store
venv/
.vscode/
.idea/
*.sqlite3
prospecting_agent.db
```

### 1.3 Arquivo requirements.txt Atualizado

Certifique-se que tem todas as dependências:

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
openai==1.3.7
requests==2.31.0
python-dotenv==1.0.0
APScheduler==3.10.4
pydantic==2.5.0
python-json-logger==2.0.7
```

### 1.4 Arquivo Procfile

Crie arquivo `Procfile` (sem extensão):

```
web: python prospecting_agent_main.py
scheduler: python -c "from scheduler import start_scheduler; start_scheduler()"
```

---

## 🌐 Passo 2: Configurar no Railway

### 2.1 Criar Novo Projeto

1. Acesse https://railway.app
2. Clique em **"New Project"**
3. Selecione **"Deploy from GitHub"**
4. Selecione seu repositório

### 2.2 Conectar GitHub

1. Autorize Railway acessar seu GitHub
2. Selecione o repositório `meu_agente_ia`
3. Clique em **"Deploy"**

---

## 🔐 Passo 3: Configurar Variáveis de Ambiente

### 3.1 No Painel do Railway

1. Vá para seu projeto no Railway
2. Clique em **"Variables"**
3. Clique em **"RAW Editor"**
4. Cole as variáveis abaixo:

```env
# OpenAI
OPENAI_API_KEY=sua_chave_openai_aqui

# ZAPI
Z_API_INSTANCE=seu_instance_id_aqui
Z_API_TOKEN=seu_token_aqui
Z_API_SECURITY_TOKEN=seu_security_token_aqui

# ClickUp (opcional)
CLICKUP_API_TOKEN=seu_token_aqui
CLICKUP_LIST_ID=seu_list_id_aqui
CLICKUP_ENABLED=true

# Server
PORT=8000
HOST=0.0.0.0
DEBUG=false
ENVIRONMENT=production

# Database
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite:///./prospecting_agent.db

# Scheduler
SCHEDULER_ENABLED=true
SCHEDULER_RESEND_HOURS=24
SCHEDULER_MAX_RETRIES=3
SCHEDULER_CHECK_INTERVAL=300

# Logging
LOG_LEVEL=INFO
LOG_FILE=agent.log

# Alerts
ALERTS_ENABLED=true
ALERTS_EMAIL=seu_email@gmail.com
ALERTS_WEBHOOK_URL=https://seu-webhook.com/alerts
ALERTS_ON_ERROR=true
ALERTS_ON_RESEND=false

# Email (para alertas)
EMAIL_SENDER=seu_email@gmail.com
EMAIL_PASSWORD=sua_senha_app_google

# Timezone
TIMEZONE=America/Fortaleza
```

### 3.2 Salvar Variáveis

1. Clique em **"Save"**
2. Railway vai fazer redeploy automaticamente

---

## 📦 Passo 4: Adicionar Banco de Dados

### 4.1 Criar Banco PostgreSQL (Opcional)

Se quiser usar PostgreSQL em vez de SQLite:

1. No painel do Railway, clique em **"+ New"**
2. Selecione **"PostgreSQL"**
3. Clique em **"Create"**
4. Copie a URL de conexão
5. Adicione como variável:

```
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://user:password@host:port/database
```

### 4.2 Usar SQLite (Recomendado para Começar)

SQLite já está configurado e funciona bem para começar.

---

## ✅ Passo 5: Verificar Deploy

### 5.1 Acompanhar Deploy

1. No Railway, clique em **"Deployments"**
2. Veja o status do deploy
3. Aguarde até ficar **"SUCCESS"**

### 5.2 Acessar a Aplicação

1. Clique em **"Domains"**
2. Copie o domínio gerado (ex: `seu-app-production.up.railway.app`)
3. Acesse no navegador

### 5.3 Testar Endpoints

```bash
# Health check
curl https://seu-app-production.up.railway.app/health

# Dashboard
https://seu-app-production.up.railway.app/dashboard.html

# Documentação Swagger
https://seu-app-production.up.railway.app/docs
```

---

## 🔗 Passo 6: Configurar Webhook ZAPI

### 6.1 No Painel do ZAPI

1. Acesse sua instância ZAPI
2. Vá em **"Webhooks"** ou **"Configurações"**
3. Adicione novo webhook:

**URL:**
```
https://seu-app-production.up.railway.app/webhook/z-api
```

**Método:** POST

**Eventos:** Mensagens recebidas

**Headers:**
```
Content-Type: application/json
```

### 6.2 Testar Webhook

```bash
curl -X POST https://seu-app-production.up.railway.app/webhook/z-api \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "5585987654321",
    "text": "Olá, tudo bem?"
  }'
```

---

## 📊 Passo 7: Monitorar Logs

### 7.1 Logs em Tempo Real

No Railway:

1. Clique em seu projeto
2. Vá em **"Logs"**
3. Veja logs em tempo real

### 7.2 Logs Locais

Os logs também são salvos em:
- `/tmp/agent.log` (no servidor)
- Banco de dados (tabela `logs`)

### 7.3 Exportar Logs

```bash
# Via API
curl https://seu-app-production.up.railway.app/api/v1/scheduler/messages
```

---

## 🚨 Passo 8: Configurar Alertas

### 8.1 Alertas por Email

1. Configure `EMAIL_SENDER` e `EMAIL_PASSWORD` nas variáveis
2. Use uma **senha de app do Google** (não a senha normal)
3. Alertas serão enviados para `ALERTS_EMAIL`

### 8.2 Alertas por Webhook

1. Configure `ALERTS_WEBHOOK_URL` com seu webhook
2. Pode usar Slack, Discord, etc.

### 8.3 Tipos de Alertas

- ✅ Erro ao enviar mensagem
- ✅ Limite de tentativas excedido
- ✅ Falha em API externa
- ✅ Erro no scheduler
- ✅ Relatório diário

---

## 🔄 Passo 9: Atualizações e Redeploy

### 9.1 Fazer Alterações

1. Edite o código localmente
2. Commit no GitHub:

```bash
git add .
git commit -m "Descrição da mudança"
git push origin main
```

### 9.2 Railway Faz Redeploy Automaticamente

Railway detecta o push e faz redeploy automaticamente.

### 9.3 Verificar Novo Deploy

1. Vá em **"Deployments"**
2. Aguarde novo deploy terminar
3. Teste a aplicação

---

## 📈 Passo 10: Escalabilidade

### 10.1 Aumentar Recursos

Se a aplicação ficar lenta:

1. No Railway, clique em **"Settings"**
2. Aumente **"Memory"** e **"CPU"**
3. Railway vai fazer redeploy

### 10.2 Múltiplas Instâncias

Para alta disponibilidade:

1. Configure **"Replicas"** em **"Settings"**
2. Railway distribui o tráfego automaticamente

---

## 🐛 Troubleshooting

### Problema: Aplicação não inicia

**Solução:**
1. Verificar logs: `Logs` no Railway
2. Verificar variáveis de ambiente
3. Verificar se requirements.txt está correto

### Problema: Webhook não funciona

**Solução:**
1. Verificar URL do webhook no ZAPI
2. Testar com curl
3. Verificar logs de erro

### Problema: Banco de dados não persiste

**Solução:**
1. Usar PostgreSQL em vez de SQLite
2. Ou usar Railway Volumes para SQLite

### Problema: Alertas não chegam

**Solução:**
1. Verificar `ALERTS_ENABLED=true`
2. Verificar email/webhook configurado
3. Verificar logs de erro

---

## 📞 Monitoramento 24/7

### Checklist Diário

- ✅ Verificar logs em tempo real
- ✅ Verificar estatísticas de mensagens
- ✅ Verificar alertas de erro
- ✅ Verificar taxa de resposta

### Métricas Importantes

| Métrica | Ideal |
|---------|-------|
| Taxa de Resposta | > 30% |
| Tempo de Resposta | < 5s |
| Taxa de Erro | < 5% |
| Uptime | > 99% |

---

## 🎯 Próximos Passos

1. ✅ Deploy no Railway
2. ✅ Configurar webhook ZAPI
3. ✅ Testar com alguns contatos
4. ✅ Monitorar logs
5. ✅ Ajustar prompts conforme necessário
6. ✅ Escalar para todos os contatos

---

## 📚 Recursos Úteis

- **Railway Docs:** https://docs.railway.app
- **FastAPI Docs:** https://fastapi.tiangolo.com
- **ZAPI Docs:** https://www.z-api.io/docs
- **OpenAI Docs:** https://platform.openai.com/docs

---

## 💡 Dicas Importantes

1. **Sempre use variáveis de ambiente** - Nunca coloque chaves no código
2. **Monitore logs regularmente** - Detecte problemas cedo
3. **Teste alterações localmente** - Antes de fazer push
4. **Faça backup de dados** - Exporte dados regularmente
5. **Atualize dependências** - Mantenha segurança

---

**Desenvolvido por:** Bruna Paz - Consultora de Energia  
**Empresa:** Sonlux Energia  
**Data:** Fevereiro 2026  
**Versão:** 1.0.0
