# Telegram Video Downloader Bot

A Telegram bot that downloads videos from YouTube with intelligent caching using Telegram's `file_id` system.

## Features

- 🎥 Download YouTube videos through Telegram
- ⚡ Smart caching system - popular videos served instantly
- 💾 SQLite database for URL-to-file_id mapping
- 🚀 Optimized for Railway PaaS deployment
- 📊 Cache statistics and performance tracking

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up your Telegram bot token:**
   ```bash
   export TELEGRAM_BOT_TOKEN="your_bot_token_here"
   ```

3. **Run the bot:**
   ```bash
   python bot.py
   ```

## How It Works

### Cache-First Architecture
- **Cache Hit**: URL exists in database → Retrieve `file_id` → Telegram serves instantly
- **Cache Miss**: Download video → Upload to user → Store `file_id` → Delete local file

### Technology Stack
- **Bot Framework**: python-telegram-bot
- **Download Engine**: youtube-dl (included in project)
- **Database**: SQLite (file-based, no external dependencies)
- **Deployment**: Optimized for Railway PaaS

## Project Structure

```
├── bot.py              # Main bot application
├── database.py         # SQLite database manager
├── downloader.py       # Video download functionality
├── requirements.txt    # Python dependencies
└── youtube-dl-master/ # Download library
```

## Commands

- `/start` - Welcome message and instructions
- `/help` - Detailed help and supported platforms
- `/stats` - Cache statistics

## Environment Variables

- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token (required)

## Deployment

The bot is optimized for Railway PaaS deployment. Simply connect your repository and set the `TELEGRAM_BOT_TOKEN` environment variable.

## Limitations

- YouTube videos only (MVP scope)
- 50MB file size limit (Telegram bot restriction)
- 720p maximum quality for faster processing
- Sequential processing (no job queue in MVP)

## Future Enhancements

- Multi-platform support (TikTok, Instagram, etc.)
- Job queue system for concurrent downloads
- Format/quality selection
- Playlist support
- Analytics dashboard