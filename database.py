import sqlite3
import logging
from pathlib import Path

class DatabaseManager:
    def __init__(self, db_path="video_cache.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize SQLite database with video cache table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS video_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                file_id TEXT NOT NULL,
                title TEXT,
                duration INTEGER,
                file_size INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create index for faster URL lookups
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_url ON video_cache(url)')
        
        conn.commit()
        conn.close()
        
    def get_cached_file_id(self, url):
        """Retrieve cached file_id for a given URL"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT file_id, title FROM video_cache 
            WHERE url = ?
        ''', (url,))
        
        result = cursor.fetchone()
        
        if result:
            # Update last_accessed timestamp
            cursor.execute('''
                UPDATE video_cache 
                SET last_accessed = CURRENT_TIMESTAMP 
                WHERE url = ?
            ''', (url,))
            conn.commit()
            
        conn.close()
        return result
        
    def store_cached_file_id(self, url, file_id, title=None, duration=None, file_size=None):
        """Store file_id for a URL in cache"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO video_cache 
            (url, file_id, title, duration, file_size, created_at, last_accessed)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', (url, file_id, title, duration, file_size))
        
        conn.commit()
        conn.close()
        
    def get_cache_stats(self):
        """Get cache statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM video_cache')
        total_cached = cursor.fetchone()[0]
        
        conn.close()
        return {"total_cached": total_cached}