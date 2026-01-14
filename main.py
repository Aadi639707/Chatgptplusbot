import os
import telebot
import requests
import img2pdf
from groq import Groq
from flask import Flask
from threading import Thread
from telebot import types
from PIL import Image, ImageDraw, ImageOps
from io import BytesIO

# --- 1. Flask Server ---
app = Flask('')
@app.route('/')
def home(): return "PDF & AI Bot is Online!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- 2. Setup ---
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
bot = telebot.TeleBot(BOT_TOKEN)

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
        pfp = pfp.resize((180, 180))
        mask = Image.new('L', (180, 180), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, 180, 180), fill=255)
        pfp.putalpha(mask)
        bg.paste(pfp, (310, 80), pfp)
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
    welcome_msg = f"Hi {message.from_user.first_name}!\n\n🤖 **AI:** Send me any question.\n📄 **PDF:** Send me a photo to convert it to PDF."
    
    if img: bot.send_photo(message.chat.id, img, caption=welcome_msg, reply_markup=markup, parse_mode="Markdown")
    else: bot.send_message(message.chat.id, welcome_msg, reply_markup=markup, parse_mode="Markdown")

# --- PDF Converter Logic ---
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    sent_msg = bot.reply_to(message, "📥 Downloading photo...")
    try:
        # Photo download karna
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        bot.edit_message_text("⚙️ Converting to PDF...", message.chat.id, sent_msg.message_id)
        
        # Image ko PDF mein badalna
        pdf_bytes = img2pdf.convert(downloaded_file)
        
        # PDF bhejna
        with BytesIO(pdf_bytes) as pdf_file:
            pdf_file.name = f"converted_by_bot.pdf"
            bot.send_document(message.chat.id, pdf_file, caption="✅ Here is your PDF!")
            
        bot.delete_message(message.chat.id, sent_msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Error: {e}", message.chat.id, sent_msg.message_id)

# --- AI Chat Logic ---
@bot.message_handler(func=lambda message: True)
def chat(message):
    try:
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": message.text}],
            model="llama-3.1-8b-instant",
        )
        bot.reply_to(message, response.choices[0].message.content)
    except:
        bot.reply_to(message, "⚠️ System Busy")

# --- 5. Run ---
if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling(skip_pending=True, timeout=60)
    
