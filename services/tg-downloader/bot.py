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
    "~/xelios-setup/services/tg-downloader/session"
)

DOWNLOAD_DIR = os.path.expanduser("~/xelios-downloads")
PAUSE_FILE = "/tmp/tg_downloader_pause"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO)

client = TelegramClient(SESSION_PATH, API_ID, API_HASH)

# ---------------- STATE ----------------
queue = asyncio.Queue()

login_state = {
    "step": None,
    "phone": None,
    "phone_code_hash": None
}

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

    elif cmd == "status":
        async def check():
            await client.connect()
            if await client.is_user_authorized():
                print("LOGGED_IN")
            else:
                print("NOT_LOGGED_IN")
            await client.disconnect()

        asyncio.run(check())
        sys.exit(0)

# ---------------- PROGRESS BAR ----------------
def bar(p):
    return "█" * (p // 10) + "░" * (10 - p // 10)

async def progress_cb(msg, current, total):
    if total == 0:
        return

    pct = int(current * 100 / total)

    try:
        await msg.edit(
            f"⬇️ Downloading...\n[{bar(pct)}] {pct}%"
        )
    except:
        pass

# ---------------- WORKER ----------------
async def worker():
    while True:
        event = await queue.get()

        try:
            ui = await event.reply("⬇️ Starting download...")

            # pause support
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

# ---------------- LOGIN HANDLER ----------------
@client.on(events.NewMessage(incoming=True))
async def login_handler(event):

    # only private chat (Saved Messages)
    if not event.is_private:
        return

    if await client.is_user_authorized():
        return

    text = (event.raw_text or "").strip()

    # STEP 1
    if login_state["step"] is None:
        login_state["step"] = "phone"

        await event.reply(
            "🔐 *Login Required*\n\nSend your phone number:\n`+1234567890`",
            parse_mode="Markdown"
        )
        return

    # STEP 2
    elif login_state["step"] == "phone":
        try:
            result = await client.send_code_request(text)

            login_state["phone"] = text
            login_state["phone_code_hash"] = result.phone_code_hash
            login_state["step"] = "code"

            await event.reply("📩 OTP sent. Send the code.")
        except Exception as e:
            await event.reply(f"❌ Failed to send OTP:\n{e}")

        return

    # STEP 3
    elif login_state["step"] == "code":
        try:
            await client.sign_in(
                phone=login_state["phone"],
                code=text,
                phone_code_hash=login_state["phone_code_hash"]
            )

            login_state["step"] = None

            await event.reply(
                "✅ *Login successful!*\n\nSend media to download.",
                parse_mode="Markdown"
            )

        except Exception as e:
            await event.reply(f"❌ Login failed:\n{e}")

        return

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

    await client.connect()

    if not await client.is_user_authorized():
        print("🔐 Waiting for login via Telegram...")
    else:
        print("✅ Already logged in")

    print("✅ Downloader running...")

    worker_task = asyncio.create_task(worker())

    try:
        await client.run_until_disconnected()
    finally:
        worker_task.cancel()
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
