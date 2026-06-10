echo "[+] Installing aria2..."
pkg install -y aria2

mkdir -p "$HOME/.aria2"

cat > "$HOME/.aria2/aria2.conf" <<EOF
dir=$HOME/storage/shared/Download
enable-rpc=true
rpc-listen-all=true
rpc-allow-origin-all=true
EOF
