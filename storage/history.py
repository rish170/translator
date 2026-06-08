import sqlite3
from pathlib import Path
from datetime import datetime

DB_FILE = Path(__file__).parent.parent / "history.db"

class HistoryManager:
    def __init__(self):
        self.conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS translations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_text TEXT,
                    translated_text TEXT,
                    source_lang TEXT,
                    target_lang TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_favorite BOOLEAN DEFAULT 0
                )
            """)

    def add_translation(self, source_text, translated_text, source_lang, target_lang):
        with self.conn:
            self.conn.execute("""
                INSERT INTO translations (source_text, translated_text, source_lang, target_lang)
                VALUES (?, ?, ?, ?)
            """, (source_text, translated_text, source_lang, target_lang))

    def toggle_favorite(self, translation_id, is_favorite):
        with self.conn:
            self.conn.execute("""
                UPDATE translations SET is_favorite = ? WHERE id = ?
            """, (1 if is_favorite else 0, translation_id))

    def get_history(self, limit=100, search_query=None):
        query = "SELECT id, source_text, translated_text, source_lang, target_lang, timestamp, is_favorite FROM translations"
        params = []
        if search_query:
            query += " WHERE source_text LIKE ? OR translated_text LIKE ?"
            params.extend([f"%{search_query}%", f"%{search_query}%"])
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

    def get_favorites(self):
        query = "SELECT id, source_text, translated_text, source_lang, target_lang, timestamp, is_favorite FROM translations WHERE is_favorite = 1 ORDER BY timestamp DESC"
        cursor = self.conn.cursor()
        cursor.execute(query)
        return cursor.fetchall()

    def clear_history(self, keep_favorites=True):
        with self.conn:
            if keep_favorites:
                self.conn.execute("DELETE FROM translations WHERE is_favorite = 0")
            else:
                self.conn.execute("DELETE FROM translations")

history_manager = HistoryManager()
