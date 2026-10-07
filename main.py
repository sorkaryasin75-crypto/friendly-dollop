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
# Railway-এর Variables অপশন থেকে মানগুলো সংগ্রহ করা হবে, 
# না পাওয়া গেলে ডিফল্ট মান কাজ করবে।
BOT_TOKEN = os.getenv("BOT_TOKEN", "8773492019:AAEJD2EvVgUgtaNvJyD-9goqA8hknG-tY58")
ADMIN_TELEGRAM_ID = int(os.getenv("ADMIN_TELEGRAM_ID", "6819070790"))
DB_NAME = "bot_database.db"


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# --- ২. বহুভাষিক টেক্সট অভিধান (Localization Texts) ---
MESSAGES = {
    "bn": {
        "welcome": "👋 **Sell Point IT**-এ আপনাকে স্বাগতম!\n\nনিচের মেনু বা বাটন থেকে আপনার সেবা নির্বাচন করুন:",
        "rates_title": "📊 **লাইভ মার্কেট রেট (প্রতি ১০০০ কয়েন):**\n\n",
        "active": "✅ সক্রিয়",
        "inactive": "❌ নিষ্ক্রিয়",
        "sell_title": "🛒 **কোন কয়েনটি বিক্রি করতে চান বেছে নিন:**\n*(সর্বনিম্ন ১০,০০০)*",
        "enter_coupon": "✏️ **ধাপ ১:** আপনার Topfollow / Coupon Code-টি প্রদান করুন:",
        "enter_username": "📥 এডমিনের কয়েন রিসিভিং আইডি: `{acc}`\n\nপ্রথমে অ্যাপ থেকে উপরের ইউজারনেমে কয়েন সেন্ড করুন।\n♻️ যে আইডি থেকে কয়েন পাঠিয়েছেন সেই ইউজারনেমটি (Sender Username) এখানে লিখুন:",
        "enter_amount": "✏️ কত পরিমাণ কয়েন বিক্রি করতে চান লিখুন (যেমন: 10000):",
        "min_amount_err": "⚠️ সর্বনিম্ন ১০,০০০ কয়েন হতে হবে।",
        "num_err": "⚠️ অনুগ্রহ করে সঠিক সংখ্যা লিখুন:",
        "enter_method": "✏️ পেমেন্ট মেথড লিখুন (যেমন: বিকাশ / নগদ / রকেট):",
        "enter_number": "✏️ আপনার পেমেন্ট নম্বরটি লিখুন:",
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
    },
    "en": {
        "welcome": "👋 Welcome to **Sell Point IT**!\n\nPlease select an option from the menu below:",
        "rates_title": "📊 **Live Market Rates (Per 1000 Coins):**\n\n",
        "active": "✅ Active",
        "inactive": "❌ Inactive",
        "sell_title": "🛒 **Select the coin you want to sell:**\n*(Minimum 10,000)*",
        "enter_coupon": "✏️ **Step 1:** Enter your Coupon Code:",
        "enter_username": "📥 Admin's Receiving ID: `{acc}`\n\nFirst send coins to the username above.\n♻️ Enter your Sender Username below:",
        "enter_amount": "✏️ Enter the coin amount to sell (e.g., 10000):",
        "min_amount_err": "⚠️ Minimum amount is 10,000 coins.",
        "num_err": "⚠️ Please enter a valid number:",
        "enter_method": "✏️ Enter payment method (e.g., bKash / Nagad / Rocket):",
        "enter_number": "✏️ Enter your account/mobile number:",
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
    }
}

# --- ৩. SQLite ডাটাবেজ সেটআপ (Fast Performance Setup) ---
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
            lang TEXT DEFAULT 'bn'
        )
    ''')
    
    # সকল কয়েন অন্তর্ভুক্ত করা হলো (কলাম লেআউট ও নতুন কয়েন)
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
    cursor.execute("INSERT OR IGNORE INTO users (user_id, lang) VALUES (?, 'bn')", (user_id,))
    conn.commit()
    conn.close()

def get_user_lang(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT lang FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else "bn"

def set_user_lang(user_id, lang):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET lang = ? WHERE user_id = ?", (lang, user_id))
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

# --- ৫. Main Menu with Inline Keyboard Markup (Column Button Layout) ---
def get_main_inline_keyboard(lang="bn"):
    txt = MESSAGES[lang]
    # Single Column Layout (প্রত্যেকটি বাটন আলাদা সারিতে বা কলাম আকারে থাকবে)
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

def get_main_reply_keyboard(lang="bn"):
    txt = MESSAGES[lang]
    keyboard = [
        [KeyboardButton(txt["btn_sell"]), KeyboardButton(txt["btn_rates"])],
        [KeyboardButton(txt["btn_history"]), KeyboardButton(txt["btn_leaderboard"])],
        [KeyboardButton(txt["btn_lang"]), KeyboardButton(txt["btn_support"])]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_language_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇧🇩 বাংলা (Bangla)", callback_data="set_lang_bn")],
        [InlineKeyboardButton("🇺🇸 English", callback_data="set_lang_en")]
    ])

# --- ৬. বট স্টার্ট হ্যান্ডলার ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user(user_id)
    lang = get_user_lang(user_id)
    txt = MESSAGES[lang]
    
    inline_markup = get_main_inline_keyboard(lang)
    reply_markup = get_main_reply_keyboard(lang)
    
    text = txt["welcome"]
    if update.message:
        await update.message.reply_text(text, reply_markup=inline_markup, parse_mode="Markdown")
        await update.message.reply_text("⬇️ Quick Bottom Menu Loaded:", reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(text, reply_markup=inline_markup, parse_mode="Markdown")

# --- ৭. এডমিন প্যানেল UI ---
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
        "⚙️ **Admin Panel - Dynamic Control**\n\nনিচের যেকোনো কয়েন সিলেক্ট করে দাম, অ্যাকাউন্ট এবং অ্যাক্টিভ/ইনঅ্যাক্টিভ স্ট্যাটাস পরিবর্তন করুন:",
        reply_markup=get_admin_keyboard(),
        parse_mode="Markdown"
    )

# --- ৮. কলব্যাক হ্যান্ডলার ---
async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    lang = get_user_lang(user_id)
    txt = MESSAGES[lang]

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
                info_text = f"🔑 কুপন: `{row[5]}`" if "topfollows" in str(row[1]).lower() else f"👤 প্রেরক আইডি: `{row[5]}`"
                text += f"🆔 `#{row[0]}` | **{row[1]}**\n{info_text}\n📦 পরিমাণ: {row[2]:,} | 💰 {row[3]} ৳\nস্ট্যাটাস: {st_icon} **{row[4]}**\n----------------------\n"
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

    # --- সেল কয়েন সিলেক্ট ---
    elif data.startswith("sell_"):
        key = data.split("_")[1]
        coins = get_coins()
        c = coins.get(key)
        context.user_data["selected_coin"] = key
        
        if key == "topfollows":
            context.user_data["step"] = "AWAITING_COUPON"
            await query.edit_message_text(txt["enter_coupon"], parse_mode="Markdown")
        else:
            admin_acc = c.get("recv_acc", "N/A")
            context.user_data["step"] = "AWAITING_USERNAME"
            msg = txt["enter_username"].format(acc=admin_acc)
            await query.edit_message_text(msg, parse_mode="Markdown")

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
            f"⚙️ **ম্যানেজ কয়েন:** {c['label']}\n"
            f"💰 বর্তমান দাম: `{c['price']}` ৳\n"
            f"📥 রিসিভিং আইডি: `{c['recv_acc']}`\n"
            f"📊 স্ট্যাটাস: {st_txt}\n\n"
            f"পরিবর্তন করতে নিচের অপশন নির্বাচন করুন:"
        )
        btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("✏️ দাম পরিবর্তন", callback_data=f"adm_p_{key}"), InlineKeyboardButton("✏️ রিসিভিং আইডি পরিবর্তন", callback_data=f"adm_a_{key}")],
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
        await query.answer("স্ট্যাটাস পরিবর্তন করা হয়েছে!")
        await handle_callbacks(update, context)

    elif data.startswith("adm_p_"):
        if user_id != ADMIN_TELEGRAM_ID: return
        key = data.split("_")[2]
        context.user_data["admin_coin_key"] = key
        context.user_data["admin_step"] = "AWAITING_NEW_PRICE"
        await query.edit_message_text("✏️ নতুন দাম লিখুন (প্রতি ১০০০ কয়েন):")

    elif data.startswith("adm_a_"):
        if user_id != ADMIN_TELEGRAM_ID: return
        key = data.split("_")[2]
        context.user_data["admin_coin_key"] = key
        context.user_data["admin_step"] = "AWAITING_NEW_ACC"
        await query.edit_message_text("✏️ নতুন রিসিভিং আইডি/ইউজারনেম লিখুন:")

    elif data == "adm_broadcast":
        if user_id != ADMIN_TELEGRAM_ID: return
        context.user_data["admin_step"] = "AWAITING_BROADCAST_MSG"
        await query.edit_message_text("📢 **পাবলিক মেসেজ ইনপুট দিন:**\n\n(এই মেসেজটি বটের সমস্ত ইউজারের কাছে পাঠানো হবে)")

# --- ৯. ইনপুট ও মেনু বাটন হ্যান্ডলার ---
async def handle_inputs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user(user_id)
    lang = get_user_lang(user_id)
    txt = MESSAGES[lang]
    text_input = update.message.text if update.message else ""
    admin_step = context.user_data.get("admin_step")
    step = context.user_data.get("step")

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
                info_text = f"🔑 কুপন: `{row[5]}`" if "topfollows" in str(row[1]).lower() else f"👤 প্রেরক আইডি: `{row[5]}`"
                text += f"🆔 `#{row[0]}` | **{row[1]}**\n{info_text}\n📦 পরিমাণ: {row[2]:,} | 💰 {row[3]} ৳\nস্ট্যাটাস: {st_icon} **{row[4]}**\n----------------------\n"
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
        info_label = "🔑 **কুপন কোড:**" if "topfollows" in str(tx[1]).lower() else "👤 **প্রেরক আইডি:**"

        msg = (
            f"✅ **আপনার কয়েন সেল রিকোয়েস্ট একসেপ্ট হয়েছে এবং আপনার দেওয়া ওয়ালেটে পেমেন্ট করা হয়েছে!**\n\n"
            f"📋 **লেনদেনের বিস্তারিত বিবরণ:**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 **Transaction ID:** `#{tx_id}`\n"
            f"🪙 **কয়েন টাইপ:** {tx[1]}\n"
            f"{info_label} `{tx[7]}`\n"
            f"📦 **কয়েন পরিমাণ:** {tx[2]:,}\n"
            f"📱 **পেমেন্ট ওয়ালেট:** {tx[3]}\n"
            f"নম্বর: `{tx[4]}`\n"
            f"💰 **পেমেন্টকৃত টাকা:** `{tx[5]} ৳`\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"প্রমাণস্বরূপ পেমেন্ট স্ক্রিনশটটি প্রদান করা হলো।"
        )
        
        await context.bot.send_photo(chat_id=tx[0], photo=photo_file_id, caption=msg, parse_mode="Markdown")
        await update.message.reply_text("✅ **পেমেন্ট ডিটেইলস ও প্রুফ কাস্টমারের কাছে সফলভাবে পাঠানো হয়েছে!**")
        context.user_data["admin_step"] = None
        return

    # --- Admin Input Handlers ---
    if user_id == ADMIN_TELEGRAM_ID and admin_step == "AWAITING_NEW_PRICE" and text_input:
        try:
            new_p = float(text_input.strip())
            key = context.user_data.get("admin_coin_key")
            update_coin_price(key, new_p)
            context.user_data["admin_step"] = None
            await update.message.reply_text("✅ **দাম সফলভাবে আপডেট করা হয়েছে!**", reply_markup=get_admin_keyboard())
        except ValueError:
            await update.message.reply_text(txt["num_err"])
        return

    if user_id == ADMIN_TELEGRAM_ID and admin_step == "AWAITING_NEW_ACC" and text_input:
        new_acc = text_input.strip()
        key = context.user_data.get("admin_coin_key")
        update_coin_acc(key, new_acc)
        context.user_data["admin_step"] = None
        await update.message.reply_text("✅ **রিসিভিং আইডি সফলভাবে আপডেট করা হয়েছে!**", reply_markup=get_admin_keyboard())
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
        await update.message.reply_text(f"✅ **মোট {sent_count} জন ইউজারের কাছে মেসেজ সফলভাবে পাঠানো হয়েছে!**", reply_markup=get_admin_keyboard())
        return

    # --- Transaction Process Multi-step Inputs ---
    if step in ["AWAITING_USERNAME", "AWAITING_COUPON"] and text_input:
        context.user_data["coin_info"] = text_input.strip()
        context.user_data["step"] = "AWAITING_AMOUNT"
        await update.message.reply_text(txt["enter_amount"])

    elif step == "AWAITING_AMOUNT" and text_input:
        try:
            amt = int(text_input.strip())
            if amt < 10000:
                await update.message.reply_text(txt["min_amount_err"])
                return
            context.user_data["amount"] = amt
            context.user_data["step"] = "AWAITING_METHOD"
            await update.message.reply_text(txt["enter_method"])
        except ValueError:
            await update.message.reply_text(txt["num_err"])

    elif step == "AWAITING_METHOD" and text_input:
        context.user_data["method"] = text_input.strip()
        context.user_data["step"] = "AWAITING_NUMBER"
        await update.message.reply_text(txt["enter_number"])

    elif step == "AWAITING_NUMBER" and text_input:
        num = text_input.strip()
        coins = get_coins()
        key = context.user_data["selected_coin"]
        c = coins[key]
        amt = context.user_data["amount"]
        method = context.user_data["method"]
        coin_info = context.user_data.get("coin_info", "N/A")

        net_taka = max(0, (amt / 1000) * c["price"] - 5)
        context.user_data["step"] = None

        tx_id = add_transaction(user_id, update.effective_user.first_name, c["label"], amt, method, num, net_taka, coin_info)

        user_msg = txt["tx_success"].format(
            tx_id=tx_id, coin=c['label'], amt=amt, method=method, num=num, taka=net_taka
        )
        await update.message.reply_text(user_msg, reply_markup=get_main_inline_keyboard(lang), parse_mode="Markdown")

        info_type = "🎟 **কুপন কোড:**" if key == "topfollows" else "👤 **প্রেরক ইউজারনেম:**"
        admin_msg = (
            f"🚨 **নতুন কয়েন সেল রিকোয়েস্ট!**\n\n"
            f"🆔 **TX ID:** `#{tx_id}`\n"
            f"👤 **ইউজার:** {update.effective_user.first_name} (`{user_id}`)\n"
            f"🪙 **কয়েন:** {c['label']}\n"
            f"{info_type} `{coin_info}`\n"
            f"📦 **পরিমাণ:** {amt:,}\n"
            f"📱 **মেথড:** {method} (`{num}`)\n"
            f"💰 **দেয় টাকা:** `{net_taka} ৳`\n\n"
            f"যাচাই করে বাটন সিলেক্ট করুন:"
        )
        btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Accept & Pay", callback_data=f"admin_accept_{tx_id}"), InlineKeyboardButton("❌ Reject", callback_data=f"admin_reject_{tx_id}")]
        ])
        await context.bot.send_message(chat_id=ADMIN_TELEGRAM_ID, text=admin_msg, reply_markup=btn, parse_mode="Markdown")

# --- ১০. ব্যাকগ্রাউন্ড অটো টাস্ক ---
async def auto_ping_task(application: Application):
    while True:
        await asyncio.sleep(400)
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

# --- ১১. বট মেইন এক্সিকিউশন ---
def main():
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(handle_callbacks))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_inputs))

    print("Bot is running with Column Layout Main Menu and Updated Coins List...")
    app.run_polling()

if __name__ == "__main__":
    main()
