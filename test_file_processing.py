#!/usr/bin/env python3
"""
Тестовый скрипт для проверки обработки различных файлов
"""

import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from server.analysis import load_data, detect_data_types, process_type
from server.utils import ensure_dir_exists, generate_unique_id

def test_file_processing(file_path):
    """Тестирование обработки конкретного файла"""
    print(f"\n{'='*60}")
    print(f"ТЕСТИРОВАНИЕ ФАЙЛА: {file_path}")
    print(f"{'='*60}")
    
    try:
        # Загружаем данные
        print("1. Загрузка данных...")
        df = load_data(file_path)
        
        # Определяем типы данных
        print("\n2. Определение типов данных...")
        data_types = detect_data_types(df)
        
        # Создаем тестовую директорию
        test_dir = f"test_output_{generate_unique_id()}"
        ensure_dir_exists(test_dir)
        
        # Обрабатываем файл
        print(f"\n3. Создание визуализаций в папке: {test_dir}")
        visualizations = process_type(file_path, test_dir)
        
        print(f"\n✅ УСПЕХ! Создано {len(visualizations)} визуализаций:")
        for viz in visualizations:
            print(f"  - {viz.get('type', 'unknown')}: {viz.get('path', 'unknown')}")
            
        return True
        
    except Exception as e:
        print(f"\n❌ ОШИБКА: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Основная функция тестирования"""
    test_files = [
        "test_datasets/test_data.csv",
        "test_datasets/Chocolate Sales.csv", 
        "test_datasets/Chocolate Sales.xlsx",
        "test_datasets/Mobiles Dataset (2025).csv"
    ]
    
    print("ТЕСТИРОВАНИЕ ОБРАБОТКИ ФАЙЛОВ")
    print("="*60)
    
    results = {}
    
    for file_path in test_files:
        if os.path.exists(file_path):
            results[file_path] = test_file_processing(file_path)
        else:
            print(f"\n❌ Файл не найден: {file_path}")
            results[file_path] = False
    
    # Итоговая статистика
    print(f"\n{'='*60}")
    print("ИТОГОВАЯ СТАТИСТИКА")
    print(f"{'='*60}")
    
    successful = sum(results.values())
    total = len(results)
    
    for file_path, success in results.items():
        status = "✅ УСПЕХ" if success else "❌ ОШИБКА"
        print(f"{status}: {file_path}")
    
    print(f"\nОбщий результат: {successful}/{total} файлов обработано успешно")
    
    if successful == total:
        print("🎉 ВСЕ ФАЙЛЫ ОБРАБОТАНЫ УСПЕШНО!")
    else:
        print("⚠️  Некоторые файлы не удалось обработать")

if __name__ == "__main__":
    main() 