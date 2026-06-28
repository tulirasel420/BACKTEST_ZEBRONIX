# backend.py
import os
from pyrogram import Client, filters
from pyrogram.errors import UserNotParticipant
from config import API_ID, API_HASH, BOT_TOKEN, REQUIRED_CHANNEL, OWNER_USERNAME
import keyboard
import strategy
import pairs

# ক্লায়েন্ট ইনিশিয়েট করা (Bot Token এবং API credentials সহ)
app = Client("quotex_premium_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

USER_FILE = "users.txt"

def save_user_info(user):
    """ইউজারের তথ্য txt ফাইলে সেভ করার ফাংশন"""
    user_id = user.id
    username = f"@{user.username}" if user.username else "No Username"
    first_name = user.first_name or ""
    
    # ডুপ্লিকেট এড়াতে আগে চেক করা
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r", encoding="utf-8") as f:
            if str(user_id) in f.read():
                return
                
    with open(USER_FILE, "a", encoding="utf-8") as f:
        f.write(f"ID: {user_id} | Username: {username} | Name: {first_name}\n")

async def check_user_joined(client, user_id):
    """ইউজার গ্রুপ/চ্যানেলে জয়েন আছে কিনা যাচাই করার ফাংশন"""
    try:
        await client.get_chat_member(REQUIRED_CHANNEL, user_id)
        return True
    except UserNotParticipant:
        return False
    except Exception:
        return False

@app.on_message(filters.command("start"))
async def start_command(client, message):
    user = message.from_user
    save_user_info(user) # ইউজার ইনফো সেভ করা হচ্ছে
    
    is_joined = await check_user_joined(client, user.id)
    
    if not is_joined:
        # জয়েন না থাকলে Decline মেসেজ শো করবে
        await message.reply_text(
            f"❌ **ACCESS DENIED!** ❌\n\nHello {user.mention},\n"
            f"বটটি ব্যবহার করতে আপনাকে অবশ্যই আমাদের অফিশিয়াল গ্রুপ/চ্যানেলে জয়েন করতে হবে।",
            reply_markup=keyboard.join_check_keyboard(f"https://t.me/{REQUIRED_CHANNEL.replace('@','')}")
        )
        return

    # জয়েন থাকলে প্রিমিয়াম ওয়েলকাম মেসেজ
    premium_welcome_emoji = "" # ফাকা রাখা হলো আপনার প্রিমিয়াম ইমোজির জন্য
    await message.reply_text(
        f"{premium_welcome_emoji} **WELCOME TO VORTEX AURA** {premium_welcome_emoji}\n\n"
        f"👤 **User:** {user.mention}\n"
        f"🆔 **Username:** @{user.username if user.username else 'N/A'}\n"
        f" status: **Premium VIP Access Granted** ✅\n\n"
        f"নিচের বাটন থেকে আপনার কাঙ্ক্ষিত অপশনটি সিলেক্ট করুন।",
        reply_markup=keyboard.main_menu_keyboard()
    )

@app.on_callback_query()
async def callback_handler(client, callback_query):
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    # প্রতিটা ক্লিকেই মেম্বারশিপ চেক হবে সিকিউরিটির জন্য
    if not await check_user_joined(client, user_id):
        await callback_query.answer("⚠️ আপনি গ্রুপ থেকে লিভ নিয়েছেন! আবার জয়েন করুন।", show_alert=True)
        return

    if data == "check_membership":
        await callback_query.message.delete()
        # পুনরায় স্টার্ট কমান্ড ট্রিগার করা
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
    print("🚀 Vortex aura is Starting...")
    app.run()
