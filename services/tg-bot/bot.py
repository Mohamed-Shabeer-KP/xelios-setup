#!/usr/bin/env python3

import os
import subprocess
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes
)

# ---------------- CONFIG ----------------
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
SERVICES_DIR = os.path.expanduser("~/xelios-setup/services")
LOGIN_FILE = os.path.expanduser("~/xelios-setup/services/tg-downloader/tg_login_code")

logging.basicConfig(level=logging.INFO)

# ---------------- HELPERS ----------------
def service_path(name):
    return os.path.join(SERVICES_DIR, name)

def list_services():
    if not os.path.isdir(SERVICES_DIR):
        return []
    return [
        s for s in sorted(os.listdir(SERVICES_DIR))
        if os.path.isdir(service_path(s))
    ]

def is_running(name):
    try:
        result = subprocess.run(
            ["sv", "status", service_path(name)],
            capture_output=True,
            text=True
        )
        return "run:" in result.stdout.lower()
    except:
        return False

def start_service(name):
    path = service_path(name)
    subprocess.run(["rm", "-f", f"{path}/down"])
    subprocess.run(["sv", "up", path])
    return f"🟢 {name} started"

def stop_service(name):
    path = service_path(name)
    subprocess.run(["sv", "down", path])
    subprocess.run(["touch", f"{path}/down"])
    return f"🔴 {name} stopped"

def service_status_text():
    text = "📊 *Service Status*\n\n"
    for s in list_services():
        icon = "🟢" if is_running(s) else "🔴"
        text += f"{icon} {s}\n"
    return text

# ---------------- UI ----------------
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Status", callback_data="status")],
        [InlineKeyboardButton("🔧 Services", callback_data="services")]
    ])

async def render_main_menu(query):
    await query.edit_message_text(
        "🤖 *Xelios Service Manager*",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

# ---------------- COMMANDS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Xelios Service Manager*",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

# ✅ OTP COMMAND (NEW)
async def otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /otp 12345")
        return

    code = context.args[0]

    try:
        print("💾 Writing OTP to:", LOGIN_FILE)

        os.makedirs(os.path.dirname(LOGIN_FILE), exist_ok=True)

        if os.path.isdir(LOGIN_FILE):
            import shutil
            shutil.rmtree(LOGIN_FILE)

        with open(LOGIN_FILE, "w") as f:
            f.write(code)

        await update.message.reply_text("✅ OTP sent to downloader")

    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {e}")

# ---------------- ROUTER ----------------
async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "status":
        await query.edit_message_text(
            service_status_text(),
            reply_markup=main_menu(),
            parse_mode="Markdown"
        )

    elif data == "services":
        keyboard = [
            [InlineKeyboardButton(s, callback_data=f"svc:{s}")]
            for s in list_services()
        ]
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back")])

        await query.edit_message_text(
            "🔧 Services:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data == "back":
        await render_main_menu(query)

    elif data.startswith("svc:"):
        name = data.split(":")[1]
        running = is_running(name)

        keyboard = []
        if running:
            keyboard.append([InlineKeyboardButton("⏹ Stop", callback_data=f"stop:{name}")])
        else:
            keyboard.append([InlineKeyboardButton("▶ Start", callback_data=f"start:{name}")])

        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="services")])

        await query.edit_message_text(
            f"*{name}*\nStatus: {'🟢 Running' if running else '🔴 Stopped'}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif data.startswith("start:"):
        name = data.split(":")[1]
        msg = start_service(name)
        await query.edit_message_text(msg, reply_markup=main_menu(), parse_mode="Markdown")

    elif data.startswith("stop:"):
        msg = stop_service(data.split(":")[1])
        await query.edit_message_text(msg, reply_markup=main_menu())

# ---------------- MAIN ----------------
def main():
    if not BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not set")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("otp", otp))  # ✅ added
    app.add_handler(CallbackQueryHandler(router))

    print("🤖 Service manager bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
