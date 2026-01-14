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

# --- 1. Flask Server (Uptime ke liye) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is Online: AI + PDF Converter is Active!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 2. API Setup ---
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

bot = telebot.TeleBot(BOT_TOKEN)

# --- 3. Welcome Image Function (Round PFP) ---
def get_welcome_image(user_id, first_name):
    try:
        # Background Image
        bg_url = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800&q=80"
        bg_resp = requests.get(bg_url, timeout=10)
        bg = Image.open(BytesIO(bg_resp.content)).resize((800, 450))
        
        # User PFP Download
        photos = bot.get_user_profile_photos(user_id)
        if photos.total_count > 0:
            file_info = bot.get_file(photos.photos[0][-1].file_id)
            pfp_resp = requests.get(f'https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}', timeout=10)
            pfp = Image.open(BytesIO(pfp_resp.content)).convert("RGBA")
        else:
            pfp = Image.new('RGBA', (200, 200), color=(50, 50, 50))

        # Rounding PFP
        size = (180, 180)
        pfp = pfp.resize(size)
        mask = Image.new('L', size, 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, size[0], size[1]), fill=255)
        pfp = ImageOps.fit(pfp, mask.size, centering=(0.5, 0.5))
        pfp.putalpha(mask)

        # Paste on Background
        bg.paste(pfp, (310, 80), pfp)
        
        bio = BytesIO()
        bio.name = 'welcome.png'
        bg.save(bio, 'PNG')
        bio.seek(0)
        return bio
    except Exception as e:
        print(f"Welcome Image Error: {e}")
        return None

# --- 4. Handlers ---

# /start command
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("👨‍💻 Support", url="https://t.me/SANATANI_GOJO")
    btn2 = types.InlineKeyboardButton("📢 Join Channel", url="https://t.me/+fYOWZAXCTythZGY9")
    markup.add(btn1, btn2)

    user_name = message.from_user.first_name
    img = get_welcome_image(message.from_user.id, user_name)
    
    welcome_text = (
        f"👋 **Hello {user_name}!**\n\n"
        "🤖 **AI Chat:** Just send me any message to talk.\n"
        "📄 **PDF Converter:** Send me a **Photo** to convert it to PDF instantly!"
    )

    if img:
        bot.send_photo(message.chat.id, img, caption=welcome_text, reply_markup=markup, parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode="Markdown")

# Photo to PDF Handler
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    sent_msg = bot.reply_to(message, "📥 Downloading your photo...")
    try:
        # Download photo
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        bot.edit_message_text("⚙️ Converting to PDF...", message.chat.id, sent_msg.message_id)
        
        # Convert to PDF
        pdf_bytes = img2pdf.convert(downloaded_file)
        
        # Send PDF
        with BytesIO(pdf_bytes) as pdf_file:
            pdf_file.name = f"Converted_File.pdf"
            bot.send_document(message.chat.id, pdf_file, caption="✅ Your PDF is ready!")
            
        bot.delete_message(message.chat.id, sent_msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Error during conversion: {e}", message.chat.id, sent_msg.message_id)

# AI Chat Handler (Groq Llama 3.1)
@bot.message_handler(func=lambda message: True)
def chat(message):
    try:
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": message.text}],
            model="llama-3.1-8b-instant",
        )
        bot.reply_to(message, response.choices[0].message.content)
    except Exception as e:
        print(f"AI Error: {e}")
        bot.reply_to(message, "⚠️ AI is currently busy. Try again later.")

# --- 5. Main Execution ---
if __name__ == "__main__":
    keep_alive()
    print("Bot started successfully...")
    # 409 Conflict fix ke liye skip_pending=True zaruri hai
    bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=30)
    
