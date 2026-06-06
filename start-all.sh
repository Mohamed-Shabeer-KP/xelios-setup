#!/data/data/com.termux/files/usr/bin/bash

echo "[*] Starting VNC..."
vncserver :1 -geometry 1280x720 -shared

echo "[*] Starting openbox..."
openbox &

echo "[*] Starting aria2..."
./start-aria2.sh &

echo "[*] Starting firefox..."
firefox &

echo "[✅] All services running!"
