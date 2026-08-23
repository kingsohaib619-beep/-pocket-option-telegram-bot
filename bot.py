import os
import asyncio

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


# =========================================================
# Main keyboard
# =========================================================

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


# =========================================================
# Start
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    await update.message.reply_text(
        "🤖 Pocket Option Demo Bot\n\n"
        "🧪 الحساب: DEMO\n\n"
        "اختر العملية:",
        reply_markup=main_keyboard(),
    )


# =========================================================
# Main menu
# =========================================================

async def show_main_menu(query, context):

    pair = context.user_data.get("pair", "غير محدد")
    duration = context.user_data.get("duration", "غير محددة")
    amount = context.user_data.get("amount", "غير محدد")
    direction = context.user_data.get("direction")

    if direction == "buy":
        direction_text = "🟢 BUY"
    elif direction == "sell":
        direction_text = "🔴 SELL"
    else:
        direction_text = "غير محدد"

    await query.edit_message_text(
        "🤖 Pocket Option Demo Bot\n\n"
        "🧪 الحساب: DEMO\n\n"
        "📋 إعدادات الصفقة:\n"
        f"💱 الزوج: {pair}\n"
        f"⏱ المدة: {duration} ثانية\n"
        f"💵 المبلغ: ${amount}\n"
        f"📈 الاتجاه: {direction_text}\n\n"
        "اختر العملية:",
        reply_markup=main_keyboard(),
    )


# =========================================================
# Balance
# =========================================================

async def show_balance(query):

    try:

        async with PocketOptionAsync(
            ssid=POCKET_SSID
        ) as client:

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

        print(
            f"Balance error: "
            f"{type(e).__name__}: {e}"
        )

        await query.edit_message_text(
            "❌ تعذر الحصول على الرصيد.\n\n"
            f"الخطأ: {type(e).__name__}",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "⬅️ رجوع",
                        callback_data="home"
                    )
                ]
            ])
        )


# =========================================================
# Status
# =========================================================

async def show_status(query):

    try:

        async with PocketOptionAsync(
            ssid=POCKET_SSID
        ) as client:

            connected = client.is_connected()
            demo = client.is_demo()
            ssid_valid = client.is_ssid_valid()

        await query.edit_message_text(
            "📊 حالة الاتصال\n\n"
            f"🔌 الاتصال: "
            f"{'🟢 متصل' if connected else '🔴 غير متصل'}\n"
            f"🧪 الحساب Demo: "
            f"{'🟢 نعم' if demo else '🔴 لا'}\n"
            f"🔐 SSID: "
            f"{'🟢 صالح' if ssid_valid else '🔴 غير صالح'}",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "⬅️ رجوع",
                        callback_data="home"
                    )
                ]
            ])
        )

    except Exception as e:

        await query.edit_message_text(
            f"❌ خطأ في الاتصال:\n"
            f"{type(e).__name__}",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "⬅️ رجوع",
                        callback_data="home"
                    )
                ]
            ])
        )


# =========================================================
# Pair menu
# =========================================================

async def show_pair_menu(query, context):

    current = context.user_data.get(
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
        f"الحالي: {current}\n\n"
        "اختر الزوج:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# Duration menu
# =========================================================

async def show_duration_menu(query, context):

    current = context.user_data.get(
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
        f"الحالية: {current} ثانية\n\n"
        "اختر المدة:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# Amount menu
# =========================================================

async def show_amount_menu(query, context):

    current = context.user_data.get(
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
        f"الحالي: ${current}\n\n"
        "اختر المبلغ:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# Confirmation
# =========================================================

async def show_trade_confirmation(query, context):

    pair = context.user_data.get("pair")
    duration = context.user_data.get("duration")
    amount = context.user_data.get("amount")
    direction = context.user_data.get("direction")

    missing = []

    if not pair:
        missing.append("💱 الزوج")

    if not duration:
        missing.append("⏱ المدة")

    if not amount:
        missing.append("💵 المبلغ")

    if not direction:
        missing.append("📈 الاتجاه")

    if missing:

        keyboard = [
            [
                InlineKeyboardButton(
                    "💱 الزوج",
                    callback_data="pair"
                ),
                InlineKeyboardButton(
                    "⏱ المدة",
                    callback_data="duration"
                ),
            ],
            [
                InlineKeyboardButton(
                    "💵 المبلغ",
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
            "المطلوب:\n" +
            "\n".join(
                f"• {item}"
                for item in missing
            ),
            reply_markup=InlineKeyboardMarkup(keyboard)
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
                "✅ تأكيد الصفقة",
                callback_data="confirm_trade"
            ),
            InlineKeyboardButton(
                "❌ إلغاء",
                callback_data="cancel_trade"
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ تعديل",
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
        "⚠️ عند الضغط على تأكيد سيتم إرسال "
        "الأمر إلى حساب Demo.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# Execute trade
# =========================================================

async def execute_trade(query, context):

    pair = context.user_data.get("pair")
    amount = context.user_data.get("amount")
    duration = context.user_data.get("duration")
    direction = context.user_data.get("direction")

    if not pair or not amount or not duration or not direction:

        await query.edit_message_text(
            "❌ معلومات الصفقة غير مكتملة.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "⬅️ رجوع",
                        callback_data="home"
                    )
                ]
            ])
        )

        return

    await query.edit_message_text(
        "⏳ جارٍ تنفيذ الصفقة...\n\n"
        f"💱 {pair}\n"
        f"💵 ${amount}\n"
        f"⏱ {duration} ثانية"
    )

    try:

        async with PocketOptionAsync(
            ssid=POCKET_SSID
        ) as client:

            # تأكد من الاتصال
            if not client.is_connected():
                await client.connect()

            # تنفيذ BUY
            if direction == "buy":

                trade_id, trade_data = await client.buy(
                    pair,
                    float(amount),
                    int(duration),
                    check_win=False
                )

            # تنفيذ SELL
            else:

                trade_id, trade_data = await client.sell(
                    pair,
                    float(amount),
                    int(duration),
                    check_win=False
                )

            print(
                "TRADE ID:",
                trade_id
            )

            print(
                "TRADE DATA:",
                trade_data
            )

            direction_text = (
                "🟢 BUY"
                if direction == "buy"
                else "🔴 SELL"
            )

            await query.edit_message_text(
                "✅ تم فتح الصفقة\n\n"
                f"🆔 Trade ID:\n"
                f"{trade_id}\n\n"
                f"💱 الزوج: {pair}\n"
                f"📈 الاتجاه: {direction_text}\n"
                f"💵 المبلغ: ${amount}\n"
                f"⏱ المدة: {duration} ثانية\n\n"
                "⏳ ننتظر النتيجة..."
            )

            # انتظار مدة الصفقة قبل طلب النتيجة
            await asyncio.sleep(
                int(duration)
            )

            # فحص النتيجة
            try:

                result = await client.check_win(
                    trade_id
                )

                print(
                    "WIN RESULT:",
                    result
                )

                result_text = str(result)

                if "win" in result_text.lower():
                    result_emoji = "🟢"
                elif "loss" in result_text.lower():
                    result_emoji = "🔴"
                else:
                    result_emoji = "ℹ️"

                await query.message.reply_text(
                    f"{result_emoji} نتيجة الصفقة\n\n"
                    f"🆔 {trade_id}\n"
                    f"💱 {pair}\n"
                    f"📈 {direction_text}\n"
                    f"💵 ${amount}\n\n"
                    f"📊 النتيجة:\n"
                    f"{result}"
                )

            except Exception as result_error:

                print(
                    "CHECK WIN ERROR:",
                    type(result_error).__name__,
                    result_error
                )

                await query.message.reply_text(
                    "⚠️ تم فتح الصفقة، "
                    "لكن تعذر قراءة النتيجة تلقائيًا.\n\n"
                    f"🆔 Trade ID:\n"
                    f"{trade_id}\n\n"
                    f"الخطأ: "
                    f"{type(result_error).__name__}"
                )

    except Exception as e:

        print(
            "TRADE ERROR:",
            type(e).__name__,
            e
        )

        await query.message.reply_text(
            "❌ فشل تنفيذ الصفقة.\n\n"
            f"الخطأ: {type(e).__name__}\n\n"
            "لم يتم اعتبار العملية ناجحة."
        )


# =========================================================
# Button handler
# =========================================================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    data = query.data

    # -------------------------
    # Home
    # -------------------------

    if data == "home":

        await show_main_menu(
            query,
            context
        )

    # -------------------------
    # Balance
    # -------------------------

    elif data == "balance":

        await show_balance(query)

    # -------------------------
    # Status
    # -------------------------

    elif data == "status":

        await show_status(query)

    # -------------------------
    # Pair
    # -------------------------

    elif data == "pair":

        await show_pair_menu(
            query,
            context
        )

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

    # -------------------------
    # Duration
    # -------------------------

    elif data == "duration":

        await show_duration_menu(
            query,
            context
        )

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

    # -------------------------
    # Amount
    # -------------------------

    elif data == "amount":

        await show_amount_menu(
            query,
            context
        )

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

    # -------------------------
    # BUY
    # -------------------------

    elif data == "buy":

        context.user_data["direction"] = "buy"

        await show_trade_confirmation(
            query,
            context
        )

    # -------------------------
    # SELL
    # -------------------------

    elif data == "sell":

        context.user_data["direction"] = "sell"

        await show_trade_confirmation(
            query,
            context
        )

    # -------------------------
    # Confirm
    # -------------------------

    elif data == "confirm_trade":

        await execute_trade(
            query,
            context
        )

    # -------------------------
    # Cancel
    # -------------------------

    elif data == "cancel_trade":

        context.user_data.pop(
            "direction",
            None
        )

        await show_main_menu(
            query,
            context
        )


# =========================================================
# Main
# =========================================================

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
