echo "[+] Installing Telegram Bot..."

pip install python-telegram-bot

echo "[+] Setting up environment variables..."

ENV_FILE="$HOME/xelios-setup/.env"

# Ensure directory exists
mkdir -p "$(dirname "$ENV_FILE")"

# Create .env if missing
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

# ✅ Load environment variables safely
if [ -f "$ENV_FILE" ]; then
    # shellcheck disable=SC1090
    source "$ENV_FILE"

    # Explicit export (clear & reliable)
    export TELEGRAM_BOT_TOKEN
fi

# ✅ Validate token loaded
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "[❌ ERROR] TELEGRAM_BOT_TOKEN is empty!"
else
    echo "[✅ Loaded TELEGRAM_BOT_TOKEN (length: ${#TELEGRAM_BOT_TOKEN})"
fi