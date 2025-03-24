import pandas as pd

def parse_xlsx(file_path):
    try:
        # Чтение xlsx файла
        df = pd.read_excel(file_path)

        # Вывод содержимого в консоль
        print(df)

    except Exception as e:
        print(f"Ошибка при обработке файла: {e}")

if __name__ == "__main__":
    file_path = "C:\\Work\\data-analysis-bot\\test_datasets\\Chocolate Sales.xlsx"  # Укажи путь к твоему xlsx файлу
    parse_xlsx(file_path)
