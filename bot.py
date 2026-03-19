import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
TOKEN = "8640038443:AAHGFxVYPr8FPrqk5U8j3M49meaWcYMxL9Y"  # Apna bot token yahan daalein
ADMIN_IDS = [5301769589, 8477195695]  # Admin ke Telegram IDs yahan daalein

# MongoDB Connection
MONGO_URI = "mongodb+srv://userbot:userbot@cluster0.iweqz.mongodb.net/test?retryWrites=true&w=majority"  # Agar local MongoDB use kar rahe hain
client = MongoClient(MONGO_URI)
db = client["hack_selling_bot"]
users_collection = db["users"]
keys_collection = db["keys"]
payments_collection = db["payments"]
orders_collection = db["orders"]

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Hack categories and items
HACKS = {
    "pubg": {
        "name": "PUBG Mobile Hacks",
        "items": {
            "aimbot": {"name": "Aimbot + Wallhack", "price": 500},
            "esp": {"name": "ESP Hack", "price": 300},
            "antiban": {"name": "Anti-Ban System", "price": 700}
        }
    },
    "freefire": {
        "name": "Free Fire Hacks",
        "items": {
            "headshot": {"name": "Headshot Hack", "price": 400},
            "aimlock": {"name": "Aimlock", "price": 350},
            "wallhack": {"name": "Wallhack", "price": 450}
        }
    },
    "coc": {
        "name": "Clash of Clans",
        "items": {
            "gems": {"name": "Unlimited Gems", "price": 600},
            "troops": {"name": "Max Troops", "price": 500},
            "builder": {"name": "Auto Builder", "price": 400}
        }
    }
}

# Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    # Save user to database
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "last_active": datetime.now()
        }},
        upsert=True
    )
    
    keyboard = [
        [InlineKeyboardButton("🛒 Buy Hacks", callback_data="buy_hacks")],
        [InlineKeyboardButton("🔑 My Keys", callback_data="my_keys")],
        [InlineKeyboardButton("🔄 Reset Key", callback_data="reset_key")],
        [InlineKeyboardButton("❌ Delete Key", callback_data="delete_key")],
        [InlineKeyboardButton("📞 Contact Admin", callback_data="contact_admin")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_msg = f"👋 Welcome {user.first_name}!\n\n"
    welcome_msg += "This is Hack Selling Panel. Here you can:\n"
    welcome_msg += "✅ Buy premium hacks\n"
    welcome_msg += "✅ View your purchased keys\n"
    welcome_msg += "✅ Reset existing keys\n"
    welcome_msg += "✅ Delete keys\n\n"
    welcome_msg += "Select an option below:"
    
    await update.message.reply_text(welcome_msg, reply_markup=reply_markup)

# Handle button callbacks
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    if data == "buy_hacks":
        await show_hack_categories(query)
    
    elif data == "my_keys":
        await show_user_keys(query)
    
    elif data == "reset_key":
        await show_reset_key_options(query)
    
    elif data == "delete_key":
        await show_delete_key_options(query)
    
    elif data == "contact_admin":
        await show_contact_admin(query)
    
    elif data.startswith("category_"):
        category = data.replace("category_", "")
        await show_hack_items(query, category)
    
    elif data.startswith("item_"):
        parts = data.split("_")
        category = parts[1]
        item_id = parts[2]
        await show_item_details(query, category, item_id)
    
    elif data.startswith("buy_"):
        parts = data.split("_")
        category = parts[1]
        item_id = parts[2]
        await process_payment(query, category, item_id)
    
    elif data.startswith("payment_verify_"):
        parts = data.split("_")
        order_id = parts[2]
        await verify_payment(query, order_id)
    
    elif data.startswith("reset_confirm_"):
        key_id = data.replace("reset_confirm_", "")
        await reset_key(query, key_id)
    
    elif data.startswith("delete_confirm_"):
        key_id = data.replace("delete_confirm_", "")
        await delete_key(query, key_id)
    
    elif data == "back_to_main":
        await back_to_main(query)
    
    elif data == "back_to_categories":
        await show_hack_categories(query)

# Show hack categories
async def show_hack_categories(query):
    keyboard = []
    
    for category_id, category in HACKS.items():
        keyboard.append([InlineKeyboardButton(category["name"], callback_data=f"category_{category_id}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Back to Main", callback_data="back_to_main")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📂 Select a game category:",
        reply_markup=reply_markup
    )

# Show items in selected category
async def show_hack_items(query, category):
    if category not in HACKS:
        await query.edit_message_text("Category not found!")
        return
    
    category_data = HACKS[category]
    keyboard = []
    
    for item_id, item in category_data["items"].items():
        keyboard.append([InlineKeyboardButton(
            f"{item['name']} - ₹{item['price']}",
            callback_data=f"item_{category}_{item_id}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Back to Categories", callback_data="back_to_categories")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"📦 {category_data['name']}\n\nSelect a hack:",
        reply_markup=reply_markup
    )

# Show item details
async def show_item_details(query, category, item_id):
    try:
        item = HACKS[category]["items"][item_id]
        
        msg = f"📦 **{item['name']}**\n\n"
        msg += f"💰 Price: ₹{item['price']}\n"
        msg += f"📁 Category: {HACKS[category]['name']}\n\n"
        msg += "Features:\n"
        msg += "✅ Lifetime validity\n"
        msg += "✅ Regular updates\n"
        msg += "✅ 24/7 support\n"
        msg += "✅ Anti-ban protection\n\n"
        msg += "Click 'Buy Now' to proceed with payment."
        
        keyboard = [
            [InlineKeyboardButton("💳 Buy Now", callback_data=f"buy_{category}_{item_id}")],
            [InlineKeyboardButton("🔙 Back to Items", callback_data=f"category_{category}")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            msg,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    except Exception as e:
        await query.edit_message_text("Error loading item details!")

# Process payment
async def process_payment(query, category, item_id):
    user_id = query.from_user.id
    item = HACKS[category]["items"][item_id]
    
    # Create order
    order = {
        "order_id": f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{user_id}",
        "user_id": user_id,
        "category": category,
        "item_id": item_id,
        "item_name": item['name'],
        "price": item['price'],
        "status": "pending",
        "created_at": datetime.now()
    }
    
    orders_collection.insert_one(order)
    
    # Payment instructions
    msg = f"💳 **Payment Instructions**\n\n"
    msg += f"Item: {item['name']}\n"
    msg += f"Amount: ₹{item['price']}\n\n"
    msg += "**UPI ID:** hacker@paytm\n"
    msg += "**QR Code:** [Click here to view](https://example.com/qr)\n\n"
    msg += "After payment, click 'Verify Payment' and send the screenshot."
    
    keyboard = [
        [InlineKeyboardButton("✅ Verify Payment", callback_data=f"payment_verify_{order['order_id']}")],
        [InlineKeyboardButton("🔙 Cancel", callback_data=f"category_{category}")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        msg,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Verify payment
async def verify_payment(query, order_id):
    user_id = query.from_user.id
    
    order = orders_collection.find_one({"order_id": order_id})
    if not order:
        await query.edit_message_text("Order not found!")
        return
    
    # Generate key
    import random
    import string
    
    key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
    key = '-'.join([key[i:i+4] for i in range(0, 16, 4)])
    
    # Save key
    key_data = {
        "key": key,
        "user_id": user_id,
        "order_id": order_id,
        "item_name": order['item_name'],
        "category": order['category'],
        "item_id": order['item_id'],
        "price": order['price'],
        "purchased_at": datetime.now(),
        "status": "active"
    }
    
    keys_collection.insert_one(key_data)
    
    # Update order
    orders_collection.update_one(
        {"order_id": order_id},
        {"$set": {"status": "completed", "key": key}}
    )
    
    # Notify admin
    admin_msg = f"🔔 **New Purchase!**\n\n"
    admin_msg += f"User: {query.from_user.first_name} (ID: {user_id})\n"
    admin_msg += f"Item: {order['item_name']}\n"
    admin_msg += f"Price: ₹{order['price']}\n"
    admin_msg += f"Order ID: {order_id}\n"
    admin_msg += f"Key: {key}\n\n"
    admin_msg += f"Status: Payment Verified ✅"
    
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(admin_id, admin_msg, parse_mode='Markdown')
        except:
            pass
    
    # Confirm to user
    msg = f"✅ **Payment Verified Successfully!**\n\n"
    msg += f"Your key for {order['item_name']}:\n\n"
    msg += f"🔑 `{key}`\n\n"
    msg += "Save this key. You can view all your keys in 'My Keys' section."
    
    keyboard = [[InlineKeyboardButton("🔙 Main Menu", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        msg,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Show user's keys
async def show_user_keys(query):
    user_id = query.from_user.id
    user_keys = keys_collection.find({"user_id": user_id, "status": "active"})
    
    if keys_collection.count_documents({"user_id": user_id, "status": "active"}) == 0:
        await query.edit_message_text(
            "You don't have any keys yet. Buy hacks to get keys!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🛒 Buy Hacks", callback_data="buy_hacks")
            ]])
        )
        return
    
    msg = "🔑 **Your Active Keys**\n\n"
    keyboard = []
    
    for key in user_keys:
        msg += f"**{key['item_name']}**\n"
        msg += f"Key: `{key['key']}`\n"
        msg += f"Purchased: {key['purchased_at'].strftime('%d-%m-%Y')}\n\n"
        
        keyboard.append([InlineKeyboardButton(
            f"🔄 Reset {key['item_name']}",
            callback_data=f"reset_confirm_{key['_id']}"
        )])
        keyboard.append([InlineKeyboardButton(
            f"❌ Delete {key['item_name']}",
            callback_data=f"delete_confirm_{key['_id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Main Menu", callback_data="back_to_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        msg,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Show reset key options
async def show_reset_key_options(query):
    user_id = query.from_user.id
    user_keys = keys_collection.find({"user_id": user_id, "status": "active"})
    
    if keys_collection.count_documents({"user_id": user_id, "status": "active"}) == 0:
        await query.edit_message_text("No keys available to reset!")
        return
    
    msg = "🔄 **Select key to reset:**\n\n"
    keyboard = []
    
    for key in user_keys:
        keyboard.append([InlineKeyboardButton(
            key['item_name'],
            callback_data=f"reset_confirm_{key['_id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Main Menu", callback_data="back_to_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(msg, reply_markup=reply_markup)

# Reset key
async def reset_key(query, key_id):
    from bson.objectid import ObjectId
    
    key = keys_collection.find_one({"_id": ObjectId(key_id)})
    if not key:
        await query.edit_message_text("Key not found!")
        return
    
    # Generate new key
    import random
    import string
    
    new_key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
    new_key = '-'.join([new_key[i:i+4] for i in range(0, 16, 4)])
    
    # Update key
    keys_collection.update_one(
        {"_id": ObjectId(key_id)},
        {"$set": {"key": new_key, "reset_at": datetime.now()}}
    )
    
    # Notify admin
    admin_msg = f"🔄 **Key Reset**\n\n"
    admin_msg += f"User: {query.from_user.first_name} (ID: {query.from_user.id})\n"
    admin_msg += f"Item: {key['item_name']}\n"
    admin_msg += f"Old Key: `{key['key']}`\n"
    admin_msg += f"New Key: `{new_key}`\n"
    admin_msg += f"Time: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
    
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(admin_id, admin_msg, parse_mode='Markdown')
        except:
            pass
    
    msg = f"✅ **Key Reset Successfully!**\n\n"
    msg += f"Item: {key['item_name']}\n"
    msg += f"New Key: `{new_key}`"
    
    keyboard = [[InlineKeyboardButton("🔙 Main Menu", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(msg, reply_markup=reply_markup, parse_mode='Markdown')

# Show delete key options
async def show_delete_key_options(query):
    user_id = query.from_user.id
    user_keys = keys_collection.find({"user_id": user_id, "status": "active"})
    
    if keys_collection.count_documents({"user_id": user_id, "status": "active"}) == 0:
        await query.edit_message_text("No keys available to delete!")
        return
    
    msg = "❌ **Select key to delete:**\n\n"
    keyboard = []
    
    for key in user_keys:
        keyboard.append([InlineKeyboardButton(
            key['item_name'],
            callback_data=f"delete_confirm_{key['_id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Main Menu", callback_data="back_to_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(msg, reply_markup=reply_markup)

# Delete key
async def delete_key(query, key_id):
    from bson.objectid import ObjectId
    
    key = keys_collection.find_one({"_id": ObjectId(key_id)})
    if not key:
        await query.edit_message_text("Key not found!")
        return
    
    # Soft delete (update status)
    keys_collection.update_one(
        {"_id": ObjectId(key_id)},
        {"$set": {"status": "deleted", "deleted_at": datetime.now()}}
    )
    
    # Notify admin
    admin_msg = f"❌ **Key Deleted**\n\n"
    admin_msg += f"User: {query.from_user.first_name} (ID: {query.from_user.id})\n"
    admin_msg += f"Item: {key['item_name']}\n"
    admin_msg += f"Key: `{key['key']}`\n"
    admin_msg += f"Time: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
    
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(admin_id, admin_msg, parse_mode='Markdown')
        except:
            pass
    
    msg = f"✅ **Key Deleted Successfully!**\n\n"
    msg += f"Item: {key['item_name']} has been removed from your account."
    
    keyboard = [[InlineKeyboardButton("🔙 Main Menu", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(msg, reply_markup=reply_markup)

# Show contact admin
async def show_contact_admin(query):
    msg = "📞 **Contact Admin**\n\n"
    msg += "For any issues or queries, contact:\n\n"
    msg += "📱 Telegram: @admin_username\n"
    msg += "📧 Email: admin@example.com\n\n"
    msg += "Please include your order ID if you have any payment issues."
    
    keyboard = [[InlineKeyboardButton("🔙 Main Menu", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(msg, reply_markup=reply_markup)

# Back to main menu
async def back_to_main(query):
    keyboard = [
        [InlineKeyboardButton("🛒 Buy Hacks", callback_data="buy_hacks")],
        [InlineKeyboardButton("🔑 My Keys", callback_data="my_keys")],
        [InlineKeyboardButton("🔄 Reset Key", callback_data="reset_key")],
        [InlineKeyboardButton("❌ Delete Key", callback_data="delete_key")],
        [InlineKeyboardButton("📞 Contact Admin", callback_data="contact_admin")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "Main Menu - Select an option:",
        reply_markup=reply_markup
    )

# Handle payment screenshots
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Forward to admins
    for admin_id in ADMIN_IDS:
        try:
            await update.message.forward(admin_id)
            
            # Add caption with user info
            caption = f"Payment screenshot from {update.effective_user.first_name} (ID: {user_id})"
            await context.bot.send_message(admin_id, caption)
        except:
            pass
    
    await update.message.reply_text(
        "✅ Payment screenshot received! Admin will verify and activate your key shortly."
    )

# Admin commands
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("You are not authorized!")
        return
    
    total_users = users_collection.count_documents({})
    total_keys = keys_collection.count_documents({})
    active_keys = keys_collection.count_documents({"status": "active"})
    total_orders = orders_collection.count_documents({})
    pending_orders = orders_collection.count_documents({"status": "pending"})
    
    # Calculate total revenue
    pipeline = [
        {"$match": {"status": "completed"}},
        {"$group": {"_id": None, "total": {"$sum": "$price"}}}
    ]
    result = list(orders_collection.aggregate(pipeline))
    total_revenue = result[0]["total"] if result else 0
    
    msg = "📊 **Admin Statistics**\n\n"
    msg += f"👥 Total Users: {total_users}\n"
    msg += f"🔑 Total Keys: {total_keys}\n"
    msg += f"✅ Active Keys: {active_keys}\n"
    msg += f"📦 Total Orders: {total_orders}\n"
    msg += f"⏳ Pending Orders: {pending_orders}\n"
    msg += f"💰 Total Revenue: ₹{total_revenue}"
    
    await update.message.reply_text(msg, parse_mode='Markdown')

# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "An error occurred. Please try again later."
        )

# Main function
def main():
    # Create application
    application = Application.builder().token(TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", admin_stats))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_error_handler(error_handler)
    
    # Start bot
    print("Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()