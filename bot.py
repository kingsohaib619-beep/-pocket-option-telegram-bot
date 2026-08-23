import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from BinaryOptionsToolsV2 import PocketOptionAsync


POCKET_SSID = os.environ["POCKET_OPTION_SSID"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("💰 الرصيد", callback_data="balance"),
            InlineKeyboardButton("📊 الحالة", callback_data="status"),
        ],
        [
            InlineKeyboardButton("💱 اختيار الزوج", callback_data="pair"),
        ],
        [
            InlineKeyboardButton("⏱ مدة الصفقة", callback_data="duration"),
            InlineKeyboardButton("💵 المبلغ", callback_data="amount"),
        ],
        [
            InlineKeyboardButton("🟢 BUY", callback_data="buy"),
            InlineKeyboardButton("🔴 SELL", callback_data="sell"),
        ],
    ]

    await update.message.reply_text(
        "🤖 Pocket Option Demo Bot\n\n"
        "🟢 الحساب: DEMO\n"
        "اختر العملية:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        async with PocketOptionAsync(ssid=POCKET_SSID) as client:
            balance = await client.balance()

        await query.message.reply_text(
            f"💰 Demo Balance\n\n{balance}"
        )

    except Exception as e:
        print(f"Balance error: {type(e).__name__}: {e}")
        await query.message.reply_text(
            f"❌ خطأ: {type(e).__name__}"
        )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "balance":
        await balance(update, context)

    elif query.data == "status":
        await query.message.reply_text(
            "🟢 Bot: Online\n"
            "🟢 Pocket Option: Connected\n"
            "🧪 Account: DEMO"
        )

    elif query.data == "pair":
        keyboard = [
            [
                InlineKeyboardButton("EUR/USD", callback_data="pair_EURUSD"),
                InlineKeyboardButton("GBP/USD", callback_data="pair_GBPUSD"),
            ],
            [
                InlineKeyboardButton("USD/JPY", callback_data="pair_USDJPY"),
                InlineKeyboardButton("AUD/USD", callback_data="pair_AUDUSD"),
            ],
        ]

        await query.message.reply_text(
            "💱 اختر الزوج:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif query.data.startswith("pair_"):
        pair = query.data.replace("pair_", "")
        context.user_data["pair"] = pair

        await query.message.reply_text(
            f"✅ تم اختيار الزوج: {pair}\n\n"
            "⚠️ لم يتم تنفيذ أي صفقة."
        )

    elif query.data == "duration":
        keyboard = [
            [
                InlineKeyboardButton("30 ثانية", callback_data="duration_30"),
                InlineKeyboardButton("1 دقيقة", callback_data="duration_60"),
            ],
            [
                InlineKeyboardButton("5 دقائق", callback_data="duration_300"),
            ],
        ]

        await query.message.reply_text(
            "⏱ اختر المدة:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif query.data.startswith("duration_"):
        duration = int(query.data.replace("duration_", ""))
        context.user_data["duration"] = duration

        await query.message.reply_text(
            f"✅ المدة: {duration} ثانية\n\n"
            "⚠️ لم يتم تنفيذ أي صفقة."
        )

    elif query.data == "amount":
    keyboard = [
        [
            InlineKeyboardButton("$1", callback_data="amount_1"),
            InlineKeyboardButton("$5", callback_data="amount_5"),
        ],
        [
            InlineKeyboardButton("$10", callback_data="amount_10"),
            InlineKeyboardButton("$25", callback_data="amount_25"),
        ],
    ]

    await query.message.reply_text(
        "💵 اختر مبلغ الصفقة:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

elif query.data.startswith("amount_"):
    amount = float(query.data.replace("amount_", ""))
    context.user_data["amount"] = amount

    pair = context.user_data.get("pair", "غير محدد")
    duration = context.user_data.get("duration", "غير محددة")

    await query.message.reply_text(
        f"✅ تم حفظ الإعدادات\n\n"
        f"💱 الزوج: {pair}\n"
        f"⏱ المدة: {duration} ثانية\n"
        f"💵 المبلغ: ${amount}\n\n"
        f"⚠️ لم يتم فتح أي صفقة."
    )

    elif query.data in ("buy", "sell"):
        await query.message.reply_text(
            "⚠️ BUY/SELL غير مفعّلين حاليًا.\n\n"
            "هذه المرحلة للاختبار فقط، ولن يتم فتح أي صفقة."
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
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Telegram bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()
