import asyncio
import logging
import sqlite3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# --- ১. কনফিগারেশন ---
BOT_TOKEN = "8773492019:AAEJD2EvVgUgtaNvJyD-9goqA8hknG-tY58"
ADMIN_TELEGRAM_ID = 6819070790
DB_NAME = "bot_database.db"

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# --- ২. SQLite ডাটাবেজ সেটআপ ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # কয়েন টেবিল (স্বয়ংক্রিয় অ্যাডমিন একাউন্ট ও স্ট্যাটাস সহ)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS coins (
            key TEXT PRIMARY KEY,
            label TEXT,
            price REAL,
            active INTEGER,
            recv_acc TEXT
        )
    ''')
    
    # ইউজার টেবিল (পাবলিক/অটো মেসেজ পাঠানোর জন্য)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY
        )
    ''')
    
    # ডিফল্ট কয়েন তথ্য ইনসার্ট (যদি না থাকে)
    cursor.execute("INSERT OR IGNORE INTO coins VALUES ('niva', 'Niva Coin', 5.0, 1, 'sell_point_it')")
    cursor.execute("INSERT OR IGNORE INTO coins VALUES ('NewTop', 'NewTop Coin', 3.0, 1, 'AdminNewTopID')")
    cursor.execute("INSERT OR IGNORE INTO coins VALUES ('topfollows', 'Topfollows Coin', 3.0, 1, 'N/A')")
    cursor.execute("INSERT OR IGNORE INTO coins VALUES ('ns', 'NS Coin', 8.0, 1, 'himelorkar019')")

    # লেনদেন টেবিল
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
    
    conn.commit()
    conn.close()

init_db()

# --- ৩. ডাটাবেজ হেল্পার ফাংশন ---
def add_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
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

# --- ৪. কিবোর্ড ও বট হ্যান্ডলার ---
def get_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Sell Coins", callback_data="menu_sell"), InlineKeyboardButton("📊 Live Rates", callback_data="menu_rates")],
        [InlineKeyboardButton("🏆 Leaderboard", callback_data="menu_leaderboard"), InlineKeyboardButton("📜 My History", callback_data="menu_history")],
        [InlineKeyboardButton("📢 Channel", url="https://t.me/EducationPointBD"), InlineKeyboardButton("👨‍💻 Support", url="https://t.me/educationpointbd24")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user(user_id) # ডাটাবেজে ইউজার যুক্ত করা
    text = "👋 **Sell Point IT**-এ আপনাকে স্বাগতম!\n\nনিচের অপশনগুলো থেকে আপনার লেনদেন পরিচালনা করুন:"
    if update.message:
        await update.message.reply_text(text, reply_markup=get_main_keyboard(), parse_mode="Markdown")
    else:
        await update.callback_query.edit_message_text(text, reply_markup=get_main_keyboard(), parse_mode="Markdown")

# --- ৫. এডমিন প্যানেল UI ---
def get_admin_keyboard():
    coins = get_coins()
    keyboard = []
    for k, c in coins.items():
        st = "🟢" if c["active"] else "🔴"
        keyboard.append([
            InlineKeyboardButton(f"{st} {c['label']}", callback_data=f"adm_manage_{k}")
        ])
    keyboard.append([InlineKeyboardButton("📢 Send Public Broadcast", callback_data="adm_broadcast")])
    return InlineKeyboardMarkup(keyboard)

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_TELEGRAM_ID:
        return
    await update.message.reply_text(
        "⚙️ **Admin Panel - Dynamic Control**\n\nনিচের যেকোনো কয়েন সিলেক্ট করে দাম, অ্যাকাউন্ট এবং অ্যাক্টিভ/ইনঅ্যাক্টিভ স্ট্যাটাস পরিবর্তন করুন:",
        reply_markup=get_admin_keyboard(),
        parse_mode="Markdown"
    )

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "main_menu":
        await start(update, context)

    # --- লাইভ রেট ---
    elif data == "menu_rates":
        coins = get_coins()
        text = "📊 **Live Market Rates (প্রতি ১০০০ কয়েন):**\n\n"
        for k, c in coins.items():
            st = "✅ Active" if c["active"] else "❌ Inactive"
            text += f"• **{c['label']}**: {c['price']} ৳ ({st})\n"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]), parse_mode="Markdown")

    # --- সেল মেনু ---
    elif data == "menu_sell":
        coins = get_coins()
        keyboard = []
        for k, c in coins.items():
            if c["active"]:
                keyboard.append([InlineKeyboardButton(f"Sell {c['label']} ({c['price']}৳/1K)", callback_data=f"sell_{k}")])
        keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
        await query.edit_message_text("🛒 **কোন কয়েনটি বিক্রি করতে চান বেছে নিন:**\n*(সর্বনিম্ন ৫০,০০০)*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data.startswith("sell_"):
        key = data.split("_")[1]
        coins = get_coins()
        c = coins.get(key)
        context.user_data["selected_coin"] = key
        
        if key == "topfollows":
            context.user_data["step"] = "AWAITING_COUPON"
            await query.edit_message_text("✏️ **ধাপ ১:** আপনার Topfollow **Coupon Code**-টি প্রদান করুন:")
        else:
            admin_acc = c.get("recv_acc", "N/A")
            context.user_data["step"] = "AWAITING_USERNAME"
            msg = (
                f"📥 এডমিনের কয়েন রিসিভিং আইডি:`{admin_acc}`\n\n"
                f"প্রথমে অ্যাপ থেকে উপরের ইউজারনেমে কয়েন সেন্ড করুন।\n"
                f"♻️যে আইডি থেকে কয়েন পাঠিয়েছেন সেই ইউজারনেম (Sender Username) -টি পেস্ট করুন:"
            )
            await query.edit_message_text(msg, parse_mode="Markdown")

    # --- লিডারবোর্ড ---
    elif data == "menu_leaderboard":
        lb = get_leaderboard()
        text = "🏆 **Public Leaderboard (Top Sellers)**\n\n"
        if not lb:
            text += "এখনো কোনো সফল লেনদেন হয়নি।"
        else:
            for idx, row in enumerate(lb, start=1):
                text += f"{idx}. **{row[0]}** — {row[1]:,} Coins ({row[2]} Sales)\n"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]), parse_mode="Markdown")

    # --- পার্সোনাল হিস্ট্রি ---
    elif data == "menu_history":
        history = get_user_history(user_id)
        text = "📜 **আপনার পার্সোনাল সেল হিস্ট্রি:**\n\n"
        if not history:
            text += "আপনার কোনো হিস্ট্রি পাওয়া যায়নি।"
        else:
            for row in history:
                st_icon = "⏳" if row[4] == "Pending" else ("✅" if row[4] == "Accepted" else "❌")
                info_text = f"🔑 কুপন: `{row[5]}`" if "topfollows" in str(row[1]).lower() else f"👤 প্রেরক আইডি: `{row[5]}`"
                text += f"🆔 `#{row[0]}` | **{row[1]}**\n{info_text}\n📦 পরিমাণ: {row[2]:,} | 💰 {row[3]} ৳\nস্ট্যাটাস: {st_icon} **{row[4]}**\n----------------------\n"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]), parse_mode="Markdown")

    # --- এডমিন একসেপ্ট / রিজেক্ট বাটন ---
    elif data.startswith("admin_accept_") or data.startswith("admin_reject_"):
        if user_id != ADMIN_TELEGRAM_ID:
            return
        parts = data.split("_")
        action = parts[1]
        tx_id = int(parts[2])

        if action == "reject":
            update_tx_status(tx_id, "Rejected")
            tx = get_tx(tx_id)
            await context.bot.send_message(
                chat_id=tx[0],
                text=f"❌ **আপনার সেল রিকোয়েস্ট (ID: #{tx_id}) রিজেক্ট করা হয়েছে।**\nকয়েন ভেরিফিকেশন অথবা প্রদানকৃত তথ্য সঠিক ছিল না।",
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
            f"⚙️ **ম্যানেজ কয়েন:** {c['label']}\n"
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

    elif data.startswith("adm_t_"): # Active/Inactive Toggle
        if user_id != ADMIN_TELEGRAM_ID: return
        key = data.split("_")[2]
        toggle_coin_active(key)
        await query.answer("স্ট্যাটাস পরিবর্তন করা হয়েছে!")
        # Refresh Panel
        await handle_callbacks(update, context)

    elif data.startswith("adm_p_"): # Edit Price
        if user_id != ADMIN_TELEGRAM_ID: return
        key = data.split("_")[2]
        context.user_data["admin_coin_key"] = key
        context.user_data["admin_step"] = "AWAITING_NEW_PRICE"
        await query.edit_message_text("✏️ নতুন দাম লিখুন (প্রতি ১০০০ কয়েন):")

    elif data.startswith("adm_a_"): # Edit Recv Account
        if user_id != ADMIN_TELEGRAM_ID: return
        key = data.split("_")[2]
        context.user_data["admin_coin_key"] = key
        context.user_data["admin_step"] = "AWAITING_NEW_ACC"
        await query.edit_message_text("✏️ নতুন রিসিভিং আইডি/ইউজারনেম লিখুন:")

    elif data == "adm_broadcast": # Public Message Broadcast
        if user_id != ADMIN_TELEGRAM_ID: return
        context.user_data["admin_step"] = "AWAITING_BROADCAST_MSG"
        await query.edit_message_text("📢 **পাবলিক মেসেজ ইনপুট দিন:**\n\n(এই মেসেজটি বটের সমস্ত ইউজারের কাছে পাঠানো হবে)")

# --- ৬. ইনপুট হ্যান্ডলার ---
async def handle_inputs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user(user_id)
    admin_step = context.user_data.get("admin_step")
    step = context.user_data.get("step")

    # এডমিন স্ক্রিনশট প্রসেস ও কাস্টমার নোটিফিকেশন
    if user_id == ADMIN_TELEGRAM_ID and admin_step == "AWAITING_PROOF" and update.message.photo:
        tx_id = context.user_data.get("pending_tx_id")
        photo_file_id = update.message.photo[-1].file_id
        
        update_tx_status(tx_id, "Accepted")
        tx = get_tx(tx_id)

        info_label = "🔑 **কুপন কোড:**" if "topfollows" in str(tx[1]).lower() else "👤 **প্রেরক আইডি:**"

        msg = (
            f"✅ **আপনার কয়েন সেল রিকোয়েস্ট একসেপ্ট হয়েছে এবং আপনার দেওয়া ওয়ালেটে পেমেন্ট করা হয়েছে!**\n\n"
            f"📋 **লেনদেনের বিস্তারিত বিবরণ:**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 **Transaction ID:** `#{tx_id}`\n"
            f"🪙 **কয়েন টাইপ:** {tx[1]}\n"
            f"{info_label} `{tx[7]}`\n"
            f"📦 **কয়েন পরিমাণ:** {tx[2]:,}\n"
            f"📱 **পেমেন্ট ওয়ালেট:** {tx[3]}\n"
            f"নম্বর: `{tx[4]}`\n"
            f"💰 **পেমেন্টকৃত টাকা:** `{tx[5]} ৳`\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"প্রমাণস্বরূপ পেমেন্ট স্ক্রিনশটটি প্রদান করা হলো।"
        )
        
        await context.bot.send_photo(
            chat_id=tx[0], 
            photo=photo_file_id, 
            caption=msg, 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Start Menu", callback_data="start")]]),
            parse_mode="Markdown"
        )
        await update.message.reply_text("✅ **পেমেন্ট ডিটেইলস ও প্রুফ কাস্টমারের কাছে সফলভাবে পাঠানো হয়েছে!**")
        context.user_data["admin_step"] = None
        return

    # এডমিন প্রাইস আপডেট
    if user_id == ADMIN_TELEGRAM_ID and admin_step == "AWAITING_NEW_PRICE" and update.message.text:
        try:
            new_p = float(update.message.text.strip())
            key = context.user_data.get("admin_coin_key")
            update_coin_price(key, new_p)
            context.user_data["admin_step"] = None
            await update.message.reply_text("✅ **দাম সফলভাবে আপডেট করা হয়েছে!**", reply_markup=get_admin_keyboard())
        except ValueError:
            await update.message.reply_text("⚠️ সঠিক সংখ্যা লিখুন:")
        return

    # এডমিন রিসিভিং আইডি আপডেট
    if user_id == ADMIN_TELEGRAM_ID and admin_step == "AWAITING_NEW_ACC" and update.message.text:
        new_acc = update.message.text.strip()
        key = context.user_data.get("admin_coin_key")
        update_coin_acc(key, new_acc)
        context.user_data["admin_step"] = None
        await update.message.reply_text("✅ **রিসিভিং আইডি সফলভাবে আপডেট করা হয়েছে!**", reply_markup=get_admin_keyboard())
        return

    # এডমিন ম্যানুয়াল ব্রডকাস্ট মেসেজ
    if user_id == ADMIN_TELEGRAM_ID and admin_step == "AWAITING_BROADCAST_MSG" and update.message.text:
        broadcast_text = f"📢 **Public Announcement:**\n\n{update.message.text.strip()}"
        users = get_all_users()
        sent_count = 0
        for uid in users:
            try:
                await context.bot.send_message(chat_id=uid, text=broadcast_text, parse_mode="Markdown")
                sent_count += 1
            except Exception:
                pass
        context.user_data["admin_step"] = None
        await update.message.reply_text(f"✅ **মোট {sent_count} জন ইউজারের কাছে মেসেজ সফলভাবে পাঠানো হয়েছে!**", reply_markup=get_admin_keyboard())
        return

    # ১. ইউজারনেম / কুপন গ্রহণ
    if step in ["AWAITING_USERNAME", "AWAITING_COUPON"] and update.message.text:
        context.user_data["coin_info"] = update.message.text.strip()
        context.user_data["step"] = "AWAITING_AMOUNT"
        await update.message.reply_text("✏️ কত পরিমাণ কয়েন বিক্রি করতে চান লিখুন (যেমন: 10000):")

    # ২. কয়েন পরিমাণ
    elif step == "AWAITING_AMOUNT" and update.message.text:
        try:
            amt = int(update.message.text.strip())
            if amt < 10000:
                await update.message.reply_text("⚠️ সর্বনিম্ন ১০,০০০ কয়েন দিতে হবে।")
                return
            context.user_data["amount"] = amt
            context.user_data["step"] = "AWAITING_METHOD"
            await update.message.reply_text("✏️ পেমেন্ট মেথড লিখুন (যেমন: বিকাশ / নগদ / রকেট):")
        except ValueError:
            await update.message.reply_text("⚠️ সঠিক সংখ্যা লিখুন:")

    # ৩. পেমেন্ট মেথড
    elif step == "AWAITING_METHOD" and update.message.text:
        context.user_data["method"] = update.message.text.strip()
        context.user_data["step"] = "AWAITING_NUMBER"
        await update.message.reply_text("✏️ বিকাশ নগদ রকেট নম্বরটি লিখুন:")

    # ৪. নম্বর গ্রহণ ও নোটিফিকেশন
    elif step == "AWAITING_NUMBER" and update.message.text:
        num = update.message.text.strip()
        coins = get_coins()
        key = context.user_data["selected_coin"]
        c = coins[key]
        amt = context.user_data["amount"]
        method = context.user_data["method"]
        coin_info = context.user_data.get("coin_info", "N/A")

        net_taka = max(0, (amt / 1000) * c["price"] - 5)
        context.user_data["step"] = None

        tx_id = add_transaction(user_id, update.effective_user.first_name, c["label"], amt, method, num, net_taka, coin_info)

        info_type = "🎟 **কুপন কোড:**" if key == "topfollows" else "👤 **প্রেরক ইউজারনেম:**"

        user_msg = (
            f"🎉 **আপনার কয়েন সেল রিকোয়েস্টটি সফলভাবে জমা হয়েছে!**\n\n"
            f"📋 **আপনার জমা দেওয়া তথ্যের বিবরণ:**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 **TX ID:** `#{tx_id}`\n"
            f"🪙 **কয়েন:** {c['label']}\n"
            f"{info_type} `{coin_info}`\n"
            f"📦 **পরিমাণ:** {amt:,}\n"
            f"📱 **মেথড:** {method}\n"
            f"📞 **নম্বর:** `{num}`\n"
            f"💰 **প্রাপ্য টাকা:** `{net_taka} ৳` (চার্জ -৫৳)\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"⏳ এডমিন অতি শীঘ্রই কয়েন ভেরিফাই করে আপনার নাম্বারে পেমেন্ট সম্পন্ন করবে।"
        )

        await update.message.reply_text(user_msg, reply_markup=get_main_keyboard(), parse_mode="Markdown")

        admin_msg = (
            f"🚨 **নতুন কয়েন সেল রিকোয়েস্ট!**\n\n"
            f"🆔 **TX ID:** `#{tx_id}`\n"
            f"👤 **ইউজার:** {update.effective_user.first_name} (`{user_id}`)\n"
            f"🪙 **কয়েন:** {c['label']}\n"
            f"{info_type} `{coin_info}`\n"
            f"📦 **পরিমাণ:** {amt:,}\n"
            f"📱 **মেথড:** {method} (`{num}`)\n"
            f"💰 **দেয় টাকা:** `{net_taka} ৳`\n\n"
            f"যাচাই করে বাটন সিলেক্ট করুন:"
        )
        btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Accept & Pay", callback_data=f"admin_accept_{tx_id}"), InlineKeyboardButton("❌ Reject", callback_data=f"admin_reject_{tx_id}")]
        ])
        await context.bot.send_message(chat_id=ADMIN_TELEGRAM_ID, text=admin_msg, reply_markup=btn, parse_mode="Markdown")

# --- ৭. ৪০০ সেকেণ্ড অটো মেসেজ ও ১২০ সেকেণ্ডে রিমুভ ব্যাকগ্রাউন্ড টাস্ক ---
async def auto_ping_task(application: Application):
    """প্রতি ৪০০ সেকেন্ড পর পর ব্রডকাস্ট মেসেজ পাঠাবে এবং ১২০ সেকেন্ড পর তা ডিলেট করে দেবে।"""
    while True:
        await asyncio.sleep(5)
        users = get_all_users()
        ping_text = "⚡ **Bot Status:** System Active & Online! 🟢"
        
        for u_id in users:
            try:
                msg = await application.bot.send_message(chat_id=u_id, text=ping_text, parse_mode="Markdown")
                # ১২০ সেকেন্ড পর মেসেজ অটো ডিলেট
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
    # বট স্টার্ট হওয়ার পর অটো ব্যাকগ্রাউন্ড টাস্ক চালু করা
    asyncio.create_task(auto_ping_task(application))

# --- ৮. বট স্টার্ট ---
def main():
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(handle_callbacks))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_inputs))

    print("Bot is running with full dynamic features & auto vanish ping task...")
    app.run_polling()

if __name__ == "__main__":
    main()

