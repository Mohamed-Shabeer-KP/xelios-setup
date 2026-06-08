echo "[+] Installing Telegram Bot..."

pip install telethon

ENV_FILE="$HOME/xelios-setup/services/tg-downloader/.env"

mkdir -p "$(dirname "$ENV_FILE")"

# Create .env if missing
if [ ! -f "$ENV_FILE" ]; then
    read -s -p "Enter Telegram API HASH: " API_HASH
    echo ""

    echo "TELEGRAM_API_HASH=$API_HASH" > "$ENV_FILE"

    echo "[+] API HASH saved to $ENV_FILE"
fi

# ✅ Load it (simple way)
source "$ENV_FILE"
export TELEGRAM_API_HASH

# ✅ Debug
if [ -z "$TELEGRAM_API_HASH" ]; then
    echo "[❌ ERROR] API HASH empty"
else
    echo "[✅ API HASH loaded (${#TELEGRAM_API_HASH} chars)"
fi