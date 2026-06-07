import os
import re
import threading
import time
from datetime import datetime
from flask import Flask
import telebot
from telebot import types

# --- Configuration ---
API_TOKEN = '8777471998:AAEJ3LzsWqj8JB15_yzwXOMyS1GHEiGtBbI' 
ADMIN_ID = 8280240170  # рждрзЛржорж╛рж░ ржЯрзЗрж▓рж┐ржЧрзНрж░рж╛ржо ржЖржЗржбрж┐ ржПржЦрж╛ржирзЗ ржжрж╛ржУ
PASSWORD = 'backtest'

app = Flask('')
bot = telebot.TeleBot(API_TOKEN)
user_data = {}

@app.route('/')
def home(): return 'Bot is running!'

# --- Signal Logic ---
def parse_raw_signals(text_block):
    parsed_list = []
    lines = text_block.strip().split('\n')
    pattern = r'([A-Z0-9_-]+(?:-OTC)?)[;\s,]+(\d{2}:\d{2})[;\s,]+(CALL|PUT)'
    for line in lines:
        match = re.search(pattern, line.upper().replace('M1', '').replace(';', ' '))
        if match:
            parsed_list.append({'asset': match.group(1), 'time': match.group(2), 'direction': match.group(3)})
    return parsed_list

def advanced_filter(signals, days):
    signals.sort(key=lambda x: datetime.strptime(x['time'], '%H:%M'))
    unique = []
    seen = set()
    for sig in signals:
        if sig['time'] not in seen:
            seen.add(sig['time']); unique.append(sig)
    
    final = []
    min_gap = int(days) * 3
    last_time = None
    for sig in unique:
        curr = datetime.strptime(sig['time'], '%H:%M')
        if not last_time or int((curr - last_time).total_seconds() / 60) >= min_gap:
            final.append(sig); last_time = curr
    return final

# --- Admin & Bot Handlers ---
@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id == ADMIN_ID:
        msg = message.text.replace('/broadcast ', '')
        # ржПржЦрж╛ржирзЗ рж╕ржм ржЗржЙржЬрж╛рж░ржХрзЗ ржорзЗрж╕рзЗржЬ ржкрж╛ржарж╛ржирзЛрж░ рж▓ржЬрж┐ржХ рж╣ржмрзЗ
        bot.reply_to(message, f"ЁЯУв Broadcast: {msg}")

@bot.message_handler(commands=['start'])
def start(message):
    user_data[message.chat.id] = {'state': 'AWAITING_PASS', 'signals': []}
    bot.send_message(message.chat.id, "ЁЯФР Enter Password:")

@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get('state') == 'AWAITING_PASS')
def check_pass(message):
    if message.text == PASSWORD:
        user_data[message.chat.id]['state'] = 'COLLECTING'
        bot.send_message(message.chat.id, "тЬЕ Access Granted! Paste signals and /done.")
    else: bot.send_message(message.chat.id, "тЭМ Wrong!")

@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get('state') == 'COLLECTING')
def collect(message):
    if message.text == '/done':
        markup = types.InlineKeyboardMarkup()
        for i in range(1, 4): markup.add(types.InlineKeyboardButton(f"MTG {i}", callback_data=f"mtg_{i}"))
        bot.send_message(message.chat.id, "Choose MTG:", reply_markup=markup)
        user_data[message.chat.id]['state'] = 'MTG'
    else:
        new = parse_raw_signals(message.text)
        user_data[message.chat.id]['signals'].extend(new)
        bot.reply_to(message, f"тЬЕ Added {len(new)} signals. Total: {len(user_data[message.chat.id]['signals'])}")

@bot.callback_query_handler(func=lambda call: user_data.get(call.message.chat.id, {}).get('state') == 'MTG')
def mtg_select(call):
    user_data[call.message.chat.id]['state'] = 'DAYS'
    markup = types.InlineKeyboardMarkup(row_width=4)
    for i in range(1, 8): markup.add(types.InlineKeyboardButton(str(i), callback_data=f"day_{i}"))
    bot.edit_message_text("Choose Days (Filter Accuracy):", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: user_data.get(call.message.chat.id, {}).get('state') == 'DAYS')
def final_filter(call):
    day = call.data.split('_')[1]
    filtered = advanced_filter(user_data[call.message.chat.id]['signals'], day)
    
    # рж░рзЗржЬрж╛рж▓рзНржЯ ржПржмржВ ржПржбрж┐ржЯ ржмрж╛ржЯржи
    text = f"ЁЯОп Filtered ({len(filtered)} signals):\n" + "\n".join([f"{s['asset']} {s['time']} {s['direction']}" for s in filtered])
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("тЬПя╕П Edit Signals", callback_data="edit_mode"))
    
    bot.send_message(call.message.chat.id, text, reply_markup=markup)
    user_data[call.message.chat.id]['last_result'] = text
    user_data[call.message.chat.id]['state'] = 'FINISHED'

@bot.callback_query_handler(func=lambda call: call.data == "edit_mode")
def edit_mode(call):
    bot.send_message(call.message.chat.id, "ЁЯУЭ Send the edited signals list now:")
    user_data[call.message.chat.id]['state'] = 'EDITING'

@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get('state') == 'EDITING')
def save_edit(message):
    bot.send_message(message.chat.id, f"тЬЕ Updated:\n{message.text}")
    user_data[message.chat.id]['state'] = None

if __name__ == '__main__':
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()
    bot.infinity_polling()
