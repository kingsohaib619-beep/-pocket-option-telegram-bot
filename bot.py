import os
import asyncio

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from BinaryOptionsToolsV2 import PocketOptionAsync


POCKET_SSID = os.environ["POCKET_OPTION_SSID"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Pocket Option Demo Bot\n\n"
        "الحالة: متصل\n"
        "الحساب: DEMO\n\n"
        "استخدم /balance لمعرفة الرصيد."
    )


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        async with PocketOptionAsync(ssid=POCKET_SSID) as client:
            balance = await client.balance()

        await update.message.reply_text(
            f"💰 Demo Balance\n\n"
            f"{balance}"
        )

    except Exception as e:
        await update.message.reply_text(
            f"❌ حدث خطأ:\n{type(e).__name__}"
        )


def main():
    app = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .connect_timeout(60)
        .read_timeout(60)
        .write_timeout(60)
        .pool_timeout(60)
        .get_updates_connect_timeout(60)
        .get_updates_read_timeout(60)
        .get_updates_write_timeout(60)
        .get_updates_pool_timeout(60)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))

    print("Telegram bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()
