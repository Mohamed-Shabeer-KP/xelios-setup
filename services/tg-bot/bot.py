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
SERVICE_NAME = "tg-downloader"

logging.basicConfig(level=logging.INFO)

# ---------------- HELPERS ----------------
def run_sv(command):
    result = subprocess.run(
        ["sv", command, SERVICE_NAME],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()


def run_downloader(cmd):
    return subprocess.run(
        ["python3", "/full/path/to/tg-downloader.py", cmd],
        capture_output=True,
        text=True
    ).stdout.strip()


# ---------------- UI ----------------
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Status", callback_data="status")],
        [InlineKeyboardButton("▶ Start", callback_data="start")],
        [InlineKeyboardButton("⏹ Stop", callback_data="stop")],
        [InlineKeyboardButton("⏸ Pause", callback_data="pause")],
        [InlineKeyboardButton("▶ Resume", callback_data="resume")],
        [InlineKeyboardButton("📦 Queue", callback_data="queue")]
    ])


# ---------------- COMMAND ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Xelios Service Manager*",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )


# ---------------- ROUTER ----------------
async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "status":
        status = run_sv("status")
        await query.edit_message_text(
            f"📊 *Service Status*\n\n{status}",
            reply_markup=main_menu(),
            parse_mode="Markdown"
        )

    elif data == "start":
        run_sv("up")
        await query.edit_message_text(
            "▶ Downloader started",
            reply_markup=main_menu()
        )

    elif data == "stop":
        run_sv("down")
        await query.edit_message_text(
            "⏹ Downloader stopped",
            reply_markup=main_menu()
        )

    elif data == "pause":
        run_downloader("pause")
        await query.edit_message_text(
            "⏸ Downloads paused",
            reply_markup=main_menu()
        )

    elif data == "resume":
        run_downloader("resume")
        await query.edit_message_text(
            "▶ Downloads resumed",
            reply_markup=main_menu()
        )

    elif data == "queue":
        q = run_downloader("queue")
        await query.edit_message_text(
            f"📦 Queue size: {q}",
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
