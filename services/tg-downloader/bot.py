#!/usr/bin/env python3

import os
import asyncio
import logging
import sys

from telethon import TelegramClient, events

# ---------------- CONFIG ----------------
API_ID = 30299030
API_HASH = os.getenv("TELEGRAM_API_HASH")

PHONE_NUMBER = "+917025257580"  # 👈 CHANGE THIS

SESSION_PATH = os.path.expanduser(
    "~/xelios-setup/services/tg-downloader/session"
)

DOWNLOAD_DIR = os.path.expanduser("~/xelios-downloads")

PAUSE_FILE = "/tmp/tg_downloader_pause"
LOGIN_FILE = "/tmp/tg_login_code"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO)

client = TelegramClient(SESSION_PATH, API_ID, API_HASH)

queue = asyncio.Queue()

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

# ---------------- LOGIN ----------------
async def auto_login():
    await client.connect()

    if await client.is_user_authorized():
        print("✅ Already logged in")
        return

    print("🔐 Sending OTP...")

    result = await client.send_code_request(PHONE_NUMBER)
    phone_code_hash = result.phone_code_hash

    print("📩 OTP sent. Waiting for /otp ...")

    while not os.path.exists(LOGIN_FILE):
        await asyncio.sleep(1)

    with open(LOGIN_FILE) as f:
        code = f.read().strip()

    os.remove(LOGIN_FILE)

    await client.sign_in(
        phone=PHONE_NUMBER,
        code=code,
        phone_code_hash=phone_code_hash
    )

    print("✅ Login successful")

# ---------------- PROGRESS ----------------
def bar(p):
    return "█" * (p // 10) + "░" * (10 - p // 10)

async def progress_cb(msg, current, total):
    if total == 0:
        return

    pct = int(current * 100 / total)

    try:
        await msg.edit(f"⬇️ Downloading...\n[{bar(pct)}] {pct}%")
    except:
        pass

# ---------------- WORKER ----------------
async def worker():
    while True:
        event = await queue.get()

        try:
            ui = await event.reply("⬇️ Starting download...")

            while os.path.exists(PAUSE_FILE):
                await asyncio.sleep(1)

            path = await event.message.download_media(
                file=DOWNLOAD_DIR,
                progress_callback=lambda c, t: asyncio.create_task(
                    progress_cb(ui, c, t)
                )
            )

            await ui.edit(f"✅ Downloaded\n📁 {path}")

        except Exception as e:
            try:
                await ui.edit(f"❌ Failed: {e}")
            except:
                pass

        finally:
            queue.task_done()

# ---------------- DOWNLOADER ----------------
@client.on(events.NewMessage(incoming=True))
async def downloader(event):

    if not await client.is_user_authorized():
        return

    if not event.message.media:
        return

    await event.reply("📥 Added to queue")
    await queue.put(event)

# ---------------- MAIN ----------------
async def main():
    cli()

    await auto_login()

    print("✅ Downloader running...")

    worker_task = asyncio.create_task(worker())

    try:
        await client.run_until_disconnected()
    finally:
        worker_task.cancel()
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
