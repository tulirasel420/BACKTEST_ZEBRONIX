# backend.py
import asyncio
import os
import threading
from flask import Flask
from pyrogram import Client, filters
from pyrogram.errors import UserNotParticipant
from config import API_ID, API_HASH, BOT_TOKEN, REQUIRED_CHANNEL
import keyboard
import strategy

# পাইথনের নতুন ভার্সনে অ্যাসিনক্রোনাস লুপ এরর এড়ানোর ফিক্স
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

# Render-এর জন্য Flask Web Server তৈরি করা হচ্ছে
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is alive and running smoothly! 🚀"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host='0.0.0.0', port=port)

# ক্লায়েন্ট ইনিশিয়েট করা
app = Client("quotex_premium_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

USER_FILE = "users.txt"

def save_user_info(user):
    user_id = user.id
    username = f"@{user.username}" if user.username else "No Username"
    first_name = user.first_name or ""
    
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r", encoding="utf-8") as f:
            if str(user_id) in f.read():
                return
                
    with open(USER_FILE, "a", encoding="utf-8") as f:
        f.write(f"ID: {user_id} | Username: {username} | Name: {first_name}\n")

async def check_user_joined(client, user_id):
    try:
        await client.get_chat_member(REQUIRED_CHANNEL, user_id)
        return True
    except UserNotParticipant:
        return False
    except Exception as e:
        # আসল সমস্যা কী তা জানার জন্য এটি Render-এর Logs-এ প্রিন্ট হবে
        print(f"❌ [MEMBERSHIP ERROR]: {str(e)}")
        return False

@app.on_message(filters.command("start"))
async def start_command(client, message):
    user = message.from_user
    save_user_info(user)
    
    is_joined = await check_user_joined(client, user.id)
    
    if not is_joined:
        # আইডি বা ইউজারনেম যাই হোক ক্র্যাশ এড়াতে স্ট্রিং কনভার্ট করা হলো
        clean_target = str(REQUIRED_CHANNEL).replace('@', '')
        invite_link = f"https://t.me/{clean_target}"
        
        await message.reply_text(
            f"❌ **ACCESS DENIED!** ❌\n\nHello {user.mention},\n"
            f"বটটি ব্যবহার করতে আপনাকে অবশ্যই আমাদের অফিশিয়াল গ্রুপ/চ্যানেলে জয়েন করতে হবে।",
            reply_markup=keyboard.join_check_keyboard(invite_link)
        )
        return

    premium_welcome_emoji = "" 
    await message.reply_text(
        f"{premium_welcome_emoji} **WELCOME TO VORTEX AURA** {premium_welcome_emoji}\n\n"
        f"👤 **User:** {user.mention}\n"
        f"🆔 **Username:** @{user.username if user.username else 'N/A'}\n"
        f"📊 Status: **Premium VIP Access Granted** ✅\n\n"
        f"নিচের বাটন থেকে আপনার কাঙ্ক্ষিত অপশনটি সিলেক্ট করুন।",
        reply_markup=keyboard.main_menu_keyboard()
    )

@app.on_callback_query()
async def callback_handler(client, callback_query):
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    if not await check_user_joined(client, user_id):
        await callback_query.answer("⚠️ আপনি গ্রুপ থেকে লিভ নিয়েছেন! আবার জয়েন করুন।", show_alert=True)
        return

    if data == "check_membership":
        await callback_query.message.delete()
        await start_command(client, callback_query.message)
        
    elif data == "news_signal":
        await callback_query.answer("Fetching Live News...")
        news_data = strategy.fetch_news_signals()
        await callback_query.message.edit_text(news_data, reply_markup=keyboard.main_menu_keyboard())
        
    elif data == "get_signal":
        await callback_query.message.edit_text("🎯 **সিগন্যালের জন্য একটি ক্যাটাগরি বেছে নিন:**", reply_markup=keyboard.pairs_menu_keyboard())
        
    elif data == "main_menu":
        await callback_query.message.edit_text("🏡 **প্রধান মেনু:**", reply_markup=keyboard.main_menu_keyboard())

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    print("🚀 Quotex Premium Bot is Starting...")
    app.run()
