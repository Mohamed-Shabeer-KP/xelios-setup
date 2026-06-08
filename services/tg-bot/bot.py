#!/usr/bin/env python3

import os
import subprocess
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)

from telethon import TelegramClient

# ---------------- CONFIG ----------------
SERVICES_DIR = os.path.expanduser("~/xelios-setup/services")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
API_HASH = os.getenv("TELEGRAM_API_HASH", "")
API_ID = 30299030

logging.basicConfig(level=logging.INFO)

client = TelegramClient("session", API_ID, API_HASH)

LOGIN_STATE = {
    "step": None,
    "phone": None
}

# ---------------- HELPERS ----------------
def service_path(name):
    return os.path.join(SERVICES_DIR, name)

def list_services():
    if not os.path.isdir(SERVICES_DIR):
        return []

    return [
        s for s in sorted(os.listdir(SERVICES_DIR))
        if os.path.isdir(service_path(s))
        and os.path.isfile(os.path.join(service_path(s), "run"))
    ]

def is_running(name):
    try:
        result = subprocess.run(
            ["sv", "status", service_path(name)],
            capture_output=True,
            text=True
        )
        return result.stdout.startswith("run:")
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

# ---------------- UI ----------------
async def main_menu():
    await client.connect()
    logged_in = await client.is_user_authorized()

    buttons = [
        [InlineKeyboardButton("📊 Status", callback_data="status")],
        [InlineKeyboardButton("🔧 Services", callback_data="services")]
    ]

    if not logged_in:
        buttons.append([InlineKeyboardButton("🔐 Login", callback_data="login")])

    return InlineKeyboardMarkup(buttons)

async def render_main_menu(query):
    await query.edit_message_text(
        "🤖 *Xelios Service Manager*",
        reply_markup=await main_menu(),
        parse_mode="Markdown"
    )

# ---------------- COMMAND ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Xelios Service Manager*",
        reply_markup=await main_menu(),
        parse_mode="Markdown"
    )

# ---------------- LOGIN FLOW ----------------
async def start_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await client.connect()

    if await client.is_user_authorized():
        if update.callback_query:
            await update.callback_query.answer("Already logged in", show_alert=True)
        else:
            await update.message.reply_text("✅ Already logged in")
        return

    LOGIN_STATE["step"] = "phone"

    if update.callback_query:
        await update.callback_query.edit_message_text("📱 Send phone number (+countrycode)")
    else:
        await update.message.reply_text("📱 Send phone number (+countrycode)")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # STEP 1: PHONE
    if LOGIN_STATE["step"] == "phone":
        LOGIN_STATE["phone"] = text

        await client.connect()
        await client.send_code_request(text)

        LOGIN_STATE["step"] = "code"
        await update.message.reply_text("📩 OTP sent. Send code")

    # STEP 2: OTP
    elif LOGIN_STATE["step"] == "code":
        try:
            await client.sign_in(LOGIN_STATE["phone"], text)

            LOGIN_STATE["step"] = None
            await update.message.reply_text("✅ Login successful!")

        except Exception as e:
            await update.message.reply_text(f"❌ {e}")

# ---------------- ROUTER ----------------
async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    # STATUS
    if data == "status":
        text = "📊 *Service Status*\n\n"
        for s in list_services():
            icon = "🟢" if is_running(s) else "🔴"
            text += f"{icon} {s}\n"

        await query.edit_message_text(
            text,
            reply_markup=await main_menu(),
            parse_mode="Markdown"
        )

    # SERVICES
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

    # BACK
    elif data == "back":
        await render_main_menu(query)

    # LOGIN
    elif data == "login":
        await start_login(update, context)

    # SERVICE DETAILS
    elif data.startswith("svc:"):
        name = data.split(":")[1]
        running = is_running(name)

        keyboard = []
        if running:
            keyboard.append([InlineKeyboardButton("⏹️ Stop", callback_data=f"stop:{name}")])
        else:
            keyboard.append([InlineKeyboardButton("▶️ Start", callback_data=f"start:{name}")])

        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="services")])

        await query.edit_message_text(
            f"*{name}*\nStatus: {'🟢 Running' if running else '🔴 Stopped'}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    # START
    elif data.startswith("start:"):
        name = data.split(":")[1]
        await query.edit_message_text(
            start_service(name),
            reply_markup=await main_menu()
        )

    # STOP
    elif data.startswith("stop:"):
        name = data.split(":")[1]
        await query.edit_message_text(
            stop_service(name),
            reply_markup=await main_menu()
        )

# ---------------- MAIN ----------------
def main():
    if not BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not set")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(router))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("🤖 Bot running...")
    app.run_polling()

# ---------------- ENTRY ----------------
if __name__ == "__main__":
    main()