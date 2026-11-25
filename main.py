import os
import asyncio
import logging
import sqlite3
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# --- ১. কনফিগারেশন ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "8773492019:AAEJD2EvVgUgtaNvJyD-9goqA8hknG-tY58")
ADMIN_TELEGRAM_ID = int(os.getenv("ADMIN_TELEGRAM_ID", "6819070790"))
DB_NAME = "bot_database.db"
MIN_COINS = 10000

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# --- ২. বহুভাষিক টেক্সট অভিধান ---
MESSAGES = {
    "en": {
        "welcome": (
            "<b>👋 Welcome to Sell Point IT!</b>\n\n"
            "<i>Buy or sell coins easily using the inline menu below:</i>"
        ),
        "rates_title": "📊 <b>LIVE MARKET RATES (Per 1,000 Coins):</b>\n\n",
        "active": "🟢 Active",
        "inactive": "🔴 Inactive",
        "sell_title": "🛒 <b>SELECT COIN TO SELL:</b>\n<i>(Minimum amount: 10,000 coins)</i>",
        "buy_title": "💎 <b>SELECT COIN TO BUY:</b>\n<i>(Minimum amount: 10,000 coins)</i>",
        "enter_coupon": "🔑 <b>STEP 1: Enter your Coupon Code below:</b>",
        "enter_username": (
            "📥 <b>Admin's Receiving ID:</b> <code>{acc}</code>\n\n"
            "<i>First send coins to the receiving ID above.</i>\n"
            "♻️ <b>Enter your Sender Username below:</b>"
        ),
        "enter_buy_receiver": (
            "📥 <b>Selected Coin:</b> <b>{coin}</b> (<code>{amt:,}</code> coins)\n"
            "💵 <b>Total Payable:</b> <code>{total} ৳</code>\n\n"
            "👤 <b>Enter the Receiver Username / Account ID where coins should be delivered:</b>"
        ),
        "enter_amount": "💰 <b>SELECT OR ENTER COIN AMOUNT:</b>\n<i>(Minimum 10,000)</i>",
        "enter_custom_amount": "✏️ <b>Type custom coin amount (e.g., 15000):</b>",
        "min_amount_err": "⚠️ <i>Minimum amount must be 10,000 coins.</i>",
        "num_err": "⚠️ <i>Please enter a valid number:</i>",
        "enter_method": "📱 <b>SELECT PAYMENT METHOD:</b>",
        "enter_number": "📞 <b>SELECT OR ENTER WALLET NUMBER:</b>",
        "enter_custom_number": "✏️ <b>Enter your mobile/account number:</b>",
        "enter_buy_trx": (
            "💳 <b>Send <code>{total} ৳</code> via {method}</b>\n"
            "📞 <b>Wallet Number:</b> <code>{num}</code>\n\n"
            "🧾 <b>Enter your Sender Number & TrxID (e.g., 01766952732 - TRX123456):</b>"
        ),
        "sell_success": (
            "🎉 <b>SALE REQUEST SUBMITTED!</b>\n\n"
            "🆔 <b>TX ID:</b> <code>#S{tx_id}</code>\n"
            "🪙 <b>Coin:</b> <b>{coin}</b>\n"
            "📦 <b>Amount:</b> <b>{amt:,}</b>\n"
            "📱 <b>Method:</b> <b>{method}</b> (<code>{num}</code>)\n"
            "💰 <b>Net Payable:</b> <code>{taka:.2f} ৳</code> <i>(Fee -5৳)</i>\n\n"
            "⏳ <i>Admin will verify and send payment shortly.</i>"
        ),
        "buy_success": (
            "🎉 <b>BUY REQUEST SUBMITTED!</b>\n\n"
            "🆔 <b>TX ID:</b> <code>#B{tx_id}</code>\n"
            "🪙 <b>Coin:</b> <b>{coin}</b>\n"
            "📦 <b>Amount:</b> <b>{amt:,}</b>\n"
            "👤 <b>Receiver ID:</b> <code>{receiver}</code>\n"
            "💳 <b>Payment Info:</b> <code>{pay_info}</code>\n"
            "💵 <b>Total Amount:</b> <code>{taka:.2f} ৳</code>\n\n"
            "⏳ <i>Admin will verify payment and deliver coins shortly.</i>"
        ),
        "history_title": "📜 <b>YOUR RECENT TRANSACTIONS:</b>\n\n",
        "no_history": "<i>No transaction history found.</i>",
        "leaderboard_title": "🏆 <b>TOP COIN SELLERS:</b>\n\n",
        "no_leaderboard": "<i>No completed sales yet.</i>",
        "lang_selected": "✅ <b>Language set to English!</b>",
        "lang_choose": "🌐 <b>Select your preferred language:</b>",
        "btn_buy": "💎 Buy Coins",
        "btn_sell": "🛒 Sell Coins",
        "btn_rates": "📊 Live Rates",
        "btn_history": "📜 My History",
        "btn_leaderboard": "🏆 Leaderboard",
        "btn_lang": "🌐 Language",
        "btn_support": "👨‍💻 Support",
        "btn_back": "🔙 Main Menu",
    },
    "bn": {
        "welcome": (
            "<b>👋 Sell Point IT-এ আপনাকে স্বাগতম!</b>\n\n"
            "<i>নিচের Inline মেনু বাটন ব্যবহার করে সহজেই কয়েন কিনুন বা বিক্রি করুন:</i>"
        ),
        "rates_title": "📊 <b>লাইভ মার্কেট রেট (প্রতি ১,০০০ কয়েন):</b>\n\n",
        "active": "🟢 সক্রিয়",
        "inactive": "🔴 নিষ্ক্রিয়",
        "sell_title": "🛒 <b>বিক্রি করার জন্য কয়েন বেছে নিন:</b>\n<i>(সর্বনিম্ন ১০,০০০ কয়েন)</i>",
        "buy_title": "💎 <b>কেনার জন্য কয়েন বেছে নিন:</b>\n<i>(সর্বনিম্ন ১০,০০০ কয়েন)</i>",
        "enter_coupon": "🔑 <b>ধাপ ১: আপনার Coupon Code-টি নিচে লিখুন:</b>",
        "enter_username": (
            "📥 <b>এডমিনের কয়েন রিসিভিং আইডি:</b> <code>{acc}</code>\n\n"
            "<i>প্রথমে উপরের আইডিতে কয়েন পাঠান।</i>\n"
            "♻️ <b>যে আইডি থেকে কয়েন পাঠিয়েছেন সেই Sender Username লিখুন:</b>"
        ),
        "enter_buy_receiver": (
            "📥 <b>নির্বাচিত কয়েন:</b> <b>{coin}</b> (<code>{amt:,}</code> কয়েন)\n"
            "💵 <b>মোট মূল্য:</b> <code>{total} ৳</code>\n\n"
            "👤 <b>যে ইউজারনেম বা অ্যাকাউন্ট আইডিতে কয়েন নিতে চান সেটি লিখুন:</b>"
        ),
        "enter_amount": "💰 <b>কয়েনের পরিমাণ নির্বাচন করুন বা টাইপ করুন:</b>\n<i>(সর্বনিম্ন ১০,০০০)</i>",
        "enter_custom_amount": "✏️ <b>কয়েনের পরিমাণ লিখুন (যেমন: 15000):</b>",
        "min_amount_err": "⚠️ <i>সর্বনিম্ন ১০,০০০ কয়েন হতে হবে।</i>",
        "num_err": "⚠️ <i>অনুগ্রহ করে সঠিক সংখ্যা লিখুন:</i>",
        "enter_method": "📱 <b>পেমেন্ট মেথড নির্বাচন করুন:</b>",
        "enter_number": "📞 <b>পেমেন্ট নম্বর নির্বাচন করুন বা নতুন লিখুন:</b>",
        "enter_custom_number": "✏️ <b>আপনার বিকাশ/নগদ/রকেট/উপায় নম্বর লিখুন:</b>",
        "enter_buy_trx": (
            "💳 <b>{method}-এ <code>{total} ৳</code> সেন্ড মানি করুন</b>\n"
            "📞 <b>এডমিন নম্বর:</b> <code>{num}</code>\n\n"
            "🧾 <b>আপনার সেন্ডার নম্বর ও TrxID লিখুন (যেমন: 01766952732 - TRX123456):</b>"
        ),
        "sell_success": (
            "🎉 <b>কয়েন বিক্রির রিকোয়েস্ট জমা হয়েছে!</b>\n\n"
            "🆔 <b>লেনদেন আইডি:</b> <code>#S{tx_id}</code>\n"
            "🪙 <b>কয়েন:</b> <b>{coin}</b>\n"
            "📦 <b>পরিমাণ:</b> <b>{amt:,}</b>\n"
            "📱 <b>মেথড:</b> <b>{method}</b> (<code>{num}</code>)\n"
            "💰 <b>মোট প্রাপ্য:</b> <code>{taka:.2f} ৳</code> <i>(চার্জ -৫৳)</i>\n\n"
            "⏳ <i>এডমিন যাচাই করে দ্রুত পেমেন্ট পাঠাবে।</i>"
        ),
        "buy_success": (
            "🎉 <b>কয়েন কেনার রিকোয়েস্ট জমা হয়েছে!</b>\n\n"
            "🆔 <b>লেনদেন আইডি:</b> <code>#B{tx_id}</code>\n"
            "🪙 <b>কয়েন:</b> <b>{coin}</b>\n"
            "📦 <b>পরিমাণ:</b> <b>{amt:,}</b>\n"
            "👤 <b>রিসিভার আইডি:</b> <code>{receiver}</code>\n"
            "💳 <b>পেমেন্ট তথ্য:</b> <code>{pay_info}</code>\n"
            "💵 <b>মোট টাকা:</b> <code>{taka:.2f} ৳</code>\n\n"
            "⏳ <i>এডমিন পেমেন্ট যাচাই করে দ্রুত কয়েন সেন্ড করবে।</i>"
        ),
        "history_title": "📜 <b>আপনার সাম্প্রতিক লেনদেন:</b>\n\n",
        "no_history": "<i>কোনো লেনদেনের ইতিহাস পাওয়া যায়নি।</i>",
        "leaderboard_title": "🏆 <b>সেরা কয়েন বিক্রেতা (Leaderboard):</b>\n\n",
        "no_leaderboard": "<i>এখনো কোনো সফল লেনদেন হয়নি।</i>",
        "lang_selected": "✅ <b>ভাষা বাংলা নির্বাচন করা হয়েছে!</b>",
        "lang_choose": "🌐 <b>আপনার ভাষা নির্বাচন করুন:</b>",
        "btn_buy": "💎 Buy Coins",
        "btn_sell": "🛒 Sell Coins",
        "btn_rates": "📊 Live Rates",
        "btn_history": "📜 My History",
        "btn_leaderboard": "🏆 Leaderboard",
        "btn_lang": "🌐 Language / ভাষা",
        "btn_support": "👨‍💻 Support",
        "btn_back": "🔙 মেইন মেনু",
    },
}

ADMIN_PAYMENT_NUMBERS = {
    "bKash": "01766952732",
    "Nagad": "01766952732",
    "Rocket": "01766952732",
    "Upay": "01766952732",
}

# --- ৩. SQLite ডাটাবেজ সেটআপ ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=NORMAL;")

    # coins টেবিলে sell_price এবং buy_price রাখা হয়েছে
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS coins (
            key TEXT PRIMARY KEY,
            label TEXT,
            sell_price REAL,
            buy_price REAL,
            active INTEGER,
            recv_acc TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            lang TEXT DEFAULT 'bn',
            saved_method TEXT DEFAULT NULL,
            saved_number TEXT DEFAULT NULL
        )
    """)

    # আপনার দেওয়া লাইভ রেট অনুযায়ী ডিফল্ট কয়েন তালিকা
    default_coins = [
        ("niva", "Niva Coin", 3.5, 4.0, 1, "sell_point_it"),
        ("newtop", "NewTop Coin", 21.0, 24.0, 1, "thiago___monteiroofc"),
        ("topfollows", "Topfollows Coin", 2.0, 3.0, 1, "N/A"),
        ("ns", "NS Coin", 22.5, 25.5, 1, "himelorkar019"),
        ("nexa", "Nexa Coin", 9.0, 11.0, 1, "AdminNexaID"),
        ("coinsta", "Coinsta Coin", 19.5, 22.0, 1, "AdminCoinstaID"),
        ("coinova", "Coinova Coin", 14.0, 16.5, 1, "AdminCoinovaID"),
        ("oldtop", "Oldtop Coin", 3.5, 4.5, 1, "AdminOldtopID"),
        ("manually_pro", "Manually Pro Coin", 6.0, 7.5, 1, "AdminManuallyProID"),
    ]

    for c in default_coins:
        cursor.execute("INSERT OR IGNORE INTO coins VALUES (?, ?, ?, ?, ?, ?)", c)

    # Sell transactions টেবিল
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            user_name TEXT,
            coin_label TEXT,
            coin_amount INTEGER,
            payment_method TEXT,
            account_number TEXT,
            net_taka REAL,
            coin_info TEXT,
            status TEXT
        )
    """)

    # Buy transactions টেবিল
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS buy_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            user_name TEXT,
            coin_key TEXT,
            coin_label TEXT,
            coin_amount INTEGER,
            receiver_id TEXT,
            payment_method TEXT,
            payment_info TEXT,
            total_taka REAL,
            status TEXT
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tx_user ON transactions(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_buy_user ON buy_transactions(user_id);")

    conn.commit()
    conn.close()


init_db()

# --- ৪. ডাটাবেজ হেল্পার ফাংশন ---
def add_user(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, lang) VALUES (?, 'bn')", (user_id,))
    conn.commit()
    conn.close()


def get_user_data(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT lang, saved_method, saved_number FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"lang": row[0], "saved_method": row[1], "saved_number": row[2]}
    return {"lang": "bn", "saved_method": None, "saved_number": None}


def set_user_lang(user_id: int, lang: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET lang = ? WHERE user_id = ?", (lang, user_id))
    conn.commit()
    conn.close()


def save_user_wallet(user_id: int, method: str, number: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET saved_method = ?, saved_number = ? WHERE user_id = ?",
        (method, number, user_id),
    )
    conn.commit()
    conn.close()


def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]


def get_coins():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT key, label, sell_price, buy_price, active, recv_acc FROM coins")
    rows = cursor.fetchall()
    conn.close()
    return {
        r[0]: {
            "label": r[1],
            "sell_price": r[2],
            "buy_price": r[3],
            "active": bool(r[4]),
            "recv_acc": r[5],
        }
        for r in rows
    }


def update_coin_price(key: str, field: str, new_price: float):
    if field not in ("sell_price", "buy_price"):
        return
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(f"UPDATE coins SET {field} = ? WHERE key = ?", (new_price, key))
    conn.commit()
    conn.close()


def update_coin_acc(key: str, new_acc: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE coins SET recv_acc = ? WHERE key = ?", (new_acc, key))
    conn.commit()
    conn.close()


def toggle_coin_active(key: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE coins SET active = CASE WHEN active = 1 THEN 0 ELSE 1 END WHERE key = ?",
        (key,),
    )
    conn.commit()
    conn.close()


def add_sell_transaction(user_id, user_name, coin_label, coin_amount, method, number, net_taka, coin_info):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO transactions (user_id, user_name, coin_label, coin_amount, payment_method, account_number, net_taka, coin_info, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Pending')
        """,
        (user_id, user_name, coin_label, coin_amount, method, number, net_taka, coin_info),
    )
    tx_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return tx_id


def add_buy_transaction(user_id, user_name, coin_key, coin_label, coin_amount, receiver_id, method, pay_info, total_taka):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO buy_transactions (user_id, user_name, coin_key, coin_label, coin_amount, receiver_id, payment_method, payment_info, total_taka, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending')
        """,
        (user_id, user_name, coin_key, coin_label, coin_amount, receiver_id, method, pay_info, total_taka),
    )
    tx_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return tx_id


def update_sell_tx_status(tx_id: int, status: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE transactions SET status = ? WHERE id = ?", (status, tx_id))
    conn.commit()
    conn.close()


def update_buy_tx_status(tx_id: int, status: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE buy_transactions SET status = ? WHERE id = ?", (status, tx_id))
    conn.commit()
    conn.close()


def get_sell_tx(tx_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, coin_label, coin_amount, payment_method, account_number, net_taka, status, coin_info FROM transactions WHERE id = ?",
        (tx_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return row


def get_buy_tx(tx_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, coin_key, coin_label, coin_amount, receiver_id, payment_method, payment_info, total_taka, status FROM buy_transactions WHERE id = ?",
        (tx_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return row


def get_user_combined_history(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT 'SELL' as type, id, coin_label, coin_amount, net_taka, status
        FROM transactions WHERE user_id = ?
        UNION ALL
        SELECT 'BUY' as type, id, coin_label, coin_amount, total_taka, status
        FROM buy_transactions WHERE user_id = ?
        ORDER BY id DESC LIMIT 10
        """,
        (user_id, user_id),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_leaderboard():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT user_name, SUM(coin_amount) as total_coins, COUNT(id) as total_sales
        FROM transactions
        WHERE status = 'Accepted'
        GROUP BY user_id
        ORDER BY total_coins DESC
        LIMIT 10
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


# --- ৫. Inline Keyboard Builders ---
def get_main_inline_keyboard(lang: str = "bn"):
    txt = MESSAGES[lang]
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(txt["btn_buy"], callback_data="menu_buy"),
                InlineKeyboardButton(txt["btn_sell"], callback_data="menu_sell"),
            ],
            [
                InlineKeyboardButton(txt["btn_rates"], callback_data="menu_rates"),
                InlineKeyboardButton(txt["btn_history"], callback_data="menu_history"),
            ],
            [
                InlineKeyboardButton(txt["btn_leaderboard"], callback_data="menu_leaderboard"),
                InlineKeyboardButton(txt["btn_lang"], callback_data="menu_lang"),
            ],
            [
                InlineKeyboardButton(txt["btn_support"], callback_data="menu_support"),
            ],
        ]
    )


def get_back_keyboard(lang: str = "bn"):
    txt = MESSAGES[lang]
    return InlineKeyboardMarkup([[InlineKeyboardButton(txt["btn_back"], callback_data="menu_main")]])


def get_language_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🇺🇸 English", callback_data="set_lang_en"),
                InlineKeyboardButton("🇧🇩 বাংলা (Bangla)", callback_data="set_lang_bn"),
            ],
            [InlineKeyboardButton("🔙 Back / ফিরে যান", callback_data="menu_main")],
        ]
    )


def get_coin_selection_keyboard(mode: str, lang: str = "bn"):
    # mode: "sell" অথবা "buy"
    coins = get_coins()
    keyboard = []
    for k, c in coins.items():
        if c["active"]:
            rate = c["sell_price"] if mode == "sell" else c["buy_price"]
            prefix = "Sell" if mode == "sell" else "Buy"
            keyboard.append(
                [InlineKeyboardButton(f"{prefix} {c['label']} ({rate}৳/1K)", callback_data=f"{mode}_coin_{k}")]
            )
    keyboard.append([InlineKeyboardButton(MESSAGES[lang]["btn_back"], callback_data="menu_main")])
    return InlineKeyboardMarkup(keyboard)


def get_amount_keyboard(mode: str, lang: str = "bn"):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("💎 10,000", callback_data=f"{mode}_amt_10000"),
                InlineKeyboardButton("💎 25,000", callback_data=f"{mode}_amt_25000"),
            ],
            [
                InlineKeyboardButton("💎 50,000", callback_data=f"{mode}_amt_50000"),
                InlineKeyboardButton("💎 100,000", callback_data=f"{mode}_amt_100000"),
            ],
            [InlineKeyboardButton("✏️ Custom Amount", callback_data=f"{mode}_amt_custom")],
            [InlineKeyboardButton(MESSAGES[lang]["btn_back"], callback_data="menu_main")],
        ]
    )


def get_method_keyboard(mode: str, lang: str = "bn"):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🌸 bKash", callback_data=f"{mode}_method_bKash"),
                InlineKeyboardButton("🟠 Nagad", callback_data=f"{mode}_method_Nagad"),
            ],
            [
                InlineKeyboardButton("🚀 Rocket", callback_data=f"{mode}_method_Rocket"),
                InlineKeyboardButton("🟡 Upay", callback_data=f"{mode}_method_Upay"),
            ],
            [InlineKeyboardButton(MESSAGES[lang]["btn_back"], callback_data="menu_main")],
        ]
    )


def get_sell_number_keyboard(saved_method, saved_number, lang: str = "bn"):
    keyboard = []
    if saved_method and saved_number:
        keyboard.append(
            [InlineKeyboardButton(f"⚡ Saved: {saved_method} ({saved_number})", callback_data="sell_num_saved")]
        )
    keyboard.append([InlineKeyboardButton("✏️ Enter New Number", callback_data="sell_num_new")])
    keyboard.append([InlineKeyboardButton(MESSAGES[lang]["btn_back"], callback_data="menu_main")])
    return InlineKeyboardMarkup(keyboard)


# --- ৬. স্টার্ট ও এডমিন কমান্ড ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user(user_id)
    context.user_data.clear()
    u_data = get_user_data(user_id)
    lang = u_data["lang"]
    txt = MESSAGES[lang]

    if update.message:
        await update.message.reply_text(
            txt["welcome"],
            reply_markup=get_main_inline_keyboard(lang),
            parse_mode="HTML",
        )


def get_admin_keyboard():
    coins = get_coins()
    keyboard = []
    for k, c in coins.items():
        st = "🟢" if c["active"] else "🔴"
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{st} {c['label']} (S:{c['sell_price']}৳ | B:{c['buy_price']}৳)",
                    callback_data=f"adm_manage_{k}",
                )
            ]
        )
    keyboard.append([InlineKeyboardButton("📢 Send Public Broadcast", callback_data="adm_broadcast")])
    return InlineKeyboardMarkup(keyboard)


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_TELEGRAM_ID:
        return
    await update.message.reply_text(
        "⚙️ <b>Admin Panel - Buy/Sell Dynamic Control</b>\n\nSelect a coin to manage:",
        reply_markup=get_admin_keyboard(),
        parse_mode="HTML",
    )


# --- ৭. Inline Callback হ্যান্ডলার ---
async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    add_user(user_id)
    u_data = get_user_data(user_id)
    lang = u_data["lang"]
    txt = MESSAGES[lang]

    # --- মেইন Inline মেনু নেভিগেশন ---
    if data == "menu_main":
        context.user_data.clear()
        await query.edit_message_text(
            txt["welcome"],
            reply_markup=get_main_inline_keyboard(lang),
            parse_mode="HTML",
        )

    elif data == "menu_buy":
        context.user_data["trade_mode"] = "buy"
        context.user_data["step"] = None
        await query.edit_message_text(
            txt["buy_title"],
            reply_markup=get_coin_selection_keyboard("buy", lang),
            parse_mode="HTML",
        )

    elif data == "menu_sell":
        context.user_data["trade_mode"] = "sell"
        context.user_data["step"] = None
        await query.edit_message_text(
            txt["sell_title"],
            reply_markup=get_coin_selection_keyboard("sell", lang),
            parse_mode="HTML",
        )

    elif data == "menu_rates":
        coins = get_coins()
        text = txt["rates_title"]
        for _, c in coins.items():
            st = txt["active"] if c["active"] else txt["inactive"]
            text += (
                f"• <b>{c['label']}</b> ({st})\n"
                f"   🛒 Sell: <code>{c['sell_price']} ৳</code> | 💎 Buy: <code>{c['buy_price']} ৳</code>\n"
            )
        await query.edit_message_text(text, reply_markup=get_back_keyboard(lang), parse_mode="HTML")

    elif data == "menu_history":
        rows = get_user_combined_history(user_id)
        text = txt["history_title"]
        if not rows:
            text += txt["no_history"]
        else:
            for r_type, r_id, c_label, c_amt, taka, status in rows:
                st_icon = "⏳" if status == "Pending" else ("✅" if status == "Accepted" else "❌")
                tag = "🛒 SELL" if r_type == "SELL" else "💎 BUY"
                prefix = "S" if r_type == "SELL" else "B"
                text += (
                    f"{tag} | <code>#{prefix}{r_id}</code> | <b>{c_label}</b>\n"
                    f"📦 {c_amt:,} Coins | 💰 {taka:.2f} ৳ | {st_icon} <b>{status}</b>\n"
                    f"━━━━━━━━━━━━━━━\n"
                )
        await query.edit_message_text(text, reply_markup=get_back_keyboard(lang), parse_mode="HTML")

    elif data == "menu_leaderboard":
        lb = get_leaderboard()
        text = txt["leaderboard_title"]
        if not lb:
            text += txt["no_leaderboard"]
        else:
            for idx, (u_name, t_coins, t_sales) in enumerate(lb, start=1):
                text += f"{idx}. <b>{u_name}</b> — {t_coins:,} Coins ({t_sales} Sales)\n"
        await query.edit_message_text(text, reply_markup=get_back_keyboard(lang), parse_mode="HTML")

    elif data == "menu_lang":
        await query.edit_message_text(txt["lang_choose"], reply_markup=get_language_keyboard(), parse_mode="HTML")

    elif data == "menu_support":
        text = (
            "👨‍💻 <b>Support Center:</b>\n"
            "Admin: @educationpointbd24\n"
            "Channel: @EducationPointBD"
        )
        await query.edit_message_text(text, reply_markup=get_back_keyboard(lang), parse_mode="HTML")

    elif data.startswith("set_lang_"):
        new_lang = data.split("_")[2]
        set_user_lang(user_id, new_lang)
        new_txt = MESSAGES[new_lang]
        await query.edit_message_text(
            new_txt["lang_selected"] + "\n\n" + new_txt["welcome"],
            reply_markup=get_main_inline_keyboard(new_lang),
            parse_mode="HTML",
        )

    # --- BUY COIN FLOW ---
    elif data.startswith("buy_coin_"):
        key = data.replace("buy_coin_", "")
        coins = get_coins()
        if key not in coins or not coins[key]["active"]:
            return
        context.user_data["trade_mode"] = "buy"
        context.user_data["selected_coin"] = key
        await query.edit_message_text(
            f"💎 <b>{coins[key]['label']}</b> (Rate: <code>{coins[key]['buy_price']} ৳</code> / 1K)\n\n" + txt["enter_amount"],
            reply_markup=get_amount_keyboard("buy", lang),
            parse_mode="HTML",
        )

    elif data.startswith("buy_amt_"):
        val = data.replace("buy_amt_", "")
        if val == "custom":
            context.user_data["step"] = "BUY_AWAITING_CUSTOM_AMOUNT"
            await query.edit_message_text(
                txt["enter_custom_amount"], reply_markup=get_back_keyboard(lang), parse_mode="HTML"
            )
        else:
            amt = int(val)
            context.user_data["amount"] = amt
            coins = get_coins()
            c = coins[context.user_data["selected_coin"]]
            total_taka = (amt / 1000) * c["buy_price"]
            context.user_data["total_taka"] = total_taka
            context.user_data["step"] = "BUY_AWAITING_RECEIVER"
            await query.edit_message_text(
                txt["enter_buy_receiver"].format(coin=c["label"], amt=amt, total=f"{total_taka:.2f}"),
                reply_markup=get_back_keyboard(lang),
                parse_mode="HTML",
            )

    elif data.startswith("buy_method_"):
        method = data.replace("buy_method_", "")
        context.user_data["method"] = method
        context.user_data["step"] = "BUY_AWAITING_TRX_INFO"
        total_taka = context.user_data.get("total_taka", 0)
        admin_num = ADMIN_PAYMENT_NUMBERS.get(method, "01700000000")
        await query.edit_message_text(
            txt["enter_buy_trx"].format(method=method, total=f"{total_taka:.2f}", num=admin_num),
            reply_markup=get_back_keyboard(lang),
            parse_mode="HTML",
        )

    # --- SELL COIN FLOW ---
    elif data.startswith("sell_coin_"):
        key = data.replace("sell_coin_", "")
        coins = get_coins()
        c = coins.get(key)
        if not c or not c["active"]:
            return
        context.user_data["trade_mode"] = "sell"
        context.user_data["selected_coin"] = key

        if key == "topfollows":
            context.user_data["step"] = "SELL_AWAITING_COUPON"
            await query.edit_message_text(txt["enter_coupon"], reply_markup=get_back_keyboard(lang), parse_mode="HTML")
        else:
            context.user_data["step"] = "SELL_AWAITING_USERNAME"
            await query.edit_message_text(
                txt["enter_username"].format(acc=c.get("recv_acc", "N/A")),
                reply_markup=get_back_keyboard(lang),
                parse_mode="HTML",
            )

    elif data.startswith("sell_amt_"):
        val = data.replace("sell_amt_", "")
        if val == "custom":
            context.user_data["step"] = "SELL_AWAITING_CUSTOM_AMOUNT"
            await query.edit_message_text(
                txt["enter_custom_amount"], reply_markup=get_back_keyboard(lang), parse_mode="HTML"
            )
        else:
            context.user_data["amount"] = int(val)
            context.user_data["step"] = "SELL_AWAITING_METHOD"
            await query.edit_message_text(
                txt["enter_method"], reply_markup=get_method_keyboard("sell", lang), parse_mode="HTML"
            )

    elif data.startswith("sell_method_"):
        m_name = data.replace("sell_method_", "")
        context.user_data["method"] = m_name
        context.user_data["step"] = "SELL_AWAITING_NUMBER"
        await query.edit_message_text(
            txt["enter_number"],
            reply_markup=get_sell_number_keyboard(u_data["saved_method"], u_data["saved_number"], lang),
            parse_mode="HTML",
        )

    elif data == "sell_num_saved":
        s_method = u_data["saved_method"]
        s_num = u_data["saved_number"]
        await finalize_sell_transaction(update, context, s_method, s_num, user_id, lang)

    elif data == "sell_num_new":
        context.user_data["step"] = "SELL_AWAITING_CUSTOM_NUMBER"
        await query.edit_message_text(
            txt["enter_custom_number"], reply_markup=get_back_keyboard(lang), parse_mode="HTML"
        )

    # --- ADMIN SELL ORDER ACTIONS ---
    elif data.startswith("sell_acc_") or data.startswith("sell_rej_"):
        if user_id != ADMIN_TELEGRAM_ID:
            return
        parts = data.split("_")
        action = parts[1]
        tx_id = int(parts[2])

        if action == "rej":
            update_sell_tx_status(tx_id, "Rejected")
            tx = get_sell_tx(tx_id)
            if tx:
                await context.bot.send_message(
                    chat_id=tx[0],
                    text=f"❌ <b>Your sell request (#S{tx_id}) was rejected.</b>",
                    parse_mode="HTML",
                )
            await query.edit_message_text(query.message.text + "\n\n❌ <b>SELL REJECTED</b>", parse_mode="HTML")

        elif action == "acc":
            context.user_data["pending_sell_tx_id"] = tx_id
            context.user_data["admin_step"] = "AWAITING_SELL_PROOF"
            await query.edit_message_text(
                query.message.text + "\n\n📸 <b>পেমেন্ট স্ক্রিনশটটি এই চ্যাটে সেন্ড করুন:</b>",
                parse_mode="HTML",
            )

    # --- ADMIN BUY ORDER ACTIONS ---
    elif data.startswith("buy_acc_") or data.startswith("buy_rej_"):
        if user_id != ADMIN_TELEGRAM_ID:
            return
        parts = data.split("_")
        action = parts[1]
        tx_id = int(parts[2])
        tx = get_buy_tx(tx_id)
        if not tx:
            return

        if action == "rej":
            update_buy_tx_status(tx_id, "Rejected")
            await context.bot.send_message(
                chat_id=tx[0],
                text=f"❌ <b>Your buy request (#B{tx_id}) was rejected.</b> Please contact support if payment was sent.",
                parse_mode="HTML",
            )
            await query.edit_message_text(query.message.text + "\n\n❌ <b>BUY REJECTED</b>", parse_mode="HTML")

        elif action == "acc":
            update_buy_tx_status(tx_id, "Accepted")
            await context.bot.send_message(
                chat_id=tx[0],
                text=(
                    f"✅ <b>Coin Purchase Approved & Delivered!</b>\n\n"
                    f"🆔 <b>TX ID:</b> <code>#B{tx_id}</code>\n"
                    f"🪙 <b>Coin:</b> <b>{tx[2]}</b>\n"
                    f"📦 <b>Amount:</b> <code>{tx[3]:,}</code>\n"
                    f"👤 <b>Receiver ID:</b> <code>{tx[4]}</code>\n"
                    f"💵 <b>Paid:</b> <code>{tx[7]:.2f} ৳</code>"
                ),
                parse_mode="HTML",
            )
            await query.edit_message_text(query.message.text + "\n\n✅ <b>BUY ACCEPTED & DELIVERED</b>", parse_mode="HTML")

    # --- ADMIN COIN MANAGEMENT ---
    elif data.startswith("adm_manage_"):
        if user_id != ADMIN_TELEGRAM_ID:
            return
        key = data.replace("adm_manage_", "")
        coins = get_coins()
        c = coins[key]
        st_txt = "Active 🟢" if c["active"] else "Inactive 🔴"
        text = (
            f"⚙️ <b>Manage Coin:</b> {c['label']}\n"
            f"🛒 Sell Rate: <code>{c['sell_price']} ৳</code>\n"
            f"💎 Buy Rate: <code>{c['buy_price']} ৳</code>\n"
            f"📥 Recv ID: <code>{c['recv_acc']}</code>\n"
            f"📊 Status: {st_txt}"
        )
        btn = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("✏️ Edit Sell Rate", callback_data=f"adm_sp_{key}"),
                    InlineKeyboardButton("✏️ Edit Buy Rate", callback_data=f"adm_bp_{key}"),
                ],
                [
                    InlineKeyboardButton("✏️ Edit Recv ID", callback_data=f"adm_a_{key}"),
                    InlineKeyboardButton(
                        f"🔄 {'Disable' if c['active'] else 'Enable'}",
                        callback_data=f"adm_t_{key}",
                    ),
                ],
                [InlineKeyboardButton("🔙 Back to Admin", callback_data="adm_back")],
            ]
        )
        await query.edit_message_text(text, reply_markup=btn, parse_mode="HTML")

    elif data == "adm_back":
        if user_id != ADMIN_TELEGRAM_ID:
            return
        await query.edit_message_text(
            "⚙️ <b>Admin Panel - Buy/Sell Dynamic Control</b>",
            reply_markup=get_admin_keyboard(),
            parse_mode="HTML",
        )

    elif data.startswith("adm_t_"):
        if user_id != ADMIN_TELEGRAM_ID:
            return
        key = data.replace("adm_t_", "")
        toggle_coin_active(key)
        await query.answer("Status updated!")
        query.data = f"adm_manage_{key}"
        await handle_callbacks(update, context)

    elif data.startswith("adm_sp_"):
        if user_id != ADMIN_TELEGRAM_ID:
            return
        context.user_data["admin_coin_key"] = data.replace("adm_sp_", "")
        context.user_data["admin_step"] = "AWAITING_SELL_PRICE"
        await query.edit_message_text("✏️ Enter new SELL price per 1,000 coins:")

    elif data.startswith("adm_bp_"):
        if user_id != ADMIN_TELEGRAM_ID:
            return
        context.user_data["admin_coin_key"] = data.replace("adm_bp_", "")
        context.user_data["admin_step"] = "AWAITING_BUY_PRICE"
        await query.edit_message_text("✏️ Enter new BUY price per 1,000 coins:")

    elif data.startswith("adm_a_"):
        if user_id != ADMIN_TELEGRAM_ID:
            return
        context.user_data["admin_coin_key"] = data.replace("adm_a_", "")
        context.user_data["admin_step"] = "AWAITING_NEW_ACC"
        await query.edit_message_text("✏️ Enter new Receiving ID/Username:")

    elif data == "adm_broadcast":
        if user_id != ADMIN_TELEGRAM_ID:
            return
        context.user_data["admin_step"] = "AWAITING_BROADCAST_MSG"
        await query.edit_message_text("📢 <b>Enter broadcast message:</b>", parse_mode="HTML")


# --- ৮. টেক্সট ও ফটো ইনপুট হ্যান্ডলার ---
async def handle_inputs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user_id = update.effective_user.id
    add_user(user_id)
    u_data = get_user_data(user_id)
    lang = u_data["lang"]
    txt = MESSAGES[lang]
    text_input = (update.message.text or "").strip()

    admin_step = context.user_data.get("admin_step")
    step = context.user_data.get("step")

    # --- Admin Proof Photo for Sell Order ---
    if user_id == ADMIN_TELEGRAM_ID and admin_step == "AWAITING_SELL_PROOF" and update.message.photo:
        tx_id = context.user_data.get("pending_sell_tx_id")
        photo_file_id = update.message.photo[-1].file_id
        update_sell_tx_status(tx_id, "Accepted")
        tx = get_sell_tx(tx_id)
        if tx:
            caption = (
                f"✅ <b>Coin Sale Accepted & Payment Sent!</b>\n\n"
                f"🆔 <b>TX ID:</b> <code>#S{tx_id}</code>\n"
                f"🪙 <b>Coin:</b> {tx[1]}\n"
                f"📦 <b>Amount:</b> {tx[2]:,}\n"
                f"📱 <b>Wallet:</b> {tx[3]} (<code>{tx[4]}</code>)\n"
                f"💰 <b>Paid:</b> <code>{tx[5]:.2f} ৳</code>"
            )
            await context.bot.send_photo(chat_id=tx[0], photo=photo_file_id, caption=caption, parse_mode="HTML")
        context.user_data["admin_step"] = None
        await update.message.reply_text("✅ <b>Payment proof sent to user!</b>", parse_mode="HTML")
        return

    # --- Admin Price & Account Updates ---
    if user_id == ADMIN_TELEGRAM_ID and admin_step in ("AWAITING_SELL_PRICE", "AWAITING_BUY_PRICE") and text_input:
        try:
            new_p = float(text_input)
            key = context.user_data.get("admin_coin_key")
            field = "sell_price" if admin_step == "AWAITING_SELL_PRICE" else "buy_price"
            update_coin_price(key, field, new_p)
            context.user_data["admin_step"] = None
            await update.message.reply_text("✅ <b>Price updated!</b>", reply_markup=get_admin_keyboard(), parse_mode="HTML")
        except ValueError:
            await update.message.reply_text(txt["num_err"], parse_mode="HTML")
        return

    if user_id == ADMIN_TELEGRAM_ID and admin_step == "AWAITING_NEW_ACC" and text_input:
        key = context.user_data.get("admin_coin_key")
        update_coin_acc(key, text_input)
        context.user_data["admin_step"] = None
        await update.message.reply_text("✅ <b>Receiving ID updated!</b>", reply_markup=get_admin_keyboard(), parse_mode="HTML")
        return

    if user_id == ADMIN_TELEGRAM_ID and admin_step == "AWAITING_BROADCAST_MSG" and text_input:
        users = get_all_users()
        sent = 0
        for uid in users:
            try:
                await context.bot.send_message(
                    chat_id=uid,
                    text=f"📢 <b>Announcement:</b>\n\n{text_input}",
                    parse_mode="HTML",
                )
                sent += 1
            except Exception:
                pass
        context.user_data["admin_step"] = None
        await update.message.reply_text(f"✅ <b>Broadcast sent to {sent} users.</b>", reply_markup=get_admin_keyboard(), parse_mode="HTML")
        return

    # --- BUY FLOW INPUTS ---
    if step == "BUY_AWAITING_CUSTOM_AMOUNT" and text_input:
        try:
            amt = int(text_input)
            if amt < MIN_COINS:
                await update.message.reply_text(txt["min_amount_err"], reply_markup=get_back_keyboard(lang), parse_mode="HTML")
                return
            context.user_data["amount"] = amt
            coins = get_coins()
            c = coins[context.user_data["selected_coin"]]
            total_taka = (amt / 1000) * c["buy_price"]
            context.user_data["total_taka"] = total_taka
            context.user_data["step"] = "BUY_AWAITING_RECEIVER"
            await update.message.reply_text(
                txt["enter_buy_receiver"].format(coin=c["label"], amt=amt, total=f"{total_taka:.2f}"),
                reply_markup=get_back_keyboard(lang),
                parse_mode="HTML",
            )
        except ValueError:
            await update.message.reply_text(txt["num_err"], reply_markup=get_back_keyboard(lang), parse_mode="HTML")
        return

    if step == "BUY_AWAITING_RECEIVER" and text_input:
        context.user_data["receiver_id"] = text_input
        context.user_data["step"] = "BUY_SELECT_METHOD"
        await update.message.reply_text(
            txt["enter_method"],
            reply_markup=get_method_keyboard("buy", lang),
            parse_mode="HTML",
        )
        return

    if step == "BUY_AWAITING_TRX_INFO" and text_input:
        await finalize_buy_transaction(update, context, text_input, user_id, lang)
        return

    # --- SELL FLOW INPUTS ---
    if step in ("SELL_AWAITING_USERNAME", "SELL_AWAITING_COUPON") and text_input:
        context.user_data["coin_info"] = text_input
        context.user_data["step"] = "SELL_AWAITING_AMOUNT"
        await update.message.reply_text(
            txt["enter_amount"],
            reply_markup=get_amount_keyboard("sell", lang),
            parse_mode="HTML",
        )
        return

    if step == "SELL_AWAITING_CUSTOM_AMOUNT" and text_input:
        try:
            amt = int(text_input)
            if amt < MIN_COINS:
                await update.message.reply_text(txt["min_amount_err"], reply_markup=get_back_keyboard(lang), parse_mode="HTML")
                return
            context.user_data["amount"] = amt
            context.user_data["step"] = "SELL_AWAITING_METHOD"
            await update.message.reply_text(
                txt["enter_method"],
                reply_markup=get_method_keyboard("sell", lang),
                parse_mode="HTML",
            )
        except ValueError:
            await update.message.reply_text(txt["num_err"], reply_markup=get_back_keyboard(lang), parse_mode="HTML")
        return

    if step == "SELL_AWAITING_CUSTOM_NUMBER" and text_input:
        method = context.user_data.get("method", "bKash")
        save_user_wallet(user_id, method, text_input)
        await finalize_sell_transaction(update, context, method, text_input, user_id, lang)
        return


# --- ৯. Sell ও Buy লেনদেন ফাইনাল প্রসেসর ---
async def finalize_sell_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE, method: str, num: str, user_id: int, lang: str):
    txt = MESSAGES[lang]
    coins = get_coins()
    key = context.user_data.get("selected_coin")
    c = coins[key]
    amt = context.user_data.get("amount", MIN_COINS)
    coin_info = context.user_data.get("coin_info", "N/A")

    net_taka = max(0.0, (amt / 1000) * c["sell_price"] - 5.0)
    user_obj = update.effective_user
    tx_id = add_sell_transaction(user_id, user_obj.first_name, c["label"], amt, method, num, net_taka, coin_info)

    context.user_data.clear()

    user_msg = txt["sell_success"].format(
        tx_id=tx_id, coin=c["label"], amt=amt, method=method, num=num, taka=net_taka
    )
    target_msg = update.callback_query.message if update.callback_query else update.message
    await target_msg.reply_text(user_msg, reply_markup=get_main_inline_keyboard(lang), parse_mode="HTML")

    admin_msg = (
        f"🚨 <b>NEW COIN SELL REQUEST!</b>\n\n"
        f"🆔 <b>TX ID:</b> <code>#S{tx_id}</code>\n"
        f"👤 <b>User:</b> {user_obj.first_name} (<code>{user_id}</code>)\n"
        f"🪙 <b>Coin:</b> {c['label']}\n"
        f"ℹ️ <b>Info:</b> <code>{coin_info}</code>\n"
        f"📦 <b>Amount:</b> {amt:,}\n"
        f"📱 <b>Pay To:</b> {method} (<code>{num}</code>)\n"
        f"💰 <b>Payable:</b> <code>{net_taka:.2f} ৳</code>"
    )
    btn = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Accept & Send Proof", callback_data=f"sell_acc_{tx_id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"sell_rej_{tx_id}"),
            ]
        ]
    )
    await context.bot.send_message(chat_id=ADMIN_TELEGRAM_ID, text=admin_msg, reply_markup=btn, parse_mode="HTML")


async def finalize_buy_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE, pay_info: str, user_id: int, lang: str):
    txt = MESSAGES[lang]
    coins = get_coins()
    key = context.user_data.get("selected_coin")
    c = coins[key]
    amt = context.user_data.get("amount", MIN_COINS)
    receiver_id = context.user_data.get("receiver_id", "N/A")
    method = context.user_data.get("method", "bKash")
    total_taka = context.user_data.get("total_taka", (amt / 1000) * c["buy_price"])

    user_obj = update.effective_user
    tx_id = add_buy_transaction(
        user_id, user_obj.first_name, key, c["label"], amt, receiver_id, method, pay_info, total_taka
    )

    context.user_data.clear()

    user_msg = txt["buy_success"].format(
        tx_id=tx_id,
        coin=c["label"],
        amt=amt,
        receiver=receiver_id,
        pay_info=pay_info,
        taka=total_taka,
    )
    await update.message.reply_text(user_msg, reply_markup=get_main_inline_keyboard(lang), parse_mode="HTML")

    admin_msg = (
        f"💎 <b>NEW COIN BUY REQUEST!</b>\n\n"
        f"🆔 <b>TX ID:</b> <code>#B{tx_id}</code>\n"
        f"👤 <b>User:</b> {user_obj.first_name} (<code>{user_id}</code>)\n"
        f"🪙 <b>Coin:</b> {c['label']}\n"
        f"📦 <b>Amount:</b> {amt:,}\n"
        f"👤 <b>Deliver To ID:</b> <code>{receiver_id}</code>\n"
        f"📱 <b>Method:</b> {method}\n"
        f"🧾 <b>Sender/TrxID:</b> <code>{pay_info}</code>\n"
        f"💵 <b>Total Paid:</b> <code>{total_taka:.2f} ৳</code>"
    )
    btn = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Approve & Deliver", callback_data=f"buy_acc_{tx_id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"buy_rej_{tx_id}"),
            ]
        ]
    )
    await context.bot.send_message(chat_id=ADMIN_TELEGRAM_ID, text=admin_msg, reply_markup=btn, parse_mode="HTML")


# --- ১০. বট মেইন এক্সিকিউশন ---
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(handle_callbacks))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_inputs))

    print("Bot is running with Inline Buy & Sell Coin support...")
    app.run_polling()


if __name__ == "__main__":
    main()
