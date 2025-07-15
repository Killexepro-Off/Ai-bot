import discord
from discord.ext import commands
from g4f.client import Client
import os
from datetime import datetime

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
gpt_client = Client()

active_dialogs = {}

def save_to_file(content, prefix="response"):
    """Создает временный txt файл"""
    filename = f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    return filename

async def get_gpt_response(prompt, history=[]):
    """Улучшенный запрос к GPT с обработкой технических тем"""
    try:
        messages = [{"role": "system", "content": "Отвечай технически точно, особенно когда просят объяснить принципы работы"}]
        for h in history[-3:]:  # Берем последние 3 сообщения для контекста
            messages.append({"role": "user", "content": h[0]})
            messages.append({"role": "assistant", "content": h[1]})
        messages.append({"role": "user", "content": prompt})

        response = gpt_client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.3  # Для более точных ответов
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"GPT Error: {e}")
        return None

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Обработка вложенных файлов
    if message.attachments:
        for attachment in message.attachments:
            if attachment.filename.endswith('.txt'):
                file_content = await attachment.read()
                user_id = str(message.author.id)

                if user_id in active_dialogs:
                    async with message.channel.typing():
                        response = await get_gpt_response(f"Анализируй этот файл:\n{file_content.decode()}")
                        if response:
                            if len(response) > 1500:
                                filename = save_to_file(response, "analysis")
                                await message.reply(file=discord.File(filename))
                                os.remove(filename)
                            else:
                                await message.reply(response)
                return

    # Обработка текстовых сообщений
    user_id = str(message.author.id)
    content = message.content.lower()

    # Точное определение упоминания
    bot_mentioned = f"<@{bot.user.id}>" in message.content

    if bot_mentioned:
        # Сброс диалога при чистом упоминании
        if message.content.strip() == f"<@{bot.user.id}>":
            if user_id in active_dialogs:
                del active_dialogs[user_id]
            await message.reply("Диалог сброшен. Задайте вопрос после упоминания.")
            return

        # Начало нового диалога
        active_dialogs[user_id] = {
            "channel": message.channel.id,
            "history": []
        }

        question = message.content.replace(f'<@{bot.user.id}>', '').strip()
        if question:
            async with message.channel.typing():
                response = await get_gpt_response(question)
                if response:
                    active_dialogs[user_id]["history"].append((question, response))
                    if len(response) > 1500:
                        filename = save_to_file(response)
                        await message.reply(file=discord.File(filename))
                        os.remove(filename)
                    else:
                        await message.reply(response)
        return

    # Продолжение диалога
    if user_id in active_dialogs:
        if content == "стоп":
            del active_dialogs[user_id]
            await message.reply("Диалог завершен")
            return

        async with message.channel.typing():
            response = await get_gpt_response(
                message.content,
                active_dialogs[user_id]["history"]
            )
            if response:
                active_dialogs[user_id]["history"].append((message.content, response))
                if len(response) > 1500:
                    filename = save_to_file(response)
                    await message.reply(file=discord.File(filename))
                    os.remove(filename)
                else:
                    await message.reply(response)

# Keep-alive для Replit
from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running"

Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

bot.run(os.getenv("BOT_TOKEN"))