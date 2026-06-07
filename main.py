import hashlib
import os
import re
import threading
import time
from datetime import datetime, timedelta
from flask import Flask
import telebot
from telebot import types

# --- Flask Web Server Setup (For Render) ---
app = Flask('')


@app.route('/')
def home():
    return 'Backtest Bot is Alive!'


def run_web_server():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)


# --- Telegram Bot Setup ---
API_TOKEN = '8777471998:AAEJ3LzsWqj8JB15_yzwXOMyS1GHEiGtBbI'  # <--- তোমার আসল বট টোকেন বসাও
PASSWORD = 'backtest'

bot = telebot.TeleBot(API_TOKEN)
user_data = {}


# --- রেগুলার এক্সপ্রেশন দিয়ে যেকোনো ফরম্যাট থেকে সিগন্যাল পার্স করার ইঞ্জিন ---
def parse_raw_signals(text_block):
    parsed_list = []
    lines = text_block.strip().split('\n')

    # বিভিন্ন ফরম্যাট খোঁজার জন্য শক্তিশালী প্যাটার্ন
    pattern = r'([A-Z0-9_-]+(?:-OTC)?)[;\s,]+(\d{2}:\d{2})[;\s,]+(CALL|PUT)|(\d{2}:\d{2})[;\s,]+([A-Z0-9_-]+(?:-OTC)?)[;\s,]+(CALL|PUT)|(CALL|PUT)[;\s,]+([A-Z0-9_-]+(?:-OTC)?)[;\s,]+(\d{2}:\d{2})'

    for line in lines:
        if not line.strip():
            continue
        cleaned_line = line.upper().replace('M1', '').replace(';', ' ').strip()
        match = re.search(pattern, cleaned_line)

        if match:
            # গ্রুপ থেকে ডাটা এক্সট্র্যাক্ট করা
            if match.group(1):
                asset, time_str, direction = (
                    match.group(1),
                    match.group(2),
                    match.group(3),
                )
            elif match.group(4):
                time_str, asset, direction = (
                    match.group(4),
                    match.group(5),
                    match.group(6),
                )
            else:
                direction, asset, time_str = (
                    match.group(7),
                    match.group(8),
                    match.group(9),
                )

            parsed_list.append(
                {'asset': asset, 'time': time_str, 'direction': direction}
            )
    return parsed_list


# --- ৩টি প্রম্পটের নিয়ম অনুযায়ী সিগন্যাল মিক্সড ও ফিল্টারিং অ্যালগরিদম ---
def advanced_filter_engine(signals, days_filter):
    if not signals:
        return []

    # প্রম্পট ১: সঠিক টাইম সিকোয়েন্স অনুযায়ী সাজানো (Sort by Time)
    signals.sort(key=lambda x: datetime.strptime(x['time'], '%H:%M'))

    # প্রম্পট ২: প্রতি ইউনিক টাইমে কেবল ১টি সিগন্যাল রাখা এবং ডুপ্লিকেট রিমুভ করা
    unique_time_signals = []
    seen_times = set()
    for sig in signals:
        if sig['time'] not in seen_times:
            seen_times.add(sig['time'])
            unique_time_signals.append(sig)

    # প্রম্পট ৩: ব্যাক-টু-ব্যাক (পরপর মিনিট) সিগন্যাল রিমুভ করা এবং দিন অনুযায়ী র‍্যান্ডম গ্যাপ তৈরি করা
    final_filtered = []
    # ১ দিন = কম গ্যাপ (কম ফিল্টার), ৭ দিন = বিশাল বড় গ্যাপ (সর্বোচ্চ ফিল্টার ও কম সিগন্যাল)
    min_allowed_gap = int(days_filter) * 3

    last_time = None
    for sig in unique_time_signals:
        current_time = datetime.strptime(sig['time'], '%H:%M')

        if last_time is None:
            final_filtered.append(sig)
            last_time = current_time
        else:
            # দুই সিগন্যালের ভেতরের গ্যাপ বা মিনিট ডিফারেন্স বের করা
            time_difference = int((current_time - last_time).total_seconds() / 60)
            if time_difference >= min_allowed_gap:
                final_filtered.append(sig)
                last_time = current_time

    return final_filtered


# --- বট কমান্ড হ্যান্ডলারস ---
@bot.message_handler(commands=['start'])
def start_command(message):
    chat_id = message.chat.id
    bot.send_message(
        chat_id, '🔐 <b>Please enter password to access Backtest Module:</b>', parse_mode='HTML'
    )
    user_data[chat_id] = {'state': 'AWAITING_PASSWORD', 'raw_signals': []}


@bot.message_handler(
    func=lambda m: user_data.get(m.chat.id, {}).get('state') == 'AWAITING_PASSWORD'
)
def check_password(message):
    chat_id = message.chat.id
    if message.text.strip() == PASSWORD:
        user_data[chat_id]['state'] = 'COLLECTING_SIGNALS'
        welcome_text = (
            '🟢<b>PRIVATE 🚀TELEGRAM.</b>\n\n'
            '🌍<b>BACKTEST MODULE</b>\n\n'
            '🐼<b>Paste your signals in ANY FORMAT:</b>\n'
            'M1 ; EURUSD-OTC;04:22;CALL\n'
            'EURUSD 04:22 CALL\n'
            'CALL EURUSD-OTC 04:22\n\n'
            '🏦 Send multiple lines and finish with /done'
        )
        bot.send_message(chat_id, welcome_text, parse_mode='HTML')
    else:
        bot.send_message(chat_id, '❌ <b>Wrong Password! Try again.</b>', parse_mode='HTML')


@bot.message_handler(
    func=lambda m: user_data.get(m.chat.id, {}).get('state') == 'COLLECTING_SIGNALS'
)
def collect_signals_handler(message):
    chat_id = message.chat.id

    if message.text.strip() == '/done':
        # কোনো সিগন্যাল না দিয়ে /done দিলে এরর হ্যান্ডেলিং
        if not user_data[chat_id]['raw_signals']:
            bot.send_message(
                chat_id, '⚠️ আপনি কোনো সিগন্যাল ইনপুট দেননি। আগে সিগন্যাল পেস্ট করুন।'
            )
            return

        # MTG সিলেকশন বাটন তৈরি
        user_data[chat_id]['state'] = 'SELECTING_MTG'
        markup = types.InlineKeyboardMarkup(row_width=3)
        markup.add(
            types.InlineKeyboardButton('MTG 1', callback_data='mtg_1'),
            types.InlineKeyboardButton('MTG 2', callback_data='mtg_2'),
            types.InlineKeyboardButton('MTG 3', callback_data='mtg_3'),
        )
        bot.send_message(chat_id, '⭐⭐<b>BACKTEST MTG CHOOSE:</b>', reply_markup=markup, parse_mode='HTML')
        return

    # সিগন্যাল রিড করা এবং লিস্টে অ্যাড করা
    new_signals = parse_raw_signals(message.text)
    user_data[chat_id]['raw_signals'].extend(new_signals)
    total_count = len(user_data[chat_id]['raw_signals'])

    # স্ক্রিনশট 484.jpg এর মতো সেম টু সেম রেসপন্স ফরম্যাট
    response_msg = (
        f'✅ <b>Added {len(new_signals)} signals</b>\n'
        f'Total: {total_count}\n'
        f'Send /done to finish.'
    )
    bot.send_message(chat_id, response_msg, parse_mode='HTML')


@bot.callback_query_handler(
    func=lambda call: user_data.get(call.message.chat.id, {}).get('state') == 'SELECTING_MTG'
)
def mtg_callback(call):
    chat_id = call.message.chat.id
    # ক্লিক করা মাত্রই ডেটা সেভ করে দিন সিলেকশন মেনু আসবে
    user_data[chat_id]['state'] = 'SELECTING_DAYS'

    markup = types.InlineKeyboardMarkup(row_width=4)
    buttons = [
        types.InlineKeyboardButton(str(i), callback_data=f'day_{i}') for i in range(1, 8)
    ]
    markup.add(*buttons)

    bot.edit_message_text(
        chat_id=chat_id,
        message_id=call.message.message_id,
        text='⭐ <b>Choose Days Filter (1 - 7):</b>\n<i>দিন যত বেশি হবে, ফিল্টার তত শক্তিশালী হবে।</i>',
        reply_markup=markup,
        parse_mode='HTML',
    )


@bot.callback_query_handler(
    func=lambda call: user_data.get(call.message.chat.id, {}).get('state') == 'SELECTING_DAYS'
)
def days_callback(call):
    chat_id = call.message.chat.id
    selected_day = call.data.split('_')[1]

    # প্রোগ্রেস বার অ্যানিমেশন লোডিং স্ক্রিন
    msg = bot.edit_message_text(
        chat_id=chat_id,
        message_id=call.message.message_id,
        text='🔍 <b>Backtesting started...</b>\nProgress: [░░░░░░░░░░] 0%',
        parse_mode='HTML',
    )

    progress_steps = [
        ('██░░░░░░░░', 20, 'Parsing signal formats...'),
        ('████░░░░░░', 40, 'Sorting time sequences...'),
        ('██████░░░░', 60, 'Removing duplicate timestamps...'),
        ('████████░░', 80, 'Applying gap analysis algorithm...'),
        ('██████████', 100, 'Filtering complete!'),
    ]

    for bar, percent, stage in progress_steps:
        time.sleep(0.7)
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=msg.message_id,
            text=f'🔍 <b>Backtesting started...</b>\nProgress: [{bar}] {percent}%\nStage: <i>{stage}</i>',
            parse_mode='HTML',
        )

    # মূল ফিল্টারিং প্রসেস এক্সিকিউট করা
    raw_list = user_data[chat_id]['raw_signals']
    filtered_list = advanced_filter_engine(raw_list, selected_day)

    # আউটপুট মেসেজ সাজানো
    output_text = (
        f'🎯 <b>FILTERED BACKTEST SIGNALS (Day {selected_day})</b>\n'
        f'━━━━━━━━━━━━━━━━━━━━━━\n'
        f'📥 <b>Total Input:</b> {len(raw_list)}\n'
        f'🔥 <b>Filtered Remaining:</b> {len(filtered_list)}\n'
        f'━━━━━━━━━━━━━━━━━━━━━━\n<pre>'
    )

    if not filtered_list:
        output_text += 'No strong signals matched this high density filter.'
    else:
        for sig in filtered_list:
            output_text += f"M1;{sig['asset']};{sig['time']};{sig['direction']}\n"

    output_text += '</pre>\n━━━━━━━━━━━━━━━━━━━━━━\n⚡ <i>Core Filter Engine Powered by Zebronix</i>'

    bot.send_message(chat_id, output_text, parse_mode='HTML')

    # ইউজারের সেশন ডাটা ক্লিয়ার করে দেওয়া যাতে আবার নতুন করে শুরু করতে পারে
    user_data.pop(chat_id, None)


# --- Main Engine ---
if __name__ == '__main__':
    # ব্যাকগ্রাউন্ডে রেন্ডার সার্ভার টিকিয়ে রাখার জন্য থ্রেড চালু করা
    threading.Thread(target=run_web_server, daemon=True).start()
    bot.infinity_polling()