"""
Logging and Alerts Module - Sistema de Logs e Alertas
Suporta arquivo, console, email e webhooks
"""

import os
import json
import logging
import smtplib
import requests
from datetime import datetime
from logging.handlers import RotatingFileHandler
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict

class LoggerManager:
    """Gerencia logging e alertas do agente"""
    
    def __init__(self):
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_file = os.getenv("LOG_FILE", "agent.log")
        self.log_max_bytes = int(os.getenv("LOG_MAX_BYTES", "10485760"))
        self.log_backup_count = int(os.getenv("LOG_BACKUP_COUNT", "5"))
        
        self.alerts_enabled = os.getenv("ALERTS_ENABLED", "true").lower() == "true"
        self.alerts_email = os.getenv("ALERTS_EMAIL")
        self.alerts_webhook = os.getenv("ALERTS_WEBHOOK_URL")
        self.alerts_on_error = os.getenv("ALERTS_ON_ERROR", "true").lower() == "true"
        self.alerts_on_resend = os.getenv("ALERTS_ON_RESEND", "true").lower() == "true"
        
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Configura logger com múltiplos handlers"""
        logger = logging.getLogger("prospecting_agent")
        logger.setLevel(getattr(logging, self.log_level))
        
        # Formato
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Handler de arquivo com rotação
        file_handler = RotatingFileHandler(
            self.log_file,
            maxBytes=self.log_max_bytes,
            backupCount=self.log_backup_count
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Handler de console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    # ==================== LOGGING ====================
    
    def info(self, message: str, phone: str = None, action: str = None):
        """Log de informação"""
        self.logger.info(f"[{phone or 'SYSTEM'}] {message}")
        if phone and action:
            self._log_to_database("INFO", message, phone, action)
    
    def warning(self, message: str, phone: str = None, action: str = None):
        """Log de aviso"""
        self.logger.warning(f"[{phone or 'SYSTEM'}] {message}")
        if phone and action:
            self._log_to_database("WARNING", message, phone, action)
    
    def error(self, message: str, phone: str = None, action: str = None, exception: Exception = None):
        """Log de erro com alerta opcional"""
        error_msg = f"[{phone or 'SYSTEM'}] {message}"
        if exception:
            error_msg += f" - {str(exception)}"
        
        self.logger.error(error_msg)
        
        if phone and action:
            self._log_to_database("ERROR", message, phone, action)
        
        # Enviar alerta se habilitado
        if self.alerts_enabled and self.alerts_on_error:
            self.send_alert(
                level="ERROR",
                title=f"Erro no Agente - {action or 'Sistema'}",
                message=error_msg,
                phone=phone
            )
    
    def debug(self, message: str, phone: str = None):
        """Log de debug"""
        self.logger.debug(f"[{phone or 'SYSTEM'}] {message}")
    
    def _log_to_database(self, level: str, message: str, phone: str, action: str):
        """Registra log no banco de dados"""
        try:
            from database import db
            db.log_action(level, message, phone, action)
        except Exception as e:
            self.logger.error(f"Erro ao registrar log no BD: {e}")
    
    # ==================== ALERTAS ====================
    
    def send_alert(self, level: str, title: str, message: str, phone: str = None):
        """Envia alerta via email e webhook"""
        if not self.alerts_enabled:
            return
        
        alert_data = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "title": title,
            "message": message,
            "phone": phone,
            "agent": "prospecting_agent"
        }
        
        # Enviar via email
        if self.alerts_email:
            self._send_email_alert(alert_data)
        
        # Enviar via webhook
        if self.alerts_webhook:
            self._send_webhook_alert(alert_data)
    
    def _send_email_alert(self, alert_data: Dict):
        """Envia alerta por email"""
        try:
            # Configuração de email (Gmail como exemplo)
            sender_email = os.getenv("EMAIL_SENDER", "seu_email@gmail.com")
            sender_password = os.getenv("EMAIL_PASSWORD", "sua_senha_app")
            
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = self.alerts_email
            msg['Subject'] = f"[{alert_data['level']}] {alert_data['title']}"
            
            # Corpo do email
            body = f"""
            <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2 style="color: {'red' if alert_data['level'] == 'ERROR' else 'orange'};">
                        {alert_data['title']}
                    </h2>
                    
                    <p><strong>Nível:</strong> {alert_data['level']}</p>
                    <p><strong>Hora:</strong> {alert_data['timestamp']}</p>
                    {f'<p><strong>Telefone:</strong> {alert_data["phone"]}</p>' if alert_data.get('phone') else ''}
                    
                    <hr>
                    
                    <p><strong>Mensagem:</strong></p>
                    <pre style="background: #f5f5f5; padding: 10px; border-radius: 5px;">
{alert_data['message']}
                    </pre>
                    
                    <hr>
                    <p style="color: #999; font-size: 12px;">
                        Agente de Prospecção Automático | {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
                    </p>
                </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            # Enviar email
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(sender_email, sender_password)
                server.send_message(msg)
            
            self.logger.info(f"Alerta enviado por email para {self.alerts_email}")
        
        except Exception as e:
            self.logger.error(f"Erro ao enviar alerta por email: {e}")
    
    def _send_webhook_alert(self, alert_data: Dict):
        """Envia alerta via webhook"""
        try:
            response = requests.post(
                self.alerts_webhook,
                json=alert_data,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                self.logger.info(f"Alerta enviado via webhook")
            else:
                self.logger.warning(f"Webhook retornou status {response.status_code}")
        
        except Exception as e:
            self.logger.error(f"Erro ao enviar alerta via webhook: {e}")
    
    # ==================== ALERTAS ESPECÍFICOS ====================
    
    def alert_resend(self, phone: str, attempt: int, max_attempts: int):
        """Alerta de reenvio automático"""
        if not self.alerts_on_resend:
            return
        
        self.send_alert(
            level="INFO",
            title=f"Reenvio Automático - {phone}",
            message=f"Mensagem reenviada para {phone} (tentativa {attempt}/{max_attempts})",
            phone=phone
        )
    
    def alert_max_retries_exceeded(self, phone: str, max_attempts: int):
        """Alerta de limite de tentativas excedido"""
        self.send_alert(
            level="WARNING",
            title=f"Limite de Tentativas Excedido - {phone}",
            message=f"Não foi possível enviar mensagem para {phone} após {max_attempts} tentativas",
            phone=phone
        )
    
    def alert_webhook_failure(self, phone: str, error: str):
        """Alerta de falha no webhook ZAPI"""
        self.send_alert(
            level="ERROR",
            title=f"Falha ao Enviar - {phone}",
            message=f"Erro ao enviar mensagem via ZAPI: {error}",
            phone=phone
        )
    
    def alert_api_error(self, service: str, error: str):
        """Alerta de erro em API externa"""
        self.send_alert(
            level="ERROR",
            title=f"Erro em API Externa - {service}",
            message=f"Erro ao comunicar com {service}: {error}"
        )
    
    def alert_scheduler_error(self, error: str):
        """Alerta de erro no scheduler"""
        self.send_alert(
            level="ERROR",
            title="Erro no Scheduler",
            message=f"Erro ao processar reenvios: {error}"
        )
    
    # ==================== RELATÓRIOS ====================
    
    def generate_daily_report(self) -> Dict:
        """Gera relatório diário"""
        try:
            from database import db
            stats = db.get_statistics(days=1)
            
            report = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "total_messages": stats['total'].get('total_messages', 0),
                "sent": stats['total'].get('sent_messages', 0),
                "responded": stats['total'].get('responded_messages', 0),
                "failed": stats['total'].get('failed_messages', 0),
                "resent": stats['total'].get('resent_messages', 0),
                "response_rate": f"{stats.get('response_rate', 0):.1f}%"
            }
            
            return report
        except Exception as e:
            self.logger.error(f"Erro ao gerar relatório: {e}")
            return {}
    
    def send_daily_report(self):
        """Envia relatório diário por email"""
        try:
            report = self.generate_daily_report()
            
            if not report:
                return
            
            message = f"""
            Relatório Diário - {report['date']}
            
            Total de Mensagens: {report['total_messages']}
            Enviadas: {report['sent']}
            Respondidas: {report['responded']}
            Falhadas: {report['failed']}
            Reenviadas: {report['resent']}
            Taxa de Resposta: {report['response_rate']}
            """
            
            self.send_alert(
                level="INFO",
                title="Relatório Diário",
                message=message
            )
        
        except Exception as e:
            self.logger.error(f"Erro ao enviar relatório: {e}")


# Instância global
logger = LoggerManager()
