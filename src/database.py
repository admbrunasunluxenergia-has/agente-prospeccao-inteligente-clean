"""
Database Module - Persistência de Dados para Agente de Prospecção
Suporta SQLite e PostgreSQL
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

class DatabaseManager:
    """Gerencia persistência de dados do agente"""
    
    def __init__(self, db_type: str = "sqlite", db_url: str = None):
        self.db_type = db_type or os.getenv("DATABASE_TYPE", "sqlite")
        self.db_url = db_url or os.getenv("DATABASE_URL", "sqlite:///./prospecting_agent.db")
        
        if self.db_type == "sqlite":
            self.db_path = self.db_url.replace("sqlite:///", "")
            self._init_sqlite()
        else:
            self._init_postgresql()
    
    def _init_sqlite(self):
        """Inicializa banco SQLite"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de mensagens agendadas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_messages (
                id TEXT PRIMARY KEY,
                phone TEXT NOT NULL,
                message TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                scheduled_at TIMESTAMP,
                sent_at TIMESTAMP,
                responded_at TIMESTAMP,
                last_retry_at TIMESTAMP
            )
        """)
        
        # Tabela de conversas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                phone TEXT NOT NULL UNIQUE,
                client_type TEXT,
                client_confidence REAL,
                history TEXT,
                last_message_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                level TEXT,
                message TEXT,
                phone TEXT,
                action TEXT,
                details TEXT
            )
        """)
        
        # Tabela de estatísticas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE DEFAULT CURRENT_DATE,
                total_messages INTEGER DEFAULT 0,
                sent_messages INTEGER DEFAULT 0,
                responded_messages INTEGER DEFAULT 0,
                failed_messages INTEGER DEFAULT 0,
                resent_messages INTEGER DEFAULT 0
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _init_postgresql(self):
        """Inicializa banco PostgreSQL (futuro)"""
        pass
    
    # ==================== MENSAGENS ====================
    
    def save_message(self, message_id: str, phone: str, message: str, 
                     scheduled_at: datetime = None) -> bool:
        """Salva mensagem agendada"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO scheduled_messages 
                (id, phone, message, scheduled_at) 
                VALUES (?, ?, ?, ?)
            """, (message_id, phone, message, scheduled_at))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao salvar mensagem: {e}")
            return False
    
    def get_messages(self, phone: str = None, status: str = None) -> List[Dict]:
        """Obtém mensagens agendadas"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM scheduled_messages WHERE 1=1"
            params = []
            
            if phone:
                query += " AND phone = ?"
                params.append(phone)
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            cursor.execute(query, params)
            messages = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return messages
        except Exception as e:
            print(f"Erro ao obter mensagens: {e}")
            return []
    
    def update_message_status(self, message_id: str, status: str, 
                             sent_at: datetime = None, responded_at: datetime = None) -> bool:
        """Atualiza status de mensagem"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE scheduled_messages 
                SET status = ?, sent_at = ?, responded_at = ?
                WHERE id = ?
            """, (status, sent_at, responded_at, message_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao atualizar mensagem: {e}")
            return False
    
    def increment_retry(self, message_id: str) -> bool:
        """Incrementa contador de tentativas"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE scheduled_messages 
                SET retry_count = retry_count + 1, last_retry_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (message_id,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao incrementar retry: {e}")
            return False
    
    # ==================== CONVERSAS ====================
    
    def save_conversation(self, phone: str, client_type: str = None, 
                         confidence: float = 0.0, history: str = "") -> bool:
        """Salva ou atualiza conversa"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO conversations 
                (id, phone, client_type, client_confidence, history, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (phone, phone, client_type, confidence, history))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao salvar conversa: {e}")
            return False
    
    def get_conversation(self, phone: str) -> Optional[Dict]:
        """Obtém histórico de conversa"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM conversations WHERE phone = ?", (phone,))
            row = cursor.fetchone()
            conn.close()
            
            return dict(row) if row else None
        except Exception as e:
            print(f"Erro ao obter conversa: {e}")
            return None
    
    # ==================== LOGS ====================
    
    def log_action(self, level: str, message: str, phone: str = None, 
                   action: str = None, details: str = None) -> bool:
        """Registra ação no log"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO logs (level, message, phone, action, details)
                VALUES (?, ?, ?, ?, ?)
            """, (level, message, phone, action, details))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao registrar log: {e}")
            return False
    
    def get_logs(self, limit: int = 100, level: str = None) -> List[Dict]:
        """Obtém logs"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM logs WHERE 1=1"
            params = []
            
            if level:
                query += " AND level = ?"
                params.append(level)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            logs = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return logs
        except Exception as e:
            print(f"Erro ao obter logs: {e}")
            return []
    
    # ==================== ESTATÍSTICAS ====================
    
    def update_statistics(self, sent: int = 0, responded: int = 0, 
                         failed: int = 0, resent: int = 0) -> bool:
        """Atualiza estatísticas do dia"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO statistics 
                (date, total_messages, sent_messages, responded_messages, failed_messages, resent_messages)
                VALUES (
                    CURRENT_DATE,
                    COALESCE((SELECT total_messages FROM statistics WHERE date = CURRENT_DATE), 0) + ?,
                    COALESCE((SELECT sent_messages FROM statistics WHERE date = CURRENT_DATE), 0) + ?,
                    COALESCE((SELECT responded_messages FROM statistics WHERE date = CURRENT_DATE), 0) + ?,
                    COALESCE((SELECT failed_messages FROM statistics WHERE date = CURRENT_DATE), 0) + ?,
                    COALESCE((SELECT resent_messages FROM statistics WHERE date = CURRENT_DATE), 0) + ?
                )
            """, (sent + responded + failed, sent, responded, failed, resent))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao atualizar estatísticas: {e}")
            return False
    
    def get_statistics(self, days: int = 7) -> Dict:
        """Obtém estatísticas dos últimos N dias"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM statistics 
                WHERE date >= date('now', '-' || ? || ' days')
                ORDER BY date DESC
            """, (days,))
            
            stats = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            # Agregação
            total = {
                'total_messages': sum(s['total_messages'] for s in stats),
                'sent_messages': sum(s['sent_messages'] for s in stats),
                'responded_messages': sum(s['responded_messages'] for s in stats),
                'failed_messages': sum(s['failed_messages'] for s in stats),
                'resent_messages': sum(s['resent_messages'] for s in stats),
            }
            
            return {
                'daily': stats,
                'total': total,
                'response_rate': (total['responded_messages'] / total['sent_messages'] * 100) if total['sent_messages'] > 0 else 0
            }
        except Exception as e:
            print(f"Erro ao obter estatísticas: {e}")
            return {}
    
    # ==================== LIMPEZA ====================
    
    def cleanup_old_messages(self, days: int = 30) -> int:
        """Remove mensagens antigas"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM scheduled_messages 
                WHERE created_at < datetime('now', '-' || ? || ' days')
                AND status IN ('sent', 'failed')
            """, (days,))
            
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            
            return deleted
        except Exception as e:
            print(f"Erro ao limpar mensagens: {e}")
            return 0
    
    def cleanup_old_logs(self, days: int = 30) -> int:
        """Remove logs antigos"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM logs 
                WHERE timestamp < datetime('now', '-' || ? || ' days')
            """, (days,))
            
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            
            return deleted
        except Exception as e:
            print(f"Erro ao limpar logs: {e}")
            return 0
    
    # ==================== EXPORTAÇÃO ====================
    
    def export_to_json(self, output_file: str = "export.json") -> bool:
        """Exporta dados para JSON"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            data = {
                'messages': [dict(row) for row in cursor.execute("SELECT * FROM scheduled_messages")],
                'conversations': [dict(row) for row in cursor.execute("SELECT * FROM conversations")],
                'statistics': [dict(row) for row in cursor.execute("SELECT * FROM statistics")],
            }
            
            conn.close()
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
            return True
        except Exception as e:
            print(f"Erro ao exportar: {e}")
            return False


# Instância global
db = DatabaseManager()
