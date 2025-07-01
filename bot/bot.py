import telebot
import os
import requests
import json
from bot.config import BOT_TOKEN, SERVER_URL
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


# Функция обработки документов
def handle_document(message):
    temp_file_name = None
    try:
        # Получаем экземпляр бота из глобальной области видимости
        if BOT_TOKEN is None:
            raise ValueError("BOT_TOKEN не найден")
        bot = telebot.TeleBot(BOT_TOKEN)
        
        # Проверяем, что это CSV файл
        if not message.document.file_name.endswith(('.csv', '.xls', '.xlsx')):
            bot.reply_to(message, "Пожалуйста, отправьте CSV/XLS/XLSX файл.")
            return
            
        # Получаем информацию о файле
        file_info = bot.get_file(message.document.file_id)
        if file_info.file_path is None:
            raise ValueError("Не удалось получить путь к файлу")
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Создаем временный файл для сохранения
        temp_file_name = f"temp_{message.document.file_name}"
        with open(temp_file_name, 'wb') as new_file:
            new_file.write(downloaded_file)
        
        # Отправляем сообщение о начале обработки
        bot.send_message(message.chat.id, "🔄 Начинаю обработку вашего файла...")
        
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
                        visualizations_count = result.get('visualizations_count', 0)
                        
                        if not web_app_url or not analysis_id:
                            raise ValueError("Не удалось получить необходимые данные из ответа сервера")
                        
                        # Формируем ссылку на универсальный отчет
                        report_url = f"{SERVER_URL}/report/{analysis_id}"
                        
                        # Проверяем, не является ли URL локальным
                        is_localhost = "localhost" in SERVER_URL or "127.0.0.1" in SERVER_URL
                        
                        if is_localhost:
                            # Для локальной разработки отправляем ссылку в тексте
                            markup = None
                            links_text = (
                                f"\n\n🔗 <b>Ссылка на отчет:</b>\n"
                                f"📊 <a href='{report_url}'>{report_url}</a>"
                            )
                        else:
                            # Для продакшена создаем кнопку
                            markup = InlineKeyboardMarkup(row_width=1)
                            markup.add(
                                InlineKeyboardButton("📊 Универсальный отчет", url=report_url)
                            )
                            links_text = ""
                        
                        # Пытаемся найти превью изображения
                        preview_path = None
                        try:
                            analysis_dir = os.path.join("static", "analyses", analysis_id)
                            metadata_path = os.path.join(analysis_dir, "metadata.json")
                            
                            if os.path.exists(metadata_path):
                                with open(metadata_path, "r", encoding="utf-8") as f:
                                    metadata = json.load(f)
                                
                                # Ищем 3D scatter plot для превью
                                for viz in metadata.get("visualizations", []):
                                    if viz.get("type") == "3d_scatter":
                                        potential_path = os.path.join(analysis_dir, viz["path"])
                                        if os.path.exists(potential_path):
                                            preview_path = potential_path
                                            break
                                
                                # Если 3D scatter не найден, ищем любой подходящий график
                                if not preview_path:
                                    for viz in metadata.get("visualizations", []):
                                        if viz.get("type") in ("distribution", "bar", "correlation", "scatter", "time_series"):
                                            potential_path = os.path.join(analysis_dir, viz["path"])
                                            if os.path.exists(potential_path):
                                                preview_path = potential_path
                                                break
                        except Exception as e:
                            print(f"Ошибка при поиске превью: {e}")
                            preview_path = None
                        
                        # Формируем описание состояния отчета
                        status_text = (
                            f"✅ <b>Анализ завершен успешно!</b>\n\n"
                            f"📁 <b>Файл:</b> {message.document.file_name}\n\n"
                            f"📝 <b>Что было сделано:</b>\n"
                            f"— Анализ структуры и типов данных\n"
                            f"— Построение графиков распределений\n"
                            f"— Создание корреляционных матриц\n"
                            f"— Анализ выбросов и аномалий\n"
                            f"— Продвинутая статистика\n"
                            f"— Интерактивные визуализации\n\n"
                            f"Откройте универсальный отчет:{links_text}"
                        )
                        
                        # Отправляем результат с превью или без
                        if preview_path and os.path.exists(preview_path):
                            try:
                                with open(preview_path, "rb") as img:
                                    bot.send_photo(
                                        message.chat.id, 
                                        img,
                                        caption=status_text,
                                        parse_mode="HTML",
                                        reply_markup=markup
                                    )
                            except Exception as photo_error:
                                print(f"Ошибка отправки фото: {photo_error}")
                                # Если не удалось отправить фото, отправляем только текст
                                bot.send_message(
                                    message.chat.id, 
                                    status_text,
                                    parse_mode="HTML",
                                    reply_markup=markup
                                )
                        else:
                            # Отправляем только текст с кнопками
                            bot.send_message(
                                message.chat.id, 
                                status_text,
                                parse_mode="HTML",
                                reply_markup=markup
                            )
                            
                    except json.JSONDecodeError:
                        # Если ответ сервера не в формате JSON
                        print(f"Ошибка: Не удалось декодировать JSON. Текст ответа: {response.text[:500]}")
                        bot.reply_to(message, "❌ Ошибка при обработке ответа сервера. Пожалуйста, попробуйте позже.")
                    except Exception as json_error:
                        # Другие ошибки при обработке JSON
                        print(f"Ошибка при обработке JSON: {str(json_error)}")
                        bot.reply_to(message, f"❌ Ошибка при обработке данных: {str(json_error)}")
                else:
                    # Обработка статусов ошибки
                    error_msg = f"❌ Ошибка при обработке файла. Код ошибки: {response.status_code}"
                    try:
                        if response.text:
                            error_data = response.json()
                            if 'error' in error_data:
                                error_msg = f"❌ Ошибка при обработке файла.\n\nПричина: {error_data['error']}"
                                print(f"Сервер вернул ошибку: {error_data['error']}")
                    except Exception as error_parse_error:
                        print(f"Не удалось распарсить ответ с ошибкой: {str(error_parse_error)}")
                        error_msg += f"\n\nТекст ответа: {response.text[:200]}"
                        
                    bot.reply_to(message, error_msg)
            except requests.RequestException as req_error:
                # Обработка ошибок соединения с сервером
                error_message = f"❌ Ошибка соединения с сервером:\n{str(req_error)}"
                print(error_message)
                bot.reply_to(message, error_message)
            except Exception as e:
                # Обработка любых других неожиданных ошибок
                error_message = f"❌ Произошла непредвиденная ошибка:\n{str(e)}"
                print(error_message)
                import traceback
                traceback.print_exc()
                bot.reply_to(message, error_message)
            
    except Exception as e:
        if BOT_TOKEN is None:
            print("❌ BOT_TOKEN не найден")
            return
        bot = telebot.TeleBot(BOT_TOKEN)
        bot.reply_to(message, f"❌ Произошла ошибка: {str(e)}")
    finally:
        # Удаляем временный файл в любом случае
        if temp_file_name and os.path.exists(temp_file_name):
            try:
                os.close(os.open(temp_file_name, os.O_RDONLY))  # Закрываем открытые дескрипторы
                os.remove(temp_file_name)
                print(f"Временный файл {temp_file_name} удален")
            except Exception as e:
                print(f"Ошибка при удалении временного файла: {e}")