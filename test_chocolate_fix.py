#!/usr/bin/env python3
"""
Специальный тест для исправления проблемы с Chocolate Sales.csv
"""

import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

def test_chocolate_csv_parsing():
    """Тестирование парсинга Chocolate Sales.csv"""
    file_path = "test_datasets/Chocolate Sales.csv"
    
    print("="*60)
    print("ТЕСТИРОВАНИЕ ПАРСИНГА CHOCOLATE SALES.CSV")
    print("="*60)
    
    # Читаем файл построчно
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"Всего строк: {len(lines)}")
    print(f"Заголовок: {lines[0].strip()}")
    print(f"Первая строка данных: {lines[1].strip()}")
    
    # Пробуем исправить парсинг
    header = lines[0].strip().split(',')
    print(f"Заголовки: {header}")
    
    data = []
    for i, line in enumerate(lines[1:], 1):
        line = line.strip()
        if not line:
            continue
            
        print(f"\nОбработка строки {i}: {line[:100]}...")
        
        # Убираем внешние кавычки
        if line.startswith('"') and line.endswith('"'):
            line = line[1:-1]
        
        # Разбиваем по запятой, но учитываем кавычки
        parts = []
        current_part = ""
        in_quotes = False
        
        for char in line:
            if char == '"':
                in_quotes = not in_quotes
            elif char == ',' and not in_quotes:
                parts.append(current_part.strip())
                current_part = ""
            else:
                current_part += char
        
        # Добавляем последнюю часть
        parts.append(current_part.strip())
        
        # Убираем лишние кавычки из каждой части
        cleaned_parts = []
        for part in parts:
            if part.startswith('"') and part.endswith('"'):
                part = part[1:-1]
            cleaned_parts.append(part)
        
        print(f"  Разбито на {len(cleaned_parts)} частей: {cleaned_parts}")
        
        # Убеждаемся, что у нас правильное количество столбцов
        while len(cleaned_parts) < len(header):
            cleaned_parts.append("")
        
        data.append(cleaned_parts[:len(header)])
    
    # Создаем DataFrame
    import pandas as pd
    df = pd.DataFrame(data, columns=header)
    
    # Преобразуем Amount, Boxes Shipped и Date
    if 'Amount' in df.columns:
        df['Amount'] = df['Amount'].str.replace('$', '', regex=False).str.replace(',', '', regex=False)
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    if 'Boxes Shipped' in df.columns:
        df['Boxes Shipped'] = pd.to_numeric(df['Boxes Shipped'], errors='coerce')
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    
    print(f"\nРезультат:")
    print(f"Размер DataFrame: {df.shape}")
    print(f"Столбцы: {list(df.columns)}")
    print(f"Первые 3 строки:")
    print(df.head(3))
    
    # Проверяем типы данных
    print(f"\nТипы данных:")
    for col in df.columns:
        print(f"  {col}: {df[col].dtype}")
    
    # Проверяем на NaN
    print(f"\nКоличество NaN в каждом столбце:")
    for col in df.columns:
        nan_count = df[col].isna().sum()
        print(f"  {col}: {nan_count}/{len(df)} ({nan_count/len(df)*100:.1f}%)")
    
    return df

if __name__ == "__main__":
    df = test_chocolate_csv_parsing() 