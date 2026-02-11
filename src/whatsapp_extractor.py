"""
WhatsApp Extractor Module
Extrai histórico de conversas do WhatsApp via Z-API
"""

import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Dict, List, Optional
import json

load_dotenv()

Z_API_INSTANCE = os.getenv("Z_API_INSTANCE")
Z_API_TOKEN = os.getenv("Z_API_TOKEN")
Z_API_SECURITY_TOKEN = os.getenv("Z_API_SECURITY_TOKEN")

BASE_URL = f"https://api.z-api.io/instances/{Z_API_INSTANCE}/token/{Z_API_TOKEN}"


class WhatsAppExtractor:
    """Extrai e processa histórico de conversas do WhatsApp"""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.headers = {
            "Content-Type": "application/json",
            "Client-Token": Z_API_SECURITY_TOKEN
        }
        self.conversation_cache = {}
    
    def get_chat_history(self, phone: str, limit: int = 50) -> Dict:
        """
        Obtém histórico de chat com um contato
        
        Args:
            phone: Número do WhatsApp (ex: 5585987654321)
            limit: Número máximo de mensagens a recuperar
            
        Returns:
            Dict com histórico formatado
        """
        try:
            # Z-API endpoint para obter histórico
            url = f"{self.base_url}/get-messages"
            payload = {
                "phone": phone,
                "limit": limit
            }
            
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("success"):
                messages = data.get("data", [])
                return {
                    "success": True,
                    "phone": phone,
                    "messages": self._format_messages(messages),
                    "message_count": len(messages)
                }
            else:
                return {
                    "success": False,
                    "error": "Falha ao obter histórico",
                    "phone": phone
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "phone": phone
            }
    
    def _format_messages(self, messages: List[Dict]) -> List[Dict]:
        """Formata mensagens para uso interno"""
        formatted = []
        
        for msg in messages:
            formatted_msg = {
                "timestamp": msg.get("timestamp"),
                "from": msg.get("from"),
                "text": msg.get("text", ""),
                "type": msg.get("type", "text"),
                "fromMe": msg.get("fromMe", False)
            }
            formatted.append(formatted_msg)
        
        return sorted(formatted, key=lambda x: x["timestamp"])
    
    def get_conversation_summary(self, phone: str) -> Dict:
        """
        Obtém resumo da conversa (últimas mensagens)
        
        Args:
            phone: Número do WhatsApp
            
        Returns:
            Dict com resumo da conversa
        """
        history = self.get_chat_history(phone, limit=20)
        
        if not history.get("success"):
            return history
        
        messages = history.get("messages", [])
        
        # Separa mensagens do cliente e do agente
        client_messages = [m for m in messages if not m.get("fromMe")]
        agent_messages = [m for m in messages if m.get("fromMe")]
        
        # Obtém última mensagem do cliente
        last_client_msg = client_messages[-1] if client_messages else None
        
        # Conta tempo desde última resposta
        time_since_last = None
        if last_client_msg:
            last_time = datetime.fromtimestamp(last_client_msg["timestamp"] / 1000)
            time_since_last = (datetime.now() - last_time).total_seconds() / 3600  # em horas
        
        return {
            "success": True,
            "phone": phone,
            "last_client_message": last_client_msg.get("text") if last_client_msg else None,
            "last_client_time": last_client_msg.get("timestamp") if last_client_msg else None,
            "hours_since_last_message": time_since_last,
            "total_messages": len(messages),
            "client_message_count": len(client_messages),
            "agent_message_count": len(agent_messages),
            "conversation_active": time_since_last is not None and time_since_last < 24
        }
    
    def get_context_for_response(self, phone: str, max_context_messages: int = 10) -> str:
        """
        Obtém contexto formatado para passar ao OpenAI
        
        Args:
            phone: Número do WhatsApp
            max_context_messages: Número máximo de mensagens para contexto
            
        Returns:
            String com contexto formatado
        """
        history = self.get_chat_history(phone, limit=max_context_messages)
        
        if not history.get("success"):
            return "Sem histórico disponível"
        
        messages = history.get("messages", [])
        
        context = "## Histórico de Conversa\n\n"
        
        for msg in messages:
            sender = "Cliente" if not msg.get("fromMe") else "Agente"
            timestamp = datetime.fromtimestamp(msg["timestamp"] / 1000).strftime("%d/%m %H:%M")
            text = msg.get("text", "[Mensagem vazia]")
            
            context += f"**{sender}** ({timestamp}):\n{text}\n\n"
        
        return context
    
    def should_resend_message(self, phone: str, hours_threshold: int = 24) -> bool:
        """
        Verifica se deve reenviar mensagem (sem resposta em 24h)
        
        Args:
            phone: Número do WhatsApp
            hours_threshold: Horas sem resposta para reenviar
            
        Returns:
            True se deve reenviar, False caso contrário
        """
        summary = self.get_conversation_summary(phone)
        
        if not summary.get("success"):
            return False
        
        hours_since = summary.get("hours_since_last_message")
        
        if hours_since is None:
            return False
        
        # Reenviar se passou do threshold e última mensagem foi do agente
        return hours_since >= hours_threshold
    
    def get_all_active_chats(self) -> List[Dict]:
        """
        Obtém lista de todos os chats ativos
        
        Returns:
            Lista de chats com informações básicas
        """
        try:
            url = f"{self.base_url}/get-chats"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("success"):
                chats = data.get("data", [])
                return {
                    "success": True,
                    "chats": chats,
                    "chat_count": len(chats)
                }
            else:
                return {
                    "success": False,
                    "error": "Falha ao obter chats"
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def save_conversation_to_file(self, phone: str, filename: Optional[str] = None) -> Dict:
        """
        Salva conversa em arquivo JSON
        
        Args:
            phone: Número do WhatsApp
            filename: Nome do arquivo (opcional)
            
        Returns:
            Dict com status da operação
        """
        history = self.get_chat_history(phone, limit=100)
        
        if not history.get("success"):
            return history
        
        if not filename:
            filename = f"conversation_{phone}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
            
            return {
                "success": True,
                "filename": filename,
                "message_count": history.get("message_count")
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Exemplo de uso
if __name__ == "__main__":
    extractor = WhatsAppExtractor()
    
    # Teste com um número
    phone = "5585987654321"  # Substitua com número real
    
    # Obter histórico
    print("=== Histórico ===")
    history = extractor.get_chat_history(phone)
    print(json.dumps(history, indent=2, ensure_ascii=False))
    
    # Obter resumo
    print("\n=== Resumo ===")
    summary = extractor.get_conversation_summary(phone)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    
    # Verificar se deve reenviar
    print("\n=== Deve Reenviar? ===")
    should_resend = extractor.should_resend_message(phone)
    print(f"Deve reenviar: {should_resend}")
    
    # Obter contexto para OpenAI
    print("\n=== Contexto para OpenAI ===")
    context = extractor.get_context_for_response(phone)
    print(context)
