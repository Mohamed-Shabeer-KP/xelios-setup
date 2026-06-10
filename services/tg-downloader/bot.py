#!/usr/bin/env python3

import os
import asyncio
import logging

from telethon import TelegramClient, events, Button

# ---------------- CONFIG ----------------
API_ID = 30299030
API_HASH = os.getenv("TELEGRAM_API_HASH")
TARGET_GROUP_NAME = "Downloader"

SESSION_PATH = os.path.expanduser(
    "~/xelios-setup/services/tg-downloader/session"
)

DOWNLOAD_DIR = os.path.expanduser("~/xelios-downloads/storage/shared/download")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO)

client = TelegramClient(SESSION_PATH, API_ID, API_HASH)

# ---------------- STATE ----------------
downloads = {}
counter = 0
lock = asyncio.Lock()

# ---------------- START MESSAGE ----------------
@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    await event.reply(
        "📥 *Downloader Ready*",
        buttons=[
            [Button.inline("📦 Queue", b"queue")]
        ],
        parse_mode="Markdown"
    )

# ---------------- NEW MEDIA ----------------
@client.on(events.NewMessage)
async def downloader(event):
    try:
        # ✅ Ensure it's a group
        if not event.is_group:
            return

        # ✅ Get group title safely
        chat = await event.get_chat()

        if not hasattr(chat, "title"):
            return

        # ✅ Filter only your group
        if chat.title != TARGET_GROUP_NAME:
            return

        # ✅ Only process messages with media
        if not event.message.media:
            return

        # ✅ DEBUG (optional — remove later)
        print(f"✅ Download triggered from group: {chat.title}")

        # ✅ Continue with your existing logic below
        await handle_download(event)

    except Exception as e:
        print("❌ Handler error:", e)

async def handle_download(event):
    global counter

    async with lock:
        counter += 1
        task_id = counter

    file_name = event.file.name or f"file_{task_id}"

    msg = await event.reply(
        f"📥 *Queued:* {file_name}",
        buttons=[[Button.inline("▶ Start", f"start:{task_id}".encode())]],
        parse_mode="Markdown"
    )

    downloads[task_id] = {
        "event": event,
        "name": file_name,
        "status": "queued",
        "paused": False,
        "cancelled": False,
        "msg": msg,
        "progress": 0
    }

# ---------------- BUTTON HANDLER ----------------
@client.on(events.CallbackQuery)
async def buttons(event):
    data = event.data.decode()

    if data == "queue":
        await show_queue(event)
        return

    if ":" not in data:
        return

    cmd, task_id = data.split(":")
    task_id = int(task_id)

    task = downloads.get(task_id)
    if not task:
        return await event.answer("❌ Not found", alert=True)

    if cmd == "start":
        if task["status"] == "queued":
            task["status"] = "downloading"
            asyncio.create_task(process_download(task_id))
            await event.answer("▶ Started")

    elif cmd == "pause":
        task["paused"] = True
        await event.answer("⏸ Paused")

    elif cmd == "resume":
        task["paused"] = False
        await event.answer("▶ Resumed")

    elif cmd == "delete":
        task["cancelled"] = True
        task["status"] = "cancelled"
        await event.answer("❌ Removed")

# ---------------- DOWNLOAD LOGIC ----------------
async def process_download(task_id):
    task = downloads[task_id]
    event = task["event"]
    msg = task["msg"]

    try:
        async def progress(current, total):
            if task["cancelled"]:
                raise Exception("Cancelled")

            while task["paused"]:
                await asyncio.sleep(1)

            pct = int(current * 100 / total)
            task["progress"] = pct

            bar = "█" * (pct // 10) + "░" * (10 - pct // 10)

            await msg.edit(
                f"⬇️ {task['name']}\n[{bar}] {pct}%",
                buttons=[[
                    Button.inline("⏸ Pause", f"pause:{task_id}".encode())
                    Button.inline("❌ Remove", f"delete:{task_id}".encode())
                ]]
            )

        path = await event.message.download_media(
            file=DOWNLOAD_DIR,
            progress_callback=lambda c, t: asyncio.create_task(progress(c, t))
        )

        task["status"] = "done"

        await msg.edit(f"✅ *Done:* {path}", parse_mode="Markdown")

    except Exception as e:
        task["status"] = "failed"
        await msg.edit(f"❌ Failed: {e}")

# ---------------- QUEUE UI ----------------
async def show_queue(event):
    if not downloads:
        return await event.edit("📦 Queue is empty")

    text = "📦 *Download Queue*\n\n"
    buttons = []

    for task_id, task in downloads.items():
        text += f"{task_id}. {task['name']} ({task['status']}, {task.get('progress',0)}%)\n"

        row = []

        if task["status"] == "downloading":
            if task["paused"]:
                row.append(Button.inline("▶", f"resume:{task_id}".encode()))
            else:
                row.append(Button.inline("⏸", f"pause:{task_id}".encode()))

        row.append(Button.inline("❌", f"delete:{task_id}"))

        buttons.append(row)

    buttons.append([Button.inline("📦 Queue", "queue".encode())])

    await event.edit(text, buttons=buttons, parse_mode="Markdown")

# ---------------- MAIN ----------------
async def main():
    await client.start()

    print("✅ Downloader running...")

    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
