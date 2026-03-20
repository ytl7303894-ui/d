import logging
import os
import random
import string
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from bson.objectid import ObjectId

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)
from pymongo import MongoClient
from dotenv import load_dotenv

# ==================== CONFIGURATION ====================
load_dotenv()

# Aapke diye gaye credentials
TOKEN = "8640038443:AAHGFxVYPr8FPrqk5U8j3M49meaWcYMxL9Y"
MONGO_URI = "mongodb+srv://userbot:userbot@cluster0.iweqz.mongodb.net/?retryWrites=true&w=majority"
ADMIN_IDS = [5301769589, 8477195695]  # Dono admin IDs

# Conversation states
ADD_HACK, EDIT_HACK, BROADCAST, ADD_BALANCE = range(4)

# ==================== DATABASE SETUP ====================
try:
    client = MongoClient(MONGO_URI)
    db = client["hack_selling_bot"]
    client.admin.command('ping')
    print("✅ MongoDB Connected Successfully!")
    
    # Collections
    users_col = db["users"]
    keys_col = db["keys"]
    orders_col = db["orders"]
    settings_col = db["settings"]
    hacks_col = db["hacks"]
    payments_col = db["payments"]
    
    # Create default settings if not exists
    if not settings_col.find_one({"_id": "settings"}):
        settings_col.insert_one({
            "_id": "settings",
            "upi_id": "userbot@okhdfcbank",  # Payment UPI ID
            "qr_code": "https://example.com/qr.png",  # QR code link
            "admin_contact": "@admin",
            "admin_email": "admin@example.com",
            "welcome_msg": "Welcome to Hack Selling Bot!",
            "currency": "₹",
            "min_amount": 100,
            "payment_wait_time": 30,  # Minutes to wait for payment
            "auto_verify": False  # Manual verification by default
        })
    
    # Create default hacks if not exists
    if hacks_col.count_documents({}) == 0:
        default_hacks = [
            {"category": "PUBG", "name": "Aimbot + Wallhack", "price": 500, "available": True, "description": "Professional aimbot with wallhack features"},
            {"category": "PUBG", "name": "ESP Hack", "price": 300, "available": True, "description": "See enemies through walls"},
            {"category": "Free Fire", "name": "Headshot Hack", "price": 400, "available": True, "description": "100% headshot accuracy"},
            {"category": "Free Fire", "name": "Aimlock", "price": 350, "available": True, "description": "Auto aimlock feature"},
            {"category": "COC", "name": "Unlimited Gems", "price": 600, "available": True, "description": "Get unlimited gems instantly"}
        ]
        hacks_col.insert_many(default_hacks)
        
except Exception as e:
    print(f"❌ MongoDB Error: {e}")
    print("⚠️ Using in-memory storage (temporary)")
    db = None

# ==================== LOGGING ====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== HELPER FUNCTIONS ====================
def get_settings():
    """Get bot settings"""
    if db:
        settings = settings_col.find_one({"_id": "settings"})
        if settings:
            return settings
    return {
        "upi_id": "userbot@okhdfcbank",
        "qr_code": "https://example.com/qr.png",
        "admin_contact": "@admin",
        "currency": "₹",
        "min_amount": 100,
        "payment_wait_time": 30
    }

def generate_key():
    """Generate unique key"""
    key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
    return '-'.join([key[i:i+4] for i in range(0, 16, 4)])

def save_user(user_id, username=None, first_name=None):
    """Save or update user"""
    if not db:
        return
    users_col.update_one(
        {"user_id": user_id},
        {"$set": {
            "username": username,
            "first_name": first_name,
            "last_active": datetime.now()
        }, "$setOnInsert": {
            "created_at": datetime.now(),
            "balance": 0,
            "total_spent": 0,
            "keys": [],
            "pending_payments": []
        }},
        upsert=True
    )

def generate_order_id():
    """Generate unique order ID"""
    return f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(100,999)}"

# ==================== USER HANDLERS ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command"""
    user = update.effective_user
    save_user(user.id, user.username, user.first_name)
    
    # Main menu
    keyboard = [
        [InlineKeyboardButton("🛒 Buy Hacks", callback_data="buy_hacks")],
        [InlineKeyboardButton("🔑 My Keys", callback_data="my_keys")],
        [InlineKeyboardButton("💰 Add Balance", callback_data="add_balance")],
        [InlineKeyboardButton("📞 Support", callback_data="support")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="user_settings")]
    ]
    
    # Admin button
    if user.id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin_panel")])
    
    await update.message.reply_text(
        f"👋 Welcome {user.first_name}!\n\n"
        f"Select an option:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all button clicks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    # ===== USER SECTION =====
    if data == "buy_hacks":
        # Show categories
        hacks = list(hacks_col.find({"available": True})) if db else []
        categories = set(h["category"] for h in hacks)
        
        keyboard = []
        for cat in categories:
            count = len([h for h in hacks if h["category"] == cat])
            keyboard.append([InlineKeyboardButton(f"📁 {cat} ({count})", callback_data=f"cat_{cat}")])
        keyboard.append([InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")])
        
        await query.edit_message_text(
            "📂 **Select Category:**\n\nChoose a game category:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif data.startswith("cat_"):
        category = data[4:]
        hacks = list(hacks_col.find({"category": category, "available": True})) if db else []
        
        keyboard = []
        for hack in hacks:
            keyboard.append([InlineKeyboardButton(
                f"🎯 {hack['name']} - {get_settings()['currency']}{hack['price']}",
                callback_data=f"hack_{hack['_id']}"
            )])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="buy_hacks")])
        
        await query.edit_message_text(
            f"📦 **{category} Hacks:**\n\nSelect a hack:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif data.startswith("hack_"):
        hack_id = data[5:]
        hack = hacks_col.find_one({"_id": ObjectId(hack_id)}) if db else None
        
        if hack:
            msg = f"**{hack['name']}**\n\n"
            msg += f"💰 Price: {get_settings()['currency']}{hack['price']}\n"
            msg += f"📁 Category: {hack['category']}\n"
            msg += f"📝 Description: {hack.get('description', 'No description')}\n\n"
            msg += "✅ Lifetime validity\n"
            msg += "✅ Instant delivery\n"
            msg += "✅ 24/7 support\n"
            msg += "✅ Anti-ban protection"
            
            keyboard = [
                [InlineKeyboardButton("💳 Buy Now", callback_data=f"buy_{hack_id}")],
                [InlineKeyboardButton("🔙 Back", callback_data=f"cat_{hack['category']}")]
            ]
            
            await query.edit_message_text(
                msg,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
    
    elif data.startswith("buy_"):
        hack_id = data[4:]
        hack = hacks_col.find_one({"_id": ObjectId(hack_id)}) if db else None
        
        if hack:
            order_id = generate_order_id()
            settings = get_settings()
            
            # Check user balance first (optional)
            user = users_col.find_one({"user_id": user_id}) if db else None
            balance = user.get('balance', 0) if user else 0
            
            if balance >= hack['price']:
                # Use balance
                if db:
                    # Deduct from balance
                    users_col.update_one(
                        {"user_id": user_id},
                        {"$inc": {"balance": -hack['price'], "total_spent": hack['price']}}
                    )
                    
                    # Generate key directly
                    key = generate_key()
                    
                    # Save key
                    keys_col.insert_one({
                        "key": key,
                        "user_id": user_id,
                        "hack_name": hack['name'],
                        "hack_id": hack_id,
                        "order_id": order_id,
                        "price": hack['price'],
                        "purchased_at": datetime.now(),
                        "status": "active"
                    })
                    
                    # Save order
                    orders_col.insert_one({
                        "order_id": order_id,
                        "user_id": user_id,
                        "hack_name": hack['name'],
                        "price": hack['price'],
                        "status": "completed",
                        "payment_method": "balance",
                        "created_at": datetime.now()
                    })
                    
                    # Update user keys list
                    users_col.update_one(
                        {"user_id": user_id},
                        {"$push": {"keys": key}}
                    )
                    
                    # Success message
                    await query.edit_message_text(
                        f"✅ **Purchase Successful!**\n\n"
                        f"Your Key for {hack['name']}:\n\n"
                        f"🔑 `{key}`\n\n"
                        f"Save this key to use the hack.",
                        parse_mode='Markdown',
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")
                        ]])
                    )
                    
                    # Notify admins
                    for admin_id in ADMIN_IDS:
                        try:
                            await context.bot.send_message(
                                admin_id,
                                f"🔔 **New Purchase (Balance)**\n\n"
                                f"User: {query.from_user.first_name}\n"
                                f"ID: {user_id}\n"
                                f"Hack: {hack['name']}\n"
                                f"Amount: ₹{hack['price']}\n"
                                f"Key: `{key}`",
                                parse_mode='Markdown'
                            )
                        except:
                            pass
                    
                    return
            else:
                # Save order
                if db:
                    orders_col.insert_one({
                        "order_id": order_id,
                        "user_id": user_id,
                        "hack_name": hack['name'],
                        "hack_id": hack_id,
                        "price": hack['price'],
                        "status": "pending",
                        "created_at": datetime.now()
                    })
                
                # Show payment options
                msg = f"💳 **Payment Required**\n\n"
                msg += f"Item: {hack['name']}\n"
                msg += f"Amount: {settings['currency']}{hack['price']}\n\n"
                msg += f"Your Balance: {settings['currency']}{balance}\n"
                msg += f"Need: {settings['currency']}{hack['price'] - balance if balance > 0 else hack['price']}\n\n"
                msg += f"**UPI ID:** `{settings['upi_id']}`\n"
                msg += f"**Order ID:** `{order_id}`\n\n"
                msg += "**Payment Steps:**\n"
                msg += "1️⃣ Send amount to above UPI ID\n"
                msg += "2️⃣ Take screenshot of payment\n"
                msg += "3️⃣ Send screenshot here\n"
                msg += "4️⃣ Click 'I've Paid' button\n\n"
                msg += "⏳ Admin will verify and send key within 30 minutes"
                
                keyboard = [
                    [InlineKeyboardButton("✅ I've Paid", callback_data=f"paid_{order_id}")],
                    [InlineKeyboardButton("📸 Send Screenshot", callback_data=f"screenshot_{order_id}")],
                    [InlineKeyboardButton("❌ Cancel", callback_data="buy_hacks")]
                ]
                
                await query.edit_message_text(
                    msg,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
    
    elif data.startswith("paid_"):
        order_id = data[5:]
        order = orders_col.find_one({"order_id": order_id}) if db else None
        
        if order and order['status'] == 'pending':
            # Update payment status
            payments_col.update_one(
                {"order_id": order_id},
                {"$set": {
                    "status": "awaiting_verification",
                    "paid_at": datetime.now()
                }},
                upsert=True
            )
            
            # Notify admins
            for admin_id in ADMIN_IDS:
                try:
                    await context.bot.send_message(
                        admin_id,
                        f"💰 **Payment Awaiting Verification**\n\n"
                        f"User: {query.from_user.first_name}\n"
                        f"ID: {user_id}\n"
                        f"Order: {order_id}\n"
                        f"Hack: {order['hack_name']}\n"
                        f"Amount: ₹{order['price']}\n\n"
                        f"Please check and verify payment.",
                        parse_mode='Markdown',
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("✅ Verify", callback_data=f"admin_verify_{order_id}"),
                            InlineKeyboardButton("❌ Reject", callback_data=f"admin_reject_{order_id}")
                        ]])
                    )
                except:
                    pass
            
            await query.edit_message_text(
                f"✅ **Payment Recorded!**\n\n"
                f"Admin will verify your payment and send the key soon.\n"
                f"Order ID: `{order_id}`",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")
                ]])
            )
    
    elif data.startswith("screenshot_"):
        order_id = data[11:]
        context.user_data['pending_order'] = order_id
        context.user_data['awaiting_screenshot'] = True
        
        await query.edit_message_text(
            f"📸 **Send Screenshot**\n\n"
            f"Please send the payment screenshot for order:\n"
            f"`{order_id}`\n\n"
            f"Admin will verify and send your key.",
            parse_mode='Markdown'
        )
    
    elif data == "my_keys":
        if not db:
            await query.edit_message_text("No keys found!")
            return
        
        keys = list(keys_col.find({"user_id": user_id, "status": "active"}))
        
        if not keys:
            await query.edit_message_text(
                "🔑 **No Keys Found**\n\nYou haven't purchased any hacks yet.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🛒 Buy Hacks", callback_data="buy_hacks")
                ]]),
                parse_mode='Markdown'
            )
            return
        
        msg = "🔑 **Your Active Keys:**\n\n"
        keyboard = []
        
        for key in keys:
            msg += f"**{key['hack_name']}**\n"
            msg += f"Key: `{key['key']}`\n"
            msg += f"Date: {key['purchased_at'].strftime('%d-%m-%Y')}\n\n"
            
            keyboard.append([InlineKeyboardButton(
                f"🔄 Reset {key['hack_name']}", 
                callback_data=f"resetkey_{key['_id']}"
            )])
            keyboard.append([InlineKeyboardButton(
                f"❌ Delete {key['hack_name']}", 
                callback_data=f"delkey_{key['_id']}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")])
        
        await query.edit_message_text(
            msg,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif data.startswith("resetkey_"):
        key_id = data[9:]
        key = keys_col.find_one({"_id": ObjectId(key_id)}) if db else None
        
        if key:
            new_key = generate_key()
            
            keys_col.update_one(
                {"_id": ObjectId(key_id)},
                {"$set": {"key": new_key, "reset_at": datetime.now()}}
            )
            
            # Notify admins
            for admin_id in ADMIN_IDS:
                try:
                    await context.bot.send_message(
                        admin_id,
                        f"🔄 **Key Reset**\n\n"
                        f"User: {query.from_user.first_name}\n"
                        f"ID: {user_id}\n"
                        f"Hack: {key['hack_name']}\n"
                        f"New Key: `{new_key}`",
                        parse_mode='Markdown'
                    )
                except:
                    pass
            
            await query.edit_message_text(
                f"✅ **Key Reset Successfully!**\n\nNew Key: `{new_key}`",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 My Keys", callback_data="my_keys")
                ]])
            )
    
    elif data.startswith("delkey_"):
        key_id = data[7:]
        
        if db:
            key = keys_col.find_one({"_id": ObjectId(key_id)})
            if key:
                keys_col.update_one(
                    {"_id": ObjectId(key_id)},
                    {"$set": {"status": "deleted"}}
                )
                
                # Remove from user's keys list
                users_col.update_one(
                    {"user_id": user_id},
                    {"$pull": {"keys": key['key']}}
                )
                
                # Notify admins
                for admin_id in ADMIN_IDS:
                    try:
                        await context.bot.send_message(
                            admin_id,
                            f"❌ **Key Deleted**\n\n"
                            f"User: {query.from_user.first_name}\n"
                            f"ID: {user_id}\n"
                            f"Hack: {key['hack_name']}",
                            parse_mode='Markdown'
                        )
                    except:
                        pass
        
        await query.edit_message_text(
            "✅ **Key Deleted Successfully!**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 My Keys", callback_data="my_keys")
            ]])
        )
    
    elif data == "add_balance":
        settings = get_settings()
        
        await query.edit_message_text(
            f"💰 **Add Balance**\n\n"
            f"Minimum: {settings['currency']}{settings.get('min_amount', 100)}\n\n"
            f"**UPI ID:** `{settings['upi_id']}`\n\n"
            f"Steps:\n"
            f"1️⃣ Send amount to above UPI\n"
            f"2️⃣ Take screenshot\n"
            f"3️⃣ Send screenshot here\n"
            f"4️⃣ Click 'I've Sent' button\n\n"
            f"Admin will verify and add balance to your account.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ I've Sent", callback_data="balance_sent")],
                [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
            ])
        )
    
    elif data == "balance_sent":
        context.user_data['adding_balance'] = True
        
        await query.edit_message_text(
            "📸 **Send Screenshot**\n\n"
            "Please send the payment screenshot.\n"
            "Admin will verify and add balance to your account.",
            parse_mode='Markdown'
        )
        return ADD_BALANCE
    
    elif data == "support":
        settings = get_settings()
        await query.edit_message_text(
            f"📞 **Support**\n\n"
            f"📱 Telegram: {settings.get('admin_contact', '@admin')}\n"
            f"📧 Email: {settings.get('admin_email', 'admin@example.com')}\n\n"
            f"For quick help, contact admin with your order ID.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")
            ]])
        )
    
    elif data == "user_settings":
        user = users_col.find_one({"user_id": user_id}) if db else None
        
        if user:
            msg = f"⚙️ **Your Settings**\n\n"
            msg += f"💰 Balance: ₹{user.get('balance', 0)}\n"
            msg += f"💳 Total Spent: ₹{user.get('total_spent', 0)}\n"
            msg += f"🔑 Total Keys: {len(user.get('keys', []))}\n"
            msg += f"📅 Joined: {user.get('created_at', datetime.now()).strftime('%d-%m-%Y')}"
            
            await query.edit_message_text(
                msg,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")
                ]])
            )
    
    elif data == "main_menu":
        keyboard = [
            [InlineKeyboardButton("🛒 Buy Hacks", callback_data="buy_hacks")],
            [InlineKeyboardButton("🔑 My Keys", callback_data="my_keys")],
            [InlineKeyboardButton("💰 Add Balance", callback_data="add_balance")],
            [InlineKeyboardButton("📞 Support", callback_data="support")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="user_settings")]
        ]
        
        if user_id in ADMIN_IDS:
            keyboard.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin_panel")])
        
        await query.edit_message_text(
            "🏠 **Main Menu**\n\nSelect an option:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    # ===== ADMIN SECTION =====
    elif data == "admin_panel":
        if user_id not in ADMIN_IDS:
            await query.edit_message_text("❌ Unauthorized!")
            return
        
        keyboard = [
            [InlineKeyboardButton("📦 Manage Hacks", callback_data="admin_hacks")],
            [InlineKeyboardButton("💰 Payment Requests", callback_data="admin_payments")],
            [InlineKeyboardButton("📊 Statistics", callback_data="admin_stats")],
            [InlineKeyboardButton("📋 Orders", callback_data="admin_orders")],
            [InlineKeyboardButton("👥 Users", callback_data="admin_users")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="admin_settings")],
            [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
        ]
        
        await query.edit_message_text(
            "👑 **Admin Panel**\n\nSelect an option:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif data == "admin_payments":
        if user_id not in ADMIN_IDS or not db:
            return
        
        pending = list(payments_col.find({"status": "awaiting_verification"}).sort("paid_at", -1))
        
        if not pending:
            await query.edit_message_text(
                "📭 No pending payments.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back", callback_data="admin_panel")
                ]])
            )
            return
        
        msg = "💰 **Pending Payments**\n\n"
        keyboard = []
        
        for payment in pending[:5]:  # Show last 5
            order = orders_col.find_one({"order_id": payment['order_id']})
            if order:
                msg += f"Order: {payment['order_id']}\n"
                msg += f"User: {order['user_id']}\n"
                msg += f"Hack: {order['hack_name']}\n"
                msg += f"Amount: ₹{order['price']}\n"
                msg += f"Time: {payment['paid_at'].strftime('%H:%M %d-%m')}\n\n"
                
                keyboard.append([
                    InlineKeyboardButton(f"✅ Verify {payment['order_id']}", callback_data=f"admin_verify_{payment['order_id']}"),
                    InlineKeyboardButton(f"❌ Reject", callback_data=f"admin_reject_{payment['order_id']}")
                ])
        
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="admin_panel")])
        
        await query.edit_message_text(
            msg,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif data.startswith("admin_verify_"):
        if user_id not in ADMIN_IDS:
            return
        
        order_id = data[13:]
        order = orders_col.find_one({"order_id": order_id}) if db else None
        
        if order:
            # Generate key
            key = generate_key()
            
            # Save key
            keys_col.insert_one({
                "key": key,
                "user_id": order['user_id'],
                "hack_name": order['hack_name'],
                "hack_id": order.get('hack_id'),
                "order_id": order_id,
                "price": order['price'],
                "purchased_at": datetime.now(),
                "status": "active"
            })
            
            # Update order
            orders_col.update_one(
                {"order_id": order_id},
                {"$set": {"status": "completed", "key": key}}
            )
            
            # Update payment
            payments_col.update_one(
                {"order_id": order_id},
                {"$set": {"status": "verified", "verified_by": user_id, "verified_at": datetime.now()}}
            )
            
            # Update user
            users_col.update_one(
                {"user_id": order['user_id']},
                {
                    "$inc": {"total_spent": order['price']},
                    "$push": {"keys": key}
                }
            )
            
            # Send key to user
            try:
                await context.bot.send_message(
                    order['user_id'],
                    f"✅ **Payment Verified!**\n\n"
                    f"Your key for {order['hack_name']}:\n\n"
                    f"🔑 `{key}`\n\n"
                    f"Thank you for your purchase!",
                    parse_mode='Markdown'
                )
            except:
                pass
            
            await query.edit_message_text(
                f"✅ Payment verified and key sent!\nKey: `{key}`",
                parse_mode='Markdown'
            )
    
    elif data.startswith("admin_reject_"):
        if user_id not in ADMIN_IDS:
            return
        
        order_id = data[13:]
        
        # Update payment
        payments_col.update_one(
            {"order_id": order_id},
            {"$set": {"status": "rejected", "rejected_by": user_id, "rejected_at": datetime.now()}}
        )
        
        # Notify user
        order = orders_col.find_one({"order_id": order_id})
        if order:
            try:
                await context.bot.send_message(
                    order['user_id'],
                    f"❌ **Payment Rejected**\n\n"
                    f"Order: {order_id}\n\n"
                    f"Please contact admin for more information.",
                    parse_mode='Markdown'
                )
            except:
                pass
        
        await query.edit_message_text("❌ Payment rejected!")
    
    elif data == "admin_hacks":
        if user_id not in ADMIN_IDS:
            return
        
        hacks = list(hacks_col.find()) if db else []
        
        keyboard = [
            [InlineKeyboardButton("➕ Add New Hack", callback_data="admin_add_hack")]
        ]
        
        for hack in hacks:
            status = "✅" if hack.get('available', True) else "❌"
            keyboard.append([
                InlineKeyboardButton(
                    f"{status} {hack['name']} - ₹{hack['price']}",
                    callback_data=f"admin_edit_{hack['_id']}"
                ),
                InlineKeyboardButton("❌", callback_data=f"admin_del_{hack['_id']}")
            ])
        
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="admin_panel")])
        
        await query.edit_message_text(
            "📦 **Manage Hacks**\n\nClick on hack to edit:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif data == "admin_add_hack":
        if user_id not in ADMIN_IDS:
            return
        
        await query.edit_message_text(
            "➕ **Add New Hack**\n\n"
            "Send in format:\n"
            "`Category | Name | Price | Description`\n\n"
            "Example:\n"
            "`PUBG | Aimbot Pro | 500 | Best aimbot with wallhack`\n\n"
            "Type /cancel to abort."
        )
        return ADD_HACK
    
    elif data.startswith("admin_edit_"):
        if user_id not in ADMIN_IDS:
            return
        
        hack_id = data[11:]
        context.user_data['edit_hack_id'] = hack_id
        
        await query.edit_message_text(
            "✏️ **Edit Hack**\n\n"
            "Send new details in format:\n"
            "`Category | Name | Price | Description | Available`\n\n"
            "Example:\n"
            "`PUBG | Aimbot Pro | 600 | New description | True`\n\n"
            "Type /cancel to abort."
        )
        return EDIT_HACK
    
    elif data.startswith("admin_del_"):
        if user_id not in ADMIN_IDS:
            return
        
        hack_id = data[10:]
        
        if db:
            hacks_col.delete_one({"_id": ObjectId(hack_id)})
        
        await query.edit_message_text("✅ Hack deleted!")
        # Refresh the hacks list
        query.data = "admin_hacks"
        await button_handler(update, context)
    
    elif data == "admin_stats":
        if user_id not in ADMIN_IDS or not db:
            return
        
        total_users = users_col.count_documents({})
        total_keys = keys_col.count_documents({})
        active_keys = keys_col.count_documents({"status": "active"})
        total_orders = orders_col.count_documents({})
        pending_orders = orders_col.count_documents({"status": "pending"})
        completed_orders = orders_col.count_documents({"status": "completed"})
        
        # Revenue
        pipeline = [
            {"$match": {"status": "completed"}},
            {"$group": {"_id": None, "total": {"$sum": "$price"}}}
        ]
        result = list(orders_col.aggregate(pipeline))
        revenue = result[0]["total"] if result else 0
        
        # Today's stats
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_orders = orders_col.count_documents({"created_at": {"$gte": today}})
        
        pipeline_today = [
            {"$match": {"status": "completed", "created_at": {"$gte": today}}},
            {"$group": {"_id": None, "total": {"$sum": "$price"}}}
        ]
        result_today = list(orders_col.aggregate(pipeline_today))
        today_revenue = result_today[0]["total"] if result_today else 0
        
        await query.edit_message_text(
            f"📊 **Bot Statistics**\n\n"
            f"**Overall:**\n"
            f"👥 Users: {total_users}\n"
            f"🔑 Total Keys: {total_keys}\n"
            f"✅ Active Keys: {active_keys}\n"
            f"📦 Orders: {total_orders}\n"
            f"⏳ Pending: {pending_orders}\n"
            f"✅ Completed: {completed_orders}\n"
            f"💰 Total Revenue: ₹{revenue}\n\n"
            f"**Today:**\n"
            f"📦 Orders: {today_orders}\n"
            f"💰 Revenue: ₹{today_revenue}",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="admin_panel")
            ]])
        )
    
    elif data == "admin_orders":
        if user_id not in ADMIN_IDS or not db:
            return
        
        orders = list(orders_col.find().sort("created_at", -1).limit(10))
        
        msg = "📋 **Recent Orders**\n\n"
        for order in orders:
            status_emoji = "✅" if order['status'] == "completed" else "⏳" if order['status'] == "pending" else "❌"
            msg += f"{status_emoji} **{order['order_id']}**\n"
            msg += f"User: {order['user_id']}\n"
            msg += f"Hack: {order['hack_name']}\n"
            msg += f"Amount: ₹{order['price']}\n"
            msg += f"Date: {order['created_at'].strftime('%d-%m-%Y %H:%M')}\n\n"
        
        await query.edit_message_text(
            msg,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="admin_panel")
            ]])
        )
    
    elif data == "admin_users":
        if user_id not in ADMIN_IDS or not db:
            return
        
        users = list(users_col.find().sort("created_at", -1).limit(10))
        
        msg = "👥 **Recent Users**\n\n"
        for user in users:
            msg += f"ID: `{user['user_id']}`\n"
            msg += f"Name: {user.get('first_name', 'N/A')}\n"
            msg += f"Balance: ₹{user.get('balance', 0)}\n"
            msg += f"Spent: ₹{user.get('total_spent', 0)}\n"
            msg += f"Keys: {len(user.get('keys', []))}\n"
            msg += f"Joined: {user['created_at'].strftime('%d-%m-%Y')}\n\n"
        
        await query.edit_message_text(
            msg,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="admin_panel")
            ]])
        )
    
    elif data == "admin_settings":
        if user_id not in ADMIN_IDS:
            return
        
        settings = get_settings()
        
        msg = f"⚙️ **Current Settings**\n\n"
        msg += f"💳 UPI ID: `{settings.get('upi_id')}`\n"
        msg += f"📱 Admin Contact: {settings.get('admin_contact')}\n"
        msg += f"📧 Admin Email: {settings.get('admin_email')}\n"
        msg += f"💰 Currency: {settings.get('currency')}\n"
        msg += f"📉 Min Amount: {settings.get('currency')}{settings.get('min_amount')}\n"
        msg += f"⏱️ Payment Wait: {settings.get('payment_wait_time')} min\n\n"
        msg += "To change:\n"
        msg += "`/set key value`\n\n"
        msg += "Available keys:\n"
        msg += "• upi_id\n"
        msg += "• admin_contact\n"
        msg += "• admin_email\n"
        msg += "• currency\n"
        msg += "• min_amount\n"
        msg += "• payment_wait_time"
        
        await query.edit_message_text(
            msg,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="admin_panel")
            ]])
        )
    
    elif data == "admin_broadcast":
        if user_id not in ADMIN_IDS:
            return
        
        await query.edit_message_text(
            "📢 **Broadcast Message**\n\n"
            "Send the message you want to broadcast to all users.\n"
            "Type /cancel to abort."
        )
        context.user_data['broadcasting'] = True
        return BROADCAST

# ==================== MESSAGE HANDLERS ====================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    user_id = update.effective_user.id
    
    # Check for broadcast mode
    if context.user_data.get('broadcasting') and user_id in ADMIN_IDS and db:
        users = users_col.find({}, {"user_id": 1})
        sent = 0
        failed = 0
        total = users_col.count_documents({})
        
        status_msg = await update.message.reply_text(f"📢 Broadcasting... 0/{total}")
        
        for user in users:
            try:
                await context.bot.send_message(
                    user['user_id'],
                    update.message.text
                )
                sent += 1
            except Exception as e:
                failed += 1
            
            if sent % 10 == 0:
                await status_msg.edit_text(f"📢 Broadcasting... {sent}/{total}")
        
        await status_msg.edit_text(
            f"✅ **Broadcast Complete!**\n\n"
            f"Total: {total}\n"
            f"Sent: {sent}\n"
            f"Failed: {failed}",
            parse_mode='Markdown'
        )
        context.user_data['broadcasting'] = False
        return
    
    # Check for add hack mode
    if context.user_data.get('adding_hack') and user_id in ADMIN_IDS and db:
        try:
            parts = update.message.text.split('|')
            if len(parts) >= 4:
                category = parts[0].strip()
                name = parts[1].strip()
                price = int(parts[2].strip())
                description = parts[3].strip()
                
                hacks_col.insert_one({
                    "category": category,
                    "name": name,
                    "price": price,
                    "description": description,
                    "available": True,
                    "created_at": datetime.now()
                })
                
                await update.message.reply_text("✅ Hack added successfully!")
                context.user_data['adding_hack'] = False
            else:
                await update.message.reply_text(
                    "❌ Invalid format! Use: Category | Name | Price | Description"
                )
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
        return
    
    # Check for edit hack mode
    if context.user_data.get('editing_hack') and user_id in ADMIN_IDS and db:
        try:
            hack_id = context.user_data.get('edit_hack_id')
            parts = update.message.text.split('|')
            
            if len(parts) >= 5:
                category = parts[0].strip()
                name = parts[1].strip()
                price = int(parts[2].strip())
                description = parts[3].strip()
                available = parts[4].strip().lower() == 'true'
                
                hacks_col.update_one(
                    {"_id": ObjectId(hack_id)},
                    {"$set": {
                        "category": category,
                        "name": name,
                        "price": price,
                        "description": description,
                        "available": available,
                        "updated_at": datetime.now()
                    }}
                )
                
                await update.message.reply_text("✅ Hack updated successfully!")
                context.user_data['editing_hack'] = False
            else:
                await update.message.reply_text(
                    "❌ Invalid format! Use: Category | Name | Price | Description | Available"
                )
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
        return
    
    # Check for add balance
    if context.user_data.get('adding_balance'):
        # This is payment screenshot text - but we need photo
        await update.message.reply_text(
            "❌ Please send the payment screenshot as a photo, not text."
        )
        return

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photos (payment screenshots)"""
    user_id = update.effective_user.id
    
    # Check if adding balance
    if context.user_data.get('adding_balance'):
        # Create payment record
        payment_id = f"PAY{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(100,999)}"
        
        if db:
            payments_col.insert_one({
                "payment_id": payment_id,
                "user_id": user_id,
                "type": "balance_add",
                "status": "pending",
                "screenshot_id": update.message.photo[-1].file_id,
                "created_at": datetime.now()
            })
        
        # Forward to admins
        for admin_id in ADMIN_IDS:
            try:
                await update.message.forward(admin_id)
                await context.bot.send_message(
                    admin_id,
                    f"💰 **Balance Add Request**\n\n"
                    f"User: {update.effective_user.first_name}\n"
                    f"ID: {user_id}\n"
                    f"Payment ID: {payment_id}\n\n"
                    f"Please verify and add balance.",
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("✅ Add Balance", callback_data=f"admin_addbalance_{user_id}_{payment_id}")
                    ]])
                )
            except:
                pass
        
        await update.message.reply_text(
            "✅ Screenshot received! Admin will verify and add balance to your account."
        )
        context.user_data['adding_balance'] = False
        return
    
    # Check for order screenshot
    if context.user_data.get('awaiting_screenshot'):
        order_id = context.user_data.get('pending_order')
        
        # Forward to admins
        for admin_id in ADMIN_IDS:
            try:
                await update.message.forward(admin_id)
                await context.bot.send_message(
                    admin_id,
                    f"💰 **Payment Screenshot**\n\n"
                    f"User: {update.effective_user.first_name}\n"
                    f"ID: {user_id}\n"
                    f"Order: {order_id}\n\n"
                    f"Please verify payment.",
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("✅ Verify", callback_data=f"admin_verify_{order_id}"),
                        InlineKeyboardButton("❌ Reject", callback_data=f"admin_reject_{order_id}")
                    ]])
                )
            except:
                pass
        
        await update.message.reply_text(
            f"✅ Screenshot received! Admin will verify order: {order_id}"
        )
        context.user_data['awaiting_screenshot'] = False
        return
    
    # General photo - forward to admins
    for admin_id in ADMIN_IDS:
        try:
            await update.message.forward(admin_id)
            await context.bot.send_message(
                admin_id,
                f"📸 Photo from {update.effective_user.first_name} (ID: {user_id})"
            )
        except:
            pass
    
    await update.message.reply_text("✅ Photo received!")

async def set_setting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Change settings"""
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Unauthorized!")
        return
    
    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text(
                "Usage: /set key value\n\n"
                "Example:\n"
                "/set upi_id newupi@okhdfcbank\n"
                "/set admin_contact @newadmin\n"
                "/set min_amount 200"
            )
            return
        
        key = args[0]
        value = ' '.join(args[1:])
        
        # Convert numeric values
        if key in ['min_amount', 'payment_wait_time']:
            try:
                value = int(value)
            except:
                await update.message.reply_text("❌ Value must be a number!")
                return
        
        if db:
            settings_col.update_one(
                {"_id": "settings"},
                {"$set": {key: value}},
                upsert=True
            )
        
        await update.message.reply_text(f"✅ {key} updated to: {value}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current operation"""
    context.user_data.clear()
    await update.message.reply_text("❌ Operation cancelled!")
    return ConversationHandler.END

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")
    
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ An error occurred. Please try again later."
            )
    except:
        pass

# ==================== MAIN FUNCTION ====================
def main():
    """Start the bot"""
    # Create application
    application = Application.builder().token(TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set", set_setting))
    application.add_handler(CommandHandler("cancel", cancel))
    
    # Callback handler
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Message handlers
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Start bot
    print("=" * 50)
    print("🤖 Bot Started Successfully!")
    print("=" * 50)
    print(f"📱 Bot Token: {TOKEN[:10]}...{TOKEN[-10:]}")
    print(f"👑 Admin IDs: {ADMIN_IDS}")
    print(f"📦 Database: {'✅ MongoDB' if db else '⚠️ In-Memory'}")
    print(f"💳 UPI ID: {get_settings().get('upi_id')}")
    print("=" * 50)
    print("Bot is running... Press Ctrl+C to stop")
    print("=" * 50)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()