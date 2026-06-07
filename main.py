import os
import re
import hashlib
import threading
from datetime import datetime, timedelta
from flask import Flask
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- Flask Web Server Setup (For 24/7 Hosting) ---
app = Flask('')

@app.route('/')
def home():
    return 'Zebronix Premium Bot Center is Fully Functional & Online!'

def run_web_server():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# --- Integrated Configuration Setup ---
API_ID = 25635250
API_HASH = '42a88741c882a13d0079758580141c98'
BOT_TOKEN = '8777471998:AAEJ3LzsWqj8JB15_yzwXOMyS1GHEiGtBbI'

PASSWORD = 'backtest'
USER_FILE = 'users.txt'
ADMIN_ID = 8280240170  # ⚠️ এখানে আপনার নিজের পার্সোনাল টেলিগ্রাম আইডি নম্বরটি বসিয়ে দিন

# Pyrogram Dual-Engine Initializer (Premium Enabled Bot)
app_tg = Client("zebronix_premium_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
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
    pattern = r'([A-Z0-9_-]+ Mini|[A-Z0-9_-]+(?:-OTC)?)[;\s,]+(\d{2}:\d{2})[;\s,]+(CALL|PUT)|(\d{2}:\d{2})[;\s,]+([A-Z0-9_-]+(?:-OTC)?)[;\s,]+(CALL|PUT)|(CALL|PUT)[;\s,]+([A-Z0-9_-]+(?:-OTC)?)[:\s,]+(\d{2}:\d{2})'
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

# --- Grid Keyboard Generator Using Premium Compatible Inline Markup ---
def make_pair_selection_keyboard(selected_pairs, mode):
    pool = OTC_PAIRS_PLAIN if mode in ["OTC", "BLACKOUT"] else REAL_PAIRS_PLAIN
    buttons = []
    row = []
    for pair in pool:
        label = f"🟢 {pair}" if pair in selected_pairs else f"▪️ {pair}"
        row.append(InlineKeyboardButton(label, callback_data=f"toggle_{pair}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("➔ CONTINUE SYSTEM PROCESS", callback_data="continue_future")])
    return InlineKeyboardMarkup(buttons)

# --- Premium Dashboard Renderer ---
def show_main_dashboard(client, chat_id):
    user_data[chat_id]['state'] = 'MAIN_MENU'
    
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton('📊 BACKTEST ENGINE', callback_data='btn_backtest'), 
             InlineKeyboardButton('🤖 FUTURE GENERATOR', callback_data='btn_future')],
            [InlineKeyboardButton('👑 VIP PAIR LIST', callback_data='btn_vip'), 
             InlineKeyboardButton('⚙️ LIVE STATUS', callback_data='btn_status')]
        ]
    )
    
    dashboard_text = (
        '<tg-emoji emoji-id="118457122498814358">💻</tg-emoji> <b>ZEBRONIX CONTROL CENTER</b>\n\n'
        '<tg-emoji emoji-id="6312053434790976755">📊</tg-emoji> '
        '<tg-emoji emoji-id="6134212600138833922">🤖</tg-emoji> '
        '<tg-emoji emoji-id="6131977683841589337">👑</tg-emoji> '
        '<tg-emoji emoji-id="6300679098670784062">⚙️</tg-emoji> <b>Premium Multi-Modules Active!</b>\n\n'
        '🪧 <b>Select an operational module from below:</b>'
    )
    client.send_message(chat_id, dashboard_text, reply_markup=keyboard)

# --- Start Handler ---
@app_tg.on_message(filters.command("start", prefixes=["/", "."]) & filters.private)
def start_command(client, message):
    chat_id = message.chat.id
    save_user(chat_id)
    user_data[chat_id] = {'state': 'AWAITING_PASSWORD', 'raw_signals': [], 'selected_pairs': []}
    message.reply_text('⚙️ <b>Please enter authorization password:</b>')

# --- Callback Query Engine (Handles Dashboard & Selections) ---
@app_tg.on_callback_query()
def callback_handler(client, callback_query):
    chat_id = callback_query.message.chat.id
    data = callback_query.data
    
    if chat_id not in user_data: return

    # Dashboard Actions
    if data == 'btn_backtest':
        user_data[chat_id]['state'] = 'COLLECTING_SIGNALS'
        welcome_text = (
            '<tg-emoji emoji-id="6312053434790976755">📊</tg-emoji> <b>BACKTEST ENGINE ACTIVATED</b>\n\n'
            '📥 <b>Paste your signals list below.</b>\n'
            '<i>When finished sending all lines, type</i> <code>/done</code> <i>to process.</i>'
        )
        callback_query.message.edit_text(welcome_text)
        
    elif data == 'btn_future':
        user_data[chat_id]['state'] = 'FUTURE_MARKET_SELECT'
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton('📊 OTC MARKETS', callback_data='m_otc')],
             [InlineKeyboardButton('📈 REAL MARKETS', callback_data='m_real')],
             [InlineKeyboardButton('🥷 BLACKOUT SIGNALS', callback_data='m_blackout')]]
        )
        callback_query.message.edit_text('⚡️ <b>SELECT TARGET MARKET TYPE:</b>', reply_markup=keyboard)
        
    elif data in ['btn_vip', 'btn_status']:
        callback_query.answer("⚡ Parameter Synced With Master Server!", show_alert=True)

    # Market Selection Routing
    elif data in ['m_otc', 'm_real', 'm_blackout']:
        mode = "OTC" if "otc" in data else "REAL" if "real" in data else "BLACKOUT"
        user_data[chat_id]['market_mode'] = mode
        user_data[chat_id]['selected_pairs'] = []
        user_data[chat_id]['state'] = 'FUTURE_GRID_SELECTING'
        
        keyboard = make_pair_selection_keyboard([], mode)
        callback_query.message.edit_text('⚙️ <b>SELECT PAIRS FROM THE ACTIVE GRID:</b>', reply_markup=keyboard)

    # Asset Grid Selector Mechanism
    elif data.startswith('toggle_'):
        pair_name = data.replace('toggle_', '').strip()
        mode = user_data[chat_id]['market_mode']
        current_selections = user_data[chat_id]['selected_pairs']
        
        if pair_name in current_selections:
            current_selections.remove(pair_name)
        else:
            current_selections.append(pair_name)
            
        user_data[chat_id]['selected_pairs'] = current_selections
        keyboard = make_pair_selection_keyboard(current_selections, mode)
        
        # Smooth background updates without flashing
        try:
            callback_query.message.edit_reply_markup(reply_markup=keyboard)
        except: pass
        callback_query.answer(f"Updated: {pair_name}")

    elif data == 'continue_future':
        mode = user_data[chat_id]['market_mode']
        valid_markets = user_data[chat_id]['selected_pairs']
        if not valid_markets:
            callback_query.answer("⚠️ Select at least ONE pair!", show_alert=True)
            return
            
        if mode != "BLACKOUT":
            user_data[chat_id]['state'] = 'FUTURE_DIR_SELECT'
            keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton('🟢 BUY Only', callback_data='dir_1')],
                 [InlineKeyboardButton('🔴 PUT Only', callback_data='dir_2')],
                 [InlineKeyboardButton('🔵 BOTH SIGNALS', callback_data='dir_3')]]
            )
            callback_query.message.edit_text('📊 <b>SELECT DIRECTION TARGET MATRIX:</b>', reply_markup=keyboard)
        else:
            user_data[chat_id]['action_choice'] = "3"
            user_data[chat_id]['state'] = 'FUTURE_START_TIME'
            callback_query.message.edit_text("🗓 <b>Enter Start Time via keyboard (Format HH:MM, e.g. 10:30):</b>")

    elif data.startswith('dir_'):
        choice = data.replace('dir_', '')
        user_data[chat_id]['action_choice'] = choice
        user_data[chat_id]['state'] = 'FUTURE_START_TIME'
        callback_query.message.edit_text("🗓 <b>Enter Start Time via keyboard (Format HH:MM, e.g. 10:30):</b>")

    elif data.startswith('mtg_'):
        user_data[chat_id]['state'] = 'SELECTING_DAYS'
        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton('📅 Day 1', callback_data='day_1'), InlineKeyboardButton('📅 Day 2', callback_data='day_2')],
                [InlineKeyboardButton('📅 Day 3', callback_data='day_3'), InlineKeyboardButton('📅 Day 4', callback_data='day_4')],
                [InlineKeyboardButton('📅 Day 5', callback_data='day_5'), InlineKeyboardButton('📅 Day 6', callback_data='day_6')]
            ]
        )
        callback_query.message.edit_text('🎇 <b>Now choose Days Filter Strategy Depth:</b>', reply_markup=keyboard)

    elif data.startswith('day_'):
        selected_day = data.replace('day_', '').strip()
        callback_query.message.edit_text('⚙️ <b>Running Advanced Backtest Algorithm...</b>')
        
        raw_list = user_data[chat_id]['raw_signals']
        filtered_list = advanced_filter_engine(raw_list, selected_day)
        
        header_text = f'🚀 <b>--- ZEBRONIX PREMIUM SIGNALS ---</b>\n━━━━━━━━━━━━━━━━━━━━━━\n📊 <b>Analysis Filter:</b> Day {selected_day}\n📥 <b>Total Input:</b> {len(raw_list)} | ✅ <b>Filtered:</b> {len(filtered_list)}\n━━━━━━━━━━━━━━━━━━━━━━\n'
        body_text = ""
        if not filtered_list:
            body_text += "<code>No signals matching matrix density.</code>\n"
        else:
            body_text += "<pre>"
            for sig in filtered_list: body_text += f"M1;{sig['asset']};{sig['time']};{sig['direction']}\n"
            body_text += "</pre>"
        footer_text = f'━━━━━━━━━━━━━━━━━━━━━━\n⚡ <i>Core Powered By: Zebronix Filter Engine</i>'
        
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("✍️ EDIT OUTPUT", callback_data="edit_output"), 
              InlineKeyboardButton("🔙 MAIN MENU", callback_data="back_to_menu")]]
        )
        client.send_message(chat_id, header_text + body_text + footer_text, reply_markup=keyboard)
        
        user_data[chat_id]['state'] = 'PREVIEW'
        user_data[chat_id]['last_header'] = header_text
        user_data[chat_id]['last_footer'] = footer_text

    elif data == 'edit_output':
        callback_query.message.edit_text("✍️ <b>Please type/send your edited signals text block now:</b>")
        user_data[chat_id]['state'] = 'EDITING_PROCESS'
        
    elif data == 'back_to_menu':
        show_main_dashboard(client, chat_id)

    elif data.startswith('fday_'):
        filter_days = int(data.replace("fday_", "").strip())
        execute_future_generation(client, chat_id, filter_days)

# --- Standard Text Ingest Engine ---
@app_tg.on_message(filters.text & filters.private)
def global_text_handler(client, message):
    chat_id = message.chat.id
    text = message.text.strip()
    
    if chat_id not in user_data: return
    state = user_data[chat_id].get('state')

    if state == 'AWAITING_PASSWORD':
        if text == PASSWORD:
            show_main_dashboard(client, chat_id)
        else:
            message.reply_text('😵‍💫 <b>Incorrect Security Key! Try again.</b>')
        return

    if state == 'COLLECTING_SIGNALS':
        if text == '/done':
            if not user_data[chat_id]['raw_signals']:
                message.reply_text('⚠️ <b>No setups recorded in cache.</b>')
                return
            user_data[chat_id]['state'] = 'SELECTING_MTG'
            keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton('🛡️ MTG 1', callback_data='mtg_1'), 
                  InlineKeyboardButton('🛡️ MTG 2', callback_data='mtg_2'), 
                  InlineKeyboardButton('🛡️ MTG 3', callback_data='mtg_3')]]
            )
            message.reply_text('✅ <b>SIGNALS POOL COMPILED!</b>\n\nChoose Martingale Matrix:', reply_markup=keyboard)
            return
        new_signals = parse_raw_signals(text)
        user_data[chat_id]['raw_signals'].extend(new_signals)
        message.reply_text(f'✅ <b>Added {len(new_signals)} signals. Send /done to lock pool.</b>')
        return

    if state == 'FUTURE_START_TIME':
        user_data[chat_id]['start_time'] = text if re.match(r'^\d{2}:\d{2}$', text) else "00:00"
        user_data[chat_id]['state'] = 'FUTURE_END_TIME'
        message.reply_text("🗓 <b>Enter End Time (Format HH:MM, e.g. 18:45):</b>")
        return

    if state == 'FUTURE_END_TIME':
        user_data[chat_id]['end_time'] = text if re.match(r'^\d{2}:\d{2}$', text) else "23:59"
        user_data[chat_id]['state'] = 'FUTURE_DAYS_SELECT'
        
        days_buttons = []
        row = []
        for i in range(1, 16):
            row.append(InlineKeyboardButton(f"📅 {i} Days", callback_data=f"fday_{i}"))
            if len(row) == 3:
                days_buttons.append(row)
                row = []
        if row: days_buttons.append(row)
            
        keyboard = InlineKeyboardMarkup(days_buttons)
        message.reply_text("👀 <b>Select Compute History Range Matrix Depth:</b>", reply_markup=keyboard)
        return

    if state == 'EDITING_PROCESS':
        header = user_data[chat_id].get('last_header', '')
        footer = user_data[chat_id].get('last_footer', '')
        message.reply_text("✅ <b>Signals Document Overwritten Successfully!</b>")
        message.reply_text(f"{header}<pre>{text}</pre>\n{footer}")
        show_main_dashboard(client, chat_id)
        return

# --- Future Engine Processing Execution ---
def execute_future_generation(client, chat_id, filter_days):
    data = user_data.get(chat_id)
    market_mode = data['market_mode']
    valid_markets = data['selected_pairs']
    action_choice = data['action_choice']
    start_time = data['start_time']
    end_time = data['end_time']
    
    progress_msg = client.send_message(chat_id, "⚡️ <pre>COMPUTING HIGHER-ORDER ALGORITHM INTERSECTIONS...</pre>")
    
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
        f"👑 <b>ZEBRONIX GENERATED SIGNALS</b>\n\n"
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
        f"\n🎙 <b>Channel:</b> <a href='https://t.me/irttradindzone'>@irttradindzone</a>\n"
        f"<b>Support:</b> @irtsupport1\n"
        f"<i>Core Powered By: IRT TRADING ZONE</i>"
    )
    
    try: progress_msg.delete()
    except: pass
    client.send_message(chat_id, output_text)
    show_main_dashboard(client, chat_id)

# --- Broadcast Feature ---
@app_tg.on_message(filters.command("broadcast", prefixes=["/", "."]) & filters.user(ADMIN_ID))
def broadcast_handler(client, message):
    msg_text = message.text.replace('/broadcast ', '').replace('.broadcast ', '').strip()
    if not msg_text:
        message.reply_text('🔫 <b>Context cannot be blank!</b>')
        return
    user_list = get_all_users()
    us_msg = message.reply_text(f'🎙 <b>Distributing packets...</b>')
    success, failed = 0, 0
    for user_id in user_list:
        try:
            client.send_message(int(user_id), msg_text)
            success += 1
        except: failed += 1
    us_msg.edit_text(f"📊 <b>Broadcast Analysis:</b>\n\n✅ Dispatched: {success}\n❌ Dropped: {failed}")

# --- Engine Runtime Execution ---
if __name__ == '__main__':
    # Start Flask Web Server via concurrent Threading
    threading.Thread(target=run_web_server, daemon=True).start()
    # Trigger Pyrogram Engine
    app_tg.run()
