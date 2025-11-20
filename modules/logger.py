# ============================================
# modules/logger.py
# ============================================
import sqlite3
from datetime import datetime
import os

def get_connection():
    db_path = os.path.join(os.path.dirname(__file__), '..', 'Data_muebles_db.db')
    conn = sqlite3.connect(db_path)
    return conn

class EventLogger:
    def __init__(self):
        pass

    def log_event(self, user_id, event_type, item_id=None, details=None):
        conn = get_connection()
        cursor = conn.cursor()

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        log_entry = {
            'timestamp': timestamp,
            'id_usuario': user_id,
            'tipo_evento': event_type,
            'id_item': item_id,
            'detalles': details if details else '-'
        }

        try:
            cursor.execute("""
                INSERT INTO evento_usuario (timestamp, id_usuario, tipo_evento, id_item, detalles)
                VALUES (:timestamp, :id_usuario, :tipo_evento, :id_item, :detalles)
            """, log_entry)

            conn.commit()

        except sqlite3.Error as e:
            print(f"Error al registrar evento: {e}")

        finally:
            conn.close()

