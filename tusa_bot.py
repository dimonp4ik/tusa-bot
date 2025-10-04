import os
import json
import aiohttp
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

# Токен из секретов Render
TOKEN = os.getenv("TUSA_TOKEN")

# Ссылка на JSON с участниками
JSON_URL = "https://raw.githubusercontent.com/dimonp4ik/tusa-bot/main/participants.json"

# Загрузка участников из GitHub
async def load_participants():
    async with aiohttp.ClientSession() as session:
        async with session.get(JSON_URL) as resp:
            text = await resp.text()
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                start = text.find("[")
                end = text.rfind("]") + 1
                data = json.loads(text[start:end])
            if isinstance(data, dict) and "participants" in data:
                return data["participants"]
            return data

# Главное меню
def main_menu():
    keyboard = [
        [InlineKeyboardButton("Список участников", callback_data="list")],
        [InlineKeyboardButton("Наши соцсети", callback_data="socials")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Кнопки участников по 3 в ряд
def participants_menu(participants):
    buttons = []
    row = []
    for i, p in enumerate(participants):
        row.append(InlineKeyboardButton(p["name"], callback_data=p["name"]))
        if (i + 1) % 3 == 0:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("Главное меню", callback_data="main")])
    return InlineKeyboardMarkup(buttons)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Привет!\n"
        "Я бот компании TUSA GANG, здесь ты можешь получить различную информацию о компании, выбери внизу нужную кнопку."
    )
    await update.message.reply_text(text, reply_markup=main_menu())

# Обработка кнопок
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    participants = await load_participants()

    if query.data == "list":
        await query.edit_message_text(
            "Список участников:", reply_markup=participants_menu(participants)
        )
    elif query.data == "socials":
        socials_text = (
            "Наш инстаграм: https://www.instagram.com/gangtusa/\n"
            "Наш телеграм канал: https://t.me/tusa_gang"
        )
        await query.edit_message_text(socials_text, reply_markup=main_menu())
    elif query.data == "main":
        await query.edit_message_text("Главное меню:", reply_markup=main_menu())
    else:
        participant = next((p for p in participants if p["name"] == query.data), None)
        if participant:
            text = f"{participant['name']}\n{participant['bio']}"
            if participant.get("instagram"):
                text += f"\nInstagram: {participant['instagram']}"
            if participant.get("photo"):
                await context.bot.send_photo(
                    chat_id=query.message.chat.id,
                    photo=participant["photo"],
                    caption=text,
                )
            else:
                await query.message.reply_text(text)
            # Кнопка назад к списку участников
            await context.bot.send_message(
                chat_id=query.message.chat.id,
                text="Выберите участника:",
                reply_markup=participants_menu(participants),
            )

def run_bot():
    # Создаем приложение
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    print("Бот запущен!")
    # Запуск polling синхронно
    app.run_polling()

