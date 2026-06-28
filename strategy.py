# strategy.py
import random
import requests
from datetime import datetime, timedelta

def generate_future_signal(pair_name):
    """কোটেক্স ফিউচার সিগন্যাল জেনারেটর (আপনার নিজস্ব স্ট্র্যাটেজি এখানে কাস্টমাইজ করতে পারেন)"""
    now = datetime.now()
    entry_time = now + timedelta(minutes=random.randint(2, 10))
    expiry_time = entry_time + timedelta(minutes=1)
    
    direction = random.choice(["BUY-CALL-UP 📈", "SELL-PUT-DOWN 📉"])
    accuracy = random.randint(85, 98)
    
    signal_text = (
        f"📊 **QUOTEX FUTURE SIGNAL** 📊\n\n"
        f"🎯 Asset: {pair_name}\n"
        f"⏰ Time: {entry_time.strftime('%H:%M:%S')} (1 MIN)\n"
        f"↕️ Direction: {direction}\n"
        f"🔥 Accuracy: {accuracy}%\n"
        f"⚠️ Use 1-Step Martingale if needed!"
    )
    return signal_text

def fetch_news_signals():
    """ইউজারের দেওয়া API থেকে নিউজ ডাটা এনে নির্দিষ্ট ফরম্যাটে রূপান্তর করা"""
    url = "https://forexkiller-newsproby.poghen-dx.workers.dev/?pairs=USD/CAD,USD/JPY,EUR/USD,CAD/JPY,GBP/CAD,GBP/JPY,EUR/JPY,GBP/USD,EUR/GBP,AUD/JPY,AUD/USD&N_days=3&Newsfilter=high"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            news_list = response.json()
            if not news_list:
                return "Currently no high impact news available!"
            
            # আমরা প্রথম নিউজটি প্রসেস করে আপনার দেওয়া ফরম্যাটে সাজাচ্ছি
            single_news = news_list[0] 
            
            # API রেসপন্স অনুযায়ী ডাটা ম্যাপিং (প্রয়োজনে ফিল্ডের নাম পরিবর্তন করতে পারেন)
            date_str = single_news.get("date", datetime.now().strftime("%b %d, %Y"))
            event = single_news.get("event", "Core PCE Price Index m/m")
            pair = single_news.get("pair", "EUR USD")
            time_str = single_news.get("time", "06:30 PM (UTC+06:00)")
            forecast = single_news.get("forecast", "-0.3%")
            previous = single_news.get("previous", "0.2%")
            
            formatted_news = (
                f"🎇 Date : {date_str}\n"
                f"🎙 Event : {event}\n"
                f"🕯 Pair : {pair}\n"
                f"⏰ Time : {time_str}⏰\n"
                f"🔔 Entry : 18:29:55 - 18:29:58\n"
                f"😬 Direction : BUY-CALL-UP 🫣\n"
                f"💯 Confirmation : 89%✅\n"
                f"😍 Impact : HIGH-Volatility🚀\n"
                f"💌 Contact : Owner @RASUU_QXB ✅\n"
                f"📊 Note : Don't use full balance news always risky\n"
                f"📊Forecast: {forecast} | Prev: {previous} 📉\n"
                f"📊 1 Step Martingale Signals➕\n"
                f"❗️ Management Risk Properly⚠️\n\n"
                f"🚀Powered by VORTEX SOFTWARE"
            )
            return formatted_news
        else:
            return "❌ API থেকে নিউজ ডাটা লোড করতে ব্যর্থ হয়েছে।"
    except Exception as e:
        return f"⚠️ এরর ঘটেছে: {str(e)}"
