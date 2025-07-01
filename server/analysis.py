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
from .advanced_analysis import AdvancedDataAnalyzer
from .interactive_plots import InteractivePlotGenerator

def detect_special_data_types(df, column):
    """Определение специальных типов данных (телефоны, email, ID и т.д.)"""
    import re
    
    # Убираем NaN значения для анализа
    non_null_data = df[column].dropna().astype(str)
    if len(non_null_data) == 0:
        return None
    
    # Паттерны для распознавания
    patterns = {
        'phone': {
            'patterns': [
                r'^\+?[0-9]{10,15}$',
                r'^\+?[0-9]{1,3}[-\s]?[0-9]{3}[-\s]?[0-9]{3}[-\s]?[0-9]{2}[-\s]?[0-9]{2}$',
                r'^[0-9]{10,11}$',
            ],
            'keywords': ['телефон', 'phone', 'тел', 'мобильный', 'mobile', 'моб']
        },
        'email': {
            'patterns': [
                r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            ],
            'keywords': ['email', 'почта', 'e-mail', 'mail']
        },
        'id': {
            'patterns': [
                r'^[0-9]+$'  # Только цифры
            ],
            'keywords': ['id', 'идентификатор', 'номер', 'code', 'индекс', 'index', 'ID', 'Id', 'Код', 'Номер']
        },
        'url': {
            'patterns': [
                r'^https?://[^\s/$.?#].[^\s]*$'
            ],
            'keywords': ['url', 'ссылка', 'link', 'сайт', 'website']
        }
    }
    
    # Проверяем название столбца на ключевые слова
    col_lower = column.lower()
    # Исключаем 'boxes shipped' из special
    if col_lower in ['boxes shipped', 'boxesshipped']:
        return None
    for data_type, config in patterns.items():
        if any(keyword in col_lower for keyword in config['keywords']):
            return data_type
    
    # Проверяем паттерны в данных
    for data_type, config in patterns.items():
        pattern_matches = 0
        for pattern in config['patterns']:
            matches = non_null_data.str.match(pattern, na=False).sum()
            pattern_matches += matches
        
        # Если больше 80% значений соответствуют паттерну
        if pattern_matches / len(non_null_data) > 0.8:
            return data_type
    
    return None

def detect_data_types(df):
    """Определить типы данных в DataFrame"""
    print("Определение типов данных...")
    
    # Получаем все столбцы
    all_columns = df.columns.tolist()
    numerical_columns = df.select_dtypes(include=['number']).columns.tolist()
    object_columns = df.select_dtypes(include=['object']).columns.tolist()
    categorical_columns = []
    date_columns = []
    special_columns = []
    
    # Анализируем каждый столбец (все типы)
    for col in all_columns:
        print(f"Анализ столбца '{col}'...")
        # Проверяем на специальные типы
        special_type = detect_special_data_types(df, col)
        if special_type:
            special_columns.append(col)
            print(f"  Столбец '{col}' определен как {special_type}")
            continue
        # Далее обычная логика для object-столбцов
        if col in object_columns:
            is_date = False
            date_keywords = ['дата', 'date', 'время', 'time', 'год', 'year', 'месяц', 'month', 'день', 'day']
            if any(keyword in col.lower() for keyword in date_keywords):
                try:
                    # Сначала пробуем стандартное преобразование
                    test_dates = pd.to_datetime(df[col], errors='coerce')
                    try:
                        is_all_nan = test_dates.isna().all()
                    except Exception:
                        is_all_nan = True
                    # Если не удалось — пробуем явно указать формат
                    if is_all_nan:
                        test_dates = pd.to_datetime(df[col], format='%d-%b-%y', errors='coerce')
                        try:
                            is_all_nan = test_dates.isna().all()
                        except Exception:
                            is_all_nan = True
                    if not is_all_nan:
                        date_columns.append(col)
                        is_date = True
                        print(f"  Столбец '{col}' определен как дата")
                except Exception as e:
                    pass
            if not is_date:
                cleaned_col = clean_numeric_column(df[col])
                if isinstance(cleaned_col, pd.Series) and cleaned_col.dtype != 'object':
                    try:
                        non_nan_ratio = 1.0 - cleaned_col.isna().mean()
                        if non_nan_ratio > 0.95:
                            numerical_columns.append(col)
                            print(f"  Столбец '{col}' определен как числовой")
                        else:
                            categorical_columns.append(col)
                            print(f"  Столбец '{col}' определен как категориальный (слишком много nan после преобразования)")
                    except Exception:
                        categorical_columns.append(col)
                        print(f"  Столбец '{col}' определен как категориальный (ошибка при проверке nan)")
                else:
                    unique_count = df[col].nunique()
                    total_count = len(df[col])
                    if unique_count <= total_count * 0.5 and unique_count <= 100:
                        categorical_columns.append(col)
                        print(f"  Столбец '{col}' определен как категориальный ({unique_count} уникальных значений)")
                    else:
                        categorical_columns.append(col)
                        print(f"  Столбец '{col}' определен как категориальный (много уникальных значений)")
    print(f"Итоговые типы данных:")
    print(f"  Числовые: {numerical_columns}")
    print(f"  Категориальные: {categorical_columns}")
    print(f"  Даты: {date_columns}")
    print(f"  Специальные: {special_columns}")
    return {
        'numerical': [col for col in numerical_columns if col not in special_columns],
        'categorical': categorical_columns,
        'date': date_columns,
        'special': special_columns
    }

def detect_encoding(file_path):
    """Определить кодировку файла"""
    try:
        import chardet
        with open(file_path, 'rb') as f:
            raw_data = f.read(10000)  # Читаем первые 10KB для определения кодировки
            result = chardet.detect(raw_data)
            detected_encoding = result['encoding']
            confidence = result['confidence']
            
            # Если уверенность низкая, возвращаем utf-8-sig
            if confidence < 0.7:
                return 'utf-8-sig'
            return detected_encoding
    except ImportError:
        return 'utf-8-sig'  # Возвращаем UTF-8 с BOM по умолчанию

def clean_numeric_column(series):
    """Очистка числовых столбцов от символов валют и форматирования"""
    if series.dtype == 'object':
        # Проверяем, содержит ли столбец в основном числовые данные
        # Считаем строки, которые можно преобразовать в числа
        numeric_count = 0
        total_count = 0
        
        for value in series.dropna():
            total_count += 1
            # Убираем символы валют и пробелы для проверки
            cleaned_value = str(value).replace('$', '').replace(',', '').replace(' ', '').strip()
            try:
                float(cleaned_value)
                numeric_count += 1
            except ValueError:
                pass
        
        # Если больше 70% значений можно преобразовать в числа, считаем столбец числовым
        if total_count > 0 and numeric_count / total_count > 0.7:
            # Очищаем только числовые значения, оставляем остальные как есть
            def clean_value(val):
                if pd.isna(val):
                    return val
                try:
                    # Убираем символы валют, пробелы, запятые
                    cleaned = str(val).replace('$', '').replace(',', '').replace(' ', '').strip()
                    return float(cleaned)
                except ValueError:
                    return val
            
            cleaned_series = series.apply(clean_value)
            # Проверяем, что получили числовой тип
            if cleaned_series.dtype == 'object':
                # Пробуем принудительно преобразовать в числовой тип
                try:
                    return pd.to_numeric(cleaned_series, errors='coerce')
                except:
                    return cleaned_series
            return cleaned_series
    
    return series

def load_data(file_path):
    """Загрузка данных с поддержкой различных форматов и кодировок"""
    print(f"Загрузка файла: {file_path}")
    
    try:
        # Определяем формат файла
        if file_path.endswith('.csv'):
            # Определяем кодировку
            encoding = detect_encoding(file_path)
            print(f"Определена кодировка: {encoding}")
            
            # Пробуем разные кодировки, если основная не работает
            encodings_to_try = [encoding, 'utf-8-sig', 'utf-8', 'latin-1', 'cp1251', 'iso-8859-1']
            
            for enc in encodings_to_try:
                try:
                    # Сначала пробуем стандартный парсинг
                    with open(file_path, 'r', encoding=enc) as f:
                        sample = f.read(1024)
                        if sample.strip():  # Проверяем, что файл не пустой
                            delimiter = csv.Sniffer().sniff(sample).delimiter
                            print(f"Определен разделитель: '{delimiter}'")
                        else:
                            delimiter = ','
                    
                    # Загружаем данные
                    df = pd.read_csv(file_path, delimiter=delimiter, encoding=enc, quotechar='"')
                    
                    # Проверяем, правильно ли загрузились данные
                    if (len(df.columns) == 1 and ',' in str(df.columns[0])) or (len(df.columns) < 2 or df.isna().iloc[:, 1:].all(axis=None)):
                        print("Обнаружена проблема с парсингом CSV, применяем специальную обработку...")
                        df = fix_malformed_csv(file_path, enc)
                    else:
                        print(f"Файл успешно загружен с кодировкой {enc}")
                    break
                except Exception as e:
                    print(f"Ошибка при загрузке с кодировкой {enc}: {e}")
                    continue
            else:
                raise ValueError(f"Не удалось загрузить файл ни с одной из кодировок: {encodings_to_try}")
                
        elif file_path.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_path, engine='openpyxl')
            print("Excel файл успешно загружен")
        else:
            raise ValueError(f"Неподдерживаемый формат файла: {file_path}")
        
        # Очищаем данные
        print("Очистка данных...")
        for col in df.columns:
            if df[col].dtype == 'object':
                # Убираем лишние пробелы
                df[col] = df[col].astype(str).str.strip()
                
                # Пытаемся преобразовать в числовой тип, если это возможно
                cleaned_col = clean_numeric_column(df[col])
                # Проверяем, действительно ли столбец стал числовым
                if isinstance(cleaned_col, pd.Series) and cleaned_col.dtype != 'object':
                    try:
                        if not cleaned_col.isna().all():
                            df[col] = cleaned_col
                            print(f"Столбец '{col}' преобразован в числовой тип")
                    except Exception:
                        pass
                else:
                    # Дополнительная проверка для известных числовых столбцов
                    if col in ['Amount', 'Boxes Shipped']:
                        try:
                            # Принудительная очистка и преобразование
                            if col == 'Amount':
                                cleaned = df[col].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False).str.strip()
                            else:
                                cleaned = df[col].astype(str).str.strip()
                            numeric_col = pd.to_numeric(cleaned, errors='coerce')
                            if not numeric_col.isna().all():
                                df[col] = numeric_col
                                print(f"Столбец '{col}' принудительно преобразован в числовой тип")
                        except Exception as e:
                            print(f"Ошибка при преобразовании столбца '{col}': {e}")
                    
                    # Дополнительная обработка для Mobile Dataset
                    mobile_numeric_columns = ['Mobile Weight', 'RAM', 'Front Camera', 'Back Camera', 'Battery Capacity', 
                                            'Screen Size', 'Launched Price (Pakistan)', 'Launched Price (India)', 
                                            'Launched Price (China)', 'Launched Price (USA)', 'Launched Price (Dubai)', 
                                            'Launched Year']
                    if col in mobile_numeric_columns:
                        try:
                            # Очищаем от символов валют, единиц измерения и пробелов
                            cleaned = df[col].astype(str).str.replace('g', '', regex=False).str.replace('GB', '', regex=False).str.replace('MP', '', regex=False).str.replace('mAh', '', regex=False).str.replace('inches', '', regex=False).str.replace('PKR', '', regex=False).str.replace('INR', '', regex=False).str.replace('CNY', '', regex=False).str.replace('USD', '', regex=False).str.replace('AED', '', regex=False).str.replace(',', '', regex=False).str.replace(' ', '', regex=False).str.strip()
                            numeric_col = pd.to_numeric(cleaned, errors='coerce')
                            if not numeric_col.isna().all():
                                df[col] = numeric_col
                                print(f"Столбец '{col}' (Mobile Dataset) принудительно преобразован в числовой тип")
                        except Exception as e:
                            print(f"Ошибка при преобразовании столбца '{col}' (Mobile Dataset): {e}")
        
        # Автоматически определяем и преобразуем даты
        for col in df.columns:
            if df[col].dtype == 'object':
                test_dates = pd.to_datetime(df[col], errors='coerce')
                try:
                    is_all_nan = test_dates.isna().all()
                except Exception:
                    is_all_nan = True
                if is_all_nan:
                    test_dates = pd.to_datetime(df[col], format='%d-%b-%y', errors='coerce')
                    try:
                        is_all_nan = test_dates.isna().all()
                    except Exception:
                        is_all_nan = True
                if not is_all_nan:  # Если хотя бы одна дата распознана
                    df[col] = test_dates
                    print(f"Столбец '{col}' преобразован в дату")
        
        # Гарантированная очистка и преобразование Amount и Boxes Shipped
        for col in ['Amount', 'Boxes Shipped']:
            if col in df.columns:
                df[col] = (
                    df[col]
                    .astype(str)
                    .str.replace('$', '', regex=False)
                    .str.replace(',', '', regex=False)
                    .str.strip()
                )
                df[col] = pd.to_numeric(df[col], errors='coerce')
                print(f"[Гарантированная очистка] Столбец '{col}' тип: {df[col].dtype}, примеры: {df[col].head().tolist()}")
        
        print(f"Данные загружены: {len(df)} строк, {len(df.columns)} столбцов")
        print(f"Типы данных: {df.dtypes.to_dict()}")
        print(f"Первые 5 строк:\n{df.head()}")
        
        return df
        
    except Exception as e:
        print(f"Ошибка при загрузке файла: {e}")
        raise

def fix_malformed_csv(file_path, encoding):
    """Исправление неправильно сформированных CSV файлов"""
    print("Применяем исправление для неправильно сформированного CSV...")
    
    data = []
    with open(file_path, 'r', encoding=encoding) as f:
        content = f.read()
    
    # Разбиваем на строки
    lines = content.split('\n')
    
    # Пропускаем заголовок и убираем BOM символ
    header_line = lines[0].strip()
    if header_line.startswith('\ufeff'):
        header_line = header_line[1:]  # Убираем BOM символ
    header = header_line.split(',')
    print(f"Заголовки: {header}")
    
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
            
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
        
        # Исправляем разделенные числовые значения
        # Если у нас больше частей, чем заголовков, объединяем числовые части
        if len(cleaned_parts) > len(header):
            # Ищем части, которые можно объединить в числа
            i = 0
            while i < len(cleaned_parts) - 1:
                # Проверяем, можно ли объединить текущую и следующую части в число
                current = cleaned_parts[i]
                next_part = cleaned_parts[i + 1]
                
                # Если текущая часть начинается с $ и следующая - число
                if current.startswith('$') and next_part.isdigit():
                    cleaned_parts[i] = current + ',' + next_part
                    cleaned_parts.pop(i + 1)
                else:
                    i += 1
        
        # Убеждаемся, что у нас правильное количество столбцов
        while len(cleaned_parts) < len(header):
            cleaned_parts.append("")
        
        data.append(cleaned_parts[:len(header)])
    
    # Создаем DataFrame
    df = pd.DataFrame(data, columns=header)
    
    # Преобразуем Amount, Boxes Shipped и Date
    if 'Amount' in df.columns:
        # Более тщательная очистка столбца Amount
        df['Amount'] = df['Amount'].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False).str.strip()
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
        print(f"Amount преобразован: {df['Amount'].dtype}, примеры: {df['Amount'].head().tolist()}")
    if 'Boxes Shipped' in df.columns:
        df['Boxes Shipped'] = pd.to_numeric(df['Boxes Shipped'], errors='coerce')
        print(f"Boxes Shipped преобразован: {df['Boxes Shipped'].dtype}, примеры: {df['Boxes Shipped'].head().tolist()}")
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        print(f"Date преобразован: {df['Date'].dtype}")
    
    # Дополнительная обработка для Mobile Dataset
    # Очищаем числовые столбцы от символов валют и единиц измерения
    numeric_columns = ['Mobile Weight', 'RAM', 'Front Camera', 'Back Camera', 'Battery Capacity', 
                      'Screen Size', 'Launched Price (Pakistan)', 'Launched Price (India)', 
                      'Launched Price (China)', 'Launched Price (USA)', 'Launched Price (Dubai)', 
                      'Launched Year']
    
    for col in numeric_columns:
        if col in df.columns:
            # Очищаем от символов валют, единиц измерения и пробелов
            df[col] = df[col].astype(str).str.replace('g', '', regex=False).str.replace('GB', '', regex=False).str.replace('MP', '', regex=False).str.replace('mAh', '', regex=False).str.replace('inches', '', regex=False).str.replace('PKR', '', regex=False).str.replace('INR', '', regex=False).str.replace('CNY', '', regex=False).str.replace('USD', '', regex=False).str.replace('AED', '', regex=False).str.replace(',', '', regex=False).str.replace(' ', '', regex=False).str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce')
            print(f"{col} преобразован: {df[col].dtype}, примеры: {df[col].head().tolist()}")
    
    print(f"Исправленный CSV загружен: {len(df)} строк, {len(df.columns)} столбцов")
    return df

def process_type(file_path, output_dir):
    """Обработка CSV файла и создание визуализаций"""
    visualizations = []
    
    # Гарантированно создаем папку для анализа
    os.makedirs(output_dir, exist_ok=True)
    print(f"Папка анализа создана/проверена: {output_dir}")
    
    try:
        df = load_data(file_path)
        
        # Базовый исследовательский анализ
        data_types = detect_data_types(df)
        numerical_columns = data_types['numerical']
        categorical_columns = data_types['categorical']
        date_columns = data_types['date']
        special_columns = data_types['special']
        
        # Приводим все числовые столбцы к числовому типу (на всякий случай)
        for col in numerical_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Исключаем специальные столбцы из числовых для статистических вычислений
        # но оставляем их для визуализации, если они числовые
        statistical_numerical = [col for col in numerical_columns if col not in special_columns]
        print(f"Числовые столбцы для статистики: {statistical_numerical}")
        print(f"Специальные столбцы (исключены из статистики): {special_columns}")
        
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
        
        # 3. Тепловая карта корреляций для числовых столбцов (исключая специальные)
        if len(statistical_numerical) > 1:
            fig_path = os.path.join(output_dir, 'correlation.png')
            plt.figure(figsize=(12, 10))
            corr_matrix = df[statistical_numerical].corr()
            sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt='.2f')
            plt.title('Корреляционная матрица')
            plt.tight_layout()  # Чтобы подписи не обрезались
            plt.savefig(fig_path)
            plt.close()
            visualizations.append({
                'type': 'correlation',
                'path': 'correlation.png'
            })
            
        # 4. Точечные диаграммы для пар числовых столбцов (исключая специальные)
        if len(statistical_numerical) >= 2:
            # Ограничиваем количество пар, чтобы не было слишком много графиков
            max_pairs = min(10, (len(statistical_numerical) * (len(statistical_numerical) - 1)) // 2)
            pairs_count = 0
            
            for i, col1 in enumerate(statistical_numerical):
                for col2 in statistical_numerical[i+1:]:
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
            # Проверяем, есть ли числовые столбцы для построения рядов (исключая специальные)
            if statistical_numerical:
                print(f"Обработка столбца с датой: {date_col}")
                # Конвертируем столбец с датой
                df[date_col] = pd.to_datetime(df[date_col])
                df = df.sort_values(by=date_col)
                
                # Строим график для каждого числового столбца (исключая специальные)
                for num_col in statistical_numerical[:3]:  # Ограничимся первыми 3 столбцами
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
            'numeric_stats': df[statistical_numerical].describe().to_dict() if statistical_numerical else {},
            'row_count': len(df),
            'column_count': len(df.columns),
            'missing_values': df.isnull().sum().to_dict(),
            'special_columns': special_columns,
            'data_types': {
                'numerical': numerical_columns,
                'categorical': categorical_columns,
                'date': date_columns,
                'special': special_columns
            }
        }
        
        # Гарантированно сохраняем stats.json
        try:
            with open(stats_path, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            print(f"Файл stats.json успешно сохранен: {stats_path}")
        except Exception as e:
            print(f"Ошибка при сохранении stats.json: {e}")
            # Создаем минимальный stats.json в случае ошибки
            minimal_stats = {
                'error': f'Ошибка при создании полной статистики: {str(e)}',
                'row_count': len(df),
                'column_count': len(df.columns)
            }
            with open(stats_path, 'w', encoding='utf-8') as f:
                json.dump(minimal_stats, f, ensure_ascii=False, indent=2)
            
        visualizations.append({
            'type': 'stats',
            'path': 'stats.json'
        })
        
        # 7. Продвинутый анализ данных
        print("Запуск продвинутого анализа...")
        try:
            analyzer = AdvancedDataAnalyzer(df, output_dir, special_columns=special_columns)
            advanced_results = analyzer.comprehensive_analysis()
            
            # Добавляем результаты продвинутого анализа в статистики
            stats['advanced_analysis'] = advanced_results
            with open(stats_path, 'w') as f:
                json.dump(stats, f, default=str)  # default=str для сериализации datetime
            
            # Добавляем ссылки на новые визуализации
            advanced_viz = [
                {'type': 'advanced_stats', 'path': 'basic_statistics.csv'},
                {'type': 'outliers', 'path': 'outliers_analysis.png'},
                {'type': 'clustering', 'path': 'clustering_analysis.png'},
                {'type': 'report', 'path': 'analysis_report.md'}
            ]
            visualizations.extend(advanced_viz)
            
            print("Продвинутый анализ завершен успешно")
            
        except Exception as e:
            print(f"Ошибка в продвинутом анализе: {e}")
            # Продолжаем работу без продвинутого анализа
        
        # 8. Создание интерактивных графиков
        print("Создание интерактивных графиков...")
        try:
            interactive_generator = InteractivePlotGenerator(df, output_dir, special_columns=special_columns)
            interactive_plots = interactive_generator.create_interactive_plots()
            
            # Добавляем ссылки на интерактивные графики
            for plot_key, plot_info in interactive_plots.items():
                visualizations.append({
                    'type': f'interactive_{plot_info["type"]}',
                    'path': plot_info['path'],
                    'plot_data': plot_info.get('plot_data', ''),
                    'column': plot_info.get('column', ''),
                    'x_column': plot_info.get('x_column', ''),
                    'y_column': plot_info.get('y_column', '')
                })
            
            print(f"Создано {len(interactive_plots)} интерактивных графиков")
            
        except Exception as e:
            print(f"Ошибка при создании интерактивных графиков: {e}")
            # Продолжаем работу без интерактивных графиков
                
        # --- ДОПОЛНИТЕЛЬНЫЕ ГРАФИКИ ---
        # Barplot: Amount по Country (топ-10)
        if 'Country' in df.columns and 'Amount' in df.columns:
            country_sales = df.groupby('Country')['Amount'].sum().sort_values(ascending=False).head(10)
            fig_path = os.path.join(output_dir, 'bar_Amount_by_Country.png')
            plt.figure(figsize=(12, 6))
            country_sales.plot(kind='bar')
            plt.title('Суммарные продажи по странам (топ-10)')
            plt.ylabel('Amount')
            plt.tight_layout()
            plt.savefig(fig_path)
            plt.close()
            visualizations.append({'type': 'bar', 'column': 'Country', 'y_column': 'Amount', 'path': 'bar_Amount_by_Country.png'})
        # Boxplot: Profit по Product (топ-10)
        if 'Product' in df.columns and 'Profit' in df.columns:
            top_products = df['Product'].value_counts().head(10).index
            fig_path = os.path.join(output_dir, 'box_Profit_by_Product.png')
            plt.figure(figsize=(14, 7))
            sns.boxplot(x='Product', y='Profit', data=df[df['Product'].isin(top_products)])
            plt.title('Распределение прибыли по продуктам (топ-10)')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(fig_path)
            plt.close()
            visualizations.append({'type': 'boxplot', 'x_column': 'Product', 'y_column': 'Profit', 'path': 'box_Profit_by_Product.png'})
        # Histogram: Discount
        if 'Discount' in df.columns:
            fig_path = os.path.join(output_dir, 'hist_Discount.png')
            plt.figure(figsize=(10, 6))
            sns.histplot(df['Discount'].dropna(), bins=10)
            plt.title('Распределение скидок')
            plt.xlabel('Discount')
            plt.tight_layout()
            plt.savefig(fig_path)
            plt.close()
            visualizations.append({'type': 'histogram', 'column': 'Discount', 'path': 'hist_Discount.png'})
        # Временной ряд: Amount по месяцам
        if 'Date' in df.columns and 'Amount' in df.columns:
            df['Month'] = df['Date'].dt.to_period('M')
            monthly_sales = df.groupby('Month')['Amount'].sum()
            fig_path = os.path.join(output_dir, 'time_Amount_by_Month.png')
            plt.figure(figsize=(12, 6))
            monthly_sales.plot()
            plt.title('Суммарные продажи по месяцам')
            plt.xlabel('Месяц')
            plt.ylabel('Amount')
            plt.tight_layout()
            plt.savefig(fig_path)
            plt.close()
            visualizations.append({'type': 'time_series', 'x_column': 'Month', 'y_column': 'Amount', 'path': 'time_Amount_by_Month.png'})
        # --- ПРОГНОЗЫ ---
        from sklearn.linear_model import LinearRegression
        # Прогноз Amount на следующий месяц
        if 'Date' in df.columns and 'Amount' in df.columns:
            df_sorted = df.sort_values('Date')
            df_sorted = df_sorted.dropna(subset=['Date', 'Amount'])
            if len(df_sorted) > 10:
                df_sorted['Date_ordinal'] = df_sorted['Date'].map(lambda x: x.toordinal())
                X = df_sorted['Date_ordinal'].values.reshape(-1, 1)
                y = df_sorted['Amount'].values
                model = LinearRegression().fit(X, y)
                next_month = df_sorted['Date'].max() + pd.DateOffset(months=1)
                next_month_ord = next_month.toordinal()
                y_pred = model.predict(np.array([[next_month_ord]]))[0]
                # Сохраняем прогноз в файл
                with open(os.path.join(output_dir, 'forecast_Amount.txt'), 'w', encoding='utf-8') as f:
                    f.write(f'Прогноз Amount на {next_month.strftime("%b-%Y")}: {y_pred:.2f}\n')
                visualizations.append({'type': 'forecast', 'target': 'Amount', 'path': 'forecast_Amount.txt'})
        # Прогноз Profit на следующий месяц
        if 'Date' in df.columns and 'Profit' in df.columns:
            df_sorted = df.sort_values('Date')
            df_sorted = df_sorted.dropna(subset=['Date', 'Profit'])
            if len(df_sorted) > 10:
                df_sorted['Date_ordinal'] = df_sorted['Date'].map(lambda x: x.toordinal())
                X = df_sorted['Date_ordinal'].values.reshape(-1, 1)
                y = df_sorted['Profit'].values
                model = LinearRegression().fit(X, y)
                next_month = df_sorted['Date'].max() + pd.DateOffset(months=1)
                next_month_ord = next_month.toordinal()
                y_pred = model.predict(np.array([[next_month_ord]]))[0]
                with open(os.path.join(output_dir, 'forecast_Profit.txt'), 'w', encoding='utf-8') as f:
                    f.write(f'Прогноз Profit на {next_month.strftime("%b-%Y")}: {y_pred:.2f}\n')
                visualizations.append({'type': 'forecast', 'target': 'Profit', 'path': 'forecast_Profit.txt'})
        
        return visualizations
        
    except Exception as e:
        print(f"Ошибка обработки CSV: {str(e)}")
        # Создаем файл с ошибкой
        error_path = os.path.join(output_dir, 'error.txt')
        with open(error_path, 'w') as f:
            f.write(f"Ошибка при обработке файла: {str(e)}")
            
        return [{'type': 'error', 'message': str(e), 'path': 'error.txt'}]