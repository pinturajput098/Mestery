import os
import requests
import telebot
from flask import Flask
from threading import Thread
import time

app = Flask('')
@app.route('/')
def home(): return "Mestrey AI (API Mode) is Online!"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run).start()

# --- CONFIG ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TD_API_KEY = os.getenv("TWELVE_DATA_API_KEY") # Nayi API Key variable

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

def get_metal_price(symbol):
    """Twelve Data API se accurate price lena"""
    try:
        # XAU/USD conversion
        api_symbol = "XAU/USD" if symbol == "XAUUSD=X" else "XAG/USD" if symbol == "XAGUSD=X" else symbol
        url = f"https://api.twelvedata.com/price?symbol={api_symbol}&apikey={TD_API_KEY}"
        res = requests.get(url, timeout=10).json()
        return float(res['price'])
    except Exception as e:
        print(f"API Error: {e}")
        return None

def get_market_context(user_input):
    context = ""
    msg = user_input.lower()
    mapping = {
        "gold": "XAUUSD=X", "xau": "XAUUSD=X", "sona": "XAUUSD=X",
        "silver": "XAGUSD=X", "xag": "XAGUSD=X", "chandi": "XAGUSD=X"
    }
    for key, ticker in mapping.items():
        if key in msg:
            p = get_metal_price(ticker)
            if p: context += f"🔴 LIVE {key.upper()} PRICE: ${p:.2f}\n"
    
    # Forex Backup (Binance filters forex, Twelve Data handles it)
    if "eur" in msg or "gbp" in msg:
        pair = "EUR/USD" if "eur" in msg else "GBP/USD"
        p = get_metal_price(pair)
        if p: context += f"🔵 LIVE {pair} PRICE: ${p:.5f}\n"
            
    return context

def ask_ai(user_input):
    market_data = get_market_context(user_input)
    
    system_prompt = (
        "You are Mestrey AI, a professional trading assistant by Pintu Rajput. "
        "Use the PROVIDED DATA for current prices. Respond in Hinglish. "
        "If market data is present, analyze it professionally."
    )
    
    # Agar data nahi mila, toh AI ko batao ki wo check kare
    if not market_data:
        market_data = "Price data currently unavailable from API."

    context = f"--- LIVE DATA ---\n{market_data}\n\nUSER: {user_input}"
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": context}]
    }
    try:
        res = requests.post(url, headers=headers, json=data, timeout=20).json()
        return res['choices'][0]['message']['content']
    except:
        return "Bhai server thoda slow hai, dobara try kar."

@bot.message_handler(func=lambda m: True)
def handle(m):
    bot.send_chat_action(m.chat.id, 'typing')
    ans = ask_ai(m.text)
    bot.reply_to(m, ans + "\n\n━━━━━━━━━━━━━━\n⚡ Mestrey AI | @Pinturajput0777")

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()

