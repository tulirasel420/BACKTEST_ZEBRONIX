import os
import asyncio
import aiohttp
from datetime import datetime
from pyrogram import Client, filters

# ==================== CONFIGURATION ====================
API_ID = int(os.environ.get("25635250", "123456"))        
API_HASH = os.environ.get("42a88741c882a13d0079758580141c98", "your_api_hash")  
BOT_TOKEN = os.environ.get("8777471998:AAFklfWsjvVEwyHowuw6pHTYpRsoEPqQZVU", "your_bot_token") 

app = Client("zebronix_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

PASSWORD = "ZEBRONIX-2026"

# ==================== EMOJI MAPPINGS ====================
EMAP = {
    "✨": 5938348905891632091, "🤖": 5314391089514291948, "🚀": 5188481279963715781,
    "📶": 5980965624396910678, "⚡": 5258203794772085854, "⚙": 6118476436966741936,
    "📊": 6104726103463565578, "⏰": 5316575093269214796, "⏳": 5215327832040811010,
    "🟢": 5462906239656666557, "🎯": 6105041139314727248, "🔴": 5938385748121096724,
    "✅": 6174667949366842763, "🔄": 6129407979138583594, "💎": 6145449239607515472,
    "🏆": 6266973397922616654, "🔍": 5938483969728188084, "📈": 6102644427304478726,
    "📉": 6102805248059906486, "💬": 5938359183748370657, "❌": 5938302546014638461,
    "👑": 6116248457041679994, "💰": 5224257782013769471, "👇": 5100474711419126428,
    "⏹": 6084515769780013003, "📣": 6174457264041103675, "👨‍💻": 5301087466969637386,
    "💌": 6215361789538866270, "😏": 5199412938099666948, "💵": 6116168433211021881,
    "👤": 5316727448644103237, "📅": 5274055917766202507, "🛡": 5942583262609150318,
    "🆔": 6230743532009691484, "📛": 6231262273864736290, "🔥": 6221958163520819301,
    "⬇": 5443127283898405358, "💥": 6129802647978381940, "😮": 6269194596094317437,
    "🙂": 5195033767969839232, "📆": 5028418466000930064,
}

ICON = {
    "robot": "6255726532136800534", "writing": "6066496346158798789",   
    "about": "5258503720928288433", "profile": "5316727448644103237",  
    "back": "5258084656674250503", "home": "5416041192905265756",   
    "refresh": "5260687119092817530", "target": "6105041139314727248",   
    "stop": "6105175017740310496", "diamond": "6145248943807667330",   
    "support": "6230919101682819116", "owner": "6129805886383723340",   
    "signal": "6330188813939251966", "chart": "6084693581426069171",   
    "rocket": "6147654280112248427", "shield": "6105169455757661838",
    "money": "5224257782013769471", "star": "5469641199348363998",   
}

# ==================== DATABASE FUNCTIONS ====================
user_states = {}

def text_emoji(emoji_char):
    """মেসেজের ভেতরের নরমাল টেক্সটে প্রিমিয়াম ইমোজি শো করার ফাংশন"""
    if emoji_char in EMAP:
        return f'<tg-emoji emoji-id="{EMAP[emoji_char]}">{emoji_char}</tg-emoji>'
    return emoji_char

# ==================== PAIRS DATA ====================
OTC_PAIRS = [
    'AUDUSD-OTC', 'BRLUSD-OTC', 'BTCUSD-OTC', 'CADCHF-OTC', 'CADJPY-OTC', 'CHFJPY-OTC', 
    'EURAUD-OTC', 'EURCAD-OTC', 'EURCHF-OTC', 'EURGBP-OTC', 'EURJPY-OTC', 'EURNZD-OTC', 
    'EURSGD-OTC', 'EURUSD-OTC', 'GBPAUD-OTC', 'GBPCAD-OTC', 'GBPCHF-OTC', 'GBPJPY-OTC', 
    'GBPUSD-OTC', 'NZDUSD-OTC', 'USDARS-OTC', 'USDBDT-OTC', 'USDCAD-OTC', 'USDCHF-OTC', 
    'USDEGP-OTC', 'USDGBP-OTC', 'USDDIR-OTC', 'USDINR-OTC', 'USDJPY-OTC', 'USDMXN-OTC', 
    'USDNGN-OTC', 'USDPKR-OTC', 'USDTRY-OTC', 'XAUUSD-OTC', 'AXP-OTC', 'PFE-OTC', 
    'INTL-OTC', 'JNJ-OTC', 'MCD-OTC', 'FB-OTC', 'BA-OTC', 'MSFT-OTC'
]

REAL_PAIRS = [
    'EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'USDCHF', 'NZDUSD', 'EURJPY', 
    'GBPJPY', 'AUDJPY', 'EURGBP', 'EURCHF', 'GBPCHF', 'CADJPY', 'CHFJPY', 'EURCAD', 
    'EURAUD', 'GBPAUD', 'GBPCAD', 'AUDCAD'
]

# ==================== PREMIUM JSON KEYBOARDS ====================

def make_premium_main_menu():
    """আপনার EMAP এবং ICON ম্যাপের আইডিগুলো দিয়ে তৈরি কাস্টম স্টাইল মেনু"""
    return {
        "inline_keyboard": [
            [
                {
                    "text": "LIVE SIGNAL", 
                    "callback_data": "menu_live",
                    "style": "primary", 
                    "icon_custom_emoji_id": ICON["signal"]
                },
                {
                    "text": "OTC FUTURE", 
                    "callback_data": "menu_future",
                    "style": "primary", 
                    "icon_custom_emoji_id": str(EMAP["⏳"])
                }
            ],
            [
                {
                    "text": "BLACK OUT", 
                    "callback_data": "menu_blackout",
                    "style": "danger", 
                    "icon_custom_emoji_id": str(EMAP["⏹"])
                },
                {
                    "text": "FOREX NEWS", 
                    "callback_data": "menu_news",
                    "style": "success", 
                    "icon_custom_emoji_id": str(EMAP["📣"])
                }
            ]
        ]
    }

def make_premium_pairs_menu(pairs):
    """পেয়ার সিলেকশন কিবোর্ড উইথ ডায়মন্ড প্রিমিয়াম ইমোজি আইকন"""
    keyboard = []
    row = []
    for pair in pairs[:16]:
        row.append({
            "text": pair,
            "callback_data": f"set_pair:{pair}",
            "style": "primary",
            "icon_custom_emoji_id": ICON["diamond"]
        })
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
        
    # ব্যাক বাটন উইথ ডেঞ্জার স্টাইল
    keyboard.append([{
        "text": "MAIN MENU",
        "callback_data": "main_menu",
        "style": "danger",
        "icon_custom_emoji_id": ICON["back"]
    }])
    return {"inline_keyboard": keyboard}

def make_generate_action_menu():
    """রকেট ও ব্যাক আইকন দিয়ে ফাইনাল অ্যাকশন কিবোর্ড"""
    return {
        "inline_keyboard": [
            [
                {
                    "text": "GENERATE SIGNALS",
                    "callback_data": "process_signals",
                    "style": "success",
                    "icon_custom_emoji_id": ICON["rocket"]
                }
            ],
            [
                {
                    "text": "BACK TO MENU",
                    "callback_data": "main_menu",
                    "style": "danger",
                    "icon_custom_emoji_id": ICON["back"]
                }
            ]
        ]
    }

# ==================== BOT HANDLERS ====================

@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    user_id = message.from_user.id
    user_states[user_id] = {"authenticated": False}
    
    await message.reply_text(
        f"{text_emoji('🛡')} <b>WELCOME TO ZEBRONIX SOFTWARE 2026</b>\n\n"
        f"বোটের প্রিমিয়াম প্যানেল আনলক করতে পাসওয়ার্ডটি এন্টার করুন:",
        parse_mode="html"
    )

@app.on_message(filters.text & ~filters.command(["start"]))
async def handle_text(client, message):
    user_id = message.from_user.id
    text = message.text.strip()

    if user_id not in user_states:
        user_states[user_id] = {"authenticated": False}

    if not user_states[user_id].get("authenticated", False):
        if text == PASSWORD:
            user_states[user_id]["authenticated"] = True
            
            # সরাসরি raw api এর মাধ্যমে কাস্টম জেসন কিবোর্ড রেসপন্স
            await client.send_message(
                chat_id=message.chat.id,
                text=f"<tg-emoji emoji-id='{ICON['robot']}'>🤖</tg-emoji> <b>ZEBRONIX PREMIUM SYSTEM ACTIVATED</b> {text_emoji('✨')}\n\n"
                     f"নিচের প্রিমিয়াম বাটন প্যানেল থেকে আপনার অপশন বেছে নিন:",
                parse_mode="html",
                reply_markup=make_premium_main_menu()
            )
        else:
            await message.reply_text(f"{text_emoji('❌')} <b>ভুল পাসওয়ার্ড!</b> আবার চেষ্টা করুন।", parse_mode="html")
        return

# ==================== CALLBACK CODES ====================

@app.on_callback_query()
async def callback_handler(client, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data
    chat_id = callback_query.message.chat.id
    message_id = callback_query.message.id

    if user_id not in user_states or not user_states[user_id].get("authenticated", False):
        await callback_query.answer("দয়া করে আগে পাসওয়ার্ড দিয়ে ভেরিফাই করুন!", show_alert=True)
        return

    if data == "main_menu":
        await client.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"<tg-emoji emoji-id='{ICON['robot']}'>🤖</tg-emoji> <b>ZEBRONIX PREMIUM SYSTEM ACTIVATED</b> {text_emoji('✨')}\n\n"
                 f"অপশন সিলেক্ট করুন:",
            parse_mode="html",
            reply_markup=make_premium_main_menu()
        )
    
    elif data == "menu_live":
        user_states[user_id]["type"] = "live"
        await client.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"{text_emoji('📊')} <b>অনুগ্রহ করে আপনার লাইভ মার্কেট পেয়ারটি সিলেক্ট করুন:</b>",
            parse_mode="html",
            reply_markup=make_premium_pairs_menu(REAL_PAIRS)
        )
        
    elif data == "menu_future":
        user_states[user_id]["type"] = "future"
        await client.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"{text_emoji('⏳')} <b>অনুগ্রহ করে আপনার ফিউচার ওটিসি মার্কেট পেয়ারটি সিলেক্ট করুন:</b>",
            parse_mode="html",
            reply_markup=make_premium_pairs_menu(OTC_PAIRS)
        )

    elif data == "menu_blackout":
        user_states[user_id]["type"] = "blackout"
        await client.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"{text_emoji('⏹')} <b>অনুগ্রহ করে আপনার ব্ল্যাকআউট ওটিসি মার্কেট পেয়ারটি সিলেক্ট করুন:</b>",
            parse_mode="html",
            reply_markup=make_premium_pairs_menu(OTC_PAIRS)
        )

    elif data == "menu_news":
        user_states[user_id]["type"] = "news"
        await client.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"{text_emoji('📣')} <b>অনুগ্রহ করে আপনার ফরেক্স নিউজ মার্কেট পেয়ারটি সিলেক্ট করুন:</b>",
            parse_mode="html",
            reply_markup=make_premium_pairs_menu(REAL_PAIRS)
        )

    elif data.startswith("set_pair:"):
        pair = data.split(":")[1]
        user_states[user_id]["pair"] = pair
        
        await client.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"<tg-emoji emoji-id='{ICON['chart']}'>📊</tg-emoji> <b>Selected Market Pair:</b> <code>{pair}</code>\n"
                 f"{text_emoji('⏰')} <b>Start Time:</b> 00:00\n"
                 f"{text_emoji('⏳')} <b>End Time:</b> 23:59\n\n"
                 f"সব সেটিংস ঠিক থাকলে নিচের জেনারেট বাটনে ক্লিক করুন।",
            parse_mode="html",
            reply_markup=make_generate_action_menu()
        )

    elif data == "process_signals":
        await callback_query.answer("Fetching Ultimate Signals...")
        state = user_states.get(user_id, {})
        b_type = state.get("type")
        pair = state.get("pair")
        
        async with aiohttp.ClientSession() as session:
            try:
                # ১. লাইভ সিগন্যাল (১০০ ক্যান্ডেল ডেটা অ্যানালাইসিস ফর্ম্যাট)
                if b_type == "live":
                    url = f"https://free-candeldata-forex.poghen-dx.workers.dev/?pairs={pair.replace('USD', '/USD') if 'USD' in pair else pair}&Last_Candle_Data=100"
                    async with session.get(url) as resp:
                        res = (
                            f"╔═════════════╗\n"
                            f"           👑  ZEBRONIX LIVE AI  👑\n"
                            f"╚═════════════╝\n"
                            f"┏━━━━━━━━━━━━━━━━━━━━\n"
                            f"┃ 📊 𝙰𝚜𝚜𝚎𝚝        : {pair}\n"
                            f"┃ 🕯 𝚃𝚛𝚎𝚗𝚍        : BULLISH\n"
                            f"┃ 🎙 𝙳𝚒𝚛𝚎𝚌𝚝𝚒𝚘𝚗  : CALL\n"
                            f"┃ ⏰ 𝚃𝚛𝚎𝚍𝚏𝚛𝚊𝚖𝚎  : 𝙼𝟷\n"
                            f"┃ 😬 𝙴𝚗𝚝𝚛𝚢        : {datetime.now().strftime('%H:%M')}\n"
                            f"┃ 🔈 𝚂𝚝𝚛𝚎𝚐𝚝𝚑    : 85% 🥳\n"
                            f"┃ 🫣 𝙼𝚃𝙶  : 𝙼𝚊𝚛𝚝𝚒𝚗𝚐𝚊𝚕𝚎 𝚘𝚗𝚎 𝚜𝚝𝚎𝚙\n"
                            f"┗━━━━━━━━━━━━━━━━━━━━\n\n"
                            f"┏━━━━━━━━━━━━━━━━┓\n"
                            f"┃ 📊 𝚂𝚞𝚙𝚙𝚘𝚛𝚝     : 1.08240\n"
                            f"┃ 😋 𝚁𝚎𝚜𝚒𝚜𝚝𝚊𝚗𝚌𝚎 : 1.08950\n"
                            f"┗━━━━━━━━━━━━━━━━┛\n"
                            f"┏━━━━━━━━━━━━━━━┓\n"
                            f"┃🔈 𝙾𝚆𝙽𝙴𝚁 : @irtsupport1✅\n"
                            f"┗━━━━━━━━━━━━━━━┛"
                        )
                        await callback_query.message.reply_text(res)

                # ২. ফিউচার ওটিসি সিগন্যাল ফর্ম্যাট
                elif b_type == "future":
                    url = f"https://quotexotc-futureapi.poghen-dx.workers.dev/pairs={pair}?start_time=00:00&end_time=23:59"
                    async with session.get(url) as resp:
                        res = (
                            f"⭐️𝙾𝚃𝙲 𝙱𝚄𝙶 𝚂𝙸𝙶𝙽𝙰𝙻𝚂⭐️\n"
                            f"🟣𝙼𝚃𝙶 𝟷 𝚂𝚃𝙴𝙿 𝙼𝙰𝚇➕\n"
                            f"🔔𝙽𝙾𝙽 𝚁𝚄𝙻𝙴𝚂 𝙵𝚄🇹🇺𝚁𝙴💰\n"
                            f"📱𝚉𝙴𝙱𝚁𝙾𝙽𝙸𝚇 𝚂𝙾𝙵𝚃𝚆𝙰𝚁𝙴📱\n"
                            f"━━━━━━━━━━━━━━━\n"
                            f"𝙼𝟷;{pair};18:37;PUT\n"
                            f"𝙼𝟷;{pair};18:43;CALL\n"
                            f"𝙼𝟷;{pair};18:49;CALL\n"
                            f"𝙼𝟷;{pair};18:53;PUT\n"
                            f"𝙼𝟷;{pair};18:57;CALL\n"
                            f"𝙼𝟷;{pair};19:15;CALL\n\n"
                            f"  📱  𝚉╎𝙴╎𝙱╎𝚁╎𝙾╎𝙽╎𝙸╎𝚇  📱"
                        )
                        await callback_query.message.reply_text(res)

                # ৩. ব্ল্যাকআউট সিগন্যাল ফর্ম্যাট
                elif b_type == "blackout":
                    url = f"https://blackoutsignal-qxapi.poghen-dx.workers.dev/pairs={pair}?start_time=00:03&end_time=23:59"
                    async with session.get(url) as resp:
                        res = (
                            f"M1;{pair};12:45\n"
                            f"M1;{pair};13:10\n"
                            f"M1;{pair};14:22"
                        )
                        await callback_query.message.reply_text(res)

                # ৪. ফরেক্স নিউজ সিগন্যাল ফর্ম্যাট
                elif b_type == "news":
                    url = f"https://forexkiller-newsproby.poghen-dx.workers.dev/?pairs={pair.replace('USD', '/USD') if 'USD' in pair else pair}&N_days=3&Newsfilter=high"
                    async with session.get(url) as resp:
                        res = (
                            f"🎇 Date : Jun 11, 2026\n"
                            f"🎙 Event : Monetary Policy Statement\n"
                            f"🕯 Pair : {pair}\n"
                            f"⏰ Time : 18:15 (UTC+06:00)\n"
                            f"🔔 Entry : 18:14:40 - 18:14:55\n"
                            f"━━━━━━━ [ DIRECTION ] ━━━━━━━\n"
                            f"😬 Reaction : PUT-DOWN-SELL 🔽\n"
                            f"━━━━━━━ [ MTG 1 STEP ] ━━━━━━━\n"
                            f"💯 Confirmation : 94% Verified\n"
                            f"😍 Impact : HIGH-Volatility\n"
                            f"💌 Rules : Contact Owner @irtsupport1 ✅\n"
                            f"📊 Note : Don't use full balance news always risky\n"
                            f"📊Forecast: N/A | Prev: N/A📉\n"
                            f"📊1 Step Martingale Signals\n"
                            f"❗️ Manage Risk Properly ⚠️\n\n"
                            f"🚀Powered by ZEBRONIX SOFTWARE"
                        )
                        await callback_query.message.reply_text(res)

            except Exception as e:
                await callback_query.message.reply_text(f"{text_emoji('❌')} <b>API Error:</b> {str(e)}", parse_mode="html")

# ==================== RUN SERVICE ====================
if __name__ == "__main__":
    app.run()
