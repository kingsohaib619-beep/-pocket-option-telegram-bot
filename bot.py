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
            balance_value = await client.balance()

        await query.message.reply_text(
            f"💰 Demo Balance\n\n{balance_value}"
        )

    except Exception as e:
        print(f"Balance error: {type(e).__name__}: {e}")

        await query.message.reply_text(
            f"❌ تعذر الحصول على الرصيد.\n"
            f"Error: {type(e).__name__}"
        )


async def show_pair_menu(query):
    keyboard = [
        [
            InlineKeyboardButton(
                "EUR/USD",
                callback_data="pair_EURUSD"
            ),
            InlineKeyboardButton(
                "GBP/USD",
                callback_data="pair_GBPUSD"
            ),
        ],
        [
            InlineKeyboardButton(
                "USD/JPY",
                callback_data="pair_USDJPY"
            ),
            InlineKeyboardButton(
                "AUD/USD",
                callback_data="pair_AUDUSD"
            ),
        ],
    ]

    await query.message.reply_text(
        "💱 اختر الزوج:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def show_duration_menu(query):
    keyboard = [
        [
            InlineKeyboardButton(
                "30 ثانية",
                callback_data="duration_30"
            ),
            InlineKeyboardButton(
                "1 دقيقة",
                callback_data="duration_60"
            ),
        ],
        [
            InlineKeyboardButton(
                "5 دقائق",
                callback_data="duration_300"
            ),
        ],
    ]

    await query.message.reply_text(
        "⏱ اختر المدة:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def show_amount_menu(query):
    keyboard = [
        [
            InlineKeyboardButton(
                "$1",
                callback_data="amount_1"
            ),
            InlineKeyboardButton(
                "$5",
                callback_data="amount_5"
            ),
        ],
        [
            InlineKeyboardButton(
                "$10",
                callback_data="amount_10"
            ),
            InlineKeyboardButton(
                "$25",
                callback_data="amount_25"
            ),
        ],
    ]

    await query.message.reply_text(
        "💵 اختر مبلغ الصفقة:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def show_trade_confirmation(query, context):
    pair = context.user_data.get("pair")
    duration = context.user_data.get("duration")
    amount = context.user_data.get("amount")
    direction = context.user_data.get("direction")

    if not pair or not duration or not amount or not direction:
        await query.message.reply_text(
            "⚠️ أكمل إعداد الصفقة أولًا:\n\n"
            "1️⃣ اختر الزوج\n"
            "2️⃣ اختر المدة\n"
            "3️⃣ اختر المبلغ\n"
            "4️⃣ اختر BUY أو SELL"
        )
        return

    direction_text = (
        "🟢 BUY"
        if direction == "buy"
        else "🔴 SELL"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ تأكيد",
                callback_data="confirm_trade"
            ),
            InlineKeyboardButton(
                "❌ إلغاء",
                callback_data="cancel_trade"
            ),
        ]
    ]

    await query.message.reply_text(
        "📋 تأكيد الصفقة\n\n"
        f"💱 الزوج: {pair}\n"
        f"📈 الاتجاه: {direction_text}\n"
        f"💵 المبلغ: ${amount}\n"
        f"⏱ المدة: {duration} ثانية\n\n"
        "🧪 الحساب: DEMO\n\n"
        "⚠️ هذه المرحلة لا تنفذ الصفقة.\n"
        "زر التأكيد سيعرض رسالة اختبار فقط.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "balance":
        await balance(update, context)

    elif data == "status":
        await query.message.reply_text(
            "🟢 Telegram Bot: Online\n"
            "🟢 Pocket Option: Connected\n"
            "🧪 Account: DEMO"
        )

    elif data == "pair":
        await show_pair_menu(query)

    elif data.startswith("pair_"):
        pair = data.replace("pair_", "")
        context.user_data["pair"] = pair

        await query.message.reply_text(
            f"✅ تم اختيار الزوج: {pair}"
        )

    elif data == "duration":
        await show_duration_menu(query)

    elif data.startswith("duration_"):
        duration = int(data.replace("duration_", ""))
        context.user_data["duration"] = duration

        await query.message.reply_text(
            f"✅ تم اختيار المدة: {duration} ثانية"
        )

    elif data == "amount":
        await show_amount_menu(query)

    elif data.startswith("amount_"):
        amount = float(data.replace("amount_", ""))
        context.user_data["amount"] = amount

        await query.message.reply_text(
            f"✅ تم اختيار المبلغ: ${amount}"
        )

    elif data in ("buy", "sell"):
        context.user_data["direction"] = data

        await show_trade_confirmation(
            query,
            context
        )

    elif data == "confirm_trade":
        await query.message.reply_text(
            "🧪 اختبار التأكيد ناجح.\n\n"
            "تم تسجيل إعداد الصفقة فقط:\n\n"
            f"💱 {context.user_data.get('pair', 'غير محدد')}\n"
            f"📈 {context.user_data.get('direction', 'غير محدد').upper()}\n"
            f"💵 ${context.user_data.get('amount', 'غير محدد')}\n"
            f"⏱ {context.user_data.get('duration', 'غير محدد')} ثانية\n\n"
            "🚫 لم يتم فتح أي صفقة."
        )

    elif data == "cancel_trade":
        context.user_data.pop("direction", None)

        await query.message.reply_text(
            "❌ تم إلغاء الصفقة.\n\n"
            "لم يتم تنفيذ أي أمر."
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

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CallbackQueryHandler(button_handler)
    )

    print("Telegram bot started...")

    app.run_polling()


if __name__ == "__main__":
    main()
