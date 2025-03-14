import telebot
from telebot import types
import os
import requests
from config import BOT_TOKEN, SERVER_URL
from flask import Flask

bot = telebot.TeleBot(BOT_TOKEN)
server = Flask(__name__)

@server.route('/')
def webhook():
    return "Бот работает!", 200

# Добавьте эту функцию для удаления вебхука
def remove_webhook():
    bot.remove_webhook()
    print("Вебхук удален успешно")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Отправьте мне CSV файл для анализа, и я создам интерактивные визуализации.")

@bot.message_handler(content_types=['document'])
def handle_document(message):
    temp_file_name = None
    try:
        # Проверяем, что это CSV файл
        if not message.document.file_name.endswith('.csv'):
            bot.reply_to(message, "Пожалуйста, отправьте CSV файл.")
            return
            
        # Получаем информацию о файле
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Создаем временный файл для сохранения
        temp_file_name = f"temp_{message.document.file_name}"
        with open(temp_file_name, 'wb') as new_file:
            new_file.write(downloaded_file)
        
        # Отправляем сообщение о начале обработки
        bot.send_message(message.chat.id, "Начинаю обработку вашего файла...")
        
        # Отправляем файл на бэкенд для обработки
        with open(temp_file_name, 'rb') as file_to_send:
            files = {'file': (message.document.file_name, file_to_send)}
            user_data = {'user_id': str(message.from_user.id), 'username': message.from_user.username}
            
            response = requests.post(f'{SERVER_URL}/process', files=files, data=user_data)
        
        if response.status_code == 200:
            # Остальной код...
            result = response.json()
            web_app_url = result.get('web_app_url')
            analysis_id = result.get('analysis_id')
            
            # Отправляем текстовые URL вместо кнопок для локальной разработки
            bot.reply_to(
                message, 
                f"Ваш файл успешно обработан!\n\n"
                f"Просмотр графиков: {SERVER_URL}{web_app_url}\n\n"
                f"Интерактивный анализ: {SERVER_URL}/interactive/{analysis_id}"
            )
        else:
            # Код обработки ошибок...
            error_msg = "Ошибка при обработке файла."
            if response.text:
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_msg += f" Причина: {error_data['error']}"
                except:
                    error_msg += f" Код ошибки: {response.status_code}"
                    
            bot.reply_to(message, error_msg)
            
    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка: {str(e)}")
    finally:
        # Удаляем временный файл в любом случае
        if temp_file_name and os.path.exists(temp_file_name):
            try:
                os.close(os.open(temp_file_name, os.O_RDONLY))  # Закрываем открытые дескрипторы
                os.remove(temp_file_name)
            except Exception as e:
                print(f"Ошибка при удалении временного файла: {e}")

if __name__ == '__main__':
    print("Бот запущен. Нажмите Ctrl+C для завершения.")
    remove_webhook()
    bot.polling(none_stop=True)