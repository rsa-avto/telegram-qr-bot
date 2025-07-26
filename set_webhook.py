import telebot
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = f"https://telegram-qr-bot-9yg7.onrender.com/{BOT_TOKEN}"

bot = telebot.TeleBot(BOT_TOKEN)
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)
print("✅ Вебхук установлен")