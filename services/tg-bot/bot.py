#!/usr/bin/env python3

import os
import subprocess

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes
)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# ✅ service name (runit)
SERVICE_NAME = "tg-downloader"


# ---------------- SERVICE HELPERS ----------------
def service_cmd(cmd):
    return subprocess.run(["sv", cmd, SERVICE_NAME],
                          capture_output=True, text=True)


def service_status():
    result = service_cmd("status")
    return result.stdout.strip()


# ---------------- UI ----------------
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Status", callback_data="status")],
        [InlineKeyboardButton("▶ Start Downloader", callback_data="start")],
        [InlineKeyboardButton("⏹ Stop Downloader", callback_data="stop")],
        [InlineKeyboardButton("⏸ Pause", callback_data="pause")],
        [InlineKeyboardButton("▶ Resume", callback_data="resume")],
        [InlineKeyboardButton("📦 Queue", callback_data="queue")],
    ])


# ---------------- COMMAND ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Downloader Control Panel*",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )


# ---------------- ROUTER ----------------
async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    # ✅ STATUS
    if data == "status":
        status = service_status()
        await query.edit_message_text(
            f"📊 *Service Status*\n\n{status}",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )

    # ✅ START SERVICE
    elif data == "start":
        service_cmd("up")
        await query.edit_message_text(
            "▶ Downloader started",
            reply_markup=main_menu()
        )

    # ✅ STOP SERVICE
    elif data == "stop":
        service_cmd("down")
        await query.edit_message_text(
            "⏹ Downloader stopped",
            reply_markup=main_menu()
        )

    # ✅ PAUSE
    elif data == "pause":
        subprocess.run(["python3", "/path/to/tg-downloader.py", "pause"])
        await query.edit_message_text(
            "⏸ Downloads paused",
            reply_markup=main_menu()
        )

    # ✅ RESUME
    elif data == "resume":
        subprocess.run(["python3", "/path/to/tg-downloader.py", "resume"])
        await query.edit_message_text(
            "▶ Downloads resumed",
            reply_markup=main_menu()
        )

    # ✅ QUEUE
    elif data == "queue":
        result = subprocess.run(
            ["python3", "/path/to/tg-downloader.py", "queue"],
            capture_output=True,
            text=True
        )

        await query.edit_message_text(
            f"📦 Queue size: {result.stdout.strip()}",
            reply_markup=main_menu()
        )


# ---------------- MAIN ----------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(router))

    print("🤖 Control bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
