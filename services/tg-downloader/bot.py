
#!/usr/bin/env python3

from telethon import TelegramClient, events
import os
import asyncio

API_HASH = os.getenv("TELEGRAM_API_HASH", "")

API_ID = 30299030

CHANNEL = "Xelios Downloader"
DOWNLOAD_DIR = "../storage/shared/download"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

SESSION_PATH = os.path.expanduser("~/xelios-setup/services/telegram-session/session")

client = TelegramClient(SESSION_PATH, API_ID, API_HASH)

# ---------------- ENSURE LOGIN ----------------
async def ensure_logged_in():
    await client.connect()

    if not await client.is_user_authorized():
        print("❌ Not logged in. Use bot LOGIN first.")
        exit(1)

# ---------------- GLOBAL STATE ----------------
DOWNLOAD_STATE = {
    "paused": False,
    "current_task": None,
    "file_path": None,
    "message": None
}

def progress_bar(received, total):
    if total == 0:
        return "0%"
    percent = received / total * 100
    bar_len = 20
    filled = int(bar_len * received // total)
    bar = "█" * filled + "░" * (bar_len - filled)
    return f"{percent:.1f}% [{bar}]"

@client.on(events.NewMessage(chats=CHANNEL))
async def handler(event):
    msg = event.message

    if not msg.media:
        return

    DOWNLOAD_STATE["paused"] = False
    DOWNLOAD_STATE["message"] = msg

    status = await event.reply("📥 Download started...")

    file_name = msg.file.name or f"{msg.id}.bin"
    file_path = os.path.join(DOWNLOAD_DIR, file_name)

    DOWNLOAD_STATE["file_path"] = file_path

    offset = os.path.getsize(file_path) if os.path.exists(file_path) else 0
    last_update_time = 0

    async def progress_callback(received, total):
        nonlocal last_update_time

        if DOWNLOAD_STATE["paused"]:
            raise asyncio.CancelledError()

        now = asyncio.get_event_loop().time()
        if now - last_update_time < 1:
            return

        last_update_time = now

        text = (
            "📥 Downloading...\n"
            f"{progress_bar(received + offset, total)}\n"
            f"{(received+offset)/1024/1024:.2f} MB / {total/1024/1024:.2f} MB"
        )

        try:
            await status.edit(text)
        except:
            pass

    try:
        DOWNLOAD_STATE["current_task"] = asyncio.create_task(
            msg.download_media(
                file=file_path,
                progress_callback=progress_callback,
                offset=offset
            )
        )

        path = await DOWNLOAD_STATE["current_task"]
        await status.edit(f"✅ Download complete:\n`{path}`")

    except asyncio.CancelledError:
        await status.edit("⏸️ Download paused")

# ---------------- PAUSE ----------------
@client.on(events.NewMessage(pattern="/pause"))
async def pause_handler(event):
    DOWNLOAD_STATE["paused"] = True
    await event.reply("⏸️ Pause requested")

# ---------------- RESUME ----------------
@client.on(events.NewMessage(pattern="/resume"))
async def resume_handler(event):
    if not DOWNLOAD_STATE["message"]:
        await event.reply("No download to resume")
        return

    await event.reply("▶️ Resuming...")
    await handler(DOWNLOAD_STATE["message"])

# ---------------- MAIN ----------------
async def main():
    await ensure_logged_in()
    print("✅ Downloader running...")
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())
