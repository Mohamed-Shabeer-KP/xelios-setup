#!/usr/bin/env python3

import os
import asyncio
import logging

from telethon import TelegramClient, events

# ---------------- CONFIG ----------------
API_ID = 30299030
API_HASH = os.getenv("TELEGRAM_API_HASH")

TARGET_GROUP_NAME = "Downloader"

SESSION_PATH = os.path.expanduser(
    "~/xelios-setup/services/tg-downloader/session"
)

DOWNLOAD_DIR = os.path.expanduser("~/storage/shared/download")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO)

client = TelegramClient(SESSION_PATH, API_ID, API_HASH)

# ---------------- STATE ----------------
downloads = {}
counter = 0
lock = asyncio.Lock()

# ---------------- NEW MEDIA ----------------
@client.on(events.NewMessage)
async def downloader(event):
    global counter

    try:
        if not event.is_group:
            return

        chat = await event.get_chat()

        if not hasattr(chat, "title"):
            return

        if chat.title != TARGET_GROUP_NAME:
            return

        if not event.message.media:
            return

        async with lock:
            counter += 1
            task_id = counter

        file_name = event.file.name or f"file_{task_id}"

        downloads[task_id] = {
            "event": event,
            "name": file_name,
            "status": "queued",
            "paused": False,
            "cancelled": False,
            "progress": 0,
        }

        await client.send_message(
            event.chat_id,
            f"📥 *Queued:* {file_name} (ID: {task_id})\n\n"
            f"Commands:\n"
            f"▶ Start → `/start_{task_id}`\n"
            f"⏸ Pause → `/pause_{task_id}`\n"
            f"▶ Resume → `/resume_{task_id}`\n"
            f"❌ Remove → `/remove_{task_id}`\n"
            f"📦 Queue → `/queue`",
            parse_mode="markdown"
        )

    except Exception as e:
        print("❌ Handler error:", e)

# ---------------- COMMAND HANDLER ----------------
@client.on(events.NewMessage(pattern=r'^/(start|pause|resume|remove)_(\d+)'))
async def command_handler(event):
    cmd, task_id = event.pattern_match.groups()
    task_id = int(task_id)

    task = downloads.get(task_id)
    if not task:
        return await event.reply("❌ Task not found")

    if cmd == "start":
        if task["status"] == "queued":
            task["status"] = "downloading"
            asyncio.create_task(process_download(task_id))
            await event.reply(f"▶ Started: {task['name']}")

    elif cmd == "pause":
        task["paused"] = True
        await event.reply(f"⏸ Paused: {task['name']}")

    elif cmd == "resume":
        task["paused"] = False
        await event.reply(f"▶ Resumed: {task['name']}")

    elif cmd == "remove":
        task["cancelled"] = True
        task["status"] = "cancelled"
        await event.reply(f"❌ Removed: {task['name']}")

# ---------------- DOWNLOAD LOGIC ----------------
async def process_download(task_id):
    task = downloads[task_id]
    event = task["event"]

    progress_msg = await event.reply(f"⬇️ Starting: {task['name']}")

    last_update = 0

    try:
        async def progress(current, total):
            nonlocal last_update

            if task["cancelled"]:
                raise Exception("Cancelled")

            while task["paused"]:
                await asyncio.sleep(1)

            pct = int(current * 100 / total)
            task["progress"] = pct

            # ✅ reduce spam (update every 5%)
            if pct - last_update < 5:
                return
            last_update = pct

            bar = "█" * (pct // 10) + "░" * (10 - pct // 10)

            try:
                await progress_msg.edit(
                    f"⬇️ {task['name']}\n[{bar}] {pct}%"
                )
            except:
                pass  # ignore edit errors

        path = await event.message.download_media(
            file=DOWNLOAD_DIR,
            progress_callback=lambda c, t: asyncio.create_task(progress(c, t))
        )

        task["status"] = "done"

        await progress_msg.edit(
            f"✅ Done: {task['name']}\n📁 {path}"
        )

    except Exception as e:
        task["status"] = "failed"
        await progress_msg.edit(f"❌ Failed: {task['name']} → {e}")

# ---------------- QUEUE ----------------
@client.on(events.NewMessage(pattern=r'^/queue'))
async def show_queue(event):
    if not downloads:
        return await event.reply("📦 Queue is empty")

    text = "📦 *Download Queue*\n\n"

    for task_id, task in downloads.items():
        text += (
            f"{task_id}. {task['name']}\n"
            f"Status: {task['status']} ({task['progress']}%)\n"
            f"`/start_{task_id}` `/pause_{task_id}` `/resume_{task_id}` `/remove_{task_id}`\n\n"
        )

    await event.reply(text, parse_mode="markdown")

# ---------------- MAIN ----------------
async def main():
    await client.start()
    print("✅ Downloader running...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
