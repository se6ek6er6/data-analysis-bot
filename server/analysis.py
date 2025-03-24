import matplotlib
matplotlib.use('Agg')  # Использование не интерактивного бэкенда
import csv
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import json
import numpy as np
from .utils import ensure_dir_exists
import mimetypes

def detect_data_types(df):
    """Определить типы данных в DataFrame"""
    numerical_columns = df.select_dtypes(include=['number']).columns.tolist()
    categorical_columns = df.select_dtypes(include=['object']).columns.tolist()
    date_columns = []
    
    # Попытка определить столбцы с датами
    for col in categorical_columns:
        try:
            # Если в названии столбца есть слово "дата" или "date", попробуем сразу его преобразовать
            if "дата" in col.lower() or "date" in col.lower():
                df[col] = pd.to_datetime(df[col], errors='coerce')
                date_columns.append(col)
                continue
                
            # Стандартная проверка преобразования
            pd.to_datetime(df[col])
            date_columns.append(col)
        except:
            pass
            
    # Удалить столбцы с датами из категориальных
    categorical_columns = [col for col in categorical_columns if col not in date_columns]
    
    return {
        'numerical': numerical_columns,
        'categorical': categorical_columns,
        'date': date_columns
    }


# Пример использования
#file_path = 'uploads/data.csv'

def load_data(file_path):
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type == 'text/csv' or file_path.endswith('.csv'):
        # Определяем разделитель автоматически
        with open(file_path, 'r', encoding='utf-8') as f:
            sample = f.read(1024)
            delimiter = csv.Sniffer().sniff(sample).delimiter
        return pd.read_csv(file_path, delimiter=delimiter)
    elif mime_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' or file_path.endswith(('.xls', '.xlsx')):
        print(pd.read_excel(file_path, engine='openpyxl'))
        return pd.read_excel(file_path, engine='openpyxl')
    else:
        raise ValueError(f"Неподдерживаемый формат файла: {file_path}")
    
    #if df:
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].str.strip()  # Убираем пробелы
                df[col] = df[col].str.replace(r'[^\d,.]', '', regex=True)  # Убираем символы ($, пробелы и т. д.)

                # Попытка преобразовать строки в числовые значения
                try:
                    df[col] = pd.to_numeric(df[col], errors='ignore')
                except Exception as e:
                    print(f"Не удалось преобразовать {col}: {e}")

        # Автоматически определяем и преобразуем даты
        for col in df.columns:
            try:
                df[col] = pd.to_datetime(df[col], errors='ignore', dayfirst=True)  # Поддержка формата DD-MM-YY
            except Exception as e:
                print(f"Ошибка преобразования даты в столбце {col}: {e}")

        print(df.head())
        return df

def process_type(file_path, output_dir):
    """Обработка CSV файла и создание визуализаций"""
    visualizations = []
    
    try:
        df = load_data(file_path)
        
        # Базовый исследовательский анализ
        data_types = detect_data_types(df)
        numerical_columns = data_types['numerical']
        categorical_columns = data_types['categorical']
        date_columns = data_types['date']
        
        # Сохраняем информацию о столбцах
        columns_info = {
            'total_columns': len(df.columns),
            'total_rows': len(df),
            'columns': {col: str(df[col].dtype) for col in df.columns}
        }
        
        with open(os.path.join(output_dir, 'columns_info.json'), 'w') as f:
            json.dump(columns_info, f)
        
        # 1. Графики распределения для числовых столбцов
        for col in numerical_columns:
            fig_path = os.path.join(output_dir, f'dist_{col}.png')
            plt.figure(figsize=(10, 6))
            sns.histplot(df[col].dropna())
            plt.title(f'Распределение {col}')
            plt.savefig(fig_path)
            plt.close()
            visualizations.append({
                'type': 'distribution',
                'column': col,
                'path': f'dist_{col}.png'
            })
        
        # 2. Столбчатые диаграммы для категориальных столбцов
        for col in categorical_columns:
            if df[col].nunique() < 20:  # Только для столбцов с разумным количеством категорий
                fig_path = os.path.join(output_dir, f'bar_{col}.png')
                plt.figure(figsize=(10, 6))
                value_counts = df[col].value_counts().sort_values(ascending=False).head(10)
                value_counts.plot(kind='bar')
                plt.title(f'Топ-10 категорий: {col}')
                plt.savefig(fig_path)
                plt.close()
                visualizations.append({
                    'type': 'bar',
                    'column': col,
                    'path': f'bar_{col}.png'
                })
        
        # 3. Тепловая карта корреляций для числовых столбцов
        if len(numerical_columns) > 1:
            fig_path = os.path.join(output_dir, 'correlation.png')
            plt.figure(figsize=(12, 10))
            corr_matrix = df[numerical_columns].corr()
            sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt='.2f')
            plt.title('Корреляционная матрица')
            plt.tight_layout()  # Чтобы подписи не обрезались
            plt.savefig(fig_path)
            plt.close()
            visualizations.append({
                'type': 'correlation',
                'path': 'correlation.png'
            })
            
        # 4. Точечные диаграммы для пар числовых столбцов
        if len(numerical_columns) >= 2:
            # Ограничиваем количество пар, чтобы не было слишком много графиков
            max_pairs = min(10, (len(numerical_columns) * (len(numerical_columns) - 1)) // 2)
            pairs_count = 0
            
            for i, col1 in enumerate(numerical_columns):
                for col2 in numerical_columns[i+1:]:
                    if pairs_count >= max_pairs:
                        break
                        
                    fig_path = os.path.join(output_dir, f'scatter_{col1}_{col2}.png')
                    plt.figure(figsize=(8, 6))
                    plt.scatter(df[col1], df[col2], alpha=0.5)
                    plt.xlabel(col1)
                    plt.ylabel(col2)
                    plt.title(f'{col1} vs {col2}')
                    
                    # Добавим линию тренда, если есть корреляция
                    if abs(df[col1].corr(df[col2])) > 0.3:
                        z = np.polyfit(df[col1].dropna(), df[col2].dropna(), 1)
                        p = np.poly1d(z)
                        plt.plot(df[col1], p(df[col1]), "r--")
                        
                    plt.savefig(fig_path)
                    plt.close()
                    visualizations.append({
                        'type': 'scatter',
                        'x_column': col1,
                        'y_column': col2,
                        'path': f'scatter_{col1}_{col2}.png'
                    })
                    
                    pairs_count += 1
        
        # 5. Временные ряды для столбцов с датами (если есть)
        print(f"Обработка временных рядов. Столбцы с датами: {date_columns}")
        for date_col in date_columns:
            # Проверяем, есть ли числовые столбцы для построения рядов
            if numerical_columns:
                print(f"Обработка столбца с датой: {date_col}")
                # Конвертируем столбец с датой
                df[date_col] = pd.to_datetime(df[date_col])
                df = df.sort_values(by=date_col)
                
                # Строим график для каждого числового столбца
                for num_col in numerical_columns[:3]:  # Ограничимся первыми 3 столбцами
                    print(f"Создание временного ряда: {num_col} по {date_col}")
                    fig_path = os.path.join(output_dir, f'time_{date_col}_{num_col}.png')
                    plt.figure(figsize=(12, 6))
                    plt.plot(df[date_col], df[num_col])
                    plt.xlabel(date_col)
                    plt.ylabel(num_col)
                    plt.title(f'Временной ряд: {num_col} по {date_col}')
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    plt.savefig(fig_path)
                    plt.close()
                    visualizations.append({
                        'type': 'time_series',
                        'x_column': date_col,
                        'y_column': num_col,
                        'path': f'time_{date_col}_{num_col}.png'
                    })
                    print(f"Временной ряд создан: time_{date_col}_{num_col}.png")
        
        # 6. Создаем сводную таблицу с основными статистиками
        stats_path = os.path.join(output_dir, 'stats.json')
        stats = {
            'numeric_stats': df[numerical_columns].describe().to_dict(),
            'row_count': len(df),
            'column_count': len(df.columns),
            'missing_values': df.isnull().sum().to_dict()
        }
        
        with open(stats_path, 'w') as f:
            json.dump(stats, f)
            
        visualizations.append({
            'type': 'stats',
            'path': 'stats.json'
        })
                
        return visualizations
        
    except Exception as e:
        print(f"Ошибка обработки CSV: {str(e)}")
        # Создаем файл с ошибкой
        error_path = os.path.join(output_dir, 'error.txt')
        with open(error_path, 'w') as f:
            f.write(f"Ошибка при обработке файла: {str(e)}")
            
        return [{'type': 'error', 'message': str(e), 'path': 'error.txt'}]