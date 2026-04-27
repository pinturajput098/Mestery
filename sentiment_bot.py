import os
import requests
import telebot
from bs4 import BeautifulSoup
from flask import Flask
from threading import Thread
import time

# --- RENDER KEEP-ALIVE ENGINE ---
# Render ko 'Web Service' ki tarah dikhane ke liye Flask zaruri hai
app = Flask('')

@app.route('/')
def home():
    return "Mestrey AI is Online and Running 24/7!"

def run():
    # Render automatically port assign karta hai
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- CONFIGURATION (Render Dashboard se uthayega) ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# --- MARKET DATA FUNCTIONS ---

def fetch_finance_data(ticker):
    """Yahoo Finance JSON API se price nikalna"""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=10).json()
        price = response['chart']['result'][0]['meta']['regularMarketPrice']
        return price
    except:
        return None

def get_market_context(user_input):
    """User ki query ke hisab se prices context banana"""
    context = ""
    msg = user_input.lower()
    
    mapping = {
        "gold": "XAUUSD=X", "xau": "XAUUSD=X", "sona": "XAUUSD=X",
        "silver": "XAGUSD=X", "xag": "XAGUSD=X", "chandi": "XAGUSD=X",
        "platinum": "XPTUSD=X", "xpt": "XPTUSD=X",
        "eurusd": "EURUSD=X", "gbpusd": "GBPUSD=X"
    }

    for key, ticker in mapping.items():
        if key in msg:
            price = fetch_finance_data(ticker)
            if price:
                context += f"Live {key.upper()} Price: ${price}\n"
    
    # BTC/ETH for Crypto
    for coin in ["btc", "eth", "sol"]:
        if coin in msg:
            try:
                r = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={coin.upper()}USDT").json()
                context += f"Live {coin.upper()}: ${float(r['price']):,.2f}\n"
            except: pass
            
    return context

def get_news():
    """Forex Factory se High Impact news fetch karna"""
    try:
        url = "https://www.forexfactory.com/calendar"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.content, 'html.parser')
        events = soup.find_all('tr', class_='calendar__row--high-impact')
        news_list = []
        for e in events[:5]:
            curr = e.find('td', class_='calendar__currency').text.strip()
            title = e.find('span', class_='calendar__event-title').text.strip()
            news_list.append(f"🔴 [{curr}] {title}")
        return "\n".join(news_list) if news_list else "No high impact news right now."
    except:
        return "Market news is updating..."

def ask_ai(user_input):
    """Groq AI Logic"""
    market_data = get_market_context(user_input)
    news = get_news()
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    
    system_prompt = (
        "You are Mestrey AI, a professional analyst developed by Pintu Rajput (@Pinturajput0777). "
        "Use provided LIVE DATA for accuracy. Respond in professional Hinglish. "
        "If whitepaper text is provided, analyze its utility and tokenomics."
    )
    
    full_prompt = f"DATA:\n{market_data}\nNEWS:\n{news}\n\nUSER: {user_input}"
    
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_prompt}
        ]
    }
    
    try:
        res = requests.post(url, headers=headers, json=data, timeout=20).json()
        return res['choices'][0]['message']['content']
    except:
        return "Bhai server busy hai, thodi der mein try kar."

# --- HANDLERS ---

@bot.message_handler(commands=['start'])
def start(m):
    welcome = (
        "🤖 *Mestrey AI v5.1 (Render)* 🚀\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Dev: *Pintu Rajput (@Pinturajput0777)*\n\n"
        "Main 24/7 active hoon. Gold, Silver aur Crypto prices ke liye puchiye!"
    )
    bot.reply_to(m, welcome, parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def handle_chat(m):
    bot.send_chat_action(m.chat.id, 'typing')
    ans = ask_ai(m.text)
    signature = "\n\n━━━━━━━━━━━━━━\n⚡ *Mestrey AI | Pintu Rajput*"
    bot.reply_to(m, ans + signature, parse_mode="Markdown")

# --- MAIN LOOP ---

if __name__ == "__main__":
    # Flask ko background thread mein chalao
    keep_alive() 
    
    print("🚀 Mestrey AI is starting on Render...")
    
    # Polling loop with error handling
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"Polling Error: {e}")
            time.sleep(15) # Error aane par 15 sec wait karke restart

