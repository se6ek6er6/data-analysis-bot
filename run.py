import os
from flask import Flask, request, json
import telebot
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from bot.config import BOT_TOKEN, SERVER_URL
from server.app import setup_routes

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')

# Настройка бота
if BOT_TOKEN is None:
    raise ValueError("BOT_TOKEN не найден в переменных окружения")
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Отправьте мне CSV файл для анализа, и я создам интерактивные визуализации.")

# Импортируем обработчик документов из bot.py
from bot.bot import handle_document
bot.register_message_handler(handle_document, content_types=['document'])

# Настройка Flask-маршрутов
setup_routes(app, bot)

@app.route('/')
def index():
    return "Бот работает!", 200

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    print(f"Request method: {request.method}")  # Логирование метода запроса
    if request.method == 'POST':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        print(f"Received update: {json_string}")  # Логирование содержимого запроса
        if update is not None:
            bot.process_new_updates([update])
        return "OK", 200
    else:
        return "Method Not Allowed", 405

def set_webhook():
    bot.remove_webhook()
    webhook_url = f"{SERVER_URL}/{BOT_TOKEN}"
    print(f"Setting webhook to: {webhook_url}")
    bot.set_webhook(url=webhook_url)

# Запуск приложения
if __name__ == '__main__':
    # Настраиваем вебхук
    set_webhook()
    
    # Запускаем Flask-приложение
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)