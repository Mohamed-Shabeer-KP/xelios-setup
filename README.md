# xelios-setup

A comprehensive service management system for running multiple services in Termux with Telegram bot integration.

## 📋 Table of Contents

- [Features](#features)
- [Services](#services)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Service Management](#service-management)
- [Telegram Bot](#telegram-bot)

## ✨ Features

- **runit-based service management** - Reliable process supervision
- **Telegram Bot control** - Manage services from your phone
- **Multiple services** - Aria2, Firefox, Desktop GUI, and more
- **Auto-start** - Services start automatically on boot
- **Easy configuration** - Simple bash scripts

## 📦 Services

### Included Services

1. **aria2** - Download manager with RPC interface
2. **firefox** - Web browser with X11 support
3. **gui** - Desktop environment (OpenBox + VNC)
4. **telegram-bot** - Service management bot (NEW)

### Available Ports

- **Aria2 RPC**: localhost:6800
- **VNC Server**: localhost:5901
- **Telegram**: Remote control via bot

## 🚀 Installation

### Prerequisites

- Termux environment (Android)
- Bash shell
- Internet connection

### Setup Steps

```bash
# 1. Clone or extract the repository
cd ~/xelios-setup

# 2. Run the installer
bash install.sh

# 3. Grant required permissions when prompted
```

The installer will:
- Install required packages (runit, X11, etc.)
- Setup storage permissions
- Configure auto-start
- Run individual app setup scripts

## ▶️ Quick Start

### Start All Services

```bash
bash start.sh
```

### Stop All Services

```bash
bash stop.sh
```

### Manage via Telegram Bot

See [Telegram Bot Setup](services/telegram-bot/README.md)

## 🔧 Service Management

### Manual Service Control

```bash
# Start a single service
runsv ~/xelios-setup/services/aria2

# Stop a single service
pkill -f "runsv aria2"

# View all services
ls ~/xelios-setup/services/

# Check service logs
tail -f ~/xelios-setup/services/aria2/log/main/current
```

### Service Directory Structure

```
services/
├── aria2/
│   ├── run              # Service startup script
│   └── log/             # Auto-generated logs
├── firefox/
│   ├── run
│   └── log/
├── gui/
│   ├── run
│   └── log/
└── telegram-bot/
    ├── run              # Telegram bot service
    ├── bot.py           # Bot implementation
    ├── README.md        # Bot documentation
    └── log/             # Auto-generated logs
```

## 🤖 Telegram Bot

The Telegram bot allows you to control all services remotely.

### Features

✅ Start/stop all services  
📊 View service status  
⚙️ Control individual services  
🔐 Optional user authentication  

### Setup

1. Create a bot with [@BotFather](https://t.me/botfather)
2. Install Python dependencies: `pip install python-telegram-bot`
3. Configure environment variables:
   ```bash
   export TELEGRAM_BOT_TOKEN="your_bot_token"
   export ALLOWED_USER_IDS="your_user_id"
   ```
4. Start the bot service: `bash start.sh`

For detailed instructions, see [Telegram Bot README](services/telegram-bot/README.md)

## 📝 Scripts Reference

### install.sh
Initial setup script that installs dependencies and configures auto-start.

### start.sh
Starts the runit service supervisor and all configured services.

### stop.sh
Stops all running services.

### apps/*.sh
Individual app setup scripts (Aria2, Firefox, GUI, etc.)

## 🐛 Troubleshooting

### Services not starting

```bash
# Check if runit is running
pgrep runsvdir

# View service logs
tail -f ~/xelios-setup/services/SERVICE_NAME/log/main/current

# Restart services
bash stop.sh
bash start.sh
```

### Telegram bot not responding

- Verify `TELEGRAM_BOT_TOKEN` is set
- Check bot logs: `tail -f ~/xelios-setup/services/telegram-bot/log/main/current`
- Ensure internet connection
- Verify your user ID is in `ALLOWED_USER_IDS`

### GUI/VNC connection issues

- Check VNC port: `netstat -tlnp | grep vnc`
- Verify X11 is running: `pgrep Xvnc`
- Connect to `localhost:5901` with VNC viewer

## 📖 Additional Resources

- [Runit documentation](http://smarden.org/runit/)
- [Aria2 documentation](https://aria2.github.io/)
- [python-telegram-bot docs](https://python-telegram-bot.readthedocs.io/)

## 📄 License

See individual service licenses