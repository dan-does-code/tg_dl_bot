@echo off
echo Starting Telegram Video Downloader Bot...

REM Check if TELEGRAM_BOT_TOKEN is set
if "%TELEGRAM_BOT_TOKEN%"=="" (
    echo ERROR: TELEGRAM_BOT_TOKEN environment variable is not set!
    echo Please set your bot token first:
    echo set TELEGRAM_BOT_TOKEN=your_bot_token_here
    pause
    exit /b 1
)

REM Install dependencies if requirements.txt exists
if exist requirements.txt (
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Run the bot
echo Starting bot...
python bot.py

pause