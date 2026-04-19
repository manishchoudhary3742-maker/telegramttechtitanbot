import os
import time
import telebot
from flask import Flask, request
from openai import OpenAI

# 1. Fetch tokens from environment variables
BOT_TOKEN = os.environ.get('BOT_TOKEN')
HF_TOKEN = os.environ.get('HF_TOKEN')

if not BOT_TOKEN or not HF_TOKEN:
    raise ValueError("Missing BOT_TOKEN or HF_TOKEN environment variables.")

# 2. Initialize Telegram Bot and Flask App
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# 3. Initialize OpenAI client for Hugging Face Router (translated from your JS)
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
)

# Set webhook dynamically when the app starts.
# Render automatically provides 'RENDER_EXTERNAL_URL' (e.g., https://your-app.onrender.com)
render_url = os.environ.get('RENDER_EXTERNAL_URL')
if render_url:
    bot.remove_webhook()
    time.sleep(1)
    # We use the bot token in the URL path to ensure the webhook is secure
    bot.set_webhook(url=f"{render_url}/{BOT_TOKEN}")

# Handle the /start and /help commands
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Hello! I am a DeepSeek-R1 AI bot. Send me a message and I'll reply!")

# Handle all incoming text messages
@bot.message_handler(content_types=['text'])
def handle_message(message):
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        # Call the Hugging Face Router API
        chat_completion = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1:novita",
            messages=[
                {
                    "role": "user",
                    "content": message.text,
                }
            ]
        )
        
        reply = chat_completion.choices[0].message.content
        
        # Telegram has a 4096 character limit per message. Split long AI responses.
        if len(reply) > 4096:
            for i in range(0, len(reply), 4096):
                bot.reply_to(message, reply[i:i+4096])
        else:
            bot.reply_to(message, reply)
            
    except Exception as e:
        bot.reply_to(message, f"An error occurred: {str(e)}")

# Flask route to receive webhooks from Telegram
@app.route('/' + BOT_TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

# Basic health check route for Render
@app.route('/')
def index():
    return "The Telegram AI Bot is running!"

if __name__ == "__main__":
    # Render assigns a dynamic port via the 'PORT' environment variable
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
