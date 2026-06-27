import os
import threading
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
from flask import Flask

# --- Flask Server for Render Keep-Alive ---
app = Flask('')

@app.route('/')
def home():
    return "ZEBRONIX SONG Bot is Running!"

def run_flask():
    # Render automatic environment variable 'PORT' ব্যবহার করবে
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- Telegram Bot Setup ---
# Render Environment Variable-এ BOT_TOKEN সেট করা থাকলে সেটি নেবে, না থাকলে তোমার দেওয়া টোকেনটি ব্যাকআপ হিসেবে কাজ করবে
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8777471998:AAF-hUhqGReYVq-cJTCh_f2FLOSx6GLjvvA")
bot = telebot.TeleBot(BOT_TOKEN)

# ডাউনলোড ফোল্ডার তৈরি
if not os.path.exists("downloads"):
    os.makedirs("downloads")

# --- Command Handlers ---
@bot.message_handler(commands=['start'])
def start_command(message):
    welcome_text = (
        "🎵 **Welcome to ZEBRONIX SONG Bot!** 🎵\n\n"
        "আমি যেকোনো ভিডিও বা মিউজিক লিংক থেকে অটোমেটিক গান ডাউনলোড করে প্লে করতে পারি। "
        "গান ডাউনলোড করতে সরাসরি লিংকটি এখানে পেস্ট করো।"
    )
    
    # কালার থিম বাটন (Using Emojis)
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🟢 Start / Active", callback_data="start_btn"))
    markup.row(
        InlineKeyboardButton("🔵 Songs Library", callback_data="songs_btn"),
        InlineKeyboardButton("🟡 Style/Settings", callback_data="style_btn")
    )
    markup.row(InlineKeyboardButton("🔴 Danger / Close", callback_data="close_btn"))
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode="Markdown")

# --- Link Downloader Handler (With Cookies Fix) ---
@bot.message_handler(func=lambda message: message.text.startswith("http://") or message.text.startswith("https://"))
def download_and_send_music(message):
    url = message.text
    processing_msg = bot.reply_to(message, "⏳ **ZEBRONIX** আপনার গানটি প্রসেস করছে... দয়া করে অপেক্ষা করুন।")
    
    # Render-এর Environment Variable থেকে কুকি ডাটা নিয়ে টেম্পোরারি ফাইল তৈরি
    cookie_path = "downloads/youtube_cookies.txt"
    cookies_data = os.environ.get("YT_COOKIES")
    
    if cookies_data:
        with open(cookie_path, "w", encoding="utf-8") as f:
            f.write(cookies_data)
    
    # yt-dlp অপশনস (অডিও ডাউনলোডের জন্য)
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True
    }
    
    # যদি Render-এ কুকি সেট করা থাকে, তবে সেটি yt-dlp-এ পাস করা হবে
    if cookies_data and os.path.exists(cookie_path):
        ydl_opts['cookiefile'] = cookie_path
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info).replace(info['ext'], 'mp3')
            title = info.get('title', 'Audio')
        
        # গান পাঠানোর জন্য কন্ট্রোল বাটন
        song_markup = InlineKeyboardMarkup()
        song_markup.row(
            InlineKeyboardButton("⏮️ Back", callback_data="back_btn"),
            InlineKeyboardButton("🔴 Delete", callback_data="delete_file")
        )
        
        # টেলিগ্রামে অ디오 ফাইল সেন্ড করা
        with open(filename, 'rb') as audio:
            bot.send_audio(
                message.chat.id, 
                audio, 
                caption=f"🎶 **Track:** {title}\n🤖 **Bot:** ZEBRONIX SONG", 
                reply_markup=song_markup,
                parse_mode="Markdown"
            )
        
        # কাজ শেষে লোকাল ফাইল এবং কুকি ফাইল ডিলিট করে স্পেস খালি করা
        if os.path.exists(filename): 
            os.remove(filename)
        if os.path.exists(cookie_path): 
            os.remove(cookie_path)
            
        bot.delete_message(message.chat.id, processing_msg.message_id)
        
    except Exception as e:
        # এরর আসলেও যেন কুকি ফাইল ডিলিট হয় তা নিশ্চিত করা
        if os.path.exists(cookie_path): 
            os.remove(cookie_path)
        bot.edit_message_text(f"❌ একটি সমস্যা হয়েছে! লিংকটি সঠিক কিনা চেক করুন।\nError: {str(e)}", message.chat.id, processing_msg.message_id)

# --- Callback Query Handlers (Buttons Functionality) ---
@bot.callback_query_handler(func=lambda call: True)
def handle_buttons(call):
    if call.data == "start_btn":
        bot.answer_callback_query(call.id, "ZEBRONIX SONG Bot ইজ একটিভ! ⚡")
    elif call.data == "songs_btn":
        bot.send_message(call.message.chat.id, "🔵 আপনার পাঠানো গানগুলো এই টেলিগ্রাম চ্যাটেই স্টোর করা আছে।")
    elif call.data == "style_btn":
        bot.answer_callback_query(call.id, "🟡 এই ফিচারটি পরবর্তী আপডেটে আসবে।")
    elif call.data == "close_btn":
        bot.delete_message(call.message.chat.id, call.message.message_id)
    elif call.data == "back_btn":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        start_command(call.message)
    elif call.data == "delete_file":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "🗑️ চ্যাট থেকে মেসেজটি ডিলিট করা হয়েছে।")

# --- Start Threading & Polling ---
if __name__ == "__main__":
    # Flask ব্যাকগ্রাউন্ডে রান করানোর জন্য Threading
    t = threading.Thread(target=run_flask)
    t.start()
    
    print("ZEBRONIX SONG Bot is starting polling...")
    bot.infinity_polling()
