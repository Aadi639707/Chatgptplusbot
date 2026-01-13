import os
import telebot
from groq import Groq

# Keys Replit ke Secrets se aayengi
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_API_KEY)

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "Main AI Assistant hoon! \n\n- Kuch bhi puchiye.\n- Image banane ke liye likhein: /img [aapki soch]")

# Image Generation Command: /img prompt
@bot.message_handler(commands=['img'])
def send_image(message):
    prompt = message.text.replace("/img", "").strip()
    if not prompt:
        bot.reply_to(message, "Kripya prompt likhein. Example: /img a futuristic city")
        return
    
    bot.send_chat_action(message.chat.id, 'upload_photo')
    # Free Image Generator URL
    image_url = f"https://pollinations.ai/p/{prompt.replace(' ', '%20')}?width=1024&height=1024&seed=42&nologo=true"
    
    try:
        bot.send_photo(message.chat.id, image_url, caption=f"Ye rahi aapki image: {prompt}")
    except Exception as e:
        bot.reply_to(message, "Maaf kijiye, image nahi ban payi.")

# Text Chat Handler
@bot.message_handler(func=lambda message: True)
def chat(message):
    try:
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": message.text}]
        )
        bot.reply_to(message, completion.choices[0].message.content)
    except Exception as e:
        bot.reply_to(message, "Error: AI abhi jawab nahi de paa raha.")

bot.infinity_polling()
