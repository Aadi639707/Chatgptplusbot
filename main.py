# Image Generation Command: /img prompt
@bot.message_handler(commands=['img'])
def send_image(message):
    # Prompt nikalna
    prompt = message.text.replace("/img", "").strip()
    
    if not prompt:
        bot.reply_to(message, "Kripya prompt likhein. Example: /img a cute cat")
        return
    
    bot.send_chat_action(message.chat.id, 'upload_photo')
    
    # Ye wala URL format zyada stable hai
    image_url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}"
    
    try:
        # Hum direct image bhej rahe hain
        bot.send_photo(message.chat.id, photo=image_url, caption=f"Generated: {prompt}")
    except Exception as e:
        bot.reply_to(message, "Maaf kijiye, image load nahi ho saki. Dubara koshish karein.")
        
