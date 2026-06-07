import os
import re
import threading
import time
from datetime import datetime
from flask import Flask
import telebot
from telebot import types

# --- Flask Web Server Setup (For Render Hosting) ---
app = Flask('')

@app.route('/')
def home():
    return 'Premium Backtest Bot with Business Mode is Online!'

def run_web_server():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# --- Configuration (এখানে তোমার ডাটা বসাও) ---
API_TOKEN = '8777471998:AAEJ3LzsWqj8JB15_yzwXOMyS1GHEiGtBbI'  # <--- তোমার বটের আসল টোকেন বসাও
ADMIN_ID = 8280240170               # <--- তোমার আসল টেলিগ্রাম আইডি বসাও
PASSWORD = 'backtest'
USER_FILE = 'users.txt'

bot = telebot.TeleBot(API_TOKEN)
user_data = {}

# --- User Database Helpers (Id Tracking) ---
def save_user(chat_id):
    if not os.path.exists(USER_FILE):
        with open(USER_FILE, 'w') as f:
            pass
    with open(USER_FILE, 'r') as f:
        users = f.read().splitlines()
    if str(chat_id) not in users:
        with open(USER_FILE, 'a') as f:
            f.write(f"{chat_id}\n")

def get_all_users():
    if not os.path.exists(USER_FILE):
        return []
    with open(USER_FILE, 'r') as f:
        return f.read().splitlines()

# --- Signal Parser Engine ---
def parse_raw_signals(text_block):
    parsed_list = []
    lines = text_block.strip().split('\n')
    pattern = r'([A-Z0-9_-]+ Mini|[A-Z0-9_-]+(?:-OTC)?)[;\s,]+(\d{2}:\d{2})[;\s,]+(CALL|PUT)|(\d{2}:\d{2})[;\s,]+([A-Z0-9_-]+(?:-OTC)?)[;\s,]+(CALL|PUT)|(CALL|PUT)[;\s,]+([A-Z0-9_-]+(?:-OTC)?)[;\s,]+(\d{2}:\d{2})'

    for line in lines:
        if not line.strip():
            continue
        cleaned_line = line.upper().replace('M1', '').replace(';', ' ').strip()
        match = re.search(pattern, cleaned_line)

        if match:
            if match.group(1):
                asset, time_str, direction = match.group(1), match.group(2), match.group(3)
            elif match.group(4):
                time_str, asset, direction = match.group(4), match.group(5), match.group(6)
            else:
                direction, asset, time_str = match.group(7), match.group(8), match.group(9)

            parsed_list.append({'asset': asset, 'time': time_str, 'direction': direction})
    return parsed_list

# --- 3 Prompts Filter Engine ---
def advanced_filter_engine(signals, days_filter):
    if not signals:
        return []
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

# --- Admin Broadcast Feature ---
@bot.message_handler(commands=['broadcast'])
def broadcast_handler(message):
    if message.from_user.id == ADMIN_ID:
        msg_text = message.text.replace('/broadcast ', '').strip()
        if not msg_text:
            bot.send_message(message.chat.id, '<tg-emoji emoji-id="6066584947039148700">⚠️</tg-emoji> <b>Please provide a message.</b>', parse_mode='HTML')
            return
        user_list = get_all_users()
        if not user_list:
            bot.send_message(message.chat.id, '<tg-emoji emoji-id="6066584947039148700">⚠️</tg-emoji> <b>No users found in database yet!</b>', parse_mode='HTML')
            return
        status_msg = bot.send_message(message.chat.id, f"📢 <b>Sending broadcast...</b>", parse_mode='HTML')
        success, failed = 0, 0
        for user_id in user_list:
            try:
                bot.send_message(int(user_id), msg_text, parse_mode='HTML')
                success += 1
            except Exception:
                failed += 1
        bot.edit_message_text(chat_id=message.chat.id, message_id=status_msg.message_id, text=f"📊 <b>Broadcast Report:</b>\n\n✅ Sent: {success}\n❌ Failed: {failed}", parse_mode='HTML')
    else:
        bot.send_message(message.chat.id, '<tg-emoji emoji-id="6132202065818035620">❌</tg-emoji> <b>Access Denied! Only Admin can use this.</b>', parse_mode='HTML')

# --- Bot Command Handlers ---
@bot.message_handler(commands=['start'])
def start_command(message):
    chat_id = message.chat.id
    save_user(chat_id)
    
    password_text = '<tg-emoji emoji-id="5429405838345265327">🔓</tg-emoji> <b>Please enter password to access Backtest Module:</b>'
    bot.send_message(chat_id, password_text, parse_mode='HTML')
    user_data[chat_id] = {'state': 'AWAITING_PASSWORD', 'raw_signals': []}

@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get('state') == 'AWAITING_PASSWORD')
def check_password(message):
    chat_id = message.chat.id
    if message.text.strip() == PASSWORD:
        user_data[chat_id]['state'] = 'COLLECTING_SIGNALS'
        
        welcome_text = (
            '🟢 <b>PRIVATE 🚀 TELEGRAM</b>\n\n'
            '<tg-emoji emoji-id="6302933664443407379">😉</tg-emoji><tg-emoji emoji-id="6301098351903383801">😌</tg-emoji><tg-emoji emoji-id="6302817872125106654">😇</tg-emoji><tg-emoji emoji-id="6303094047112174523">🙂</tg-emoji><tg-emoji emoji-id="6253781912679095168">🔤</tg-emoji><tg-emoji emoji-id="6253649906859249270">🔤</tg-emoji><tg-emoji emoji-id="6253644851682742620">🔤</tg-emoji>\n\n'
            '<tg-emoji emoji-id="6300758774609092069">🌍</tg-emoji> <b>BACKTEST MODULE</b>\n\n'
            '<tg-emoji emoji-id="6131977683841589337">👑</tg-emoji> <b>Paste your signals in ANY FORMAT:</b>\n'
            '<code>M1 ; EURUSD-OTC;04:22;CALL</code>\n'
            '<code>EURUSD 04:22 CALL</code>\n'
            '<code>CALL EURUSD-OTC 04:22</code>\n\n'
            '<tg-emoji emoji-id="6075758322873541432">🏦</tg-emoji> <b>Send multiple lines and finish with /done</b>'
        )
        bot.send_message(chat_id, welcome_text, parse_mode='HTML')
    else:
        bot.send_message(chat_id, '<tg-emoji emoji-id="6066584947039148700">⚠️</tg-emoji> <b>Wrong Password! Try again.</b>', parse_mode='HTML')

@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get('state') == 'COLLECTING_SIGNALS')
def collect_signals_handler(message):
    chat_id = message.chat.id
    if message.text.strip() == '/done':
        if not user_data[chat_id]['raw_signals']:
            bot.send_message(chat_id, '<tg-emoji emoji-id="6066584947039148700">⚠️</tg-emoji> <b>No signals received yet.</b>', parse_mode='HTML')
            return
        user_data[chat_id]['state'] = 'SELECTING_MTG'
        
        markup = types.InlineKeyboardMarkup(row_width=3)
        markup.add(
            types.InlineKeyboardButton('<tg-emoji emoji-id="6212950328610923100">🛡</tg-emoji> MTG 1', callback_data='mtg_1'),
            types.InlineKeyboardButton('<tg-emoji emoji-id="6212950328610923100">🛡</tg-emoji> MTG 2', callback_data='mtg_2'),
            types.InlineKeyboardButton('<tg-emoji emoji-id="6212950328610923100">🛡</tg-emoji> MTG 3', callback_data='mtg_3')
        )
        # 🌟 এখানে তোমার দেওয়া নতুন প্রিমিয়াম জোড়া স্টার ইমোজি সেট করা হয়েছে
        bot.send_message(chat_id, '<tg-emoji emoji-id="6311888482277007276">⭐️</tg-emoji><tg-emoji emoji-id="6311888482277007276">⭐️</tg-emoji> <b>BACKTEST MTG CHOOSE:</b>', reply_markup=markup, parse_mode='HTML')
        return

    new_signals = parse_raw_signals(message.text)
    user_data[chat_id]['raw_signals'].extend(new_signals)
    bot.send_message(chat_id, f'✅ <b>Added {len(new_signals)} signals. Send /done to finish.</b>', parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: user_data.get(call.message.chat.id, {}).get('state') == 'SELECTING_MTG')
def mtg_callback(call):
    chat_id = call.message.chat.id
    user_data[chat_id]['state'] = 'SELECTING_DAYS'
    markup = types.InlineKeyboardMarkup(row_width=4)
    buttons = [types.InlineKeyboardButton(f"📅 {i}", callback_data=f'day_{i}') for i in range(1, 8)]
    markup.add(*buttons)
    bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text='⭐ <b>CHOOSE DAYS FILTER (1 - 7):</b>', reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: user_data.get(call.message.chat.id, {}).get('state') == 'SELECTING_DAYS')
def days_callback(call):
    chat_id = call.message.chat.id
    selected_day = call.data.split('_')[1]

    msg = bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text='🔍 <b>Backtesting started...</b>\nProgress: [░░░░░░░░░░] 0%', parse_mode='HTML')
    progress_steps = [
        ('██░░░░░░░░', 20, 'Processing...'),
        ('██████░░░░', 60, 'Deduplicating...'),
        ('██████████', 100, 'Complete!')
    ]
    for bar, percent, stage in progress_steps:
        time.sleep(0.4)
        bot.edit_message_text(chat_id=chat_id, message_id=msg.message_id, text=f'🔍 <b>Backtesting...</b>\n[{bar}] {percent}%\n<i>{stage}</i>', parse_mode='HTML')

    raw_list = user_data[chat_id]['raw_signals']
    filtered_list = advanced_filter_engine(raw_list, selected_day)

    header_text = (
        f'🚀 <b>--- ZEBRONIX PREMIUM SIGNALS ---</b> 🚀\n'
        f'━━━━━━━━━━━━━━━━━━━━━━\n'
        f'📊 <b>Analysis Filter:</b> Day {selected_day}\n'
        f'📥 <b>Total Input:</b> {len(raw_list)} | 🔥 <b>Filtered:</b> {len(filtered_list)}\n'
        f'━━━━━━━━━━━━━━━━━━━━━━\n'
    )

    body_text = ""
    if not filtered_list:
        body_text += "<code>No signals matched this density filter.</code>\n"
    else:
        body_text += "<pre>"
        for sig in filtered_list:
            body_text += f"M1;{sig['asset']};{sig['time']};{sig['direction']}\n"
        body_text += "</pre>"

    footer_text = f'━━━━━━━━━━━━━━━━━━━━━━\n⚡ <i>Core Powered By: Zebronix Filter Engine</i>'
    final_output = header_text + body_text + footer_text

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✏️ EDIT SIGNALS", callback_data="edit_mode"))
    
    bot.send_message(chat_id, final_output, reply_markup=markup, parse_mode='HTML')
    user_data[chat_id]['state'] = 'PREVIEW'
    user_data[chat_id]['last_header'] = header_text
    user_data[chat_id]['last_footer'] = footer_text

@bot.callback_query_handler(func=lambda call: call.data == "edit_mode")
def edit_mode_callback(call):
    chat_id = call.message.chat.id
    bot.send_message(chat_id, "✍️ <b>Please send your edited signals list now:</b>", parse_mode='HTML')
    user_data[chat_id]['state'] = 'EDITING_PROCESS'

@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get('state') == 'EDITING_PROCESS')
def save_edited_signals_handler(message):
    chat_id = message.chat.id
    edited_text = message.text.strip()
    header = user_data[chat_id].get('last_header', '')
    footer = user_data[chat_id].get('last_footer', '')
    final_output = f"{header}<pre>{edited_text}</pre>\n{footer}"
    bot.send_message(chat_id, "✅ <b>Signals Updated Successfully!</b>", parse_mode='HTML')
    bot.send_message(chat_id, final_output, parse_mode='HTML')
    user_data.pop(chat_id, None)

if __name__ == '__main__':
    threading.Thread(target=run_web_server, daemon=True).start()
    bot.infinity_polling()
