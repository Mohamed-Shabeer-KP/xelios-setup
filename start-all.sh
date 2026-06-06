#!/data/data/com.termux/files/usr/bin/bash

echo "[*] Starting runit..."

runsvdir ~/services &

echo "[✅] All services running!"
