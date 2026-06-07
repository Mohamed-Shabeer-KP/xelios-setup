echo "[+] Installing Telegram Bot..."

pip install python-telegram-bot

echo "[+] Setting up environment variables..."

if [ ! -f "$HOME/.env" ]; then
    read -p "Enter Telegram Bot Token: " TOKEN

    cat > ~/.env <<EOF
TELEGRAM_BOT_TOKEN=$TOKEN
EOF

    echo "[+] Token saved to ~/.env"
else
    echo "[+] ~/.env already exists, skipping..."
fi