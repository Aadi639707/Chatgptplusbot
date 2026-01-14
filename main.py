import os
import telebot
import requests
from groq import Groq
from flask import Flask
from threading import Thread
from telebot import types
from PIL import Image, ImageDraw, ImageOps, ImageFont
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
    # 1. Background Image
    bg_url = "https://w0.peakpx.com/wallpaper/594/544/wallpaper-abstract-background-blue-and-black-3d.jpg"
    bg_resp = requests.get(bg_url)
    bg = Image.open(BytesIO(bg_resp.content)).resize((800, 450))
    draw = ImageDraw.Draw(bg)

    # 2. Get User Profile Photo
    try:
        photos = bot.get_user_profile_photos(user_id)
        if photos.total_count > 0:
            file_info = bot.get_file(photos.photos[0][-1].file_id)
            pfp_resp = requests.get(f'https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}')
            pfp = Image.open(BytesIO(pfp_resp.content)).convert("RGBA")
        else:
            pfp = Image.new('RGBA', (200, 200), color=(100, 100, 100))
    except:
        pfp = Image.new('RGBA', (200, 200), color=(100, 100, 100))

    # 3. Make PFP Round with Border
    size = (180, 180)
    pfp = pfp.resize(size)
    mask = Image.new('L', size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, size[0], size[1]), fill=255)
    pfp = ImageOps.fit(pfp, mask.size, centering=(0.5, 0.5))
    pfp.putalpha(mask)

    # 4. Paste PFP and Add Text
    bg.paste(pfp, (310, 50), pfp) # PFP Center
    
    # Text: "WELCOME [NAME]"
    # Note: Render par default font use hoga
    welcome_msg = f"WELCOME {first_name.upper()}"
    draw.text((400, 280), welcome_msg, fill="white", anchor="mm")
    draw.text((400, 320), "AI Assistant is Ready!", fill="#00ffff", anchor="mm")

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
            caption=f"Hello **{message.from_user.first_name}**! I am your AI. How can I help you?",
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
    
