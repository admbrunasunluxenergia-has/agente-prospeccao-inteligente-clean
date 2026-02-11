# 🏗️ Arquitetura Técnica - Agente de Prospecção Inteligente

## Visão Geral

O agente é construído como um sistema modular com componentes independentes que se comunicam através de APIs e eventos.

---

## 📐 Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────┐
│                    ZAPI (WhatsApp)                          │
│              (Recebe/Envia Mensagens)                       │
└──────────────────────┬──────────────────────────────────────┘
                       │ Webhook
                       ↓
┌─────────────────────────────────────────────────────────────┐
│         FastAPI Server (prospecting_agent_main.py)          │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Endpoints REST                                       │  │
│  │ - POST /webhook/z-api                               │  │
│  │ - POST /api/v1/prospecting/send                      │  │
│  │ - GET  /api/v1/agent/status                          │  │
│  │ - GET  /api/v1/scheduler/statistics                  │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ↓              ↓              ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  WhatsApp    │ │   Client     │ │   OpenAI     │
│  Extractor   │ │  Identifier  │ │   Handler    │
│              │ │              │ │              │
│ Lê histórico │ │ Classifica   │ │ Gera resposta│
│ da conversa  │ │ tipo cliente │ │ com IA       │
└──────────────┘ └──────────────┘ └──────────────┘
        ↓              ↓              ↓
        └──────────────┼──────────────┘
                       │
        ┌──────────────┼──────────────┐
        ↓              ↓              ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Database    │ │  Scheduler   │ │  Logging &   │
│              │ │              │ │  Alerts      │
│ Armazena     │ │ Reenvio 24h  │ │              │
│ conversas    │ │ Máx 3 tent.  │ │ Email/Webhook│
└──────────────┘ └──────────────┘ └──────────────┘
```

---

## 🔄 Fluxo de Dados

### 1. Recebimento de Mensagem

```
ZAPI → Webhook /webhook/z-api
  ↓
Validar assinatura
  ↓
Extrair dados (phone, message, timestamp)
  ↓
Armazenar no banco de dados
```

### 2. Processamento

```
Extrair histórico da conversa
  ↓
Identificar tipo de cliente
  ↓
Gerar prompt personalizado
  ↓
Chamar OpenAI com contexto
  ↓
Gerar resposta inteligente
```

### 3. Envio de Resposta

```
Enviar via ZAPI
  ↓
Registrar no banco de dados
  ↓
Registrar no ClickUp (opcional)
  ↓
Agendar reenvio (se necessário)
```

### 4. Reenvio Automático

```
Scheduler verifica a cada hora
  ↓
Identifica mensagens sem resposta > 24h
  ↓
Verifica tentativas (máx 3)
  ↓
Reenvia mensagem
  ↓
Atualiza banco de dados
```

---

## 📦 Módulos Principais

### 1. **prospecting_agent_main.py**

**Responsabilidade:** Orquestração principal

**Funções:**
- Inicializa FastAPI
- Define endpoints REST
- Recebe webhooks ZAPI
- Coordena outros módulos
- Gerencia estado da aplicação

**Endpoints:**
```python
POST   /webhook/z-api                    # Receber mensagens
POST   /api/v1/prospecting/send          # Enviar prospecção
POST   /api/v1/prospecting/send-batch    # Enviar múltiplos
POST   /api/v1/intervention/send         # Intervenção manual
GET    /api/v1/agent/status              # Status
GET    /api/v1/scheduler/statistics      # Estatísticas
GET    /api/v1/conversation/{phone}      # Histórico
```

---

### 2. **whatsapp_extractor.py**

**Responsabilidade:** Extração de histórico do WhatsApp

**Funções:**
- Conectar ao WhatsApp/ZAPI
- Extrair histórico de conversas
- Formatar mensagens
- Detectar contexto
- Identificar quando reenviou

**Métodos:**
```python
get_conversation_history(phone)      # Obter histórico
extract_context(messages)            # Extrair contexto
format_for_openai(messages)          # Formatar para IA
should_resend(last_message_time)     # Verificar reenvio
```

---

### 3. **client_identifier.py**

**Responsabilidade:** Identificação e classificação de cliente

**Funções:**
- Analisar texto da conversa
- Identificar tipo de cliente
- Retornar prompt personalizado
- Calcular confiança da classificação

**Tipos de Cliente:**
```python
SYNDIC           # Síndico de condomínio
FARM             # Dono de granja
CLINIC           # Dono de clínica
GAS_STATION      # Posto de gasolina
RESIDENTIAL      # Cliente residencial
UNKNOWN          # Tipo desconhecido
```

**Métodos:**
```python
identify_client_type(text)           # Identificar tipo
get_prompt_for_client(client_type)   # Obter prompt
get_client_profile(phone, text)      # Perfil completo
```

---

### 4. **openai_handler.py**

**Responsabilidade:** Integração com OpenAI

**Funções:**
- Chamar API OpenAI
- Gerar respostas personalizadas
- Analisar respostas do cliente
- Tratar erros de API

**Métodos:**
```python
generate_response(prompt, context)   # Gerar resposta
analyze_response(message)            # Analisar resposta
generate_followup(history)           # Gerar follow-up
```

---

### 5. **scheduler.py**

**Responsabilidade:** Reenvio automático 24h

**Funções:**
- Verificar mensagens sem resposta
- Contar tentativas
- Agendar reenvios
- Limpar dados antigos
- Gerar estatísticas

**Métodos:**
```python
check_resend_needed()                # Verificar reenvios
resend_message(phone, message)       # Reenviar
get_statistics()                     # Estatísticas
cleanup_old_messages()               # Limpeza
```

---

### 6. **database.py**

**Responsabilidade:** Persistência de dados

**Funções:**
- Armazenar conversas
- Armazenar mensagens
- Rastrear tentativas
- Gerar relatórios

**Tabelas:**
```sql
conversations      # Histórico de conversas
messages          # Mensagens enviadas/recebidas
resend_attempts   # Tentativas de reenvio
statistics        # Estatísticas
logs              # Logs de operação
```

---

### 7. **logging_alerts.py**

**Responsabilidade:** Logging e alertas

**Funções:**
- Registrar eventos
- Enviar alertas por email
- Enviar webhooks
- Gerar relatórios

**Níveis de Log:**
```
DEBUG    - Informações detalhadas
INFO     - Eventos normais
WARNING  - Avisos importantes
ERROR    - Erros
CRITICAL - Erros críticos
```

---

## 🔐 Fluxo de Segurança

```
1. Validação de Webhook
   ├─ Verificar assinatura ZAPI
   ├─ Validar timestamp
   └─ Verificar token de segurança

2. Validação de Entrada
   ├─ Sanitizar texto
   ├─ Validar formato de phone
   └─ Limitar tamanho de mensagem

3. Autenticação
   ├─ Verificar API keys
   ├─ Validar credenciais
   └─ Usar variáveis de ambiente

4. Autorização
   ├─ Verificar permissões
   ├─ Validar acesso a recursos
   └─ Limitar operações por usuário
```

---

## 🚀 Escalabilidade

### Horizontal Scaling

```
Load Balancer
    ↓
┌─────────────────────────────────────┐
│ Instance 1 (Web)                    │
│ Instance 2 (Web)                    │
│ Instance 3 (Web)                    │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ Scheduler (Único)                   │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ Database (PostgreSQL/MySQL)         │
└─────────────────────────────────────┘
```

### Vertical Scaling

- Aumentar CPU/RAM das instâncias
- Otimizar queries do banco
- Usar cache (Redis)
- Implementar connection pooling

---

## 📊 Performance

### Métricas Monitoradas

- Tempo de resposta (< 2s)
- Taxa de erro (< 1%)
- Mensagens processadas/hora
- Taxa de sucesso de reenvio
- Uptime (> 99.9%)

### Otimizações

- Cache de histórico
- Batch processing
- Async/await
- Connection pooling
- Query optimization

---

## 🔄 Ciclo de Vida da Mensagem

```
1. Recebimento (0-100ms)
   └─ Webhook ZAPI recebe

2. Validação (100-200ms)
   └─ Verifica assinatura e formato

3. Extração (200-500ms)
   └─ Puxa histórico do WhatsApp

4. Identificação (500-700ms)
   └─ Classifica tipo de cliente

5. IA (700-2000ms)
   └─ OpenAI gera resposta

6. Envio (2000-2200ms)
   └─ ZAPI envia mensagem

7. Armazenamento (2200-2300ms)
   └─ Salva no banco de dados

8. Agendamento (2300-2400ms)
   └─ Agenda reenvio se necessário

TOTAL: ~2400ms (2.4 segundos)
```

---

## 🛠️ Stack Tecnológico

| Componente | Tecnologia |
|-----------|-----------|
| Framework | FastAPI |
| Servidor | Uvicorn |
| IA | OpenAI API |
| WhatsApp | ZAPI |
| Database | SQLite/PostgreSQL |
| Scheduler | APScheduler |
| Logging | Python Logging |
| Deployment | Railway/Heroku |

---

## 📚 Referências

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OpenAI API](https://platform.openai.com/docs)
- [ZAPI Documentation](https://docs.z-api.io/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [APScheduler](https://apscheduler.readthedocs.io/)

