#!/data/data/com.termux/files/usr/bin/bash

echo "[+] Installing Telegram Bot..."

pip install python-telegram-bot

echo "[+] Setting up environment variables..."

ENV_FILE="$HOME/xelios-setup/.env"

# Ensure directory exists
mkdir -p "$(dirname "$ENV_FILE")"

# Create .env if not exists
if [ ! -f "$ENV_FILE" ]; then
    read -s -p "Enter Telegram Bot Token: " TOKEN
    echo ""

    cat > "$ENV_FILE" <<EOF
TELEGRAM_BOT_TOKEN=$TOKEN
EOF

    echo "[+] Token saved to $ENV_FILE"
else
    echo "[+] $ENV_FILE already exists, skipping..."
fi

# ✅ Load env into CURRENT script
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
    export TELEGRAM_BOT_TOKEN
fi

# ✅ Validate loading
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "[❌ ERROR] TELEGRAM_BOT_TOKEN is EMPTY"
    exit 1
else
    echo "[✅ Token loaded (length: ${#TELEGRAM_BOT_TOKEN})"
fi

echo "[+] Setup complete!"