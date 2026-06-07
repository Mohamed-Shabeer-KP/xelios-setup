echo "[+] Installing Telegram Bot..."

pip install python-telegram-bot

echo "[+] Setting up environment variables..."

if [ ! -f "$HOME/xelios-setup/.env" ]; then
    read -p "Enter Telegram Bot Token: " TOKEN

    cat > "$HOME/xelios-setup/.env" <<EOF
TELEGRAM_BOT_TOKEN=$TOKEN
EOF

    echo "[+] Token saved to ~/xelios-setup/.env"
else
    echo "[+] ~/xelios-setup/.env already exists, skipping..."
fi

export TELEGRAM_BOT_TOKEN=$TOKEN