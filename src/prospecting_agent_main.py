"""
Main Module - Agente de Prospecção 24/7
Orquestra todos os módulos para criar um agente de prospecção inteligente
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import logging
import os
from dotenv import load_dotenv
from datetime import datetime
import asyncio
import json

# Importa módulos customizados
from whatsapp_extractor import WhatsAppExtractor
from client_identifier import ClientIdentifier
from openai_handler import OpenAIHandler
from scheduler import MessageScheduler

# Importa handlers existentes do repositório
try:
    from z_api_handler import send_message, parse_webhook_message
    from clickup_handler import log_interaction
except ImportError:
    print("Aviso: Handlers existentes não encontrados. Usando versões simplificadas.")
    
    def send_message(phone: str, message: str) -> dict:
        return {"success": True, "phone": phone, "message": message}
    
    def parse_webhook_message(webhook_data: dict) -> dict:
        return {"success": True, "phone": webhook_data.get("phone"), "text": webhook_data.get("text")}
    
    def log_interaction(phone: str, user_message: str, agent_response: str, agent_type: str):
        return {"success": True}

load_dotenv()

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Inicializa aplicação FastAPI
app = FastAPI(
    title="Agente de Prospecção Inteligente",
    description="Agente 24/7 para prospecção de clientes via WhatsApp com OpenAI",
    version="1.0.0"
)

# Inicializa componentes
whatsapp_extractor = WhatsAppExtractor()
client_identifier = ClientIdentifier()
openai_handler = OpenAIHandler()
message_scheduler = MessageScheduler()

# Inicia scheduler
message_scheduler.start()


class ProspectingAgent:
    """Agente principal de prospecção"""
    
    def __init__(self):
        self.extractor = whatsapp_extractor
        self.identifier = client_identifier
        self.openai = openai_handler
        self.scheduler = message_scheduler
        self.conversation_cache = {}
    
    async def handle_incoming_message(self, phone: str, text: str) -> dict:
        """
        Processa mensagem de entrada
        
        Args:
            phone: Número do WhatsApp
            text: Texto da mensagem
            
        Returns:
            Dict com resposta gerada
        """
        try:
            logger.info(f"Mensagem recebida de {phone}: {text[:50]}...")
            
            # Obtém histórico da conversa
            context = self.extractor.get_context_for_response(phone, max_context_messages=10)
            
            # Identifica tipo de cliente
            client_type, confidence = self.identifier.identify_client_type(context)
            client_prompt = self.identifier.get_prompt_for_client(client_type)
            
            logger.info(f"Cliente identificado: {client_type.value} (confiança: {confidence:.2%})")
            
            # Gera resposta com OpenAI
            response = self.openai.generate_response(
                user_message=text,
                conversation_context=context,
                client_type_prompt=client_prompt,
                phone=phone
            )
            
            if not response.get("success"):
                logger.error(f"Erro ao gerar resposta: {response.get('error')}")
                return {
                    "success": False,
                    "error": response.get("error"),
                    "response": "Desculpe, não consegui processar sua mensagem."
                }
            
            agent_response = response.get("response")
            
            # Envia mensagem via ZAPI
            send_result = send_message(phone, agent_response)
            
            if send_result.get("success"):
                logger.info(f"Mensagem enviada para {phone}")
                
                # Registra interação no ClickUp
                log_interaction(
                    phone=phone,
                    user_message=text,
                    agent_response=agent_response,
                    agent_type=f"Prospecting Agent - {client_type.value}"
                )
                
                # Agenda reenvio se necessário
                should_resend = self.extractor.should_resend_message(phone, hours_threshold=24)
                if should_resend:
                    logger.info(f"Agendando reenvio para {phone}")
                    self.scheduler.schedule_message(
                        phone=phone,
                        message=agent_response,
                        message_type="followup",
                        resend_after_hours=24,
                        max_retries=2
                    )
                
                return {
                    "success": True,
                    "phone": phone,
                    "response": agent_response,
                    "client_type": client_type.value,
                    "client_confidence": confidence
                }
            else:
                logger.error(f"Erro ao enviar mensagem: {send_result.get('error')}")
                return {
                    "success": False,
                    "error": "Falha ao enviar mensagem",
                    "response": agent_response
                }
        
        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "phone": phone
            }
    
    async def send_prospecting_message(self, phone: str) -> dict:
        """
        Envia mensagem de prospecção inicial
        
        Args:
            phone: Número do WhatsApp
            
        Returns:
            Dict com resultado
        """
        try:
            logger.info(f"Enviando mensagem de prospecção para {phone}")
            
            # Obtém histórico (se houver)
            context = self.extractor.get_context_for_response(phone, max_context_messages=5)
            
            # Identifica tipo de cliente
            client_type, confidence = self.identifier.identify_client_type(context)
            client_prompt = self.identifier.get_prompt_for_client(client_type)
            
            # Gera mensagem de prospecção
            message_result = self.openai.generate_prospecting_message(
                client_type_prompt=client_prompt,
                conversation_context=context,
                phone=phone
            )
            
            if not message_result.get("success"):
                logger.error(f"Erro ao gerar mensagem: {message_result.get('error')}")
                return message_result
            
            message = message_result.get("message")
            
            # Envia via ZAPI
            send_result = send_message(phone, message)
            
            if send_result.get("success"):
                logger.info(f"Mensagem de prospecção enviada para {phone}")
                
                # Agenda reenvio
                self.scheduler.schedule_message(
                    phone=phone,
                    message=message,
                    message_type="prospecting",
                    resend_after_hours=24,
                    max_retries=3
                )
                
                return {
                    "success": True,
                    "phone": phone,
                    "message": message,
                    "client_type": client_type.value,
                    "scheduled_for_resend": True
                }
            else:
                logger.error(f"Erro ao enviar: {send_result.get('error')}")
                return {
                    "success": False,
                    "error": "Falha ao enviar mensagem",
                    "phone": phone
                }
        
        except Exception as e:
            logger.error(f"Erro ao enviar prospecção: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "phone": phone
            }
    
    def get_agent_status(self) -> dict:
        """Retorna status do agente"""
        stats = self.scheduler.get_statistics()
        
        return {
            "status": "running",
            "timestamp": datetime.now().isoformat(),
            "scheduler": {
                "running": self.scheduler.scheduler.running,
                "messages_stats": stats
            },
            "uptime": "24/7"
        }


# Instancia o agente
agent = ProspectingAgent()


# ============ ENDPOINTS ============

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "agent": agent.get_agent_status()
    }


@app.post("/webhook/z-api")
async def webhook_z_api(request: Request):
    """
    Webhook para receber mensagens do Z-API
    """
    try:
        webhook_data = await request.json()
        logger.info(f"Webhook recebido: {webhook_data}")
        
        # Parse da mensagem
        parsed = parse_webhook_message(webhook_data)
        
        if not parsed.get("success"):
            logger.warning(f"Mensagem ignorada: {parsed.get('error')}")
            return JSONResponse(content={"status": "ignored"})
        
        phone = parsed.get("phone")
        text = parsed.get("text")
        
        # Processa mensagem
        result = await agent.handle_incoming_message(phone, text)
        
        return JSONResponse(content={
            "status": "processed",
            "success": result.get("success"),
            "phone": phone
        })
    
    except Exception as e:
        logger.error(f"Erro no webhook: {e}", exc_info=True)
        return JSONResponse(
            content={"status": "error", "error": str(e)},
            status_code=500
        )


@app.post("/api/v1/prospecting/send")
async def send_prospecting(request: Request):
    """
    Envia mensagem de prospecção para um contato
    
    Body:
    {
        "phone": "5585987654321"
    }
    """
    try:
        data = await request.json()
        phone = data.get("phone")
        
        if not phone:
            raise HTTPException(status_code=400, detail="Phone number required")
        
        result = await agent.send_prospecting_message(phone)
        
        return JSONResponse(content=result)
    
    except Exception as e:
        logger.error(f"Erro ao enviar prospecção: {e}", exc_info=True)
        return JSONResponse(
            content={"success": False, "error": str(e)},
            status_code=500
        )


@app.post("/api/v1/prospecting/send-batch")
async def send_prospecting_batch(request: Request):
    """
    Envia mensagens de prospecção para múltiplos contatos
    
    Body:
    {
        "phones": ["5585987654321", "5585987654322", ...]
    }
    """
    try:
        data = await request.json()
        phones = data.get("phones", [])
        
        if not phones:
            raise HTTPException(status_code=400, detail="Phone list required")
        
        results = []
        
        for phone in phones:
            result = await agent.send_prospecting_message(phone)
            results.append(result)
            # Aguarda um pouco entre envios para não sobrecarregar
            await asyncio.sleep(2)
        
        return JSONResponse(content={
            "success": True,
            "total": len(phones),
            "sent": sum(1 for r in results if r.get("success")),
            "failed": sum(1 for r in results if not r.get("success")),
            "results": results
        })
    
    except Exception as e:
        logger.error(f"Erro ao enviar batch: {e}", exc_info=True)
        return JSONResponse(
            content={"success": False, "error": str(e)},
            status_code=500
        )


@app.get("/api/v1/agent/status")
async def get_status():
    """Retorna status do agente"""
    return agent.get_agent_status()


@app.get("/api/v1/scheduler/messages")
async def get_scheduled_messages(phone: str = None):
    """
    Obtém mensagens agendadas
    
    Query params:
    - phone: Filtrar por número (opcional)
    """
    if phone:
        messages = agent.scheduler.get_phone_messages(phone)
    else:
        messages = list(agent.scheduler.messages_db.values())
    
    return JSONResponse(content={
        "success": True,
        "count": len(messages),
        "messages": messages
    })


@app.get("/api/v1/scheduler/statistics")
async def get_scheduler_stats():
    """Retorna estatísticas do scheduler"""
    stats = agent.scheduler.get_statistics()
    return JSONResponse(content={
        "success": True,
        "statistics": stats
    })


@app.post("/api/v1/scheduler/resend-check")
async def check_and_resend():
    """
    Verifica e reenvia mensagens pendentes
    (Pode ser chamado manualmente ou via cron)
    """
    try:
        messages_to_resend = agent.scheduler.get_messages_to_resend()
        
        logger.info(f"Verificando reenvios: {len(messages_to_resend)} mensagens encontradas")
        
        resent_count = 0
        
        for message in messages_to_resend:
            phone = message.get("phone")
            text = message.get("message")
            message_id = message.get("id")
            
            # Envia mensagem
            send_result = send_message(phone, text)
            
            if send_result.get("success"):
                resent_count += 1
                agent.scheduler.increment_retry(message_id)
                logger.info(f"Mensagem reenviada: {message_id}")
            else:
                logger.error(f"Erro ao reenviar {message_id}: {send_result.get('error')}")
        
        return JSONResponse(content={
            "success": True,
            "checked": len(messages_to_resend),
            "resent": resent_count
        })
    
    except Exception as e:
        logger.error(f"Erro ao verificar reenvios: {e}", exc_info=True)
        return JSONResponse(
            content={"success": False, "error": str(e)},
            status_code=500
        )


@app.get("/api/v1/conversation/{phone}")
async def get_conversation(phone: str):
    """Obtém histórico de conversa"""
    try:
        summary = agent.extractor.get_conversation_summary(phone)
        context = agent.extractor.get_context_for_response(phone)
        
        return JSONResponse(content={
            "success": True,
            "phone": phone,
            "summary": summary,
            "context": context
        })
    
    except Exception as e:
        logger.error(f"Erro ao obter conversa: {e}", exc_info=True)
        return JSONResponse(
            content={"success": False, "error": str(e)},
            status_code=500
        )


@app.post("/api/v1/intervention/send")
async def manual_intervention(request: Request):
    """
    Permite intervenção manual - enviar mensagem customizada
    
    Body:
    {
        "phone": "5585987654321",
        "message": "Mensagem customizada"
    }
    """
    try:
        data = await request.json()
        phone = data.get("phone")
        message = data.get("message")
        
        if not phone or not message:
            raise HTTPException(status_code=400, detail="Phone and message required")
        
        # Envia mensagem
        send_result = send_message(phone, message)
        
        if send_result.get("success"):
            logger.info(f"Intervenção manual enviada para {phone}")
            
            # Registra no ClickUp
            log_interaction(
                phone=phone,
                user_message="[Intervenção Manual]",
                agent_response=message,
                agent_type="Manual Intervention"
            )
            
            return JSONResponse(content={
                "success": True,
                "phone": phone,
                "message": message,
                "type": "manual_intervention"
            })
        else:
            return JSONResponse(
                content={"success": False, "error": send_result.get("error")},
                status_code=500
            )
    
    except Exception as e:
        logger.error(f"Erro na intervenção manual: {e}", exc_info=True)
        return JSONResponse(
            content={"success": False, "error": str(e)},
            status_code=500
        )


# ============ STARTUP/SHUTDOWN ============

@app.on_event("startup")
async def startup_event():
    """Executado ao iniciar a aplicação"""
    logger.info("=== Agente de Prospecção Iniciado ===")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info("Scheduler iniciado para reenvios automáticos")


@app.on_event("shutdown")
async def shutdown_event():
    """Executado ao desligar a aplicação"""
    logger.info("=== Agente de Prospecção Desligado ===")
    agent.scheduler.stop()


if __name__ == "__main__":
    import uvicorn
    
    # Inicia servidor
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        log_level="info"
    )
