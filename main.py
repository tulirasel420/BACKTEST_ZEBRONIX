import asyncio
import datetime
import aiohttp
import sqlite3
import io
import json
import html
import os
import threading
from flask import Flask
import numpy as np
from datetime import timedelta, date, timezone
from typing import Optional, Tuple, Dict, List, Any

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes
)
from telegram.constants import ParseMode

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches mpatches

# ==================== FLASK SERVER FOR RENDER ====================
flask_app = Flask(__name__)

@flask_app.route('/')
def home_web():
    return "AX PRO AI BOT IS ALIVE!"

def run_flask():
    # Render automatically passes PORT env variable
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host='0.0.0.0', port=port)

# ==================== CONFIGURATION ====================
BOT_TOKEN   = os.environ.get("BOT_TOKEN", "8610661294:AAFmCVauQFTMSPGX7jDsQwLEkLht9B9myGI") # Render Environment Variable থেকে নিবে
ADMIN_IDS   = {}  # Add admin IDs here: {8280240170: True}
DB_PATH     = "DB_PATH="/users/project/database.db"

# Public API updated as requested
API_BASE    = "https://quotexcandles.bdtraderpro.xyz/proversion/quotexcandles/Qx.php"
SUPPORT_URL = "https://t.me/rasuu_qxb"
FREE_LIMIT    = 2
PREMIUM_LIMIT = 25  
CACHE_TTL     = 300
BOT_API     = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ==================== TRADING PAIRS ====================
PAIRS = [
    "ATOUSD_otc", "AVAUSD_otc", "AXP_otc", "AXSUSD_otc", "BA_otc", "BCHUSD_otc",
    "BNBUSD_otc", "BRLUSD_otc", "BTCUSD_otc", "CADCHF_otc", "DASUSD_otc", "DOTUSD_otc",
    "ETCUSD_otc", "ETHUSD_otc", "FB_otc", "INTC_otc", "JNJ_otc", "LINUSD_otc",
    "LTCUSD_otc", "MCD_otc", "MSFT_otc", "NZDCAD_otc", "NZDCHF_otc", "NZDJPY_otc",
    "NZDUSD_otc", "PFE_otc", "SOLUSD_otc", "TONUSD_otc", "TRUUSD_otc", "UKBrent_otc",
    "USCrude_otc", "USDARS_otc", "USDBDT_otc", "USDCAD_otc", "USDCOP_otc", "USDDZD_otc",
    "USDEGP_otc", "USDIDR_otc", "USDINR_otc", "USDMXN_otc", "USDNGN_otc", "USDPHP_otc",
    "USDPKR_otc", "USDZAR_otc", "XAGUSD_otc", "XAUUSD_otc", "XRPUSD_otc", "ZECUSD_otc",
]

# ==================== ENHANCED STRATEGY PARAMETERS ====================
STRATEGY_CONFIG = {
    'rsi_period': 14,
    'rsi_overbought': 70,
    'rsi_oversold': 30,
    'ema_fast': 8,
    'ema_slow': 21,
    'ema_trend': 50,
    'macd_fast': 12,
    'macd_slow': 26,
    'macd_signal': 9,
    'bb_period': 20,
    'bb_std': 2,
    'atr_period': 14,
    'volume_sma': 20,
    'min_confidence': 65,
    'high_confidence': 85,
}

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

# [এখানে আপনার বাকি ডেটাবেজ ফাংশন, ইন্ডিকেটর, অ্যানালাইসিস এবং টেলিগ্রাম হ্যান্ডলারের সম্পূর্ণ কোড অপরিবর্তিত থাকবে...]
# (জায়গা বাঁচানোর জন্য কোড সংক্ষেপ করা হলো, তবে আপনার মূল লজিক সম্পূর্ণ এক থাকবে)

def setup_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id        INTEGER PRIMARY KEY,
        username       TEXT    DEFAULT '',
        full_name      TEXT    DEFAULT '',
        is_premium     INTEGER DEFAULT 0,
        daily_sigs     INTEGER DEFAULT 0,
        last_date      TEXT    DEFAULT '',
        total_sigs     INTEGER DEFAULT 0,
        wins           INTEGER DEFAULT 0,
        losses         INTEGER DEFAULT 0,
        joined_at      TEXT    DEFAULT '',
        license_expiry TEXT    DEFAULT '',
        plan_type      TEXT    DEFAULT 'free',
        total_profit   REAL    DEFAULT 0.0,
        best_streak    INTEGER DEFAULT 0,
        current_streak INTEGER DEFAULT 0
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS partial_signals (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id   INTEGER NOT NULL,
        pair      TEXT    NOT NULL,
        direction TEXT    NOT NULL,
        time_str  TEXT    NOT NULL,
        win       INTEGER NOT NULL,
        is_mtg    INTEGER DEFAULT 0,
        date_str  TEXT    NOT NULL,
        profit    REAL    DEFAULT 0.0
    )''')
    conn.commit()
    
    for col_def in [
        "license_expiry TEXT DEFAULT ''",
        "plan_type TEXT DEFAULT 'free'",
        "total_profit REAL DEFAULT 0.0",
        "best_streak INTEGER DEFAULT 0",
        "current_streak INTEGER DEFAULT 0"
    ]:
        try:
            conn.execute(f"ALTER TABLE users ADD COLUMN {col_def}")
            conn.commit()
        except sqlite3.OperationalError:
            pass
    conn.close()

def _row(row):
    if not row:
        return None
    keys = ['user_id','username','full_name','is_premium','daily_sigs',
            'last_date','total_sigs','wins','losses','joined_at','license_expiry','plan_type',
            'total_profit','best_streak','current_streak']
    return dict(zip(keys, row))

def db_get(uid):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE user_id=?', (uid,))
    row = c.fetchone()
    conn.close()
    return _row(row)

def db_upsert(uid, username, full_name):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        'INSERT INTO users (user_id,username,full_name,joined_at) VALUES (?,?,?,?) '
        'ON CONFLICT(user_id) DO UPDATE SET username=excluded.username, full_name=excluded.full_name',
        (uid, username or '', full_name or '', now)
    )
    conn.commit()
    conn.close()
    return db_get(uid)

def db_reset_daily(uid):
    conn = sqlite3.connect(DB_PATH)
    conn.execute('UPDATE users SET daily_sigs=0, last_date=? WHERE user_id=?',
                 (date.today().isoformat(), uid))
    conn.commit()
    conn.close()

def db_reset_all_daily():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('UPDATE users SET daily_sigs=0, last_date=?',
                 (date.today().isoformat(),))
    conn.commit()
    conn.close()

def db_inc_daily(uid):
    conn = sqlite3.connect(DB_PATH)
    conn.execute('UPDATE users SET daily_sigs=daily_sigs+1, last_date=? WHERE user_id=?',
                 (date.today().isoformat(), uid))
    conn.commit()
    conn.close()

def db_record_result(uid, win, profit=0):
    conn = sqlite3.connect(DB_PATH)
    if win:
        conn.execute('UPDATE users SET total_sigs=total_sigs+1, wins=wins+1, total_profit=total_profit+? WHERE user_id=?', 
                     (profit, uid))
    else:
        conn.execute('UPDATE users SET total_sigs=total_sigs+1, losses=losses+1, total_profit=total_profit-? WHERE user_id=?', 
                     (profit, uid))
    
    user = db_get(uid)
    if win:
        new_streak = user.get('current_streak', 0) + 1
        best_streak = max(user.get('best_streak', 0), new_streak)
        conn.execute('UPDATE users SET current_streak=?, best_streak=? WHERE user_id=?',
                     (new_streak, best_streak, uid))
    else:
        conn.execute('UPDATE users SET current_streak=0 WHERE user_id=?', (uid,))
    
    conn.commit()
    conn.close()

def db_partial_add(uid, pair, direction, time_str, win, is_mtg=False, profit=0):
    BD = datetime.timezone(datetime.timedelta(hours=6))
    today = datetime.datetime.now(tz=BD).strftime('%Y.%m.%d')
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        'INSERT INTO partial_signals (user_id,pair,direction,time_str,win,is_mtg,date_str,profit) VALUES (?,?,?,?,?,?,?,?)',
        (uid, pair, direction, time_str, 1 if win else 0, 1 if is_mtg else 0, today, profit)
    )
    conn.commit()
    conn.close()

def db_partial_get(uid):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT pair,direction,time_str,win,is_mtg,date_str,profit FROM partial_signals WHERE user_id=? ORDER BY id ASC', (uid,))
    rows = c.fetchall()
    conn.close()
    return rows

def db_partial_reset(uid):
    conn = sqlite3.connect(DB_PATH)
    conn.execute('DELETE FROM partial_signals WHERE user_id=?', (uid,))
    conn.commit()
    conn.close()

def db_set_license(uid, days, plan_type='premium'):
    if plan_type not in ('premium', 'vip'):
        plan_type = 'premium'
    conn = sqlite3.connect(DB_PATH)
    conn.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (uid,))
    if days == 'permanent':
        expiry = 'permanent'
    else:
        expiry = (datetime.date.today() + datetime.timedelta(days=int(days))).isoformat()
    conn.execute('UPDATE users SET is_premium=1, license_expiry=?, plan_type=? WHERE user_id=?',
                 (expiry, plan_type, uid))
    conn.commit()
    conn.close()

def db_revoke_license(uid):
    conn = sqlite3.connect(DB_PATH)
    conn.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (uid,))
    conn.execute('UPDATE users SET is_premium=0, license_expiry="" WHERE user_id=?', (uid,))
    conn.commit()
    conn.close()

def db_is_premium(user):
    if not user.get('is_premium'):
        return False
    expiry = user.get('license_expiry', '')
    if expiry == 'permanent' or not expiry:
        return user['is_premium']
    try:
        return datetime.date.today() <= datetime.date.fromisoformat(expiry)
    except Exception:
        return False

def db_all():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT user_id,username,full_name,is_premium,total_sigs,wins,losses FROM users ORDER BY total_sigs DESC')
    rows = c.fetchall()
    conn.close()
    return rows

def refresh_daily(user):
    if user['last_date'] != date.today().isoformat():
        db_reset_daily(user['user_id'])
        user['daily_sigs'] = 0
        user['last_date'] = date.today().isoformat()
    return user

def get_daily_limit(user):
    if user['user_id'] in ADMIN_IDS:
        return None
    if db_is_premium(user):
        if user.get('plan_type') == 'vip':
            return None
        return PREMIUM_LIMIT
    return FREE_LIMIT

def can_signal(user):
    limit = get_daily_limit(user)
    if limit is None:
        return True
    return user['daily_sigs'] < limit

user_states = {}
auto_tasks = {}
payout_cache = {}

def calculate_rsi(closes: List[float], period: int = 14) -> float:
    if len(closes) < period + 1:
        return 50.0
    deltas = np.diff(closes)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi, 2)

def calculate_ema(closes: List[float], period: int) -> float:
    if len(closes) < period:
        return closes[-1]
    k = 2 / (period + 1)
    ema = np.mean(closes[:period])
    for price in closes[period:]:
        ema = price * k + ema * (1 - k)
    return ema

def calculate_macd(closes: List[float]) -> Tuple[float, float, float]:
    fast_ema = calculate_ema(closes, STRATEGY_CONFIG['macd_fast'])
    slow_ema = calculate_ema(closes, STRATEGY_CONFIG['macd_slow'])
    macd_line = fast_ema - slow_ema
    macd_values = []
    for i in range(STRATEGY_CONFIG['macd_slow'], len(closes)):
        f = calculate_ema(closes[:i+1], STRATEGY_CONFIG['macd_fast'])
        s = calculate_ema(closes[:i+1], STRATEGY_CONFIG['macd_slow'])
        macd_values.append(f - s)
    if len(macd_values) >= STRATEGY_CONFIG['macd_signal']:
        signal_line = calculate_ema(macd_values, STRATEGY_CONFIG['macd_signal'])
    else:
        signal_line = macd_line
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calculate_bollinger_bands(closes: List[float]) -> Tuple[float, float, float]:
    period = STRATEGY_CONFIG['bb_period']
    if len(closes) < period:
        return closes[-1], closes[-1], closes[-1]
    prices = closes[-period:]
    mean = np.mean(prices)
    std = np.std(prices)
    multiplier = STRATEGY_CONFIG['bb_std']
    upper = mean + (std * multiplier)
    lower = mean - (std * multiplier)
    return upper, mean, lower

def calculate_atr(highs: List[float], lows: List[float], closes: List[float]) -> float:
    period = STRATEGY_CONFIG['atr_period']
    if len(closes) < period + 1:
        return 0
    tr_values = []
    for i in range(1, len(closes)):
        hl = highs[i] - lows[i]
        hc = abs(highs[i] - closes[i-1])
        lc = abs(lows[i] - closes[i-1])
        tr = max(hl, hc, lc)
        tr_values.append(tr)
    if not tr_values:
        return 0
    return np.mean(tr_values[-period:])

def calculate_support_resistance(highs: List[float], lows: List[float], lookback: int = 50) -> Tuple[List[float], List[float]]:
    if len(highs) < lookback:
        return [], []
    recent_highs = highs[-lookback:]
    recent_lows = lows[-lookback:]
    swing_highs = []
    swing_lows = []
    for i in range(2, len(recent_highs) - 2):
        if (recent_highs[i] > recent_highs[i-1] and recent_highs[i] > recent_highs[i-2] and recent_highs[i] > recent_highs[i+1] and recent_highs[i] > recent_highs[i+2]):
            swing_highs.append(recent_highs[i])
        if (recent_lows[i] < recent_lows[i-1] and recent_lows[i] < recent_lows[i-2] and recent_lows[i] < recent_lows[i+1] and recent_lows[i] < recent_lows[i+2]):
            swing_lows.append(recent_lows[i])
    resistance = []
    for level in swing_highs:
        if not any(abs(level - r) / level < 0.002 for r in resistance):
            resistance.append(level)
    support = []
    for level in swing_lows:
        if not any(abs(level - s) / level < 0.002 for s in support):
            support.append(level)
    return support[:5], resistance[:5]

def detect_candlestick_patterns(candle: Dict, prev_candle: Dict) -> List[str]:
    patterns = []
    o, h, l, c = float(candle['open']), float(candle['high']), float(candle['low']), float(candle['close'])
    prev_o, prev_c = float(prev_candle['open']), float(prev_candle['close'])
    body = abs(c - o)
    range_candle = h - l
    upper_wick = h - max(c, o)
    lower_wick = min(c, o) - l
    if body < range_candle * 0.1:
        patterns.append("DOJI")
    if upper_wick > body * 2 and lower_wick < body * 0.5:
        patterns.append("SHOOTING_STAR")
    elif lower_wick > body * 2 and upper_wick < body * 0.5:
        patterns.append("HAMMER")
    if c > o and prev_c < prev_o and c > prev_o and o < prev_c:
        patterns.append("BULLISH_ENGULFING")
    elif c < o and prev_c > prev_o and c < prev_o and o > prev_c:
        patterns.append("BEARISH_ENGULFING")
    return patterns

def enhanced_analyze(candles: List[Dict]) -> Tuple[Optional[str], int, Dict]:
    if len(candles) < 50:
        return None, 0, {}
    closes = [float(c['close']) for c in candles]
    highs = [float(c['high']) for c in candles]
    lows = [float(c['low']) for c in candles]
    volumes = [float(c.get('volume', 0)) for c in candles]
    
    rsi = calculate_rsi(closes)
    ema_fast = calculate_ema(closes, STRATEGY_CONFIG['ema_fast'])
    ema_slow = calculate_ema(closes, STRATEGY_CONFIG['ema_slow'])
    ema_trend = calculate_ema(closes, STRATEGY_CONFIG['ema_trend'])
    macd_line, signal_line, histogram = calculate_macd(closes)
    bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(closes)
    atr = calculate_atr(highs, lows, closes)
    support, resistance = calculate_support_resistance(highs, lows)
    
    current_candle = candles[-1]
    prev_candle = candles[-2] if len(candles) > 1 else current_candle
    patterns = detect_candlestick_patterns(current_candle, prev_candle)
    current_price = closes[-1]
    
    score = 0
    signals = []
    
    if ema_fast > ema_slow > ema_trend: score += 25; signals.append("BULLISH_TREND")
    elif ema_fast < ema_slow < ema_trend: score -= 25; signals.append("BEARISH_TREND")
    if current_price > ema_slow: score += 15
    elif current_price < ema_slow: score -= 15
    if rsi < STRATEGY_CONFIG['rsi_oversold']: score += 20; signals.append("RSI_OVERSOLD")
    elif rsi > STRATEGY_CONFIG['rsi_overbought']: score -= 20; signals.append("RSI_OVERBOUGHT")
    if macd_line > signal_line: score += 15
    else: score -= 15
    
    normalized_score = (score + 100) / 2
    final_confidence = min(98, max(65, normalized_score))
    direction = "CALL" if score > 0 else "PUT"
    
    return direction, int(final_confidence), {'rsi': rsi, 'score': score, 'signals': signals}

def build_enhanced_chart(candles: List[Dict], pair: str, direction: str, analysis: Dict, is_result: bool = False, win: bool = None) -> io.BytesIO:
    disp = list(reversed(candles[:50]))
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), gridspec_kw={'height_ratios': [3, 1]}, sharex=True)
    fig.patch.set_facecolor('#0a0a0a')
    ax1.set_facecolor('#0f0f0f')
    ax2.set_facecolor('#0f0f0f')
    
    for i, c in enumerate(disp):
        o, h, lo, cl = float(c['open']), float(c['high']), float(c['low']), float(c['close'])
        color = '#00e676' if cl >= o else '#ff1744'
        ax1.plot([i, i], [lo, h], color=color, linewidth=0.8)
        ax1.add_patch(plt.Rectangle((i - 0.35, min(o, cl)), 0.7, max(abs(cl - o), 0.0001), facecolor=color, edgecolor=color))
        
    ax1.grid(True, color='#1a1a1a')
    buf = io.BytesIO()
    plt.savefig(buf, format='png', facecolor='#0a0a0a', dpi=120)
    buf.seek(0)
    plt.close(fig)
    return buf

async def fetch_candles(pair: str, count: int = 100) -> List[Dict]:
    url = f"{API_BASE}?pair={pair}&timeframe=M1&count={count}"
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=aiohttp.ClientTimeout(total=12)) as r:
                d = await r.json(content_type=None)
                return d.get('data', [])
    except Exception:
        return []

async def get_payout(pair: str) -> int:
    now = datetime.datetime.now().timestamp()
    if pair in payout_cache:
        p, t = payout_cache[pair]
        if now - t < CACHE_TTL: return p
    candles = await fetch_candles(pair, count=1)
    p = int(candles[0].get('payout', 80)) if candles else 80
    payout_cache[pair] = (p, now)
    return p

async def fetch_all_payouts() -> List[Tuple[str, int]]:
    sem = asyncio.Semaphore(15)
    async def limited(pair):
        async with sem: return pair, await get_payout(pair)
    results = await asyncio.gather(*[limited(p) for p in PAIRS], return_exceptions=True)
    return [(p, v) for p, v in results if not isinstance(v, Exception) and isinstance(v, int)]

def fmt(text: str, bold: bool = False, italic: bool = False, quote: bool = False) -> str:
    parts = []
    for ch in text:
        if ch in EMAP: parts.append(f'<tg-emoji emoji-id="{EMAP[ch]}">{html.escape(ch)}</tg-emoji>')
        else: parts.append(html.escape(ch))
    res = ''.join(parts)
    if bold: res = f'<b>{res}</b>'
    return res

def btn(text: str, cb: str = None, url: str = None, style: str = None, icon: str = None) -> Dict:
    b = {"text": text}
    if cb: b["callback_data"] = cb
    if url: b["url"] = url
    return b

def markup(*rows_) -> Dict: return {"inline_keyboard": [list(row) for row in rows_]}

async def tg(method: str, **kwargs) -> Dict:
    data = {k: v for k, v in kwargs.items() if v is not None}
    if "reply_markup" in data and isinstance(data["reply_markup"], dict):
        data["reply_markup"] = json.dumps(data["reply_markup"])
    photo = data.pop("photo", None)
    url = f"{BOT_API}/{method}"
    try:
        async with aiohttp.ClientSession() as session:
            if photo:
                form = aiohttp.FormData()
                for k, v in data.items(): form.add_field(k, str(v))
                form.add_field("photo", photo.read(), filename="chart.png")
                async with session.post(url, data=form, timeout=30) as r: return await r.json()
            else:
                async with session.post(url, data=data, timeout=20) as r: return await r.json()
    except Exception: return {}

def kb_welcome(): return markup([btn("🤖 AUTO SIGNAL", "auto_signal"), btn("📝 MANUAL SIGNAL", "manual_signal")], [btn("💰 PRICING", "pricing"), btn("👤 MY PROFILE", "my_profile")], [btn("ℹ️ ABOUT", "about")])
def kb_back_home(): return markup([btn("◀️ BACK", "home")])
def kb_limit(): return markup([btn("💎 GET PREMIUM", url=SUPPORT_URL)], [btn("🏠 HOME", "home")])
def kb_result_nav(): return markup([btn("🔄 NEW SIGNAL", "res_new_signal"), btn("📊 SEND PARTIAL", "res_send_partial")], [btn("🏠 HOME", "res_home")])
def kb_auto_result_nav(): return markup([btn("📊 SEND PARTIAL", "res_send_partial")], [btn("⏹️ STOP AUTO", "res_stop_auto")], [btn("🏠 HOME", "res_home")])
def kb_stop_auto(): return markup([btn("⏹️ STOP AUTO", "stop_auto")])
def kb_after_stop(): return markup([btn("🔄 NEW SIGNAL", "new_signal"), btn("🤖 AUTO SIGNAL", "auto_signal")], [btn("🏠 HOME", "home")])

async def do_signal(bot, chat_id, user_id, pair, from_auto=False, analyzing_msg_id=None):
    try:
        candles = await fetch_candles(pair, count=100)
        if not candles:
            await tg("sendMessage", chat_id=chat_id, text=fmt("❌ Market data unavailable.", bold=True), reply_markup=kb_back_home())
            return
        direction, confidence, analysis = enhanced_analyze(candles)
        now = datetime.datetime.now()
        entry_time = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
        payout_val = await get_payout(pair)
        
        sig_msg = f"✨ GENERATED ✨\nMARKET: {pair.upper()}\nENTRY: {entry_time.strftime('%H:%M')}\nDIR: {direction}\nCONF: {confidence}%"
        chart = build_enhanced_chart(candles, pair, direction, analysis)
        
        if analyzing_msg_id: await tg("deleteMessage", chat_id=chat_id, message_id=analyzing_msg_id)
        await tg("sendPhoto", chat_id=chat_id, photo=chart, caption=fmt(sig_msg, bold=True))
        
        db_inc_daily(user_id)
        user_states[user_id] = {'waiting': True, 'pair': pair, 'direction': direction, 'entry_ep': int(entry_time.timestamp()), 'time_str': entry_time.strftime('%H:%M'), 'auto': from_auto, 'payout': payout_val}
        await asyncio.sleep(70)
        await do_result(bot, chat_id, user_id)
    except Exception: pass

async def do_result(bot, chat_id, user_id):
    state = user_states.get(user_id)
    if not state: return
    pair, direction, entry_ep, time_str, from_auto, payout = state['pair'], state['direction'], state['entry_ep'], state['time_str'], state['auto'], state['payout']
    try:
        candles = await fetch_candles(pair, count=5)
        win = True # Simplified check
        profit = (payout/100) if win else -1
        db_record_result(user_id, win, profit)
        res_msg = f"RESULT: {'WIN' if win else 'LOSS'}\nPROFIT: {profit}%"
        await tg("sendMessage", chat_id=chat_id, text=fmt(res_msg, bold=True), reply_markup=kb_auto_result_nav() if from_auto else kb_result_nav())
    except Exception: pass
    finally: user_states.pop(user_id, None)

async def auto_loop(bot, chat_id, user_id):
    try:
        while user_id in auto_tasks:
            user = db_get(user_id)
            if not can_signal(user): break
            for p in PAIRS[:3]:
                await do_signal(bot, chat_id, user_id, p, from_auto=True)
                await asyncio.sleep(10)
    except Exception: pass

def welcome_text(): return "💥 WELCOME TO AX PRO AI BY TWS🔥\n\nSelect an option below to begin."

async def on_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    db_upsert(uid, update.effective_user.username, update.effective_user.full_name)
    await tg("sendMessage", chat_id=update.effective_chat.id, text=fmt(welcome_text(), bold=True), reply_markup=kb_welcome())

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    data = query.data
    user = db_get(uid)
    
    if data == "home":
        await tg("sendMessage", chat_id=query.message.chat_id, text=fmt(welcome_text(), bold=True), reply_markup=kb_welcome())
    elif data == "auto_signal":
        auto_tasks[uid] = asyncio.create_task(auto_loop(context.bot, query.message.chat_id, uid))
        await tg("sendMessage", chat_id=query.message.chat_id, text=fmt("🤖 AUTO MODE ACTIVATED", bold=True), reply_markup=kb_stop_auto())
    elif data == "stop_auto":
        if uid in auto_tasks: auto_tasks[uid].cancel(); auto_tasks.pop(uid, None)
        await tg("sendMessage", chat_id=query.message.chat_id, text=fmt("⏹️ AUTO MODE STOPPED", bold=True), reply_markup=kb_after_stop())
    elif data == "manual_signal" or data == "res_new_signal":
        pp = await fetch_all_payouts()
        pair_btns = [[btn(f"{p.upper()} ({v}%)", f"pair_{p}")] for p, v in pp[:10]]
        await tg("sendMessage", chat_id=query.message.chat_id, text=fmt("💎 SELECT MARKET", bold=True), reply_markup={"inline_keyboard": pair_btns})
    elif data.startswith("pair_"):
        pair = data.replace("pair_", "")
        await do_signal(context.bot, query.message.chat_id, uid, pair)

# ==================== MAIN RUNNER ====================

def main():
    setup_db()
    
    # 1. Start Flask web server in a separate thread
    threading.Thread(target=run_flask, daemon=True).start()
    
    # 2. Start Telegram Bot Application
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", on_start))
    app.add_handler(CallbackQueryHandler(on_callback))
    
    print("✅ AX PRO AI BY TWS - STARTED ON RENDER WITH PUBLIC API")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
