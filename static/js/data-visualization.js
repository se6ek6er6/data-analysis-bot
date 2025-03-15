// Проверяем доступность библиотек
console.log("React доступен:", typeof React !== 'undefined');
console.log("ReactDOM доступен:", typeof ReactDOM !== 'undefined');
console.log("Recharts доступен:", typeof Recharts !== 'undefined');
console.log("PapaParse доступен:", typeof Papa !== 'undefined');

// Деструктурируем компоненты из Recharts
const {
  LineChart, Line, BarChart, Bar, PieChart, Pie, ResponsiveContainer,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, Cell
} = Recharts;

// Создаем простой компонент для визуализации данных
const DataVisualizationDashboard = () => {
  const [data, setData] = React.useState([]);
  const [columns, setColumns] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);
  const [debugInfo, setDebugInfo] = React.useState([]);

  // Функция для добавления отладочной информации
  const addDebugInfo = (message) => {
    console.log(message);
    setDebugInfo(prev => [...prev, message]);
  };

  // Эффект для загрузки данных при первом рендеринге
  React.useEffect(() => {
    const fetchData = async () => {
      try {
        addDebugInfo("Начинаем загрузку данных");
        
        // Получаем ID анализа из URL
        const analysisId = window.location.pathname.split('/').pop();
        addDebugInfo(`ID анализа: ${analysisId}`);
        
        // Загружаем CSV файл
        addDebugInfo("Пытаемся загрузить CSV файл");
        const fileContent = await window.fs.readFile(`static/analyses/${analysisId}/data.csv`);
        const csvText = new TextDecoder().decode(fileContent);
        addDebugInfo(`CSV файл загружен, размер: ${csvText.length} байт`);
        
        // Парсим CSV
        Papa.parse(csvText, {
          header: true,
          dynamicTyping: true,
          skipEmptyLines: true,
          complete: (results) => {
            addDebugInfo(`Парсинг завершен, найдено строк: ${results.data.length}`);
            
            if (results.data && results.data.length > 0) {
              setData(results.data);
              
              // Получаем список столбцов
              const allColumns = results.meta.fields || [];
              setColumns(allColumns);
              addDebugInfo(`Найдено столбцов: ${allColumns.join(', ')}`);
              
              // Пример базовой статистики
              const numericColumns = allColumns.filter(col => {
                return results.data.every(row => 
                  row[col] === null || row[col] === undefined || typeof row[col] === 'number'
                );
              });
              
              addDebugInfo(`Числовые столбцы: ${numericColumns.join(', ')}`);
            }
            
            setLoading(false);
          },
          error: (error) => {
            addDebugInfo(`Ошибка при парсинге CSV: ${error}`);
            setError(`Ошибка при обработке данных: ${error}`);
            setLoading(false);
          }
        });
      } catch (error) {
        addDebugInfo(`Ошибка: ${error.message}`);
        setError(`Ошибка загрузки данных: ${error.message}`);
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);

  // Рендеринг отладочной информации
  const renderDebugInfo = () => (
    <div className="mt-4 p-4 border rounded bg-gray-100">
      <h3 className="font-bold mb-2">Отладочная информация:</h3>
      <pre className="text-xs overflow-auto max-h-40 p-2 bg-gray-800 text-green-400 rounded">
        {debugInfo.map((info, index) => (
          <div key={index}>{info}</div>
        ))}
      </pre>
    </div>
  );

  // Если загрузка данных еще не завершена
  if (loading) {
    return (
      <div className="p-4">
        <div className="text-xl font-bold mb-4">Загрузка данных...</div>
        {renderDebugInfo()}
      </div>
    );
  }

  // Если произошла ошибка
  if (error) {
    return (
      <div className="p-4">
        <div className="text-xl font-bold text-red-500 mb-4">{error}</div>
        {renderDebugInfo()}
      </div>
    );
  }

  // Если все хорошо, показываем данные
  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Интерактивный анализ данных</h1>
      
      <div className="bg-blue-50 p-4 rounded mb-4">
        <h2 className="text-xl font-semibold mb-2">Информация о данных</h2>
        <p>Количество строк: <strong>{data.length}</strong></p>
        <p>Количество столбцов: <strong>{columns.length}</strong></p>
        <p>Столбцы: <strong>{columns.join(', ')}</strong></p>
      </div>
      
      {/* Пример простой визуализации: таблица с первыми 5 записями */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold mb-2">Предпросмотр данных</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full bg-white border">
            <thead>
              <tr>
                {columns.map(column => (
                  <th key={column} className="px-4 py-2 border">{column}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.slice(0, 5).map((row, rowIndex) => (
                <tr key={rowIndex}>
                  {columns.map(column => (
                    <td key={column} className="px-4 py-2 border">{row[column]}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      
      {/* Пример простого графика */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold mb-2">Пример графика</h2>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data.slice(0, 10)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={columns[0]} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey={columns.find(col => typeof data[0][col] === 'number')} fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
      
      {renderDebugInfo()}
    </div>
  );
};

// Рендерим компонент в DOM
ReactDOM.render(<DataVisualizationDashboard />, document.getElementById('root'));