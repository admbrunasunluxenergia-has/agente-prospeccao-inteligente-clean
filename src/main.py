"""
Agente de Prospecção Inteligente 24/7
Recebe mensagens do WhatsApp via Z-API e responde com IA
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging
import os
import requests
import json
from openai import OpenAI
from datetime import datetime

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Inicializa FastAPI
app = FastAPI(
    title="Agente de Prospecção Inteligente",
    description="Bot de vendas consultivas de energia 24/7",
    version="1.0.0"
)

# Carrega variáveis de ambiente
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
Z_API_INSTANCE = os.getenv("Z_API_INSTANCE")
Z_API_TOKEN = os.getenv("Z_API_TOKEN")
Z_API_SECURITY_TOKEN = os.getenv("Z_API_SECURITY_TOKEN")

# Inicializa cliente OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# Dicionário para armazenar histórico de conversas
conversation_history = {}

# Prompt do agente de vendas consultivas
SYSTEM_PROMPT = """Você é um agente de vendas consultivas de energia solar e eficiência energética.

Seu objetivo é:
1. Entender as necessidades do cliente
2. Oferecer soluções personalizadas de energia
3. Destacar benefícios: economia, sustentabilidade, confiabilidade
4. Ser consultivo e não agressivo
5. Agendar uma conversa ou visita quando apropriado

Tipos de clientes:
- Síndicos: Foco em redução de taxas do condomínio
- Granja: Foco em custos operacionais
- Clínica: Foco em confiabilidade + economia
- Posto de Gasolina: Foco em margem de lucro
- Residencial: Foco em economia pessoal

Sempre seja educado, profissional e ofereça valor real."""


@app.get("/health")
async def health():
    """Health check do agente"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "agent": "Agente de Prospecção Inteligente",
        "version": "1.0.0"
    }


@app.post("/webhook/z-api")
async def webhook_z_api(request: Request):
    """Webhook para receber mensagens do Z-API"""
    try:
        webhook_data = await request.json()
        logger.info(f"✅ Webhook recebido: {json.dumps(webhook_data, indent=2)}")
        
        phone = webhook_data.get("phone") or webhook_data.get("sender")
        text = webhook_data.get("text") or webhook_data.get("message")
        name = webhook_data.get("name") or "Cliente"
        
        if not phone or not text:
            logger.warning(f"❌ Dados incompletos: {webhook_data}")
            return JSONResponse(content={"status": "error"}, status_code=400)
        
        logger.info(f"📱 Mensagem de {name} ({phone}): {text}")
        
        if phone not in conversation_history:
            conversation_history[phone] = []
        
        conversation_history[phone].append({"role": "user", "content": text})
        
        if len(conversation_history[phone]) > 20:
            conversation_history[phone] = conversation_history[phone][-20:]
        
        logger.info(f"🤖 Gerando resposta com OpenAI...")
        
        try:
            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    *conversation_history[phone]
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            agent_response = response.choices[0].message.content
            logger.info(f"✅ Resposta gerada: {agent_response[:100]}...")
            
        except Exception as e:
            logger.error(f"❌ Erro OpenAI: {e}")
            agent_response = "Desculpe, estou com dificuldades. Tente novamente."
        
        conversation_history[phone].append({"role": "assistant", "content": agent_response})
        
        logger.info(f"📤 Enviando para {phone}...")
        success = send_message_via_zapi(phone, agent_response)
        
        if success:
            logger.info(f"✅ Enviado com sucesso")
            return JSONResponse(content={"status": "success", "phone": phone})
        else:
            logger.error(f"❌ Falha ao enviar")
            return JSONResponse(content={"status": "error"}, status_code=500)
    
    except Exception as e:
        logger.error(f"❌ Erro: {e}", exc_info=True)
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


def send_message_via_zapi(phone: str, message: str) -> bool:
    """Envia mensagem via Z-API"""
    try:
        url = f"https://api.z-api.io/instances/{Z_API_INSTANCE}/token/{Z_API_TOKEN}/send-text"
        payload = {"phone": phone, "message": message}
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {Z_API_SECURITY_TOKEN}"
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        logger.info(f"📤 Z-API: {response.status_code}")
        
        return response.status_code in [200, 201]
    
    except Exception as e:
        logger.error(f"❌ Erro Z-API: {e}")
        return False


@app.get("/api/v1/agent/status")
async def get_agent_status():
    """Status do agente"""
    return {
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "conversations": len(conversation_history),
        "uptime": "24/7"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
