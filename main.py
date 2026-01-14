import os
import telebot
import requests
import random
import google.generativeai as genai
from flask import Flask
from threading import Thread
from io import BytesIO

# --- 1. Flask Setup (Uptime ke liye) ---
app = Flask('')
@app.route('/')
def home(): return "Gemini-Partner is Live!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- 2. Gemini API Setup ---
# Render par GEMINI_API_KEY variable zaroor add karein
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)

# Gemini Model Config (Clone logic)
generation_config = {
  "temperature": 0.9,
  "top_p": 0.95,
  "max_output_tokens": 2048,
}

model = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
  system_instruction="You are Gemini, a helpful AI partner. Remember the context of the conversation. Stay on topic until the user resets or changes it. Be natural and friendly."
)

# Har user ki history save karne ke liye dictionary
chat_sessions = {}

# --- 3. Bot Setup ---
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# --- 4. Handlers ---

# /start Command: Nayi session shuru karega
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    chat_sessions[user_id] = model.start_chat(history=[])
    welcome_msg = (f"Hi {message.from_user.first_name}! Main aapka Gemini AI partner hoon.\n\n"
                   "Sawaal puchiye, main context yaad rakhunga. Chat reset karne ke liye `/reset` likhein.")
    bot.reply_to(message, welcome_msg)

# /reset Command: History delete karne ke liye
@bot.message_handler(commands=['reset'])
def reset_chat(message):
    user_id = message.chat.id
    chat_sessions[user_id] = model.start_chat(history=[])
    bot.reply_to(message, "🔄 Chat history reset ho gayi hai. Naya topic shuru karein!")

# /draw Command: Image generation ke liye
@bot.message_handler(commands=['draw'])
def draw_image(message):
    query = message.text.replace("/draw", "").strip()
    if not query:
        bot.reply_to(message, "Prompt dein: `/draw a white horse`", parse_mode="Markdown")
        return
    
    sent_msg = bot.reply_to(message, "🎨 Gemini is imagining... please wait.")
    seed = random.randint(1, 999999)
    # nologo=true taaki bada sa waterwark na aaye
    image_url = f"https://pollinations.ai/p/{query.replace(' ', '%20')}?width=1080&height=1080&seed={seed}&nologo=true"
    
    try:
        img_data = requests.get(image_url, timeout=30).content
        with BytesIO(img_data) as photo:
            photo.name = 'ai_img.jpg'
            bot.send_photo(message.chat.id, photo, caption=f"✨ Result: `{query}`", parse_mode="Markdown")
        bot.delete_message(message.chat.id, sent_msg.message_id)
    except Exception as e:
        bot.edit_message_text("❌ Image server busy! Thodi der baad try karein.", message.chat.id, sent_msg.message_id)

# Smart Chat Handler (Context Memory ke saath)
@bot.message_handler(func=lambda message: True)
def gemini_chat(message):
    user_id = message.chat.id
    
    # Agar user ka session nahi hai, toh naya banao
    if user_id not in chat_sessions:
        chat_sessions[user_id] = model.start_chat(history=[])

    try:
        # User ka message session mein bhejna (Memory isi se banti hai)
        response = chat_sessions[user_id].send_message(message.text)
        bot.reply_to(message, response.text, parse_mode="Markdown")
    except Exception as e:
        print(f"Chat Error: {e}")
        # Crash hone par session reset karke try karna
        try:
            chat_sessions[user_id] = model.start_chat(history=[])
            bot.reply_to(message, "⚠️ Connection refresh kiya gaya hai. Kripya apna sawal phir se likhein.")
        except:
            bot.reply_to(message, "😔 Maaf kijiye, abhi mera brain refresh ho raha hai. 1 minute baad try karein.")

# --- 5. Error-Free Execution (Conflict 409 Fix) ---
if __name__ == "__main__":
    keep_alive()
    print("Gemini Clone is Starting...")
    # skip_pending=True purane atke hue messages aur conflict ko khatam karta hai
    bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=30)
    
