import logging
import os
import re
import asyncio
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from database import DatabaseManager
from downloader import VideoDownloader

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramVideoBot:
    def __init__(self, token):
        self.token = token
        self.db = DatabaseManager()
        self.downloader = VideoDownloader()
        self.application = Application.builder().token(token).build()
        
        # Setup handlers
        self.setup_handlers()
        
    def setup_handlers(self):
        """Setup command and message handlers"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = (
            "🎥 Welcome to Video Downloader Bot!\n\n"
            "Send me a YouTube video URL and I'll download it for you.\n"
            "The bot uses smart caching - popular videos are served instantly!\n\n"
            "Commands:\n"
            "/help - Show this help message\n"
            "/stats - Show cache statistics"
        )
        await update.message.reply_text(welcome_message)
        
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = (
            "🎥 Video Downloader Bot Help\n\n"
            "📹 **How to use:**\n"
            "Just send me a YouTube video URL and I'll download it for you!\n\n"
            "⚡ **Smart Caching:**\n"
            "Popular videos are cached and served instantly on repeat requests.\n\n"
            "📊 **Commands:**\n"
            "/start - Welcome message\n"
            "/help - This help message\n"
            "/stats - Cache statistics\n\n"
            "🚀 **Supported platforms:**\n"
            "• YouTube (youtube.com, youtu.be)\n"
            "• More platforms coming soon!\n\n"
            "💡 **Tips:**\n"
            "• Videos are limited to 720p for faster downloads\n"
            "• Large files may take a few minutes to process"
        )
        await update.message.reply_text(help_message, parse_mode='Markdown')
        
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        stats = self.db.get_cache_stats()
        stats_message = (
            f"📊 **Cache Statistics**\n\n"
            f"🎥 Total cached videos: {stats['total_cached']}\n"
            f"💾 Cache hit rate: Calculated after more usage\n\n"
            f"This helps reduce download times and server costs!"
        )
        await update.message.reply_text(stats_message, parse_mode='Markdown')
        
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages (potential video URLs)"""
        message_text = update.message.text.strip()
        
        # Check if message contains a video URL
        if not self.is_video_url(message_text):
            await update.message.reply_text(
                "Please send me a valid YouTube video URL.\n"
                "Example: https://www.youtube.com/watch?v=VIDEO_ID"
            )
            return
            
        # Process the video URL
        await self.process_video_url(update, message_text)
        
    def is_video_url(self, text):
        """Check if text contains a valid video URL"""
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
        
    async def process_video_url(self, update: Update, url):
        """Process video URL - check cache first, then download if needed"""
        # Send initial processing message
        processing_msg = await update.message.reply_text("🔍 Processing video URL...")
        
        try:
            # Check cache first (CACHE HIT PATH)
            cached_result = self.db.get_cached_file_id(url)
            
            if cached_result:
                file_id, title = cached_result
                await processing_msg.edit_text(f"⚡ Found in cache! Sending: {title}")
                
                try:
                    # Send cached video using file_id
                    await update.message.reply_video(
                        video=file_id,
                        caption=f"🎥 {title}\n\n⚡ Served from cache (instant delivery!)"
                    )
                    logger.info(f"Cache HIT for URL: {url}")
                    return
                    
                except Exception as e:
                    logger.warning(f"Failed to send cached video: {e}")
                    await processing_msg.edit_text("⚠️ Cached video failed, downloading fresh copy...")
                    
            # CACHE MISS PATH - Download video
            await processing_msg.edit_text("📥 Downloading video... This may take a few minutes.")
            
            # Download video in a separate thread to avoid blocking
            download_result = await asyncio.get_event_loop().run_in_executor(
                None, self.downloader.download_video, url
            )
            
            if not download_result:
                await processing_msg.edit_text("❌ Failed to download video. Please check the URL and try again.")
                return
                
            file_path, title, duration, file_size = download_result
            
            # Check file size limit (Telegram has 50MB limit for bots)
            if file_size > 50 * 1024 * 1024:  # 50MB
                await processing_msg.edit_text(f"❌ Video too large ({file_size // 1024 // 1024}MB). Telegram limit is 50MB.")
                # Clean up
                Path(file_path).unlink(missing_ok=True)
                return
                
            await processing_msg.edit_text(f"📤 Uploading: {title}")
            
            # Upload video to Telegram
            with open(file_path, 'rb') as video_file:
                message = await update.message.reply_video(
                    video=video_file,
                    caption=f"🎥 {title}\n\n📥 Fresh download (will be cached for future requests)",
                    duration=duration,
                    supports_streaming=True
                )
                
                # Extract file_id from uploaded video
                file_id = message.video.file_id
                
                # Store in cache for future requests
                self.db.store_cached_file_id(url, file_id, title, duration, file_size)
                
                logger.info(f"Cache MISS - Downloaded and cached: {title}")
                
            # Clean up temporary file
            Path(file_path).unlink(missing_ok=True)
            
            # Update final message
            await processing_msg.edit_text("✅ Video processed and cached for future requests!")
            
        except Exception as e:
            logger.error(f"Error processing video: {e}")
            await processing_msg.edit_text(f"❌ Error processing video: {str(e)}")
            
    def run(self):
        """Run the bot"""
        logger.info("Starting Telegram Video Downloader Bot...")
        self.application.run_polling()

def main():
    # Get bot token from environment variable
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set!")
        logger.info("Please set your bot token: export TELEGRAM_BOT_TOKEN='your_bot_token_here'")
        return
        
    # Initialize and run bot
    bot = TelegramVideoBot(bot_token)
    bot.run()

if __name__ == "__main__":
    main()