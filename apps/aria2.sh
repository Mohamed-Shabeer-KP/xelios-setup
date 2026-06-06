echo "[+] Installing aria2..."
pkg install -y aria2

mkdir -p ~/.aria2

cat > ~/.aria2/aria2.conf <<EOF
dir=~/storage/shared/download
enable-rpc=true
rpc-listen-all=true
rpc-allow-origin-all=true
EOF
