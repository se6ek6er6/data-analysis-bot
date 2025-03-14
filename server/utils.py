import os
import uuid
import shutil

def ensure_dir_exists(directory):
    """Убедиться, что директория существует, создать если нет"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def generate_unique_id():
    """Сгенерировать уникальный ID для анализа"""
    return str(uuid.uuid4())

def save_uploaded_file(file, directory, filename=None):
    """Сохранить загруженный файл"""
    ensure_dir_exists(directory)
    if filename is None:
        filename = file.filename
    file_path = os.path.join(directory, filename)
    file.save(file_path)
    return file_path

def create_file_copies(original_path, analysis_id):
    """Создать копии файла для разных способов доступа"""
    # Копия с именем data.csv в директории анализа
    analysis_dir = os.path.dirname(original_path)
    data_csv_path = os.path.join(analysis_dir, 'data.csv')
    
    try:
        shutil.copy(original_path, data_csv_path)
        print(f"Файл скопирован в: {data_csv_path}")
    except Exception as e:
        print(f"Ошибка при копировании файла: {e}")
    
    return [data_csv_path]