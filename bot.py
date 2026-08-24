import os
import asyncio
import time
from typing import Dict, Any, Optional

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.error import BadRequest, TelegramError
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from BinaryOptionsToolsV2 import PocketOptionAsync


# =========================================================
# ENVIRONMENT
# =========================================================

POCKET_SSID = os.environ["POCKET_OPTION_SSID"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]


# =========================================================
# CONFIG
# =========================================================

ASSET_CACHE_TTL = 300
ASSETS_PER_PAGE = 12

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
# GLOBAL CACHE
# =========================================================

ASSET_CACHE: Dict[str, Dict[str, Any]] = {}
ASSET_CACHE_TIME = 0.0

ASSET_LOCK = asyncio.Lock()

# منع تنفيذ أكثر من صفقة في نفس الوقت للمستخدم
TRADE_LOCKS: Dict[int, asyncio.Lock] = {}


# =========================================================
# SAFE TELEGRAM EDIT
# =========================================================

async def safe_edit(
    query,
    text: str,
    reply_markup=None
):
    """
    يمنع:
    BadRequest: Message is not modified
    """

    try:

        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
        )

    except BadRequest as e:

        if "Message is not modified" in str(e):

            return

        raise


# =========================================================
# SAFE ANSWER
# =========================================================

async def safe_answer(
    query,
    text: Optional[str] = None,
    show_alert: bool = False
):

    try:

        await query.answer(
            text=text,
            show_alert=show_alert,
        )

    except Exception:
        pass


# =========================================================
# DURATION TEXT
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

        if minutes in (10, 15, 30, 45):

            return f"{minutes} دقيقة"

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
# FORMAT NUMBER
# =========================================================

def money(value):

    try:

        value = float(value)

        if value.is_integer():

            return f"${int(value)}"

        return f"${value:.2f}"

    except Exception:

        return f"${value}"


# =========================================================
# USER SETTINGS
# =========================================================

def get_saved_settings(context):

    pair = context.user_data.get("pair")

    duration = context.user_data.get("duration")

    amount = context.user_data.get("amount")

    direction = context.user_data.get("direction")

    pair_text = pair or "غير محدد"

    duration_value = (
        duration_text(duration)
        if duration is not None
        else "غير محددة"
    )

    amount_text = (
        money(amount)
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
# MAIN UI
# =========================================================

def main_keyboard():

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "💰 الرصيد",
                callback_data="balance",
            ),

            InlineKeyboardButton(
                "📡 الحالة",
                callback_data="status",
            ),
        ],

        [
            InlineKeyboardButton(
                "💱 اختيار الأصل",
                callback_data="pair",
            ),
        ],

        [
            InlineKeyboardButton(
                "⏱ المدة",
                callback_data="duration",
            ),

            InlineKeyboardButton(
                "💵 المبلغ",
                callback_data="amount",
            ),
        ],

        [
            InlineKeyboardButton(
                "🟢 BUY",
                callback_data="buy",
            ),

            InlineKeyboardButton(
                "🔴 SELL",
                callback_data="sell",
            ),
        ],

    ])


# =========================================================
# HOME TEXT
# =========================================================

def home_text(context):

    pair, duration, amount, direction = (
        get_saved_settings(context)
    )

    return (
        "╭━━━━━━━━━━━━━━━━━━╮\n"
        "   🤖 POCKET OPTION BOT\n"
        "╰━━━━━━━━━━━━━━━━━━╯\n\n"

        "🧪 الحساب: `DEMO`\n"
        "🟢 النظام: جاهز\n\n"

        "┌─ 📋 إعدادات الصفقة\n"
        f"├ 💱 الأصل: {pair}\n"
        f"├ ⏱ المدة: {duration}\n"
        f"├ 💵 المبلغ: {amount}\n"
        f"└ 📈 الاتجاه: {direction}\n\n"

        "اختر العملية من القائمة 👇"
    )


# =========================================================
# START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    context.user_data.clear()

    await update.message.reply_text(

        home_text(context),

        parse_mode="Markdown",

        reply_markup=main_keyboard(),
    )


# =========================================================
# SHOW HOME
# =========================================================

async def show_main_menu(
    query,
    context,
):

    await safe_edit(

        query,

        home_text(context),

        main_keyboard(),
    )


# =========================================================
# POCKET CLIENT
# =========================================================

async def create_client():

    client = PocketOptionAsync(
        ssid=POCKET_SSID
    )

    try:

        if not client.is_connected():

            await client.connect()

        return client

    except Exception:

        try:

            await client.close()

        except Exception:

            pass

        raise


# =========================================================
# LOAD ACTIVE ASSETS
#
# IMPORTANT:
# BinaryOptionsToolsV2 0.2.13
# uses active_assets()
#
# NEVER get_all_assets()
# =========================================================

async def load_active_assets(
    force=False
):

    global ASSET_CACHE
    global ASSET_CACHE_TIME

    now = time.monotonic()

    # -----------------------------------------------------
    # FAST CACHE
    # -----------------------------------------------------

    if (
        not force
        and ASSET_CACHE
        and (now - ASSET_CACHE_TIME) < ASSET_CACHE_TTL
    ):

        return ASSET_CACHE

    # -----------------------------------------------------
    # Prevent simultaneous loading
    # -----------------------------------------------------

    async with ASSET_LOCK:

        now = time.monotonic()

        if (
            not force
            and ASSET_CACHE
            and (now - ASSET_CACHE_TIME) < ASSET_CACHE_TTL
        ):

            return ASSET_CACHE

        print("=" * 60)
        print("LOADING ACTIVE ASSETS")
        print("=" * 60)

        try:

            async with PocketOptionAsync(
                ssid=POCKET_SSID
            ) as client:

                if not client.is_connected():

                    await client.connect()

                # -------------------------------------------------
                # Wait for asset information
                # -------------------------------------------------

                try:

                    await client.wait_for_assets()

                except Exception as wait_error:

                    print(
                        "WAIT FOR ASSETS WARNING:",
                        type(wait_error).__name__,
                        str(wait_error)
                    )

                # -------------------------------------------------
                # CRITICAL:
                # Use active_assets()
                # -------------------------------------------------

                active_assets_method = getattr(
                    client,
                    "active_assets",
                    None
                )

                if not callable(
                    active_assets_method
                ):

                    raise RuntimeError(
                        "BinaryOptionsToolsV2 لا يحتوي "
                        "على active_assets(). "
                        "تأكد من تثبيت BinaryOptionsToolsV2==0.2.13."
                    )

                assets = await active_assets_method()

            print(
                "ACTIVE ASSETS TYPE:",
                type(assets)
            )

            if assets is None:

                assets = []

            print(
                "ACTIVE ASSETS COUNT:",
                len(assets)
            )

            normalized = {}

            # =================================================
            # PARSE
            # =================================================

            if isinstance(assets, dict):

                iterable = assets.values()

            elif isinstance(assets, list):

                iterable = assets

            else:

                iterable = []

            for asset in iterable:

                if not isinstance(
                    asset,
                    dict
                ):

                    continue

                # -------------------------------------------------
                # Symbol
                # -------------------------------------------------

                symbol = (
                    asset.get("symbol")
                    or asset.get("asset")
                    or asset.get("name")
                )

                if not symbol:

                    continue

                symbol = str(symbol)

                # -------------------------------------------------
                # Active
                # -------------------------------------------------

                is_active = asset.get(
                    "is_active",
                    asset.get(
                        "active",
                        True
                    )
                )

                if is_active is False:

                    continue

                # -------------------------------------------------
                # Candles
                # -------------------------------------------------

                allowed_candles = []

                candles = asset.get(
                    "allowed_candles",
                    []
                )

                if isinstance(
                    candles,
                    (list, tuple)
                ):

                    for candle in candles:

                        value = None

                        if isinstance(
                            candle,
                            dict
                        ):

                            value = (
                                candle.get("time")
                                or candle.get("duration")
                                or candle.get("seconds")
                            )

                        elif isinstance(
                            candle,
                            (int, float)
                        ):

                            value = candle

                        if value is not None:

                            try:

                                allowed_candles.append(
                                    int(value)
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

                normalized[symbol] = {

                    "id": asset.get("id"),

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

            # -------------------------------------------------
            # Save cache
            # -------------------------------------------------

            if normalized:

                ASSET_CACHE = normalized

                ASSET_CACHE_TIME = (
                    time.monotonic()
                )

            print(
                f"✅ Active assets loaded: "
                f"{len(ASSET_CACHE)}"
            )

            print("=" * 60)

            return ASSET_CACHE

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

            # -------------------------------------------------
            # Use old cache if available
            # -------------------------------------------------

            if ASSET_CACHE:

                print(
                    "⚠️ Using previous asset cache"
                )

                return ASSET_CACHE

            raise


# =========================================================
# BACKGROUND ASSET PRELOAD
# =========================================================

async def preload_assets(
    application: Application
):

    try:

        print("🚀 Preloading assets...")

        assets = await load_active_assets(
            force=True
        )

        print(
            f"✅ Asset preload complete: "
            f"{len(assets)} assets"
        )

    except Exception as e:

        print(
            "⚠️ Asset preload failed:",
            type(e).__name__,
            str(e)
        )


# =========================================================
# POST INIT
# =========================================================

async def post_init(
    application: Application
):

    await preload_assets(
        application
    )


# =========================================================
# GET ASSET DURATIONS
# =========================================================

async def get_asset_durations(
    pair
):

    if not pair:

        return DEFAULT_DURATIONS.copy()

    try:

        assets = await load_active_assets()

        asset_info = assets.get(pair)

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
# BALANCE
# =========================================================

async def show_balance(
    query,
    context,
):

    await safe_edit(

        query,

        "⏳ جاري تحميل الرصيد...\n\n"
        "⚡ لحظة واحدة..."
    )

    try:

        async with PocketOptionAsync(
            ssid=POCKET_SSID
        ) as client:

            if not client.is_connected():

                await client.connect()

            balance = await client.balance()

        keyboard = InlineKeyboardMarkup([

            [
                InlineKeyboardButton(
                    "🔄 تحديث",
                    callback_data="balance",
                ),
            ],

            [
                InlineKeyboardButton(
                    "🏠 الرئيسية",
                    callback_data="home",
                ),
            ],

        ])

        await safe_edit(

            query,

            "╭━━━━━━━━━━━━━━━━━━╮\n"
            "       💰 BALANCE\n"
            "╰━━━━━━━━━━━━━━━━━━╯\n\n"

            f"💵 الرصيد:\n"
            f"   {balance}\n\n"

            "🧪 الحساب: DEMO\n"
            "🟢 الاتصال: نشط",

            keyboard,
        )

    except Exception as e:

        await safe_edit(

            query,

            "❌ تعذر الحصول على الرصيد.\n\n"

            f"الخطأ: `{type(e).__name__}`",

            InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "🔄 إعادة المحاولة",
                        callback_data="balance",
                    )
                ],

                [
                    InlineKeyboardButton(
                        "🏠 الرئيسية",
                        callback_data="home",
                    )
                ],

            ]),
        )


# =========================================================
# STATUS
# =========================================================

async def show_status(
    query,
    context,
):

    await safe_edit(

        query,

        "⏳ فحص الاتصال..."
    )

    try:

        async with PocketOptionAsync(
            ssid=POCKET_SSID
        ) as client:

            if not client.is_connected():

                await client.connect()

            connected = (
                client.is_connected()
            )

            try:

                demo = client.is_demo()

            except Exception:

                demo = True

            try:

                ssid_valid = (
                    client.is_ssid_valid()
                )

            except Exception:

                ssid_valid = True

        await safe_edit(

            query,

            "╭━━━━━━━━━━━━━━━━━━╮\n"
            "       📡 STATUS\n"
            "╰━━━━━━━━━━━━━━━━━━╯\n\n"

            f"🔌 الاتصال: "
            f"{'🟢 متصل' if connected else '🔴 غير متصل'}\n\n"

            f"🧪 Demo: "
            f"{'🟢 نعم' if demo else '🔴 لا'}\n\n"

            f"🔐 SSID: "
            f"{'🟢 صالح' if ssid_valid else '🔴 غير صالح'}\n\n"

            f"💱 الأصول في الذاكرة: "
            f"{len(ASSET_CACHE)}",

            InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "🔄 فحص مرة أخرى",
                        callback_data="status",
                    )
                ],

                [
                    InlineKeyboardButton(
                        "🏠 الرئيسية",
                        callback_data="home",
                    )
                ],

            ]),
        )

    except Exception as e:

        await safe_edit(

            query,

            "🔴 فشل فحص الاتصال\n\n"

            f"`{type(e).__name__}`\n"
            f"{str(e)}",

            InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "🏠 الرئيسية",
                        callback_data="home",
                    )
                ],

            ]),
        )


# =========================================================
# ASSET MENU
# =========================================================

async def show_pair_menu(
    query,
    context,
    page=0,
):

    # -----------------------------------------------------
    # If cache exists -> instant
    # -----------------------------------------------------

    try:

        assets = await load_active_assets()

    except Exception as e:

        await safe_edit(

            query,

            "❌ تعذر تحميل قائمة الأصول.\n\n"

            f"نوع الخطأ: `{type(e).__name__}`\n\n"

            f"{str(e)}",

            InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "🔄 إعادة المحاولة",
                        callback_data="pair",
                    )
                ],

                [
                    InlineKeyboardButton(
                        "🏠 الرئيسية",
                        callback_data="home",
                    )
                ],

            ]),
        )

        return

    if not assets:

        await safe_edit(

            query,

            "❌ لم يتم العثور على أصول نشطة.",

            InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "🔄 تحديث",
                        callback_data="assets_refresh",
                    )
                ],

                [
                    InlineKeyboardButton(
                        "🏠 الرئيسية",
                        callback_data="home",
                    )
                ],

            ]),
        )

        return

    # -----------------------------------------------------
    # Sort
    # -----------------------------------------------------

    asset_list = sorted(

        assets.values(),

        key=lambda x: str(
            x.get(
                "symbol",
                ""
            )
        ).lower()
    )

    total_pages = max(

        1,

        (
            len(asset_list)
            + ASSETS_PER_PAGE
            - 1
        )
        // ASSETS_PER_PAGE
    )

    page = max(

        0,

        min(
            int(page),
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

    current_pair = context.user_data.get(
        "pair"
    )

    for asset in current_assets:

        symbol = asset.get(
            "symbol",
            ""
        )

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

        label = symbol

        if is_otc:

            label += " OTC"

        if payout:

            label += f" • {payout}%"

        if current_pair == symbol:

            label = f"✅ {label}"

        keyboard.append([

            InlineKeyboardButton(

                label[:64],

                callback_data=(
                    f"asset_{symbol}"
                )
            )

        ])

    # -----------------------------------------------------
    # Navigation
    # -----------------------------------------------------

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

    navigation.append(

        InlineKeyboardButton(
            f"📄 {page + 1}/{total_pages}",
            callback_data="noop",
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

    keyboard.append(
        navigation
    )

    keyboard.append([

        InlineKeyboardButton(
            "🔄 تحديث",
            callback_data="assets_refresh",
        ),

        InlineKeyboardButton(
            "🏠 الرئيسية",
            callback_data="home",
        ),

    ])

    current = current_pair or "غير محدد"

    await safe_edit(

        query,

        "╭━━━━━━━━━━━━━━━━━━╮\n"
        "       💱 ASSETS\n"
        "╰━━━━━━━━━━━━━━━━━━╯\n\n"

        f"🎯 الحالي: `{current}`\n"
        f"🟢 النشطة: {len(asset_list)}\n"
        f"📄 الصفحة: {page + 1}/{total_pages}\n\n"

        "اختر الأصل 👇",

        InlineKeyboardMarkup(
            keyboard
        ),
    )


# =========================================================
# DURATION MENU
# =========================================================

async def show_duration_menu(
    query,
    context,
):

    pair = context.user_data.get(
        "pair"
    )

    current = context.user_data.get(
        "duration"
    )

    if not pair:

        await safe_edit(

            query,

            "⚠️ يجب اختيار الأصل أولًا.",

            InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "💱 اختيار الأصل",
                        callback_data="pair",
                    )
                ],

                [
                    InlineKeyboardButton(
                        "🏠 الرئيسية",
                        callback_data="home",
                    )
                ],

            ]),
        )

        return

    durations = await get_asset_durations(
        pair
    )

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

        label = duration_text(
            duration
        )

        if (
            current is not None
            and int(current) == int(duration)
        ):

            label = f"✅ {label}"

        row.append(

            InlineKeyboardButton(

                label,

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
            callback_data="home",
        )

    ])

    current_text = (

        duration_text(current)
        if current is not None
        else "غير محددة"
    )

    await safe_edit(

        query,

        "╭━━━━━━━━━━━━━━━━━━╮\n"
        "      ⏱ DURATION\n"
        "╰━━━━━━━━━━━━━━━━━━╯\n\n"

        f"💱 الأصل: `{pair}`\n"
        f"⏱ الحالية: {current_text}\n\n"

        "اختر المدة 👇",

        InlineKeyboardMarkup(
            keyboard
        ),
    )


# =========================================================
# AMOUNT MENU
# =========================================================

async def show_amount_menu(
    query,
    context,
):

    current = context.user_data.get(
        "amount"
    )

    amounts = [
        1,
        5,
        10,
        25,
    ]

    keyboard = []

    row = []

    for amount in amounts:

        label = (
            f"✅ {amount}$"
            if current == amount
            else f"{amount}$"
        )

        row.append(

            InlineKeyboardButton(

                label,

                callback_data=(
                    f"amount_{amount}"
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
            callback_data="home",
        )

    ])

    current_text = (
        money(current)
        if current is not None
        else "غير محدد"
    )

    await safe_edit(

        query,

        "╭━━━━━━━━━━━━━━━━━━╮\n"
        "        💵 AMOUNT\n"
        "╰━━━━━━━━━━━━━━━━━━╯\n\n"

        f"💵 الحالي: {current_text}\n\n"

        "اختر المبلغ 👇",

        InlineKeyboardMarkup(
            keyboard
        ),
    )


# =========================================================
# CONFIRMATION
# =========================================================

async def show_trade_confirmation(
    query,
    context,
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
        missing.append("💱 الأصل")

    if duration is None:
        missing.append("⏱ المدة")

    if amount is None:
        missing.append("💵 المبلغ")

    if not direction:
        missing.append("📈 الاتجاه")

    if missing:

        await safe_edit(

            query,

            "⚠️ إعداد الصفقة غير مكتمل.\n\n"

            + "\n".join(
                f"• {x}"
                for x in missing
            ),

            InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "💱 الأصل",
                        callback_data="pair",
                    )
                ],

                [
                    InlineKeyboardButton(
                        "⏱ المدة",
                        callback_data="duration",
                    )
                ],

                [
                    InlineKeyboardButton(
                        "💵 المبلغ",
                        callback_data="amount",
                    )
                ],

                [
                    InlineKeyboardButton(
                        "🏠 الرئيسية",
                        callback_data="home",
                    )
                ],

            ]),
        )

        return

    direction_text = (

        "🟢 BUY"
        if direction == "buy"
        else "🔴 SELL"
    )

    keyboard = InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "🚀 تأكيد الصفقة",
                callback_data="confirm_trade",
            )
        ],

        [
            InlineKeyboardButton(
                "❌ إلغاء",
                callback_data="cancel_trade",
            )
        ],

        [
            InlineKeyboardButton(
                "🏠 الرئيسية",
                callback_data="home",
            )
        ],

    ])

    await safe_edit(

        query,

        "╭━━━━━━━━━━━━━━━━━━╮\n"
        "     📋 CONFIRM TRADE\n"
        "╰━━━━━━━━━━━━━━━━━━╯\n\n"

        f"💱 الأصل: `{pair}`\n"
        f"📈 الاتجاه: {direction_text}\n"
        f"💵 المبلغ: {money(amount)}\n"
        f"⏱ المدة: {duration_text(duration)}\n\n"

        "🧪 الحساب: DEMO\n\n"

        "⚠️ تأكد من البيانات قبل التنفيذ.",

        keyboard,
    )


# =========================================================
# RESULT PARSER
# =========================================================

def parse_trade_result(result):

    if result is None:

        return (
            "ℹ️",
            "UNKNOWN"
        )

    # -----------------------------------------------------
    # Dict
    # -----------------------------------------------------

    if isinstance(
        result,
        dict
    ):

        status = str(
            result.get(
                "result",
                ""
            )
        ).lower()

        if status in (
            "win",
            "won",
            "profit"
        ):

            return (
                "🟢",
                "WIN"
            )

        if status in (
            "loss",
            "lost"
        ):

            return (
                "🔴",
                "LOSS"
            )

        try:

            profit = float(
                result.get(
                    "profit",
                    0
                )
            )

            if profit > 0:

                return (
                    "🟢",
                    "WIN"
                )

            if profit < 0:

                return (
                    "🔴",
                    "LOSS"
                )

            return (
                "⚪",
                "DRAW"
            )

        except Exception:

            pass

    # -----------------------------------------------------
    # String fallback
    # -----------------------------------------------------

    text = str(
        result
    ).lower()

    if "loss" in text:

        return (
            "🔴",
            "LOSS"
        )

    if "win" in text:

        return (
            "🟢",
            "WIN"
        )

    return (
        "ℹ️",
        "UNKNOWN"
    )


# =========================================================
# EXECUTE TRADE
# =========================================================

async def execute_trade(
    query,
    context,
):

    user_id = query.from_user.id

    lock = TRADE_LOCKS.setdefault(
        user_id,
        asyncio.Lock()
    )

    if lock.locked():

        await safe_answer(

            query,

            "⏳ توجد صفقة قيد التنفيذ بالفعل.",

            show_alert=True,
        )

        return

    async with lock:

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

            await safe_edit(

                query,

                "❌ معلومات الصفقة غير مكتملة.",

                InlineKeyboardMarkup([

                    [
                        InlineKeyboardButton(
                            "🏠 الرئيسية",
                            callback_data="home",
                        )
                    ]

                ]),
            )

            return

        # -------------------------------------------------
        # Instant UI
        # -------------------------------------------------

        await safe_edit(

            query,

            "⏳ جاري تجهيز الصفقة...\n\n"

            f"💱 `{pair}`\n"
            f"📈 {direction.upper()}\n"
            f"💵 {money(amount)}\n"
            f"⏱ {duration_text(duration)}",
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

                await safe_edit(

                    query,

                    "❌ الأصل غير متاح حاليًا.\n\n"

                    f"💱 `{pair}`",

                    InlineKeyboardMarkup([

                        [
                            InlineKeyboardButton(
                                "💱 اختيار أصل",
                                callback_data="pair",
                            )
                        ],

                        [
                            InlineKeyboardButton(
                                "🏠 الرئيسية",
                                callback_data="home",
                            )
                        ],

                    ]),
                )

                return

            # -------------------------------------------------
            # Duration verification
            # -------------------------------------------------

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
                allowed
                and int(duration) not in allowed
            ):

                context.user_data.pop(
                    "duration",
                    None
                )

                await safe_edit(

                    query,

                    "❌ المدة غير مدعومة لهذا الأصل.\n\n"

                    f"💱 `{pair}`\n"
                    f"⏱ المطلوبة: "
                    f"{duration_text(duration)}\n\n"

                    "المدد المتاحة:\n"

                    + ", ".join(
                        duration_text(x)
                        for x in allowed
                    ),

                    InlineKeyboardMarkup([

                        [
                            InlineKeyboardButton(
                                "⏱ اختيار مدة",
                                callback_data="duration",
                            )
                        ],

                        [
                            InlineKeyboardButton(
                                "🏠 الرئيسية",
                                callback_data="home",
                            )
                        ],

                    ]),
                )

                return

            print("=" * 60)
            print("TRADE PRE-CHECK")
            print("PAIR:", pair)
            print("AMOUNT:", amount)
            print("DURATION:", duration)
            print("DIRECTION:", direction)
            print("SUPPORTED:", allowed)
            print("=" * 60)

            # -------------------------------------------------
            # Execute
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

                if direction == "buy":

                    trade_id, trade_data = (
                        await client.buy(

                            pair,

                            float(amount),

                            int(duration),

                            check_win=False,
                        )
                    )

                else:

                    trade_id, trade_data = (
                        await client.sell(

                            pair,

                            float(amount),

                            int(duration),

                            check_win=False,
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

                await safe_edit(

                    query,

                    "╭━━━━━━━━━━━━━━━━━━╮\n"
                    "      🟢 TRADE OPEN\n"
                    "╰━━━━━━━━━━━━━━━━━━╯\n\n"

                    f"🆔 `{trade_id}`\n\n"

                    f"💱 الأصل: `{pair}`\n"
                    f"📈 الاتجاه: {direction_text}\n"
                    f"💵 المبلغ: {money(amount)}\n"
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
                # Check result
                # -------------------------------------------------

                try:

                    result = await client.check_win(
                        trade_id
                    )

                    print(
                        "WIN RESULT:",
                        result
                    )

                    emoji, label = (
                        parse_trade_result(
                            result
                        )
                    )

                    await query.message.reply_text(

                        "╭━━━━━━━━━━━━━━━━━━╮\n"
                        f"      {emoji} TRADE RESULT\n"
                        "╰━━━━━━━━━━━━━━━━━━╯\n\n"

                        f"🆔 `{trade_id}`\n\n"

                        f"💱 الأصل: `{pair}`\n"
                        f"📈 الاتجاه: {direction_text}\n"
                        f"💵 المبلغ: {money(amount)}\n"
                        f"⏱ المدة: "
                        f"{duration_text(duration)}\n\n"

                        f"📊 النتيجة: "
                        f"{emoji} {label}\n\n"

                        f"`{result}`",
                    )

                except Exception as result_error:

                    print(
                        "CHECK WIN ERROR:",
                        type(result_error).__name__,
                        result_error,
                    )

                    await query.message.reply_text(

                        "⚠️ تم فتح الصفقة، "
                        "لكن تعذر قراءة النتيجة.\n\n"

                        f"🆔 `{trade_id}`\n\n"

                        f"الخطأ: "
                        f"`{type(result_error).__name__}`",
                    )

        except Exception as e:

            print("=" * 60)
            print("TRADE ERROR")
            print(
                "TYPE:",
                type(e).__name__
            )
            print(
                "MESSAGE:",
                str(e)
            )
            print("=" * 60)

            await safe_edit(

                query,

                "❌ فشل تنفيذ الصفقة.\n\n"

                f"النوع:\n"
                f"`{type(e).__name__}`\n\n"

                f"التفاصيل:\n"
                f"{str(e)}",

                InlineKeyboardMarkup([

                    [
                        InlineKeyboardButton(
                            "🔄 إعادة المحاولة",
                            callback_data="confirm_trade",
                        )
                    ],

                    [
                        InlineKeyboardButton(
                            "🏠 الرئيسية",
                            callback_data="home",
                        )
                    ],

                ]),
            )


# =========================================================
# CALLBACK HANDLER
# =========================================================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    await safe_answer(query)

    data = query.data

    # =====================================================
    # NOOP
    # =====================================================

    if data == "noop":

        return

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
    # PAIR
    # =====================================================

    if data == "pair":

        await show_pair_menu(
            query,
            context,
            0
        )

        return

    # =====================================================
    # PAGE
    # =====================================================

    if data.startswith(
        "assets_page_"
    ):

        try:

            page = int(
                data.replace(
                    "assets_page_",
                    ""
                )
            )

        except ValueError:

            page = 0

        await show_pair_menu(

            query,

            context,

            page
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

        await safe_edit(

            query,

            "⏳ تحديث قائمة الأصول..."
        )

        await show_pair_menu(

            query,

            context,

            0
        )

        return

    # =====================================================
    # ASSET SELECT
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

            await safe_answer(

                query,

                "❌ الأصل غير متاح حاليًا.",

                True
            )

            return

        context.user_data[
            "pair"
        ] = symbol

        old_duration = (
            context.user_data.get(
                "duration"
            )
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
            "SELECTED ASSET:",
            symbol
        )

        print(
            "USER DATA:",
            dict(
                context.user_data
            )
        )

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

        try:

            duration = int(
                data.replace(
                    "duration_",
                    ""
                )
            )

        except ValueError:

            await safe_answer(
                query,
                "❌ مدة غير صالحة.",
                True
            )

            return

        pair = context.user_data.get(
            "pair"
        )

        if not pair:

            await safe_answer(

                query,

                "❌ اختر الأصل أولًا.",

                True
            )

            return

        durations = await get_asset_durations(
            pair
        )

        if (
            durations
            and duration not in durations
        ):

            await safe_answer(

                query,

                f"❌ {duration_text(duration)} "
                f"غير مدعومة لـ {pair}",

                True
            )

            return

        context.user_data[
            "duration"
        ] = duration

        print(
            "SELECTED DURATION:",
            duration
        )

        await show_main_menu(
            query,
            context
        )

        return

    # =====================================================
    # AMOUNT
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

        try:

            amount = float(
                data.replace(
                    "amount_",
                    ""
                )
            )

        except ValueError:

            await safe_answer(
                query,
                "❌ مبلغ غير صالح.",
                True
            )

            return

        context.user_data[
            "amount"
        ] = amount

        print(
            "SELECTED AMOUNT:",
            amount
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
# ERROR HANDLER
# =========================================================

async def error_handler(
    update,
    context,
):

    error = context.error

    print("=" * 60)
    print("BOT ERROR")
    print(
        "TYPE:",
        type(error).__name__
    )
    print(
        "MESSAGE:",
        str(error)
    )
    print("=" * 60)


# =========================================================
# MAIN
# =========================================================

def main():

    app = (

        Application.builder()

        .token(
            TELEGRAM_TOKEN
        )

        .post_init(
            post_init
        )

        .connect_timeout(20)

        .read_timeout(30)

        .write_timeout(30)

        .pool_timeout(30)

        .get_updates_connect_timeout(20)

        .get_updates_read_timeout(30)

        .get_updates_write_timeout(30)

        .get_updates_pool_timeout(30)

        .build()
    )

    # -----------------------------------------------------
    # Handlers
    # -----------------------------------------------------

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

    print("=" * 60)
    print("🚀 TELEGRAM BOT STARTING")
    print("=" * 60)

    print(
        "📦 BinaryOptionsToolsV2:"
        " active_assets()"
    )

    print(
        "⚡ Asset cache enabled"
    )

    print(
        "🎨 UI enabled"
    )

    print(
        "🛡 Safe message editing enabled"
    )

    print(
        "⏱ Fast callback handling enabled"
    )

    print("=" * 60)

    # -----------------------------------------------------
    # IMPORTANT
    #
    # Removes old pending Telegram updates.
    # It does NOT allow multiple bot instances.
    # -----------------------------------------------------

    app.run_polling(
        drop_pending_updates=True,
        poll_interval=0.0,
        timeout=10,
        allowed_updates=[
            "message",
            "callback_query",
        ],
    )


# =========================================================
# ENTRY
# =========================================================

if __name__ == "__main__":

    main()
