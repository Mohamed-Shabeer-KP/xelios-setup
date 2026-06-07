#!/data/data/com.termux/files/usr/bin/bash

echo "[*] Starting runit system..."

SERVICES_DIR="$HOME/xelios-setup/services"
BOT_DIR="$SERVICES_DIR/telegram-bot"

# Fix permissions
find "$SERVICES_DIR" -type f -name run -exec chmod +x {} \;

# ✅ Start service supervisor (VERY IMPORTANT)
runsvdir "$SERVICES_DIR" &

# Give it time to initialize
sleep 2

# ✅ Start ONLY telegram bot
sv up "$BOT_DIR"

echo "[✅] Bot is running. Use Telegram to control other services."