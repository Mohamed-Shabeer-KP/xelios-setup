echo "[+] Installing Telegram Bot..."

pip install python-telegram-bot

echo "[+] Setting up environment variables..."

ENV_FILE="$HOME/xelios-setup/.env"

if [ ! -f "$ENV_FILE" ]; then
    read -p "Enter Telegram Bot Token: " TOKEN

    cat > "$ENV_FILE" <<EOF
TELEGRAM_BOT_TOKEN=$TOKEN
EOF

    echo "[+] Token saved to $ENV_FILE"
else
    echo "[+] $ENV_FILE already exists, skipping..."
fi

# ✅ ALWAYS load from .env (correct way)
set -a
source "$ENV_FILE"
set +a

echo "[+] Loaded TELEGRAM_BOT_TOKEN (length: ${#TELEGRAM_BOT_TOKEN})]"