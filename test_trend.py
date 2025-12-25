import pandas as pd
from src import plots

# Загружаем данные
df = pd.read_csv('data/raw/students_raw.csv')
print(f"Всего записей: {len(df)}")
print(f"Студентов: {df['student_id'].nunique()}")
print(f"Предметов: {df['subject'].nunique()}")

# Тест 1: Все данные
print("\n=== Тест 1: Все данные ===")
plot1 = plots.create_performance_trend_plot(df)
if plot1.get('data'):
    data1 = plot1['data'][0]
    print(f"Количество точек: {len(data1.get('x', []))}")
    if data1.get('x'):
        print(f"Месяца: {data1['x']}")
        print(f"Оценки: {data1['y']}")

# Тест 2: Конкретный студент
print("\n=== Тест 2: Студент ID=1 ===")
plot2 = plots.create_performance_trend_plot(df, student_id=1)
if plot2.get('data'):
    data2 = plot2['data'][0]
    print(f"Количество точек: {len(data2.get('x', []))}")
    if data2.get('x'):
        print(f"Месяца: {data2['x'][:5]}...")
        print(f"Оценки: {data2['y'][:5]}...")

# Тест 3: Конкретный предмет
print("\n=== Тест 3: Предмет 'Математика' ===")
plot3 = plots.create_performance_trend_plot(df, subject='Математика')
if plot3.get('data'):
    data3 = plot3['data'][0]
    print(f"Количество точек: {len(data3.get('x', []))}")
    if data3.get('x'):
        print(f"Месяца: {data3['x'][:5]}...")
        print(f"Оценки: {data3['y'][:5]}...")

# Тест 4: Студент + предмет
print("\n=== Тест 4: Студент ID=1, Предмет 'Математика' ===")
plot4 = plots.create_performance_trend_plot(df, student_id=1, subject='Математика')
if plot4.get('data'):
    data4 = plot4['data'][0]
    print(f"Количество точек: {len(data4.get('x', []))}")
    if data4.get('x'):
        print(f"Месяца: {data4['x']}")
        print(f"Оценки: {data4['y']}")

# Проверка данных студента 1
print("\n=== Проверка исходных данных студента 1 ===")
student1_df = df[df['student_id'] == 1].copy()
student1_df['date'] = pd.to_datetime(student1_df['date'])
student1_df = student1_df.sort_values('date')
print(f"Записей у студента 1: {len(student1_df)}")
print(f"\nПервые 10 записей:")
print(student1_df[['date', 'subject', 'grade']].head(10))
print(f"\nГруппировка по месяцам:")
student1_df['month'] = student1_df['date'].dt.to_period('M')
monthly = student1_df.groupby('month')['grade'].agg(['mean', 'count'])
print(monthly)

