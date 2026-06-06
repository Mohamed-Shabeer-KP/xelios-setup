echo "[+] Installing VNC..."
pkg install -y tigervnc

mkdir -p ~/.vnc

vncserver :1
vncserver -kill :1

cat > ~/.vnc/xstartup <<EOF
#!/data/data/com.termux/files/usr/bin/bash
unset SESSION_MANAGER
unset DBUS_SESSION_BUS_ADDRESS
exec openbox-session
EOF

chmod +x ~/.vnc/xstartup