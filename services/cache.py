import sqlite3
from pathlib import Path
from datetime import datetime

CACHE_DB = Path(__file__).parent.parent / "translation_cache.db"

class TranslationCache:
    def __init__(self):
        self.conn = sqlite3.connect(CACHE_DB, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    source_text TEXT,
                    source_lang TEXT,
                    target_lang TEXT,
                    translated_text TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (source_text, source_lang, target_lang)
                )
            """)

    def get(self, source_text, source_lang, target_lang):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT translated_text FROM cache 
            WHERE source_text = ? AND source_lang = ? AND target_lang = ?
        """, (source_text, source_lang, target_lang))
        row = cursor.fetchone()
        return row[0] if row else None

    def set(self, source_text, source_lang, target_lang, translated_text):
        with self.conn:
            self.conn.execute("""
                INSERT OR REPLACE INTO cache (source_text, source_lang, target_lang, translated_text)
                VALUES (?, ?, ?, ?)
            """, (source_text, source_lang, target_lang, translated_text))

    def clear(self):
        with self.conn:
            self.conn.execute("DELETE FROM cache")

translation_cache = TranslationCache()
