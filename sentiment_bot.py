import os
import requests
import telebot
from bs4 import BeautifulSoup
import time

# --- CONFIGURATION (Environment Variables se data uthayega) ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

def fetch_finance_data(ticker):
    """Yahoo Finance se real-time price fetch karne ka function"""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=10).json()
        price = response['chart']['result'][0]['meta']['regularMarketPrice']
        return price
    except:
        return None

def get_market_context(user_input):
    """User ki query ke hisab se prices nikalna"""
    context = ""
    msg = user_input.lower()
    
    # Metal & Forex Mapping
    mapping = {
        "gold": "XAUUSD=X", "xau": "XAUUSD=X", "sona": "XAUUSD=X",
        "silver": "XAGUSD=X", "xag": "XAGUSD=X", "chandi": "XAGUSD=X",
        "platinum": "XPTUSD=X", "xpt": "XPTUSD=X",
        "eurusd": "EURUSD=X", "gbpusd": "GBPUSD=X", "usdjpy": "USDJPY=X"
    }

    for key, ticker in mapping.items():
        if key in msg:
            price = fetch_finance_data(ticker)
            if price:
                context += f"Live {key.upper()} Price: ${price}\n"
    
    # Crypto Check (Binance API)
    for coin in ["btc", "eth", "sol", "bnb"]:
        if coin in msg:
            try:
                r = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={coin.upper()}USDT").json()
                context += f"Live {coin.upper()}: ${float(r['price']):,.2f}\n"
            except: pass
            
    return context

def get_news():
    """Forex Factory se High Impact news scan karna"""
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
        return "\n".join(news_list) if news_list else "No major high impact news for now."
    except:
        return "Market news is being updated..."

def ask_ai(user_input):
    """Groq Llama 3.3 AI with Market Context"""
    market_data = get_market_context(user_input)
    news = get_news()
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    
    system_prompt = (
        "You are Mestrey AI, an expert Financial Analyst developed by Pintu Rajput (@Pinturajput0777). "
        "Use the provided LIVE DATA (Prices & News) to give high-accuracy trading insights. "
        "Analyze crypto whitepapers if text is provided. Be professional and sharp. "
        "Respond in Hinglish."
    )
    
    full_prompt = f"CURRENT MARKET DATA:\n{market_data}\n\nTODAY'S NEWS:\n{news}\n\nUSER QUERY: {user_input}"
    
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
        return "Bhai, server thoda busy lag raha hai. Ek minute baad try karna."

# --- TELEGRAM HANDLERS ---

@bot.message_handler(commands=['start'])
def start(m):
    welcome_text = (
        "🤖 *Mestrey AI v5.0 Ready* 🚀\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Dev: *Pintu Rajput (@Pinturajput0777)*\n\n"
        "Main Live Gold, Silver, Forex aur Crypto prices track karta hoon. "
        "Aap mujhse trading setups ya news impact puch sakte hain."
    )
    bot.reply_to(m, welcome_text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def chat_handler(m):
    bot.send_chat_action(m.chat.id, 'typing')
    response = ask_ai(m.text)
    signature = "\n\n━━━━━━━━━━━━━━\n⚡ *Mestrey AI | Pintu Rajput*"
    bot.reply_to(m, response + signature, parse_mode="Markdown")

if __name__ == "__main__":
    print("🔥 Mestrey AI is starting in Secure Mode...")
    bot.infinity_polling()

