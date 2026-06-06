#!/data/data/com.termux/files/usr/bin/bash

echo "[+] Updating system..."
pkg update -y && pkg upgrade -y

echo "[+] Setup storage..." 
termux-setup-storage -y

echo "[+] Setup austo start..." 
pkg install termux-api -y

mkdir -p ~/.termux/boot

cat > ~/.termux/boot/start.sh <<EOF
#!/data/data/com.termux/files/usr/bin/bash

# Start runit services
chmod +x \$HOME/services/*/run
runsvdir \$HOME/services &
EOF

chmod +x ~/.termux/boot/start.sh

echo "[+] install runit..."
pkg install runit -y

echo "[+] Running app setups..."

for app in apps/*.sh; do
    echo "[+] Running $app"
    bash "$app"
done

echo "[✅ DONE]"