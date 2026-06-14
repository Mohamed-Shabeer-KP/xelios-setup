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
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
SERVICES_DIR = os.path.expanduser("~/xelios-setup/services")

API_ID = 30299030
API_HASH = os.getenv("TELEGRAM_API_HASH")

SESSION_PATH = os.path.expanduser(
    "~/xelios-setup/services/tg-downloader/session"
)

logging.basicConfig(level=logging.INFO)

login_client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
login_state = {}

async def get_login_status():
    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)

    await client.connect()

    try:
        if await client.is_user_authorized():
            status = "✅ Logged In"
        else:
            status = "❌ Not Logged In"
    except Exception:
        status = "❌ Not Logged In"

    await client.disconnect()
    return status
    
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
    status = await get_login_status()
    whoami = await get_whoami()

    await update.message.reply_text(
        f"🤖 *Xelios Service Manager*\n\n"
        f"🔐 *Login Status:* {status}\n"
        f"👤 *Whoami:* `{whoami}`",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

# ✅ LOGIN COMMAND
async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    login_state[user_id] = {"step": "phone"}

    await update.message.reply_text("🔐 Send your phone number (+1234567890)")

# ✅ LOGIN FLOW
async def login_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in login_state:
        return

    text = update.message.text.strip()
    state = login_state[user_id]

    # STEP 1: PHONE
    if state["step"] == "phone":
        await login_client.connect()

        result = await login_client.send_code_request(text)

        state["phone"] = text
        state["phone_code_hash"] = result.phone_code_hash
        state["step"] = "code"

        await update.message.reply_text("📩 OTP sent. Send code like:\n`1 2 3 4 5`", parse_mode="Markdown")

    # STEP 2: OTP
    elif state["step"] == "code":
        try:
            # ✅ Remove spaces/dashes (OBFUSCATION SUPPORT)
            code = text.replace(" ", "").replace("-", "")

            print("👉 Using OTP:", code)
            print("👉 Using hash:", state["phone_code_hash"])

            await login_client.sign_in(
                phone=state["phone"],
                code=code,
                phone_code_hash=state["phone_code_hash"]
            )

            await update.message.reply_text("✅ Login successful!")

            login_state.pop(user_id)

        except Exception as e:
            if "PASSWORD" in str(e).upper():
                state["step"] = "password"
                await update.message.reply_text("🔐 Enter your 2FA password")
            else:
                await update.message.reply_text(f"❌ Login failed:\n{e}")

    # STEP 3: 2FA
    elif state["step"] == "password":
        try:
            await login_client.sign_in(password=text)

            await update.message.reply_text("✅ Login successful!")
            login_state.pop(user_id)

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
        keyboard = [[InlineKeyboardButton(s, callback_data=f"svc:{s}")]
                    for s in list_services()]
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
        msg = start_service(data.split(":")[1])
        await query.edit_message_text(msg, reply_markup=main_menu(), parse_mode="Markdown")

    elif data.startswith("stop:"):
        msg = stop_service(data.split(":")[1])
        await query.edit_message_text(msg, reply_markup=main_menu())

# ---------------- WHOAMI ----------------
async def get_whoami():
    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)

    await client.connect()

    try:
        if await client.is_user_authorized():
            me = await client.get_me()

            if me.username:
                return f"@{me.username}"
            elif me.first_name:
                return me.first_name
            else:
                return str(me.id)

        return "Not Logged In"

    except Exception:
        return "Unknown"

    finally:
        await client.disconnect()

# ---------------- MAIN ----------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("login", login))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, login_flow))
    app.add_handler(CallbackQueryHandler(router))

    print("🤖 Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
