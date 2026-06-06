#!/data/data/com.termux/files/usr/bin/bash

set -e

echo "[*] Updating packages..."
pkg update -y
pkg upgrade -y

echo "[*] Installing dependencies..."
pkg install -y git python ansible

echo "[*] Running Ansible..."
ansible-playbook -i inventory playbook.yml

echo "[✅] Setup complete!"