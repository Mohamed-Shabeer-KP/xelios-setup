echo "[+] Installing Telegram Bot..."

pip install python-telegram-bot

echo "[+] Setting up environment variables..."

ENV_FILE="$HOME/xelios-setup/.env"

if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
    export TELEGRAM_BOT_TOKEN
fi

echo "TOKEN: $TELEGRAM_BOT_TOKEN"