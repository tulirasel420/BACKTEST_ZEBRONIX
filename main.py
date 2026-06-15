import os
import asyncio
import aiohttp
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

# ==================== CONFIGURATION ====================
API_ID = int(os.environ.get("API_ID", "25635250"))        
API_HASH = os.environ.get("API_HASH", "42a88741c882a13d0079758580141c98")  
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8777471998:AAFklfWsjvVEwyHowuw6pHTYpRsoEPqQZVU") 

app = Client("zebronix_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

PASSWORD = "ZEBRONIX-2026"

# ==================== DATABASE STATES ====================
user_states = {}

# ==================== TIME CONVERSION HELPER (BDT to UTC) ====================
def convert_to_api_time(user_time_str):
    try:
        user_dt = datetime.strptime(user_time_str, "%H:%M")
        api_dt = user_dt - timedelta(hours=6)
        return api_dt.strftime("%H:%M")
    except:
        return user_time_str

# ==================== SELECTED TOP 5 PAIRS ====================
REAL_PAIRS = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD']
OTC_PAIRS = ['EURUSD-OTC', 'GBPUSD-OTC', 'USDJPY-OTC', 'AUDUSD-OTC', 'USDCAD-OTC']

# ==================== PREMIUM KEYBOARDS ====================
def make_premium_main_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 LIVE SIGNAL", callback_data="menu_live"), 
            InlineKeyboardButton("⏳ OTC FUTURE", callback_data="menu_future")
        ],
        [
            InlineKeyboardButton("⏹ BLACK OUT", callback_data="menu_blackout"), 
            InlineKeyboardButton("📣 FOREX NEWS", callback_data="menu_news")
        ]
    ])

def make_premium_pairs_menu(pairs):
    keyboard = [[InlineKeyboardButton(f"💎 {pair}", callback_data=f"set_pair:{pair}")] for pair in pairs]
    keyboard.append([InlineKeyboardButton("🔙 MAIN MENU", callback_data="main_menu")])
    return InlineKeyboardMarkup(keyboard)

def make_generate_action_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 GENERATE SIGNALS", callback_data="process_signals")],
        [InlineKeyboardButton("🔙 BACK TO MENU", callback_data="main_menu")]
    ])

# ==================== BOT HANDLERS ====================
@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    user_states[message.from_user.id] = {"authenticated": False}
    await message.reply_text(
        '<tg-emoji emoji-id="6115911147490123771">💻</tg-emoji> <b>WELCOME TO ZEBRONIX SOFTWARE 2026 <tg-emoji emoji-id="6312053434790976755">📊</tg-emoji></b>\n\n'
        'বোটের প্রিমিয়াম প্যানেল আনলক করতে পাসওয়ার্ডটি এন্টার করুন:', 
        parse_mode=ParseMode.HTML
    )

@app.on_message(filters.text & ~filters.command(["start"]))
async def handle_text(client, message):
    user_id = message.from_user.id
    text = message.text.strip()
    if user_id not in user_states: 
        user_states[user_id] = {"authenticated": False}
    
    state = user_states[user_id]
    
    # পাসওয়ার্ড চেক
    if not state.get("authenticated", False):
        if text == PASSWORD:
            state["authenticated"] = True
            await client.send_message(
                chat_id=message.chat.id, 
                text='<tg-emoji emoji-id="6131826698561265458">🎙</tg-emoji> <b>ZEBRONIX ACTIVATED</b>\n\nনিচের বাটন প্যানেল থেকে অপশন সিলেক্ট করুন:', 
                parse_mode=ParseMode.HTML, 
                reply_markup=make_premium_main_menu()
            )
        else: 
            await message.reply_text('<tg-emoji emoji-id="6154405023808758521">🔥</tg-emoji> <b>ভুল পাসওয়ার্ড!</b> আবার চেষ্টা করুন।', parse_mode=ParseMode.HTML)
        return

    # স্টার্ট টাইম ইনপুট
    if state.get("step") == "awaiting_start_time":
        state["start_time"] = text
        state["step"] = "awaiting_end_time"
        await message.reply_text("⏳ <b>End Time লিখুন (যেমন 23:59):</b>", parse_mode=ParseMode.HTML)
        return
        
    # এন্ড টাইম ইনপুট
    elif state.get("step") == "awaiting_end_time":
        state["end_time"] = text
        state["step"] = "ready"
        await message.reply_text(
            f'<tg-emoji emoji-id="6154242686929870878">🎮</tg-emoji> <b>Settings Configured:</b>\n\n'
            f'📊 <b>Pair:</b> <code>{state["pair"]}</code>\n'
            f'⏰ <b>Start Time (BDT):</b> {state["start_time"]}\n'
            f'⏳ <b>End Time (BDT):</b> {state["end_time"]}\n\n'
            f'সব ঠিক থাকলে নিচের জেনারেট বাটনে ক্লিক করুন।', 
            parse_mode=ParseMode.HTML, 
            reply_markup=make_generate_action_menu()
        )
        return

# ==================== CALLBACK CODES ====================
@app.on_callback_query()
async def callback_handler(client, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data
    chat_id = callback_query.message.chat.id
    message_id = callback_query.message.id
    state = user_states.get(user_id)
    
    if not state or not state.get("authenticated"):
        await callback_query.answer("দয়া করে আগে পাসওয়ার্ড দিন!", show_alert=True)
        return

    if data == "main_menu":
        state["step"] = "none"
        await client.edit_message_text(chat_id, message_id, "🤖 <b>অপশন সিলেক্ট করুন:</b>", reply_markup=make_premium_main_menu(), parse_mode=ParseMode.HTML)
    
    elif data.startswith("menu_"):
        state["type"] = data.split("_")[1]
        await client.edit_message_text(
            chat_id=chat_id, 
            message_id=message_id, 
            text="💎 <b>আপনার পছন্দের পেয়ারটি সিলেক্ট করুন (Top 5):</b>", 
            reply_markup=make_premium_pairs_menu(REAL_PAIRS if state["type"] in ["live", "news"] else OTC_PAIRS),
            parse_mode=ParseMode.HTML
        )
        
    elif data.startswith("set_pair:"):
        state["pair"] = data.split(":")[1]
        state["step"] = "awaiting_start_time"
        await client.edit_message_text(
            chat_id=chat_id, 
            message_id=message_id, 
            text='<tg-emoji emoji-id="6212950328610923100">🛡</tg-emoji> <b>Start Time লিখুন (যেমন 00:00):</b>', 
            parse_mode=ParseMode.HTML
        )
    
    elif data == "process_signals":
        await callback_query.answer("Fetching Data From API...")
        
        # BDT থেকে API সার্ভার টাইম জোনে কনভার্ট
        api_start = convert_to_api_time(state.get("start_time", "00:00"))
        api_end = convert_to_api_time(state.get("end_time", "23:59"))
        pair = state.get("pair")
        
        async with aiohttp.ClientSession() as session:
            try:
                url = ""
                if state["type"] == "live": 
                    url = f"https://free-candeldata-forex.poghen-dx.workers.dev/?pairs={pair.replace('USD', '/USD')}&Last_Candle_Data=100"
                elif state["type"] == "future": 
                    url = f"https://quotexotc-futureapi.poghen-dx.workers.dev/pairs={pair}?start_time={api_start}&end_time={api_end}"
                elif state["type"] == "blackout": 
                    url = f"https://blackoutsignal-qxapi.poghen-dx.workers.dev/pairs={pair}?start_time={api_start}&end_time={api_end}"
                elif state["type"] == "news": 
                    url = f"https://forexkiller-newsproby.poghen-dx.workers.dev/?pairs={pair.replace('USD', '/USD')}&N_days=3&Newsfilter=high"
                
                async with session.get(url) as resp:
                    api_response = await resp.text()
                    # এপিআই থেকে আসা ডাটা হুবহু কোন সাজানো জানালা ছাড়াই সেন্ড হবে
                    await callback_query.message.reply_text(api_response)
            except Exception as e:
                await callback_query.message.reply_text(f"❌ Error: {str(e)}")

# ==================== WEB SERVER SETUP ====================
async def web_home(request):
    return web.Response(text="Bot is Running Live!")

# ==================== RUNNER ====================
async def main():
    server = web.Application()
    server.add_routes([web.get('/', web_home)])
    runner = web.AppRunner(server)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

    await app.start()
    await asyncio.Event().wait()

if __name__ == "__main__":
    app.run(main())
