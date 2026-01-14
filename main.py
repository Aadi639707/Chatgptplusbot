import os
import telebot
from groq import Groq
from flask import Flask
from threading import Thread

# 1. Flask App for 24/7 Uptime
app = Flask('')

@app.route('/')
def home():
    return "Bot is running perfectly!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# 2. API Keys
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

bot = telebot.TeleBot(BOT_TOKEN)

# 3. Handlers
@bot.message_handler(commands=['start'])
def start(message):
    # Professional English Start Message
    bot.reply_to(message, "Hello! I am your AI Assistant. I can speak many languages. How can I help you today?")

@bot.message_handler(func=lambda message: True)
def chat(message):
    try:
        client = Groq(api_key=os.environ.get('GROQ_API_KEY'))
        
        # AI will automatically detect user's language and reply in the same
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": message.text}],
            model="llama3-8b-8192",
        )
        bot.reply_to(message, response.choices[0].message.content)
        
    except Exception as e:
        # Error message in English for debugging
        error_str = str(e)
        if "api_key" in error_str.lower():
            bot.reply_to(message, "⚠️ Configuration Error: Invalid API Key. Please check Render settings.")
        else:
            bot.reply_to(message, f"⚠️ System Error: {error_str[:100]}")

# 4. Run
if __name__ == "__main__":
    keep_alive()
    print("Bot is starting...")
    bot.infinity_polling()
    
