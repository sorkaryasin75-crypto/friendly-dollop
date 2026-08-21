import os
import sqlite3
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes, ConversationState
)

# ==========================================
# CONFIGURATION & CONSTANTS
# ==========================================
# Your Telegram User ID
ADMIN_TELEGRAM_ID =? 6819070790

# Replace with your actual Telegram Bot Token from @BotFather
BOT_TOKEN = "8773492019:AAEJD2EvVgUgtaNvJyD-9goqA8hknG-tY58"

# Setup Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

WAITING_FOR_PRICE = 1
DB_FILE = 'coin_system.db'

# ==========================================
# DATABASE INITIALIZATION
# ==========================================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Coin Prices Table (per 1,000 / 1K coins in BDT)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS coin_prices (
            coin_type TEXT PRIMARY KEY,
            price_per_k REAL
        )
    ''')
    
    # Default Rates Setup
    default_prices = [
        ('niva', 5.0),
        ('NewTop', 3.0),
        ('topfollows', 3.0),
        ('ns', 8.0)
    ]
    cursor.executemany('INSERT OR IGNORE INTO coin_prices VALUES (?, ?)', default_prices)
    
    # Sell Requests Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sell_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            username TEXT,
            coin_type TEXT NOT NULL,
            amount INTEGER NOT NULL,
            total_taka REAL NOT NULL,
            payment_method TEXT NOT NULL,
            account_number TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            proof_photo_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def db_get_prices():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT coin_type, price_per_k FROM coin_prices')
    rows = cursor.fetchall()
    conn.close()
    return dict(rows)

def db_update_price(coin_type, price):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('UPDATE coin_prices SET price_per_k = ? WHERE coin_type = ?', (price, coin_type))
    conn.commit()
    conn.close()

def db_update_status(req_id, status, proof_id=None):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    if proof_id:
        cursor.execute('UPDATE sell_requests SET status = ?, proof_photo_id = ? WHERE id = ?', (status, proof_id, req_id))
    else:
        cursor.execute('UPDATE sell_requests SET status = ? WHERE id = ?', (status, req_id))
    
    cursor.execute('SELECT user_id, coin_type, amount, total_taka, payment_method, account_number FROM sell_requests WHERE id = ?', (req_id,))
    row = cursor.fetchone()
    conn.commit()
    conn.close()
    return row

def db_get_leaderboard():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT username, user_id, COUNT(*) as total_sells, SUM(total_taka) as total_earned
        FROM sell_requests
        WHERE status = 'Accepted'
        GROUP BY user_id
        ORDER BY total_earned DESC
        LIMIT 10
    ''')
    rows = cursor.fetchall()
    conn.close()
    return rows

def db_get_user_history(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, coin_type, amount, total_taka, payment_method, account_number, status, created_at
        FROM sell_requests
        WHERE user_id = ?
        ORDER BY id DESC LIMIT 10
    ''', (str(user_id),))
    rows = cursor.fetchall()
    conn.close()
    return rows

# ==========================================
# BOT COMMAND & BUTTON HANDLERS
# ==========================================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    keyboard = [
        [InlineKeyboardButton("🏆 Leaderboard", callback_data='menu_leaderboard'), 
         InlineKeyboardButton("📜 My History", callback_data='menu_history')]
    ]
    
    if user.id == ADMIN_TELEGRAM_ID:
        keyboard.append([InlineKeyboardButton("⚙️ Admin Control Panel", callback_data='admin_panel')])
        
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        f"👋 *Welcome, {user.first_name}!*\n\n"
        f"Welcome to the official *Coin Selling & Exchange Bot*.\n\n"
        f"✨ *Supported Coins:* Niva, NewTop, TopFollows, NS Coin\n"
        f"💳 *Supported Payments:* bKash, Nagad, Rocket\n\n"
        f"Select an option below:"
    )
    
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
    elif update.callback_query:
        await update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == 'main_menu':
        await start_command(update, context)

    elif data == 'menu_leaderboard':
        board = db_get_leaderboard()
        if not board:
            msg = "🏆 *Top Sellers Leaderboard*\n\nNo completed sales yet!"
        else:
            msg = "🏆 *Top Sellers Leaderboard (Earned BDT)*\n\n"
            for idx, item in enumerate(board, 1):
                name = f"@{item[0]}" if item[0] != 'NoUsername' else f"ID: {item[1]}"
                msg += f"*{idx}. {name}* — {item[2]} Orders | *{item[3]:.2f} TK*\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data='main_menu')]]
        await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == 'menu_history':
        history = db_get_user_history(user_id)
        if not history:
            msg = "📜 *My Transaction History*\n\nYou haven't submitted any coin requests yet."
        else:
            msg = "📜 *Your Last 10 Transactions*\n\n"
            for req in history:
                st = req[6]
                status_icon = "✅ Accepted" if st == 'Accepted' else ("❌ Rejected" if st == 'Rejected' else "⏳ Pending")
                msg += (
                    f"🆔 *Order ID:* `#{req[0]}`\n"
                    f"🪙 *Coin:* {req[1].upper()} | *Amount:* {req[2]:,}\n"
                    f"💰 *Total:* {req[3]:.2f} TK ({req[4].upper()}: `{req[5]}`)\n"
                    f"📌 *Status:* {status_icon}\n"
                    f"----------------------------------------\n"
                )
                
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data='main_menu')]]
        await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == 'admin_panel':
        if user_id != ADMIN_TELEGRAM_ID:
            await query.edit_message_text("❌ *Access Denied!*")
            return
            
        prices = db_get_prices()
        msg = "⚙️ *Admin Control Panel*\n\n📊 *Current Live Rates (Per 1,000 Coins):*\n"
        for coin, price in prices.items():
            msg += f"• *{coin.upper()}:* {price:.2f} BDT\n"
            
        keyboard = [
            [InlineKeyboardButton("✏️ Update Price Rates", callback_data='admin_choose_coin')],
            [InlineKeyboardButton("🔙 Main Menu", callback_data='main_menu')]
        ]
        await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == 'admin_choose_coin':
        if user_id != ADMIN_TELEGRAM_ID:
            return
        keyboard = [
            [InlineKeyboardButton("Niva Coin", callback_data='setrate_niva'), InlineKeyboardButton("NewTop Coin", callback_data='setrate_NewTop')],
            [InlineKeyboardButton("TopFollows", callback_data='setrate_topfollows'), InlineKeyboardButton("NS Coin", callback_data='setrate_ns')],
            [InlineKeyboardButton("🔙 Admin Panel", callback_data='admin_panel')]
        ]
        await query.edit_message_text("Select the coin whose price rate you wish to update:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("accept_") or data.startswith("reject_"):
        if user_id != ADMIN_TELEGRAM_ID:
            return
            
        action, req_id = data.split("_")
        
        if action == "reject":
            req_data = db_update_status(req_id, "Rejected")
            if req_data:
                target_user_id, coin, amount, total_taka, method, number = req_data
                try:
                    user_msg = f"❌ *Sell Request Rejected*\n\nYour request `#{req_id}` for *{amount:,} {coin.upper()}* has been rejected."
                    await context.bot.send_message(chat_id=target_user_id, text=user_msg, parse_mode='Markdown')
                except Exception as e:
                    logger.error(f"Error notifying user: {e}")
            await query.edit_message_text(text=query.message.text + "\n\n🔴 *STATUS: REJECTED*", parse_mode='Markdown')
        
        elif action == "accept":
            await query.edit_message_text(
                text=query.message.text + f"\n\n⏳ *STATUS: AWAITING PAYMENT PROOF SCREENSHOT...*\n"
                f"👉 To complete this order, reply/send a payment screenshot in this chat with caption: `#{req_id}`",
                parse_mode='Markdown'
            )

# ==========================================
# ADMIN PROOF SCREENSHOT HANDLER
# ==========================================
async def admin_handle_proof_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_TELEGRAM_ID:
        return

    if update.message.photo and update.message.caption:
        caption = update.message.caption.strip()
        if "#" in caption:
            try:
                req_id = int(caption.split("#")[1].split()[0])
                photo_file_id = update.message.photo[-1].file_id
                
                req_data = db_update_status(req_id, "Accepted", photo_file_id)
                
                if req_data:
                    target_user_id, coin, amount, total_taka, method, number = req_data
                    
                    user_receipt = (
                        f"🎉 *PAYMENT COMPLETED & VERIFIED!*\n\n"
                        f"🆔 *Order ID:* `#{req_id}`\n"
                        f"🪙 *Coin Type:* {coin.upper()}\n"
                        f"🔢 *Coin Amount:* {amount:,}\n"
                        f"💰 *Total Paid:* *{total_taka:.2f} BDT*\n"
                        f"💳 *Payment Method:* {method.upper()}\n"
                        f"📱 *Account Number:* `{number}`\n\n"
                        f"📸 *Payment Proof Screenshot Attached Below:* 👇"
                    )
                    
                    await context.bot.send_photo(
                        chat_id=target_user_id,
                        photo=photo_file_id,
                        caption=user_receipt,
                        parse_mode='Markdown'
                    )
                    
                    await update.message.reply_text(f"✅ Payment proof for Order `#{req_id}` sent successfully to User (`{target_user_id}`)!")
            except Exception as e:
                await update.message.reply_text(f"❌ Error processing screenshot: {e}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO & filters.CaptionHas('*'), admin_handle_proof_photo))
    
    print("🤖 Telegram Bot Server is up and running...")
    app.run_polling()

if __name__ == "__main__":
    main()
