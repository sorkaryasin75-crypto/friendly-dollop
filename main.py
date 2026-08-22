import sqlite3
import logging
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
BOT_TOKEN = "8773492019:AAEJD2EvVgUgtaNvJyD-9goqA8hknG-tY58"  # আপনার বট টোকেন দিন
ADMIN_TELEGRAM_ID = 6819070790  # আপনার টেলিগ্রাম UID
DB_NAME = "bot_database.db"

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# --- ২. SQLite ডাটাবেজ সেটআপ ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # কয়েন টেবিল (দাম ও স্ট্যাটাস রাখার জন্য)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS coins (
            key TEXT PRIMARY KEY,
            label TEXT,
            price REAL,
            active INTEGER
        )
    ''')
    
    # প্রাথমিক কয়েনের ডাটা
    cursor.execute("INSERT OR IGNORE INTO coins VALUES ('niva', 'Niva Coin', 5.0, 1)")
    cursor.execute("INSERT OR IGNORE INTO coins VALUES ('NewTop', 'NewTop Coin', 3.0, 1)")
    cursor.execute("INSERT OR IGNORE INTO coins VALUES ('topfollows', 'Topfollows Coin', 3.0, 1)")
    cursor.execute("INSERT OR IGNORE INTO coins VALUES ('ns', 'NS Coin', 8.0, 1)")

    # লেনদেন হিস্ট্রি টেবিল
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
            status TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

# --- ৩. ডাটাবেজ হেল্পার ফাংশন ---
def get_coins():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT key, label, price, active FROM coins")
    rows = cursor.fetchall()
    conn.close()
    return {r[0]: {"label": r[1], "price": r[2], "active": bool(r[3])} for r in rows}

def update_coin_price(key, new_price):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE coins SET price = ? WHERE key = ?", (new_price, key))
    conn.commit()
    conn.close()

def add_transaction(user_id, user_name, coin_label, coin_amount, method, number, net_taka):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transactions (user_id, user_name, coin_label, coin_amount, payment_method, account_number, net_taka, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending')
    ''', (user_id, user_name, coin_label, coin_amount, method, number, net_taka))
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
    cursor.execute("SELECT user_id, coin_label, coin_amount, payment_method, account_number, net_taka, status FROM transactions WHERE id = ?", (tx_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def get_user_history(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, coin_label, coin_amount, net_taka, status FROM transactions WHERE user_id = ? ORDER BY id DESC LIMIT 10", (user_id,))
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
    text = "👋 **Earning Elevated**-এ আপনাকে স্বাগতম!\n\nনিচের অপশনগুলো থেকে আপনার লেনদেন পরিচালনা করুন:"
    if update.message:
        await update.message.reply_text(text, reply_markup=get_main_keyboard(), parse_mode="Markdown")
    else:
        await update.callback_query.edit_message_text(text, reply_markup=get_main_keyboard(), parse_mode="Markdown")

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "main_menu":
        await start(update, context)

    # --- লাইভ রেট (Realtime SQLite থেকে লোড হবে) ---
    elif data == "menu_rates":
        coins = get_coins()
        text = "📊 **Live Market Rates (প্রতি ১০০০ কয়েন):**\n\n"
        for k, c in coins.items():
            st = "✅ Active" if c["active"] else "❌ Inactive"
            text += f"• **{c['label']}**: {c['price']} ৳ ({st})\n"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]), parse_mode="Markdown")

    # --- সেল মেনু ---
    elif data == "menu_sell":
        coins = get_coins()
        keyboard = []
        for k, c in coins.items():
            if c["active"]:
                keyboard.append([InlineKeyboardButton(f"Sell {c['label']} ({c['price']}৳/1K)", callback_data=f"sell_{k}")])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="main_menu")])
        await query.edit_message_text("🛒 **কোন কয়েনটি বিক্রি করতে চান বেছে নিন:**\n*(সর্বনিম্ন ৫০,০০০)*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data.startswith("sell_"):
        key = data.split("_")[1]
        context.user_data["selected_coin"] = key
        context.user_data["step"] = "AWAITING_AMOUNT"
        await query.edit_message_text("ধাপ ১: কত পরিমাণ কয়েন বিক্রি করতে চান লিখুন (যেমন: 50000):")

    # --- লিডারবোর্ড (Public Leaderboard) ---
    elif data == "menu_leaderboard":
        lb = get_leaderboard()
        text = "🏆 **Public Leaderboard (Top Sellers)**\n\n"
        if not lb:
            text += "এখনো কোনো সফল লেনদেন হয়নি।"
        else:
            for idx, row in enumerate(lb, start=1):
                text += f"{idx}. **{row[0]}** — {row[1]:,} Coins ({row[2]} 次 Sales)\n"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]), parse_mode="Markdown")

    # --- পার্সোনাল হিস্ট্রি (My History) ---
    elif data == "menu_history":
        history = get_user_history(user_id)
        text = "📜 **আপনার পার্সোনাল সেল হিস্ট্রি:**\n\n"
        if not history:
            text += "আপনার কোনো হিস্ট্রি পাওয়া যায়নি।"
        else:
            for row in history:
                st_icon = "⏳" if row[4] == "Pending" else ("✅" if row[4] == "Accepted" else "❌")
                text += f"🆔 `#{row[0]}` | **{row[1]}**\n📦 পরিমাণ: {row[2]:,} | 💰 {row[3]} ৳\nস্ট্যাটাস: {st_icon} **{row[4]}**\n----------------------\n"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]), parse_mode="Markdown")

    # --- এডমিন প্যানেল একসেপ্ট / রিজেক্ট বাটন ---
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
                text=f"❌ **আপনার সেল রিকোয়েস্ট (ID: #{tx_id}) রিজেক্ট করা হয়েছে।**\nকয়েন ভেরিফিকেশন অথবা কুপন তথ্য সঠিক ছিল না।",
                parse_mode="Markdown"
            )
            await query.edit_message_text(query.message.text + "\n\n❌ **REJECTED and User Notified.**")
        
        elif action == "accept":
            context.user_data["pending_tx_id"] = tx_id
            context.user_data["admin_step"] = "AWAITING_PROOF"
            await query.edit_message_text(query.message.text + "\n\n📸 **কাস্টমারকে পেমেন্ট করে স্ক্রিনশটটি এই চ্যাটে সেন্ড করুন (Caption এ কিছু লেখার প্রয়োজন নেই):**")

    # --- এডমিন প্রাইস চেঞ্জ সিলেক্ট ---
    elif data.startswith("adm_p_"):
        if user_id != ADMIN_TELEGRAM_ID: return
        key = data.split("_")[2]
        context.user_data["admin_coin_key"] = key
        context.user_data["admin_step"] = "AWAITING_NEW_PRICE"
        await query.edit_message_text(f"✏️ নতুন দাম লিখুন (প্রতি ১০০০ কয়েন):")

# --- ৫. ইনপুট হ্যান্ডলার (টেক্সট ও ছবি) ---
async def handle_inputs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admin_step = context.user_data.get("admin_step")
    step = context.user_data.get("step")

    # --- এডমিন দ্বারা স্ক্রিনশট আপলোড প্রসেস ---
    if user_id == ADMIN_TELEGRAM_ID and admin_step == "AWAITING_PROOF" and update.message.photo:
        tx_id = context.user_data.get("pending_tx_id")
        photo_file_id = update.message.photo[-1].file_id
        
        update_tx_status(tx_id, "Accepted")
        tx = get_tx(tx_id)

        msg = (
            f"✅ **আপনার পেমেন্ট সফলভাবে করা হয়েছে!**\n\n"
            f"🆔 **Transaction ID:** `#{tx_id}`\n"
            f"🪙 **কয়েন:** {tx[1]}\n"
            f"📦 **পরিমাণ:** {tx[2]:,}\n"
            f"💰 **পেমেন্ট পরিমাণ:** {tx[5]} ৳\n"
            f"📱 **মেথড/নম্বর:** {tx[3]} ({tx[4]})\n\n"
            f"প্রমাণস্বরূপ পেমেন্ট স্ক্রিনশটটি উপরে দেওয়া হলো।"
        )
        # ট্রাফিকের কাছে পেমেন্ট স্ক্রিনশট সহ বার্তা পাঠানো
        await context.bot.send_photo(chat_id=tx[0], photo=photo_file_id, caption=msg, parse_mode="Markdown")
        await update.message.reply_text("✅ **পেমেন্ট স্ক্রিনশট ট্রাফিকের কাছে সফলভাবে পৌঁছে দেওয়া হয়েছে!**")
        context.user_data["admin_step"] = None
        return

    # --- এডমিন প্রাইস আপডেট ---
    if user_id == ADMIN_TELEGRAM_ID and admin_step == "AWAITING_NEW_PRICE" and update.message.text:
        try:
            new_p = float(update.message.text.strip())
            key = context.user_data.get("admin_coin_key")
            update_coin_price(key, new_p)
            context.user_data["admin_step"] = None
            await update.message.reply_text(f"✅ **দাম রিয়েলটাইমে আপডেট করে ডাটাবেজে সেভ করা হয়েছে!**")
        except ValueError:
            await update.message.reply_text("⚠️ সঠিক সংখ্যা লিখুন:")
        return

    # --- ইউজার ইনপুট প্রসেস (অ্যামাউন্ট, মেথড, নম্বর) ---
    if step == "AWAITING_AMOUNT" and update.message.text:
        try:
            amt = int(update.message.text.strip())
            if amt < 50000:
                await update.message.reply_text("⚠️ সর্বনিম্ন ৫০,০০০ কয়েন দিতে হবে।")
                return
            context.user_data["amount"] = amt
            context.user_data["step"] = "AWAITING_METHOD"
            await update.message.reply_text("ধাপ ২: পেমেন্ট মেথড লিখুন (যেমন: বিকাশ / নগদ / রকেট):")
        except ValueError:
            await update.message.reply_text("⚠️ সংখ্যা লিখুন:")

    elif step == "AWAITING_METHOD" and update.message.text:
        context.user_data["method"] = update.message.text.strip()
        context.user_data["step"] = "AWAITING_NUMBER"
        await update.message.reply_text("ধাপ ৩: পেমেন্ট নেওয়ার অ্যাকাউন্ট নম্বরটি লিখুন:")

    elif step == "AWAITING_NUMBER" and update.message.text:
        num = update.message.text.strip()
        coins = get_coins()
        key = context.user_data["selected_coin"]
        c = coins[key]
        amt = context.user_data["amount"]
        method = context.user_data["method"]

        net_taka = max(0, (amt / 1000) * c["price"] - 5)
        context.user_data["step"] = None

        tx_id = add_transaction(user_id, update.effective_user.first_name, c["label"], amt, method, num, net_taka)

        await update.message.reply_text(
            f"⏳ **আপনার সেল রিকোয়েস্ট জমা হয়েছে!**\n\nID: `#{tx_id}`\nএডমিন এটি যাচাই করে পেমেন্ট করবে।",
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )

        # এডমিন বক্সে বার্তা পাঠানো
        admin_msg = (
            f"🚨 **নতুন কয়েন সেল রিকোয়েস্ট!**\n\n"
            f"🆔 **TX ID:** `#{tx_id}`\n"
            f"👤 **ইউজার:** {update.effective_user.first_name} (`{user_id}`)\n"
            f"🪙 **কয়েন:** {c['label']}\n"
            f"📦 **পরিমাণ:** {amt:,}\n"
            f"📱 **পেমেন্ট:** {method} (`{num}`)\n"
            f"💰 **দেয় টাকা:** `{net_taka} ৳`\n\n"
            f"যাচাই করে বাটন সিলেক্ট করুন:"
        )
        btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Accept & Pay", callback_data=f"admin_accept_{tx_id}"), InlineKeyboardButton("❌ Reject", callback_data=f"admin_reject_{tx_id}")]
        ])
        await context.bot.send_message(chat_id=ADMIN_TELEGRAM_ID, text=admin_msg, reply_markup=btn, parse_mode="Markdown")

# --- ৬. এডমিন প্যানেল কমান্ড (`/admin`) ---
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_TELEGRAM_ID:
        return
    coins = get_coins()
    keyboard = []
    for k, c in coins.items():
        keyboard.append([InlineKeyboardButton(f"✏️ {c['label']} ({c['price']}৳)", callback_data=f"adm_p_{k}")])
    
    await update.message.reply_text("⚙️ **Admin Panel - Dynamic Control**\n\nদাম পরিবর্তন করতে কয়েন সিলেক্ট করুন:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# --- ৭. বট স্টার্ট ---
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(handle_callbacks))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_inputs))

    print("Bot is active with SQLite Persistence!")
    app.run_polling()

if __name__ == "__main__":
    main()
            
