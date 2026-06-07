#!/usr/bin/env python3
"""
Xelios Telegram Service Manager (FINAL)
"""

import os
import subprocess
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ---------------- LOGGING ----------------
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---------------- CONFIG ----------------
SERVICES_DIR = os.path.expanduser("~/xelios-setup/services")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

ALLOWED_USERS = []
for uid in os.getenv("ALLOWED_USER_IDS", "").split(","):
    uid = uid.strip()
    if uid.isdigit():
        ALLOWED_USERS.append(int(uid))


# ---------------- SECURITY ----------------
def is_allowed(user_id):
    return (not ALLOWED_USERS) or (user_id in ALLOWED_USERS)


# ---------------- HELPERS ----------------
def service_path(name):
    return os.path.join(SERVICES_DIR, name)


# ---------------- SERVICES ----------------
def list_services():
    if not os.path.isdir(SERVICES_DIR):
        return []

    return [
        s for s in sorted(os.listdir(SERVICES_DIR))
        if os.path.isdir(service_path(s))
        and os.path.isfile(os.path.join(service_path(s), "run"))
    ]


# ✅ FIXED STATUS CHECK
def is_running(name):
    try:
        path = service_path(name)

        result = subprocess.run(
            ["sv", "status", path],
            capture_output=True,
            text=True
        )

        return result.stdout.startswith("run:")

    except Exception:
        return False


def start_service(name):
    try:
        path = service_path(name)

        # remove "down" file if exists
        subprocess.run(["rm", "-f", f"{path}/down"])

        subprocess.run(["sv", "up", path], capture_output=True)

        return True, f"🟢 {name} started"

    except Exception as e:
        return False, str(e)


def stop_service(name):
    try:
        path = service_path(name)

        subprocess.run(["sv", "down", path], capture_output=True)
        subprocess.run(["touch", f"{path}/down"])

        return True, f"🔴 {name} stopped"

    except Exception as e:
        return False, str(e)


def start_all():
    try:
        for s in list_services():
            start_service(s)
        return True, "All services started"
    except Exception as e:
        return False, str(e)


def stop_all():
    try:
        for s in list_services():
            stop_service(s)
        return True, "All services stopped"
    except Exception as e:
        return False, str(e)


# ---------------- UI ----------------
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Status", callback_data="status")],
        [
            InlineKeyboardButton("▶️ Start All", callback_data="start_all"),
            InlineKeyboardButton("⏹️ Stop All", callback_data="stop_all")
        ],
        [InlineKeyboardButton("🔧 Services", callback_data="services")]
    ])


# ---------------- COMMAND ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        await update.message.reply_text("❌ Unauthorized")
        return

    await update.message.reply_text(
        "🤖 *Xelios Service Manager*",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )


# ---------------- ROUTER ----------------
async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_allowed(update.effective_user.id):
        await query.edit_message_text("❌ Unauthorized")
        return

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

    # ---- START ALL ----
    elif data == "start_all":
        ok, msg = start_all()
        await query.edit_message_text(("✅ " if ok else "❌ ") + msg, reply_markup=main_menu())

    # ---- STOP ALL ----
    elif data == "stop_all":
        ok, msg = stop_all()
        await query.edit_message_text(("✅ " if ok else "❌ ") + msg, reply_markup=main_menu())

    # ---- SERVICES MENU ----
    elif data == "services":
        services = list_services()

        keyboard = [
            [InlineKeyboardButton(s, callback_data=f"svc:{s}")]
            for s in services
        ]
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back")])

        await query.edit_message_text(
            "🔧 Services:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # ---- BACK ----
    elif data == "back":
        await start(update, context)

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

    # ---- START SERVICE ----
    elif data.startswith("start:"):
        name = data.split("start:")[1]
        ok, msg = start_service(name)

        await query.edit_message_text(
            ("✅ " if ok else "❌ ") + msg,
            reply_markup=main_menu()
        )

    # ---- STOP SERVICE ----
    elif data.startswith("stop:"):
        name = data.split("stop:")[1]
        ok, msg = stop_service(name)

        await query.edit_message_text(
            ("✅ " if ok else "❌ ") + msg,
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


if __name__ == "__main__":
    main()