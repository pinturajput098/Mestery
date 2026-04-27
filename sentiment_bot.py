import os
import requests
import telebot
from bs4 import BeautifulSoup
from flask import Flask
from threading import Thread
import time

# --- RENDER ENGINE ---
app = Flask('')
@app.route('/')
def home(): return "Mestrey AI is Online!"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run).start()

# --- CONFIG ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# --- ROBUST PRICE FETCHING ---
def fetch_finance_data(ticker):
    """Yahoo Finance API with robust headers"""
    try:
        # Ticker fix for Yahoo
        url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={ticker}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        res = requests.get(url, headers=headers, timeout=10).json()
        price = res['quoteResponse']['result'][0]['regularMarketPrice']
        return price
    except Exception as e:
        print(f"Price Error for {ticker}: {e}")
        return None

def get_market_context(user_input):
    context = ""
    msg = user_input.lower()
    mapping = {
        "gold": "XAUUSD=X", "xau": "XAUUSD=X", "sona": "XAUUSD=X",
        "silver": "XAGUSD=X", "xag": "XAGUSD=X", "chandi": "XAGUSD=X",
        "eur": "EURUSD=X", "gbp": "GBPUSD=X", "jpy": "USDJPY=X"
    }
    for key, ticker in mapping.items():
        if key in msg:
            p = fetch_finance_data(ticker)
            if p: context += f"🔴 LIVE {key.upper()} PRICE: ${p}\n"
    
    # Crypto Backup
    for coin in ["btc", "eth", "sol"]:
        if coin in msg:
            try:
                r = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={coin.upper()}USDT").json()
                context += f"🔵 LIVE {coin.upper()} PRICE: ${float(r['price']):,.2f}\n"
            except: pass
    return context

# --- REAL-TIME NEWS FETCHING ---
def get_news():
    """Forex Factory High Impact News Analysis"""
    try:
        url = "https://www.forexfactory.com/calendar"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.content, 'html.parser')
        rows = soup.find_all('tr', class_='calendar__row--high-impact')
        news_data = []
        for row in rows[:5]:
            curr = row.find('td', class_='calendar__currency').text.strip()
            event = row.find('span', class_='calendar__event-title').text.strip()
            news_data.append(f"🔥 [{curr}] {event}")
        return "\n".join(news_data) if news_data else "No High Impact News right now."
    except:
        return "News sources temporarily unavailable."

def ask_ai(user_input):
    market_data = get_market_context(user_input)
    news = get_news()
    
    # AI Prompt ko 'FORCE' karna ki wo LIVE DATA hi use kare
    system_prompt = (
        "You are Mestrey AI, a pro trader bot by Pintu Rajput. "
        "IMPORTANT: Only use the 'PROVIDED DATA' below for prices. "
        "If you see a price in 'PROVIDED DATA', that is the ABSOLUTE current price. "
        "NEVER say $1947 for Gold if the data says something else. "
        "Give trading signals based on News and Prices provided. "
        "Respond in sharp, professional Hinglish."
    )
    
    context = f"--- PROVIDED LIVE DATA ---\n{market_data}\n\n--- TODAY'S NEWS ---\n{news}\n\nUSER QUESTION: {user_input}"
    
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
        return "Bhai server down hai, thodi der mein check kar."

@bot.message_handler(func=lambda m: True)
def handle(m):
    bot.send_chat_action(m.chat.id, 'typing')
    ans = ask_ai(m.text)
    bot.reply_to(m, ans + "\n\n━━━━━━━━━━━━━━\n⚡ Mestrey AI | @Pinturajput0777", parse_mode="Markdown")

if __name__ == "__main__":
    keep_alive()
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except:
            time.sleep(10)

