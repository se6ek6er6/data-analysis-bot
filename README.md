# Data Analysis Bot

Telegram бот для автоматического анализа данных и создания визуализаций.

## Возможности

- Загрузка CSV/XLS/XLSX файлов через Telegram
- Автоматическое создание визуализаций:
  - Гистограммы распределения
  - Столбчатые диаграммы
  - Корреляционные матрицы
  - Точечные диаграммы
  - Временные ряды
- Веб-интерфейс для просмотра результатов
- Интерактивный анализ данных

## Быстрый старт

1. **Создайте Telegram бота** через @BotFather
2. **Создайте файл `.env`** с вашим токеном:
   ```env
   BOT_TOKEN=your_telegram_bot_token_here
   SERVER_URL=http://localhost:5000
   ```
3. **Установите зависимости**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Запустите приложение**:
   ```bash
   python run_local.py
   ```

## Подробная настройка

См. файл [LOCAL_SETUP.md](LOCAL_SETUP.md) для подробных инструкций по настройке.

## Структура проекта

```
├── bot/                 # Telegram бот
│   ├── bot.py          # Обработчики сообщений
│   └── config.py       # Конфигурация
├── server/             # Веб-сервер
│   ├── app.py          # Flask маршруты
│   ├── analysis.py     # Анализ данных
│   └── utils.py        # Утилиты
├── static/             # Статические файлы
│   ├── analyses/       # Результаты анализов
│   └── js/            # JavaScript файлы
├── templates/          # HTML шаблоны
├── run.py             # Запуск с webhook
├── run_local.py       # Локальный запуск
└── requirements.txt   # Зависимости
```

## Технологии

- **Python** + Flask
- **Telegram Bot API**
- **Pandas** + Matplotlib + Seaborn
- **React** (для интерактивного интерфейса)