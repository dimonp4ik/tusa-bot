from keep_alive import keep_alive
import tusa_bot  # твой рабочий файл бота

if __name__ == "__main__":
    # Запускаем веб-сервер для Render (keep_alive)
    keep_alive()
    
    # Запускаем Telegram-бот
    # Функция run_bot() должна быть в tusa_bot.py
    tusa_bot.run_bot()
