# keyboard.py
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_keyboard():
    # প্রিমিয়াম ইমোজির জন্য খালি জায়গা রাখা হয়েছে ""
    premium_emoji_1 = ""  # এখানে আপনার প্রিমিয়াম ইমোজি ID বসান
    premium_emoji_2 = ""  
    
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"{premium_emoji_1} 🟢 GET FUTURE SIGNAL 🟢", callback_data="get_signal"),
        ],
        [
            InlineKeyboardButton(f"{premium_emoji_2} 🔴 NEWS SIGNAL 🔴", callback_data="news_signal")
        ]
    ])

def pairs_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💱 Currency OTC", callback_data="cat_currency")],
        [InlineKeyboardButton("🪙 Commodities OTC", callback_data="cat_commodities")],
        [InlineKeyboardButton("⚡ Crypto OTC", callback_data="cat_crypto")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
    ])

def join_check_keyboard(invite_link):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Group/Channel", url=invite_link)],
        [InlineKeyboardButton("🔄 Verified / Check Access", callback_data="check_membership")]
    ])
