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

# Список админов
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
        [InlineKeyboardButton("📋 Список участников", callback_data="list")],
        [InlineKeyboardButton("🏆 TUSA SPORT", callback_data="sports")],
        [InlineKeyboardButton("ℹ️ Информация TUSA GANG", callback_data="info")],
        [InlineKeyboardButton("📱 Наши соцсети", callback_data="socials")]
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

# Меню выбора типа рассылки
def broadcast_type_menu():
    keyboard = [
        [InlineKeyboardButton("📝 Только текст", callback_data="broadcast_text")],
        [InlineKeyboardButton("🖼️ Текст + фото", callback_data="broadcast_photo")],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin")]
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
    save_subscriber(user.id, user.username, user.first_name)
    
    text = (
        "Привет!\n"
        "Я бот компании TUSA GANG, здесь ты можешь получить различную информацию о компании, выбери внизу нужную кнопку.\n\n"
        ":3"
    )
    
    if user.id in ADMINS:
        keyboard = [
            [InlineKeyboardButton("Обычное меню", callback_data="main")],
            [InlineKeyboardButton("👑 Админ-панель", callback_data="admin")]
        ]
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(text, reply_markup=main_menu())

# Рассылка текстового сообщения
async def broadcast_text_message(context: ContextTypes.DEFAULT_TYPE, message_text: str):
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
                await asyncio.sleep(0.1)
            except:
                failed += 1
                sub["subscribed"] = False
    
    if failed > 0:
        with open(SUBSCRIBERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(subscribers, f, ensure_ascii=False, indent=2)
    
    return success, failed

# Рассылка фото с текстом
async def broadcast_photo_message(context: ContextTypes.DEFAULT_TYPE, photo_url: str, caption: str):
    subscribers = load_subscribers()
    success = 0
    failed = 0
    
    for sub in subscribers["subscribers"]:
        if sub["subscribed"]:
            try:
                await context.bot.send_photo(
                    chat_id=sub["user_id"],
                    photo=photo_url,
                    caption=caption
                )
                success += 1
                await asyncio.sleep(0.1)
            except:
                failed += 1
                sub["subscribed"] = False
    
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
    info = data.get("info", {})
    
    user = query.from_user
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
    elif query.data == "info":
        if info:
            text = f"ℹ️ {info.get('title', 'Информация TUSA GANG')}\n\n{info.get('text', '')}"
            
            # Отправляем несколько фото если есть
            photos = info.get("photos", [])
            if photos:
                # Первую фото с описанием
                await context.bot.send_photo(
                    chat_id=query.message.chat.id,
                    photo=photos[0],
                    caption=text,
                )
                # Остальные фото без описания
                for photo_url in photos[1:]:
                    await context.bot.send_photo(
                        chat_id=query.message.chat.id,
                        photo=photo_url
                    )
                # Кнопка назад после всех фото
                await context.bot.send_message(
                    chat_id=query.message.chat.id,
                    text="Выберите раздел:",
                    reply_markup=main_menu()
                )
            else:
                # Если фото нет - просто текст с кнопками
                await query.edit_message_text(text, reply_markup=main_menu())
        else:
            await query.edit_message_text(
                "Информация о TUSA GANG пока не добавлена.", 
                reply_markup=main_menu()
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
            await query.edit_message_text(
                "📢 Выберите тип рассылки:",
                reply_markup=broadcast_type_menu()
            )
    elif query.data == "broadcast_text":
        if user.id in ADMINS:
            context.user_data["waiting_for_broadcast_text"] = True
            await query.edit_message_text(
                "📝 Введите текст для рассылки:"
            )
    elif query.data == "broadcast_photo":
        if user.id in ADMINS:
            context.user_data["waiting_for_broadcast_photo"] = True
            await query.edit_message_text(
                "🖼️ Введите ссылку на фото:"
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
            
            photos = sport.get("photos", [])
            if photos:
                await context.bot.send_photo(
                    chat_id=query.message.chat.id,
                    photo=photos[0],
                    caption=text,
                )
                for photo_url in photos[1:]:
                    await context.bot.send_photo(
                        chat_id=query.message.chat.id,
                        photo=photo_url
                    )
            else:
                await query.edit_message_text(text)
            
            await context.bot.send_message(
                chat_id=query.message.chat.id,
                text="Выберите вид спорта:",
                reply_markup=sports_menu(sports),
            )

# Обработка текстовых сообщений для рассылки
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    save_subscriber(user.id, user.username, user.first_name)
    
    message_text = update.message.text
    
    # Рассылка только текста
    if context.user_data.get("waiting_for_broadcast_text") and user.id in ADMINS:
        await update.message.reply_text("🔄 Начинаю текстовую рассылку...")
        
        success, failed = await broadcast_text_message(context, message_text)
        
        context.user_data["waiting_for_broadcast_text"] = False
        await update.message.reply_text(
            f"✅ Текстовая рассылка завершена!\nУспешно: {success}\nНе удалось: {failed}",
            reply_markup=admin_menu()
        )
    
    # Рассылка фото (первый шаг - получение ссылки на фото)
    elif context.user_data.get("waiting_for_broadcast_photo") and user.id in ADMINS:
        if "photo_url" not in context.user_data:
            # Сохраняем ссылку на фото и запрашиваем текст
            context.user_data["photo_url"] = message_text
            context.user_data["waiting_for_broadcast_photo_caption"] = True
            await update.message.reply_text("📝 Теперь введите текст для фото:")
        else:
            await update.message.reply_text("❌ Ошибка: неверная последовательность")
    
    # Ввод текста для фото (второй шаг)
    elif context.user_data.get("waiting_for_broadcast_photo_caption") and user.id in ADMINS:
        photo_url = context.user_data.get("photo_url")
        caption = message_text
        
        await update.message.reply_text("🔄 Начинаю рассылку с фото...")
        
        success, failed = await broadcast_photo_message(context, photo_url, caption)
        
        # Очищаем временные данные
        context.user_data["waiting_for_broadcast_photo"] = False
        context.user_data["waiting_for_broadcast_photo_caption"] = False
        context.user_data["photo_url"] = None
        
        await update.message.reply_text(
            f"✅ Рассылка с фото завершена!\nУспешно: {success}\nНе удалось: {failed}",
            reply_markup=admin_menu()
        )
    
    else:
        await update.message.reply_text("Используйте кнопки меню :)", reply_markup=main_menu())

def run_bot():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен!")
    app.run_polling()

