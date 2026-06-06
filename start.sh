#!/data/data/com.termux/files/usr/bin/bash

echo "[*] Starting runit..."

echo "[+] Fixing permissions..."

if [ -d "$HOME/xelios-setup/services" ]; then
    find "$HOME/xelios-setup/services" -type f -name run -exec chmod +x {} \;
fi

runsvdir ~/xelios-setup/services 

echo "[✅] All services running!"
