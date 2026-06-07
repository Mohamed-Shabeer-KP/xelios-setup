#!/data/data/com.termux/files/usr/bin/bash

echo "[*] Starting runit system..."

SERVICES_DIR="$HOME/xelios-setup/services"
BOT_DIR="$SERVICES_DIR/telegram-bot"

# Fix permissions
find "$SERVICES_DIR" -type f -name run -exec chmod +x {} \;

# Ensure non-bot services are DOWN
for svc in "$SERVICES_DIR"/*; do
    [ "$(basename "$svc")" != "telegram-bot" ] && touch "$svc/down"
done

# Ensure bot is UP
rm -f "$BOT_DIR/down"

# Start supervisor
runsvdir "$SERVICES_DIR" 

sleep 2

# Explicitly start bot
sv up "$BOT_DIR"

echo "[✅] Bot running, other services disabled"