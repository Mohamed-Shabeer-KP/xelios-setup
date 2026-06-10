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

DOWNLOAD_DIR = os.path.expanduser("~/xelios-downloads")

logging.basicConfig(level=logging.INFO)

client = TelegramClient(SESSION_PATH, API_ID, API_HASH)


# ✅ Ensure download directory exists
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# ✅ EVENT: new message
@client.on(events.NewMessage)
async def handler(event):

    message = event.message

    # ✅ Ignore if no media
    if not message.media:
        return

    try:
        logging.info("⬇️ Downloading media...")

        file_path = await message.download_media(file=DOWNLOAD_DIR)

        logging.info(f"✅ Downloaded: {file_path}")

    except Exception as e:
        logging.error(f"❌ Failed: {e}")


async def main():
    await client.start()

    if not await client.is_user_authorized():
        print("❌ Not logged in. Run bot login first.")
        return

    print("✅ Downloader service running...")

    # ✅ Run forever (no polling loop needed)
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
