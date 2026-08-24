import os
import asyncio

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from BinaryOptionsToolsV2 import PocketOptionAsync


# =========================================================
# Environment
# =========================================================

POCKET_SSID = os.environ["POCKET_OPTION_SSID"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]


# =========================================================
# Asset cache
# =========================================================

ASSET_CACHE = {}
ASSET_CACHE_TIME = 0

ASSET_CACHE_TTL = 300
ASSETS_PER_PAGE = 12


# =========================================================
# Default durations
# =========================================================

DEFAULT_DURATIONS = [
    30,
    60,
    120,
    180,
    300,
    600,
    900,
    1800,
    2700,
    3600,
    7200,
    10800,
    14400,
]


# =========================================================
# Duration text
# =========================================================

def duration_text(seconds):

    seconds = int(seconds)

    if seconds < 60:
        return f"{seconds} ثانية"

    if seconds == 60:
        return "1 دقيقة"

    if seconds < 3600:

        minutes = seconds // 60

        if minutes == 1:
            return "1 دقيقة"

        if minutes == 2:
            return "2 دقيقة"

        if minutes == 3:
            return "3 دقائق"

        if minutes == 10:
            return "10 دقائق"

        if minutes == 15:
            return "15 دقيقة"

        if minutes == 30:
            return "30 دقيقة"

        if minutes == 45:
            return "45 دقيقة"

        return f"{minutes} دقيقة"

    hours = seconds // 3600

    if hours == 1:
        return "1 ساعة"

    if hours == 2:
        return "2 ساعة"

    if hours == 3:
        return "3 ساعات"

    return f"{hours} ساعة"


# =========================================================
# Format saved settings
# =========================================================

def get_saved_settings(context):

    pair = context.user_data.get(
        "pair"
    )

    duration = context.user_data.get(
        "duration"
    )

    amount = context.user_data.get(
        "amount"
    )

    direction = context.user_data.get(
        "direction"
    )

    pair_text = (
        pair
        if pair
        else "غير محدد"
    )

    duration_value = (
        duration_text(duration)
        if duration is not None
        else "غير محددة"
    )

    amount_text = (
        f"${amount}"
        if amount is not None
        else "غير محدد"
    )

    if direction == "buy":

        direction_text = "🟢 BUY"

    elif direction == "sell":

        direction_text = "🔴 SELL"

    else:

        direction_text = "غير محدد"

    return (
        pair_text,
        duration_value,
        amount_text,
        direction_text,
    )


# =========================================================
# Main keyboard
# =========================================================

def main_keyboard():

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "💰 الرصيد",
                callback_data="balance"
            ),

            InlineKeyboardButton(
                "📊 الحالة",
                callback_data="status"
            ),
        ],

        [
            InlineKeyboardButton(
                "💱 اختيار الأصل",
                callback_data="pair"
            ),
        ],

        [
            InlineKeyboardButton(
                "⏱ مدة الصفقة",
                callback_data="duration"
            ),

            InlineKeyboardButton(
                "💵 المبلغ",
                callback_data="amount"
            ),
        ],

        [
            InlineKeyboardButton(
                "🟢 BUY",
                callback_data="buy"
            ),

            InlineKeyboardButton(
                "🔴 SELL",
                callback_data="sell"
            ),
        ],

    ])


# =========================================================
# Load active assets
#
# BinaryOptionsToolsV2 0.2.13
# uses active_assets()
#
# NOT get_all_assets()
# =========================================================

async def load_active_assets():

    global ASSET_CACHE
    global ASSET_CACHE_TIME

    now = asyncio.get_running_loop().time()

    # -----------------------------------------------------
    # Cache
    # -----------------------------------------------------

    if (
        ASSET_CACHE
        and
        (now - ASSET_CACHE_TIME)
        < ASSET_CACHE_TTL
    ):

        return ASSET_CACHE

    try:

        print("=" * 60)
        print("LOADING ACTIVE ASSETS")
        print("=" * 60)

        async with PocketOptionAsync(
            ssid=POCKET_SSID
        ) as client:

            if not client.is_connected():

                await client.connect()

            await client.wait_for_assets()

            assets = await client.active_assets()

        print(
            "ACTIVE ASSETS TYPE:",
            type(assets)
        )

        print(
            "ACTIVE ASSETS COUNT:",
            len(assets)
        )

        active_assets = {}

        # =================================================
        # Parse assets
        # =================================================

        for asset in assets:

            if not isinstance(
                asset,
                dict
            ):
                continue

            symbol = asset.get(
                "symbol"
            )

            if not symbol:
                continue

            # -------------------------------------------------
            # Active
            # -------------------------------------------------

            is_active = asset.get(
                "is_active",
                True
            )

            if is_active is not True:
                continue

            # -------------------------------------------------
            # Allowed candles
            # -------------------------------------------------

            allowed_candles = []

            candles = asset.get(
                "allowed_candles",
                []
            )

            if isinstance(
                candles,
                list
            ):

                for candle in candles:

                    if isinstance(
                        candle,
                        dict
                    ):

                        time_value = candle.get(
                            "time"
                        )

                        if time_value is not None:

                            try:

                                allowed_candles.append(
                                    int(time_value)
                                )

                            except (
                                TypeError,
                                ValueError
                            ):

                                pass

                    elif isinstance(
                        candle,
                        (int, float)
                    ):

                        try:

                            allowed_candles.append(
                                int(candle)
                            )

                        except (
                            TypeError,
                            ValueError
                        ):

                            pass

            allowed_candles = sorted(
                set(
                    allowed_candles
                )
            )

            # -------------------------------------------------
            # Normalize
            # -------------------------------------------------

            active_assets[symbol] = {

                "id": asset.get(
                    "id"
                ),

                "name": asset.get(
                    "name",
                    symbol
                ),

                "symbol": symbol,

                "is_otc": bool(
                    asset.get(
                        "is_otc",
                        False
                    )
                ),

                "is_active": True,

                "payout": asset.get(
                    "payout",
                    0
                ),

                "asset_type": asset.get(
                    "asset_type",
                    "unknown"
                ),

                "allowed_candles":
                    allowed_candles,
            }

        ASSET_CACHE = active_assets
        ASSET_CACHE_TIME = now

        print(
            f"✅ Active assets loaded: "
            f"{len(active_assets)}"
        )

        # Debug
        if "AUDCHF" in active_assets:

            print(
                "AUDCHF DURATIONS:",
                active_assets[
                    "AUDCHF"
                ].get(
                    "allowed_candles",
                    []
                )
            )

        print("=" * 60)

        return active_assets

    except Exception as e:

        print("=" * 60)

        print(
            "ASSET LOAD ERROR"
        )

        print(
            "TYPE:",
            type(e).__name__
        )

        print(
            "MESSAGE:",
            str(e)
        )

        print("=" * 60)

        if ASSET_CACHE:

            print(
                "⚠️ Using old asset cache"
            )

            return ASSET_CACHE

        raise


# =========================================================
# Get asset durations
# =========================================================

async def get_asset_durations(pair):

    if not pair:

        return DEFAULT_DURATIONS.copy()

    try:

        assets = await load_active_assets()

        asset_info = assets.get(
            pair
        )

        if not asset_info:

            return DEFAULT_DURATIONS.copy()

        allowed = asset_info.get(
            "allowed_candles",
            []
        )

        allowed = sorted(
            set(
                int(x)
                for x in allowed
            )
        )

        if allowed:

            return allowed

        return DEFAULT_DURATIONS.copy()

    except Exception as e:

        print(
            "GET DURATIONS ERROR:",
            type(e).__name__,
            str(e)
        )

        return DEFAULT_DURATIONS.copy()


# =========================================================
# Start
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    # فقط /start يمسح الإعدادات القديمة
    context.user_data.clear()

    await update.message.reply_text(

        "🤖 Pocket Option Demo Bot\n\n"

        "🧪 الحساب: DEMO\n\n"

        "📋 إعدادات الصفقة:\n"

        "💱 الأصل: غير محدد\n"

        "⏱ المدة: غير محددة\n"

        "💵 المبلغ: غير محدد\n"

        "📈 الاتجاه: غير محدد\n\n"

        "اختر العملية:",

        reply_markup=main_keyboard(),
    )


# =========================================================
# Main menu
# IMPORTANT:
# This function NEVER clears user_data
# =========================================================

async def show_main_menu(
    query,
    context
):

    (
        pair,
        duration,
        amount,
        direction
    ) = get_saved_settings(
        context
    )

    await query.edit_message_text(

        "🤖 Pocket Option Demo Bot\n\n"

        "🧪 الحساب: DEMO\n\n"

        "📋 إعدادات الصفقة:\n"

        f"💱 الأصل: {pair}\n"

        f"⏱ المدة: {duration}\n"

        f"💵 المبلغ: {amount}\n"

        f"📈 الاتجاه: {direction}\n\n"

        "اختر العملية:",

        reply_markup=main_keyboard(),
    )


# =========================================================
# Balance
# =========================================================

async def show_balance(
    query,
    context
):

    try:

        async with PocketOptionAsync(
            ssid=POCKET_SSID
        ) as client:

            if not client.is_connected():

                await client.connect()

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
                    "🏠 الرئيسية",
                    callback_data="home"
                )
            ],

        ]

        await query.edit_message_text(

            "💰 Demo Balance\n\n"

            f"الرصيد: {balance}\n\n"

            "📋 إعداداتك محفوظة.",

            reply_markup=InlineKeyboardMarkup(
                keyboard
            )
        )

    except Exception as e:

        print(
            "BALANCE ERROR:",
            type(e).__name__,
            str(e)
        )

        await query.edit_message_text(

            "❌ تعذر الحصول على الرصيد.\n\n"

            f"الخطأ: {type(e).__name__}",

            reply_markup=InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "🏠 الرئيسية",
                        callback_data="home"
                    )
                ]

            ])
        )


# =========================================================
# Status
# =========================================================

async def show_status(
    query,
    context
):

    try:

        async with PocketOptionAsync(
            ssid=POCKET_SSID
        ) as client:

            if not client.is_connected():

                await client.connect()

            connected = (
                client.is_connected()
            )

            demo = client.is_demo()

            ssid_valid = (
                client.is_ssid_valid()
            )

        await query.edit_message_text(

            "📊 حالة الاتصال\n\n"

            f"🔌 الاتصال: "
            f"{'🟢 متصل' if connected else '🔴 غير متصل'}\n"

            f"🧪 الحساب Demo: "
            f"{'🟢 نعم' if demo else '🔴 لا'}\n"

            f"🔐 SSID: "
            f"{'🟢 صالح' if ssid_valid else '🔴 غير صالح'}\n\n"

            "📋 إعدادات الصفقة محفوظة.",

            reply_markup=InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "🏠 الرئيسية",
                        callback_data="home"
                    )
                ]

            ])
        )

    except Exception as e:

        print(
            "STATUS ERROR:",
            type(e).__name__,
            str(e)
        )

        await query.edit_message_text(

            "❌ خطأ في الاتصال:\n\n"

            f"{type(e).__name__}",

            reply_markup=InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "🏠 الرئيسية",
                        callback_data="home"
                    )
                ]

            ])
        )


# =========================================================
# Asset menu
# =========================================================

async def show_pair_menu(
    query,
    context,
    page=0
):

    try:

        assets = await load_active_assets()

    except Exception as e:

        await query.edit_message_text(

            "❌ تعذر تحميل قائمة الأصول.\n\n"

            f"الخطأ: {type(e).__name__}\n"

            f"{str(e)}",

            reply_markup=InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "🏠 الرئيسية",
                        callback_data="home"
                    )
                ]

            ])
        )

        return

    if not assets:

        await query.edit_message_text(

            "❌ لم يتم العثور على أصول نشطة.",

            reply_markup=InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "🏠 الرئيسية",
                        callback_data="home"
                    )
                ]

            ])
        )

        return

    asset_list = sorted(

        assets.values(),

        key=lambda x:
        str(
            x.get(
                "name",
                x.get(
                    "symbol",
                    ""
                )
            )
        ).lower()
    )

    total_pages = (

        len(asset_list)
        + ASSETS_PER_PAGE
        - 1
    ) // ASSETS_PER_PAGE

    page = max(
        0,
        min(
            page,
            total_pages - 1
        )
    )

    start_index = (
        page * ASSETS_PER_PAGE
    )

    end_index = (
        start_index
        + ASSETS_PER_PAGE
    )

    current_assets = asset_list[
        start_index:end_index
    ]

    keyboard = []

    for asset in current_assets:

        symbol = asset["symbol"]

        name = asset.get(
            "name",
            symbol
        )

        payout = asset.get(
            "payout",
            0
        )

        is_otc = asset.get(
            "is_otc",
            False
        )

        if is_otc:

            button_text = (
                f"{name} OTC"
            )

        else:

            button_text = name

        if len(button_text) > 28:

            button_text = (
                f"{symbol} "
                f"({payout}%)"
            )

        # إظهار الأصل المختار
        current_pair = context.user_data.get(
            "pair"
        )

        if current_pair == symbol:

            button_text = (
                f"✅ {button_text}"
            )

        keyboard.append([

            InlineKeyboardButton(

                button_text,

                callback_data=(
                    f"asset_{symbol}"
                )
            )

        ])

    navigation = []

    if page > 0:

        navigation.append(

            InlineKeyboardButton(
                "⬅️ السابق",
                callback_data=(
                    f"assets_page_{page - 1}"
                )
            )
        )

    if page < total_pages - 1:

        navigation.append(

            InlineKeyboardButton(
                "التالي ➡️",
                callback_data=(
                    f"assets_page_{page + 1}"
                )
            )
        )

    if navigation:

        keyboard.append(
            navigation
        )

    keyboard.append([

        InlineKeyboardButton(
            "🔄 تحديث القائمة",
            callback_data="assets_refresh"
        )

    ])

    keyboard.append([

        InlineKeyboardButton(
            "🏠 الرئيسية",
            callback_data="home"
        )

    ])

    current = context.user_data.get(
        "pair",
        "غير محدد"
    )

    await query.edit_message_text(

        "💱 اختيار الأصل\n\n"

        f"الأصل الحالي: {current}\n"

        f"🟢 الأصول النشطة: "
        f"{len(asset_list)}\n"

        f"📄 الصفحة: "
        f"{page + 1}/{total_pages}\n\n"

        "اختر الأصل:",

        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# =========================================================
# Duration menu
# =========================================================

async def show_duration_menu(
    query,
    context
):

    pair = context.user_data.get(
        "pair"
    )

    current = context.user_data.get(
        "duration"
    )

    if not pair:

        await query.edit_message_text(

            "⚠️ يجب اختيار الأصل أولًا.\n\n"

            "اختر الأصل الذي تريد التداول عليه.",

            reply_markup=InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "💱 اختيار الأصل",
                        callback_data="pair"
                    )
                ],

                [
                    InlineKeyboardButton(
                        "🏠 الرئيسية",
                        callback_data="home"
                    )
                ]

            ])
        )

        return

    try:

        durations = await get_asset_durations(
            pair
        )

    except Exception as e:

        await query.edit_message_text(

            "❌ تعذر الحصول على مدد الأصل.\n\n"

            f"{type(e).__name__}",

            reply_markup=InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "🏠 الرئيسية",
                        callback_data="home"
                    )
                ]

            ])
        )

        return

    # -----------------------------------------------------
    # Validate existing duration
    # -----------------------------------------------------

    if (
        current is not None
        and durations
        and int(current) not in durations
    ):

        context.user_data.pop(
            "duration",
            None
        )

        current = None

    keyboard = []

    row = []

    for duration in durations:

        button_text = duration_text(
            duration
        )

        if (
            current is not None
            and int(current) == int(duration)
        ):

            button_text = (
                f"✅ {button_text}"
            )

        row.append(

            InlineKeyboardButton(

                button_text,

                callback_data=(
                    f"duration_{duration}"
                )
            )
        )

        if len(row) == 2:

            keyboard.append(row)

            row = []

    if row:

        keyboard.append(row)

    keyboard.append([

        InlineKeyboardButton(
            "🏠 الرئيسية",
            callback_data="home"
        )

    ])

    current_display = (

        duration_text(current)
        if current is not None
        else "غير محددة"
    )

    await query.edit_message_text(

        "⏱ اختيار مدة الصفقة\n\n"

        f"💱 الأصل: {pair}\n"

        f"⏱ الحالية: {current_display}\n\n"

        "📋 المدد المدعومة لهذا الأصل:\n"

        + ", ".join(
            duration_text(x)
            for x in durations
        )

        + "\n\nاختر المدة:",

        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# =========================================================
# Amount menu
# =========================================================

async def show_amount_menu(
    query,
    context
):

    current = context.user_data.get(
        "amount"
    )

    keyboard = [

        [
            InlineKeyboardButton(
                "1$" if current != 1 else "✅ 1$",
                callback_data="amount_1"
            ),

            InlineKeyboardButton(
                "5$" if current != 5 else "✅ 5$",
                callback_data="amount_5"
            ),
        ],

        [
            InlineKeyboardButton(
                "10$" if current != 10 else "✅ 10$",
                callback_data="amount_10"
            ),

            InlineKeyboardButton(
                "25$" if current != 25 else "✅ 25$",
                callback_data="amount_25"
            ),
        ],

        [
            InlineKeyboardButton(
                "🏠 الرئيسية",
                callback_data="home"
            )
        ],

    ]

    current_text = (

        f"${current}"
        if current is not None
        else "غير محدد"
    )

    await query.edit_message_text(

        "💵 اختيار المبلغ\n\n"

        f"💵 الحالي: {current_text}\n\n"

        "اختر المبلغ:",

        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# =========================================================
# Confirmation
# =========================================================

async def show_trade_confirmation(
    query,
    context
):

    pair = context.user_data.get(
        "pair"
    )

    duration = context.user_data.get(
        "duration"
    )

    amount = context.user_data.get(
        "amount"
    )

    direction = context.user_data.get(
        "direction"
    )

    missing = []

    if not pair:

        missing.append(
            "💱 الأصل"
        )

    if duration is None:

        missing.append(
            "⏱ المدة"
        )

    if amount is None:

        missing.append(
            "💵 المبلغ"
        )

    if not direction:

        missing.append(
            "📈 الاتجاه"
        )

    if missing:

        await query.edit_message_text(

            "⚠️ إعداد الصفقة غير مكتمل.\n\n"

            "المطلوب:\n"

            + "\n".join(
                f"• {item}"
                for item in missing
            ),

            reply_markup=InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "💱 الأصل",
                        callback_data="pair"
                    )
                ],

                [
                    InlineKeyboardButton(
                        "⏱ المدة",
                        callback_data="duration"
                    )
                ],

                [
                    InlineKeyboardButton(
                        "💵 المبلغ",
                        callback_data="amount"
                    )
                ],

                [
                    InlineKeyboardButton(
                        "🏠 الرئيسية",
                        callback_data="home"
                    )
                ]

            ])
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
            )
        ],

        [
            InlineKeyboardButton(
                "❌ إلغاء",
                callback_data="cancel_trade"
            )
        ],

        [
            InlineKeyboardButton(
                "🏠 الرئيسية",
                callback_data="home"
            )
        ]

    ]

    await query.edit_message_text(

        "📋 تأكيد الصفقة\n\n"

        f"💱 الأصل: {pair}\n"

        f"📈 الاتجاه: {direction_text}\n"

        f"💵 المبلغ: ${amount}\n"

        f"⏱ المدة: "
        f"{duration_text(duration)}\n\n"

        "🧪 الحساب: DEMO\n\n"

        "⚠️ عند الضغط على تأكيد سيتم إرسال "
        "الأمر إلى حساب Demo.",

        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# =========================================================
# Execute trade
# =========================================================

async def execute_trade(
    query,
    context
):

    pair = context.user_data.get(
        "pair"
    )

    amount = context.user_data.get(
        "amount"
    )

    duration = context.user_data.get(
        "duration"
    )

    direction = context.user_data.get(
        "direction"
    )

    if (
        not pair
        or amount is None
        or duration is None
        or not direction
    ):

        await query.edit_message_text(

            "❌ معلومات الصفقة غير مكتملة.",

            reply_markup=InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "🏠 الرئيسية",
                        callback_data="home"
                    )
                ]

            ])
        )

        return

    await query.edit_message_text(

        "⏳ جارٍ فحص الأصل وتنفيذ الصفقة...\n\n"

        f"💱 {pair}\n"

        f"💵 ${amount}\n"

        f"⏱ {duration_text(duration)}"
    )

    try:

        # -------------------------------------------------
        # Asset verification
        # -------------------------------------------------

        assets = await load_active_assets()

        asset_info = assets.get(
            pair
        )

        if not asset_info:

            await query.message.reply_text(

                "❌ الأصل غير موجود في قائمة "
                "الأصول النشطة:\n\n"

                f"{pair}"
            )

            return

        if not asset_info.get(
            "is_active",
            False
        ):

            await query.message.reply_text(

                "❌ الأصل غير نشط حاليًا.\n\n"

                f"💱 {pair}"
            )

            return

        # -------------------------------------------------
        # Duration verification
        # -------------------------------------------------

        allowed_candles = sorted(
            set(
                int(x)
                for x in asset_info.get(
                    "allowed_candles",
                    []
                )
            )
        )

        if (
            allowed_candles
            and int(duration)
            not in allowed_candles
        ):

            context.user_data.pop(
                "duration",
                None
            )

            await query.message.reply_text(

                "❌ مدة الصفقة غير مدعومة لهذا الأصل.\n\n"

                f"💱 الأصل: {pair}\n"

                f"⏱ المطلوبة: "
                f"{duration_text(duration)}\n\n"

                "📋 المدد المدعومة:\n"

                + ", ".join(
                    duration_text(x)
                    for x in allowed_candles
                ),

                reply_markup=InlineKeyboardMarkup([

                    [
                        InlineKeyboardButton(
                            "⏱ اختيار مدة أخرى",
                            callback_data="duration"
                        )
                    ],

                    [
                        InlineKeyboardButton(
                            "🏠 الرئيسية",
                            callback_data="home"
                        )
                    ]

                ])
            )

            return

        # -------------------------------------------------
        # Debug
        # -------------------------------------------------

        print("=" * 60)
        print("TRADE PRE-CHECK")
        print("PAIR:", pair)
        print("AMOUNT:", amount)
        print("DURATION:", duration)
        print("DIRECTION:", direction)
        print(
            "SUPPORTED:",
            allowed_candles
        )
        print("=" * 60)

        # -------------------------------------------------
        # Connect
        # -------------------------------------------------

        async with PocketOptionAsync(
            ssid=POCKET_SSID
        ) as client:

            if not client.is_connected():

                await client.connect()

            if not client.is_ssid_valid():

                raise RuntimeError(
                    "SSID is not valid"
                )

            # -------------------------------------------------
            # Buy
            # -------------------------------------------------

            if direction == "buy":

                trade_id, trade_data = (
                    await client.buy(

                        pair,

                        float(amount),

                        int(duration),

                        check_win=False
                    )
                )

            # -------------------------------------------------
            # Sell
            # -------------------------------------------------

            else:

                trade_id, trade_data = (
                    await client.sell(

                        pair,

                        float(amount),

                        int(duration),

                        check_win=False
                    )
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

                f"💱 الأصل: {pair}\n"

                f"📈 الاتجاه: {direction_text}\n"

                f"💵 المبلغ: ${amount}\n"

                f"⏱ المدة: "
                f"{duration_text(duration)}\n\n"

                f"💰 Payout: "
                f"{asset_info.get('payout', 0)}%\n\n"

                "⏳ ننتظر النتيجة..."
            )

            # -------------------------------------------------
            # Wait
            # -------------------------------------------------

            await asyncio.sleep(
                int(duration)
            )

            # -------------------------------------------------
            # Result
            # -------------------------------------------------

            try:

                result = await client.check_win(
                    trade_id
                )

                print(
                    "WIN RESULT:",
                    result
                )

                result_text = str(
                    result
                ).lower()

                if "win" in result_text:

                    result_emoji = "🟢"
                    result_label = "WIN"

                elif "loss" in result_text:

                    result_emoji = "🔴"
                    result_label = "LOSS"

                else:

                    result_emoji = "ℹ️"
                    result_label = "UNKNOWN"

                await query.message.reply_text(

                    f"{result_emoji} نتيجة الصفقة\n\n"

                    f"🆔 Trade ID:\n"
                    f"{trade_id}\n\n"

                    f"💱 الأصل: {pair}\n"

                    f"📈 الاتجاه: {direction_text}\n"

                    f"💵 المبلغ: ${amount}\n"

                    f"⏱ المدة: "
                    f"{duration_text(duration)}\n\n"

                    f"📊 النتيجة: "
                    f"{result_label}\n\n"

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
                    f"{type(result_error).__name__}\n"

                    f"{str(result_error)}"
                )

    except Exception as e:

        print("=" * 60)
        print("TRADE ERROR")
        print("TYPE:", type(e).__name__)
        print("MESSAGE:", str(e))
        print("REPR:", repr(e))
        print("=" * 60)

        await query.message.reply_text(

            "❌ فشل تنفيذ الصفقة.\n\n"

            f"نوع الخطأ:\n"
            f"{type(e).__name__}\n\n"

            f"التفاصيل:\n"
            f"{str(e)}",

            reply_markup=InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "🏠 الرئيسية",
                        callback_data="home"
                    )
                ]

            ])
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

    # =====================================================
    # HOME
    # =====================================================

    if data == "home":

        await show_main_menu(
            query,
            context
        )

        return

    # =====================================================
    # BALANCE
    # =====================================================

    if data == "balance":

        await show_balance(
            query,
            context
        )

        return

    # =====================================================
    # STATUS
    # =====================================================

    if data == "status":

        await show_status(
            query,
            context
        )

        return

    # =====================================================
    # PAIR MENU
    # =====================================================

    if data == "pair":

        await show_pair_menu(
            query,
            context,
            page=0
        )

        return

    # =====================================================
    # ASSET PAGINATION
    # =====================================================

    if data.startswith(
        "assets_page_"
    ):

        page = int(
            data.replace(
                "assets_page_",
                ""
            )
        )

        await show_pair_menu(
            query,
            context,
            page=page
        )

        return

    # =====================================================
    # REFRESH
    # =====================================================

    if data == "assets_refresh":

        global ASSET_CACHE
        global ASSET_CACHE_TIME

        ASSET_CACHE = {}
        ASSET_CACHE_TIME = 0

        await show_pair_menu(
            query,
            context,
            page=0
        )

        return

    # =====================================================
    # SELECT ASSET
    # =====================================================

    if data.startswith(
        "asset_"
    ):

        symbol = data[
            len("asset_"):
        ]

        assets = await load_active_assets()

        asset_info = assets.get(
            symbol
        )

        if not asset_info:

            await query.answer(

                "❌ الأصل غير متاح حاليًا.",

                show_alert=True
            )

            return

        # -------------------------------------------------
        # SAVE PAIR
        # -------------------------------------------------

        context.user_data[
            "pair"
        ] = symbol

        # -------------------------------------------------
        # Validate old duration
        # -------------------------------------------------

        old_duration = context.user_data.get(
            "duration"
        )

        allowed = sorted(
            set(
                int(x)
                for x in asset_info.get(
                    "allowed_candles",
                    []
                )
            )
        )

        if (
            old_duration is not None
            and allowed
            and int(old_duration)
            not in allowed
        ):

            context.user_data.pop(
                "duration",
                None
            )

            print(
                "OLD DURATION REMOVED:",
                old_duration
            )

        print(
            "SELECTED ASSET:",
            symbol
        )

        print(
            "USER DATA:",
            dict(context.user_data)
        )

        # مهم:
        # لا نمسح amount
        # لا نمسح direction

        await show_main_menu(
            query,
            context
        )

        return

    # =====================================================
    # DURATION MENU
    # =====================================================

    if data == "duration":

        await show_duration_menu(
            query,
            context
        )

        return

    # =====================================================
    # SELECT DURATION
    # =====================================================

    if data.startswith(
        "duration_"
    ):

        duration = int(
            data.replace(
                "duration_",
                ""
            )
        )

        pair = context.user_data.get(
            "pair"
        )

        if not pair:

            await query.answer(

                "❌ اختر الأصل أولًا.",

                show_alert=True
            )

            return

        durations = await get_asset_durations(
            pair
        )

        if (
            durations
            and duration not in durations
        ):

            await query.answer(

                f"❌ {duration_text(duration)} "
                f"غير مدعومة لـ {pair}",

                show_alert=True
            )

            return

        # -------------------------------------------------
        # SAVE DURATION
        # -------------------------------------------------

        context.user_data[
            "duration"
        ] = duration

        print(
            "SELECTED DURATION:",
            duration
        )

        print(
            "USER DATA:",
            dict(context.user_data)
        )

        await show_main_menu(
            query,
            context
        )

        return

    # =====================================================
    # AMOUNT MENU
    # =====================================================

    if data == "amount":

        await show_amount_menu(
            query,
            context
        )

        return

    # =====================================================
    # SELECT AMOUNT
    # =====================================================

    if data.startswith(
        "amount_"
    ):

        amount = float(
            data.replace(
                "amount_",
                ""
            )
        )

        # SAVE
        context.user_data[
            "amount"
        ] = amount

        print(
            "SELECTED AMOUNT:",
            amount
        )

        print(
            "USER DATA:",
            dict(context.user_data)
        )

        await show_main_menu(
            query,
            context
        )

        return

    # =====================================================
    # BUY
    # =====================================================

    if data == "buy":

        context.user_data[
            "direction"
        ] = "buy"

        print(
            "SELECTED DIRECTION: BUY"
        )

        print(
            "USER DATA:",
            dict(context.user_data)
        )

        await show_trade_confirmation(
            query,
            context
        )

        return

    # =====================================================
    # SELL
    # =====================================================

    if data == "sell":

        context.user_data[
            "direction"
        ] = "sell"

        print(
            "SELECTED DIRECTION: SELL"
        )

        print(
            "USER DATA:",
            dict(context.user_data)
        )

        await show_trade_confirmation(
            query,
            context
        )

        return

    # =====================================================
    # CONFIRM
    # =====================================================

    if data == "confirm_trade":

        await execute_trade(
            query,
            context
        )

        return

    # =====================================================
    # CANCEL
    # =====================================================

    if data == "cancel_trade":

        # فقط إلغاء الاتجاه
        # ولا نمسح الأصل أو المبلغ أو المدة

        context.user_data.pop(
            "direction",
            None
        )

        await show_main_menu(
            query,
            context
        )

        return


# =========================================================
# Error handler
# =========================================================

async def error_handler(
    update,
    context
):

    print("=" * 60)
    print("BOT ERROR")
    print(
        "TYPE:",
        type(context.error).__name__
    )
    print(
        "MESSAGE:",
        str(context.error)
    )
    print("=" * 60)


# =========================================================
# Main
# =========================================================

def main():

    app = (

        Application.builder()

        .token(
            TELEGRAM_TOKEN
        )

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

    app.add_error_handler(
        error_handler
    )

    print(
        "Telegram bot started..."
    )

    app.run_polling()


# =========================================================
# Entry point
# =========================================================

if __name__ == "__main__":

    main()
