import os
import telebot
from groq import Groq

# Get keys from Environment Variables
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_API_KEY)

# Command: /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🚀 Groq AI Bot is Online! Ask me anything.")

# Command: /img (Using Pollinations as it's free)
@bot.message_handler(commands=['img'])
def send_image(message):
    prompt = message.text.replace("/img", "").strip()
    if not prompt:
        bot.reply_to(message, "Please provide a prompt. Example: /img space cat")
        return
    
    image_url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?nologo=true"
    bot.send_photo(message.chat.id, image_url, caption=f"Generated: {prompt}")

# Handle All Messages
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": message.text}],
            model="llama3-8b-8192",
        )
        bot.reply_to(message, chat_completion.choices[0].message.content)
    except Exception as e:
        bot.reply_to(message, "⚠️ System Busy. Try again later.")

print("Bot is starting...")
bot.infinity_polling()
