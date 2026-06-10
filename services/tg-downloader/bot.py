#!/usr/bin/env python3

import os
import sys
import asyncio
import logging
import warnings

from telethon import TelegramClient, events

warnings.filterwarnings("ignore")

# ---------------- CONFIG ----------------
API_ID = 30299030
API_HASH = os.getenv("TELEGRAM_API_HASH")

SESSION_PATH = os.path.expanduser(
    "~/xelios-setup/services/telegram-session/downloader"
)

DOWNLOAD_DIR = os.path.expanduser("~/xelios-downloads")
PAUSE_FILE = "/tmp/tg_downloader_pause"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO)

client = TelegramClient(SESSION_PATH, API_ID, API_HASH)

# ---------------- STATE ----------------
queue = asyncio.Queue()

current = {
    "msg": None,
    "progress": 0
}

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

    elif cmd == "queue":
        print(queue.qsize())
        sys.exit(0)

# ---------------- UI ----------------
def bar(p):
    return "█" * (p // 10) + "░" * (10 - p // 10)

# ---------------- PROGRESS ----------------
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

    while os.path.exists(PAUSE_FILE):
        await asyncio.sleep(2)

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
    # ✅ Start login when user sends ANY message first
    if login_state["step"] == "phone" and not login_state["phone"]:
        await event.reply("🔐 Send your phone number (+countrycode)")
        return

    text = event.raw_text.strip()
    if not text:
        return

    # PHONE STEP
    if login_state["step"] == "phone":
        login_state["phone"] = text

        try:
            result = await client.send_code_request(text)

            login_state["phone_code_hash"] = result.phone_code_hash
            login_state["step"] = "code"

            await event.reply("📩 OTP sent. Send the code")

        except Exception as e:
            await event.reply(f"❌ {e}")

    # OTP STEP
    elif login_state["step"] == "code":
        try:
            await client.sign_in(
                phone=login_state["phone"],
                code=text,
                phone_code_hash=login_state["phone_code_hash"]
            )

            login_state["step"] = None

            await event.reply("✅ Login successful!")

        except Exception as e:
            await event.reply(f"❌ {e}")

# ---------------- DOWNLOAD HANDLER ----------------
@client.on(events.NewMessage(incoming=True))
async def downloader(event):

    # ✅ Ignore messages during login
    if login_state["step"] is not None:
        return

    if not event.message.media:
        return

    await event.reply("📥 Added to queue")
    await queue.put(event)

# ---------------- MAIN ----------------
async def main():
    cli()

    # ✅ ONLY connect (Critical fix)
    await client.connect()

    if not await client.is_user_authorized():
    
        print("🔐 Not logged in → waiting for Telegram login")
    
        # ✅ Use a known chat (Saved Messages via "me")
        login_state["step"] = "phone"
    
        # ✅ You must manually send first message
        print("\n👉 Send ANY message in Telegram (Saved Messages) to start login")

    else:
        print("✅ Already logged in")

    print("✅ Downloader running...")

    worker_task = asyncio.create_task(worker())

    try:
        await client.run_until_disconnected()

    finally:
        worker_task.cancel()
        try:
            await worker_task
        except:
            pass

        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
