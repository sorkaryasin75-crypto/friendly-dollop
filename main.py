import os
import logging
import firebase_admin
from firebase_admin import credentials, db
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# --- ১. কনফিগারেশন ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8773492019:AAEJD2EvVgUgtaNvJyD-9goqA8hknG-tY58")
ADMIN_TELEGRAM_ID = 6582650458  # আপনার টেলিগ্রাম UID[span_0](start_span)[span_0](end_span)
FIREBASE_KEY_PATH = "config/firebase_key.json"
FIREBASE_DB_URL = os.environ.get("FIREBASE_DB_URL", "https://sell-point-it-default-rtdb.firebaseio.com")
BLOGSPOT_WEBAPP_URL = "https://moneyloop24.blogspot.com"  # আপনার ব্লগার ওয়েব অ্যাপ URL

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# --- ২. Firebase ইনিশিয়ালাইজেশন ---
if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_KEY_PATH)
    firebase_admin.initialize_app(cred, {
        'databaseURL': FIREBASE_DB_URL
    })

# --- ৩. ডাটাবেজ হেল্পার ফাংশনসমূহ (Blogspot DB Sync) ---

def get_coins():
    ref = db.reference('coins')
    return ref.get() or {
        "niva": {"label": "Niva Coin", "price": 5.0, "active": True},
        "NewTop": {"label": "NewTop Coin", "price": 3.0, "active": True},
        "topfollows": {"label": "Topfollows Coin", "price": 3.0, "active": True},
        "ns": {"label": "NS Coin", "price": 8.0, "active": True}
    }

def update_coin_price(key, new_price):
    ref = db.reference(f'coins/{key}')
    ref.update({"price": new_price})

def add_transaction(user_id, user_name, coin_label, coin_amount, method, number, net_taka):
    ref = db.reference('requests')  # ব্লগস্পট অ্যাপের রিকোয়েস্ট টেবিল
    new_req = ref.push()
    tx_id = new_req.key
    data = {
        "id": tx_id,
        "userId": user_id,
        "telegramName": user_name,
        "coinLabel": coin_label,
        "coinAmount": coin_amount,
        "paymentMethod": method,
        "nagadNumber": number,
        "netTaka": net_taka,
        "status": "Pending",
        "source": "Telegram Inline Keyboard"
    }
    new_req.set(data)
    return tx_id

def update_tx_status(tx_id, status):
    ref = db.reference(f'requests/{tx_id}')
    ref.update({"status": status})

def get_tx(tx_id):
    ref = db.reference(f'requests/{tx_id}')
    return ref.get()

def get_user_history(user_id):
    ref = db.reference('requests')
    all_tx = ref.order_by_child('userId').equal_to(user_id).get()
    if not all_tx:
        return []
    return list(all_tx.values())[::-1][:10]

def get_leaderboard():
    ref = db.reference('requests')
    all_tx = ref.get()
    if not all_tx:
        return []
    
    leaderboard_data = {}
    for tx in all_tx.values():
        if isinstance(tx, dict) and tx.get("status") == "Accepted":
            u_name = tx.get("telegramName", "Unknown")
            amt = tx.get("coinAmount", 0)
            if u_name not in leaderboard_data:
                leaderboard_data[u_name] = {"total_coins": 0, "sales_count": 0}
            leaderboard_data[u_name]["total_coins"] += amt
            leaderboard_data[u_name]["sales_count"] += 1

    sorted_lb = sorted(leaderboard_data.items(), key=lambda x: x[1]["total_coins"], reverse=True)
    return sorted_lb[:10]

# --- ৪. ইনলাইন কিবোর্ড ইউআই (UI) ---

def get_main_inline_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🛒 Sell Coins", callback_data="menu_sell"),
            InlineKeyboardButton("📊 Live Rates", callback_data="menu_rates")
        ],
        [
            InlineKeyboardButton("🏆 Leaderboard", callback_data="menu_leaderboard"),
            InlineKeyboardButton("📜 My History", callback_data="menu_history")
        ],
        [
            InlineKeyboardButton("🌐 Open Blogspot Web App", web_app=WebAppInfo(url=BLOGSPOT_WEBAPP_URL))
        ],
        [
            InlineKeyboardButton("📢 Channel", url="https://t.me/EducationPointBD"),
            InlineKeyboardButton("👨‍💻 Support", url="https://t.me/educationpointbd24")
        ]
    ])

# --- ৫. বট হ্যান্ডলারসমূহ ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "👋 **Earning Elevated**-এ আপনাকে স্বাগতম!\n\nআপনি চাইলে নিচের **Inline Buttons** চাপ দিয়ে সরাসরি বটের ভেতর লেনদেন করতে পারেন অথবা আমাদের Web App ব্যবহার করতে পারেন:"
    if update.message:
        await update.message.reply_text(text, reply_markup=get_main_inline_keyboard(), parse_mode="Markdown")
    else:
        await update.callback_query.edit_message_text(text, reply_markup=get_main_inline_keyboard(), parse_mode="Markdown")

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
        text = "📊 **Live Market Rates (Blogspot DB Live Sync):**\n\n"
        for k, c in coins.items():
            st = "✅ Active" if c.get("active") else "❌ Inactive"
            text += f"• **{c.get('label')}**: {c.get('price')} ৳ ({st})\n"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]]), parse_mode="Markdown")

    # --- ইনলাইন সেল বাটন ---
    elif data == "menu_sell":
        coins = get_coins()
        keyboard = []
        for k, c in coins.items():
            if c.get("active"):
                keyboard.append([InlineKeyboardButton(f"Sell {c.get('label')} ({c.get('price')}৳/1K)", callback_data=f"sell_{k}")])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="main_menu")])
        await query.edit_message_text("🛒 **কোন কয়েনটি ইনলাইন বাটনের মাধ্যমে বিক্রি করতে চান বেছে নিন:**\n*(সর্বনিম্ন: ৫০,০০০)*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data.startswith("sell_"):
        key = data.split("_")[1]
        context.user_data["selected_coin"] = key
        context.user_data["step"] = "AWAITING_AMOUNT"
        await query.edit_message_text("ধাপ ১: কত পরিমাণ কয়েন বিক্রি করতে চান লিখুন (যেমন: 50000):")

    # --- লিডারবোর্ড ---
    elif data == "menu_leaderboard":
        lb = get_leaderboard()
        text = "🏆 **Public Leaderboard (Blogspot Sync):**\n\n"
        if not lb:
            text += "এখনো কোনো সফল লেনদেন হয়নি।"
        else:
            for idx, (name, stats) in enumerate(lb, start=1):
                text += f"{idx}. **{name}** — {stats['total_coins']:,} Coins ({stats['sales_count']} Sales)\n"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]), parse_mode="Markdown")

    # --- মাই হিস্ট্রি ---
    elif data == "menu_history":
        history = get_user_history(user_id)
        text = "📜 **আপনার পার্সোনাল সেল হিস্ট্রি:**\n\n"
        if not history:
            text += "আপনার কোনো হিস্ট্রি পাওয়া যায়নি।"
        else:
            for tx in history:
                st = tx.get("status")
                st_icon = "⏳" if st == "Pending" else ("✅" if st == "Accepted" else "❌")
                text += f"🆔 `{tx.get('id')}` | **{tx.get('coinLabel')}**\n📦 পরিমাণ: {tx.get('coinAmount'):,} | 💰 {tx.get('netTaka')} ৳\nস্ট্যাটাস: {st_icon} **{st}**\n----------------------\n"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]), parse_mode="Markdown")

    # --- এডমিন অ্যাকশন ---
    elif data.startswith("admin_accept_") or data.startswith("admin_reject_"):
        if user_id != ADMIN_TELEGRAM_ID:
            return
        parts = data.split("_")
        action = parts[1]
        tx_id = parts[2]

        if action == "reject":
            update_tx_status(tx_id, "Rejected")
            tx = get_tx(tx_id)
            await context.bot.send_message(
                chat_id=tx.get("userId"),
                text=f"❌ **আপনার সেল রিকোয়েস্ট (ID: `{tx_id}`) রিজেক্ট করা হয়েছে।**\nকয়েন ভেরিফিকেশন সঠিক ছিল না।",
                parse_mode="Markdown"
            )
            await query.edit_message_text(query.message.text + "\n\n❌ **REJECTED and User Notified.**")
        
        elif action == "accept":
            context.user_data["pending_tx_id"] = tx_id
            context.user_data["admin_step"] = "AWAITING_PROOF"
            await query.edit_message_text(query.message.text + "\n\n📸 **কাস্টমারকে পেমেন্ট করে স্ক্রিনশটটি বোটে সেন্ড করুন:**")

    elif data.startswith("adm_p_"):
        if user_id != ADMIN_TELEGRAM_ID: return
        key = data.split("_")[2]
        context.user_data["admin_coin_key"] = key
        context.user_data["admin_step"] = "AWAITING_NEW_PRICE"
        await query.edit_message_text("✏️ নতুন দাম লিখুন (প্রতি ১০০০ কয়েন):")

# --- ৬. ইনপুট প্রসেসিং ---

async def handle_inputs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admin_step = context.user_data.get("admin_step")
    step = context.user_data.get("step")

    # পেমেন্ট স্ক্রিনশট প্রসেস
    if user_id == ADMIN_TELEGRAM_ID and admin_step == "AWAITING_PROOF" and update.message.photo:
        tx_id = context.user_data.get("pending_tx_id")
        photo_file_id = update.message.photo[-1].file_id
        
        update_tx_status(tx_id, "Accepted")
        tx = get_tx(tx_id)

        msg = (
            f"✅ **আপনার পেমেন্ট সফলভাবে করা হয়েছে!**\n\n"
            f"🆔 **Transaction ID:** `{tx_id}`\n"
            f"🪙 **কয়েন:** {tx.get('coinLabel')}\n"
            f"📦 **পরিমাণ:** {tx.get('coinAmount'):,}\n"
            f"💰 **পেমেন্ট:** {tx.get('netTaka')} ৳\n"
            f"📱 **মেথড/নম্বর:** {tx.get('paymentMethod')} ({tx.get('nagadNumber')})\n\n"
            f"পেমেন্টের প্রমাণস্বরূপ স্ক্রিনশটটি উপরে দেওয়া হলো।"
        )
        await context.bot.send_photo(chat_id=tx.get("userId"), photo=photo_file_id, caption=msg, parse_mode="Markdown")
        await update.message.reply_text("✅ **পেমেন্ট স্ক্রিনশট ট্রাফিকের কাছে পাঠানো হয়েছে!**")
        context.user_data["admin_step"] = None
        return

    # দাম আপডেট
    if user_id == ADMIN_TELEGRAM_ID and admin_step == "AWAITING_NEW_PRICE" and update.message.text:
        try:
            new_p = float(update.message.text.strip())
            key = context.user_data.get("admin_coin_key")
            update_coin_price(key, new_p)
            context.user_data["admin_step"] = None
            await update.message.reply_text("✅ **ব্লগস্পট ডাটাবেজে কয়েনের দাম আপডেট করা হয়েছে!**")
        except ValueError:
            await update.message.reply_text("⚠️ সঠিক সংখ্যা লিখুন:")
        return

    # ইউজার সেল ইনপুট
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
        c = coins.get(key, {})
        amt = context.user_data["amount"]
        method = context.user_data["method"]

        net_taka = max(0, (amt / 1000) * c.get("price", 0) - 5)
        context.user_data["step"] = None

        tx_id = add_transaction(user_id, update.effective_user.first_name, c.get("label"), amt, method, num, net_taka)

        await update.message.reply_text(
            f"⏳ **আপনার সেল রিকোয়েস্ট জমা হয়েছে!**\n\nID: `{tx_id}`\nএডমিন এটি ভেরিফাই করে পেমেন্ট করবে।",
            reply_markup=get_main_inline_keyboard(),
            parse_mode="Markdown"
        )

        admin_msg = (
            f"🚨 **নতুন কয়েন সেল রিকোয়েস্ট (Inline UI)!**\n\n"
            f"🆔 **TX ID:** `{tx_id}`\n"
            f"👤 **ইউজার:** {update.effective_user.first_name} (`{user_id}`)\n"
            f"🪙 **কয়েন:** {c.get('label')}\n"
            f"📦 **পরিমাণ:** {amt:,}\n"
            f"📱 **পেমেন্ট:** {method} (`{num}`)\n"
            f"💰 **দেয় টাকা:** `{net_taka} ৳`\n\n"
            f"যাচাই করে বাটন চাপুন:"
        )
        btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Accept & Pay", callback_data=f"admin_accept_{tx_id}"), InlineKeyboardButton("❌ Reject", callback_data=f"admin_reject_{tx_id}")]
        ])
        await context.bot.send_message(chat_id=ADMIN_TELEGRAM_ID, text=admin_msg, reply_markup=btn, parse_mode="Markdown")

# --- ৭. এডমিন প্যানেল ---
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_TELEGRAM_ID:
        return
    coins = get_coins()
    keyboard = []
    for k, c in coins.items():
        keyboard.append([InlineKeyboardButton(f"✏️ {c.get('label')} ({c.get('price')}৳)", callback_data=f"adm_p_{k}")])
    
    await update.message.reply_text("⚙️ **Admin Panel - Blogspot Web App Control**\n\nদাম পরিবর্তন করতে কয়েন সিলেক্ট করুন:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(handle_callbacks))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_inputs))

    print("Bot is synchronized with Blogspot Web App Engine!")
    app.run_polling()

if __name__ == "__main__":
    main()
    
