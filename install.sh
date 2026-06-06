#!/data/data/com.termux/files/usr/bin/bash

set -e

export DEBIAN_FRONTEND=noninteractive

# Keep existing config files during upgrades
APT_OPTS='-y -o Dpkg::Options::=--force-confold'

echo "[+] Updating system..."
apt update
apt $APT_OPTS upgrade

echo "[+] Installing required packages..."
pkg install runit termux-api -y
pkg install root-repo -y
pkg install x11-repo -y
apt $APT_OPTS install runit termux-api

echo "[+] Setup storage..."

if [ ! -d "$HOME/storage" ]; then
    echo "[*] Requesting storage permission..."
    termux-setup-storage

    echo "[*] Please grant the Android storage permission if prompted."
    sleep 5
fi

echo "[+] Setup auto start..."

mkdir -p "$HOME/.termux/boot"

cat > "$HOME/.termux/boot/start.sh" <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash

sleep 5
runsvdir "$HOME/xelios-setup/services" &
EOF

chmod +x "$HOME/.termux/boot/start.sh"

echo "[+] Running app setups..."

for app in apps/*.sh; do
    [ -f "$app" ] || continue

    echo "[+] Running $app"
    bash "$app"
done

echo "[+] Fixing permissions..."

if [ -d "$HOME/xelios-setup/services" ]; then
    find "$HOME/xelios-setup/services" -type f -name run -exec chmod +x {} \;
fi

echo "[✅ DONE]"
