#!/data/data/com.termux/files/usr/bin/bash

echo "[*] Starting runit..."
chmod +x ~/services/*/run

runsvdir ~/services &

echo "[✅] All services running!"
