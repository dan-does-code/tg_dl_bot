import logging
import os
import re
import asyncio
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
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
        
        # Temporary storage for format data during user selection
        self.format_cache = {}  # {user_id: {url: format_data}}
        
        # Setup handlers
        self.setup_handlers()
        
    def setup_handlers(self):
        """Setup command and message handlers"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("settings", self.settings_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.application.add_handler(CallbackQueryHandler(self.handle_callback_query))
        
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
            "/stats - Cache statistics\n"
            "/settings - Configure download preferences\n\n"
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
        
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /settings command"""
        user_id = update.effective_user.id
        settings = self.db.get_user_settings(user_id)
        
        # Create settings display message
        settings_message = (
            "⚙️ **Your Download Settings**\n\n"
            f"📐 **Quality Constraints:**\n"
            f"  • Minimum: {settings['min_quality'] or 'None'}\n"
            f"  • Maximum: {settings['max_quality'] or 'None'}\n\n"
            f"📊 **File Size Constraints:**\n"
            f"  • Minimum: {settings['min_file_size_mb'] or 'None'} MB\n"
            f"  • Maximum: {settings['max_file_size_mb'] or 'None'} MB\n\n"
            f"🚀 **Quick Mode:** {'Enabled' if settings['quick_mode_enabled'] else 'Disabled'}\n\n"
            f"Use the buttons below to modify your settings:"
        )
        
        # Create settings keyboard
        keyboard = self.create_settings_keyboard(settings)
        
        await update.message.reply_text(
            text=settings_message,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
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
            
        # Process the video URL with quality selection
        await self.handle_video_url_with_selection(update, message_text)
        
    async def handle_video_url_with_selection(self, update: Update, url):
        """Handle video URL with interactive quality selection"""
        user_id = update.effective_user.id
        
        # Send initial processing message
        processing_msg = await update.message.reply_text("🔍 Detecting available qualities...")
        
        try:
            # Check if we have any cached version first (for instant delivery option)
            cached_result = self.db.get_cached_file_id(url)
            has_cached = cached_result is not None
            
            # Detect available formats
            format_detection_result = await asyncio.get_event_loop().run_in_executor(
                None, self.downloader.detect_available_formats, url
            )
            
            if not format_detection_result:
                # Fallback to direct download if format detection fails
                await processing_msg.edit_text("⚠️ Could not detect qualities. Downloading with default quality...")
                await self.process_video_url_direct(update, url, processing_msg)
                return
            
            # Store format data for user selection
            if user_id not in self.format_cache:
                self.format_cache[user_id] = {}
            self.format_cache[user_id][url] = format_detection_result
            
            # Check if user has quick mode enabled with constraints
            user_settings = self.db.get_user_settings(user_id)
            if user_settings['quick_mode_enabled'] and self._has_constraints(user_settings):
                # Try quick download with constraint matching
                best_match = self._find_best_matching_format(format_detection_result, user_settings)
                
                if best_match:
                    # Automatically download the best match
                    await processing_msg.edit_text(f"🚀 Quick mode: Auto-selecting {best_match['quality_text']}...")
                    await self._download_quick_mode_selection(update, url, best_match, processing_msg)
                    return
                else:
                    # No formats match constraints, show interactive selection with explanation
                    await processing_msg.edit_text("⚠️ No formats match your constraints. Showing available options...")
                    await asyncio.sleep(1)  # Brief pause to show message
            
            # Create quality selection keyboard
            keyboard = self.create_quality_selection_keyboard(url, format_detection_result, has_cached)
            
            # Update message with quality selection
            title = format_detection_result['title']
            duration_text = f" ({format_detection_result['duration']//60}:{format_detection_result['duration']%60:02d})" if format_detection_result['duration'] else ""
            
            selection_msg = (
                f"🎥 **{title}**{duration_text}\n\n"
                f"📊 Choose your preferred quality:\n"
                f"{'🚀 Cached version available for instant delivery!' if has_cached else ''}"
            )
            
            await processing_msg.edit_text(
                text=selection_msg,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in quality selection: {e}")
            await processing_msg.edit_text("⚠️ Error detecting qualities. Trying direct download...")
            await self.process_video_url_direct(update, url, processing_msg)
    
    def create_quality_selection_keyboard(self, url, format_data, has_cached=False):
        """Create inline keyboard for quality selection"""
        keyboard = []
        
        # Add cached version option if available
        if has_cached:
            keyboard.append([
                InlineKeyboardButton("🚀 Instant (Cached)", callback_data=f"cached:{url}")
            ])
        
        # Add video quality options
        video_formats = format_data['formats']['video']
        if video_formats:
            # Group video formats in rows of 2 or 3
            for i in range(0, len(video_formats), 2):
                row = []
                for j in range(i, min(i + 2, len(video_formats))):
                    fmt = video_formats[j]
                    quality = fmt['quality']
                    file_size = f" ({fmt['filesize_mb']}MB)" if fmt['filesize_mb'] > 0 else ""
                    button_text = f"🎥 {quality}{file_size}"
                    callback_data = f"video:{url}:{fmt['format_id']}"
                    row.append(InlineKeyboardButton(button_text, callback_data=callback_data))
                keyboard.append(row)
        
        # Add audio-only options
        audio_formats = format_data['formats']['audio']
        if audio_formats:
            # Take the best audio format (first one, since they're sorted by quality)
            best_audio = audio_formats[0]
            file_size = f" ({best_audio['filesize_mb']}MB)" if best_audio['filesize_mb'] > 0 else ""
            button_text = f"🎵 Audio Only{file_size}"
            callback_data = f"audio:{url}:{best_audio['format_id']}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        # Add cancel option
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data=f"cancel:{url}")])
        
        return InlineKeyboardMarkup(keyboard)
    
    def create_settings_keyboard(self, settings):
        """Create inline keyboard for settings management"""
        keyboard = []
        
        # Quality constraints section
        keyboard.append([
            InlineKeyboardButton("📐 Set Min Quality", callback_data="setting:min_quality"),
            InlineKeyboardButton("📐 Set Max Quality", callback_data="setting:max_quality")
        ])
        
        # File size constraints section
        keyboard.append([
            InlineKeyboardButton("📊 Set Min Size", callback_data="setting:min_size"),
            InlineKeyboardButton("📊 Set Max Size", callback_data="setting:max_size")
        ])
        
        # Quick mode toggle
        quick_mode_text = "🚀 Disable Quick Mode" if settings['quick_mode_enabled'] else "🚀 Enable Quick Mode"
        keyboard.append([
            InlineKeyboardButton(quick_mode_text, callback_data="setting:toggle_quick_mode")
        ])
        
        # Management options
        keyboard.append([
            InlineKeyboardButton("🔄 Reset All", callback_data="setting:reset_all"),
            InlineKeyboardButton("❌ Close", callback_data="setting:close")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard button callbacks"""
        query = update.callback_query
        await query.answer()  # Acknowledge the callback
        
        try:
            # Parse callback data
            callback_data = query.data
            
            # Find first colon to separate action
            first_colon = callback_data.find(':')
            if first_colon == -1:
                await query.edit_message_text("❌ Invalid selection. Please try again.")
                return
            
            action = callback_data[:first_colon]
            remainder = callback_data[first_colon + 1:]
            
            if action == "cancel":
                # Handle cancellation
                await query.edit_message_text("❌ Download cancelled.")
                self._cleanup_user_cache(query.from_user.id, remainder)
                return
            
            elif action == "cached":
                # Handle cached version selection
                await self.download_cached_version(query, remainder)
                
            elif action in ["video", "audio"]:
                # Handle specific format selection - parse format_id from end
                last_colon = remainder.rfind(':')
                if last_colon == -1:
                    await query.edit_message_text("❌ Invalid format selection. Please try again.")
                    return
                
                url = remainder[:last_colon]
                format_id = remainder[last_colon + 1:]
                await self.download_selected_format(query, url, format_id, action)
                
            elif action == "setting":
                # Handle settings callback
                await self.handle_settings_callback(query, remainder)
                
            elif action == "quality_set":
                # Handle quality setting callback
                await self.handle_quality_set_callback(query, remainder)
                
            elif action == "size_set":
                # Handle size setting callback
                await self.handle_size_set_callback(query, remainder)
            
            else:
                await query.edit_message_text("❌ Unknown selection. Please try again.")
                
        except Exception as e:
            logger.error(f"Error handling callback query: {e}")
            await query.edit_message_text("❌ Error processing your selection. Please try again.")
    
    async def download_cached_version(self, query, url):
        """Download and send cached version immediately"""
        try:
            cached_result = self.db.get_cached_file_id(url)
            
            if not cached_result:
                await query.edit_message_text("❌ Cached version no longer available. Please select a quality.")
                return
            
            file_id, title = cached_result
            await query.edit_message_text(f"🚀 Sending cached version: {title}")
            
            # Send cached video
            await query.message.reply_video(
                video=file_id,
                caption=f"🎥 {title}\n\n⚡ Served from cache (instant delivery!)"
            )
            
            # Clean up
            self._cleanup_user_cache(query.from_user.id, url)
            logger.info(f"Cache HIT via selection for URL: {url}")
            
        except Exception as e:
            logger.error(f"Error sending cached video: {e}")
            await query.edit_message_text("❌ Error sending cached video. Please try selecting a quality.")
    
    async def download_selected_format(self, query, url, format_id, format_type):
        """Download video with selected format"""
        user_id = query.from_user.id
        
        try:
            # Get format information from cache
            if user_id not in self.format_cache or url not in self.format_cache[user_id]:
                await query.edit_message_text("❌ Session expired. Please send the URL again.")
                return
            
            format_data = self.format_cache[user_id][url]
            title = format_data['title']
            
            # Find the selected format details
            selected_format = None
            formats_list = format_data['formats']['video'] if format_type == 'video' else format_data['formats']['audio']
            
            for fmt in formats_list:
                if fmt['format_id'] == format_id:
                    selected_format = fmt
                    break
            
            if not selected_format:
                await query.edit_message_text("❌ Selected format no longer available. Please try again.")
                return
            
            # Check cache first for this specific quality/format combination (CACHE HIT PATH)
            quality = selected_format['quality']
            format_type_db = 'audio' if format_type == 'audio' else 'video'
            cached_result = self.db.get_cached_file_id_compound(url, quality, format_type_db)
            
            if cached_result:
                file_id, cached_title, cached_quality, cached_format, cached_file_size, cached_duration = cached_result
                quality_text = cached_quality if format_type == 'video' else 'Audio Only'
                await query.edit_message_text(f"⚡ Found in cache! Sending {quality_text}: {cached_title}")
                
                try:
                    # Send cached video using file_id
                    if format_type == 'video':
                        await query.message.reply_video(
                            video=file_id,
                            caption=f"🎥 {cached_title} ({quality_text})\n\n⚡ Served from cache (instant delivery!)",
                            duration=cached_duration,
                            supports_streaming=True
                        )
                    else:
                        await query.message.reply_audio(
                            audio=file_id,
                            caption=f"🎵 {cached_title} (Audio Only)\n\n⚡ Served from cache (instant delivery!)",
                            duration=cached_duration
                        )
                    
                    # Clean up and log cache hit
                    self._cleanup_user_cache(user_id, url)
                    logger.info(f"Compound key cache HIT for URL: {url}, Quality: {quality}, Format: {format_type_db}")
                    return
                    
                except Exception as e:
                    logger.warning(f"Failed to send cached video with compound key: {e}")
                    await query.edit_message_text("⚠️ Cached video failed, downloading fresh copy...")
            
            # CACHE MISS PATH - Download video with specific format
            quality_text = selected_format['quality'] if format_type == 'video' else 'Audio Only'
            await query.edit_message_text(f"📥 Downloading {quality_text}: {title}...")
            
            # Download with specific format
            download_result = await asyncio.get_event_loop().run_in_executor(
                None, self.downloader.download_video, url, format_id
            )
            
            if not download_result:
                await query.edit_message_text("❌ Download failed. Please try again.")
                return
            
            file_path, title, duration, file_size = download_result
            
            # Check file size limit
            if file_size > 50 * 1024 * 1024:  # 50MB
                await query.edit_message_text(f"❌ File too large ({file_size // 1024 // 1024}MB). Telegram limit is 50MB.")
                Path(file_path).unlink(missing_ok=True)
                return
            
            # Upload to Telegram
            await query.edit_message_text(f"📤 Uploading {quality_text}: {title}")
            
            with open(file_path, 'rb') as media_file:
                if format_type == 'video':
                    message = await query.message.reply_video(
                        video=media_file,
                        caption=f"🎥 {title} ({quality_text})\n\n📥 Downloaded and cached for future requests",
                        duration=duration,
                        supports_streaming=True
                    )
                    file_id = message.video.file_id
                else:
                    message = await query.message.reply_audio(
                        audio=media_file,
                        caption=f"🎵 {title} (Audio Only)\n\n📥 Downloaded and cached for future requests",
                        duration=duration
                    )
                    file_id = message.audio.file_id
            
            # Store in enhanced cache with compound key
            quality = selected_format['quality']
            format_type_db = 'audio' if format_type == 'audio' else 'video'
            self.db.store_cached_file_id_compound(url, quality, format_type_db, file_id, title, duration, file_size)
            
            # Clean up
            Path(file_path).unlink(missing_ok=True)
            self._cleanup_user_cache(user_id, url)
            
            logger.info(f"Downloaded and cached: {title} ({quality_text})")
            
        except Exception as e:
            logger.error(f"Error downloading selected format: {e}")
            await query.edit_message_text(f"❌ Download error: {str(e)}")
    
    async def handle_settings_callback(self, query, setting_action):
        """Handle settings-related callback queries"""
        user_id = query.from_user.id
        
        try:
            if setting_action == "close":
                # Close settings menu
                await query.edit_message_text("⚙️ Settings menu closed.")
                return
                
            elif setting_action == "reset_all":
                # Reset all settings to defaults
                self.db.clear_user_settings(user_id)
                await query.edit_message_text(
                    "🔄 All settings have been reset to defaults.\n\n"
                    "Use /settings to configure your preferences again."
                )
                return
                
            elif setting_action == "toggle_quick_mode":
                # Toggle quick mode
                current_settings = self.db.get_user_settings(user_id)
                new_quick_mode = not current_settings['quick_mode_enabled']
                self.db.update_user_settings(user_id, quick_mode_enabled=new_quick_mode)
                
                # Refresh settings display
                updated_settings = self.db.get_user_settings(user_id)
                settings_message = (
                    "⚙️ **Your Download Settings**\n\n"
                    f"📐 **Quality Constraints:**\n"
                    f"  • Minimum: {updated_settings['min_quality'] or 'None'}\n"
                    f"  • Maximum: {updated_settings['max_quality'] or 'None'}\n\n"
                    f"📊 **File Size Constraints:**\n"
                    f"  • Minimum: {updated_settings['min_file_size_mb'] or 'None'} MB\n"
                    f"  • Maximum: {updated_settings['max_file_size_mb'] or 'None'} MB\n\n"
                    f"🚀 **Quick Mode:** {'Enabled' if updated_settings['quick_mode_enabled'] else 'Disabled'}\n\n"
                    f"Use the buttons below to modify your settings:"
                )
                
                keyboard = self.create_settings_keyboard(updated_settings)
                await query.edit_message_text(
                    text=settings_message,
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
                
            elif setting_action in ["min_quality", "max_quality"]:
                # Show quality selection interface
                await self.show_quality_selection(query, setting_action)
                
            elif setting_action in ["min_size", "max_size"]:
                # Show file size selection interface
                await self.show_size_selection(query, setting_action)
                
            elif setting_action == "back_to_main":
                # Return to main settings menu
                await self.show_main_settings(query)
                
            else:
                await query.edit_message_text("❌ Unknown settings action.")
                
        except Exception as e:
            logger.error(f"Error handling settings callback: {e}")
            await query.edit_message_text("❌ Error updating settings. Please try again.")
    
    async def show_quality_selection(self, query, quality_type):
        """Show quality selection interface for min/max quality settings"""
        quality_options = ['240p', '360p', '480p', '720p', '1080p']
        
        keyboard = []
        
        # Add quality options in rows of 2
        for i in range(0, len(quality_options), 2):
            row = []
            for j in range(i, min(i + 2, len(quality_options))):
                quality = quality_options[j]
                callback_data = f"quality_set:{quality_type}:{quality}"
                row.append(InlineKeyboardButton(f"📐 {quality}", callback_data=callback_data))
            keyboard.append(row)
        
        # Add clear option and back button
        keyboard.append([
            InlineKeyboardButton("🚫 Clear", callback_data=f"quality_set:{quality_type}:clear"),
            InlineKeyboardButton("⬅️ Back", callback_data="setting:back_to_main")
        ])
        
        quality_name = "Minimum" if quality_type == "min_quality" else "Maximum"
        message = f"📐 **Set {quality_name} Quality**\n\nSelect your preferred {quality_name.lower()} video quality:"
        
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def show_size_selection(self, query, size_type):
        """Show file size selection interface for min/max size settings"""
        size_options = [1, 5, 10, 20, 30, 50]  # MB options
        
        keyboard = []
        
        # Add size options in rows of 3
        for i in range(0, len(size_options), 3):
            row = []
            for j in range(i, min(i + 3, len(size_options))):
                size_mb = size_options[j]
                callback_data = f"size_set:{size_type}:{size_mb}"
                row.append(InlineKeyboardButton(f"📊 {size_mb}MB", callback_data=callback_data))
            keyboard.append(row)
        
        # Add clear option and back button
        keyboard.append([
            InlineKeyboardButton("🚫 Clear", callback_data=f"size_set:{size_type}:clear"),
            InlineKeyboardButton("⬅️ Back", callback_data="setting:back_to_main")
        ])
        
        size_name = "Minimum" if size_type == "min_size" else "Maximum"
        message = f"📊 **Set {size_name} File Size**\n\nSelect your preferred {size_name.lower()} file size limit:"
        
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def show_main_settings(self, query):
        """Show the main settings menu"""
        user_id = query.from_user.id
        settings = self.db.get_user_settings(user_id)
        
        settings_message = (
            "⚙️ **Your Download Settings**\n\n"
            f"📐 **Quality Constraints:**\n"
            f"  • Minimum: {settings['min_quality'] or 'None'}\n"
            f"  • Maximum: {settings['max_quality'] or 'None'}\n\n"
            f"📊 **File Size Constraints:**\n"
            f"  • Minimum: {settings['min_file_size_mb'] or 'None'} MB\n"
            f"  • Maximum: {settings['max_file_size_mb'] or 'None'} MB\n\n"
            f"🚀 **Quick Mode:** {'Enabled' if settings['quick_mode_enabled'] else 'Disabled'}\n\n"
            f"Use the buttons below to modify your settings:"
        )
        
        keyboard = self.create_settings_keyboard(settings)
        await query.edit_message_text(
            text=settings_message,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    async def handle_quality_set_callback(self, query, remainder):
        """Handle quality setting callbacks"""
        user_id = query.from_user.id
        
        # Parse remainder: quality_type:value
        parts = remainder.split(':', 1)
        if len(parts) != 2:
            await query.edit_message_text("❌ Invalid quality setting. Please try again.")
            return
            
        quality_type, value = parts
        
        # Update setting with validation
        if value == "clear":
            if quality_type == "min_quality":
                self.db.update_user_settings(user_id, min_quality=None)
            else:  # max_quality
                self.db.update_user_settings(user_id, max_quality=None)
        else:
            # Validate the new quality constraint
            current_settings = self.db.get_user_settings(user_id)
            
            if quality_type == "min_quality":
                # Check if new min_quality <= existing max_quality
                if current_settings['max_quality'] and not self._validate_quality_range(value, current_settings['max_quality']):
                    await query.edit_message_text(
                        f"❌ Invalid constraint: Minimum quality {value} cannot be higher than maximum quality {current_settings['max_quality']}.\n\n"
                        f"Please adjust your maximum quality first or choose a lower minimum quality."
                    )
                    await asyncio.sleep(2)
                    await self.show_quality_selection(query, quality_type)
                    return
                self.db.update_user_settings(user_id, min_quality=value)
            else:  # max_quality
                # Check if existing min_quality <= new max_quality
                if current_settings['min_quality'] and not self._validate_quality_range(current_settings['min_quality'], value):
                    await query.edit_message_text(
                        f"❌ Invalid constraint: Maximum quality {value} cannot be lower than minimum quality {current_settings['min_quality']}.\n\n"
                        f"Please adjust your minimum quality first or choose a higher maximum quality."
                    )
                    await asyncio.sleep(2)
                    await self.show_quality_selection(query, quality_type)
                    return
                self.db.update_user_settings(user_id, max_quality=value)
        
        # Show success message and return to main settings
        quality_name = "Minimum" if quality_type == "min_quality" else "Maximum"
        if value == "clear":
            await query.edit_message_text(f"✅ {quality_name} quality constraint cleared!")
        else:
            await query.edit_message_text(f"✅ {quality_name} quality set to {value}!")
        
        # Auto-return to main settings after a brief moment
        await asyncio.sleep(1)
        await self.show_main_settings(query)
    
    async def handle_size_set_callback(self, query, remainder):
        """Handle file size setting callbacks"""
        user_id = query.from_user.id
        
        # Parse remainder: size_type:value
        parts = remainder.split(':', 1)
        if len(parts) != 2:
            await query.edit_message_text("❌ Invalid size setting. Please try again.")
            return
            
        size_type, value = parts
        
        # Update setting with validation
        if value == "clear":
            if size_type == "min_size":
                self.db.update_user_settings(user_id, min_file_size_mb=None)
            else:  # max_size
                self.db.update_user_settings(user_id, max_file_size_mb=None)
        else:
            size_mb = int(value)
            current_settings = self.db.get_user_settings(user_id)
            
            if size_type == "min_size":
                # Check if new min_size <= existing max_size
                if current_settings['max_file_size_mb'] and size_mb > current_settings['max_file_size_mb']:
                    await query.edit_message_text(
                        f"❌ Invalid constraint: Minimum file size {size_mb}MB cannot be larger than maximum file size {current_settings['max_file_size_mb']}MB.\n\n"
                        f"Please adjust your maximum size first or choose a smaller minimum size."
                    )
                    await asyncio.sleep(2)
                    await self.show_size_selection(query, size_type)
                    return
                self.db.update_user_settings(user_id, min_file_size_mb=size_mb)
            else:  # max_size
                # Check if existing min_size <= new max_size
                if current_settings['min_file_size_mb'] and current_settings['min_file_size_mb'] > size_mb:
                    await query.edit_message_text(
                        f"❌ Invalid constraint: Maximum file size {size_mb}MB cannot be smaller than minimum file size {current_settings['min_file_size_mb']}MB.\n\n"
                        f"Please adjust your minimum size first or choose a larger maximum size."
                    )
                    await asyncio.sleep(2)
                    await self.show_size_selection(query, size_type)
                    return
                self.db.update_user_settings(user_id, max_file_size_mb=size_mb)
        
        # Show success message and return to main settings
        size_name = "Minimum" if size_type == "min_size" else "Maximum"
        if value == "clear":
            await query.edit_message_text(f"✅ {size_name} file size constraint cleared!")
        else:
            await query.edit_message_text(f"✅ {size_name} file size set to {value}MB!")
        
        # Auto-return to main settings after a brief moment
        await asyncio.sleep(1)
        await self.show_main_settings(query)
    
    def _validate_quality_range(self, min_quality, max_quality):
        """Validate that min_quality <= max_quality"""
        if min_quality is None or max_quality is None:
            return True
        
        quality_order = ['240p', '360p', '480p', '720p', '1080p']
        
        try:
            min_idx = quality_order.index(min_quality)
            max_idx = quality_order.index(max_quality)
            return min_idx <= max_idx
        except ValueError:
            # Unknown quality, assume valid
            return True
    
    def _has_constraints(self, user_settings):
        """Check if user has any quality or file size constraints configured"""
        return (user_settings['min_quality'] is not None or 
                user_settings['max_quality'] is not None or
                user_settings['min_file_size_mb'] is not None or
                user_settings['max_file_size_mb'] is not None)
    
    def _find_best_matching_format(self, format_data, user_settings):
        """Find the best format that matches user constraints"""
        # Get all available formats (video and audio)
        all_formats = []
        
        # Add video formats
        for fmt in format_data['formats']['video']:
            all_formats.append({
                'format_id': fmt['format_id'],
                'quality': fmt['quality'],
                'format_type': 'video',
                'filesize_mb': fmt['filesize_mb'],
                'ext': fmt['ext'],
                'quality_text': fmt['quality']
            })
        
        # Add audio formats
        for fmt in format_data['formats']['audio']:
            all_formats.append({
                'format_id': fmt['format_id'],
                'quality': 'audio_only',
                'format_type': 'audio',
                'filesize_mb': fmt['filesize_mb'],
                'ext': fmt['ext'],
                'quality_text': 'Audio Only'
            })
        
        # Filter by constraints
        matching_formats = []
        
        for fmt in all_formats:
            # Check quality constraints (only apply to video formats)
            if fmt['format_type'] == 'video':
                if not self._quality_matches_constraints(fmt['quality'], user_settings):
                    continue
            
            # Check file size constraints
            if not self._file_size_matches_constraints(fmt['filesize_mb'], user_settings):
                continue
            
            matching_formats.append(fmt)
        
        if not matching_formats:
            return None
        
        # Select best match (highest quality video, or audio if no video matches)
        video_matches = [f for f in matching_formats if f['format_type'] == 'video']
        audio_matches = [f for f in matching_formats if f['format_type'] == 'audio']
        
        if video_matches:
            # Return highest quality video
            return self._select_highest_quality_video(video_matches)
        elif audio_matches:
            # Return best audio format
            return audio_matches[0]  # Audio formats are already sorted by quality
        
        return None
    
    def _quality_matches_constraints(self, quality, user_settings):
        """Check if a video quality matches user constraints"""
        quality_order = ['240p', '360p', '480p', '720p', '1080p']
        
        try:
            quality_idx = quality_order.index(quality)
        except ValueError:
            # Unknown quality, assume it matches
            return True
        
        # Check minimum quality constraint
        if user_settings['min_quality']:
            try:
                min_idx = quality_order.index(user_settings['min_quality'])
                if quality_idx < min_idx:
                    return False
            except ValueError:
                pass
        
        # Check maximum quality constraint
        if user_settings['max_quality']:
            try:
                max_idx = quality_order.index(user_settings['max_quality'])
                if quality_idx > max_idx:
                    return False
            except ValueError:
                pass
        
        return True
    
    def _file_size_matches_constraints(self, file_size_mb, user_settings):
        """Check if file size matches user constraints"""
        # Check minimum file size constraint
        if user_settings['min_file_size_mb'] is not None:
            if file_size_mb < user_settings['min_file_size_mb']:
                return False
        
        # Check maximum file size constraint
        if user_settings['max_file_size_mb'] is not None:
            if file_size_mb > user_settings['max_file_size_mb']:
                return False
        
        return True
    
    def _select_highest_quality_video(self, video_formats):
        """Select the highest quality video from matching formats"""
        quality_order = ['240p', '360p', '480p', '720p', '1080p']
        
        best_format = None
        best_quality_idx = -1
        
        for fmt in video_formats:
            try:
                quality_idx = quality_order.index(fmt['quality'])
                if quality_idx > best_quality_idx:
                    best_quality_idx = quality_idx
                    best_format = fmt
            except ValueError:
                # Unknown quality, consider it if we have no other choice
                if best_format is None:
                    best_format = fmt
        
        return best_format
    
    async def _download_quick_mode_selection(self, update, url, selected_format, processing_msg):
        """Download the automatically selected format in quick mode"""
        user_id = update.effective_user.id
        
        try:
            # Check cache first with compound key
            quality = selected_format['quality']
            format_type_db = selected_format['format_type']
            cached_result = self.db.get_cached_file_id_compound(url, quality, format_type_db)
            
            if cached_result:
                # Cache hit - serve immediately
                file_id, cached_title, cached_quality, cached_format, cached_file_size, cached_duration = cached_result
                quality_text = selected_format['quality_text']
                await processing_msg.edit_text(f"⚡ Found in cache! Sending {quality_text}: {cached_title}")
                
                try:
                    if format_type_db == 'video':
                        await update.message.reply_video(
                            video=file_id,
                            caption=f"🎥 {cached_title} ({quality_text})\n\n🚀 Quick mode: Auto-selected based on your settings\n⚡ Served from cache (instant delivery!)",
                            duration=cached_duration,
                            supports_streaming=True
                        )
                    else:
                        await update.message.reply_audio(
                            audio=file_id,
                            caption=f"🎵 {cached_title} (Audio Only)\n\n🚀 Quick mode: Auto-selected based on your settings\n⚡ Served from cache (instant delivery!)",
                            duration=cached_duration
                        )
                    
                    self._cleanup_user_cache(user_id, url)
                    logger.info(f"Quick mode cache HIT for URL: {url}, Quality: {quality}, Format: {format_type_db}")
                    return
                    
                except Exception as e:
                    logger.warning(f"Failed to send cached video in quick mode: {e}")
                    await processing_msg.edit_text("⚠️ Cached video failed, downloading fresh copy...")
            
            # Cache miss - download
            quality_text = selected_format['quality_text']
            await processing_msg.edit_text(f"📥 Quick mode: Downloading {quality_text}...")
            
            # Download with specific format
            download_result = await asyncio.get_event_loop().run_in_executor(
                None, self.downloader.download_video, url, selected_format['format_id']
            )
            
            if not download_result:
                await processing_msg.edit_text("❌ Download failed. Please try again.")
                return
            
            file_path, title, duration, file_size = download_result
            
            # Check file size limit
            if file_size > 50 * 1024 * 1024:  # 50MB
                await processing_msg.edit_text(f"❌ File too large ({file_size // 1024 // 1024}MB). Telegram limit is 50MB.")
                Path(file_path).unlink(missing_ok=True)
                return
            
            # Upload to Telegram
            await processing_msg.edit_text(f"📤 Quick mode: Uploading {quality_text}: {title}")
            
            with open(file_path, 'rb') as media_file:
                if format_type_db == 'video':
                    message = await update.message.reply_video(
                        video=media_file,
                        caption=f"🎥 {title} ({quality_text})\n\n🚀 Quick mode: Auto-selected based on your settings\n📥 Downloaded and cached for future requests",
                        duration=duration,
                        supports_streaming=True
                    )
                    file_id = message.video.file_id
                else:
                    message = await update.message.reply_audio(
                        audio=media_file,
                        caption=f"🎵 {title} (Audio Only)\n\n🚀 Quick mode: Auto-selected based on your settings\n📥 Downloaded and cached for future requests",
                        duration=duration
                    )
                    file_id = message.audio.file_id
            
            # Store in enhanced cache with compound key
            self.db.store_cached_file_id_compound(url, quality, format_type_db, file_id, title, duration, file_size)
            
            # Clean up
            Path(file_path).unlink(missing_ok=True)
            self._cleanup_user_cache(user_id, url)
            
            logger.info(f"Quick mode cache MISS - Downloaded and cached: {title} ({quality_text})")
            
        except Exception as e:
            logger.error(f"Error in quick mode download: {e}")
            await processing_msg.edit_text(f"❌ Quick mode download error: {str(e)}")
    
    def _cleanup_user_cache(self, user_id, url):
        """Clean up format cache for user and URL"""
        if user_id in self.format_cache and url in self.format_cache[user_id]:
            del self.format_cache[user_id][url]
            if not self.format_cache[user_id]:  # Remove user entry if empty
                del self.format_cache[user_id]
        
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
        
    async def process_video_url_direct(self, update: Update, url, processing_msg=None):
        """Process video URL - check cache first, then download if needed"""
        # Send initial processing message if not provided
        if processing_msg is None:
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