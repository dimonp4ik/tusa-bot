from flask import Flask
from threading import Thread
import os  # обязательно для работы с переменными окружения

app = Flask('')


@app.route('/')
def home():
    return "I'm alive!"


def run():
    # берём порт из переменной окружения PORT, если её нет — 8080
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)


def keep_alive():
    t = Thread(target=run)
    t.start()
