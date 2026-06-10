#!/usr/bin/env python3

import os
import asyncio
import logging
import warnings
import sys

from telethon import TelegramClient, events

warnings.filterwarnings("ignore")

# ---------------- CONFIG ----------------
API_ID = 30299030
API_HASH = os.getenv("TELEGRAM_API_HASH")

SESSION_PATH = os.path.expanduser(
    "~/xelios-setup/services/tg-downloader/session"
)

DOWNLOAD_DIR = os.path.expanduser("~/xelios-downloads")
PAUSE_FILE = "/tmp/tg_downloader_pause"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO)

client = TelegramClient(SESSION_PATH, API_ID, API_HASH)

# ---------------- STATE ----------------
queue = asyncio.Queue()

current = {"msg": None}
login_state = {
    "step": None,
    "phone": None,
    "phone_code_hash": None
}

# ---------------- CLI ----------------
def cli():
    if len(sys.argv) < 2:
        return

    cmd = sys.argv[1]

    if cmd == "pause":
        open(PAUSE_FILE, "w").close()
        sys.exit(0)

    elif cmd == "resume":
        if os.path.exists(PAUSE_FILE):
            os.remove(PAUSE_FILE)
        sys.exit(0)
    
    elif cmd == "status":
        async def check():
            await client.connect()
            if await client.is_user_authorized():
                print("LOGGED_IN")
            else:
                print("NOT_LOGGED_IN")
            await client.disconnect()
    
        asyncio.run(check())
        sys.exit(0)


# ---------------- UI ----------------
def bar(p):
    return "█" * (p // 10) + "░" * (10 - p // 10)

async def progress_cb(current_bytes, total):
    if total == 0:
        return

    p = int(current_bytes * 100 / total)

    if current["msg"]:
        try:
            await current["msg"].edit(
                f"⬇️ Downloading...\n[{bar(p)}] {p}%"
            )
        except:
            pass

# ---------------- WORKER ----------------
async def worker():
    while True:
        event = await queue.get()

        try:
            ui = await event.reply("⬇️ Starting download...")
            current["msg"] = ui

            path = await event.message.download_media(
                file=DOWNLOAD_DIR,
                progress_callback=progress_cb
            )

            await ui.edit(f"✅ Downloaded\n📁 {path}")

        except Exception as e:
            if current["msg"]:
                await current["msg"].edit(f"❌ Failed: {e}")

        finally:
            current["msg"] = None
            queue.task_done()

# ---------------- LOGIN FLOW ----------------
@client.on(events.NewMessage(incoming=True))
async def login_flow(event):

    if not await client.is_user_authorized():

        text = event.raw_text.strip() if event.raw_text else ""

        if login_state["step"] is None:
            login_state["step"] = "phone"
            await event.reply(
                "🔐 Login Required\n\nSend your phone number (+countrycode)"
            )
            return

        elif login_state["step"] == "phone":
            login_state["phone"] = text

            result = await client.send_code_request(text)

            login_state["phone_code_hash"] = result.phone_code_hash
            login_state["step"] = "code"

            await event.reply("📩 OTP sent. Send code")
            return

        elif login_state["step"] == "code":
            await client.sign_in(
                phone=login_state["phone"],
                code=text,
                phone_code_hash=login_state["phone_code_hash"]
            )

            login_state["step"] = None

            await event.reply("✅ Login successful!")
            return

# ---------------- DOWNLOAD ----------------
@client.on(events.NewMessage(incoming=True))
async def downloader(event):

    if login_state["step"] is not None:
        return

    if not event.message.media:
        return

    await event.reply("📥 Added to queue")
    await queue.put(event)

# ---------------- MAIN ----------------
async def main():
    cli()

    await client.connect()

    if not await client.is_user_authorized():
        print("🔐 Not logged in → send message in Telegram to start login")
    else:
        print("✅ Logged in")

    worker_task = asyncio.create_task(worker())

    try:
        await client.run_until_disconnected()

    finally:
        worker_task.cancel()
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
