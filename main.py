import os
import re
import hashlib
import threading
import time
import requests
from datetime import datetime, timedelta
from flask import Flask
import telebot
from telebot import types

# --- Flask Web Server Setup (For 24/7 Hosting) ---
app = Flask('')

@app.route('/')
def home():
    return 'Zebronix Ultimate Control Center is 100% Online!'

def run_web_server():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# --- Configuration Setup ---
API_TOKEN = '8777471998:AAEJ3LzsWqj8JB15_yzwXOMyS1GHEiGtBbI' 
ADMIN_ID = 8280240170                                           
PASSWORD = 'ZEBRONIX1'
USER_FILE = 'users.txt'

CHANNEL_USERNAME = '@irttradingzone'
OWNER_USERNAME = '@irtsupport1'
ADMIN_USERNAME = '@imtiaz_x_admin'
POWERED_BY = 'ZEBRONIX NEWS'

NEWS_API_URL = 'https://forexkiller-newsproby.poghen-dx.workers.dev' 

bot = telebot.TeleBot(API_TOKEN)
user_data = {}

# --- Trading Asset Databases ---
OTC_PAIRS_PLAIN = [
    'TRUUSD-OTC', 'MANUSD-OTC', 'BCHUSD-OTC', 'AXSUSD-OTC', 'ATOUSD-OTC', 'TONUSD-OTC', 
    'MSFT-OTC', 'LTCUSD-OTC', 'USDNGN-OTC', 'USDCOP-OTC', 'USDBRL-OTC', 'USDMXN-OTC', 
    'USDPHP-OTC', 'USDINR-OTC', 'USDZAR-OTC', 'USDBDT-OTC', 'USDPKR-OTC', 'USDARS-OTC', 
    'USDDZD-OTC', 'USDIDR-OTC', 'USDEGP-OTC', 'CADCHF-OTC', 'NZDUSD-OTC', 'NZDCAD-OTC', 
    'AUDCAD-OTC', 'AUDJPY-OTC', 'AUDNZD-OTC', 'GBPJPY-OTC', 'EURCAD-OTC', 'AUDCHF-OTC', 
    'CHFJPY-OTC', 'GBPUSD-OTC', 'EURUSD-OTC', 'USDJPY-OTC', 'USDCAD-OTC', 'USDCHF-OTC', 
    'ETCUSD-OTC', 'BNBUSD-OTC', 'ETHUSD-OTC', 'SOLUSD-OTC'
]

REAL_PAIRS_PLAIN = [
    'EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'USDCHF', 'NZDUSD', 'EURJPY', 
    'GBPJPY', 'AUDJPY', 'EURGBP', 'EURCHF', 'GBPCHF', 'CADJPY', 'CHFJPY', 'EURCAD', 
    'EURAUD', 'GBPAUD', 'GBPCAD', 'AUDCAD'
]

# --- Database Helpers ---
def save_user(chat_id):
    if not os.path.exists(USER_FILE):
        with open(USER_FILE, 'w') as f: pass
    with open(USER_FILE, 'r') as f:
        users = f.read().splitlines()
    if str(chat_id) not in users:
        with open(USER_FILE, 'a') as f:
            f.write(f"{chat_id}\n")

def get_all_users():
    if not os.path.exists(USER_FILE): return []
    with open(USER_FILE, 'r') as f: return f.read().splitlines()

# --- Core Processing Engines ---
def parse_raw_signals(text_block):
    parsed_list = []
    lines = text_block.strip().split('\n')
    pattern = r'([A-Z0-9_-]+ Mini|[A-Z0-9_-]+(?:-OTC)?)[;\s,]+(\d{2}:\d{2})[;\s,]+(CALL|PUT)|(\d{2}:\d{2})[;\s,]+([A-Z0-9_-]+(?:-OTC)?)[;\s,]+(CALL|PUT)|(CALL|PUT)[;\s,]+([A-Z0-9_-]+(?:-OTC)?)[;\s,]+(\d{2}:\d{2})'
    for line in lines:
        if not line.strip(): continue
        cleaned_line = line.upper().replace('M1', '').replace(';', ' ').strip()
        match = re.search(pattern, cleaned_line)
        if match:
            if match.group(1): asset, time_str, direction = match.group(1), match.group(2), match.group(3)
            elif match.group(4): time_str, asset, direction = match.group(4), match.group(5), match.group(6)
            else: direction, asset, time_str = match.group(7), match.group(8), match.group(9)
            parsed_list.append({'asset': asset, 'time': time_str, 'direction': direction})
    return parsed_list

def original_backtest_engine(signals, days_filter):
    if not signals: return []
    signals.sort(key=lambda x: datetime.strptime(x['time'], '%H:%M'))
    unique_time_signals = []
    seen_times = set()
    for sig in signals:
        if sig['time'] not in seen_times:
            seen_times.add(sig['time'])
            unique_time_signals.append(sig)
    final_filtered = []
    min_allowed_gap = int(days_filter) * 3
    last_time = None
    for sig in unique_time_signals:
        current_time = datetime.strptime(sig['time'], '%H:%M')
        if last_time is None:
            final_filtered.append(sig)
            last_time = current_time
        else:
            time_difference = int((current_time - last_time).total_seconds() / 60)
            if time_difference >= min_allowed_gap:
                final_filtered.append(sig)
                last_time = current_time
    return final_filtered

# --- UPDATED AI FILTER LOGIC ---
def custom_ai_filter_logic(signals, days):
    if not signals: return []
    
    # সময় অনুযায়ী সাজানো
    signals.sort(key=lambda x: datetime.strptime(x['time'], '%H:%M'))
    days = int(days)
    
    # ডুপ্লিকেট সময় ফিল্টার করা
    unique_signals = []
    seen_times = set()
    for sig in signals:
        if sig['time'] not in seen_times:
            seen_times.add(sig['time'])
            unique_signals.append(sig)
            
    total_count = len(unique_signals)
    if total_count == 0: return []

    # উন্নত ফিল্টারিং প্যারামিটার (দিন অনুযায়ী গ্যাপ সেট করা)
    gap_matrix = {1: 3, 2: 4, 3: 5, 4: 6, 5: 8, 6: 10, 7: 12}
    min_gap = gap_matrix.get(days, 5)
    
    final_filtered = []
    last_time = None
    
    # অ্যালগরিদম: সিগন্যাল টাইম গ্যাপ এবং কনসিস্টেন্সি চেক
    for sig in unique_signals:
        current_time = datetime.strptime(sig['time'], '%H:%M')
        
        if last_time is None:
            final_filtered.append(sig)
            last_time = current_time
        else:
            time_diff = int((current_time - last_time).total_seconds() / 60)
            # গ্যাপ চেক এবং সিগন্যাল স্থায়িত্ব নিশ্চিত করা
            if time_diff >= min_gap:
                final_filtered.append(sig)
                last_time = current_time
    
    # যদি ফিল্টারের পর খুব কম সিগন্যাল থাকে, কিছু সিগন্যাল রিটেইন করা
    if len(final_filtered) < 2 and total_count > 2:
        return unique_signals[:3]
        
    return final_filtered

def generate_future_signals(valid_markets, start_time, end_time, mode, filter_days):
    generated_list = []
    try:
        start_h, start_m = map(int, start_time.split(':'))
        end_h, end_m = map(int, end_time.split(':'))
        fixed_date_str = datetime.now().strftime('%Y%m%d')
        base_date = datetime.strptime(fixed_date_str, '%Y%m%d')
        start_slot = base_date.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
        end_slot = base_date.replace(hour=end_h, minute=end_m, second=0, microsecond=0)
        
        if end_slot <= start_slot:
            end_slot += timedelta(days=1)
        
        if filter_days <= 3: hash_threshold, gap_modifier = 35, 2
        elif filter_days <= 5: hash_threshold, gap_modifier = 60, 4
        else: hash_threshold, gap_modifier = 82, 7

        for pair in valid_markets:
            current_slot = start_slot
            while current_slot <= end_slot:
                time_str = current_slot.strftime("%H:%M")
                seed = f"{time_str}-{pair}-{mode}-{fixed_date_str}-{filter_days}"
                hasher = int(hashlib.md5(seed.encode()).hexdigest(), 16)
                
                if (hasher % 100) > hash_threshold:
                    direction = "CALL" if (hasher % 2 == 0) else "PUT"
                    generated_list.append({"asset": pair, "time": time_str, "direction": direction})
                
                static_gap = 1 + (hasher % gap_modifier)
                current_slot += timedelta(minutes=static_gap)
    except: pass
    return generated_list

# --- Grid Keyboard Generator ---
def make_pair_selection_keyboard(selected_pairs, mode):
    markup = types.InlineKeyboardMarkup(row_width=2)
    pool = OTC_PAIRS_PLAIN if mode in ["OTC", "BLACKOUT"] else REAL_PAIRS_PLAIN
    
    buttons = []
    for pair in pool:
        label = f"🟢 {pair}" if pair in selected_pairs else f"▪️ {pair}"
        buttons.append(types.InlineKeyboardButton(label, callback_data=f"toggle_{pair}"))
    
    markup.add(*buttons)
    markup.add(types.InlineKeyboardButton("➔ CONTINUE NEXT", callback_data="pair_selection_done"))
    markup.add(types.InlineKeyboardButton("🏠 HOME", callback_data="go_home"))
    return markup

# --- Main Dashboard Setup ---
def show_main_dashboard(chat_id):
    if chat_id not in user_data:
        user_data[chat_id] = {'raw_signals': [], 'selected_pairs': []}
    user_data[chat_id]['state'] = 'MAIN_MENU'
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton('📰 TODAY NEWS', callback_data='btn_today_news'),
        types.InlineKeyboardButton('📊 BACKTEST SIGNAL', callback_data='btn_backtest_mode'),
        types.InlineKeyboardButton('🧠 AI FILTER SIGNAL', callback_data='btn_ai_filter_mode'),
        types.InlineKeyboardButton('🤖 FUTURE GENERATOR', callback_data='btn_future_mode')
    )
    
    dashboard_text = (
        '<tg-emoji emoji-id="6066435044090583397">💰</tg-emoji> <b>WELCOME TO ZEBRONIX SOFTWARE</b>\n\n'
        '<tg-emoji emoji-id="6132052287423522342">💎</tg-emoji> <b>Select your operational module below to start:</b>'
    )
    bot.send_message(chat_id, dashboard_text, reply_markup=markup, parse_mode='HTML')

# --- Live Forex News Core Engine ---
def fetch_and_send_news_signals(chat_id, message_id):
    bot.edit_message_text(chat_id=chat_id, message_id=message_id, text='<pre>Fetching Live News Data <tg-emoji emoji-id=\"6312077782960579315\">🆕</tg-emoji>...</pre>', parse_mode='HTML')
    
    try:
        response = requests.get(NEWS_API_URL, timeout=15)
        if response.status_code != 200:
            bot.send_message(chat_id, "<tg-emoji emoji-id=\"6312054040381367354\">🕯</tg-emoji> <b>API no data please wait.. (Status Error)</b>", parse_mode='HTML')
            return
            
        data = response.json()
        if data.get("status") != "success" or not data.get("signals"):
            bot.send_message(chat_id, "<tg-emoji emoji-id=\"6312054040381367354\">🕯</tg-emoji> <b>বর্তমানে কোনো লাইভ নিউজ সিগন্যাল উপলব্ধ নেই।</b>", parse_mode='HTML')
            return
            
        for sig in data["signals"]:
            date = sig.get("date", "N/A")
            event = sig.get("event", "N/A")
            pair = sig.get("pair", "N/A")
            time_str = sig.get("time", "N/A")
            entry_window = sig.get("entry_window", "N/A")
            direction = sig.get("direction", "N/A").upper()
            confirmation = sig.get("confirmation", "N/A")
            impact = sig.get("impact", "N/A").upper()
            forecast = sig.get("forecast", "N/A")
            previous = sig.get("previous", "N/A")
            
            reaction_emoji = "<tg-emoji emoji-id=\"6311874557993033039\">🔼</tg-emoji>" if "BUY" in direction else "<tg-emoji emoji-id=\"6312244088389247483\">🔽</tg-emoji>"
            
            news_template = (
                f'<tg-emoji emoji-id="6132037293692691226">🎇</tg-emoji> <b>Date</b> : {date}\n'
                f'<tg-emoji emoji-id="6131826698561265458">🎙</tg-emoji> <b>Event</b> : {event}\n'
                f'<tg-emoji emoji-id="6312054040381367354">🕯</tg-emoji> <b>Pair</b> : {pair}\n'
                f'<tg-emoji emoji-id="6311921227107671342">⏰</tg-emoji> <b>Time</b> : {time_str} (UTC+06:00)\n'
                f'<tg-emoji emoji-id="6312196117899517195">🔔</tg-emoji> <b>Entry</b> : {entry_window}\n'
                f"━━━━━━━ [ DIRECTION ] ━━━━━━━\n"
                f'<tg-emoji emoji-id="6311943144325783428">😬</tg-emoji> <b>Reaction</b> : {direction} {reaction_emoji}\n'
                f"━━━━━━━ [ MTG 1 STEP ] ━━━━━━━\n"
                f'<tg-emoji emoji-id="6311864288726228831">💯</tg-emoji> <b>Confirmation</b> : {confirmation} Verified\n'
                f'<tg-emoji emoji-id="6300609412826406453">😍</tg-emoji> <b>Impact</b> : {impact}-Volatility\n'
                f'<tg-emoji emoji-id="6300781159978639271">💌</tg-emoji> <b>Rules</b> : Contact Owner {OWNER_USERNAME} <tg-emoji emoji-id=\"6300666179409157866\">✅</tg-emoji>\n'
                f'<tg-emoji emoji-id="6303181741754424089">📊</tg-emoji> <b>Note</b> : Don\'t use full balance news always risky\n'
                f'<tg-emoji emoji-id="6300603412757093500">📊</tg-emoji>Forecast: {forecast} | Prev: {previous}<tg-emoji emoji-id="6300810288446840855">📉</tg-emoji>\n'
                f'<tg-emoji emoji-id="6302799249146911743">📊</tg-emoji>1 Step Martingale Signals\n'
                f'<tg-emoji emoji-id="6303243301520678287">❗️</tg-emoji> Manage Risk Properly <tg-emoji emoji-id="6303178164046666974">⚠️</tg-emoji>\n\n'
                f'<tg-emoji emoji-id="6300570740940874222">🚀</tg-emoji><b>Powered by {POWERED_BY}</b>'
            )
            bot.send_message(chat_id, news_template, parse_mode='HTML')
            time.sleep(0.4)
            
        end_markup = types.InlineKeyboardMarkup()
        end_markup.add(types.InlineKeyboardButton("🏠 MAIN DASHBOARD", callback_data="go_home"))
        
        credit_text = (
            f'<tg-emoji emoji-id="6303181741754424089">📊</tg-emoji> <b>Channel: {CHANNEL_USERNAME}\n'
            f'<tg-emoji emoji-id="6303015509340201177">👑</tg-emoji> Owner   : {OWNER_USERNAME}\n'
            f'<tg-emoji emoji-id="6303081480037866015">🍾</tg-emoji> Admin  : {ADMIN_USERNAME}\n'
            f'<tg-emoji emoji-id="6300924843814558816">☄️</tg-emoji> Powered By: {POWERED_BY}</b>'
        )
        bot.send_message(chat_id, credit_text, reply_markup=end_markup, parse_mode='HTML')

    except Exception as e:
        bot.send_message(chat_id, f"❌ <b>Error Occured:</b> <code>{str(e)}</code>", parse_mode='HTML')

# --- Start Action ---
@bot.message_handler(commands=['start'])
def start_command(message):
    chat_id = message.chat.id
    save_user(chat_id)
    bot.send_message(chat_id, '<tg-emoji emoji-id="5429405838345265327">🔓</tg-emoji> <b>Please enter password to access Control Center:</b>', parse_mode='HTML')
    user_data[chat_id] = {'state': 'AWAITING_PASSWORD', 'raw_signals': [], 'selected_pairs': []}

@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get('state') == 'AWAITING_PASSWORD')
def check_password(message):
    chat_id = message.chat.id
    if message.text.strip() == PASSWORD:
        show_main_dashboard(chat_id)
    else:
        bot.send_message(chat_id, '<tg-emoji emoji-id="6066584947039148700">⚠️</tg-emoji> <b>Wrong Password! Try again.</b>', parse_mode='HTML')

# --- Core Inline Router Hub ---
@bot.callback_query_handler(func=lambda call: True)
def global_callback_router(call):
    chat_id = call.message.chat.id
    state = user_data.get(chat_id, {}).get('state')

    if call.data == 'go_home':
        show_main_dashboard(chat_id)
        return

    if call.data == 'btn_today_news':
        fetch_and_send_news_signals(chat_id, call.message.message_id)
        return

    if call.data == 'btn_backtest_mode':
        user_data[chat_id]['state'] = 'COLLECTING_BACKTEST'
        user_data[chat_id]['raw_signals'] = []  
        welcome_text = (
            '<tg-emoji emoji-id="6276089822490662156">😉</tg-emoji><tg-emoji emoji-id="6278133818901666441">😌</tg-emoji><tg-emoji emoji-id="6276079828101765459">😇</tg-emoji><tg-emoji emoji-id="6275803150603522302">😊</tg-emoji><tg-emoji emoji-id="6275939064843603913">🚀</tg-emoji><tg-emoji emoji-id="6275853229922193308">🅰</tg-emoji><tg-emoji emoji-id="6278459282933419717">🅰</tg-emoji><tg-emoji emoji-id="6276014351325337415">🅰</tg-emoji><tg-emoji emoji-id="6278369556771639533">🅰</tg-emoji>\n\n'
            '<tg-emoji emoji-id="6300758774609092069">🌍</tg-emoji> <b> ORIGINAL BACKTEST MODULE</b>\n\n'
            '<tg-emoji emoji-id="6075388783887392362">🚀</tg-emoji> <b>Paste your raw lines below.</b>\n\n'
            '<i>When completely finished, send</i> <b>/done</b> <i>to compile original data.</i>'
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🏠 CANCEL & HOME", callback_data="go_home"))
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=welcome_text, reply_markup=markup, parse_mode='HTML')
        return

    if call.data == 'btn_ai_filter_mode':
        user_data[chat_id]['state'] = 'COLLECTING_AI_FILTER'
        user_data[chat_id]['raw_signals'] = []  
        welcome_text = (
            '<tg-emoji emoji-id="1134212600138833922">🧠</tg-emoji> <b>AI FILTER SIGNAL MODULE</b>\n\n'
            '<tg-emoji emoji-id="6075388783887392362">🚀</tg-emoji> <b>Paste your signal lines below.</b>\n\n'
            '<i>When completely finished, send</i> <b>/done</b> <i>to apply math cut filters.</i>'
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🏠 CANCEL & HOME", callback_data="go_home"))
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=welcome_text, reply_markup=markup, parse_mode='HTML')
        return

    if call.data == 'btn_future_mode':
        user_data[chat_id]['state'] = 'FUTURE_MARKET_SELECT'
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton('📊 OTC MARKETS', callback_data='f_m_OTC'),
            types.InlineKeyboardButton('📈 REAL MARKETS', callback_data='f_m_REAL'),
            types.InlineKeyboardButton('🥷 BLACKOUT SIGNALS', callback_data='f_m_BLACKOUT'),
            types.InlineKeyboardButton('🏠 HOME', callback_data='go_home')
        )
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text='<tg-emoji emoji-id="6073116733302906931">⛈</tg-emoji> <b>SELECT TARGET MARKET TYPE FROM BELOW:</b>', reply_markup=markup, parse_mode='HTML')
        return

    if state == 'DAYS_SELECT_BACKTEST' and call.data.startswith('b_day_'):
        selected_day = call.data.split('_')[2]
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text='<tg-emoji emoji-id="5440410042773824003">🔗</tg-emoji> <b>Running Original Backtest Engine...</b>', parse_mode='HTML')
        
        raw_list = user_data[chat_id].get('raw_signals', [])
        filtered_list = original_backtest_engine(raw_list, selected_day)
        
        header_text = f'<b><tg-emoji emoji-id="6172600880391526117">🗓</tg-emoji> BACKTEST COMPLETED (Day {selected_day})</b>\n<b>━━━━━━━━━━━━━━━━━</b>\n'
        body_text = "<code>" + "".join([f"M1;{s['asset'].replace('<','&lt;').replace('>','&gt;')};{s['time']};{s['direction']}\n" for s in filtered_list]) + "</code>" if filtered_list else "<code>No matching setups.</code>\n"
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("⬅️ BACK", callback_data="back_to_b_days"), types.InlineKeyboardButton("🏠 HOME", callback_data="go_home"))
        bot.send_message(chat_id, header_text + body_text, reply_markup=markup, parse_mode='HTML')
        return

    if call.data == "back_to_b_days":
        user_data[chat_id]['state'] = 'DAYS_SELECT_BACKTEST'
        markup = types.InlineKeyboardMarkup(row_width=3)
        markup.add(*[types.InlineKeyboardButton(f"🗓 Day {i}", callback_data=f'b_day_{i}') for i in range(1, 8)])
        markup.add(types.InlineKeyboardButton("🏠 HOME", callback_data="go_home"))
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text='<b>Choose Backtest Days Depth Strategy:</b>', reply_markup=markup, parse_mode='HTML')
        return

    if state == 'DAYS_SELECT_AI_FILTER' and call.data.startswith('ai_day_'):
        selected_day = call.data.split('_')[2]
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text='<tg-emoji emoji-id="5440410042773824003">🔗</tg-emoji> <b>Running AI Filter Matrix Processing...</b>', parse_mode='HTML')
        
        raw_list = user_data[chat_id].get('raw_signals', [])
        filtered_list = custom_ai_filter_logic(raw_list, selected_day)
        
        header_text = f'<b><tg-emoji emoji-id="6300963760513228226">🥳</tg-emoji> AI FILTER SIGNAL COMPLETED (Day {selected_day})</b>\n<b>━━━━━━━━━━━━━━━━━</b>\n'
        body_text = "<code>" + "".join([f"M1;{s['asset'].replace('<','&lt;').replace('>','&gt;')};{s['time']};{s['direction']}\n" for s in filtered_list]) + "</code>" if filtered_list else "<code>No parameters matching clear klines.</code>\n"
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("⬅️ BACK", callback_data="back_to_ai_days"), types.InlineKeyboardButton("🏠 HOME", callback_data="go_home"))
        bot.send_message(chat_id, header_text + body_text, reply_markup=markup, parse_mode='HTML')
        return

    if call.data == "back_to_ai_days":
        user_data[chat_id]['state'] = 'DAYS_SELECT_AI_FILTER'
        markup = types.InlineKeyboardMarkup(row_width=3)
        markup.add(*[types.InlineKeyboardButton(f"🗓 Day {i}", callback_data=f'ai_day_{i}') for i in range(1, 8)])
        markup.add(types.InlineKeyboardButton("🏠 HOME", callback_data="go_home"))
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text='<b>Choose AI Cut Strategy Range Matrix:</b>', reply_markup=markup, parse_mode='HTML')
        return

    if state == 'FUTURE_MARKET_SELECT' and call.data.startswith('f_m_'):
        mode = call.data.replace('f_m_', '')
        user_data[chat_id]['market_mode'] = mode
        user_data[chat_id]['selected_pairs'] = []  
        user_data[chat_id]['state'] = 'FUTURE_GRID_SELECTING'
        
        keyboard = make_pair_selection_keyboard([], mode)
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text='<tg-emoji emoji-id="6066485535726118367">⬇️</tg-emoji> <b>TAP PAIRS FROM GRID TO SELECT / UNSELECT:</b>', reply_markup=keyboard, parse_mode='HTML')
        return

    if state == 'FUTURE_GRID_SELECTING' and call.data.startswith('toggle_'):
        pair = call.data.replace('toggle_', '')
        mode = user_data[chat_id]['market_mode']
        current_selections = user_data[chat_id].get('selected_pairs', [])
        
        if pair in current_selections: current_selections.remove(pair)
        else: current_selections.append(pair)
            
        user_data[chat_id]['selected_pairs'] = current_selections
        keyboard = make_pair_selection_keyboard(current_selections, mode)
        
        pairs_formatted = ", ".join(current_selections) if current_selections else "None"
        display_text = f'<tg-emoji emoji-id="6066485535726118367">⬇️</tg-emoji> <b>TAP PAIRS FROM GRID TO SELECT / UNSELECT:</b>\n\n<tg-emoji emoji-id="6311890389242487133">✅</tg-emoji> <b>Selected:</b> <code>{pairs_formatted}</code>'
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=display_text, reply_markup=keyboard, parse_mode='HTML')
        return

    if state == 'FUTURE_GRID_SELECTING' and call.data == 'pair_selection_done':
        valid_markets = user_data[chat_id].get('selected_pairs', [])
        if not valid_markets:
            bot.answer_callback_query(call.id, text="⚠️ Please select at least ONE pair before continuing!", show_alert=True)
            return
            
        market_mode = user_data[chat_id]['market_mode']
        if market_mode != "BLACKOUT":
            user_data[chat_id]['state'] = 'FUTURE_DIR_SELECT'
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                types.InlineKeyboardButton('🟢 CALL', callback_data='f_d_1'),
                types.InlineKeyboardButton('🔴 PUT', callback_data='f_d_2'),
                types.InlineKeyboardButton('🔵 BOTH', callback_data='f_d_3'),
                types.InlineKeyboardButton('🏠 HOME', callback_data='go_home')
            )
            bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text='<tg-emoji emoji-id="6212777095400006386">💱</tg-emoji> <b>SELECT DIRECTION :</b>', reply_markup=markup, parse_mode='HTML')
        else:
            user_data[chat_id]['action_choice'] = "3"
            user_data[chat_id]['state'] = 'FUTURE_START_TIME'
            bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text='<tg-emoji emoji-id="5321022677933120114">⏰</tg-emoji> <b>Enter Start Time (Format HH:MM, e.g. 10:30):</b>', parse_mode='HTML')
        return

    if state == 'FUTURE_DIR_SELECT' and call.data.startswith('f_d_'):
        choice = call.data.replace('f_d_', '')
        user_data[chat_id]['action_choice'] = choice
        user_data[chat_id]['state'] = 'FUTURE_START_TIME'
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text='<tg-emoji emoji-id="5321022677933120114">⏰</tg-emoji> <b>Enter Start Time (Format HH:MM, e.g. 10:30):</b>', parse_mode='HTML')
        return

    if state == 'FUTURE_DAYS_SELECT' and call.data.startswith('f_day_'):
        filter_days = int(call.data.replace('f_day_', ''))
        execute_future_generation(chat_id, call.message.message_id, filter_days)
        return

# --- Text Handlers Module ---
@bot.message_handler(func=lambda m: True)
def global_text_handler(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        user_data[chat_id] = {'raw_signals': [], 'selected_pairs': []}
    state = user_data[chat_id].get('state')
    text = message.text.strip()

    if state == 'COLLECTING_BACKTEST':
        if text == '/done':
            if not user_data[chat_id].get('raw_signals'):
                bot.send_message(chat_id, '⚠️ <b>No signals received yet.</b>', parse_mode='HTML')
                return
            user_data[chat_id]['state'] = 'DAYS_SELECT_BACKTEST'
            markup = types.InlineKeyboardMarkup(row_width=3)
            markup.add(*[types.InlineKeyboardButton(f"🗓 Day {i}", callback_data=f'b_day_{i}') for i in range(1, 8)])
            markup.add(types.InlineKeyboardButton("🏠 HOME", callback_data="go_home"))
            bot.send_message(chat_id, '<b><tg-emoji emoji-id="6066652700148243688">😀</tg-emoji> Select Backtest Strategy (Day 1 to 7):</b>', reply_markup=markup, parse_mode='HTML')
            return
        new_signals = parse_raw_signals(text)
        user_data[chat_id]['raw_signals'].extend(new_signals)
        bot.send_message(chat_id, f'<tg-emoji emoji-id="6312039841219485770">🏆</tg-emoji> <b>Added {len(new_signals)} Backtest Signal Send /done.</b>', parse_mode='HTML')
        return

    if state == 'COLLECTING_AI_FILTER':
        if text == '/done':
            if not user_data[chat_id].get('raw_signals'):
                bot.send_message(chat_id, '⚠️ <b>No signals received yet.</b>', parse_mode='HTML')
                return
            user_data[chat_id]['state'] = 'DAYS_SELECT_AI_FILTER'
            markup = types.InlineKeyboardMarkup(row_width=3)
            markup.add(*[types.InlineKeyboardButton(f"🗓 Day {i}", callback_data=f'ai_day_{i}') for i in range(1, 8)])
            markup.add(types.InlineKeyboardButton("🏠 HOME", callback_data="go_home"))
            bot.send_message(chat_id, '<tg-emoji emoji-id="6303015509340201177">👑</tg-emoji> <b>Select AI Filter Strategy (Day 1 to 7):</b>\n\n<i><tg-emoji emoji-id="6132037293692691226">🎇</tg-emoji> Day 1-3: Auto Clean Cut Algorithm</i>\n<i><tg-emoji emoji-id="6132037293692691226">🎇</tg-emoji> Day 4-7: Trim & Custom Time Gap Sync</i>', reply_markup=markup, parse_mode='HTML')
            return
        new_signals = parse_raw_signals(text)
        user_data[chat_id]['raw_signals'].extend(new_signals)
        bot.send_message(chat_id, f'<tg-emoji emoji-id="6302799249146911743">📊</tg-emoji> <b>Added {len(new_signals)} to AI Filter Send /done to process.</b>', parse_mode='HTML')
        return

    if state == 'FUTURE_START_TIME':
        if not re.match(r'^\d{2}:\d{2}$', text):
            bot.send_message(chat_id, "⚠️ <b>Invalid format! Please enter start time in HH:MM format (e.g. 10:30):</b>", parse_mode='HTML')
            return
        user_data[chat_id]['start_time'] = text
        user_data[chat_id]['state'] = 'FUTURE_END_TIME'
        bot.send_message(chat_id, "<tg-emoji emoji-id='6323361327767099558'>⭐</tg-emoji> <b>Enter End Time (Format HH:MM, e.g. 18:45):</b>", parse_mode='HTML')
        return

    if state == 'FUTURE_END_TIME':
        if not re.match(r'^\d{2}:\d{2}$', text):
            bot.send_message(chat_id, "⚠️ <b>Invalid format! Please enter end time in HH:MM format (e.g. 18:45):</b>", parse_mode='HTML')
            return
        user_data[chat_id]['end_time'] = text
        user_data[chat_id]['state'] = 'FUTURE_DAYS_SELECT'
        
        markup = types.InlineKeyboardMarkup(row_width=3)
        buttons = [types.InlineKeyboardButton(f"🎇 {d} Days", callback_data=f"f_day_{d}") for d in range(1, 16)]
        markup.add(*buttons)
        markup.add(types.InlineKeyboardButton("🏠 HOME", callback_data="go_home"))
        
        info_msg = '<tg-emoji emoji-id="6172731696505427144">💯</tg-emoji> <b>FUTURE DAYS FILTER</b>\n\n<i>Select Day Analyses tap below:</i>'
        bot.send_message(chat_id, info_msg, reply_markup=markup, parse_mode='HTML')
        return

# --- Future Engine Processing Execution ---
def execute_future_generation(chat_id, message_id, filter_days):
    data = user_data.get(chat_id)
    if not data: return
        
    market_mode = data['market_mode']
    valid_markets = data['selected_pairs']
    action_choice = data['action_choice']
    start_time = data['start_time']
    end_time = data['end_time']
    
    bot.edit_message_text(chat_id=chat_id, message_id=message_id, text='<pre>ZEBRONIX RUNNING WAIT <tg-emoji emoji-id="6174917297988179811">⌛</tg-emoji>...</pre>', parse_mode='HTML')
    all_signals = generate_future_signals(valid_markets, start_time, end_time, market_mode, filter_days)
    
    filtered = []
    for sig in all_signals:
        direction = sig.get('direction', '').upper()
        if market_mode == "BLACKOUT": filtered.append(sig)
        else:
            if (action_choice == "1" and direction == "CALL") or (action_choice == "2" and direction == "PUT") or (action_choice == "3"):
                filtered.append(sig)
                
    filtered.sort(key=lambda s: datetime.strptime(s['time'], "%H:%M") if s.get('time') else datetime.min)
    
    output_text = "<b>╔═══════════════╗\n<tg-emoji emoji-id='6174544597906102118'>👑</tg-emoji>ZEBRONIX GENERATED SIGNAL<tg-emoji emoji-id='6323361327767099558'>⭐</tg-emoji>\n╚═══════════════╝</b>\n\n"
    output_text += f'<b><tg-emoji emoji-id="6213083249258799034">♦️</tg-emoji> Mode: {market_mode}\n<tg-emoji emoji-id="6303076304602274890">🗓</tg-emoji> Days Analyser: {filter_days} Days\n<tg-emoji emoji-id="6174514743588426961">🔒</tg-emoji> Time Window: {start_time} - {end_time}</b>\n<b>───────────────────</b>\n'
    
    call_count, put_count = 0, 0
    if not filtered: output_text += "<code>No setups match current algorithm parameters.</code>\n"
    else:
        output_text += "<code>"
        for sig in filtered:
            time_normal = sig.get('time', '')
            asset = sig.get('asset', '').strip().replace("-OTC", "_OTC").replace('<', '&lt;').replace('>', '&gt;')
            direction = sig.get('direction', '').upper()
            if market_mode == "BLACKOUT": output_text += f"M1;{asset};{time_normal}\n"
            else:
                output_text += f"M1;{asset};{time_normal};{direction}\n"
                if direction == "CALL": call_count += 1
                else: put_count += 1
        output_text += "</code>"
                
    output_text += "<b>───────────────────</b>\n"
    if market_mode == "BLACKOUT":
        output_text += f'<b><tg-emoji emoji-id="6132052287423522342">💎</tg-emoji>Total: {len(filtered)}</b>\n\n<b>সিগনাল টাইমের আগের কেন্ডেল যে দিকে যাবে তার বিপরিতে এন্ট্রি নিবেন যেমন:</b>\n<b><tg-emoji emoji-id="6210635890994192211">🔗</tg-emoji> 00:54 এর আগের কেন্ডেল যদি গ্রিন হয় তাহলে Down নিবেন।</b>\n<b><tg-emoji emoji-id="6210635890994192211">🔗</tg-emoji> 00:54 এর আগের কেন্ডেল যদি রেড হয় তাহলে Up নিবেন।</b>\n\n'
    else:
        output_text += f'<b><tg-emoji emoji-id="6132052287423522342">💎</tg-emoji>Total: {str(len(filtered)).zfill(2)} | <tg-emoji emoji-id="6311874557993033039">🔼</tg-emoji> CALL: {str(call_count).zfill(2)} | <tg-emoji emoji-id="6312244088389247483">🔽</tg-emoji>PUT: {str(put_count).zfill(2)}</b>\n\n'
        
    output_text += f'<b><tg-emoji emoji-id="6075388783887392362">🚀</tg-emoji> Channel: {CHANNEL_USERNAME}\n<tg-emoji emoji-id="6312351947902952139">🚀</tg-emoji> Owner   : {OWNER_USERNAME}\n<tg-emoji emoji-id="6300679098670784062">⚙️</tg-emoji> Admin  : {ADMIN_USERNAME}\n<tg-emoji emoji-id="6300963760513228226">🥳</tg-emoji> Powered By: {POWERED_BY}</b>'
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🏠 MAIN DASHBOARD", callback_data="go_home"))
    bot.send_message(chat_id, output_text, reply_markup=markup, parse_mode="HTML", disable_web_page_preview=True)

# --- Broadcast Feature ---
@bot.message_handler(commands=['broadcast'])
def broadcast_handler(message):
    if message.from_user.id == ADMIN_ID:
        msg_text = message.text.replace('/broadcast ', '').strip()
        if not msg_text: return
        user_list = get_all_users()
        success, failed = 0, 0
        for user_id in user_list:
            try:
                bot.send_message(int(user_id), msg_text, parse_mode='HTML')
                success += 1
            except: failed += 1
        bot.send_message(message.chat.id, f"<b>Report:</b>\n✅ Sent: {success}\n❌ Failed: {failed}", parse_mode='HTML')

if __name__ == '__main__':
    threading.Thread(target=run_web_server, daemon=True).start()
    bot.infinity_polling(skip_pending=True)
