echo "[+] Installing Telegram Bot..."

pip install python-telegram-bot

ENV_FILE="$HOME/xelios-setup/services/tg-bot/.env"

mkdir -p "$(dirname "$ENV_FILE")"

# Create .env if missing
if [ ! -f "$ENV_FILE" ]; then
    read -s -p "Enter Telegram Bot Token: " TOKEN
    echo ""

    echo "TELEGRAM_BOT_TOKEN=$TOKEN" > "$ENV_FILE"

    echo "[+] Token saved to $ENV_FILE"
fi

# ✅ Load it (simple way)
source "$ENV_FILE"
export TELEGRAM_BOT_TOKEN

# ✅ Debug
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "[❌ ERROR] Token empty"
else
    echo "[✅ Token loaded (${#TELEGRAM_BOT_TOKEN} chars)"
fi

# Create session dir for Telethon
mkdir -p ~/xelios-setup/telegram-session

chmod -R 777 ~/xelios-setup/services/telegram-session