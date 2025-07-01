import pandas as pd
import random
from datetime import datetime, timedelta

countries = [
    'USA', 'Germany', 'France', 'UK', 'Canada', 'Australia', 'Japan', 'Brazil', 'India', 'China',
    'Italy', 'Spain', 'Russia', 'Mexico', 'South Africa', 'Turkey', 'Poland', 'Sweden', 'Norway', 'Finland'
]
products = [
    'Chocolate', 'Coffee', 'Tea', 'Biscuits', 'Juice', 'Candy', 'Chips', 'Nuts', 'Soda', 'Water',
    'Cake', 'Bread', 'Milk', 'Cheese', 'Butter', 'Yogurt', 'Ice Cream', 'Cereal', 'Jam', 'Honey'
]
sales_people = [
    'John Smith', 'Anna Muller', 'Wei Zhang', 'Maria Garcia', 'Ivan Ivanov', 'Sara Lee', 'Tom Brown', 'Linda White',
    'Ahmed Hassan', 'Julia Rossi', 'Peter Svensson', 'Satoshi Tanaka', 'Carlos Silva', 'Fatima Zahra', 'Olga Petrova'
]
channels = ['Online', 'Retail', 'Wholesale']
regions = ['America', 'Europe', 'Asia', 'Africa']
promos = ['Yes', 'No']

rows = []
start_date = datetime(2022, 1, 1)
for i in range(3000):
    date = (start_date + timedelta(days=random.randint(0, 730))).strftime('%d-%b-%y')
    country = random.choice(countries)
    product = random.choice(products)
    person = random.choice(sales_people)
    channel = random.choice(channels)
    region = random.choice(regions)
    promo = random.choice(promos)
    amount = round(random.uniform(100, 10000), 2)
    boxes = random.randint(1, 200)
    discount = random.choice([0, 5, 10, 15, 20, 25]) if promo == 'Yes' else 0
    cost = round(amount * random.uniform(0.5, 0.85), 2)
    profit = round(amount - cost, 2)
    rows.append([
        date, country, product, person, channel, region, promo, amount, boxes, discount, cost, profit
    ])

df = pd.DataFrame(rows, columns=[
    'Date', 'Country', 'Product', 'Sales Person', 'Channel', 'Region', 'Promo',
    'Amount', 'Boxes Shipped', 'Discount', 'Cost', 'Profit'
])
df.to_csv('test_datasets/SalesData_advanced.csv', index=False)
print('Файл test_datasets/SalesData_advanced.csv создан!') 