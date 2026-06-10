#!/usr/bin/env python3

import sys
import os
import re
import asyncio

from telethon import TelegramClient

API_ID = 30299030
API_HASH = os.getenv("TELEGRAM_API_HASH", "")

SESSION_PATH = os.path.expanduser(
    "~/xelios-setup/services/telegram-session/session"
)


# ✅ Parse Telegram link
def parse_tg_link(link):
    match = re.search(r"t\.me/([^/]+)/(\d+)", link)
    if not match:
        return None, None
    return match.group(1), int(match.group(2))


async def main(link):
    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
    await client.connect()

    if not await client.is_user_authorized():
        print("NOT_LOGGED_IN", file=sys.stderr)
        return 1

    chat, msg_id = parse_tg_link(link)

    if not chat:
        print("INVALID_LINK", file=sys.stderr)
        return 1

    try:
        message = await client.get_messages(chat, ids=msg_id)

        if not message or not message.media:
            print("NO_MEDIA", file=sys.stderr)
            return 1

        file_path = await message.download_media()

        print(file_path)  # ✅ return to bot

        return 0

    except Exception as e:
        print(str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("NO_LINK_PROVIDED", file=sys.stderr)
        sys.exit(1)

    link = sys.argv[1]

    exit_code = asyncio.run(main(link))
    sys.exit(exit_code)
