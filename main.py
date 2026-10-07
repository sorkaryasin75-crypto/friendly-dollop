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

# --- ২. বহুভাষিক টেক্সট অভিধান (Default English) ---
MESSAGES = {
    "en": {
        "welcome": "👋 Welcome to **Sell Point IT**!\n\nPlease select an option from the menu below:",
        "rates_title": "📊 **Live Market Rates (Per 1000 Coins):**\n\n",
        "active": "✅ Active",
        "inactive": "❌ Inactive",
        "sell_title": "🛒 **Select the coin you want to sell:**\n*(Minimum 10,000)*",
        "enter_coupon": "✏️ **Step 1:** Enter your Coupon Code:",
        "enter_username": "📥 Admin's Receiving ID: `{acc}`\n\nFirst send coins to the username above.\n♻️ Enter your Sender Username below:",
        "enter_amount": "💰 **Select or Enter Coin Amount:**\n*(Minimum 10,000)*",
        "enter_custom_amount": "✏️ Type your custom coin amount (e.g., 15000):",
        "min_amount_err": "⚠️ Minimum amount is 10,000 coins.",
        "num_err": "⚠️ Please enter a valid number:",
        "enter_method": "📱 **Select Payment Method:**",
        "enter_number": "📞 **Select or Enter Mobile/Account Number:**",
        "enter_custom_number": "✏️ Enter your account/mobile number:",
        "tx_success": "🎉 **Your coin sale request submitted successfully!**\n\n🆔 **TX ID:** `#{tx_id}`\n🪙 **Coin:** {coin}\n📦 **Amount:** {amt:,}\n📱 **Method:** {method}\n📞 **Number:** `{num}`\n💰 **Net Payable:** `{taka} ৳` (Fee -5৳)\n\n⏳ Admin will verify and process your payment shortly.",
        "history_title": "📜 **Your Transaction History:**\n\n",
        "no_history": "No transaction history found.",
        "leaderboard_title": "🏆 **Public Leaderboard (Top Sellers):**\n\n",
        "no_leaderboard": "No successful transactions yet.",
        "lang_selected": "✅ Language successfully set to 'English'!",
        "lang_choose": "🌐 **Select your preferred language / আপনার পছন্দসই ভাষা নির্বাচন করুন:**",
        "btn_sell": "🛒 Sell Coins",
        "btn_rates": "📊 Live Rates",
        "btn_history": "📜 My History",
        "btn_leaderboard": "🏆 Leaderboard",
        "btn_lang": "🌐 Language / ভাষা",
        "btn_support": "👨‍💻 Support",
        "btn_channel": "📢 Channel"
    },
    "bn": {
        "welcome": "👋 **Sell Point IT**-এ আপনাকে স্বাগতম!\n\nনিচের মেনু বা বাটন থেকে আপনার সেবা নির্বাচন করুন:",
        "rates_title": "📊 **লাইভ মার্কেট রেট (প্রতি ১০০০ কয়েন):**\n\n",
        "active": "✅ সক্রিয়",
        "inactive": "❌ নিষ্ক্রিয়",
        "sell_title": "🛒 **কোন কয়েনটি বিক্রি করতে চান বেছে নিন:**\n*(সর্বনিম্ন ১০,০০০)*",
        "enter_coupon": "✏️ **ধাপ ১:** আপনার Topfollow / Coupon Code-টি প্রদান করুন:",
        "enter_username": "📥 এডমিনের কয়েন রিসিভিং আইডি: `{acc}`\n\nপ্রথমে অ্যাপ থেকে উপরের ইউজারনেমে কয়েন সেন্ড করুন।\n♻️ যে আইডি থেকে কয়েন পাঠিয়েছেন সেই ইউজারনেমটি (Sender Username) এখানে লিখুন:",
        "enter_amount": "💰 **কয়েনের পরিমাণ নির্বাচন করুন বা লিখুন:**\n*(সর্বনিম্ন ১০,০০০)*",
        "enter_custom_amount": "✏️ আপনার কয়েনের সঠিক পরিমাণ লিখুন (যেমন: 15000):",
        "min_amount_err": "⚠️ সর্বনিম্ন ১০,০০০ কয়েন হতে হবে।",
        "num_err": "⚠️ অনুগ্রহ করে সঠিক সংখ্যা লিখুন:",
        "enter_method": "📱 **পেমেন্ট মেথড নির্বাচন করুন:**",
        "enter_number": "📞 **পেমেন্ট নম্বর নির্বাচন করুন বা নতুন লিখুন:**",
        "enter_custom_number": "✏️ আপনার অ্যাকাউন্টের মোবাইল নম্বরটি লিখুন:",
        "tx_success": "🎉 **আপনার কয়েন সেল রিকোয়েস্টটি সফলভাবে জমা হয়েছে!**\n\n🆔 **TX ID:** `#{tx_id}`\n🪙 **কয়েন:** {coin}\n📦 **পরিমাণ:** {amt:,}\n📱 **মেথড:** {method}\n📞 **নম্বর:** `{num}`\n💰 **প্রাপ্য টাকা:** `{taka} ৳` (চার্জ -৫৳)\n\n⏳ এডমিন অতি শীঘ্রই যাচাই করে পেমেন্ট সম্পন্ন করবেন।",
        "history_title": "📜 **আপনার লেনদেনের ইতিহাস:**\n\n",
        "no_history": "আপনার কোনো লেনদেনের ইতিহাস পাওয়া যায়নি।",
        "leaderboard_title": "🏆 **পাবলিক লিডারবোর্ড (সেরা বিক্রেতা):**\n\n",
        "no_leaderboard": "এখনো কোনো সফল লেনদেন হয়নি।",
        "lang_selected": "✅ ভাষা সফলভাবে 'বাংলা' নির্বাচন করা হয়েছে!",
        "lang_choose": "🌐 **আপনার পছন্দসই ভাষা নির্বাচন করুন / Select your language:**",
        "btn_sell": "🛒 Sell Coins",
        "btn_rates": "📊 Live Rates",
        "btn_history": "📜 My History",
        "btn_leaderboard": "🏆 Leaderboard",
        "btn_lang": "🌐 Language / ভাষা",
        "btn_support": "👨‍💻 Support",
        "btn_channel": "📢 Channel"
    }
}

# --- ৩. SQLite ডাটাবেজ সেটআপ (Saved Wallet Columns সহ) ---
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
    
    # ইউজারের সেভ করা মেথড এবং নাম্বার সংরক্ষণের জন্য কলাম যুক্ত করা হয়েছে
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            lang TEXT DEFAULT 'en',
            saved_method TEXT DEFAULT NULL,
            saved_number TEXT DEFAULT NULL
        )
    ''')
    
    default_coins = [
        ('niva', 'Niva Coin', 5.0, 1, 'sell_point_it'),
        ('NewTop', 'NewTop Coin', 3.0, 1, 'AdminNewTopID'),
        ('topfollows', 'Topfollows Coin', 3.0, 1, 'N/A'),
        ('ns', 'NS Coin', 8.0, 1, 'himelorkar019'),
        ('nexa', 'Nexa Coin', 4.0, 1, 'AdminNexaID'),
        ('coinsta', 'Coinsta Coin', 4.5, 1, 'AdminCoinstaID'),
        ('coinova', 'Coinova Coin', 6.0, 1, 'AdminCoinovaID'),
        ('oldtop', 'Oldtop Coin', 3.5, 1, 'AdminOldtopID'),
        ('manually_pro', 'Manually Pro Coin', 7.0, 1, 'AdminManuallyProID')
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

# --- ৫. চ্যাট পরিষ্কারক ব্যাকগ্রাউন্ড ফাংশন ---
async def delete_messages_after_delay(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_ids: list, delay: int = 3):
    await asyncio.sleep(delay)
    for msg_id in message_ids:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception:
            pass

# --- ৬. ডাইনামিক এবং কালারফুল Inline Keyboards Layout ---
def get_main_inline_keyboard(lang="en"):
    txt = MESSAGES[lang]
    keyboard = [
        [InlineKeyboardButton(txt["btn_sell"], callback_data="menu_sell")],
        [InlineKeyboardButton(txt["btn_rates"], callback_data="menu_rates")],
        [InlineKeyboardButton(txt["btn_history"], callback_data="menu_history")],
        [InlineKeyboardButton(txt["btn_leaderboard"], callback_data="menu_leaderboard")],
        [InlineKeyboardButton(txt["btn_lang"], callback_data="menu_lang")],
        [InlineKeyboardButton(txt["btn_support"], url="https://t.me/educationpointbd24")],
        [InlineKeyboardButton(txt["btn_channel"], url="https://t.me/EducationPointBD")]
    ]
    return InlineKeyboardMarkup(keyboard)

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

# কাস্টম অ্যামাউন্ট নির্বাচন বাটন (Column Layout)
def get_amount_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 10,000 Coins", callback_data="amt_10000"), InlineKeyboardButton("💎 25,000 Coins", callback_data="amt_25000")],
        [InlineKeyboardButton("💎 50,000 Coins", callback_data="amt_50000"), InlineKeyboardButton("💎 100,000 Coins", callback_data="amt_100000")],
        [InlineKeyboardButton("✏️ Custom Amount (অন্যান্য)", callback_data="amt_custom")]
    ])

# কাস্টম পেমেন্ট মেথড বাটন (Beautiful Column Color Layout)
def get_method_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌸 bKash (বিকাশ)", callback_data="method_bKash")],
        [InlineKeyboardButton("🟠 Nagad (নগদ)", callback_data="method_Nagad")],
        [InlineKeyboardButton("🚀 Rocket (রকেট)", callback_data="method_Rocket")],
        [InlineKeyboardButton("🟡 Upay (উপায়)", callback_data="method_Upay")]
    ])

# সেভ করা নাম্বার দিয়ে দ্রুত লেনদেন করার বাটন
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
    
    inline_markup = get_main_inline_keyboard(lang)
    reply_markup = get_main_reply_keyboard(lang)
    
    text = txt["welcome"]
    if update.message:
        await update.message.reply_text(text, reply_markup=inline_markup, parse_mode="Markdown")
        await update.message.reply_text("⬇️ Quick Bottom Menu Loaded:", reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(text, reply_markup=inline_markup, parse_mode="Markdown")

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
        "⚙️ **Admin Panel - Dynamic Control**\n\nSelect coin to modify price, account, or status:",
        reply_markup=get_admin_keyboard(),
        parse_mode="Markdown"
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
    temp_ids = context.user_data.get("temp_msg_ids", [])

    if data == "main_menu":
        await start(update, context)

    # Inline Main Menu Navigation
    elif data == "menu_sell":
        coins = get_coins()
        keyboard = []
        for k, c in coins.items():
            if c["active"]:
                keyboard.append([InlineKeyboardButton(f"Sell {c['label']} ({c['price']}৳/1K)", callback_data=f"sell_{k}")])
        keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
        await query.edit_message_text(txt["sell_title"], reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "menu_rates":
        coins = get_coins()
        text = txt["rates_title"]
        for k, c in coins.items():
            st = txt["active"] if c["active"] else txt["inactive"]
            text += f"• **{c['label']}**: {c['price']} ৳ ({st})\n"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]), parse_mode="Markdown")

    elif data == "menu_history":
        history = get_user_history(user_id)
        text = txt["history_title"]
        if not history:
            text += txt["no_history"]
        else:
            for row in history:
                st_icon = "⏳" if row[4] == "Pending" else ("✅" if row[4] == "Accepted" else "❌")
                info_text = f"🔑 Coupon: `{row[5]}`" if "topfollows" in str(row[1]).lower() else f"👤 Sender ID: `{row[5]}`"
                text += f"🆔 `#{row[0]}` | **{row[1]}**\n{info_text}\n📦 Amount: {row[2]:,} | 💰 {row[3]} ৳\nStatus: {st_icon} **{row[4]}**\n----------------------\n"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]), parse_mode="Markdown")

    elif data == "menu_leaderboard":
        lb = get_leaderboard()
        text = txt["leaderboard_title"]
        if not lb:
            text += txt["no_leaderboard"]
        else:
            for idx, row in enumerate(lb, start=1):
                text += f"{idx}. **{row[0]}** — {row[1]:,} Coins ({row[2]} Sales)\n"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]), parse_mode="Markdown")

    elif data == "menu_lang":
        await query.edit_message_text(txt["lang_choose"], reply_markup=get_language_keyboard(), parse_mode="Markdown")

    elif data.startswith("set_lang_"):
        new_lang = data.split("_")[2]
        set_user_lang(user_id, new_lang)
        new_txt = MESSAGES[new_lang]
        await query.edit_message_text(new_txt["lang_selected"], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]))

    # --- সেল কয়েন প্রসেস শুরু ---
    elif data.startswith("sell_"):
        key = data.split("_")[1]
        coins = get_coins()
        c = coins.get(key)
        context.user_data["selected_coin"] = key
        context.user_data["temp_msg_ids"] = []
        
        if key == "topfollows":
            context.user_data["step"] = "AWAITING_COUPON"
            sent_msg = await query.edit_message_text(txt["enter_coupon"], parse_mode="Markdown")
            context.user_data["temp_msg_ids"].append(sent_msg.message_id)
        else:
            admin_acc = c.get("recv_acc", "N/A")
            context.user_data["step"] = "AWAITING_USERNAME"
            msg = txt["enter_username"].format(acc=admin_acc)
            sent_msg = await query.edit_message_text(msg, parse_mode="Markdown")
            context.user_data["temp_msg_ids"].append(sent_msg.message_id)

    # --- Amount Selection via Buttons ---
    elif data.startswith("amt_"):
        val = data.split("_")[1]
        if val == "custom":
            context.user_data["step"] = "AWAITING_CUSTOM_AMOUNT"
            sent_msg = await query.edit_message_text(txt["enter_custom_amount"], parse_mode="Markdown")
            temp_ids.append(sent_msg.message_id)
        else:
            amt = int(val)
            context.user_data["amount"] = amt
            context.user_data["step"] = "AWAITING_METHOD"
            sent_msg = await query.edit_message_text(txt["enter_method"], reply_markup=get_method_keyboard(), parse_mode="Markdown")
            temp_ids.append(sent_msg.message_id)

    # --- Method Selection via Buttons ---
    elif data.startswith("method_"):
        m_name = data.split("_")[1]
        context.user_data["method"] = m_name
        context.user_data["step"] = "AWAITING_NUMBER"
        
        s_method = u_data["saved_method"]
        s_num = u_data["saved_number"]
        
        sent_msg = await query.edit_message_text(txt["enter_number"], reply_markup=get_number_keyboard(s_method, s_num), parse_mode="Markdown")
        temp_ids.append(sent_msg.message_id)

    # --- Number Selection via Buttons ---
    elif data == "num_use_saved":
        s_method = u_data["saved_method"]
        s_num = u_data["saved_number"]
        await finalize_transaction(update, context, s_method, s_num, user_id, u_data["lang"])

    elif data == "num_enter_new":
        context.user_data["step"] = "AWAITING_CUSTOM_NUMBER"
        sent_msg = await query.edit_message_text(txt["enter_custom_number"], parse_mode="Markdown")
        temp_ids.append(sent_msg.message_id)

    # --- এডমিন অ্যাকশন ---
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
                text=f"❌ **Your sell request (ID: #{tx_id}) was rejected.**\nVerification or provided information was invalid.",
                parse_mode="Markdown"
            )
            await query.edit_message_text(query.message.text + "\n\n❌ **REJECTED and User Notified.**")
        
        elif action == "accept":
            context.user_data["pending_tx_id"] = tx_id
            context.user_data["admin_step"] = "AWAITING_PROOF"
            await query.edit_message_text(query.message.text + "\n\n📸 **কাস্টমারকে পেমেন্ট করে স্ক্রিনশটটি এই চ্যাটে সেন্ড করুন:**")

    # --- এডমিন কন্ট্রোল ম্যানেজমেন্ট ---
    elif data.startswith("adm_manage_"):
        if user_id != ADMIN_TELEGRAM_ID: return
        key = data.split("_")[2]
        coins = get_coins()
        c = coins[key]
        st_txt = "Active 🟢" if c["active"] else "Inactive 🔴"
        
        text = (
            f"⚙️ **Manage Coin:** {c['label']}\n"
            f"💰 Price: `{c['price']}` ৳\n"
            f"📥 Receiving ID: `{c['recv_acc']}`\n"
            f"📊 Status: {st_txt}\n\n"
            f"Select option below to change:"
        )
        btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("✏️ Edit Price", callback_data=f"adm_p_{key}"), InlineKeyboardButton("✏️ Edit Recv ID", callback_data=f"adm_a_{key}")],
            [InlineKeyboardButton(f"🔄 Toggle ({'Disable' if c['active'] else 'Enable'})", callback_data=f"adm_t_{key}")],
            [InlineKeyboardButton("🔙 Back to Admin", callback_data="adm_back")]
        ])
        await query.edit_message_text(text, reply_markup=btn, parse_mode="Markdown")

    elif data == "adm_back":
        if user_id != ADMIN_TELEGRAM_ID: return
        await query.edit_message_text("⚙️ **Admin Panel - Dynamic Control**", reply_markup=get_admin_keyboard(), parse_mode="Markdown")

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
        await query.edit_message_text("📢 **Enter broadcast message:**\n\n(This will be sent to all users)")

# --- ১০. ইনপুট ও চ্যাট অটো-ভ্যানিশ হ্যান্ডলার ---
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
    temp_ids = context.user_data.get("temp_msg_ids", [])

    # --- Reply Menu Buttons Handling ---
    if text_input in ["🛒 Sell Coins", "🛒 কয়েন বিক্রি"]:
        coins = get_coins()
        keyboard = []
        for k, c in coins.items():
            if c["active"]:
                keyboard.append([InlineKeyboardButton(f"Sell {c['label']} ({c['price']}৳/1K)", callback_data=f"sell_{k}")])
        await update.message.reply_text(txt["sell_title"], reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return

    elif text_input in ["📊 Live Rates", "📊 লাইভ রেট"]:
        coins = get_coins()
        text = txt["rates_title"]
        for k, c in coins.items():
            st = txt["active"] if c["active"] else txt["inactive"]
            text += f"• **{c['label']}**: {c['price']} ৳ ({st})\n"
        await update.message.reply_text(text, parse_mode="Markdown")
        return

    elif text_input in ["📜 My History", "📜 মাই হিস্ট্রি"]:
        history = get_user_history(user_id)
        text = txt["history_title"]
        if not history:
            text += txt["no_history"]
        else:
            for row in history:
                st_icon = "⏳" if row[4] == "Pending" else ("✅" if row[4] == "Accepted" else "❌")
                info_text = f"🔑 Coupon: `{row[5]}`" if "topfollows" in str(row[1]).lower() else f"👤 Sender ID: `{row[5]}`"
                text += f"🆔 `#{row[0]}` | **{row[1]}**\n{info_text}\n📦 Amount: {row[2]:,} | 💰 {row[3]} ৳\nStatus: {st_icon} **{row[4]}**\n----------------------\n"
        await update.message.reply_text(text, parse_mode="Markdown")
        return

    elif text_input in ["🏆 Leaderboard", "🏆 লিডারবোর্ড"]:
        lb = get_leaderboard()
        text = txt["leaderboard_title"]
        if not lb:
            text += txt["no_leaderboard"]
        else:
            for idx, row in enumerate(lb, start=1):
                text += f"{idx}. **{row[0]}** — {row[1]:,} Coins ({row[2]} Sales)\n"
        await update.message.reply_text(text, parse_mode="Markdown")
        return

    elif text_input in ["🌐 Language / ভাষা", "🌐 Language"]:
        await update.message.reply_text(txt["lang_choose"], reply_markup=get_language_keyboard(), parse_mode="Markdown")
        return

    # --- Admin Proof Verification ---
    if user_id == ADMIN_TELEGRAM_ID and admin_step == "AWAITING_PROOF" and update.message.photo:
        tx_id = context.user_data.get("pending_tx_id")
        photo_file_id = update.message.photo[-1].file_id
        
        update_tx_status(tx_id, "Accepted")
        tx = get_tx(tx_id)
        info_label = "🔑 **Coupon Code:**" if "topfollows" in str(tx[1]).lower() else "👤 **Sender ID:**"

        msg = (
            f"✅ **Your coin sale request was accepted and payment sent to your wallet!**\n\n"
            f"📋 **Transaction Details:**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 **Transaction ID:** `#{tx_id}`\n"
            f"🪙 **Coin Type:** {tx[1]}\n"
            f"{info_label} `{tx[7]}`\n"
            f"📦 **Coin Amount:** {tx[2]:,}\n"
            f"📱 **Payment Wallet:** {tx[3]}\n"
            f"Number: `{tx[4]}`\n"
            f"💰 **Paid Amount:** `{tx[5]} ৳`\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"Payment proof screenshot is attached below."
        )
        
        await context.bot.send_photo(chat_id=tx[0], photo=photo_file_id, caption=msg, parse_mode="Markdown")
        await update.message.reply_text("✅ **Payment details and proof successfully sent to customer!**")
        context.user_data["admin_step"] = None
        return

    # --- Admin Input Handlers ---
    if user_id == ADMIN_TELEGRAM_ID and admin_step == "AWAITING_NEW_PRICE" and text_input:
        try:
            new_p = float(text_input.strip())
            key = context.user_data.get("admin_coin_key")
            update_coin_price(key, new_p)
            context.user_data["admin_step"] = None
            await update.message.reply_text("✅ **Price successfully updated!**", reply_markup=get_admin_keyboard())
        except ValueError:
            await update.message.reply_text(txt["num_err"])
        return

    if user_id == ADMIN_TELEGRAM_ID and admin_step == "AWAITING_NEW_ACC" and text_input:
        new_acc = text_input.strip()
        key = context.user_data.get("admin_coin_key")
        update_coin_acc(key, new_acc)
        context.user_data["admin_step"] = None
        await update.message.reply_text("✅ **Receiving ID successfully updated!**", reply_markup=get_admin_keyboard())
        return

    if user_id == ADMIN_TELEGRAM_ID and admin_step == "AWAITING_BROADCAST_MSG" and text_input:
        broadcast_text = f"📢 **Public Announcement:**\n\n{text_input.strip()}"
        users = get_all_users()
        sent_count = 0
        for uid in users:
            try:
                await context.bot.send_message(chat_id=uid, text=broadcast_text, parse_mode="Markdown")
                sent_count += 1
            except Exception:
                pass
        context.user_data["admin_step"] = None
        await update.message.reply_text(f"✅ **Message successfully sent to {sent_count} users!**", reply_markup=get_admin_keyboard())
        return

    # --- Transaction Multi-step Inputs ---
    if step in ["AWAITING_USERNAME", "AWAITING_COUPON"] and text_input:
        if user_msg_id: temp_ids.append(user_msg_id)
        context.user_data["coin_info"] = text_input.strip()
        context.user_data["step"] = "AWAITING_AMOUNT"
        
        bot_prompt = await update.message.reply_text(txt["enter_amount"], reply_markup=get_amount_keyboard(), parse_mode="Markdown")
        temp_ids.append(bot_prompt.message_id)

    elif step == "AWAITING_CUSTOM_AMOUNT" and text_input:
        if user_msg_id: temp_ids.append(user_msg_id)
        try:
            amt = int(text_input.strip())
            if amt < 10000:
                err_msg = await update.message.reply_text(txt["min_amount_err"])
                temp_ids.append(err_msg.message_id)
                return
            
            context.user_data["amount"] = amt
            context.user_data["step"] = "AWAITING_METHOD"
            
            bot_prompt = await update.message.reply_text(txt["enter_method"], reply_markup=get_method_keyboard(), parse_mode="Markdown")
            temp_ids.append(bot_prompt.message_id)
        except ValueError:
            err_msg = await update.message.reply_text(txt["num_err"])
            temp_ids.append(err_msg.message_id)

    elif step == "AWAITING_CUSTOM_NUMBER" and text_input:
        if user_msg_id: temp_ids.append(user_msg_id)
        num = text_input.strip()
        method = context.user_data.get("method", "bKash")
        
        # ইউজারের দেওয়া নতুন মেথড এবং নাম্বার ডাটাবেজে অটো-সেভ করা
        save_user_wallet(user_id, method, num)
        
        await finalize_transaction(update, context, method, num, user_id, lang)

# --- ১১. লেনদেন সাবমিট এবং ফাইনাল মেসেজ প্রসেসর ---
async def finalize_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE, method: str, num: str, user_id: int, lang: str):
    txt = MESSAGES[lang]
    temp_ids = context.user_data.get("temp_msg_ids", [])
    
    coins = get_coins()
    key = context.user_data["selected_coin"]
    c = coins[key]
    amt = context.user_data["amount"]
    coin_info = context.user_data.get("coin_info", "N/A")

    net_taka = max(0, (amt / 1000) * c["price"] - 5)
    context.user_data["step"] = None

    user_obj = update.effective_user
    tx_id = add_transaction(user_id, user_obj.first_name, c["label"], amt, method, num, net_taka, coin_info)

    # ১. ইউজারকে ফাইনাল সাকসেস রসিদ পাঠানো
    user_msg_text = txt["tx_success"].format(
        tx_id=tx_id, coin=c['label'], amt=amt, method=method, num=num, taka=net_taka
    )
    
    if update.callback_query:
        await update.callback_query.message.reply_text(user_msg_text, reply_markup=get_main_inline_keyboard(lang), parse_mode="Markdown")
    else:
        await update.message.reply_text(user_msg_text, reply_markup=get_main_inline_keyboard(lang), parse_mode="Markdown")

    # ২. ৩ সেকেন্ডের মধ্যে চ্যাটের আগের সমস্ত কথোপকথন ডিলিট করা
    asyncio.create_task(delete_messages_after_delay(context, user_id, temp_ids, delay=3))
    context.user_data["temp_msg_ids"] = []

    # ৩. এডমিনকে নোটিফিকেশন পাঠানো
    info_type = "🎟 **Coupon Code:**" if key == "topfollows" else "👤 **Sender Username:**"
    admin_msg = (
        f"🚨 **New Coin Sale Request!**\n\n"
        f"🆔 **TX ID:** `#{tx_id}`\n"
        f"👤 **User:** {user_obj.first_name} (`{user_id}`)\n"
        f"🪙 **Coin:** {c['label']}\n"
        f"{info_type} `{coin_info}`\n"
        f"📦 **Amount:** {amt:,}\n"
        f"📱 **Method:** {method} (`{num}`)\n"
        f"💰 **Payable:** `{net_taka} ৳`\n\n"
        f"Please verify and choose action:"
    )
    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Accept & Pay", callback_data=f"admin_accept_{tx_id}"), InlineKeyboardButton("❌ Reject", callback_data=f"admin_reject_{tx_id}")]
    ])
    await context.bot.send_message(chat_id=ADMIN_TELEGRAM_ID, text=admin_msg, reply_markup=btn, parse_mode="Markdown")

# --- ১২. ব্যাকগ্রাউন্ড অটো টাস্ক ---
async def auto_ping_task(application: Application):
    while True:
        await asyncio.sleep(4000)
        users = get_all_users()
        ping_text = "⚡ **Bot Status:** System Active & Online! 🟢"
        
        for u_id in users:
            try:
                msg = await application.bot.send_message(chat_id=u_id, text=ping_text, parse_mode="Markdown")
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

    print("Bot is running with Auto-Saved Wallet Info & Professional Column Layout Buttons...")
    app.run_polling()

if __name__ == "__main__":
    main()
