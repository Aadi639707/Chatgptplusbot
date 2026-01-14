import os
import telebot
import requests
from groq import Groq
from flask import Flask
from threading import Thread
from telebot import types
from PIL import Image, ImageDraw, ImageOps
from io import BytesIO

# --- 1. Flask Setup (Render ko zinda rakhne ke liye) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is Online and Running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 2. Bot aur API Setup ---
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

bot = telebot.TeleBot(BOT_TOKEN)

# --- 3. Welcome Image Generator Function ---
def get_welcome_image(user_id, first_name):
    try:
        # Background Image
        bg_url = "https://w0.peakpx.com/wallpaper/594/544/wallpaper-abstract-background-blue-and-black-3d.jpg"
        bg_resp = requests.get(bg_url)
        bg = Image.open(BytesIO(bg_resp.content)).resize((800, 450))
        draw = ImageDraw.Draw(bg)

        # Get User PFP
        photos = bot.get_user_profile_photos(user_id)
        if photos.total_count > 0:
            file_info = bot.get_file(photos.photos[0][-1].file_id)
            pfp_resp = requests.get(f'https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}')
            pfp = Image.open(BytesIO(pfp_resp.content)).convert("RGBA")
        else:
            pfp = Image.new('RGBA', (200, 200), color=(100, 100, 100))

        # Make PFP Round
        size = (180, 180)
        pfp = pfp.resize(size)
        mask = Image.new('L', size, 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, size[0], size[1]), fill=255)
        pfp = ImageOps.fit(pfp, mask.size, centering=(0.5, 0.5))
        pfp.putalpha(mask)

        # Paste PFP on Background
        bg.paste(pfp, (310, 60), pfp)
        
        # Add Welcome Text
        welcome_msg = f"WELCOME {first_name.upper()}"
        # Note: Render par custom fonts load karna mushkil hota hai, isliye basic text draw hoga
        draw.text((400, 300), welcome_msg, fill="white", anchor="mm")
        draw.text((400, 340), "I am your AI Assistant", fill="#00ffff", anchor="mm")

        bio = BytesIO()
        bio.name = 'welcome.png'
        bg.save(bio, 'PNG')
        bio.seek(0)
        return bio
    except Exception as e:
        print(f"Image Error: {e}")
        return None

# --- 4. Bot Handlers ---

@bot.message_handler(commands=['start'])
def start(message):
    # Buttons setup
    markup = types.InlineKeyboardMarkup(row_width=2)
    support_btn = types.InlineKeyboardButton("👨‍💻 Support", url="https://t.me/SANATANI_GOJO")
    channel_btn = types.InlineKeyboardButton("📢 Join Channel", url="https://t.me/+fYOWZAXCTythZGY9")
    markup.add(support_btn, channel_btn)

    user_name = message.from_user.first_name
    welcome_img = get_welcome_image(message.from_user.id, user_name)

    if welcome_img:
        bot.send_photo(
            message.chat.id, 
            welcome_img, 
            caption=f"Hi {user_name}! I'm 24/7 Online. Ask me anything in any language!",
            reply_markup=markup,
            parse_mode="Markdown"
        )
    else:
        bot.send_message(
            message.chat.id, 
            f"Welcome {user_name}! How can I help you today?", 
            reply_markup=markup
        )

@bot.message_handler(func=lambda message: True)
def chat(message):
    try:
        client = Groq(api_key=GROQ_API_KEY)
        
        # Multi-lingual model
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": message.text}],
            model="llama-3.1-8b-instant",
        )
        bot.reply_to(message, response.choices[0].message.content)
        
    except Exception as e:
        bot.reply_to(message, "⚠️ System is a bit busy. Please try again in a few seconds.")

# --- 5. Start Bot ---
if __name__ == "__main__":
    keep_alive() # Flask shuru karega
    print("Bot is starting...")
    # 409 Conflict fix karne ke liye timeout parameters
    bot.infinity_polling(skip_pending=True, timeout=10, long_polling_timeout=5)
    
