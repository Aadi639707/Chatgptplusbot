import os
import telebot
from groq import Groq
from flask import Flask
from threading import Thread

# Flask App setup
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Environment Variables
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "I am 24/7 Online! Ask me anything.")

@bot.message_handler(func=lambda message: True)
def chat(message):
    try:
        # Client ko try ke andar rakha hai taaki key error pakda jaye
        client = Groq(api_key=os.environ.get('GROQ_API_KEY'))
        
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": message.text}],
            model="llama3-8b-8192",
        )
        bot.reply_to(message, response.choices[0].message.content)
    except Exception as e:
        # Ye line aapko batayegi ki asli problem kya hai
        bot.reply_to(message, f"❌ Groq Error: {str(e)}")

if __name__ == "__main__":
    keep_alive()
    print("Bot is starting...")
    bot.infinity_polling()
    
