echo "[+] Installing aria2..."
pkg install -y aria2

mkdir -p "$HOME/.aria2"
touch -p "$HOME/.aria2/aria2.session"

cat > "$HOME/.aria2/aria2.conf" <<EOF
dir=$HOME/storage/shared/Download
enable-rpc=true
rpc-listen-all=true
rpc-allow-origin-all=true
input-file=$HOME/.aria2/aria2.session
save-session=$HOME/.aria2/aria2.session
save-session-interval=60
force-save=true
continue=true
EOF
