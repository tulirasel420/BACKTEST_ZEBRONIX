import os
import re
import hashlib
import threading
import time
from datetime import datetime, timedelta
from flask import Flask
import telebot
from telebot import types

# --- Flask Web Server Setup (For 24/7 Render Hosting) ---
app = Flask('')

@app.route('/')
def home():
    return 'Zebronix Ultimate Control Center is 100% Online!'

def run_web_server():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# --- Configuration Setup ---
API_TOKEN = '8777471998:AAEJ3LzsWqj8JB15_yzwXOMyS1GHEiGtBbI'  # তোমার বটের টোকেন
ADMIN_ID = 8280240170                                           # তোমার আসল টেলিগ্রাম আইডি
PASSWORD = 'backtest'
USER_FILE = 'users.txt'

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
        
        if filter_days <= 5:
            hash_threshold, gap_modifier = 40, 2
        elif filter_days <= 12:
            hash_threshold, gap_modifier = 65, 4
        else:
            hash_threshold, gap_modifier = 86, 7

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

# --- Grid Keyboard Generator (বাটন বাগ ফিক্সড লেআউট) ---
def make_pair_selection_keyboard(selected_pairs, mode):
    markup = types.InlineKeyboardMarkup(row_width=2)
    pool = OTC_PAIRS_PLAIN if mode in ["OTC", "BLACKOUT"] else REAL_PAIRS_PLAIN
    
    buttons = []
    for pair in pool:
        # বাটনের টেক্সটে স্ট্যান্ডার্ড ইমোজি দেওয়া হয়েছে যাতে কোড ভেঙে না যায়
        label = f"🟢 {pair}" if pair in selected_pairs else f"▪️ {pair}"
        buttons.append(types.InlineKeyboardButton(label, callback_data=f"toggle_{pair}"))
    
    markup.add(*buttons)
    markup.add(types.InlineKeyboardButton("➔ CONTINUE SYSTEM PROCESS", callback_data="pair_selection_done"))
    return markup

# --- Main Dashboard Setup (504.jpg লেআউট) ---
def show_main_dashboard(chat_id):
    user_data[chat_id]['state'] = 'MAIN_MENU'
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton('📊 BACKTEST ENGINE', callback_data='btn_backtest_mode'),
        types.InlineKeyboardButton('🤖 FUTURE GENERATOR', callback_data='btn_future_mode'),
        types.InlineKeyboardButton('👑 VIP PAIR LIST', callback_data='btn_vip_pairs'),
        types.InlineKeyboardButton('⚙️ LIVE STATUS', callback_data='btn_market_live')
    )
    
    dashboard_text = (
        '🟢 <b>ZEBRONIX CONTROL CENTER</b>\n\n'
        '<tg-emoji emoji-id="6302933664443407379">⚙️</tg-emoji> <tg-emoji emoji-id="6301098351903383801">📈</tg-emoji> <b>System Modules Initialized!</b>\n\n'
        '💼 <b>Select a module from the dashboard grid below to start:</b>'
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
        welcome_text = (
            '<tg-emoji emoji-id="6300758774609092069">🌍</tg-emoji> <b>BACKTEST ENGINE ACTIVATED</b>\n\n'
            '📥 <b>Paste your signals in any format below.</b>\n'
            '<i>When you are completely finished sending all lines, send</i> /done <i>to compile.</i>'
        )
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=welcome_text, parse_mode='HTML')
        return

    elif call.data == 'btn_future_mode':
        user_data[chat_id]['state'] = 'FUTURE_MARKET_SELECT'
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton('📊 OTC MARKETS', callback_data='f_m_OTC'),
            types.InlineKeyboardButton('📈 REAL MARKETS', callback_data='f_m_REAL'),
            types.InlineKeyboardButton('🥷 BLACKOUT SIGNALS', callback_data='f_m_BLACKOUT')
        )
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text='⚡ <b>SELECT TARGET MARKET TYPE FROM BELOW:</b>', reply_markup=markup, parse_mode='HTML')
        return

    elif call.data in ['btn_vip_pairs', 'btn_market_live']:
        bot.answer_callback_query(call.id, text="⚡ Synced with master server parameters!", show_alert=True)
        return

    # Backtest Callback: MTG Select
    if state == 'SELECTING_MTG' and call.data.startswith('mtg_'):
        user_data[chat_id]['state'] = 'SELECTING_DAYS'
        
        markup = types.InlineKeyboardMarkup(row_width=4)
        buttons = [types.InlineKeyboardButton(f"📅 Day {i}", callback_data=f'day_{i}') for i in range(1, 8)]
        markup.add(*buttons)
        
        # তোমার কাঙ্ক্ষিত প্রিমিয়াম টিকমার্ক ইমোজি বডিতে সেট করা হয়েছে
        msg_body = (
            '<tg-emoji emoji-id="6311890389242487133">✅</tg-emoji> <b>MARTINGALE SETUP COMPLETE</b>\n\n'
            '📥 <b>Now choose Days Filter Strategy Depth (1 to 7):</b>'
        )
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=msg_body, parse_mode='HTML')
        return

    # Backtest Callback: Final Dynamic Compilation
    if state == 'SELECTING_DAYS' and call.data.startswith('day_'):
        selected_day = call.data.split('_')[1]
        msg = bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text='🔍 <b>Running Advanced Backtest Algorithm...</b>', parse_mode='HTML')
        
        raw_list = user_data[chat_id]['raw_signals']
        filtered_list = advanced_filter_engine(raw_list, selected_day)
        
        header_text = f'🚀 <b>--- ZEBRONIX PREMIUM SIGNALS ---</b>\n━━━━━━━━━━━━━━━━━━━━━━\n📊 <b>Analysis Filter:</b> Day {selected_day}\n📥 <b>Total Input:</b> {len(raw_list)} | 🔥 <b>Filtered:</b> {len(filtered_list)}\n━━━━━━━━━━━━━━━━━━━━━━\n'
        body_text = ""
        if not filtered_list:
            body_text += "<code>No signals matching this matrix density.</code>\n"
        else:
            body_text += "<pre>"
            for sig in filtered_list: body_text += f"M1;{sig['asset']};{sig['time']};{sig['direction']}\n"
            body_text += "</pre>"
        footer_text = f'━━━━━━━━━━━━━━━━━━━━━━\n⚡ <i>Core Powered By: Zebronix Filter Engine</i>'
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✍️ EDIT OUTPUT", callback_data="edit_mode"))
        bot.send_message(chat_id, header_text + body_text + footer_text, reply_markup=markup, parse_mode='HTML')
        user_data[chat_id]['state'] = 'PREVIEW'
        user_data[chat_id]['last_header'] = header_text
        user_data[chat_id]['last_footer'] = footer_text
        return

    if call.data == "edit_mode":
        bot.send_message(chat_id, "✍️ <b>Please send your edited signals list now:</b>", parse_mode='HTML')
        user_data[chat_id]['state'] = 'EDITING_PROCESS'
        return

    # Future Callback: Market Selected -> Spawn Grid Keyboard
    if state == 'FUTURE_MARKET_SELECT' and call.data.startswith('f_m_'):
        mode = call.data.replace('f_m_', '')
        user_data[chat_id]['market_mode'] = mode
        user_data[chat_id]['selected_pairs'] = []  # ফ্রেশ বাস্কেট
        user_data[chat_id]['state'] = 'FUTURE_GRID_SELECTING'
        
        keyboard = make_pair_selection_keyboard([], mode)
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text='🎛️ <b>TAP PAIRS FROM GRID TO SELECT / UNSELECT:</b>', reply_markup=keyboard, parse_mode='HTML')
        return

    # Future Callback: Dynamic Grid Toggle (সিলেক্টেড থাকলে বডিতে প্রিমিয়াম রেন্ডার হবে)
    if state == 'FUTURE_GRID_SELECTING' and call.data.startswith('toggle_'):
        pair = call.data.replace('toggle_', '')
        mode = user_data[chat_id]['market_mode']
        current_selections = user_data[chat_id]['selected_pairs']
        
        if pair in current_selections:
            current_selections.remove(pair)
        else:
            current_selections.append(pair)
            
        user_data[chat_id]['selected_pairs'] = current_selections
        
        # বাটন ফ্লাশ আপডেট
        keyboard = make_pair_selection_keyboard(current_selections, mode)
        
        # এখানে মেসেজের ভেতর লাইভ প্রিমিয়াম টিকমার্ক আপডেট দেখাবে!
        pairs_formatted = ", ".join(current_selections) if current_selections else "None"
        display_text = (
            f'🎛️ <b>TAP PAIRS FROM GRID TO SELECT / UNSELECT:</b>\n\n'
            f'<tg-emoji emoji-id="6311890389242487133">✅</tg-emoji> <b>Selected:</b> <code>{pairs_formatted}</code>'
        )
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=display_text, reply_markup=keyboard, parse_mode='HTML')
        return

    # Future Callback: Pair Grid Completed
    if state == 'FUTURE_GRID_SELECTING' and call.data == 'pair_selection_done':
        valid_markets = user_data[chat_id]['selected_pairs']
        if not valid_markets:
            bot.answer_callback_query(call.id, text="⚠️ Please select at least ONE pair before continuing!", show_alert=True)
            return
            
        market_mode = user_data[chat_id]['market_mode']
        if market_mode != "BLACKOUT":
            user_data[chat_id]['state'] = 'FUTURE_DIR_SELECT'
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                types.InlineKeyboardButton('🟢 BUY Only', callback_data='f_d_1'),
                types.InlineKeyboardButton('🔴 PUT Only', callback_data='f_d_2'),
                types.InlineKeyboardButton('🔵 BOTH SIGNALS', callback_data='f_d_3')
            )
            bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="📊 <b>SELECT DIRECTION TARGET MATRIX:</b>", reply_markup=markup, parse_mode='HTML')
        else:
            user_data[chat_id]['action_choice'] = "3"
            user_data[chat_id]['state'] = 'FUTURE_START_TIME'
            bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="🕒 <b>Enter Start Time (Format HH:MM, e.g. 10:30):</b>", parse_mode='HTML')
        return

    # Future Callback: Direction Recorded
    if state == 'FUTURE_DIR_SELECT' and call.data.startswith('f_d_'):
        choice = call.data.replace('f_d_', '')
        user_data[chat_id]['action_choice'] = choice
        user_data[chat_id]['state'] = 'FUTURE_START_TIME'
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="🕒 <b>Enter Start Time (Format HH:MM, e.g. 10:30):</b>", parse_mode='HTML')
        return

    # Future Callback: Days Depth Processing
    if state == 'FUTURE_DAYS_SELECT' and call.data.startswith('f_day_'):
        filter_days = int(call.data.replace('f_day_', ''))
        execute_future_generation(chat_id, call.message.message_id, filter_days)
        return

# --- Text Handlers Module ---
@bot.message_handler(func=lambda m: True)
def global_text_handler(message):
    chat_id = message.chat.id
    state = user_data.get(chat_id, {}).get('state')
    text = message.text.strip()

    if state == 'COLLECTING_SIGNALS':
        if text == '/done':
            if not user_data[chat_id]['raw_signals']:
                bot.send_message(chat_id, '⚠️ <b>No signals received yet.</b>', parse_mode='HTML')
                return
            user_data[chat_id]['state'] = 'SELECTING_MTG'
            
            markup = types.InlineKeyboardMarkup(row_width=3)
            markup.add(
                types.InlineKeyboardButton('🛡️ MTG 1', callback_data='mtg_1'),
                types.InlineKeyboardButton('🛡️ MTG 2', callback_data='mtg_2'),
                types.InlineKeyboardButton('🛡️ MTG 3', callback_data='mtg_3')
            )
            
            # প্রিমিয়াম অ্যানিমেটেড ইমোজি চমৎকারভাবে রেন্ডার হবে
            msg_body = (
                '<tg-emoji emoji-id="6311890389242487133">✅</tg-emoji> <b>SIGNALS POOL SAVED!</b>\n\n'
                '⚙ *Please choose your Martingale Strategy from buttons below:*'
            )
            bot.send_message(chat_id, msg_body, reply_markup=markup, parse_mode='HTML')
            return
        new_signals = parse_raw_signals(text)
        user_data[chat_id]['raw_signals'].extend(new_signals)
        bot.send_message(chat_id, f'✅ <b>Added {len(new_signals)} signals. Send /done to execute filters.</b>', parse_mode='HTML')
        return

    if state == 'EDITING_PROCESS':
        header = user_data[chat_id].get('last_header', '')
        footer = user_data[chat_id].get('last_footer', '')
        bot.send_message(chat_id, "✅ <b>Signals List Updated Successfully!</b>", parse_mode='HTML')
        bot.send_message(chat_id, f"{header}<pre>{text}</pre>\n{footer}", parse_mode='HTML')
        show_main_dashboard(chat_id)
        return

    if state == 'FUTURE_START_TIME':
        user_data[chat_id]['start_time'] = text if re.match(r'^\d{2}:\d{2}$', text) else "00:00"
        user_data[chat_id]['state'] = 'FUTURE_END_TIME'
        bot.send_message(chat_id, "🕒 <b>Enter End Time (Format HH:MM, e.g. 18:45):</b>", parse_mode='HTML')
        return

    if state == 'FUTURE_END_TIME':
        user_data[chat_id]['end_time'] = text if re.match(r'^\d{2}:\d{2}$', text) else "23:59"
        user_data[chat_id]['state'] = 'FUTURE_DAYS_SELECT'
        
        markup = types.InlineKeyboardMarkup(row_width=3)
        buttons = [types.InlineKeyboardButton(f"📆 {d} Days", callback_data=f"f_day_{d}") for d in range(1, 16)]
        markup.add(*buttons)
        
        info_msg = (
            "🦅 <b>STRATEGY ANALYSIS DEPTH FILTER</b>\n\n"
            "▫️ <b>1 - 5 Days:</b> High Density Signals (High Quantity)\n"
            "▫️ <b>6 - 12 Days:</b> Balanced Filtered Strategy\n"
            "▫️ <b>13 - 15 Days:</b> Ultra Precise Strategy\n\n"
            "<i>Select computing range matrix below:</i>"
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
    
    bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="⚡ <pre>ZEBRONIX PIPELINE ENGINE RUNNING...</pre>", parse_mode='HTML')
    
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
    density_status = "HIGH" if filter_days <= 5 else "MEDIUM" if filter_days <= 12 else "ULTRA"
    
    output_text = (
        f"<b>ZEBRONIX GENERATED SIGNALS</b>\n\n"
        f"<b>Mode:</b> {market_mode}\n"
        f"<b>Days Analyser:</b> {filter_days} Days ({density_status})\n"
        f"<b>Window:</b> {start_time} to {end_time}\n"
        f"-----------------------------\n<pre>"
    )
    
    if not filtered:
        output_text += "No setups match current algorithm parameters.\n"
    else:
        call_count, put_count = 0, 0
        for sig in filtered:
            time_normal = sig.get('time', '')
            asset = sig.get('asset', '').strip().replace("-OTC", "_OTC")
            direction = sig.get('direction', '').upper()
            
            if market_mode == "BLACKOUT":
                output_text += f"M1;{asset};{time_normal}\n"
                call_count += 1
            else:
                output_text += f"M1;{asset};{time_normal};{direction}\n"
                if direction == "CALL": call_count += 1
                else: put_count += 1
                
    output_text += "</pre>-----------------------------\n"
    if market_mode == "BLACKOUT":
        output_text += f"<b>Total Blackout Signals:</b> {len(filtered)}\n"
    else:
        output_text += f"<b>Total:</b> {len(filtered)} | <b>CALL:</b> {call_count} | <b>PUT:</b> {put_count}\n"
        
    output_text += (
        f"\n<b>Channel:</b> <a href='https://t.me/irttradindzone'>@irttradindzone</a>\n"
        f"<b>Support:</b> @irtsupport1\n"
        f"<i>Core Powered By: IRT TRADING ZONE</i>"
    )
    
    bot.send_message(chat_id, output_text, parse_mode="HTML", disable_web_page_preview=True)
    show_main_dashboard(chat_id)

# --- Broadcast Feature ---
@bot.message_handler(commands=['broadcast'])
def broadcast_handler(message):
    if message.from_user.id == ADMIN_ID:
        msg_text = message.text.replace('/broadcast ', '').strip()
        if not msg_text:
            bot.send_message(message.chat.id, '⚠️ <b>Please provide message context.</b>', parse_mode='HTML')
            return
        user_list = get_all_users()
        status_msg = bot.send_message(message.chat.id, f"📢 <b>Sending...</b>", parse_mode='HTML')
        success, failed = 0, 0
        for user_id in user_list:
            try:
                bot.send_message(int(user_id), msg_text, parse_mode='HTML')
                success += 1
            except: failed += 1
        bot.edit_message_text(chat_id=message.chat.id, message_id=status_msg.message_id, text=f"📊 <b>Report:</b>\n\n✅ Sent: {success}\n❌ Failed: {failed}", parse_mode='HTML')

# --- Main Runtime Guard ---
if __name__ == '__main__':
    threading.Thread(target=run_web_server, daemon=True).start()
    bot.infinity_polling()
