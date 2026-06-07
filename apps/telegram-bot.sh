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