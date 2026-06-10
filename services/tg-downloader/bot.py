#!/usr/bin/env python3

import os
import sys
import asyncio
import logging
import warnings

from telethon import TelegramClient, events

warnings.filterwarnings("ignore", category=RuntimeWarning)

# ---------------- CONFIG ----------------
API_ID = 30299030
API_HASH = os.getenv("TELEGRAM_API_HASH", "")

SESSION_PATH = os.path.expanduser(
    "~/xelios-setup/services/telegram-session/session"
)

DOWNLOAD_DIR = os.path.expanduser("~/xelios-downloads")

PAUSE_FILE = "/tmp/tg_downloader_pause"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO)

client = TelegramClient(SESSION_PATH, API_ID, API_HASH)

# ---------------- STATE ----------------
download_queue = asyncio.Queue()

current_download = {
    "event": None,
    "progress": 0,
    "msg": None
}

# ---------------- PROGRESS BAR ----------------
def build_progress_bar(percent):
    filled = int(percent / 10)
    bar = "█" * filled + "░" * (10 - filled)
    return f"[{bar}] {percent}%"

# ---------------- CLI COMMANDS ----------------
def handle_cli_commands():
    if len(sys.argv) < 2:
        return

    cmd = sys.argv[1]

    if cmd == "pause":
        open(PAUSE_FILE, "w").close()
        print("⏸️ Paused")
        sys.exit(0)

    elif cmd == "resume":
        if os.path.exists(PAUSE_FILE):
            os.remove(PAUSE_FILE)
        print("▶️ Resumed")
        sys.exit(0)

    elif cmd == "status":
        if current_download["event"]:
            print(f"{current_download['progress']}%")
        else:
            print("idle")
        sys.exit(0)

    elif cmd == "queue":
        print(download_queue.qsize())
        sys.exit(0)

# ---------------- PROGRESS CALLBACK ----------------
async def progress_callback(current, total):
    if total == 0:
        return

    percent = int(current * 100 / total)
    current_download["progress"] = percent

    bar = build_progress_bar(percent)

    # ✅ Update Telegram UI message
    if current_download["msg"]:
        try:
            await current_download["msg"].edit(
                f"⬇️ Downloading...\n{bar}"
            )
        except:
            pass

    # ✅ Pause logic
    while os.path.exists(PAUSE_FILE):
        await asyncio.sleep(2)

# ---------------- WORKER ----------------
async def worker():
    while True:
        event = await download_queue.get()

        try:
            message = event.message
            current_download["event"] = event
            current_download["progress"] = 0

            # ✅ Create UI message
            ui_msg = await event.reply("⬇️ Starting download...")
            current_download["msg"] = ui_msg

            file_path = await message.download_media(
                file=DOWNLOAD_DIR,
                progress_callback=progress_callback
            )

            await ui_msg.edit(f"✅ Downloaded\n📁 {file_path}")

        except Exception as e:
            logging.error(f"\n❌ Failed: {e}")
            if current_download["msg"]:
                await current_download["msg"].edit(f"❌ Failed: {e}")

        finally:
            current_download["event"] = None
            current_download["progress"] = 0
            current_download["msg"] = None

            download_queue.task_done()

# ---------------- EVENT HANDLER ----------------
@client.on(events.NewMessage(pattern=r"^/(pause|resume|status|queue)$"))
async def control_handler(event):

    cmd = event.pattern_match.group(1)

    if cmd == "pause":
        open(PAUSE_FILE, "w").close()
        await event.reply("⏸️ Paused")

    elif cmd == "resume":
        if os.path.exists(PAUSE_FILE):
            os.remove(PAUSE_FILE)
        await event.reply("▶️ Resumed")

    elif cmd == "status":
        if current_download["event"]:
            await event.reply(
                f"⬇️ {build_progress_bar(current_download['progress'])}"
            )
        else:
            await event.reply("✅ No active download")

    elif cmd == "queue":
        await event.reply(f"📦 Queue size: {download_queue.qsize()}")

# ✅ Capture media
@client.on(events.NewMessage)
async def handler(event):

    message = event.message

    if not message.media:
        return

    await event.reply("📥 Added to queue")

    await download_queue.put(event)

# ---------------- MAIN ----------------
async def main():
    handle_cli_commands()

    await client.start()

    if not await client.is_user_authorized():
        print("❌ Not logged in")
        return

    print("✅ Downloader running...")

    worker_task = asyncio.create_task(worker())

    try:
        await client.run_until_disconnected()

    except asyncio.CancelledError:
        print("\n🛑 Stopped")

    finally:
        print("🧹 Cleaning up...")

        worker_task.cancel()
        try:
            await worker_task
        except:
            pass

        try:
            await client.disconnect()
        except:
            pass

        await asyncio.sleep(0.5)

        print("✅ Shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())
