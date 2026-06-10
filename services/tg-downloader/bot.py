#!/usr/bin/env python3

import os
import asyncio
import logging

from telethon import TelegramClient, events

API_ID = 30299030
API_HASH = os.getenv("TELEGRAM_API_HASH", "")

SESSION_PATH = os.path.expanduser(
    "~/xelios-setup/services/telegram-session/session"
)

DOWNLOAD_DIR = os.path.expanduser("~/storage/shared/download")

PAUSE_FILE = "/tmp/tg_downloader_pause"

logging.basicConfig(level=logging.INFO)

client = TelegramClient(SESSION_PATH, API_ID, API_HASH)

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ✅ Queue
download_queue = asyncio.Queue()

current_download = {
    "name": None,
    "progress": 0
}


# ✅ Progress callback
async def progress_callback(current, total):
    if total == 0:
        return

    percent = int(current * 100 / total)
    current_download["progress"] = percent

    print(f"⬇️ Downloading: {percent}%", end="\r")

    # ✅ Pause handling
    while os.path.exists(PAUSE_FILE):
        print("⏸️ Paused... waiting")
        await asyncio.sleep(2)


# ✅ Process queue
async def worker():
    while True:
        event = await download_queue.get()

        try:
            message = event.message

            current_download["name"] = f"{message.id}"
            current_download["progress"] = 0

            logging.info("⬇️ Starting download...")

            file_path = await message.download_media(
                file=DOWNLOAD_DIR,
                progress_callback=progress_callback
            )

            logging.info(f"\n✅ Downloaded: {file_path}")

        except Exception as e:
            logging.error(f"\n❌ Failed: {e}")

        finally:
            current_download["name"] = None
            current_download["progress"] = 0

            download_queue.task_done()


# ✅ Event listener
@client.on(events.NewMessage)
async def handler(event):

    message = event.message

    if not message.media:
        return

    logging.info("📥 Added to queue")

    await download_queue.put(event)


# ✅ CLI control commands
def handle_cli_commands():
    import sys

    if len(sys.argv) < 2:
        return

    cmd = sys.argv[1]

    # ✅ Pause
    if cmd == "pause":
        open(PAUSE_FILE, "w").close()
        print("⏸️ Paused downloads")
        exit(0)

    # ✅ Resume
    elif cmd == "resume":
        if os.path.exists(PAUSE_FILE):
            os.remove(PAUSE_FILE)
        print("▶️ Resumed downloads")
        exit(0)

    # ✅ Status
    elif cmd == "status":
        if current_download["name"]:
            print(f"Downloading: {current_download['progress']}%")
        else:
            print("No active download")
        exit(0)

    # ✅ Queue size
    elif cmd == "queue":
        print(f"Queue size: {download_queue.qsize()}")
        exit(0)


async def main():
    handle_cli_commands()

    await client.start()

    if not await client.is_user_authorized():
        print("❌ Not logged in")
        return

    print("✅ Downloader service running")

    # ✅ Start worker
    asyncio.create_task(worker())

    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
``
