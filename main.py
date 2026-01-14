import os
import telebot
import requests
from groq import Groq
from flask import Flask
from threading import Thread
from telebot import types
from PIL import Image, ImageDraw, ImageOps
from io import BytesIO

# --- Flask Setup ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Alive!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- Bot Setup ---
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

def get_welcome_image(user_id, first_name):
    # 1. Background Image (Aap is URL ko kisi bhi acche background link se badal sakte hain)
    bg_url = "https://img.freepik.com/free-vector/abstract-technology-particle-background_23-2148426649.jpg"
    bg_resp = requests.get(bg_url)
    bg = Image.open(BytesIO(bg_resp.content)).resize((800, 400))

    # 2. Get User Profile Photo
    photos = bot.get_user_profile_photos(user_id)
    if photos.total_count > 0:
        file_info = bot.get_file(photos.photos[0][-1].file_id)
        pfp_resp = requests.get(f'https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}')
        pfp = Image.open(BytesIO(pfp_resp.content)).convert("RGBA")
    else:
        # Agar user ki photo nahi hai toh default image
        pfp = Image.new('RGBA', (200, 200), color=(200, 200, 200))

    # 3. Make PFP Round
    pfp = pfp.resize((150, 150))
    mask = Image.new('L', (150, 150), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, 150, 150), fill=255)
    pfp = ImageOps.fit(pfp, mask.size, centering=(0.5, 0.5))
    pfp.putalpha(mask)

    # 4. Paste PFP on Background
    bg.paste(pfp, (325, 50), pfp) # Center mein paste
    
    # 5. Save to memory
    bio = BytesIO()
    bio.name = 'welcome.png'
    bg.save(bio, 'PNG')
    bio.seek(0)
    return bio

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    support_btn = types.InlineKeyboardButton("👨‍💻 Support", url="https://t.me/SANATANI_GOJO")
    channel_btn = types.InlineKeyboardButton("📢 Join Channel", url="https://t.me/+fYOWZAXCTythZGY9")
    markup.add(support_btn, channel_btn)

    try:
        welcome_img = get_welcome_image(message.from_user.id, message.from_user.first_name)
        bot.send_photo(
            message.chat.id, 
            welcome_img, 
            caption=f"Welcome **{message.from_user.first_name}**! How can I help you today?",
            reply_markup=markup,
            parse_mode="Markdown"
        )
    except Exception as e:
        bot.send_message(message.chat.id, f"Welcome {message.from_user.first_name}!", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def chat(message):
    try:
        client = Groq(api_key=os.environ.get('GROQ_API_KEY'))
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": message.text}],
            model="llama-3.1-8b-instant",
        )
        bot.reply_to(message, response.choices[0].message.content)
    except:
        bot.reply_to(message, "⚠️ System busy, try again.")

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling(skip_pending=True)
        
