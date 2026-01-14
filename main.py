import os
import telebot
import requests
from groq import Groq
from flask import Flask
from threading import Thread
from telebot import types
from PIL import Image, ImageDraw, ImageOps
from io import BytesIO

# --- 1. Flask Server (Uptime ke liye) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is 100% Alive and Running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 2. API Setup ---
# Render ke Environment Variables mein BOT_TOKEN aur GROQ_API_KEY hona zaruri hai
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

bot = telebot.TeleBot(BOT_TOKEN)

# --- 3. Image Generation Function (Round PFP) ---
def get_welcome_image(user_id, first_name):
    try:
        # Background Image (Stable Link)
        bg_url = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800&q=80"
        bg_resp = requests.get(bg_url, timeout=10)
        bg = Image.open(BytesIO(bg_resp.content)).resize((800, 450))
        draw = ImageDraw.Draw(bg)

        # User ki Profile Photo mangwana
        photos = bot.get_user_profile_photos(user_id)
        if photos.total_count > 0:
            file_info = bot.get_file(photos.photos[0][-1].file_id)
            pfp_resp = requests.get(f'https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}', timeout=10)
            pfp = Image.open(BytesIO(pfp_resp.content)).convert("RGBA")
        else:
            # Agar PFP nahi hai toh ek stylish default circle
            pfp = Image.new('RGBA', (200, 200), color=(50, 50, 50))

        # Photo ko Round (Gool) karna
        size = (180, 180)
        pfp = pfp.resize(size)
        mask = Image.new('L', size, 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, size[0], size[1]), fill=255)
        pfp.putalpha(mask)

        # Background par chipkana (Center mein)
        bg.paste(pfp, (310, 80), pfp)
        
        # Binary Data mein convert karna
        bio = BytesIO()
        bio.name = 'welcome.png'
        bg.save(bio, 'PNG')
        bio.seek(0)
        return bio
    except Exception as e:
        print(f"Welcome Image Error: {e}")
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
            caption=f"👋 **Welcome {user_name}!**\n\nI am your AI Assistant. I can speak any language. How can I help you today?",
            reply_markup=markup,
            parse_mode="Markdown"
        )
    else:
        bot.send_message(
            message.chat.id, 
            f"Welcome {user_name}! System is ready. Ask me anything.", 
            reply_markup=markup
        )

@bot.message_handler(func=lambda message: True)
def chat(message):
    try:
        client = Groq(api_key=GROQ_API_KEY)
        
        # Model update: llama-3.1-8b-instant (Fast and Multi-lingual)
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": message.text}],
            model="llama-3.1-8b-instant",
        )
        bot.reply_to(message, response.choices[0].message.content)
        
    except Exception as e:
        bot.reply_to(message, "⚠️ System is temporarily busy. Please try again.")

# --- 5. Main Execution ---
if __name__ == "__main__":
    keep_alive() # Flask starts in background
    print("Bot is starting and cleaning old updates...")
    
    # skip_pending=True purane conflicts hatata hai
    # timeout parameters connection ko stable rakhte hain
    bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=30)
    
