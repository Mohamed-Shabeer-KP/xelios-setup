#!/usr/bin/env python3

import os
import sys
import asyncio
import logging
import signal

from telethon import TelegramClient, events

# ---------------- CONFIG ----------------
API_ID = 30299030
API_HASH = os.getenv("TELEGRAM_API_HASH", "")

SESSION_PATH = os.path.expanduser(
    "~/xelios-setup/services/telegram-session/session"
)

DOWNLOAD_DIR = os.path.expanduser("~/xelios-downloads")

PAUSE_FILE = "/tmp/tg_downloader_pause"

# ✅ Fix for Termux / Python 3.13 stability
asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())

logging.basicConfig(level=logging.INFO)

client = TelegramClient(SESSION_PATH, API_ID, API_HASH)

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ---------------- STATE ----------------
download_queue = asyncio.Queue()

current_download = {
    "name": None,
    "progress": 0
}


# ✅ CLI COMMANDS (pause/resume/status/queue)
def handle_cli_commands():
    if len(sys.argv) < 2:
        return

    cmd = sys.argv[1]

    if cmd == "pause":
        open(PAUSE_FILE, "w").close()
        print("⏸️ Paused downloads")
        sys.exit(0)

    elif cmd == "resume":
        if os.path.exists(PAUSE_FILE):
            os.remove(PAUSE_FILE)
        print("▶️ Resumed downloads")
        sys.exit(0)

    elif cmd == "status":
        if current_download["name"]:
            print(f"Downloading: {current_download['progress']}%")
        else:
            print("No active download")
        sys.exit(0)

    elif cmd == "queue":
        print(f"Queue size: {download_queue.qsize()}")
        sys.exit(0)


# ---------------- PROGRESS ----------------
async def progress_callback(current, total):
    if total == 0:
        return

    percent = int(current * 100 / total)
    current_download["progress"] = percent

    print(f"⬇️ Progress: {percent}%", end="\r")

    # ✅ Pause handling
    while os.path.exists(PAUSE_FILE):
        print("\n⏸️ Paused...")
        await asyncio.sleep(2)


# ---------------- WORKER ----------------
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


# ---------------- EVENT LISTENER ----------------
@client.on(events.NewMessage)
async def handler(event):

    message = event.message

    # ✅ Only download media
    if not message.media:
        return

    logging.info("📥 Added to queue")

    await download_queue.put(event)


# ---------------- MAIN ----------------
async def main():
    handle_cli_commands()

    await client.start()

    if not await client.is_user_authorized():
        print("❌ Not logged in")
        return

    print("✅ Downloader service running...")

    # ✅ Start worker
    worker_task = asyncio.create_task(worker())

    # ✅ Graceful shutdown (FIXES YOUR ERROR)
    stop_event = asyncio.Event()

    def shutdown_handler(*args):
        print("\n🛑 Shutting down...")
        stop_event.set()

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    # ✅ Wait until stop signal
    await stop_event.wait()

    # ✅ Cleanup
    worker_task.cancel()

    await client.disconnect()

    print("✅ Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
