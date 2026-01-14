import os
import telebot
import requests
from groq import Groq
from flask import Flask
from threading import Thread
from telebot import types
from PIL import Image, ImageDraw, ImageOps
from io import BytesIO

# Flask setup
app = Flask('')
@app.route('/')
def home(): return "Bot is Alive!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

def get_welcome_image(user_id, first_name):
    try:
        # Background: Ek naya stable link
        bg_url = "https://raw.githubusercontent.com/python-pillow/Pillow/master/src/PIL/Image.py" # Yeh example hai, niche stable image link hai
        bg_url = "https://images.unsplash.com/photo-1557683316-973673baf926?w=800&q=80"
        
        bg_resp = requests.get(bg_url, timeout=10)
        bg = Image.open(BytesIO(bg_resp.content)).resize((800, 450))
        draw = ImageDraw.Draw(bg)

        # Get User PFP
        photos = bot.get_user_profile_photos(user_id)
        if photos.total_count > 0:
            file_info = bot.get_file(photos.photos[0][-1].file_id)
            pfp_resp = requests.get(f'https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}', timeout=10)
            pfp = Image.open(BytesIO(pfp_resp.content)).convert("RGBA")
        else:
            # Default agar pfp nahi hai
            pfp = Image.new('RGBA', (200, 200), color=(70, 70, 70))

        # Make Round
        pfp = pfp.resize((180, 180))
        mask = Image.new('L', (180, 180), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, 180, 180), fill=255)
        pfp.putalpha(mask)

        # Paste
        bg.paste(pfp, (310, 80), pfp)
        
        bio = BytesIO()
        bio.name = 'welcome.png'
        bg.save(bio, 'PNG')
        bio.seek(0)
        return bio
    except Exception as e:
        print(f"Error making image: {e}")
        return None

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("👨‍💻 Support", url="https://t.me/SANATANI_GOJO")
    btn2 = types.InlineKeyboardButton("📢 Join Channel", url="https://t.me/+fYOWZAXCTythZGY9")
    markup.add(btn1, btn2)

    welcome_img = get_welcome_image(message.from_user.id, message.from_user.first_name)
    
    if welcome_img:
        bot.send_photo(message.chat.id, welcome_img, caption=f"Welcome {message.from_user.first_name}!", reply_markup=markup)
    else:
        # Agar image fail ho jaye toh message toh jaye kam se kam
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
        bot.reply_to(message, "⚠️ System Busy")

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling(skip_pending=True)
        
