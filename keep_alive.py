from flask import Flask
from threading import Thread
import os
import requests
import time

app = Flask('')

def ping_self():
    def ping():
        while True:
            try:
                # Твой реальный URL
                requests.get("https://tusa-bot-1.onrender.com/")
                print("Pinged successfully!")
            except Exception as e:
                print(f"Ping failed: {e}")
            time.sleep(300)  # Пинг каждые 5 минут
    
    ping_thread = Thread(target=ping, daemon=True)
    ping_thread.start()

@app.route('/')
def home():
    return "I'm alive!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    # Запускаем пингер
    ping_self()
    # Запускаем Flask сервер
    t = Thread(target=run)
    t.start()


