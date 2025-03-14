import telebot
import os
import requests
import json
from .config import BOT_TOKEN, SERVER_URL

# Функция обработки документов
def handle_document(message):
    temp_file_name = None
    try:
        # Получаем экземпляр бота из глобальной области видимости
        bot = telebot.TeleBot(BOT_TOKEN)
        
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
            try:
                # Готовим данные для отправки
                files = {'file': (message.document.file_name, file_to_send)}
                user_data = {'user_id': str(message.from_user.id), 'username': message.from_user.username}
                
                # Отправляем запрос на сервер
                print(f"Отправляем файл {message.document.file_name} на сервер {SERVER_URL}/process")
                response = requests.post(f'{SERVER_URL}/process', files=files, data=user_data, timeout=60)
                
                # Проверяем статус ответа
                print(f"Получен ответ от сервера, статус: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        result = response.json()
                        web_app_url = result.get('web_app_url')
                        analysis_id = result.get('analysis_id')
                        
                        if not web_app_url or not analysis_id:
                            raise ValueError("Не удалось получить необходимые данные из ответа сервера")
                        
                        # Отправляем успешный ответ пользователю
                        bot.reply_to(
                            message, 
                            f"Ваш файл успешно обработан!\n\n"
                            f"Просмотр графиков: {SERVER_URL}{web_app_url}\n\n"
                            f"Интерактивный анализ: {SERVER_URL}/interactive/{analysis_id}"
                        )
                    except json.JSONDecodeError:
                        # Если ответ сервера не в формате JSON
                        print(f"Ошибка: Не удалось декодировать JSON. Текст ответа: {response.text[:500]}")
                        bot.reply_to(message, "Ошибка при обработке ответа сервера. Пожалуйста, попробуйте позже.")
                    except Exception as json_error:
                        # Другие ошибки при обработке JSON
                        print(f"Ошибка при обработке JSON: {str(json_error)}")
                        bot.reply_to(message, f"Ошибка при обработке данных: {str(json_error)}")
                else:
                    # Обработка статусов ошибки
                    error_msg = f"Ошибка при обработке файла. Код ошибки: {response.status_code}"
                    try:
                        if response.text:
                            error_data = response.json()
                            if 'error' in error_data:
                                error_msg = f"Ошибка при обработке файла. Причина: {error_data['error']}"
                                print(f"Сервер вернул ошибку: {error_data['error']}")
                    except Exception as error_parse_error:
                        print(f"Не удалось распарсить ответ с ошибкой: {str(error_parse_error)}")
                        error_msg += f"\nТекст ответа: {response.text[:200]}"
                        
                    bot.reply_to(message, error_msg)
            except requests.RequestException as req_error:
                # Обработка ошибок соединения с сервером
                error_message = f"Ошибка соединения с сервером: {str(req_error)}"
                print(error_message)
                bot.reply_to(message, error_message)
            except Exception as e:
                # Обработка любых других неожиданных ошибок
                error_message = f"Произошла непредвиденная ошибка: {str(e)}"
                print(error_message)
                import traceback
                traceback.print_exc()
                bot.reply_to(message, error_message)
            
    except Exception as e:
        bot = telebot.TeleBot(BOT_TOKEN)
        bot.reply_to(message, f"Произошла ошибка: {str(e)}")
    finally:
        # Удаляем временный файл в любом случае
        if temp_file_name and os.path.exists(temp_file_name):
            try:
                os.close(os.open(temp_file_name, os.O_RDONLY))  # Закрываем открытые дескрипторы
                os.remove(temp_file_name)
                print(f"Временный файл {temp_file_name} удален")
            except Exception as e:
                print(f"Ошибка при удалении временного файла: {e}")