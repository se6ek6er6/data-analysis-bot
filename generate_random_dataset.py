import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import string

def generate_random_dataset(n_rows=200):
    """Генерирует случайный датасет с разнообразными типами данных"""
    
    # Случайные имена для колонок
    column_types = [
        ('ID', 'int'),
        ('Дата', 'date'),
        ('Имя', 'string'),
        ('Возраст', 'int'),
        ('Зарплата', 'float'),
        ('Рейтинг', 'float'),
        ('Активен', 'bool'),
        ('Город', 'categorical'),
        ('Департамент', 'categorical'),
        ('Оценка', 'int'),
        ('Время_работы', 'float'),
        ('Проекты', 'int'),
        ('Email', 'string'),
        ('Телефон', 'string'),
        ('Статус', 'categorical')
    ]
    
    data = {}
    
    for col_name, col_type in column_types:
        if col_type == 'int':
            if col_name == 'ID':
                data[col_name] = list(range(1, n_rows + 1))
            elif col_name == 'Возраст':
                data[col_name] = [random.randint(18, 65) for _ in range(n_rows)]
            elif col_name == 'Оценка':
                data[col_name] = [random.randint(1, 10) for _ in range(n_rows)]
            elif col_name == 'Проекты':
                data[col_name] = [random.randint(0, 20) for _ in range(n_rows)]
        
        elif col_type == 'float':
            if col_name == 'Зарплата':
                data[col_name] = [round(random.uniform(30000, 150000), 2) for _ in range(n_rows)]
            elif col_name == 'Рейтинг':
                data[col_name] = [round(random.uniform(1.0, 5.0), 2) for _ in range(n_rows)]
            elif col_name == 'Время_работы':
                data[col_name] = [round(random.uniform(0.5, 12.0), 1) for _ in range(n_rows)]
        
        elif col_type == 'date':
            start_date = datetime(2020, 1, 1)
            data[col_name] = [(start_date + timedelta(days=random.randint(0, 1000))).strftime('%Y-%m-%d') for _ in range(n_rows)]
        
        elif col_type == 'string':
            if col_name == 'Имя':
                names = ['Алексей', 'Мария', 'Дмитрий', 'Анна', 'Сергей', 'Елена', 'Андрей', 'Ольга', 'Михаил', 'Татьяна']
                data[col_name] = [random.choice(names) for _ in range(n_rows)]
            elif col_name == 'Email':
                domains = ['gmail.com', 'yandex.ru', 'mail.ru', 'outlook.com']
                data[col_name] = [f"user{random.randint(1, 999)}@{random.choice(domains)}" for _ in range(n_rows)]
            elif col_name == 'Телефон':
                data[col_name] = [f"+7{random.randint(9000000000, 9999999999)}" for _ in range(n_rows)]
        
        elif col_type == 'bool':
            data[col_name] = [random.choice([True, False]) for _ in range(n_rows)]
        
        elif col_type == 'categorical':
            if col_name == 'Город':
                cities = ['Москва', 'Санкт-Петербург', 'Новосибирск', 'Екатеринбург', 'Казань', 'Нижний Новгород', 'Челябинск', 'Самара']
                data[col_name] = [random.choice(cities) for _ in range(n_rows)]
            elif col_name == 'Департамент':
                depts = ['IT', 'Маркетинг', 'Продажи', 'HR', 'Финансы', 'Операции', 'Разработка', 'Дизайн']
                data[col_name] = [random.choice(depts) for _ in range(n_rows)]
            elif col_name == 'Статус':
                statuses = ['Активен', 'Неактивен', 'В ожидании', 'Заблокирован', 'Новый']
                data[col_name] = [random.choice(statuses) for _ in range(n_rows)]
    
    # Добавляем немного пропущенных значений для реалистичности
    for col_name in data:
        if col_name not in ['ID', 'Имя']:  # Не добавляем пропуски в ID и имена
            missing_count = random.randint(0, int(n_rows * 0.1))  # До 10% пропусков
            for _ in range(missing_count):
                idx = random.randint(0, n_rows - 1)
                data[col_name][idx] = None
    
    # Создаем DataFrame
    df = pd.DataFrame(data)
    
    # Добавляем несколько выбросов для тестирования
    if 'Зарплата' in df.columns:
        outlier_indices = random.sample(range(n_rows), min(3, n_rows // 20))
        for idx in outlier_indices:
            df.loc[idx, 'Зарплата'] = random.uniform(200000, 500000)
    
    if 'Возраст' in df.columns:
        outlier_indices = random.sample(range(n_rows), min(2, n_rows // 30))
        for idx in outlier_indices:
            df.loc[idx, 'Возраст'] = random.randint(70, 85)
    
    return df

if __name__ == "__main__":
    # Генерируем случайный датасет
    df = generate_random_dataset(200)
    
    # Сохраняем в разных форматах для тестирования
    df.to_csv('random_dataset.csv', index=False, encoding='utf-8-sig')  # Добавляем BOM для лучшей совместимости
    df.to_excel('random_dataset.xlsx', index=False)
    
    print(f"Создан случайный датасет с {len(df)} строками и {len(df.columns)} столбцами")
    print(f"Размер CSV файла: {len(df.to_csv(index=False, encoding='utf-8'))} байт")
    
    print("\nСтруктура данных:")
    print(df.info())
    
    print("\nПервые 5 строк:")
    print(df.head())
    
    print("\nСтатистика числовых столбцов:")
    print(df.describe())
    
    print("\nКоличество пропущенных значений:")
    print(df.isnull().sum())
    
    print("\nУникальные значения в категориальных столбцах:")
    for col in df.select_dtypes(include=['object']).columns:
        if df[col].nunique() < 20:  # Показываем только для столбцов с небольшим количеством уникальных значений
            print(f"{col}: {df[col].unique()}") 