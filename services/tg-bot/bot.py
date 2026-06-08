#!/usr/bin/env python3

import os
import subprocess
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ---------------- CONFIG ----------------
SERVICES_DIR = os.path.expanduser("~/xelios-setup/services")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

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
    except Exception:
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
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Status", callback_data="status")],
        [InlineKeyboardButton("🔧 Services", callback_data="services")]
    ])

# ---------------- RENDER HELPERS ----------------
async def render_main_menu(query):
    await query.edit_message_text(
        "🤖 *Xelios Service Manager*",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

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

    # ---- STATUS ----
    if data == "status":
        services = list_services()

        text = "📊 *Service Status*\n\n"
        for s in services:
            icon = "🟢" if is_running(s) else "🔴"
            text += f"{icon} {s}\n"

        await query.edit_message_text(
            text,
            reply_markup=main_menu(),
            parse_mode="Markdown"
        )

    # ---- SERVICES MENU ----
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

    # ---- BACK TO MAIN MENU ----
    elif data == "back":
        await render_main_menu(query)

    # ---- SERVICE DETAILS ----
    elif data.startswith("svc:"):
        name = data.split("svc:")[1]
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

    # ---- START ----
    elif data.startswith("start:"):
        name = data.split("start:")[1]
        msg = start_service(name)

        await query.edit_message_text(
            msg,
            reply_markup=main_menu()
        )

    # ---- STOP ----
    elif data.startswith("stop:"):
        name = data.split("stop:")[1]
        msg = stop_service(name)

        await query.edit_message_text(
            msg,
            reply_markup=main_menu()
        )

# ---------------- MAIN ----------------
def main():
    if not BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not set")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(router))

    print("🤖 Bot running...")
    app.run_polling()

# ---------------- ENTRY ----------------
if __name__ == "__main__":
    main()