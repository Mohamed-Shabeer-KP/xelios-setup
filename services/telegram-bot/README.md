# Telegram Bot Service

A Telegram bot for managing xelios-setup services. Control and monitor all services directly from Telegram.

## Features

- ✅ Start all services
- ⏹️ Stop all services
- 📊 Check status of all services
- ⚙️ Start/stop individual services
- 🔐 Optional user authentication

## Setup

### 1. Create a Telegram Bot

1. Open Telegram and find `@BotFather`
2. Send `/newbot` to create a new bot
3. Follow the prompts and get your bot token
4. Save the token (you'll need it in the next step)

### 2. Install Dependencies

```bash
pip install python-telegram-bot
```

### 3. Configure the Bot

Set the environment variables:

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export ALLOWED_USER_IDS="123456789,987654321"  # Optional: comma-separated user IDs
```

To find your Telegram user ID:
1. Send a message to the bot
2. Visit `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Look for the `"id"` field in the message data

### 4. Add to Startup

The bot will auto-start when the service manager starts. You can manually start it with:

```bash
runsvdir ~/xelios-setup/services
```

Or individually:

```bash
runsv ~/xelios-setup/services/telegram-bot
```

## Commands

- `/start` - Show main menu
- Use inline buttons to:
  - 📊 Check service status
  - ▶️ Start all services
  - ⏹️ Stop all services
  - 🔧 Manage individual services

## Security Notes

- If `ALLOWED_USER_IDS` is not set, anyone who knows your bot token can control your services
- Always set `ALLOWED_USER_IDS` to restrict access to trusted users only
- Use environment variables or a config file to store sensitive data
- Never commit bot tokens to version control

## Troubleshooting

### Bot not responding
- Check that `TELEGRAM_BOT_TOKEN` is set correctly
- Verify internet connectivity
- Check logs: `tail -f ~/xelios-setup/services/telegram-bot/log/main/current`

### Commands not working
- Ensure `ALLOWED_USER_IDS` includes your Telegram user ID (if configured)
- Check that services have proper `run` scripts with execute permissions

### Service control not working
- Verify runit is running: `pgrep runsvdir`
- Check service `run` scripts are executable
- Review service logs: `tail -f ~/xelios-setup/services/<service>/log/main/current`
