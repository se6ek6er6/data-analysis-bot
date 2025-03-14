from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import json
from datetime import datetime
import pandas as pd
from .analysis import process_csv
from .utils import ensure_dir_exists, generate_unique_id, save_uploaded_file, create_file_copies
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from bot.config import BOT_TOKEN, SERVER_URL
import telebot
from bot.bot import bot

app = Flask(__name__, 
            template_folder='../templates',
            static_folder='../static')

@app.route('/')
def index():
    return "Бот работает!", 200

# Добавьте webhook-маршрут
@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "OK"

@app.route('/process', methods=['POST'])
def process_file():
    if 'file' not in request.files:
        return jsonify({'error': 'Отсутствует часть файла'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Не выбран файл'}), 400
        
    # Получаем данные о пользователе (если есть)
    user_id = request.form.get('user_id', 'anonymous')
    username = request.form.get('username', 'anonymous')
    
    # Создаем уникальный ID для этого анализа
    analysis_id = generate_unique_id()
    
    # Создаем директорию для этого анализа
    analysis_dir = os.path.join(app.static_folder, 'analyses', analysis_id)
    ensure_dir_exists(analysis_dir)
    
    try:
        # Сохраняем оригинальный файл
        file_path = save_uploaded_file(file, analysis_dir)
        
        # Создаем копии файла для разных способов доступа
        file_copies = create_file_copies(file_path, analysis_id)
        
        # Проверяем расширение файла
        if file.filename.endswith('.csv'):
            # Обрабатываем файл
            visualizations = process_csv(file_path, analysis_dir)
        else:
            return jsonify({'error': 'Неподдерживаемый тип файла. Поддерживаются только CSV.'}), 400
        
        # Генерируем URL веб-приложения
        web_app_url = f"/analysis/{analysis_id}"
        
        # Сохраняем метаданные
        metadata = {
            'file_name': file.filename,
            'visualizations': visualizations,
            'created_at': datetime.now().isoformat(),
            'user_id': user_id,
            'username': username
        }
        
        with open(os.path.join(analysis_dir, 'metadata.json'), 'w') as f:
            json.dump(metadata, f)
        
        return jsonify({
            'web_app_url': web_app_url, 
            'analysis_id': analysis_id,
            'visualizations_count': len(visualizations)
        })
        
    except Exception as e:
        # В случае ошибки, возвращаем сообщение
        return jsonify({'error': str(e)}), 500

@app.route('/analysis/<analysis_id>')
def view_analysis(analysis_id):
    analysis_dir = os.path.join(app.static_folder, 'analyses', analysis_id)
    
    if not os.path.exists(analysis_dir):
        return "Анализ не найден", 404
    
    # Загружаем метаданные
    try:
        with open(os.path.join(analysis_dir, 'metadata.json'), 'r') as f:
            metadata = json.load(f)
        
        return render_template(
            'analysis.html', 
            analysis_id=analysis_id, 
            metadata=metadata,
            file_name=metadata['file_name'],
            visualizations=metadata['visualizations'],
            created_at=metadata.get('created_at', 'Неизвестно')
        )
    except Exception as e:
        return f"Ошибка загрузки анализа: {str(e)}", 500

# Маршрут для интерактивного анализа
@app.route('/interactive/<analysis_id>')
def interactive_analysis(analysis_id):
    analysis_dir = os.path.join(app.static_folder, 'analyses', analysis_id)
    
    if not os.path.exists(analysis_dir):
        return "Анализ не найден", 404
        
    # Проверяем наличие метаданных
    metadata_path = os.path.join(analysis_dir, 'metadata.json')
    if not os.path.exists(metadata_path):
        return "Метаданные анализа не найдены", 404
        
    try:
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
            
        return render_template(
            'interactive.html',
            analysis_id=analysis_id,
            file_name=metadata['file_name']
        )
    except Exception as e:
        return f"Ошибка загрузки интерактивного анализа: {str(e)}", 500

# Вместо включения кода JavaScript в строковую переменную, 
# лучше создать отдельный файл и отдавать его
@app.route('/static/js/data-visualization.js')
def data_visualization_js():
    # Отдаем файл из директории static/js
    js_file_path = os.path.join(app.static_folder, 'js', 'data-visualization.js')
    js_dir = os.path.dirname(js_file_path)
    
    # Если директория не существует, создаем ее
    if not os.path.exists(js_dir):
        os.makedirs(js_dir)
    
    # Если файла нет, создаем его с базовым содержимым
    if not os.path.exists(js_file_path):
        with open(js_file_path, 'w', encoding='utf-8') as f:
            f.write('''
// Код React-компонента для интерактивного анализа
const { useState, useEffect } = React;
const { BarChart, Bar, LineChart, Line, PieChart, Pie, ScatterChart, Scatter, 
       XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } = Recharts;

const DataVisualizationDashboard = () => {
  // Состояние компонента здесь...
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Логика загрузки данных здесь...
    const fetchData = async () => {
      try {
        // Базовая загрузка
        setLoading(false);
      } catch (error) {
        setError("Ошибка загрузки данных");
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);

  // Возвращаем JSX содержимое компонента
  return (
    <div className="p-4">
      <h1 className="text-xl font-bold mb-4">Интерактивный анализ данных</h1>
      
      {loading && <p>Загрузка данных...</p>}
      
      {error && (
        <div className="text-red-500">
          <p>{error}</p>
        </div>
      )}
      
      {!loading && !error && (
        <div>
          <p>Данные успешно загружены!</p>
          {/* Здесь будут компоненты визуализации */}
        </div>
      )}
    </div>
  );
};

// Рендерим приложение в DOM
ReactDOM.render(
  <DataVisualizationDashboard />,
  document.getElementById('root')
);
''')
    
    return send_from_directory(os.path.dirname(js_file_path), 
                               os.path.basename(js_file_path), 
                               mimetype='application/javascript')

def set_webhook():
    bot.remove_webhook()
    bot.set_webhook(url=f"{SERVER_URL}/{BOT_TOKEN}")

# Вызываем установку webhook при старте приложения
set_webhook()

if __name__ == '__main__':
    app.run(debug=True)