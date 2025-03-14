import os
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
SERVER_URL = os.getenv('SERVER_URL')