import os
import threading
from flask import Flask
import telebot
import sys
import pandas as pd
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
    return "Бот работает локально!", 200

def run_flask():
    """Запуск Flask приложения в отдельном потоке"""
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

def run_bot():
    """Запуск бота с polling"""
    print("Запуск бота в режиме polling...")
    bot.polling(none_stop=True, interval=0)

# Запуск приложения
if __name__ == '__main__':
    print(f"Запуск приложения на {SERVER_URL}")
    print("Для остановки нажмите Ctrl+C")
    
    # Запускаем Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Запускаем бота в основном потоке
    try:
        run_bot()
    except KeyboardInterrupt:
        print("\nПриложение остановлено")

# После создания df = pd.DataFrame(data, columns=header)
if 'Amount' in df.columns:
    df['Amount'] = df['Amount'].str.replace('$', '', regex=False).str.replace(',', '', regex=False)
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
if 'Boxes Shipped' in df.columns:
    df['Boxes Shipped'] = pd.to_numeric(df['Boxes Shipped'], errors='coerce')
if 'Date' in df.columns:
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce') 