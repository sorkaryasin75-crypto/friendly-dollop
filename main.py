import os
import asyncio
import logging
import sqlite3
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
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

# --- ১. কনফিগারেশন (Railway Environment Variables support) ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "8773492019:AAEJD2EvVgUgtaNvJyD-9goqA8hknG-tY58")
ADMIN_TELEGRAM_ID = int(os.getenv("ADMIN_TELEGRAM_ID", "6819070790"))
DB_NAME = "bot_database.db"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# --- ২. বহুভাষিক টেক্সট অভিধান (Telegram Custom Premium Emojis Supported) ---
MESSAGES = {
    "en": {
        "welcome": (
            "<b><tg-emoji emoji-id='5368324170671202286'>👋</tg-emoji> Welcome to Sell Point IT!</b>\n\n"
            "<i>Please select an option from the menu keyboard below to start trading:</i>"
        ),
        "rates_title": "<tg-emoji emoji-id='5368324170671202286'>📊</tg-emoji> <b>LIVE MARKET RATES (Per 1000 Coins):</b>\n\n",
        "active": "🟢 Active",
        "inactive": "🔴 Inactive",
        "sell_title": "<tg-emoji emoji-id='5368324170671202286'>🛒</tg-emoji> <b>SELECT COIN TO SELL:</b>\n<i>(Minimum amount: 10,000)</i>",
        "enter_coupon": "<tg-emoji emoji-id='5368324170671202286'>🔑</tg-emoji> <b>STEP 1: Enter your Coupon Code below:</b>",
        "enter_username": (
            "<tg-emoji emoji-id='5368324170671202286'>📥</tg-emoji> <b>Admin's Receiving ID:</b> <code>{acc}</code>\n\n"
            "<i>First send coins to the receiving ID above.</i>\n"
            "<tg-emoji emoji-id='5368324170671202286'>♻️</tg-emoji> <b>Enter your Sender Username below:</b>"
        ),
        "enter_amount": "<tg-emoji emoji-id='5368324170671202286'>💰</tg-emoji> <b>SELECT OR ENTER COIN AMOUNT:</b>\n<i>(Minimum 10,000)</i>",
        "enter_custom_amount": "<tg-emoji emoji-id='5368324170671202286'>✏️</tg-emoji> <b>Type custom coin amount (e.g., 15000):</b>",
        "min_amount_err": "⚠️ <i>Minimum amount must be 10,000 coins.</i>",
        "num_err": "⚠️ <i>Please enter a valid number:</i>",
        "enter_method": "<tg-emoji emoji-id='5368324170671202286'>📱</tg-emoji> <b>SELECT PAYMENT METHOD:</b>",
        "enter_number": "<tg-emoji emoji-id='5368324170671202286'>📞</tg-emoji> <b>SELECT OR ENTER WALLET NUMBER:</b>",
        "enter_custom_number": "<tg-emoji emoji-id='5368324170671202286'>✏️</tg-emoji> <b>Enter your mobile/account number:</b>",
        "tx_success": (
            "<b>┌─────────────────────┐</b>\n"
            "<b>│ <tg-emoji emoji-id='5368324170671202286'>🎉</tg-emoji> SALE REQUEST SUBMITTED! │</b>\n"
            "<b>└─────────────────────┘</b>\n\n"
            "<tg-emoji emoji-id='5368324170671202286'>🆔</tg-emoji> <b>TRANSACTION ID :</b> <code>#{tx_id}</code>\n"
            "<tg-emoji emoji-id='5368324170671202286'>🪙</tg-emoji> <b>COIN TYPE      :</b> <b>{coin}</b>\n"
            "<tg-emoji emoji-id='5368324170671202286'>📦</tg-emoji> <b>COIN AMOUNT    :</b> <b>{amt:,}</b>\n"
            "<tg-emoji emoji-id='5368324170671202286'>📱</tg-emoji> <b>PAYMENT METHOD :</b> <b>{method}</b>\n"
            "<tg-emoji emoji-id='5368324170671202286'>📞</tg-emoji> <b>WALLET NUMBER  :</b> <code>{num}</code>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "<tg-emoji emoji-id='5368324170671202286'>💰</tg-emoji> <b>NET PAYABLE    :</b> <code>{taka} ৳</code> <i>(Fee -5৳)</i>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "<tg-emoji emoji-id='5368324170671202286'>⏳</tg-emoji> <i>Admin will verify and send payment shortly!</i>"
        ),
        "history_title": "<tg-emoji emoji-id='5368324170671202286'>📜</tg-emoji> <b>YOUR TRANSACTION HISTORY:</b>\n\n",
        "no_history": "<i>No transaction history found.</i>",
        "leaderboard_title": "<tg-emoji emoji-id='5368324170671202286'>🏆</tg-emoji> <b>PUBLIC LEADERBOARD (Top Sellers):</b>\n\n",
        "no_leaderboard": "<i>No successful transactions yet.</i>",
        "lang_selected": "✅ <b>Language set to English!</b>",
        "lang_choose": "<tg-emoji emoji-id='5368324170671202286'>🌐</tg-emoji> <b>Select your preferred language:</b>",
        "btn_sell": "🛒 Sell Coins",
        "btn_rates": "📊 Live Rates",
        "btn_history": "📜 My History",
        "btn_leaderboard": "🏆 Leaderboard",
        "btn_lang": "🌐 Language / ভাষা",
        "btn_support": "👨‍💻 Support"
    },
    "bn": {
        "welcome": (
            "<b><tg-emoji emoji-id='5368324170671202286'>👋</tg-emoji> Sell Point IT-এ আপনাকে স্বাগতম!</b>\n\n"
            "<i>লেনদেন শুরু করতে নিচের মেনু কিবোর্ড বাটনগুলো ব্যবহার করুন:</i>"
        ),
        "rates_title": "<tg-emoji emoji-id='5368324170671202286'>📊</tg-emoji> <b>লাইভ মার্কেট রেট (প্রতি ১০০০ কয়েন):</b>\n\n",
        "active": "🟢 সক্রিয়",
        "inactive": "🔴 নিষ্ক্রিয়",
        "sell_title": "<tg-emoji emoji-id='5368324170671202286'>🛒</tg-emoji> <b>কোন কয়েনটি বিক্রি করতে চান বেছে নিন:</b>\n<i>(সর্বনিম্ন ১০,০০০ কয়েন)</i>",
        "enter_coupon": "<tg-emoji emoji-id='5368324170671202286'>🔑</tg-emoji> <b>ধাপ ১: আপনার Coupon Code-টি নিচে লিখুন:</b>",
        "enter_username": (
            "<tg-emoji emoji-id='5368324170671202286'>📥</tg-emoji> <b>এডমিনের কয়েন রিসিভিং আইডি:</b> <code>{acc}</code>\n\n"
            "<i>প্রথমে অ্যাপ থেকে উপরের ইউজারনেমে কয়েন সেন্ড করুন।</i>\n"
            "<tg-emoji emoji-id='5368324170671202286'>♻️</tg-emoji> <b>যে আইডি থেকে কয়েন পাঠিয়েছেন সেই Sender Username লিখুন:</b>"
        ),
        "enter_amount": "<tg-emoji emoji-id='5368324170671202286'>💰</tg-emoji> <b>কয়েনের পরিমাণ নির্বাচন করুন বা টাইপ করুন:</b>\n<i>(সর্বনিম্ন ১০,০০০)</i>",
        "enter_custom_amount": "<tg-emoji emoji-id='5368324170671202286'>✏️</tg-emoji> <b>কয়েনের পরিমাণ লিখুন (যেমন: 15000):</b>",
        "min_amount_err": "⚠️ <i>সর্বনিম্ন ১০,০০০ কয়েন হতে হবে।</i>",
        "num_err": "⚠️ <i>অনুগ্রহ করে সঠিক সংখ্যা লিখুন:</i>",
        "enter_method": "<tg-emoji emoji-id='5368324170671202286'>📱</tg-emoji> <b>পেমেন্ট মেথড নির্বাচন করুন:</b>",
        "enter_number": "<tg-emoji emoji-id='5368324170671202286'>📞</tg-emoji> <b>পেমেন্ট নম্বর নির্বাচন করুন বা নতুন লিখুন:</b>",
        "enter_custom_number": "<tg-emoji emoji-id='5368324170671202286'>✏️</tg-emoji> <b>আপনার অ্যাকাউন্টের বিকাশ/নগদ নম্বর লিখুন:</b>",
        "tx_success": (
            "<b>┌─────────────────────┐</b>\n"
            "<b>│ <tg-emoji emoji-id='5368324170671202286'>🎉</tg-emoji> রিকোয়েস্ট সফলভাবে জমা হয়েছে! │</b>\n"
            "<b>└─────────────────────┘</b>\n\n"
            "<tg-emoji emoji-id='5368324170671202286'>🆔</tg-emoji> <b>লেনদেন আইডি   :</b> <code>#{tx_id}</code>\n"
            "<tg-emoji emoji-id='5368324170671202286'>🪙</tg-emoji> <b>কয়েন টাইপ     :</b> <b>{coin}</b>\n"
            "<tg-emoji emoji-id='5368324170671202286'>📦</tg-emoji> <b>কয়েনের পরিমাণ  :</b> <b>{amt:,}</b>\n"
            "<tg-emoji emoji-id='5368324170671202286'>📱</tg-emoji> <b>পেমেন্ট মেথড   :</b> <b>{method}</b>\n"
            "<tg-emoji emoji-id='5368324170671202286'>📞</tg-emoji> <b>ওয়ালেট নম্বর   :</b> <code>{num}</code>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "<tg-emoji emoji-id='5368324170671202286'>💰</tg-emoji> <b>মোট প্রাপ্ত টাকা :</b> <code>{taka} ৳</code> <i>(চার্জ -৫৳)</i>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "<tg-emoji emoji-id='5368324170671202286'>⏳</tg-emoji> <i>এডমিন দ্রুত কয়েন যাচাই করে পেমেন্ট সম্পন্ন করবে!</i>"
        ),
        "history_title": "<tg-emoji emoji-id='5368324170671202286'>📜</tg-emoji> <b>আপনার লেনদেনের ইতিহাস:</b>\n\n",
        "no_history": "<i>আপনার কোনো লেনদেনের ইতিহাস পাওয়া যায়নি।</i>",
        "leaderboard_title": "<tg-emoji emoji-id='5368324170671202286'>🏆</tg-emoji> <b>পাবলিক লিডারবোর্ড (সেরা বিক্রেতা):</b>\n\n",
        "no_leaderboard": "<i>এখনো কোনো সফল লেনদেন হয়নি।</i>",
        "lang_selected": "✅ <b>ভাষা সফলভাবে বাংলা নির্বাচন করা হয়েছে!</b>",
        "lang_choose": "<tg-emoji emoji-id='5368324170671202286'>🌐</tg-emoji> <b>আপনার পছন্দসই ভাষা নির্বাচন করুন:</b>",
        "btn_sell": "🛒 Sell Coins",
        "btn_rates": "📊 Live Rates",
        "btn_history": "📜 My History",
        "btn_leaderboard": "🏆 Leaderboard",
        "btn_lang": "🌐 Language / ভাষা",
        "btn_support": "👨‍💻 Support"
    }
}

# --- ৩. SQLite ডাটাবেজ সেটআপ ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=NORMAL;")
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS coins (
            key TEXT PRIMARY KEY,
            label TEXT,
            price REAL,
            active INTEGER,
            recv_acc TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            lang TEXT DEFAULT 'en',
            saved_method TEXT DEFAULT NULL,
            saved_number TEXT DEFAULT NULL
        )
    ''')
    
    default_coins = [
        ('niva', 'Niva Coin', 4.0, 1, 'sell_point_it'),
        ('NewTop', 'NewTop Coin', 21.0, 1, 'AdminNewTopID'),
        ('topfollows', 'Topfollows Coin', 2.0, 1, 'N/A'),
        ('ns', 'NS Coin', 9.0, 1, 'himelorkar019'),
        ('nexa', 'Nexa Coin', 9.0, 1, 'AdminNexaID'),
        ('coinsta', 'Coinsta Coin', 19.5, 1, 'AdminCoinstaID'),
        ('coinova', 'Coinova Coin', 14.0, 1, 'AdminCoinovaID'),
        ('oldtop', 'Oldtop Coin', 3.5, 1, 'AdminOldtopID'),
        ('manually_pro', 'Manually Pro Coin', 6.0, 1, 'AdminManuallyProID')
    ]
    
    for c in default_coins:
        cursor.execute("INSERT OR IGNORE INTO coins VALUES (?, ?, ?, ?, ?)", c)

    cursor.execute('''
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
    ''')
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tx_user ON transactions(user_id);")
    
    conn.commit()
    conn.close()

init_db()

# --- ৪. ডাটাবেজ হেল্পার ফাংশন ---
def add_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, lang) VALUES (?, 'en')", (user_id,))
    conn.commit()
    conn.close()

def get_user_data(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT lang, saved_method, saved_number FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"lang": row[0], "saved_method": row[1], "saved_number": row[2]}
    return {"lang": "en", "saved_method": None, "saved_number": None}

def set_user_lang(user_id, lang):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET lang = ? WHERE user_id = ?", (lang, user_id))
    conn.commit()
    conn.close()

def save_user_wallet(user_id, method, number):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET saved_method = ?, saved_number = ? WHERE user_id = ?", (method, number, user_id))
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
    cursor.execute("SELECT key, label, price, active, recv_acc FROM coins")
    rows = cursor.fetchall()
    conn.close()
    return {r[0]: {"label": r[1], "price": r[2], "active": bool(r[3]), "recv_acc": r[4]} for r in rows}

def update_coin_price(key, new_price):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE coins SET price = ? WHERE key = ?", (new_price, key))
    conn.commit()
    conn.close()

def update_coin_acc(key, new_acc):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE coins SET recv_acc = ? WHERE key = ?", (new_acc, key))
    conn.commit()
    conn.close()

def toggle_coin_active(key):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE coins SET active = CASE WHEN active = 1 THEN 0 ELSE 1 END WHERE key = ?", (key,))
    conn.commit()
    conn.close()

def add_transaction(user_id, user_name, coin_label, coin_amount, method, number, net_taka, coin_info):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transactions (user_id, user_name, coin_label, coin_amount, payment_method, account_number, net_taka, coin_info, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Pending')
    ''', (user_id, user_name, coin_label, coin_amount, method, number, net_taka, coin_info))
    tx_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return tx_id

def update_tx_status(tx_id, status):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE transactions SET status = ? WHERE id = ?", (status, tx_id))
    conn.commit()
    conn.close()

def get_tx(tx_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, coin_label, coin_amount, payment_method, account_number, net_taka, status, coin_info FROM transactions WHERE id = ?", (tx_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def get_user_history(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, coin_label, coin_amount, net_taka, status, coin_info FROM transactions WHERE user_id = ? ORDER BY id DESC LIMIT 10", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_leaderboard():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_name, SUM(coin_amount) as total_coins, COUNT(id) as total_sales
        FROM transactions
        WHERE status = 'Accepted'
        GROUP BY user_id
        ORDER BY total_coins DESC
        LIMIT 10
    ''')
    rows = cursor.fetchall()
    conn.close()
    return rows

# --- ৫. চ্যাট পরিষ্কার করার হেল্পার ফাংশন ---
def track_msg(context: ContextTypes.DEFAULT_TYPE, msg_id: int):
    if "temp_msg_ids" not in context.user_data or not isinstance(context.user_data["temp_msg_ids"], list):
        context.user_data["temp_msg_ids"] = []
    if msg_id and msg_id not in context.user_data["temp_msg_ids"]:
        context.user_data["temp_msg_ids"].append(msg_id)

async def delete_messages_after_delay(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_ids: list, delay: int = 3):
    await asyncio.sleep(delay)
    for msg_id in message_ids:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception:
            pass

# --- ৬. বট এর স্থায়ী Reply Keyboard Layout ---
def get_main_reply_keyboard(lang="en"):
    txt = MESSAGES[lang]
    keyboard = [
        [KeyboardButton(txt["btn_sell"]), KeyboardButton(txt["btn_rates"])],
        [KeyboardButton(txt["btn_history"]), KeyboardButton(txt["btn_leaderboard"])],
        [KeyboardButton(txt["btn_lang"]), KeyboardButton(txt["btn_support"])]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_language_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇺🇸 English", callback_data="set_lang_en")],
        [InlineKeyboardButton("🇧🇩 বাংলা (Bangla)", callback_data="set_lang_bn")]
    ])

def get_amount_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 10,000 Coins", callback_data="amt_10000"), InlineKeyboardButton("💎 25,000 Coins", callback_data="amt_25000")],
        [InlineKeyboardButton("💎 50,000 Coins", callback_data="amt_50000"), InlineKeyboardButton("💎 100,000 Coins", callback_data="amt_100000")],
        [InlineKeyboardButton("✏️ Custom Amount (অন্যান্য)", callback_data="amt_custom")]
    ])

def get_method_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌸 bKash (বিকাশ)", callback_data="method_bKash")],
        [InlineKeyboardButton("🟠 Nagad (নগদ)", callback_data="method_Nagad")],
        [InlineKeyboardButton("🚀 Rocket (রকেট)", callback_data="method_Rocket")],
        [InlineKeyboardButton("🟡 Upay (উপায়)", callback_data="method_Upay")]
    ])

def get_number_keyboard(saved_method, saved_number):
    keyboard = []
    if saved_method and saved_number:
        keyboard.append([InlineKeyboardButton(f"⚡ Use Saved: {saved_method} ({saved_number})", callback_data="num_use_saved")])
    keyboard.append([InlineKeyboardButton("✏️ Enter New Number (নতুন নাম্বার লিখুন)", callback_data="num_enter_new")])
    return InlineKeyboardMarkup(keyboard)

# --- ৭. বট স্টার্ট হ্যান্ডলার ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user(user_id)
    u_data = get_user_data(user_id)
    lang = u_data["lang"]
    txt = MESSAGES[lang]
    
    reply_markup = get_main_reply_keyboard(lang)
    if update.message:
        await update.message.reply_text(txt["welcome"], reply_markup=reply_markup, parse_mode="HTML")

# --- ৮. এডমিন প্যানেল UI ---
def get_admin_keyboard():
    coins = get_coins()
    keyboard = []
    for k, c in coins.items():
        st = "🟢" if c["active"] else "🔴"
        keyboard.append([InlineKeyboardButton(f"{st} {c['label']}", callback_data=f"adm_manage_{k}")])
    keyboard.append([InlineKeyboardButton("📢 Send Public Broadcast", callback_data="adm_broadcast")])
    return InlineKeyboardMarkup(keyboard)

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_TELEGRAM_ID:
        return
    await update.message.reply_text(
        "⚙️ <b>Admin Panel - Dynamic Control</b>\n\nSelect coin to modify price, account, or status:",
        reply_markup=get_admin_keyboard(),
        parse_mode="HTML"
    )

# --- ৯. কলব্যাক হ্যান্ডলার ---
async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    u_data = get_user_data(user_id)
    lang = u_data["lang"]
    txt = MESSAGES[lang]

    if data.startswith("set_lang_"):
        new_lang = data.split("_")[2]
        set_user_lang(user_id, new_lang)
        new_txt = MESSAGES[new_lang]
        await query.edit_message_text(new_txt["lang_selected"], parse_mode="HTML")

    elif data.startswith("sell_"):
        key = data.split("_")[1]
        coins = get_coins()
        c = coins.get(key)
        context.user_data["selected_coin"] = key
        
        if query.message:
            track_msg(context, query.message.message_id)
        
        if key == "topfollows":
            context.user_data["step"] = "AWAITING_COUPON"
            sent_msg = await query.edit_message_text(txt["enter_coupon"], parse_mode="HTML")
            track_msg(context, sent_msg.message_id)
        else:
            admin_acc = c.get("recv_acc", "N/A")
            context.user_data["step"] = "AWAITING_USERNAME"
            msg = txt["enter_username"].format(acc=admin_acc)
            sent_msg = await query.edit_message_text(msg, parse_mode="HTML")
            track_msg(context, sent_msg.message_id)

    elif data.startswith("amt_"):
        val = data.split("_")[1]
        if val == "custom":
            context.user_data["step"] = "AWAITING_CUSTOM_AMOUNT"
            sent_msg = await query.edit_message_text(txt["enter_custom_amount"], parse_mode="HTML")
            track_msg(context, sent_msg.message_id)
        else:
            amt = int(val)
            context.user_data["amount"] = amt
            context.user_data["step"] = "AWAITING_METHOD"
            sent_msg = await query.edit_message_text(txt["enter_method"], reply_markup=get_method_keyboard(), parse_mode="HTML")
            track_msg(context, sent_msg.message_id)

    elif data.startswith("method_"):
        m_name = data.split("_")[1]
        context.user_data["method"] = m_name
        context.user_data["step"] = "AWAITING_NUMBER"
        
        s_method = u_data["saved_method"]
        s_num = u_data["saved_number"]
        
        sent_msg = await query.edit_message_text(txt["enter_number"], reply_markup=get_number_keyboard(s_method, s_num), parse_mode="HTML")
        track_msg(context, sent_msg.message_id)

    elif data == "num_use_saved":
        s_method = u_data["saved_method"]
        s_num = u_data["saved_number"]
        await finalize_transaction(update, context, s_method, s_num, user_id, u_data["lang"])

    elif data == "num_enter_new":
        context.user_data["step"] = "AWAITING_CUSTOM_NUMBER"
        sent_msg = await query.edit_message_text(txt["enter_custom_number"], parse_mode="HTML")
        track_msg(context, sent_msg.message_id)

    elif data.startswith("admin_accept_") or data.startswith("admin_reject_"):
        if user_id != ADMIN_TELEGRAM_ID: return
        parts = data.split("_")
        action = parts[1]
        tx_id = int(parts[2])

        if action == "reject":
            update_tx_status(tx_id, "Rejected")
            tx = get_tx(tx_id)
            await context.bot.send_message(
                chat_id=tx[0],
                text=f"❌ <b>Your sell request (ID: #{tx_id}) was rejected.</b>\nVerification or provided information was invalid.",
                parse_mode="HTML"
            )
            await query.edit_message_text(query.message.text + "\n\n❌ <b>REJECTED and User Notified.</b>", parse_mode="HTML")
        
        elif action == "accept":
            context.user_data["pending_tx_id"] = tx_id
            context.user_data["admin_step"] = "AWAITING_PROOF"
            await query.edit_message_text(query.message.text + "\n\n📸 <b>কাস্টমারকে পেমেন্ট করে স্ক্রিনশটটি এই চ্যাটে সেন্ড করুন:</b>", parse_mode="HTML")

    elif data.startswith("adm_manage_"):
        if user_id != ADMIN_TELEGRAM_ID: return
        key = data.split("_")[2]
        coins = get_coins()
        c = coins[key]
        st_txt = "Active 🟢" if c["active"] else "Inactive 🔴"
        
        text = (
            f"⚙️ <b>Manage Coin:</b> {c['label']}\n"
            f"💰 Price: <code>{c['price']}</code> ৳\n"
            f"📥 Receiving ID: <code>{c['recv_acc']}</code>\n"
            f"📊 Status: {st_txt}\n\n"
            f"Select option below to change:"
        )
        btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("✏️ Edit Price", callback_data=f"adm_p_{key}"), InlineKeyboardButton("✏️ Edit Recv ID", callback_data=f"adm_a_{key}")],
            [InlineKeyboardButton(f"🔄 Toggle ({'Disable' if c['active'] else 'Enable'})", callback_data=f"adm_t_{key}")],
            [InlineKeyboardButton("🔙 Back to Admin", callback_data="adm_back")]
        ])
        await query.edit_message_text(text, reply_markup=btn, parse_mode="HTML")

    elif data == "adm_back":
        if user_id != ADMIN_TELEGRAM_ID: return
        await query.edit_message_text("⚙️ <b>Admin Panel - Dynamic Control</b>", reply_markup=get_admin_keyboard(), parse_mode="HTML")

    elif data.startswith("adm_t_"):
        if user_id != ADMIN_TELEGRAM_ID: return
        key = data.split("_")[2]
        toggle_coin_active(key)
        await query.answer("Status Updated!")
        await handle_callbacks(update, context)

    elif data.startswith("adm_p_"):
        if user_id != ADMIN_TELEGRAM_ID: return
        key = data.split("_")[2]
        context.user_data["admin_coin_key"] = key
        context.user_data["admin_step"] = "AWAITING_NEW_PRICE"
        await query.edit_message_text("✏️ Enter new price (Per 1000 Coins):")

    elif data.startswith("adm_a_"):
        if user_id != ADMIN_TELEGRAM_ID: return
        key = data.split("_")[2]
        context.user_data["admin_coin_key"] = key
        context.user_data["admin_step"] = "AWAITING_NEW_ACC"
        await query.edit_message_text("✏️ Enter new Receiving ID/Username:")

    elif data == "adm_broadcast":
        if user_id != ADMIN_TELEGRAM_ID: return
        context.user_data["admin_step"] = "AWAITING_BROADCAST_MSG"
        await query.edit_message_text("📢 <b>Enter broadcast message:</b>\n\n(This will be sent to all users)", parse_mode="HTML")

# --- ১০. ইনপুট ও বাটন হ্যান্ডলার ---
async def handle_inputs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user(user_id)
    u_data = get_user_data(user_id)
    lang = u_data["lang"]
    txt = MESSAGES[lang]
    text_input = update.message.text if update.message else ""
    user_msg_id = update.message.message_id if update.message else None
    
    admin_step = context.user_data.get("admin_step")
    step = context.user_data.get("step")

    # --- Reply Keyboard Button Press ---
    if text_input in ["🛒 Sell Coins", "🛒 কয়েন বিক্রি"]:
        context.user_data["temp_msg_ids"] = []
        if user_msg_id: track_msg(context, user_msg_id)
        
        coins = get_coins()
        keyboard = []
        for k, c in coins.items():
            if c["active"]:
                keyboard.append([InlineKeyboardButton(f"Sell {c['label']} ({c['price']}৳/1K)", callback_data=f"sell_{k}")])
        
        bot_prompt = await update.message.reply_text(txt["sell_title"], reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        track_msg(context, bot_prompt.message_id)
        return

    elif text_input in ["📊 Live Rates", "📊 লাইভ রেট"]:
        coins = get_coins()
        text = txt["rates_title"]
        for k, c in coins.items():
            st = txt["active"] if c["active"] else txt["inactive"]
            text += f"• <b>{c['label']}</b>: {c['price']} ৳ ({st})\n"
        await update.message.reply_text(text, parse_mode="HTML")
        return

    elif text_input in ["📜 My History", "📜 মাই হিস্ট্রি"]:
        history = get_user_history(user_id)
        text = txt["history_title"]
        if not history:
            text += txt["no_history"]
        else:
            for row in history:
                st_icon = "⏳" if row[4] == "Pending" else ("✅" if row[4] == "Accepted" else "❌")
                info_text = f"🔑 Coupon: <code>{row[5]}</code>" if "topfollows" in str(row[1]).lower() else f"👤 Sender ID: <code>{row[5]}</code>"
                text += f"🆔 <code>#{row[0]}</code> | <b>{row[1]}</b>\n{info_text}\n📦 Amount: {row[2]:,} | 💰 {row[3]} ৳\nStatus: {st_icon} <b>{row[4]}</b>\n----------------------\n"
        await update.message.reply_text(text, parse_mode="HTML")
        return

    elif text_input in ["🏆 Leaderboard", "🏆 লিডারবোর্ড"]:
        lb = get_leaderboard()
        text = txt["leaderboard_title"]
        if not lb:
            text += txt["no_leaderboard"]
        else:
            for idx, row in enumerate(lb, start=1):
                text += f"{idx}. <b>{row[0]}</b> — {row[1]:,} Coins ({row[2]} Sales)\n"
        await update.message.reply_text(text, parse_mode="HTML")
        return

    elif text_input in ["🌐 Language / ভাষা", "🌐 Language"]:
        await update.message.reply_text(txt["lang_choose"], reply_markup=get_language_keyboard(), parse_mode="HTML")
        return

    elif text_input in ["👨‍💻 Support"]:
        text = "👨‍💻 <b>Support Center:</b>\nContact admin: @educationpointbd24\nOfficial Channel: @EducationPointBD"
        await update.message.reply_text(text, parse_mode="HTML")
        return

    # --- Admin Proof Verification ---
    if user_id == ADMIN_TELEGRAM_ID and admin_step == "AWAITING_PROOF" and update.message.photo:
        tx_id = context.user_data.get("pending_tx_id")
        photo_file_id = update.message.photo[-1].file_id
        
        update_tx_status(tx_id, "Accepted")
        tx = get_tx(tx_id)
        info_label = "🔑 <b>Coupon Code:</b>" if "topfollows" in str(tx[1]).lower() else "👤 <b>Sender ID:</b>"

        msg = (
            f"✅ <b>Your coin sale request was accepted and payment sent to your wallet!</b>\n\n"
            f"📋 <b>Transaction Details:</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🆔 <b>Transaction ID:</b> <code>#{tx_id}</code>\n"
            f"🪙 <b>Coin Type:</b> {tx[1]}\n"
            f"{info_label} <code>{tx[7]}</code>\n"
            f"📦 <b>Coin Amount:</b> {tx[2]:,}\n"
            f"📱 <b>Payment Wallet:</b> {tx[3]}\n"
            f"Number: <code>{tx[4]}</code>\n"
            f"💰 <b>Paid Amount:</b> <code>{tx[5]} ৳</code>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"Payment proof screenshot is attached below."
        )
        
        await context.bot.send_photo(chat_id=tx[0], photo=photo_file_id, caption=msg, parse_mode="HTML")
        await update.message.reply_text("✅ <b>Payment details and proof successfully sent to customer!</b>", parse_mode="HTML")
        context.user_data["admin_step"] = None
        return

    # --- Admin Input Handlers ---
    if user_id == ADMIN_TELEGRAM_ID and admin_step == "AWAITING_NEW_PRICE" and text_input:
        try:
            new_p = float(text_input.strip())
            key = context.user_data.get("admin_coin_key")
            update_coin_price(key, new_p)
            context.user_data["admin_step"] = None
            await update.message.reply_text("✅ <b>Price successfully updated!</b>", reply_markup=get_admin_keyboard(), parse_mode="HTML")
        except ValueError:
            await update.message.reply_text(txt["num_err"], parse_mode="HTML")
        return

    if user_id == ADMIN_TELEGRAM_ID and admin_step == "AWAITING_NEW_ACC" and text_input:
        new_acc = text_input.strip()
        key = context.user_data.get("admin_coin_key")
        update_coin_acc(key, new_acc)
        context.user_data["admin_step"] = None
        await update.message.reply_text("✅ <b>Receiving ID successfully updated!</b>", reply_markup=get_admin_keyboard(), parse_mode="HTML")
        return

    if user_id == ADMIN_TELEGRAM_ID and admin_step == "AWAITING_BROADCAST_MSG" and text_input:
        broadcast_text = f"📢 <b>Public Announcement:</b>\n\n{text_input.strip()}"
        users = get_all_users()
        sent_count = 0
        for uid in users:
            try:
                await context.bot.send_message(chat_id=uid, text=broadcast_text, parse_mode="HTML")
                sent_count += 1
            except Exception:
                pass
        context.user_data["admin_step"] = None
        await update.message.reply_text(f"✅ <b>Message successfully sent to {sent_count} users!</b>", reply_markup=get_admin_keyboard(), parse_mode="HTML")
        return

    # --- Transaction Multi-step Inputs ---
    if step in ["AWAITING_USERNAME", "AWAITING_COUPON"] and text_input:
        if user_msg_id: track_msg(context, user_msg_id)
        context.user_data["coin_info"] = text_input.strip()
        context.user_data["step"] = "AWAITING_AMOUNT"
        
        bot_prompt = await update.message.reply_text(txt["enter_amount"], reply_markup=get_amount_keyboard(), parse_mode="HTML")
        track_msg(context, bot_prompt.message_id)

    elif step == "AWAITING_CUSTOM_AMOUNT" and text_input:
        if user_msg_id: track_msg(context, user_msg_id)
        try:
            amt = int(text_input.strip())
            if amt < 10000:
                err_msg = await update.message.reply_text(txt["min_amount_err"], parse_mode="HTML")
                track_msg(context, err_msg.message_id)
                return
            
            context.user_data["amount"] = amt
            context.user_data["step"] = "AWAITING_METHOD"
            
            bot_prompt = await update.message.reply_text(txt["enter_method"], reply_markup=get_method_keyboard(), parse_mode="HTML")
            track_msg(context, bot_prompt.message_id)
        except ValueError:
            err_msg = await update.message.reply_text(txt["num_err"], parse_mode="HTML")
            track_msg(context, err_msg.message_id)

    elif step == "AWAITING_CUSTOM_NUMBER" and text_input:
        if user_msg_id: track_msg(context, user_msg_id)
        num = text_input.strip()
        method = context.user_data.get("method", "bKash")
        
        save_user_wallet(user_id, method, num)
        await finalize_transaction(update, context, method, num, user_id, lang)

# --- ১১. লেনদেন ফাইনাল প্রসেসর ---
async def finalize_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE, method: str, num: str, user_id: int, lang: str):
    txt = MESSAGES[lang]
    temp_ids = context.user_data.get("temp_msg_ids", []).copy()
    
    coins = get_coins()
    key = context.user_data["selected_coin"]
    c = coins[key]
    amt = context.user_data["amount"]
    coin_info = context.user_data.get("coin_info", "N/A")

    net_taka = max(0, (amt / 1000) * c["price"] - 5)
    context.user_data["step"] = None

    user_obj = update.effective_user
    tx_id = add_transaction(user_id, user_obj.first_name, c["label"], amt, method, num, net_taka, coin_info)

    user_msg_text = txt["tx_success"].format(
        tx_id=tx_id, coin=c['label'], amt=amt, method=method, num=num, taka=net_taka
    )
    
    if update.callback_query:
        await update.callback_query.message.reply_text(user_msg_text, parse_mode="HTML")
    else:
        await update.message.reply_text(user_msg_text, parse_mode="HTML")

    asyncio.create_task(delete_messages_after_delay(context, user_id, temp_ids, delay=3))
    context.user_data["temp_msg_ids"] = []

    info_type = "🎟 <b>Coupon Code:</b>" if key == "topfollows" else "👤 <b>Sender Username:</b>"
    admin_msg = (
        f"🚨 <b>New Coin Sale Request!</b>\n\n"
        f"🆔 <b>TX ID:</b> <code>#{tx_id}</code>\n"
        f"👤 <b>User:</b> {user_obj.first_name} (<code>{user_id}</code>)\n"
        f"🪙 <b>Coin:</b> {c['label']}\n"
        f"{info_type} <code>{coin_info}</code>\n"
        f"📦 <b>Amount:</b> {amt:,}\n"
        f"📱 <b>Method:</b> {method} (<code>{num}</code>)\n"
        f"💰 <b>Payable:</b> <code>{net_taka} ৳</code>\n\n"
        f"Please verify and choose action:"
    )
    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Accept & Pay", callback_data=f"admin_accept_{tx_id}"), InlineKeyboardButton("❌ Reject", callback_data=f"admin_reject_{tx_id}")]
    ])
    await context.bot.send_message(chat_id=ADMIN_TELEGRAM_ID, text=admin_msg, reply_markup=btn, parse_mode="HTML")

# --- ১২. ব্যাকগ্রাউন্ড অটো টাস্ক ---
async def auto_ping_task(application: Application):
    while True:
        await asyncio.sleep(400)
        users = get_all_users()
        ping_text = "⚡ <b>Bot Status:</b> System Active & Online! 🟢"
        
        for u_id in users:
            try:
                msg = await application.bot.send_message(chat_id=u_id, text=ping_text, parse_mode="HTML")
                asyncio.create_task(delete_msg_after_delay(application, u_id, msg.message_id, 120))
            except Exception:
                pass

async def delete_msg_after_delay(application: Application, chat_id: int, message_id: int, delay: int):
    await asyncio.sleep(delay)
    try:
        await application.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass

async def post_init(application: Application):
    asyncio.create_task(auto_ping_task(application))

# --- ১৩. বট মেইন এক্সিকিউশন ---
def main():
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    
    app.add_handler(CallbackQueryHandler(handle_callbacks))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_inputs))

    print("Bot is running with Telegram Custom Premium Emoji Support...")
    app.run_polling()

if __name__ == "__main__":
    main()
