import os
import requests
import telebot
from flask import Flask
from threading import Thread
import time

# --- RENDER SERVER ---
app = Flask('')
@app.route('/')
def home(): return "Mestrey AI v5.4 is LIVE!"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run).start()

# --- CONFIG ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TD_API_KEY = os.getenv("TWELVE_DATA_API_KEY")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# --- REAL-TIME DATA FETCHERS ---

def get_crypto_price(symbol):
    """Binance Public API (No Key Needed)"""
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol.upper()}USDT"
        res = requests.get(url, timeout=10).json()
        return f"${float(res['price']):,.2f}"
    except:
        return None

def get_metal_forex_price(symbol):
    """Twelve Data API for Gold & Forex"""
    if not TD_API_KEY: return None
    try:
        # Ticker fix
        pair = "XAU/USD" if "XAU" in symbol else "XAG/USD" if "XAG" in symbol else symbol
        url = f"https://api.twelvedata.com/price?symbol={pair}&apikey={TD_API_KEY}"
        res = requests.get(url, timeout=10).json()
        if 'price' in res:
            return f"${float(res['price']):.2f}"
        return None
    except:
        return None

def get_market_context(user_input):
    context = ""
    msg = user_input.lower()
    
    # Metal Mapping
    if any(x in msg for x in ["gold", "xau", "sona"]):
        p = get_metal_forex_price("XAUUSD")
        if p: context += f"🔴 LIVE GOLD PRICE: {p}\n"
    
    if any(x in msg for x in ["silver", "xag", "chandi"]):
        p = get_metal_forex_price("XAGUSD")
        if p: context += f"⚪ LIVE SILVER PRICE: {p}\n"

    # Crypto Mapping
    for coin in ["btc", "eth", "sol"]:
        if coin in msg:
            p = get_crypto_price(coin)
            if p: context += f"🔵 LIVE {coin.upper()} PRICE: {p}\n"
            
    return context

def ask_ai(user_input):
    market_data = get_market_context(user_input)
    
    system_prompt = (
        "You are Mestrey AI, a professional financial bot by Pintu Rajput. "
        "Strictly use the 'LIVE DATA' provided for current prices. "
        "If data is provided, analyze it. If not, say prices are being updated. "
        "Respond in professional Hinglish."
    )
    
    full_prompt = f"--- LIVE DATA ---\n{market_data if market_data else 'No live data found.'}\n\nUSER: {user_input}"
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": full_prompt}]
    }
    try:
        res = requests.post(url, headers=headers, json=data, timeout=20).json()
        return res['choices'][0]['message']['content']
    except:
        return "Bhai, AI server response nahi de raha. Thoda wait kar."

# --- HANDLERS ---

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "🤖 *Mestrey AI v5.4 Ready* 🚀\nXAUUSD, BTC, aur News ke liye pucho!", parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def handle(m):
    bot.send_chat_action(m.chat.id, 'typing')
    ans = ask_ai(m.text)
    bot.reply_to(m, ans + "\n\n━━━━━━━━━━━━━━\n⚡ *Mestrey AI | Pintu Rajput*")

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()

