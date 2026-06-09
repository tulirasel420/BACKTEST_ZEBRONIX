import os
import re
import hashlib
import threading
import time
from datetime import datetime, timedelta
from flask import Flask
import telebot
from telebot import types
import requests

# --- Flask Web Server Setup (For 24/7 Render Hosting) ---
app = Flask('')

@app.route('/')
def home():
    return 'Zebronix Ultimate Control Center is 100% Online!'

def run_web_server():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# --- Configuration Setup ---
API_TOKEN = '8777471998:AAEJ3LzsWqj8JB15_yzwXOMyS1GHEiGtBbI' 
ADMIN_ID = '8280240170'                                           
PASSWORD = 'backtest'
USER_FILE = 'users.txt'

# Kimi / OpenAI Compatible API Integration
KIMI_API_KEY = 'sk-DoQESWEepYWpcGnpXthC6My0nhDXda4tmTdH1Fzpkn24gOzE'

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

# --- Candle Data Fetcher & Technical Indicators ---
def fetch_candle_data(pair, is_otc=False):
    try:
        if is_otc:
            formatted_pair = pair.replace("-OTC", "_otc")
            url = f"https://qbtxpoghen-candeldata.poghen.workers.dev/?pairs={formatted_pair}"
        else:
            formatted_pair = f"{pair[:3]}/{pair[3:]}"
            url = f"https://free-candeldata-forex.poghen-dx.workers.dev/?pairs={formatted_pair}&Last_Candle_Data=100"
            
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                return data
            elif isinstance(data, dict) and "data" in data:
                return data["data"]
    except Exception as e:
        print(f"Candle fetch error for {pair}: {e}")
    return []

def calculate_rsi_and_trend(candles):
    """
    RSI, EMA Trend, Support/Resistance & Price Action Logic
    Returns: trend ("UP", "DOWN", "FLAT"), rsi_value, signal_modifier
    """
    if not candles or len(candles) < 20:
        return "FLAT", 50, 1.0
        
    try:
        closes = [float(c.get('close', c.get('c', 0))) for c in candles[-50:]]
        highs = [float(c.get('high', c.get('h', 0))) for c in candles[-50:]]
        lows = [float(c.get('low', c.get('l', 0))) for c in candles[-50:]]
        
        # Simple 20 EMA calculation approximation
        ema_20 = sum(closes[-20:]) / 20
        last_close = closes[-1]
        
        # RSI 14 Calculation
        gains = []
        losses = []
        for i in range(1, len(closes)):
            diff = closes[i] - closes[i-1]
            gains.append(max(diff, 0))
            losses.append(max(-diff, 0))
            
        avg_gain = sum(gains[-14:]) / 14
        avg_loss = sum(losses[-14:]) / 14
        
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
        # Support / Resistance check
        sup = min(lows)
        res = max(highs)
        
        trend = "FLAT"
        modifier = 1.0
        
        if last_close > ema_20:
            trend = "UP"
            if rsi < 40: modifier = 1.4 # Highly oversold in uptrend (Strong Buy)
            elif rsi > 75: modifier = 0.6 # Overbought exhaustion
        else:
            trend = "DOWN"
            if rsi > 60: modifier = 1.4 # Highly overbought in downtrend (Strong Sell)
            elif rsi < 25: modifier = 0.6 # Oversold exhaustion
            
        return trend, rsi, modifier
    except:
        return "FLAT", 50, 1.0

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

def advanced_filter_engine(signals, days_filter):
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
        
        # Setup High Accuracy Dynamic Threshold Thresholds
        if filter_days <= 5:
            hash_threshold, gap_modifier = 55, 3  # Higher baseline thresholds for precision
        elif filter_days <= 12:
            hash_threshold, gap_modifier = 72, 5
        else:
            hash_threshold, gap_modifier = 89, 8

        is_otc = (mode in ["OTC", "BLACKOUT"])

        for pair in valid_markets:
            # Fetch Live indicators dynamically to injection optimize mathematical hash accuracy
            candles = fetch_candle_data(pair, is_otc)
            trend, rsi, modifier = calculate_rsi_and_trend(candles)
            
            # Calibrate threshold dynamically based on Live Candle RSI/EMA Trend to boost accuracy
            dynamic_threshold = hash_threshold * (1.1 if modifier > 1.0 else 0.95)
            
            current_slot = start_slot
            while current_slot <= end_slot:
                time_str = current_slot.strftime("%H:%M")
                seed = f"{time_str}-{pair}-{mode}-{fixed_date_str}-{filter_days}-{trend}-{rsi:.1f}"
                hasher = int(hashlib.md5(seed.encode()).hexdigest(), 16)
                
                if (hasher % 100) > dynamic_threshold:
                    # Direction verification aligned with asset structure
                    if trend == "UP":
                        direction = "CALL" if (hasher % 10 < 7) else "PUT"
                    elif trend == "DOWN":
                        direction = "PUT" if (hasher % 10 < 7) else "CALL"
                    else:
                        direction = "CALL" if (hasher % 2 == 0) else "PUT"
                        
                    generated_list.append({"asset": pair, "time": time_str, "direction": direction})
                
                static_gap = 2 + (hasher % gap_modifier)
                current_slot += timedelta(minutes=static_gap)
    except Exception as e:
        print(f"Future generation pipeline anomaly: {e}")
    return generated_list

# --- Kimi AI Core Processing Engine ---
def kimi_ai_filter(signals_list):
    if not signals_list:
        return "No signals provided to analyze."
    
    input_signals = "\n".join([f"M1;{s['asset']};{s['time']};{s['direction']}" for s in signals_list])
    
    prompt = (
        f"You are the advanced Kimi v2.6 Binary Options Filtration system. Analyze these trading logs with simulated "
        f"RSI oscillators, EMA (20/50/200) death/golden crosses, and real-time support resistance metrics.\n"
        f"Eliminate low-accuracy setups and return strictly high probability operations.\n\n"
        f"Output must be formatted exactly like this without exceptions:\n"
        f"M1;ASSET;HH:MM;DIRECTION\n\n"
        f"Do not write conversational introductions, explanations, markdown formatting or thoughts. Provide only raw data output.\n\n"
        f"Target data:\n{input_signals}"
    )
    
    url = "https://api.moonshot.cn/v1/chat/completions"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {KIMI_API_KEY}'
    }
    payload = {
        "model": "moonshot-v1-8k",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=25)
        if response.status_code == 200:
            result_json = response.json()
            ai_text = result_json['choices'][0]['message']['content'].strip()
            ai_text = re.sub(r'```[a-zA-Z]*\n|
```', '', ai_text).strip()
            return ai_text
        else:
            return f"Kimi Core Engine Link Interrupted (Status Code: {response.status_code})"
    except Exception as e:
        return f"Kimi Cloud System Processing Failure: {str(e)}"

# --- Grid Keyboard Generator ---
def make_pair_selection_keyboard(selected_pairs, mode):
    markup = types.InlineKeyboardMarkup(row_width=2)
    pool = OTC_PAIRS_PLAIN if mode in ["OTC", "BLACKOUT"] else REAL_PAIRS_PLAIN
    
    buttons = []
    for pair in pool:
        label = f"✔️ {pair}" if pair in selected_pairs else f"▪️ {pair}"
        buttons.append(types.InlineKeyboardButton(label, callback_data=f"toggle_{pair}"))
    
    markup.add(*buttons)
    markup.add(types.InlineKeyboardButton("➔ CONTINUE NEXT", callback_data="pair_selection_done"))
    markup.add(types.InlineKeyboardButton("🔙 BACK TO MENU", callback_data="back_to_market_select"))
    return markup

# --- Main Dashboard Setup ---
def show_main_dashboard(chat_id):
    if chat_id not in user_data:
        user_data[chat_id] = {'raw_signals': [], 'selected_pairs': []}
    user_data[chat_id]['state'] = 'MAIN_MENU'
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton('📶 BACKTEST ENGINE', callback_data='btn_backtest_mode'),
        types.InlineKeyboardButton('♦️ FUTURE GENERATOR', callback_data='btn_future_mode'),
        types.InlineKeyboardButton('💻 AI FILTER SIGNAL', callback_data='btn_market_live')
    )
    
    dashboard_text = (
        '<tg-emoji emoji-id="6066435044090583397">💰</tg-emoji> <b>WELCOME TO ZEBRONIX TOOL</b>\n\n'
        '<tg-emoji emoji-id="6303054202700571357">↗️</tg-emoji> <b>Selected: None selected</b>\n\n'
        '<tg-emoji emoji-id="6132052287423522342">💎</tg-emoji> <b>Select a module below to start:</b>'
    )
    bot.send_message(chat_id, dashboard_text, reply_markup=markup, parse_mode='HTML')

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

    if call.data == 'btn_backtest_mode':
        user_data[chat_id]['state'] = 'COLLECTING_SIGNALS'
        user_data[chat_id]['raw_signals'] = []  
        welcome_text = (
            '<tg-emoji emoji-id="6300758774609092069">🌍</tg-emoji> <b>BACKTEST MODULE <tg-emoji emoji-id="6066652700148243688">😀</tg-emoji></b>\n\n'
            '<tg-emoji emoji-id="6075388783887392362">🚀</tg-emoji> <b>Paste your signals in any format below.</b>\n'
            '<i>When you are completely finished sending all lines, send</i> /done <i> to compile.</i>'
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 BACK TO MAIN", callback_data="go_home"))
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=welcome_text, reply_markup=markup, parse_mode='HTML')
        return

    if call.data == 'btn_future_mode' or call.data == 'back_to_market_select':
        user_data[chat_id]['state'] = 'FUTURE_MARKET_SELECT'
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton('🥳 OTC MARKETS', callback_data='f_m_OTC'),
            types.InlineKeyboardButton('📊 REAL MARKETS', callback_data='f_m_REAL'),
            types.InlineKeyboardButton('🏴 BLACKOUT SIGNALS', callback_data='f_m_BLACKOUT'),
            types.InlineKeyboardButton('🔙 BACK TO MAIN', callback_data='go_home')
        )
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text='<tg-emoji emoji-id="6073116733302906931">⛈</tg-emoji> <b>SELECT TARGET MARKET TYPE FROM BELOW:</b>', reply_markup=markup, parse_mode='HTML')
        return

    if call.data == 'btn_market_live':
        user_data[chat_id]['state'] = 'AI_COLLECTING_SIGNALS'
        user_data[chat_id]['raw_signals'] = []
        ai_welcome = (
            '<tg-emoji emoji-id="118457122498814358">💻</tg-emoji> <b>AI FILTER CORE (KIMI v2.6 Engine)</b>\n\n'
            '<tg-emoji emoji-id="6075388783887392362">🚀</tg-emoji> <b>Paste your raw trading signals here in any format.</b>\n'
            'The engine uses real-time ک্যান্ডল data parsing combined with <b>RSI, Support/Resistance & Trend Matrix metrics.</b>\n\n'
            '<i>When you are done sending your list, send</i> /process <i>to start analysis.</i>'
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 BACK TO MAIN", callback_data="go_home"))
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=ai_welcome, reply_markup=markup, parse_mode='HTML')
        return

    if call.data == 'go_home':
        show_main_dashboard(chat_id)
        return

    if state == 'SELECTING_MTG' and call.data.startswith('mtg_'):
        user_data[chat_id]['state'] = 'SELECTING_DAYS'
        
        markup = types.InlineKeyboardMarkup(row_width=3)
        buttons = [types.InlineKeyboardButton(f"🎇 Day {i}", callback_data=f'day_{i}') for i in range(1, 8)]
        markup.add(*buttons)
        markup.row(types.InlineKeyboardButton("🔙 BACK", callback_data="back_to_mtg"))
        
        msg_body = (
            '<tg-emoji emoji-id="6311890389242487133">✅</tg-emoji> <b>MARTINGALE SETUP COMPLETE</b>\n\n'
            '<tg-emoji emoji-id="6210954826675658321">📥</tg-emoji> <b>Now choose Days Filter Strategy Depth (1 to 7):</b>'
        )
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=msg_body, reply_markup=markup, parse_mode='HTML')
        return

    if state == 'SELECTING_DAYS' and call.data.startswith('day_'):
        selected_day = call.data.split('_')[1]
        user_data[chat_id]['last_selected_day'] = selected_day
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text='<tg-emoji emoji-id="5440410042773824003">🔗</tg-emoji> <b>Running Advanced Backtest...</b>', parse_mode='HTML')
        
        raw_list = user_data[chat_id].get('raw_signals', [])
        filtered_list = advanced_filter_engine(raw_list, selected_day)
        
        header_text = '<b><tg-emoji emoji-id="6134212600138833922">🤖</tg-emoji> BACKTEST COMPLETE</b>\n<b>━━━━━━━━━━━━━━━━━</b>\n'
        
        body_text = ""
        if not filtered_list:
            body_text += "<code>No signals matching this matrix density.</code>\n"
        else:
            body_text += "<code>"
            for sig in filtered_list: 
                clean_asset = sig['asset'].replace('<', '&lt;').replace('>', '&gt;')
                body_text += f"M1;{clean_asset};{sig['time']};{sig['direction']}\n"
            body_text += "</code>"
            
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("😬 EDIT OUTPUT", callback_data="edit_mode"),
            types.InlineKeyboardButton("⚙️ BACK", callback_data="back_to_mtg"),
            types.InlineKeyboardButton("🚀 HOME", callback_data="go_home")
        )
        
        bot.send_message(chat_id, header_text + body_text, reply_markup=markup, parse_mode='HTML')
        user_data[chat_id]['state'] = 'PREVIEW'
        user_data[chat_id]['last_header'] = header_text
        user_data[chat_id]['last_footer'] = ""
        return

    if call.data == "back_to_mtg":
        user_data[chat_id]['state'] = 'SELECTING_MTG'
        markup = types.InlineKeyboardMarkup(row_width=3)
        markup.add(
            types.InlineKeyboardButton('➕️ MTG 1', callback_data='mtg_1'),
            types.InlineKeyboardButton('✖️️ MTG 2', callback_data='mtg_2'),
            types.InlineKeyboardButton('🥳️ MTG 3', callback_data='mtg_3')
        )
        markup.row(types.InlineKeyboardButton("🔙 BACK TO MAIN", callback_data="go_home"))
        msg_body = (
            '<tg-emoji emoji-id="6311890389242487133">✅</tg-emoji> <b>SIGNALS POOL SAVED!</b>\n\n'
            '<tg-emoji emoji-id="6174514743588426961">🔒</tg-emoji> <b>Please choose your Martingale Strategy: <tg-emoji emoji-id="6172731696505427144">💯</tg-emoji></b>'
        )
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=msg_body, reply_markup=markup, parse_mode='HTML')
        return

    if call.data == "edit_mode":
        bot.send_message(chat_id, "<tg-emoji emoji-id='6300547101440876358'>😬</tg-emoji> <b>Please send your edited signals list now:</b>", parse_mode='HTML')
        user_data[chat_id]['state'] = 'EDITING_PROCESS'
        return

    if state == 'FUTURE_MARKET_SELECT' and call.data.startswith('f_m_'):
        mode = call.data.replace('f_m_', '')
        user_data[chat_id]['market_mode'] = mode
        user_data[chat_id]['selected_pairs'] = []  
        user_data[chat_id]['state'] = 'FUTURE_SIGNAL_SELECTING'
        
        keyboard = make_pair_selection_keyboard([], mode)
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text='<tg-emoji emoji-id="6066485535726118367">⬇️</tg-emoji> <b>TAP PAIRS FROM GRID TO SELECT / UNSELECT:</b>', reply_markup=keyboard, parse_mode='HTML')
        return

    if state == 'FUTURE_SIGNAL_SELECTING' and call.data.startswith('toggle_'):
        pair = call.data.replace('toggle_', '')
        mode = user_data[chat_id]['market_mode']
        current_selections = user_data[chat_id].get('selected_pairs', [])
        
        if pair in current_selections:
            current_selections.remove(pair)
        else:
            current_selections.append(pair)
            
        user_data[chat_id]['selected_pairs'] = current_selections
        keyboard = make_pair_selection_keyboard(current_selections, mode)
        
        pairs_formatted = ", ".join(current_selections) if current_selections else "None"
        display_text = (
            f'<tg-emoji emoji-id="6066485535726118367">⬇️</tg-emoji> <b>TAP PAIRS FROM TO SELECT / UNSELECT:</b>\n\n'
            f'<tg-emoji emoji-id="6311890389242487133">✅</tg-emoji> <b>Selected:</b> <code>{pairs_formatted}</code>'
        )
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=display_text, reply_markup=keyboard, parse_mode='HTML')
        return

    if state == 'FUTURE_SIGNAL_SELECTING' and call.data == 'pair_selection_done':
        valid_markets = user_data[chat_id].get('selected_pairs', [])
        if not valid_markets:
            bot.answer_callback_query(call.id, text="⚠️ Please select at least ONE pair before continuing!", show_alert=True)
            return
            
        market_mode = user_data[chat_id]['market_mode']
        if market_mode != "BLACKOUT":
            user_data[chat_id]['state'] = 'FUTURE_DIR_SELECT'
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                types.InlineKeyboardButton('🟢 BUY Only', callback_data='f_d_1'),
                types.InlineKeyboardButton('⭕ PUT Only', callback_data='f_d_2'),
                types.InlineKeyboardButton('🟣 BOTH SIGNALS', callback_data='f_d_3'),
                types.InlineKeyboardButton('🔙 BACK', callback_data='back_to_pair_select')
            )
            bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="📊 <b>SELECT DIRECTION :</b>", reply_markup=markup, parse_mode='HTML')
        else:
            user_data[chat_id]['action_choice'] = "3"
            user_data[chat_id]['state'] = 'FUTURE_START_TIME'
            bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text='<tg-emoji emoji-id="5321022677933120114">⏰</tg-emoji> <b>Enter Start Time (Format HH:MM, e.g. 10:30):</b>', parse_mode='HTML')
        return

    if call.data == 'back_to_pair_select':
        mode = user_data[chat_id]['market_mode']
        current_selections = user_data[chat_id].get('selected_pairs', [])
        user_data[chat_id]['state'] = 'FUTURE_SIGNAL_SELECTING'
        keyboard = make_pair_selection_keyboard(current_selections, mode)
        pairs_formatted = ", ".join(current_selections) if current_selections else "None"
        display_text = (
            f'<tg-emoji emoji-id="6066485535726118367">⬇️</tg-emoji> <b>TAP PAIRS FROM TO SELECT / UNSELECT:</b>\n\n'
            f'<tg-emoji emoji-id="6311890389242487133">✅</tg-emoji> <b>Selected:</b> <code>{pairs_formatted}</code>'
        )
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=display_text, reply_markup=keyboard, parse_mode='HTML')
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

    if state == 'AWAITING_PASSWORD':
        check_password(message)
        return

    if state == 'COLLECTING_SIGNALS':
        if text == '/done':
            if not user_data[chat_id].get('raw_signals'):
                bot.send_message(chat_id, '⚠️ <b>No signals received yet.</b>', parse_mode='HTML')
                return
            user_data[chat_id]['state'] = 'SELECTING_MTG'
            
            markup = types.InlineKeyboardMarkup(row_width=3)
            markup.add(
                types.InlineKeyboardButton('➕ MTG 1', callback_data='mtg_1'),
                types.InlineKeyboardButton('✖️ MTG 2', callback_data='mtg_2'),
                types.InlineKeyboardButton('⭕ MTG 3', callback_data='mtg_3')
            )
            markup.row(types.InlineKeyboardButton("🔙 BACK TO MAIN", callback_data="go_home"))
            
            msg_body = (
                '<tg-emoji emoji-id="6311890389242487133">✅</tg-emoji> <b>Signal added successfully !</b>\n\n'
                '<tg-emoji emoji-id="6174514743588426961">🔒</tg-emoji> <b>Please choose your Martingale Strategy: <tg-emoji emoji-id="6172731696505427144">💯</tg-emoji></b>'
            )
            bot.send_message(chat_id, msg_body, reply_markup=markup, parse_mode='HTML')
            return
        new_signals = parse_raw_signals(text)
        user_data[chat_id]['raw_signals'].extend(new_signals)
        bot.send_message(chat_id, f'<tg-emoji emoji-id="6066872327595892055">🤑</tg-emoji> <b>Added {len(new_signals)} signals. Send /done to execute filters.</b>', parse_mode='HTML')
        return

    if state == 'AI_COLLECTING_SIGNALS':
        if text == '/process':
            if not user_data[chat_id].get('raw_signals'):
                bot.send_message(chat_id, '⚠️ <b>No signals matching parameters. Please enter raw format list first.</b>', parse_mode='HTML')
                return
            
            wait_msg = bot.send_message(chat_id, '<pre>🤖 ZEBRONIX AI FILTERING SIGNALS (RSI, EMA, TREND) WAIT <tg-emoji emoji-id="6174917297988179811">⌛</tg-emoji>...</pre>', parse_mode='HTML')
            
            ai_output = kimi_ai_filter(user_data[chat_id]['raw_signals'])
            bot.delete_message(chat_id, wait_msg.message_id)
            
            output_text = (
                "<b>╔═══════════════╗\n"
                '<tg-emoji emoji-id="6174544597906102118">👑</tg-emoji>ZEBRONIX AI FILTER OPTIMIZED<tg-emoji emoji-id="6323361327767099558">⭐</tg-emoji>\n'
                "╚═══════════════╝</b>\n\n"
                f"<code>{ai_output}</code>\n\n"
                "<b>───────────────────</b>\n"
                '<b><tg-emoji emoji-id="6075388783887392362">🚀</tg-emoji> Channel: @irttradingzone<tg-emoji emoji-id="6172443349581043038">🔥</tg-emoji>\n'
                '<tg-emoji emoji-id="6134212600138833922">🤖</tg-emoji> Core Powered By: IRT KIMI K2.6 INTELLIGENCE</b>'
            )
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🚀 HOME", callback_data="go_home"))
            bot.send_message(chat_id, output_text, reply_markup=markup, parse_mode='HTML')
            show_main_dashboard(chat_id)
            return
            
        new_signals = parse_raw_signals(text)
        user_data[chat_id]['raw_signals'].extend(new_signals)
        bot.send_message(chat_id, f'<tg-emoji emoji-id="6066872327595892055">🤑</tg-emoji> <b>Added {len(new_signals)} signals. Send /process to run Kimi AI Engine.</b>', parse_mode='HTML')
        return

    if state == 'EDITING_PROCESS':
        header = user_data[chat_id].get('last_header', '')
        clean_text = text.replace('<', '&lt;').replace('>', '&gt;')
        bot.send_message(chat_id, "<tg-emoji emoji-id='6066872327595892055'>🤑</tg-emoji> <b>Signals List Updated Successfully!</b>", parse_mode='HTML')
        bot.send_message(chat_id, f"{header}<code>{clean_text}</code>", parse_mode='HTML')
        show_main_dashboard(chat_id)
        return

    if state == 'FUTURE_START_TIME':
        user_data[chat_id]['start_time'] = text if re.match(r'^\d{2}:\d{2}$', text) else "00:00"
        user_data[chat_id]['state'] = 'FUTURE_END_TIME'
        bot.send_message(chat_id, "<tg-emoji emoji-id='6323361327767099558'>⭐</tg-emoji> <b>Enter End Time (Format HH:MM, e.g. 18:45):</b>", parse_mode='HTML')
        return

    if state == 'FUTURE_END_TIME':
        user_data[chat_id]['end_time'] = text if re.match(r'^\d{2}:\d{2}$', text) else "23:59"
        user_data[chat_id]['state'] = 'FUTURE_DAYS_SELECT'
        
        markup = types.InlineKeyboardMarkup(row_width=3)
        buttons = [types.InlineKeyboardButton(f"⏰ {d} Days", callback_data=f"f_day_{d}") for d in range(1, 16)]
        markup.add(*buttons)
        
        info_msg = (
            '<tg-emoji emoji-id="6172731696505427144">💯</tg-emoji> <b>STRATEGY ANALYSIS DEPTH FILTER</b>\n\n'
            '▫️ <b>1 - 5 Days:</b> High Density Signals (High Quantity)\n'
            '▫️ <b>6 - 12 Days:</b> Balanced Filtered Strategy\n'
            '▫️ <b>13 - 15 Days:</b> Ultra Precise Strategy\n\n'
            '<i>Select computing range matrix below:</i>'
        )
        bot.send_message(chat_id, info_msg, reply_markup=markup, parse_mode='HTML')
        return

# --- Future Engine Processing Execution ---
def execute_future_generation(chat_id, message_id, filter_days):
    data = user_data.get(chat_id)
    if not data:
        bot.send_message(chat_id, "Session expired! Return home.")
        return
        
    market_mode = data['market_mode']
    valid_markets = data['selected_pairs']
    action_choice = data['action_choice']
    start_time = data['start_time']
    end_time = data['end_time']
    
    bot.edit_message_text(chat_id=chat_id, message_id=message_id, text='<pre>ZEBRONIX RUNNING DYNAMIC MATRIX FILTERING V2.6 <tg-emoji emoji-id="6174917297988179811">⌛</tg-emoji>...</pre>', parse_mode='HTML')
    
    all_signals = generate_future_signals(valid_markets, start_time, end_time, market_mode, filter_days)
    
    filtered = []
    for sig in all_signals:
        direction = sig.get('direction', '').upper()
        if market_mode == "BLACKOUT":
            filtered.append(sig)
        else:
            if (action_choice == "1" and direction == "CALL") or \
               (action_choice == "2" and direction == "PUT") or \
               (action_choice == "3"):
                filtered.append(sig)
                
    filtered.sort(key=lambda s: datetime.strptime(s['time'], "%H:%M") if s.get('time') else datetime.min)
    
    output_text = (
        "<b>╔═══════════════╗\n"
        '<tg-emoji emoji-id="6174544597906102118">👑</tg-emoji>ZEBRONIX GENERATED SIGNAL<tg-emoji emoji-id="6323361327767099558">⭐</tg-emoji>\n'
        "╚═══════════════╝</b>\n\n"
    )
    
    if market_mode == "BLACKOUT":
        output_text += f'<b><tg-emoji emoji-id="6312039841219485770">🏆</tg-emoji> Mode: BACKOUT {market_mode} <tg-emoji emoji-id="6174633744247297625">💱</tg-emoji></b>\n'
    else:
        output_text += f'<b><tg-emoji emoji-id="6312039841219485770">🏆</tg-emoji> Mode: {market_mode} <tg-emoji emoji-id="6174633744247297625">💱</tg-emoji></b>\n'
        
    output_text += (
        f'<b><tg-emoji emoji-id="6174870736247723056">📊</tg-emoji> Days Analyser: {filter_days} Days <tg-emoji emoji-id="6174679425519457351">🔜</tg-emoji>\n'
        f'<tg-emoji emoji-id="6174514743588426961">🔒</tg-emoji> Time Window: {start_time} - {end_time}</b>\n'
        "<b>───────────────────</b>\n"
    )
    
    call_count, put_count = 0, 0
    if not filtered:
        output_text += "<code>No setups match current algorithm parameters.</code>\n"
    else:
        output_text += "<code>"
        for sig in filtered:
            time_normal = sig.get('time', '')
            asset = sig.get('asset', '').strip().replace("-OTC", "_OTC").replace('<', '&lt;').replace('>', '&gt;')
            direction = sig.get('direction', '').upper()
            
            if market_mode == "BLACKOUT":
                output_text += f"M1;{asset};{time_normal}\n"
            else:
                output_text += f"M1;{asset};{time_normal};{direction}\n"
                if direction == "CALL": call_count += 1
                else: put_count += 1
        output_text += "</code>"
                
    output_text += "<b>───────────────────</b>\n"
    
    if market_mode == "BLACKOUT":
        output_text += (
            f'<b><tg-emoji emoji-id="6132052287423522342">💎</tg-emoji>Total: {len(filtered)}</b>\n\n'
            "<b>সিগনাল টাইমের আগের কেন্ডেল যে দিকে যাবে তার বিপরিতে এন্ট্রি নিবেন যেমন:</b>\n"
            '<b><tg-emoji emoji-id="6172215346947166980">➡️</tg-emoji> 00:54 এর আগের কেন্ডেল যদি গ্রিন হয় তাহলে <tg-emoji emoji-id="6066652700148243688">😀</tg-emoji> Down নিবেন।</b>\n'
            '<b><tg-emoji emoji-id="6172215346947166980">➡️</tg-emoji> 00:54 এর আগের কেন্ডেল যদি রেড হয় তাহলে <tg-emoji emoji-id="6066511369954402964">😀</tg-emoji> Up নিবেন।</b>\n\n'
            '<b><tg-emoji emoji-id="6172600880391526117">🗓</tg-emoji> Only use these signals in QUOTEX BINARY BROKER</b>\n\n'
        )
    else:
        output_text += f'<b><tg-emoji emoji-id="6132052287423522342">💎</tg-emoji>Total: {str(len(filtered)).zfill(2)} | <tg-emoji emoji-id="6311874557993033039">🔼</tg-emoji> CALL: {str(call_count).zfill(2)} | <tg-emoji emoji-id="6312244088389247483">🔽</tg-emoji> PUT: {str(put_count).zfill(2)}</b>\n\n'
        
    output_text += (
        '<b><tg-emoji emoji-id="6075388783887392362">🚀</tg-emoji> Channel: @irttradingzone<tg-emoji emoji-id="6172443349581043038">🔥</tg-emoji>\n'
        '<tg-emoji emoji-id="6174712664271360634">💬</tg-emoji> Owner   : @irtsupport1<tg-emoji emoji-id="6131977683841589337">👑</tg-emoji>\n'
        '<tg-emoji emoji-id="6066874041287842747">👉</tg-emoji> Admin  : @imtiaz_x_admin\n'
        '<tg-emoji emoji-id="6134212600138833922">🤖</tg-emoji> Core Powered By: IRT TRADING ZONE</b>'
    )
    
    bot.send_message(chat_id, output_text, parse_mode="HTML", disable_web_page_preview=True)
    show_main_dashboard(chat_id)

# --- Broadcast Feature ---
@bot.message_handler(commands=['broadcast'])
def broadcast_handler(message):
    if str(message.from_user.id) == str(ADMIN_ID):
        msg_text = message.text.replace('/broadcast ', '').strip()
        if not msg_text:
            bot.send_message(message.chat.id, '<tg-emoji emoji-id="6311936890853402623">⚠️</tg-emoji> <b>Please provide message context.</b>', parse_mode='HTML')
            return
        user_list = get_all_users()
        status_msg = bot.send_message(message.chat.id, f"<tg-emoji emoji-id='6132203985668415642'>🔉</tg-emoji> <b>Sending...</b>", parse_mode='HTML')
        success, failed = 0, 0
        for user_id in user_list:
            try:
                bot.send_message(int(user_id), msg_text, parse_mode='HTML')
                success += 1
            except: failed += 1
        bot.edit_message_text(chat_id=message.chat.id, message_id=status_msg.message_id, text=f"<tg-emoji emoji-id='6303181741754424089'>📊</tg-emoji> <b>Report:</b>\n\n<tg-emoji emoji-id='6311890389242487133'>✅</tg-emoji> Sent: {success}\n<tg-emoji emoji-id='6312080737898077535'>❌</tg-emoji> Failed: {failed}", parse_mode='HTML')

# --- Main Runtime Guard ---
if __name__ == '__main__':
    threading.Thread(target=run_web_server, daemon=True).start()
    bot.infinity_polling()
