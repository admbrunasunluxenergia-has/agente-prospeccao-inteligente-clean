# 🤖 Agente de Prospecção Inteligente 24/7

**Agente autônomo de prospecção via WhatsApp com IA (OpenAI) e integração ZAPI**

Um sistema completo de prospecção inteligente que funciona 24/7, lendo histórico de conversas do WhatsApp, identificando tipo de cliente e respondendo com mensagens personalizadas usando OpenAI.

---

## ✨ Características Principais

✅ **Prospecção Automática 24/7** - Funciona continuamente sem intervenção  
✅ **Leitura de Histórico** - Analisa conversas anteriores do WhatsApp  
✅ **Identificação de Cliente** - Classifica em 5 segmentos diferentes  
✅ **IA Inteligente** - OpenAI gera respostas personalizadas  
✅ **Reenvio Automático** - Reenvia em 24h se sem resposta (máx 3 tentativas)  
✅ **Banco Persistente** - Armazena todas as conversas e dados  
✅ **Logs Completos** - Email + Webhook + Arquivo  
✅ **Dashboard Web** - Interface para monitoramento  
✅ **API REST** - Endpoints para integração  
✅ **Deploy Pronto** - Railway, Heroku, AWS  

---

## 🎯 Segmentos de Clientes

O agente identifica e personaliza para:

- 🏢 **Síndicos de Condomínio** - Foco em redução de taxas
- 🚜 **Donos de Granja** - Foco em custos operacionais
- 🏥 **Clínicas** - Foco em confiabilidade + economia
- ⛽ **Postos de Gasolina** - Foco em margem de lucro
- 🏠 **Residencial** - Foco em economia pessoal

---

## 🚀 Quick Start

### 1. Clonar Repositório

```bash
git clone https://github.com/admbrunasunluxenergia-has/agente-prospeccao-inteligente.git
cd agente-prospeccao-inteligente
```

### 2. Criar Ambiente Virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar Variáveis de Ambiente

```bash
# Copie o arquivo de exemplo
cp config/.env.example .env

# Edite com suas credenciais
# OPENAI_API_KEY=sua_chave_openai_aqui
# Z_API_INSTANCE=seu_instance_id
# Z_API_TOKEN=seu_token
# etc
```

### 5. Executar Localmente

```bash
python -m uvicorn src.prospecting_agent_main:app --reload
```

Acesse: http://localhost:8000

---

## 📋 Estrutura do Projeto

```
agente-prospeccao-inteligente/
├── src/
│   ├── __init__.py
│   ├── prospecting_agent_main.py    # Orquestrador FastAPI
│   ├── whatsapp_extractor.py        # Extração de histórico
│   ├── client_identifier.py         # Classificação de cliente
│   ├── openai_handler.py            # Integração OpenAI
│   ├── scheduler.py                 # Reenvio automático 24h
│   ├── database.py                  # Banco de dados
│   └── logging_alerts.py            # Logs e alertas
├── config/
│   └── .env.example                 # Variáveis de ambiente
├── docs/
│   ├── ARCHITECTURE.md              # Arquitetura técnica
│   ├── RAILWAY_DEPLOY_GUIDE.md      # Deploy passo-a-passo
│   └── AGENTE_FEATURES.md           # Funcionalidades detalhadas
├── requirements.txt                 # Dependências
├── Procfile                         # Configuração Railway
├── LICENSE                          # MIT License
└── README.md                        # Este arquivo
```

---

## 🔗 Endpoints da API

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v1/prospecting/send` | Enviar prospecção |
| POST | `/api/v1/prospecting/send-batch` | Enviar para múltiplos |
| POST | `/webhook/z-api` | Receber mensagens ZAPI |
| GET | `/api/v1/agent/status` | Status do agente |
| GET | `/api/v1/scheduler/statistics` | Estatísticas |
| GET | `/api/v1/conversation/{phone}` | Histórico |

---

## 🔧 Configuração ZAPI

Configure o webhook no ZAPI:

**URL:**
```
https://seu-dominio.up.railway.app/webhook/z-api
```

**Método:** POST

**Headers:**
```
Content-Type: application/json
Authorization: Bearer seu_webhook_secret
```

---

## 📊 Fluxo de Funcionamento

```
1. Cliente envia mensagem no WhatsApp
   ↓
2. ZAPI envia webhook para seu servidor
   ↓
3. Agente extrai histórico da conversa
   ↓
4. Identifica tipo de cliente (síndico, granja, etc)
   ↓
5. OpenAI gera resposta personalizada
   ↓
6. Envia resposta via ZAPI
   ↓
7. Registra no ClickUp (opcional)
   ↓
8. Se sem resposta em 24h → Reenvia automaticamente
   ↓
9. Máximo 3 tentativas
```

---

## 🚢 Deploy no Railway

### Pré-requisitos

- Conta no Railway (https://railway.app)
- Repositório no GitHub
- Variáveis de ambiente configuradas

### Passos

1. Acesse https://railway.app
2. Clique em "New Project"
3. Selecione "Deploy from GitHub"
4. Selecione este repositório
5. Configure as variáveis de ambiente
6. Deploy automático!

**Documentação completa:** `docs/RAILWAY_DEPLOY_GUIDE.md`

---

## 📚 Documentação

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Arquitetura técnica detalhada
- **[RAILWAY_DEPLOY_GUIDE.md](docs/RAILWAY_DEPLOY_GUIDE.md)** - Deploy passo-a-passo
- **[AGENTE_FEATURES.md](docs/AGENTE_FEATURES.md)** - Funcionalidades e recursos

---

## 🔐 Segurança

⚠️ **NUNCA coloque chaves secretas no código!**

Sempre use variáveis de ambiente:

```python
# ✅ Correto
api_key = os.getenv("OPENAI_API_KEY")

# ❌ Errado
api_key = os.getenv("OPENAI_API_KEY")
```

---

## 🐛 Troubleshooting

### Erro: "OpenAI API Key not found"

```bash
# Verifique se .env está configurado
cat .env | grep OPENAI_API_KEY
```

### Erro: "ZAPI connection failed"

```bash
# Verifique credenciais ZAPI
# Z_API_INSTANCE, Z_API_TOKEN, Z_API_SECURITY_TOKEN
```

### Agente não está respondendo

```bash
# Verifique logs
tail -f logs/agente.log

# Verifique status
curl http://localhost:8000/api/v1/agent/status
```

---

## 📞 Suporte

Desenvolvido por: **Bruna Paz**  
Empresa: **Sonlux Energia**  
Email: bruna@sonluxenergia.com.br

---

## 📄 Licença

MIT License - Veja arquivo [LICENSE](LICENSE)

---

## 🙏 Agradecimentos

Desenvolvido com ❤️ para prospecção inteligente e automática.

**Versão:** 1.0.0  
**Status:** ✅ Pronto para Produção  
**Última Atualização:** Fevereiro 2024
