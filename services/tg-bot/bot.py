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
API_HASH = os.getenv("TELEGRAM_API_HASH", "")
API_ID = 30299030

SESSION_PATH = os.path.expanduser(
    "~/xelios-setup/services/telegram-session/session"
)

DOWNLOADER_PATH = os.path.abspath("tg-downloader.py")

logging.basicConfig(level=logging.INFO)

client = TelegramClient(SESSION_PATH, API_ID, API_HASH)

# ✅ Login state
LOGIN_STATE = {
    "step": None,
    "phone": None,
    "phone_code_hash": None
}

# ---------------- UI ----------------
async def main_menu():
    await client.connect()
    logged_in = await client.is_user_authorized()

    buttons = []

    if not logged_in:
        buttons.append([InlineKeyboardButton("🔐 Login", callback_data="login")])

    return InlineKeyboardMarkup(buttons)


# ---------------- COMMAND ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Telegram Downloader Bot*\n\n"
        "Send a Telegram link or file to download.",
        reply_markup=await main_menu(),
        parse_mode="Markdown"
    )


# ---------------- LOGIN FLOW ----------------
async def start_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await client.connect()

    if await client.is_user_authorized():
        await update.callback_query.answer("✅ Already logged in", show_alert=True)
        return

    LOGIN_STATE["step"] = "phone"

    await update.callback_query.edit_message_text(
        "📱 Send phone number (+countrycode)"
    )


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await client.connect()

    text = update.message.text if update.message.text else ""

    # -------------------------------------------------
    # ✅ LOGIN FLOW
    # -------------------------------------------------
    if LOGIN_STATE["step"] is not None:

        if await client.is_user_authorized():
            LOGIN_STATE["step"] = None
            await update.message.reply_text("✅ Already logged in")
            return

        if LOGIN_STATE["step"] == "phone":
            LOGIN_STATE["phone"] = text

            result = await client.send_code_request(text)

            LOGIN_STATE["phone_code_hash"] = result.phone_code_hash
            LOGIN_STATE["step"] = "code"

            await update.message.reply_text("📩 OTP sent. Send the code")

        elif LOGIN_STATE["step"] == "code":
            try:
                await client.sign_in(
                    phone=LOGIN_STATE["phone"],
                    code=text,
                    phone_code_hash=LOGIN_STATE["phone_code_hash"]
                )

                LOGIN_STATE["step"] = None
                LOGIN_STATE["phone"] = None
                LOGIN_STATE["phone_code_hash"] = None

                await update.message.reply_text("✅ Login successful!")

            except Exception as e:
                await update.message.reply_text(f"❌ {e}")

        return

    # -------------------------------------------------
    # ✅ REQUIRE LOGIN
    # -------------------------------------------------
    if not await client.is_user_authorized():
        await update.message.reply_text("🔐 Please login first")
        return

    # -------------------------------------------------
    # ✅ CALL DOWNLOADER FOR LINKS
    # -------------------------------------------------
    if "t.me/" in text:

        await update.message.reply_text("⬇️ Downloading...")

        try:
            result = subprocess.run(
                ["python3", DOWNLOADER_PATH, text],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                await update.message.reply_text(f"❌ {result.stderr}")
                return

            file_path = result.stdout.strip()

            if not os.path.exists(file_path):
                await update.message.reply_text("❌ File not found")
                return

            await update.message.reply_document(document=file_path)

        except Exception as e:
            await update.message.reply_text(f"❌ {e}")

        return

    await update.message.reply_text(
        "📩 Send a Telegram link to download."
    )


# ---------------- ROUTER ----------------
async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "login":
        await start_login(update, context)


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
