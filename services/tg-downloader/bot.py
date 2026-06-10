#!/usr/bin/env python3

import os
import sys
import logging
import warnings

from telethon import TelegramClient, events

warnings.filterwarnings("ignore", category=RuntimeWarning)

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
download_queue = asyncio.Queue()

current = {
    "progress": 0,
    "msg": None
}


# ---------------- CLI ----------------
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
        print(download_queue.qsize())
        sys.exit(0)


# ---------------- UI ----------------
def progress_bar(p):
    filled = p // 10
    return "█" * filled + "░" * (10 - filled)


# ---------------- PROGRESS ----------------
async def progress_cb(current_bytes, total):
    if total == 0:
        return

    percent = int(current_bytes * 100 / total)
    current["progress"] = percent

    if current["msg"]:
        try:
            await current["msg"].edit(
                f"⬇️ Downloading...\n"
                f"[{progress_bar(percent)}] {percent}%"
            )
        except:
            pass

    while os.path.exists(PAUSE_FILE):
        await asyncio.sleep(2)


# ---------------- WORKER ----------------
async def worker():
    while True:
        event = await download_queue.get()

        try:
            msg = await event.reply("⬇️ Starting download...")
            current["msg"] = msg
            current["progress"] = 0

            path = await event.message.download_media(
                file=DOWNLOAD_DIR,
                progress_callback=progress_cb
            )

            await msg.edit(f"✅ Download completed\n📁 {path}")

        except Exception as e:
            if current["msg"]:
                await current["msg"].edit(f"❌ Failed: {e}")

        finally:
            current["msg"] = None
            current["progress"] = 0
            download_queue.task_done()


# ---------------- EVENTS ----------------
@client.on(events.NewMessage)
async def handle_media(event):

    if not event.message.media:
        return

    await event.reply("📥 Added to download queue")

    await download_queue.put(event)


# ---------------- MAIN ----------------
async def main():
    cli()

    await client.start()

    if not await client.is_user_authorized():
        print("❌ Not logged in")
        return

    print("✅ Downloader running...")

    task = asyncio.create_task(worker())

    try:
        await client.run_until_disconnected()

    finally:
        task.cancel()
        try:
            await task
        except:
            pass

        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
