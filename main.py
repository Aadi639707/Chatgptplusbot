import os
import telebot
import requests
import random
import google.generativeai as genai
from flask import Flask
from threading import Thread
from io import BytesIO

# --- Flask Server ---
app = Flask('')
@app.route('/')
def home(): return "Gemini-Clone is Online!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- Gemini Setup ---
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)

# Model configuration
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction="You are Gemini, a smart AI partner. Remember chat history and be helpful."
)

# User Memory
chat_sessions = {}

# --- Bot Setup ---
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# Start & Reset Logic
@bot.message_handler(commands=['start', 'reset'])
def start_or_reset(message):
    user_id = message.chat.id
    chat_sessions[user_id] = model.start_chat(history=[])
    text = "🔄 Chat reset ho gayi hai! Poochiye kya puchna hai, main sab yaad rakhunga." if message.text == "/reset" else "👋 Hi! Main Gemini hoon. Main hamari baatein yaad rakhunga. Poochiye!"
    bot.reply_to(message, text)

# Draw Logic (Image Generation)
@bot.message_handler(commands=['draw'])
def draw(message):
    prompt = message.text.replace("/draw", "").strip()
    if not prompt:
        bot.reply_to(message, "Kripya prompt dein. Ex: /draw a cat")
        return
    sent_msg = bot.reply_to(message, "🎨 Generating image...")
    image_url = f"https://pollinations.ai/p/{prompt.replace(' ', '%20')}?width=1080&height=1080&nologo=true"
    try:
        img_data = requests.get(image_url, timeout=30).content
        bot.send_photo(message.chat.id, img_data, caption=f"✨ Result: {prompt}")
        bot.delete_message(message.chat.id, sent_msg.message_id)
    except:
        bot.edit_message_text("❌ Server busy!", message.chat.id, sent_msg.message_id)

# Fixed Smart Chat (Error solving part)
@bot.message_handler(func=lambda message: True)
def handle_chat(message):
    user_id = message.chat.id
    
    # Session check and Re-creation if missing
    if user_id not in chat_sessions:
        try:
            chat_sessions[user_id] = model.start_chat(history=[])
        except Exception:
            bot.reply_to(message, "⚠️ API Key issue. Check your Gemini API Key on Render.")
            return

    try:
        # Gemini se response lena
        response = chat_sessions[user_id].send_message(message.text)
        bot.reply_to(message, response.text, parse_mode="Markdown")
    except Exception as e:
        print(f"Error: {e}")
        # Agar error aaye toh session reset karke firse try karna
        try:
            chat_sessions[user_id] = model.start_chat(history=[])
            response = chat_sessions[user_id].send_message(message.text)
            bot.reply_to(message, response.text, parse_mode="Markdown")
        except:
            bot.reply_to(message, "😔 Maaf kijiye, abhi mera brain refresh ho raha hai. 1 minute baad try karein.")

# --- Polling ---
if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling(skip_pending=True)
  
