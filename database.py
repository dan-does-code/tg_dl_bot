import sqlite3
import logging
from pathlib import Path

class DatabaseManager:
    def __init__(self, db_path="video_cache.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize SQLite database with enhanced video cache table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if we need to migrate from old schema
        cursor.execute("PRAGMA table_info(video_cache)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if not columns:  # Table doesn't exist, create new schema
            self._create_enhanced_schema(cursor)
        elif 'quality' not in columns or 'format_type' not in columns:
            # Old schema exists, need migration
            self._migrate_to_enhanced_schema(cursor)
            
        # Create user settings table if it doesn't exist
        self._create_user_settings_table(cursor)
        
        conn.commit()
        conn.close()
        
    def _create_enhanced_schema(self, cursor):
        """Create the enhanced schema from scratch"""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS video_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                quality TEXT DEFAULT 'auto',
                format_type TEXT DEFAULT 'video',
                file_id TEXT NOT NULL,
                title TEXT,
                duration INTEGER,
                file_size INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(url, quality, format_type)
            )
        ''')
        
        # Create optimized indexes for compound key lookups
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_url_quality_format ON video_cache(url, quality, format_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_url ON video_cache(url)')  # For backward compatibility
        
    def _migrate_to_enhanced_schema(self, cursor):
        """Migrate existing schema to enhanced version"""
        logging.info("Migrating database schema to enhanced version...")
        
        # Check if migration already completed
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='video_cache_old'")
        if cursor.fetchone():
            logging.info("Migration already completed")
            return
        
        # Step 1: Rename old table to backup
        cursor.execute('ALTER TABLE video_cache RENAME TO video_cache_old')
        
        # Step 2: Create new table with enhanced schema
        self._create_enhanced_schema(cursor)
        
        # Step 3: Migrate existing data with default quality/format values
        cursor.execute('''
            INSERT INTO video_cache 
            (url, quality, format_type, file_id, title, duration, file_size, created_at, last_accessed)
            SELECT url, 'auto', 'video', file_id, title, duration, file_size, created_at, last_accessed
            FROM video_cache_old
        ''')
        
        # Step 4: Drop old table (commented out for safety - can be removed after verification)
        # cursor.execute('DROP TABLE video_cache_old')
        
        logging.info("Database migration completed successfully")
        
    def _create_user_settings_table(self, cursor):
        """Create user settings table for storing user preferences"""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                min_quality TEXT,
                max_quality TEXT,
                min_file_size_mb INTEGER,
                max_file_size_mb INTEGER,
                quick_mode_enabled BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create index for user lookups
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_settings ON user_settings(user_id)')
        
    def get_cached_file_id(self, url, quality=None, format_type=None):
        """
        Retrieve cached file_id for a given URL with optional quality/format.
        
        For backward compatibility:
        - If quality/format not specified, tries to find any cached version
        - If quality/format specified, looks for exact match first, then falls back to any version
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        result = None
        
        if quality and format_type:
            # Try exact match first
            cursor.execute('''
                SELECT file_id, title, quality, format_type FROM video_cache 
                WHERE url = ? AND quality = ? AND format_type = ?
            ''', (url, quality, format_type))
            result = cursor.fetchone()
            
        if not result:
            # Fallback to any cached version for this URL (backward compatibility)
            cursor.execute('''
                SELECT file_id, title, quality, format_type FROM video_cache 
                WHERE url = ?
                ORDER BY last_accessed DESC
                LIMIT 1
            ''', (url,))
            result = cursor.fetchone()
        
        if result:
            # Update last_accessed timestamp
            file_id, title, cached_quality, cached_format = result
            cursor.execute('''
                UPDATE video_cache 
                SET last_accessed = CURRENT_TIMESTAMP 
                WHERE url = ? AND quality = ? AND format_type = ?
            ''', (url, cached_quality, cached_format))
            conn.commit()
            
            # Return in old format for backward compatibility
            conn.close()
            return (file_id, title)
            
        conn.close()
        return None
        
    def get_cached_file_id_compound(self, url, quality, format_type):
        """
        Retrieve cached file_id for exact URL + quality + format combination.
        Returns full details including quality and format info.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT file_id, title, quality, format_type, file_size, duration FROM video_cache 
            WHERE url = ? AND quality = ? AND format_type = ?
        ''', (url, quality, format_type))
        
        result = cursor.fetchone()
        
        if result:
            # Update last_accessed timestamp
            cursor.execute('''
                UPDATE video_cache 
                SET last_accessed = CURRENT_TIMESTAMP 
                WHERE url = ? AND quality = ? AND format_type = ?
            ''', (url, quality, format_type))
            conn.commit()
            
        conn.close()
        return result
        
    def store_cached_file_id(self, url, file_id, title=None, duration=None, file_size=None, quality='auto', format_type='video'):
        """
        Store file_id for a URL in cache with quality and format support.
        
        For backward compatibility, defaults to quality='auto' and format_type='video'
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO video_cache 
            (url, quality, format_type, file_id, title, duration, file_size, created_at, last_accessed)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', (url, quality, format_type, file_id, title, duration, file_size))
        
        conn.commit()
        conn.close()
        
    def store_cached_file_id_compound(self, url, quality, format_type, file_id, title=None, duration=None, file_size=None):
        """
        Store file_id for a specific URL + quality + format combination.
        This is the preferred method for new compound key storage.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO video_cache 
            (url, quality, format_type, file_id, title, duration, file_size, created_at, last_accessed)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', (url, quality, format_type, file_id, title, duration, file_size))
        
        conn.commit()
        conn.close()
        
    def get_cache_stats(self):
        """Get enhanced cache statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total cached videos
        cursor.execute('SELECT COUNT(*) FROM video_cache')
        total_cached = cursor.fetchone()[0]
        
        # Breakdown by format type
        cursor.execute('SELECT format_type, COUNT(*) FROM video_cache GROUP BY format_type')
        format_breakdown = dict(cursor.fetchall())
        
        # Breakdown by quality
        cursor.execute('SELECT quality, COUNT(*) FROM video_cache GROUP BY quality')
        quality_breakdown = dict(cursor.fetchall())
        
        conn.close()
        return {
            "total_cached": total_cached,
            "by_format": format_breakdown,
            "by_quality": quality_breakdown
        }
    
    def get_user_settings(self, user_id):
        """Get user settings for a specific user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT min_quality, max_quality, min_file_size_mb, max_file_size_mb, quick_mode_enabled
            FROM user_settings WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'min_quality': result[0],
                'max_quality': result[1],
                'min_file_size_mb': result[2],
                'max_file_size_mb': result[3],
                'quick_mode_enabled': bool(result[4])
            }
        else:
            # Return default settings
            return {
                'min_quality': None,
                'max_quality': None,
                'min_file_size_mb': None,
                'max_file_size_mb': None,
                'quick_mode_enabled': False
            }
    
    def update_user_settings(self, user_id, **settings):
        """Update user settings for a specific user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get current settings first
        current_settings = self.get_user_settings(user_id)
        
        # Update with new values
        for key, value in settings.items():
            if key in current_settings:
                current_settings[key] = value
        
        # Insert or replace the settings
        cursor.execute('''
            INSERT OR REPLACE INTO user_settings 
            (user_id, min_quality, max_quality, min_file_size_mb, max_file_size_mb, quick_mode_enabled, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            user_id,
            current_settings['min_quality'],
            current_settings['max_quality'],
            current_settings['min_file_size_mb'],
            current_settings['max_file_size_mb'],
            current_settings['quick_mode_enabled']
        ))
        
        conn.commit()
        conn.close()
    
    def clear_user_settings(self, user_id):
        """Clear all settings for a user (reset to defaults)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM user_settings WHERE user_id = ?', (user_id,))
        
        conn.commit()
        conn.close()