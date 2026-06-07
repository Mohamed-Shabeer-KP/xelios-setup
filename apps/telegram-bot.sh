#!/data/data/com.termux/files/usr/bin/bash

ENV_FILE="$HOME/xelios-setup/.env"

# Load environment variables
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
    export TELEGRAM_BOT_TOKEN
fi

# Debug (optional)
echo "[*] Token length: ${#TELEGRAM_BOT_TOKEN}"

# Fail if missing
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "[ERROR] TELEGRAM_BOT_TOKEN not set!"
    exit 1
fi

# Start bot
exec python "$HOME/bot.py"


echo "[+] Installing Telegram Bot..."

pip install python-telegram-bot

ENV_FILE="$HOME/xelios-setup/.env"

mkdir -p "$(dirname "$ENV_FILE")"

if [ ! -f "$ENV_FILE" ]; then
    read -s -p "Enter Telegram Bot Token: " TOKEN
    echo ""

    printf "TELEGRAM_BOT_TOKEN=%s\n" "$TOKEN" > "$ENV_FILE"

    echo "[+] Token saved"
fi

# ✅ Load env safely (bulletproof)
while IFS='=' read -r key value; do
    if [ "$key" = "TELEGRAM_BOT_TOKEN" ]; then
        export TELEGRAM_BOT_TOKEN="$value"
    fi
done < "$ENV_FILE"

# ✅ Debug
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "[❌ ERROR] Token still empty"
else
    echo "[✅ Token loaded (length: ${#TELEGRAM_BOT_TOKEN})"
fi