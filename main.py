import discord
from discord.ext import commands
from g4f import Client
import os
from dotenv import load_dotenv
from flask import Flask
from threading import Thread
import logging
import sys  # Добавлен импорт sys
import time  # Для задержки при перезапуске

# Инициализация
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')  # Исправлено на TOKEN
if not TOKEN:
    raise ValueError("Токен не найден в .env файле!")

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
gpt_client = Client()
active_dialogs = {}

# Настройка логов
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

# Flask сервер (изменен порт на 8000)
app = Flask('')
@app.route('/')
def home(): return "Bot is alive"

Thread(target=lambda: app.run(host='0.0.0.0', port=8000)).start()

@bot.event
async def on_ready():
    logging.info(f'Бот {bot.user.name} запущен!')
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.listening,
        name="ваши команды"
    ))

# Ваша основная логика бота (оставить без изменений)
# ...

if __name__ == '__main__':
    while True:
        try:
            bot.run(TOKEN)  # Исправлено на TOKEN
        except Exception as e:
            logging.error(f"Ошибка: {e}\nПерезапуск через 10 секунд...")
            time.sleep(10)
            os.execv(sys.executable, ['python'] + sys.argv)