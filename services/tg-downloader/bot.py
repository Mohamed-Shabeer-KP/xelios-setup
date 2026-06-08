#!/usr/bin/env python3

from telethon import TelegramClient, events
import os
import asyncio

API_HASH = os.getenv("TELEGRAM_API_HASH", "")

api_id = 30299030
api_hash = API_HASH

CHANNEL = "Xelios Downloader"
DOWNLOAD_DIR = "../storage/shared/download"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

client = TelegramClient("session", api_id, api_hash)

# Global control flags
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

    # get existing file size (for resume)
    offset = 0
    if os.path.exists(file_path):
        offset = os.path.getsize(file_path)

    last_update_time = 0

    async def progress_callback(received, total):
        nonlocal last_update_time

        # Pause logic
        if DOWNLOAD_STATE["paused"]:
            raise asyncio.CancelledError()  # stop download

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
                offset=offset  # ✅ resume support
            )
        )

        path = await DOWNLOAD_STATE["current_task"]

        await status.edit(f"✅ Download complete:\n`{path}`")

    except asyncio.CancelledError:
        await status.edit("⏸️ Download paused")


# ✅ Pause command
@client.on(events.NewMessage(pattern="/pause"))
async def pause_handler(event):
    DOWNLOAD_STATE["paused"] = True
    await event.reply("⏸️ Download pause requested...")


# ✅ Resume command
@client.on(events.NewMessage(pattern="/resume"))
async def resume_handler(event):
    if not DOWNLOAD_STATE["message"]:
        await event.reply("No download to resume")
        return

    await event.reply("▶️ Resuming download...")

    # Trigger handler again (resume from file size)
    await handler(DOWNLOAD_STATE["message"])


async def main():
    print("Listening...")
    await client.run_until_disconnected()


with client:
    client.loop.run_until_complete(main())