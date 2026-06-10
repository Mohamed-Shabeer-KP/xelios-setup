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
    "~/xelios-setup/services/telegram-session/downloader"
)

DOWNLOAD_DIR = os.path.expanduser("~/xelios-downloads")
PAUSE_FILE = "/tmp/tg_downloader_pause"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO)

client = TelegramClient(SESSION_PATH, API_ID, API_HASH)

# ---------------- STATE ----------------
queue = asyncio.Queue()
current = {"msg": None, "progress": 0}


# ---------------- CLI CONTROL ----------------
def cli():
    if len(sys.argv) < 2:
        return

    cmd = sys.argv[1]

    if cmd == "pause":
        open(PAUSE_FILE, "w").close()
        print("paused")
        sys.exit(0)

    elif cmd == "resume":
        if os.path.exists(PAUSE_FILE):
            os.remove(PAUSE_FILE)
        print("resumed")
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
    current["progress"] = p

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
            current["progress"] = 0
            queue.task_done()


# ---------------- EVENTS ----------------
@client.on(events.NewMessage)
async def handle(event):
    if not event.message.media:
        return

    await event.reply("📥 Added to queue")
    await queue.put(event)


# ---------------- MAIN ----------------
async def main():
    cli()

    await client.start()

    if not await client.is_user_authorized():
        print("❌ Login required")
        return

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
