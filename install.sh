#!/data/data/com.termux/files/usr/bin/bash

echo "[+] Updating system..."
pkg update -y && pkg upgrade -y -o Dpkg::Options::="--force-confold"

echo "[+] Installing required packages..."
pkg install runit termux-api -y

echo "[+] Setup storage..."
termux-setup-storage

echo "[+] Setup auto start..."

mkdir -p ~/.termux/boot

cat > ~/.termux/boot/start.sh <<EOF
#!/data/data/com.termux/files/usr/bin/bash

sleep 5
runsvdir \$HOME/xelios-setup/services &
EOF

chmod +x ~/.termux/boot/start.sh

echo "[+] Running app setups..."

for app in apps/*.sh; do
    echo "[+] Running $app"
    bash "$app"
done

echo "[+] Fixing permissions..."
chmod +x ~/xelios-setup/services/*/run

echo "[✅ DONE]"