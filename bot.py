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


# =========================
# Main menu
# =========================

def main_keyboard():
    return InlineKeyboardMarkup([
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
    ])


async def show_main_menu(query, context):
    pair = context.user_data.get("pair", "غير محدد")
    duration = context.user_data.get("duration", "غير محددة")
    amount = context.user_data.get("amount", "غير محدد")
    direction = context.user_data.get("direction", "غير محدد")

    if direction == "buy":
        direction_text = "🟢 BUY"
    elif direction == "sell":
        direction_text = "🔴 SELL"
    else:
        direction_text = "غير محدد"

    text = (
        "🤖 Pocket Option Demo Bot\n\n"
        "🧪 الحساب: DEMO\n\n"
        "📋 إعدادات الصفقة الحالية:\n"
        f"💱 الزوج: {pair}\n"
        f"⏱ المدة: {duration} ثانية\n"
        f"💵 المبلغ: ${amount}\n"
        f"📈 الاتجاه: {direction_text}\n\n"
        "اختر العملية:"
    )

    await query.edit_message_text(
        text,
        reply_markup=main_keyboard()
    )


# =========================
# Start
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    await update.message.reply_text(
        "🤖 Pocket Option Demo Bot\n\n"
        "🧪 الحساب: DEMO\n\n"
        "اختر العملية:",
        reply_markup=main_keyboard(),
    )


# =========================
# Balance
# =========================

async def show_balance(query):
    try:
        async with PocketOptionAsync(ssid=POCKET_SSID) as client:
            balance = await client.balance()

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔄 تحديث",
                    callback_data="balance"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ رجوع",
                    callback_data="home"
                )
            ],
        ]

        await query.edit_message_text(
            f"💰 Demo Balance\n\n"
            f"{balance}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        print(f"Balance error: {type(e).__name__}: {e}")

        await query.edit_message_text(
            f"❌ تعذر الحصول على الرصيد.\n\n"
            f"Error: {type(e).__name__}",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "⬅️ رجوع",
                        callback_data="home"
                    )
                ]
            ])
        )


# =========================
# Status
# =========================

async def show_status(query):
    keyboard = [
        [
            InlineKeyboardButton(
                "⬅️ رجوع",
                callback_data="home"
            )
        ]
    ]

    await query.edit_message_text(
        "📊 حالة البوت\n\n"
        "🟢 Telegram Bot: Online\n"
        "🟢 Pocket Option: Connected\n"
        "🧪 Account: DEMO",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# Pair menu
# =========================

async def show_pair_menu(query, context):

    current_pair = context.user_data.get(
        "pair",
        "غير محدد"
    )

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
        [
            InlineKeyboardButton(
                "⬅️ رجوع",
                callback_data="home"
            )
        ],
    ]

    await query.edit_message_text(
        f"💱 اختيار الزوج\n\n"
        f"الزوج الحالي: {current_pair}\n\n"
        "اختر الزوج:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# Duration menu
# =========================

async def show_duration_menu(query, context):

    current_duration = context.user_data.get(
        "duration",
        "غير محددة"
    )

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
        [
            InlineKeyboardButton(
                "⬅️ رجوع",
                callback_data="home"
            )
        ],
    ]

    await query.edit_message_text(
        f"⏱ اختيار المدة\n\n"
        f"المدة الحالية: {current_duration} ثانية\n\n"
        "اختر المدة:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# Amount menu
# =========================

async def show_amount_menu(query, context):

    current_amount = context.user_data.get(
        "amount",
        "غير محدد"
    )

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
        [
            InlineKeyboardButton(
                "⬅️ رجوع",
                callback_data="home"
            )
        ],
    ]

    await query.edit_message_text(
        f"💵 اختيار المبلغ\n\n"
        f"المبلغ الحالي: ${current_amount}\n\n"
        "اختر المبلغ:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# Trade confirmation
# =========================

async def show_trade_confirmation(query, context):

    pair = context.user_data.get("pair")
    duration = context.user_data.get("duration")
    amount = context.user_data.get("amount")
    direction = context.user_data.get("direction")

    if not pair or not duration or not amount:

        keyboard = [
            [
                InlineKeyboardButton(
                    "💱 اختيار الزوج",
                    callback_data="pair"
                )
            ],
            [
                InlineKeyboardButton(
                    "⏱ اختيار المدة",
                    callback_data="duration"
                )
            ],
            [
                InlineKeyboardButton(
                    "💵 اختيار المبلغ",
                    callback_data="amount"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ رجوع",
                    callback_data="home"
                )
            ],
        ]

        await query.edit_message_text(
            "⚠️ إعداد الصفقة غير مكتمل.\n\n"
            "يجب اختيار:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return

    if direction == "buy":
        direction_text = "🟢 BUY"
    else:
        direction_text = "🔴 SELL"

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
        ],
        [
            InlineKeyboardButton(
                "⬅️ رجوع",
                callback_data="home"
            )
        ],
    ]

    await query.edit_message_text(
        "📋 تأكيد الصفقة\n\n"
        f"💱 الزوج: {pair}\n"
        f"📈 الاتجاه: {direction_text}\n"
        f"💵 المبلغ: ${amount}\n"
        f"⏱ المدة: {duration} ثانية\n\n"
        "🧪 الحساب: DEMO\n\n"
        "⚠️ هذه مرحلة اختبار.\n"
        "لن يتم فتح أي صفقة.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# Button handler
# =========================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    data = query.data

    # Home
    if data == "home":
        await show_main_menu(query, context)

    # Balance
    elif data == "balance":
        await show_balance(query)

    # Status
    elif data == "status":
        await show_status(query)

    # Pair menu
    elif data == "pair":
        await show_pair_menu(query, context)

    # Pair selected
    elif data.startswith("pair_"):

        pair = data.replace(
            "pair_",
            ""
        )

        context.user_data["pair"] = pair

        await show_main_menu(
            query,
            context
        )

    # Duration menu
    elif data == "duration":
        await show_duration_menu(
            query,
            context
        )

    # Duration selected
    elif data.startswith("duration_"):

        duration = int(
            data.replace(
                "duration_",
                ""
            )
        )

        context.user_data["duration"] = duration

        await show_main_menu(
            query,
            context
        )

    # Amount menu
    elif data == "amount":
        await show_amount_menu(
            query,
            context
        )

    # Amount selected
    elif data.startswith("amount_"):

        amount = float(
            data.replace(
                "amount_",
                ""
            )
        )

        context.user_data["amount"] = amount

        await show_main_menu(
            query,
            context
        )

    # BUY / SELL
    elif data == "buy":

        context.user_data["direction"] = "buy"

        await show_trade_confirmation(
            query,
            context
        )

    elif data == "sell":

        context.user_data["direction"] = "sell"

        await show_trade_confirmation(
            query,
            context
        )

    # Confirm
    elif data == "confirm_trade":

        pair = context.user_data.get(
            "pair",
            "غير محدد"
        )

        direction = context.user_data.get(
            "direction",
            "غير محدد"
        )

        amount = context.user_data.get(
            "amount",
            "غير محدد"
        )

        duration = context.user_data.get(
            "duration",
            "غير محددة"
        )

        direction_text = (
            "🟢 BUY"
            if direction == "buy"
            else "🔴 SELL"
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "⬅️ القائمة الرئيسية",
                    callback_data="home"
                )
            ]
        ]

        await query.edit_message_text(
            "🧪 اختبار التأكيد ناجح\n\n"
            f"💱 الزوج: {pair}\n"
            f"📈 الاتجاه: {direction_text}\n"
            f"💵 المبلغ: ${amount}\n"
            f"⏱ المدة: {duration} ثانية\n\n"
            "🚫 لم يتم فتح أي صفقة.",
            reply_markup=InlineKeyboardMarkup(
                keyboard
            )
        )

    # Cancel
    elif data == "cancel_trade":

        context.user_data.pop(
            "direction",
            None
        )

        await show_main_menu(
            query,
            context
        )


# =========================
# Main
# =========================

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
        .build()
    )

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            button_handler
        )
    )

    print(
        "Telegram bot started..."
    )

    app.run_polling()


if __name__ == "__main__":
    main()
