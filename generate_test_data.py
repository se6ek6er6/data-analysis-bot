import pandas as pd
import numpy as np

# Создаем тестовые данные
np.random.seed(42)
data = {
    'Дата': pd.date_range(start='2023-01-01', periods=100, freq='D'),
    'Продажи': np.random.randint(100, 1000, 100),
    'Расходы': np.random.randint(50, 500, 100),
    'Категория': np.random.choice(['A', 'B', 'C', 'D'], 100),
    'Регион': np.random.choice(['Север', 'Юг', 'Запад', 'Восток'], 100)
}

# Создаем DataFrame и сохраняем в CSV
df = pd.DataFrame(data)
df['Прибыль'] = df['Продажи'] - df['Расходы']
df.to_csv('test_data.csv', index=False, sep=';', encoding="utf-8-sig")  # Явно указываем разделитель
print("Файл test_data.csv создан успешно!")
