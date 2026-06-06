#!/data/data/com.termux/files/usr/bin/bash

set -e

export ANDROID_API_LEVEL=24

echo "[*] Updating packages..."
pkg update -y
pkg upgrade -y

echo "[*] Installing dependencies for ansible..."
pkg install -y git python python-pip

echo "[*] Installing dependencies..."
pip install ansible

echo "[*] Running Ansible..."
ansible-playbook -i inventory playbook.yml

echo "[✅] Setup complete!"