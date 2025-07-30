#!/bin/bash

echo "Starting Telegram Video Downloader Bot..."

# Check if TELEGRAM_BOT_TOKEN is set
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "ERROR: TELEGRAM_BOT_TOKEN environment variable is not set!"
    echo "Please set your bot token first:"
    echo "export TELEGRAM_BOT_TOKEN='your_bot_token_here'"
    exit 1
fi

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Run the bot
echo "Starting bot..."
python bot.py