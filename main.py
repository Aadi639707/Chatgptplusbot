import os
import telebot
import requests
import img2pdf
import random
from groq import Groq
from flask import Flask
from threading import Thread
from telebot import types
from PIL import Image, ImageDraw, ImageOps
from io import BytesIO

# --- 1. Flask Setup (Uptime) ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Online and Smart!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- 2. Bot Setup ---
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
bot = telebot.TeleBot(BOT_TOKEN)

user_temp_file = {} # Memory for Smart Options

# --- 3. Welcome Image Function ---
def get_welcome_image(user_id, first_name):
    try:
        bg_url = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800&q=80"
        bg_resp = requests.get(bg_url, timeout=10)
        bg = Image.open(BytesIO(bg_resp.content)).resize((800, 450))
        photos = bot.get_user_profile_photos(user_id)
        if photos.total_count > 0:
            file_info = bot.get_file(photos.photos[0][-1].file_id)
            pfp_resp = requests.get(f'https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}', timeout=10)
            pfp = Image.open(BytesIO(pfp_resp.content)).convert("RGBA")
        else:
            pfp = Image.new('RGBA', (200, 200), color=(50, 50, 50))
        pfp = pfp.resize((180, 180)); mask = Image.new('L', (180, 180), 0)
        draw = ImageDraw.Draw(mask); draw.ellipse((0, 0, 180, 180), fill=255)
        pfp.putalpha(mask); bg.paste(pfp, (310, 80), pfp)
        bio = BytesIO(); bio.name = 'welcome.png'; bg.save(bio, 'PNG'); bio.seek(0)
        return bio
    except: return None

# --- 4. Handlers ---

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("👨‍💻 Support", url="https://t.me/SANATANI_GOJO"),
               types.InlineKeyboardButton("📢 Channel", url="https://t.me/+fYOWZAXCTythZGY9"))
    img = get_welcome_image(message.from_user.id, message.from_user.first_name)
    welcome_txt = f"👋 Hello {message.from_user.first_name}!\n\nAI Chat karein, Image banayein `/draw` se, ya Photo bhej kar PDF/Link banayein."
    if img: bot.send_photo(message.chat.id, img, caption=welcome_txt, reply_markup=markup, parse_mode="Markdown")
    else: bot.send_message(message.chat.id, welcome_txt, reply_markup=markup, parse_mode="Markdown")

# --- Fixed Image Generation (/draw) ---
@bot.message_handler(commands=['draw'])
def draw_image(message):
    query = message.text.replace("/draw", "").strip()
    if not query:
        bot.reply_to(message, "Kripya prompt dein. Example: `/draw a white horse`", parse_mode="Markdown")
        return

    sent_msg = bot.reply_to(message, "🎨 Generating your image... please wait.")
    seed = random.randint(1, 999999)
    image_url = f"https://pollinations.ai/p/{query.replace(' ', '%20')}?width=1080&height=1080&seed={seed}&model=flux&nologo=true"
    
    try:
        # Image download karke bhejna (Taaki logo wala error na aaye)
        img_data = requests.get(image_url, timeout=30).content
        with BytesIO(img_data) as photo:
            photo.name = 'ai_image.jpg'
            bot.send_photo(message.chat.id, photo, caption=f"✨ Result for: `{query}`", parse_mode="Markdown")
        bot.delete_message(message.chat.id, sent_msg.message_id)
    except Exception as e:
        bot.edit_message_text("❌ Server busy hai, thodi der baad try karein.", message.chat.id, sent_msg.message_id)

# --- Photo Smart Handler ---
@bot.message_handler(content_types=['photo'])
def handle_incoming_photo(message):
    user_id = message.chat.id
    user_temp_file[user_id] = message.photo[-1].file_id 

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📄 Make PDF", callback_data="pdf"),
               types.InlineKeyboardButton("🔗 Generate Link", callback_data="link"))
    
    bot.reply_to(message, "Aap is image ka kya karna chahte hain?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    user_id = call.message.chat.id
    if user_id not in user_temp_file:
        bot.answer_callback_query(call.id, "Photo purani ho gayi hai!")
        return

    if call.data == "pdf":
        bot.edit_message_text("⚙️ Creating PDF...", user_id, call.message.message_id)
        try:
            file_info = bot.get_file(user_temp_file[user_id])
            downloaded_file = bot.download_file(file_info.file_path)
            pdf_bytes = img2pdf.convert(downloaded_file)
            with BytesIO(pdf_bytes) as pdf_file:
                pdf_file.name = "converted.pdf"
                bot.send_document(user_id, pdf_file, caption="✅ PDF Ready!")
            bot.delete_message(user_id, call.message.message_id)
        except Exception as e:
            bot.send_message(user_id, f"❌ Error: {e}")

    elif call.data == "link":
        bot.edit_message_text("🔗 Link generation start...", user_id, call.message.message_id)
        bot.send_message(user_id, "Ye feature update ho raha hai. Jald hi Telegraph link support milega!")

# --- AI Chat Handler ---
@bot.message_handler(func=lambda message: True)
def ai_chat(message):
    try:
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": message.text}],
            model="llama-3.1-8b-instant",
        )
        bot.reply_to(message, response.choices[0].message.content)
    except:
        bot.reply_to(message, "⚠️ System Busy!")

# --- 5. Error-Free Execution ---
if __name__ == "__main__":
    keep_alive()
    print("Bot is starting...")
    # Infinity polling without multiple values error
    bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=30)
                     
