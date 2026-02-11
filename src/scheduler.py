"""
Scheduler Module
Gerencia reenvio automático de mensagens em 24h
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
import time
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MessageScheduler:
    """Gerencia agendamento e reenvio de mensagens"""
    
    def __init__(self, database_file: str = "scheduled_messages.json"):
        self.database_file = database_file
        self.scheduler = BackgroundScheduler()
        self.messages_db = self._load_database()
        self._initialize_scheduler()
    
    def _load_database(self) -> Dict:
        """Carrega banco de dados de mensagens agendadas"""
        if os.path.exists(self.database_file):
            try:
                with open(self.database_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Erro ao carregar banco de dados: {e}")
                return {}
        return {}
    
    def _save_database(self) -> bool:
        """Salva banco de dados de mensagens agendadas"""
        try:
            with open(self.database_file, 'w', encoding='utf-8') as f:
                json.dump(self.messages_db, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar banco de dados: {e}")
            return False
    
    def schedule_message(
        self,
        phone: str,
        message: str,
        message_type: str = "prospecting",
        resend_after_hours: int = 24,
        max_retries: int = 3
    ) -> Dict:
        """
        Agenda uma mensagem para reenvio automático
        
        Args:
            phone: Número do WhatsApp
            message: Texto da mensagem
            message_type: Tipo da mensagem (prospecting, followup, etc)
            resend_after_hours: Horas para reenviar se sem resposta
            max_retries: Número máximo de tentativas
            
        Returns:
            Dict com informações do agendamento
        """
        message_id = f"{phone}_{int(time.time())}"
        
        scheduled_message = {
            "id": message_id,
            "phone": phone,
            "message": message,
            "type": message_type,
            "created_at": datetime.now().isoformat(),
            "scheduled_for": (datetime.now() + timedelta(hours=resend_after_hours)).isoformat(),
            "resend_after_hours": resend_after_hours,
            "max_retries": max_retries,
            "retry_count": 0,
            "status": "pending",
            "sent": False,
            "responded": False,
            "last_sent_at": None,
            "response": None
        }
        
        self.messages_db[message_id] = scheduled_message
        self._save_database()
        
        logger.info(f"Mensagem agendada: {message_id} para {phone}")
        
        return {
            "success": True,
            "message_id": message_id,
            "phone": phone,
            "scheduled_for": scheduled_message["scheduled_for"]
        }
    
    def mark_as_sent(self, message_id: str) -> bool:
        """Marca mensagem como enviada"""
        if message_id in self.messages_db:
            self.messages_db[message_id]["sent"] = True
            self.messages_db[message_id]["last_sent_at"] = datetime.now().isoformat()
            self.messages_db[message_id]["status"] = "sent"
            self._save_database()
            return True
        return False
    
    def mark_as_responded(self, message_id: str, response: str) -> bool:
        """Marca mensagem como respondida"""
        if message_id in self.messages_db:
            self.messages_db[message_id]["responded"] = True
            self.messages_db[message_id]["response"] = response
            self.messages_db[message_id]["status"] = "responded"
            self._save_database()
            logger.info(f"Mensagem {message_id} marcada como respondida")
            return True
        return False
    
    def get_messages_to_resend(self) -> List[Dict]:
        """
        Obtém mensagens que devem ser reenviadas
        
        Returns:
            Lista de mensagens para reenvio
        """
        now = datetime.now()
        messages_to_resend = []
        
        for message_id, message in self.messages_db.items():
            # Pula se já respondeu
            if message.get("responded"):
                continue
            
            # Pula se atingiu máximo de tentativas
            if message.get("retry_count", 0) >= message.get("max_retries", 3):
                continue
            
            # Verifica se chegou a hora de reenviar
            scheduled_for = datetime.fromisoformat(message.get("scheduled_for", ""))
            
            if now >= scheduled_for:
                messages_to_resend.append(message)
        
        return messages_to_resend
    
    def increment_retry(self, message_id: str) -> bool:
        """Incrementa contador de tentativas"""
        if message_id in self.messages_db:
            self.messages_db[message_id]["retry_count"] += 1
            
            # Agenda próximo reenvio
            resend_hours = self.messages_db[message_id].get("resend_after_hours", 24)
            self.messages_db[message_id]["scheduled_for"] = (
                datetime.now() + timedelta(hours=resend_hours)
            ).isoformat()
            
            self._save_database()
            return True
        return False
    
    def get_message_status(self, message_id: str) -> Optional[Dict]:
        """Obtém status de uma mensagem"""
        return self.messages_db.get(message_id)
    
    def get_phone_messages(self, phone: str) -> List[Dict]:
        """Obtém todas as mensagens agendadas para um telefone"""
        return [
            msg for msg in self.messages_db.values()
            if msg.get("phone") == phone
        ]
    
    def get_statistics(self) -> Dict:
        """Obtém estatísticas do scheduler"""
        total = len(self.messages_db)
        pending = sum(1 for m in self.messages_db.values() if m.get("status") == "pending")
        sent = sum(1 for m in self.messages_db.values() if m.get("status") == "sent")
        responded = sum(1 for m in self.messages_db.values() if m.get("responded"))
        
        return {
            "total_messages": total,
            "pending": pending,
            "sent": sent,
            "responded": responded,
            "response_rate": (responded / total * 100) if total > 0 else 0,
            "messages_to_resend": len(self.get_messages_to_resend())
        }
    
    def _initialize_scheduler(self):
        """Inicializa o scheduler de background"""
        # Adiciona job para verificar mensagens a cada 5 minutos
        self.scheduler.add_job(
            self._check_and_resend,
            IntervalTrigger(minutes=5),
            id='check_resend_job',
            replace_existing=True
        )
        
        logger.info("Scheduler inicializado")
    
    def _check_and_resend(self):
        """Verifica e reenvia mensagens (chamado periodicamente)"""
        messages = self.get_messages_to_resend()
        
        if messages:
            logger.info(f"Encontradas {len(messages)} mensagens para reenvio")
            
            for message in messages:
                logger.info(f"Reenvio necessário: {message['id']}")
                # Aqui seria chamada a função de envio real
                # send_message(message['phone'], message['message'])
    
    def start(self):
        """Inicia o scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler iniciado")
    
    def stop(self):
        """Para o scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler parado")
    
    def export_messages(self, filename: str = "messages_export.json") -> bool:
        """Exporta mensagens para arquivo"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.messages_db, f, indent=2, ensure_ascii=False)
            logger.info(f"Mensagens exportadas para {filename}")
            return True
        except Exception as e:
            logger.error(f"Erro ao exportar: {e}")
            return False
    
    def cleanup_old_messages(self, days: int = 30) -> int:
        """Remove mensagens antigas do banco de dados"""
        cutoff_date = datetime.now() - timedelta(days=days)
        removed = 0
        
        message_ids_to_remove = []
        
        for message_id, message in self.messages_db.items():
            created_at = datetime.fromisoformat(message.get("created_at", ""))
            
            # Remove se respondida e antiga
            if message.get("responded") and created_at < cutoff_date:
                message_ids_to_remove.append(message_id)
        
        for message_id in message_ids_to_remove:
            del self.messages_db[message_id]
            removed += 1
        
        if removed > 0:
            self._save_database()
            logger.info(f"Removidas {removed} mensagens antigas")
        
        return removed


# Exemplo de uso
if __name__ == "__main__":
    scheduler = MessageScheduler()
    
    # Agenda uma mensagem
    print("=== Agendando Mensagem ===")
    result = scheduler.schedule_message(
        phone="5585987654321",
        message="Oi! Tudo bem? Sou Bruna Paz da Sonlux Energia.",
        message_type="prospecting",
        resend_after_hours=24,
        max_retries=3
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Obtém estatísticas
    print("\n=== Estatísticas ===")
    stats = scheduler.get_statistics()
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    # Obtém mensagens para reenvio
    print("\n=== Mensagens para Reenvio ===")
    to_resend = scheduler.get_messages_to_resend()
    print(f"Total: {len(to_resend)}")
    
    # Inicia scheduler
    scheduler.start()
    print("\nScheduler iniciado. Pressione Ctrl+C para parar.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.stop()
        print("Scheduler parado.")
