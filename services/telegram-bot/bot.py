#!/usr/bin/env python3
"""
Telegram Bot for xelios-setup service management
Provides commands to start, stop, and check status of all services
"""

import os
import subprocess
import logging
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ChatAction

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
SERVICES_DIR = os.path.expanduser("~/xelios-setup/services")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ALLOWED_USERS = [int(uid) for uid in os.getenv("ALLOWED_USER_IDS", "").split(",") if uid]

# Service management functions
def get_services():
    """Get list of all services"""
    services = []
    if os.path.isdir(SERVICES_DIR):
        for item in sorted(os.listdir(SERVICES_DIR)):
            service_path = os.path.join(SERVICES_DIR, item)
            if os.path.isdir(service_path) and os.path.isfile(os.path.join(service_path, "run")):
                services.append(item)
    return services

def is_service_running(service_name):
    """Check if a service is running"""
    try:
        result = subprocess.run(
            ["pgrep", "-f", f"runsv {service_name}"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error checking service {service_name}: {e}")
        return False

def get_all_services_status():
    """Get status of all services"""
    services = get_services()
    status = {}
    for service in services:
        status[service] = is_service_running(service)
    return status

def start_service(service_name):
    """Start a service using runit"""
    try:
        service_path = os.path.join(SERVICES_DIR, service_name)
        if not os.path.isdir(service_path):
            return False, f"Service {service_name} not found"
        
        # Create the service directory if it has a run script
        run_script = os.path.join(service_path, "run")
        if not os.path.isfile(run_script):
            return False, f"No run script for {service_name}"
        
        # Start using runit
        subprocess.run(
            ["runsv", service_path],
            capture_output=True,
            timeout=5,
            start_new_session=True
        )
        return True, f"Service {service_name} started"
    except subprocess.TimeoutExpired:
        return True, f"Service {service_name} started (timeout)"
    except Exception as e:
        logger.error(f"Error starting service {service_name}: {e}")
        return False, f"Error starting {service_name}: {str(e)}"

def stop_service(service_name):
    """Stop a service"""
    try:
        result = subprocess.run(
            ["pkill", "-f", f"runsv {service_name}"],
            capture_output=True,
            timeout=5
        )
        return True, f"Service {service_name} stopped"
    except Exception as e:
        logger.error(f"Error stopping service {service_name}: {e}")
        return False, f"Error stopping {service_name}: {str(e)}"

def start_all_services():
    """Start all services"""
    try:
        subprocess.run(
            ["runsvdir", SERVICES_DIR],
            capture_output=True,
            timeout=5,
            start_new_session=True
        )
        return True, "All services started"
    except subprocess.TimeoutExpired:
        return True, "All services started (timeout)"
    except Exception as e:
        logger.error(f"Error starting all services: {e}")
        return False, f"Error starting services: {str(e)}"

def stop_all_services():
    """Stop all services"""
    try:
        subprocess.run(["pkill", "runsvdir"], capture_output=True, timeout=5)
        subprocess.run(["pkill", "runsv"], capture_output=True, timeout=5)
        return True, "All services stopped"
    except Exception as e:
        logger.error(f"Error stopping services: {e}")
        return False, f"Error stopping services: {str(e)}"

# Telegram Bot Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start command - show main menu"""
    if ALLOWED_USERS and update.effective_user.id not in ALLOWED_USERS:
        await update.message.reply_text("❌ Unauthorized access denied.")
        return
    
    keyboard = [
        [InlineKeyboardButton("📊 Status", callback_data="status")],
        [InlineKeyboardButton("▶️ Start All", callback_data="start_all"), 
         InlineKeyboardButton("⏹️ Stop All", callback_data="stop_all")],
        [InlineKeyboardButton("🔧 Service Menu", callback_data="service_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🤖 *Xelios Service Manager*\n\n"
        "Welcome! Choose an option:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Status command - show all services status"""
    if ALLOWED_USERS and update.effective_user.id not in ALLOWED_USERS:
        await update.callback_query.answer("❌ Unauthorized")
        return
    
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("⏳ Fetching service status...")
    
    status_info = get_all_services_status()
    
    if not status_info:
        await query.edit_message_text("ℹ️ No services found")
        return
    
    message = "📊 *Service Status*\n\n"
    for service, running in sorted(status_info.items()):
        status_icon = "🟢" if running else "🔴"
        message += f"{status_icon} {service}\n"
    
    keyboard = [[InlineKeyboardButton("🔄 Refresh", callback_data="status"),
                 InlineKeyboardButton("🔙 Back", callback_data="start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")

async def start_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start all services"""
    if ALLOWED_USERS and update.effective_user.id not in ALLOWED_USERS:
        await update.callback_query.answer("❌ Unauthorized")
        return
    
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("⏳ Starting all services...")
    
    success, message = start_all_services()
    emoji = "✅" if success else "❌"
    
    keyboard = [[InlineKeyboardButton("📊 Status", callback_data="status"),
                 InlineKeyboardButton("🔙 Back", callback_data="start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(f"{emoji} {message}", reply_markup=reply_markup, parse_mode="Markdown")

async def stop_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stop all services"""
    if ALLOWED_USERS and update.effective_user.id not in ALLOWED_USERS:
        await update.callback_query.answer("❌ Unauthorized")
        return
    
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("⏳ Stopping all services...")
    
    success, message = stop_all_services()
    emoji = "✅" if success else "❌"
    
    keyboard = [[InlineKeyboardButton("📊 Status", callback_data="status"),
                 InlineKeyboardButton("🔙 Back", callback_data="start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(f"{emoji} {message}", reply_markup=reply_markup, parse_mode="Markdown")

async def service_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show individual service management menu"""
    if ALLOWED_USERS and update.effective_user.id not in ALLOWED_USERS:
        await update.callback_query.answer("❌ Unauthorized")
        return
    
    query = update.callback_query
    await query.answer()
    
    services = get_services()
    if not services:
        await query.edit_message_text("ℹ️ No services found")
        return
    
    keyboard = []
    for service in services:
        keyboard.append([InlineKeyboardButton(f"⚙️ {service}", callback_data=f"service__{service}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="start")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text("🔧 *Select a service:*", reply_markup=reply_markup, parse_mode="Markdown")

async def service_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show actions for a specific service"""
    query = update.callback_query
    service_name = query.data.split("__")[1]
    
    if ALLOWED_USERS and update.effective_user.id not in ALLOWED_USERS:
        await query.answer("❌ Unauthorized")
        return
    
    running = is_service_running(service_name)
    status_icon = "🟢" if running else "🔴"
    
    keyboard = []
    if not running:
        keyboard.append([InlineKeyboardButton("▶️ Start", callback_data=f"service_start__{service_name}")])
    else:
        keyboard.append([InlineKeyboardButton("⏹️ Stop", callback_data=f"service_stop__{service_name}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="service_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.answer()
    await query.edit_message_text(
        f"{status_icon} *{service_name}*\n\n"
        "Choose action:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def service_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start individual service"""
    query = update.callback_query
    service_name = query.data.split("__")[1]
    
    if ALLOWED_USERS and update.effective_user.id not in ALLOWED_USERS:
        await query.answer("❌ Unauthorized")
        return
    
    await query.answer()
    await query.edit_message_text(f"⏳ Starting {service_name}...")
    
    success, message = start_service(service_name)
    emoji = "✅" if success else "❌"
    
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data=f"service__{service_name}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(f"{emoji} {message}", reply_markup=reply_markup, parse_mode="Markdown")

async def service_stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stop individual service"""
    query = update.callback_query
    service_name = query.data.split("__")[1]
    
    if ALLOWED_USERS and update.effective_user.id not in ALLOWED_USERS:
        await query.answer("❌ Unauthorized")
        return
    
    await query.answer()
    await query.edit_message_text(f"⏳ Stopping {service_name}...")
    
    success, message = stop_service(service_name)
    emoji = "✅" if success else "❌"
    
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data=f"service__{service_name}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(f"{emoji} {message}", reply_markup=reply_markup, parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route button callbacks"""
    query = update.callback_query
    data = query.data
    
    if data == "status":
        await status(update, context)
    elif data == "start_all":
        await start_all(update, context)
    elif data == "stop_all":
        await stop_all(update, context)
    elif data == "service_menu":
        await service_menu(update, context)
    elif data == "start":
        await start(update, context)
    elif data.startswith("service__"):
        await service_action(update, context)
    elif data.startswith("service_start__"):
        await service_start(update, context)
    elif data.startswith("service_stop__"):
        await service_stop(update, context)

def main() -> None:
    """Start the bot"""
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set!")
        print("❌ Error: TELEGRAM_BOT_TOKEN not configured")
        print("Please set the TELEGRAM_BOT_TOKEN environment variable")
        return
    
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Start the Bot
    logger.info("🤖 Telegram Bot started and polling...")
    print("✅ Telegram Bot is running. Send /start to begin.")
    
    application.run_polling()

if __name__ == '__main__':
    main()
