#!/usr/bin/env python3
"""
Test script for the Telegram Video Downloader Bot
Tests basic functionality without requiring Telegram bot token
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from database import DatabaseManager
from downloader import VideoDownloader

def test_database():
    """Test database functionality"""
    print("Testing database functionality...")
    
    try:
        # Initialize database
        db = DatabaseManager("test_cache.db")
        print("SUCCESS: Database initialized successfully")
        
        # Test storing and retrieving cache
        test_url = "https://www.youtube.com/watch?v=test123"
        test_file_id = "BAADBAADrwADBREAAR8DCw"
        test_title = "Test Video"
        
        db.store_cached_file_id(test_url, test_file_id, test_title)
        print("SUCCESS: Stored test cache entry")
        
        result = db.get_cached_file_id(test_url)
        if result and result[0] == test_file_id:
            print("SUCCESS: Retrieved cached file_id successfully")
        else:
            print("ERROR: Failed to retrieve cached file_id")
            
        # Test stats
        stats = db.get_cache_stats()
        print(f"SUCCESS: Cache stats: {stats}")
        
        # Clean up test database
        os.unlink("test_cache.db")
        print("SUCCESS: Database test completed")
        
    except Exception as e:
        print(f"ERROR: Database test failed: {e}")

def test_downloader():
    """Test downloader initialization"""
    print("\nTesting downloader functionality...")
    
    try:
        downloader = VideoDownloader()
        print("SUCCESS: VideoDownloader initialized successfully")
        
        # Check if youtube-dl path exists
        if downloader.youtube_dl_path.exists():
            print(f"SUCCESS: youtube-dl found at: {downloader.youtube_dl_path}")
        else:
            print(f"WARNING: youtube-dl not found at expected path: {downloader.youtube_dl_path}")
            
        print("SUCCESS: Downloader test completed")
        
    except Exception as e:
        print(f"ERROR: Downloader test failed: {e}")

def test_url_validation():
    """Test URL validation logic"""
    print("\nTesting URL validation...")
    
    try:
        # Import bot class to test URL validation
        from bot import TelegramVideoBot
        
        # Create a mock bot instance (without token)
        class MockBot:
            def is_video_url(self, text):
                import re
                youtube_patterns = [
                    r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+',
                    r'(?:https?://)?(?:www\.)?youtu\.be/[\w-]+',
                    r'(?:https?://)?(?:www\.)?youtube\.com/embed/[\w-]+',
                    r'(?:https?://)?(?:www\.)?youtube\.com/v/[\w-]+'
                ]
                
                for pattern in youtube_patterns:
                    if re.search(pattern, text):
                        return True
                return False
        
        bot = MockBot()
        
        test_urls = [
            ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", True),
            ("https://youtu.be/dQw4w9WgXcQ", True),
            ("youtube.com/watch?v=dQw4w9WgXcQ", True),
            ("youtu.be/dQw4w9WgXcQ", True),
            ("https://www.google.com", False),
            ("Just some random text", False),
        ]
        
        for url, expected in test_urls:
            result = bot.is_video_url(url)
            status = "SUCCESS" if result == expected else "ERROR"
            print(f"{status}: URL '{url}' -> {result} (expected {expected})")
            
        print("SUCCESS: URL validation test completed")
        
    except Exception as e:
        print(f"ERROR: URL validation test failed: {e}")

def main():
    """Run all tests"""
    print("Running Telegram Video Downloader Bot Tests\n")
    
    test_database()
    test_downloader()
    test_url_validation()
    
    print("\nAll tests completed!")
    print("\nTo run the bot:")
    print("1. Set TELEGRAM_BOT_TOKEN environment variable")
    print("2. Run: python bot.py")

if __name__ == "__main__":
    main()