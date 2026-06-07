ENV_FILE="$HOME/xelios-setup/.env"

# create if not exists
if [ ! -f "$ENV_FILE" ]; then
    read -p "Enter Telegram Bot Token: " TOKEN

    cat > "$ENV_FILE" <<EOF
TELEGRAM_BOT_TOKEN=$TOKEN
EOF
fi

# ✅ LOAD + EXPORT (this is what you need)
export $(grep -v '^#' "$ENV_FILE" | xargs)

# test
echo "Token loaded: $TELEGRAM_BOT_TOKEN"