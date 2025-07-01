import os
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
# Для локальной разработки используем localhost, если SERVER_URL не задан
SERVER_URL = os.getenv('SERVER_URL', 'http://localhost:5000')