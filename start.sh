#!/data/data/com.termux/files/usr/bin/bash

BOT_DIR="$HOME/xelios-setup/services/telegram-bot"

# Ensure run script is executable
if [ -f "$BOT_DIR/run" ]; then
    chmod +x "$BOT_DIR/run"
fi

# Start only bot service
runsv "$BOT_DIR" &

echo "[✅] Telegram bot service running!"

