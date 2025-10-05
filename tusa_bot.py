import os
import json
import aiohttp
import asyncio
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# Токен из секретов Render
TOKEN = os.getenv("TUSA_TOKEN")
JSON_URL = "https://raw.githubusercontent.com/dimonp4ik/tusa-bot/main/participants.json"
SUBSCRIBERS_FILE = "subscribers.json"

# Список админов (ЗАМЕНИ НА РЕАЛЬНЫЕ ID)
ADMINS = [671071896, 1254580347]  # Твой ID и второго админа

# Загрузка/сохранение подписчиков
def load_subscribers():
    try:
        with open(SUBSCRIBERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"subscribers": []}

def save_subscriber(user_id, username, first_name):
    data = load_subscribers()
    
    # Проверяем нет ли уже пользователя
    existing_user = next((sub for sub in data["subscribers"] if sub["user_id"] == user_id), None)
    
    if not existing_user:
        # Новый пользователь
        data["subscribers"].append({
            "user_id": user_id,
            "username": username,
            "first_name": first_name,
            "subscribed": True,
            "joined_date": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat()
        })
    else:
        # Обновляем существующего пользователя
        existing_user["subscribed"] = True
        existing_user["last_activity"] = datetime.now().isoformat()
        if username:
            existing_user["username"] = username
        if first_name:
            existing_user["first_name"] = first_name
        
    with open(SUBSCRIBERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Загрузка данных из GitHub
async def load_data():
    async with aiohttp.ClientSession() as session:
        async with session.get(JSON_URL) as resp:
            text = await resp.text()
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                start = text.find("{")
                end = text.rfind("}") + 1
                return json.loads(text[start:end])

# Главное меню
def main_menu():
    keyboard = [
        [InlineKeyboardButton("Список участников", callback_data="list")],
        [InlineKeyboardButton("TUSA SPORT", callback_data="sports")],
        [InlineKeyboardButton("Наши соцсети", callback_data="socials")]
        # Убрали кнопку "Подписаться" - теперь автоподписка
    ]
    return InlineKeyboardMarkup(keyboard)

# Админское меню
def admin_menu():
    keyboard = [
        [InlineKeyboardButton("📢 Сделать рассылку", callback_data="broadcast")],
        [InlineKeyboardButton("👥 Статистика подписчиков", callback_data="stats")],
        [InlineKeyboardButton("Главное меню", callback_data="main")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Кнопки участников по 3 в ряд
def participants_menu(participants):
    buttons = []
    row = []
    for i, p in enumerate(participants):
        row.append(InlineKeyboardButton(p["name"], callback_data=f"participant_{p['name']}"))
        if (i + 1) % 3 == 0:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("Главное меню", callback_data="main")])
    return InlineKeyboardMarkup(buttons)

# Кнопки видов спорта
def sports_menu(sports):
    buttons = []
    for sport in sports:
        buttons.append([InlineKeyboardButton(sport["name"], callback_data=f"sport_{sport['name']}")])
    buttons.append([InlineKeyboardButton("Главное меню", callback_data="main")])
    return InlineKeyboardMarkup(buttons)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    save_subscriber(user.id, user.username, user.first_name)  # Автоподписка!
    
    text = (
        "Привет!\n"
        "Я бот компании TUSA GANG, здесь ты можешь получить различную информацию о компании, выбери внизу нужную кнопку.\n\n"
        "✅ Вы автоматически подписаны на новости!"
    )
    
    # Проверяем админа (два ID)
    if user.id in ADMINS:
        keyboard = [
            [InlineKeyboardButton("Обычное меню", callback_data="main")],
            [InlineKeyboardButton("👑 Админ-панель", callback_data="admin")]
        ]
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(text, reply_markup=main_menu())

# Рассылка сообщения всем подписчикам
async def broadcast_message(context: ContextTypes.DEFAULT_TYPE, message_text: str):
    subscribers = load_subscribers()
    success = 0
    failed = 0
    
    for sub in subscribers["subscribers"]:
        if sub["subscribed"]:
            try:
                await context.bot.send_message(
                    chat_id=sub["user_id"],
                    text=message_text
                )
                success += 1
                await asyncio.sleep(0.1)  # Чтобы не спамить
            except:
                failed += 1
                # Помечаем как отписавшегося если не удалось отправить
                sub["subscribed"] = False
    
    # Сохраняем изменения если есть отписавшиеся
    if failed > 0:
        with open(SUBSCRIBERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(subscribers, f, ensure_ascii=False, indent=2)
    
    return success, failed

# Обработка кнопок
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = await load_data()
    participants = data.get("participants", [])
    sports = data.get("sports", [])
    
    user = query.from_user
    
    # АВТОПОДПИСКА при любом взаимодействии с кнопками!
    save_subscriber(user.id, user.username, user.first_name)

    if query.data == "list":
        await query.edit_message_text(
            "Список участников:", reply_markup=participants_menu(participants)
        )
    elif query.data == "sports":
        if sports:
            await query.edit_message_text(
                "🏆 TUSA SPORT - выберите вид спорта:", reply_markup=sports_menu(sports)
            )
        else:
            await query.edit_message_text(
                "Спортивные события пока не добавлены.", reply_markup=main_menu()
            )
    elif query.data == "socials":
        socials_text = (
            "Наш инстаграм: https://www.instagram.com/gangtusa/following/\n"
            "Наш телеграм канал: https://t.me/tusa_gang"
        )
        await query.edit_message_text(socials_text, reply_markup=main_menu())
    elif query.data == "admin":
        if user.id in ADMINS:
            await query.edit_message_text(
                "👑 Админ-панель:", 
                reply_markup=admin_menu()
            )
    elif query.data == "broadcast":
        if user.id in ADMINS:
            # Сохраняем сообщение для рассылки
            context.user_data["waiting_for_broadcast"] = True
            await query.edit_message_text(
                "📢 Введите сообщение для рассылки всем подписчикам:"
            )
    elif query.data == "stats":
        if user.id in ADMINS:
            subscribers = load_subscribers()
            total = len(subscribers["subscribers"])
            active = len([s for s in subscribers["subscribers"] if s["subscribed"]])
            
            stats_text = f"📊 Статистика подписчиков:\n\nВсего: {total}\nАктивных: {active}"
            await query.edit_message_text(stats_text, reply_markup=admin_menu())
    elif query.data == "main":
        await query.edit_message_text("Главное меню:", reply_markup=main_menu())
    elif query.data.startswith("participant_"):
        participant_name = query.data.replace("participant_", "")
        participant = next((p for p in participants if p["name"] == participant_name), None)
        if participant:
            text = f"{participant['name']}\n{participant['bio']}"
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
    elif query.data.startswith("sport_"):
        sport_name = query.data.replace("sport_", "")
        sport = next((s for s in sports if s["name"] == sport_name), None)
        if sport:
            text = f"🏆 {sport['name']} 🏆\n\n{sport['description']}\n\n📅 Расписание: {sport['schedule']}"
            
            # Отправляем несколько фото если есть
            if sport.get("photos") and len(sport["photos"]) > 0:
                # Первую фото с описанием
                await context.bot.send_photo(
                    chat_id=query.message.chat.id,
                    photo=sport["photos"][0],
                    caption=text,
                )
                # Остальные фото без описания
                for photo_url in sport["photos"][1:]:
                    await context.bot.send_photo(
                        chat_id=query.message.chat.id,
                        photo=photo_url
                    )
            else:
                await query.edit_message_text(text)
            
            # Кнопка назад к видам спорта
            await context.bot.send_message(
                chat_id=query.message.chat.id,
                text="Выберите вид спорта:",
                reply_markup=sports_menu(sports),
            )

# Обработка текстовых сообщений для рассылки
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    
    # АВТОПОДПИСКА при любом текстовом сообщении!
    save_subscriber(user.id, user.username, user.first_name)
    
    if context.user_data.get("waiting_for_broadcast") and user.id in ADMINS:
        message_text = update.message.text
        await update.message.reply_text("🔄 Начинаю рассылку...")
        
        success, failed = await broadcast_message(context, message_text)
        
        context.user_data["waiting_for_broadcast"] = False
        await update.message.reply_text(
            f"✅ Рассылка завершена!\nУспешно: {success}\nНе удалось: {failed}",
            reply_markup=admin_menu()
        )
    else:
        await update.message.reply_text("Используйте кнопки меню :)", reply_markup=main_menu())

def run_bot():
    # Создаем приложение
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен!")
    # Запуск polling синхронно
    app.run_polling()

