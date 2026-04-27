import os
import requests
import telebot
from bs4 import BeautifulSoup
from flask import Flask
from threading import Thread

# --- RENDER KEEP-ALIVE SERVER ---
app = Flask('')

@app.route('/')
def home():
    return "Mestrey AI is running 24/7!"

def run():
    # Render assigns a port automatically
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- BOT CONFIGURATION ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

def fetch_finance_data(ticker):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10).json()
        return response['chart']['result'][0]['meta']['regularMarketPrice']
    except:
        return None

def ask_ai(user_input):
    # (Market data logic wahi purani v5 wali hi hai)
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    
    system_prompt = "You are Mestrey AI by Pintu Rajput (@Pinturajput0777). Respond in Hinglish."
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
    }
    try:
        res = requests.post(url, headers=headers, json=data, timeout=20).json()
        return res['choices'][0]['message']['content']
    except:
        return "Bhai, server busy hai. Wait kar."

@bot.message_handler(func=lambda m: True)
def chat_handler(m):
    bot.send_chat_action(m.chat.id, 'typing')
    ans = ask_ai(m.text)
    bot.reply_to(m, ans + "\n\n━━━━━━━━━━━━━━\n⚡ *Mestrey AI | @Pinturajput0777*")

if __name__ == "__main__":
    keep_alive() # Ye bot ko Render par sote waqt jagayega
    print("🔥 Render Deploy Mode Active...")
    bot.infinity_polling()

