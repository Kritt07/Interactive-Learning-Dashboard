"""
Скрипт для генерации HTML отчета о статистике успеваемости студентов.
Может использоваться в CI/CD для автоматической генерации отчетов.
"""
import sys
import json
from pathlib import Path
from datetime import datetime
import pandas as pd

# Добавляем корневую директорию в путь
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.data_loader import get_data_loader
from src.config import DATA_DIR, PROCESSED_DIR
try:
    from src import analytics
except ImportError:
    # Fallback если модуль не найден
    analytics = None


def generate_html_report(output_path: Path = None):
    """
    Генерирует HTML отчет со статистикой успеваемости.
    
    Args:
        output_path: Путь для сохранения отчета. Если None, сохраняет в reports/report.html
    """
    if output_path is None:
        reports_dir = BASE_DIR / "reports"
        reports_dir.mkdir(exist_ok=True)
        output_path = reports_dir / "report.html"
    
    try:
        # Загружаем данные
        data_loader = get_data_loader(
            data_dir=str(DATA_DIR / "raw"),
            cache_dir=str(PROCESSED_DIR)
        )
        
        # Пробуем загрузить данные (если файлов нет, это нормально для CI)
        try:
            df = data_loader.load_data(use_cache=True)
            has_data = not df.empty
        except FileNotFoundError:
            df = pd.DataFrame()
            has_data = False
        
        # Генерируем статистику, если есть данные
        if has_data and analytics is not None:
            stats = analytics.calculate_statistics(df)
            # Получаем статистику по всем студентам
            student_stats = {}
            for student_id in df['student_id'].unique():
                student_stats[student_id] = analytics.get_student_statistics(df, student_id)
            # Получаем статистику по каждому предмету отдельно
            subject_stats = {}
            if 'subject' in df.columns:
                for subject in df['subject'].unique():
                    subject_stats[subject] = analytics.get_subject_statistics(df, subject=subject)
            
            # Формируем HTML
            html_content = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Отчет об успеваемости студентов</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stat-card h3 {{
            margin: 0 0 10px 0;
            color: #333;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .stat-card .value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
            margin: 0;
        }}
        .section {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            color: #333;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
            margin-top: 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #667eea;
            color: white;
            font-weight: 600;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .footer {{
            text-align: center;
            color: #666;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
        }}
        .no-data {{
            text-align: center;
            padding: 40px;
            color: #999;
            font-size: 1.2em;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Отчет об успеваемости студентов</h1>
        <p>Дата генерации: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</p>
    </div>
    
    <div class="stats-grid">
        <div class="stat-card">
            <h3>Всего записей</h3>
            <p class="value">{stats.get('total_grades', stats.get('total_records', 0))}</p>
        </div>
        <div class="stat-card">
            <h3>Студентов</h3>
            <p class="value">{stats.get('total_students', 0)}</p>
        </div>
        <div class="stat-card">
            <h3>Предметов</h3>
            <p class="value">{stats.get('total_subjects', 0)}</p>
        </div>
        <div class="stat-card">
            <h3>Средняя оценка</h3>
            <p class="value">{stats.get('average_grade', 0):.2f if isinstance(stats.get('average_grade'), (int, float)) else 'N/A'}</p>
        </div>
    </div>
    
    <div class="section">
        <h2>📈 Общая статистика</h2>
        <table>
            <tr>
                <th>Метрика</th>
                <th>Значение</th>
            </tr>
            <tr>
                <td>Минимальная оценка</td>
                <td>{stats.get('min_grade', 'N/A') if stats.get('min_grade') is not None else 'N/A'}</td>
            </tr>
            <tr>
                <td>Максимальная оценка</td>
                <td>{stats.get('max_grade', 'N/A') if stats.get('max_grade') is not None else 'N/A'}</td>
            </tr>
            <tr>
                <td>Медианная оценка</td>
                <td>{stats.get('median_grade', 'N/A') if stats.get('median_grade') is not None else 'N/A'}</td>
            </tr>
            <tr>
                <td>Стандартное отклонение</td>
                <td>{stats.get('std_grade', 'N/A') if stats.get('std_grade') is not None else 'N/A'}</td>
            </tr>
        </table>
    </div>
    
    <div class="section">
        <h2>📚 Статистика по предметам</h2>
        <table>
            <tr>
                <th>Предмет</th>
                <th>Средняя оценка</th>
                <th>Количество оценок</th>
            </tr>
"""
            
            # Добавляем статистику по предметам
            if isinstance(subject_stats, dict):
                for subject, subj_stats in subject_stats.items():
                    avg_grade = subj_stats.get('average_grade', 0)
                    if isinstance(avg_grade, (int, float)) and not pd.isna(avg_grade):
                        avg_grade_str = f"{avg_grade:.2f}"
                    else:
                        avg_grade_str = 'N/A'
                    html_content += f"""
            <tr>
                <td>{subject}</td>
                <td>{avg_grade_str}</td>
                <td>{subj_stats.get('total_grades', 0)}</td>
            </tr>
"""
            
            html_content += """
        </table>
    </div>
    
    <div class="section">
        <h2>👥 Топ студентов</h2>
        <table>
            <tr>
                <th>ID</th>
                <th>Имя</th>
                <th>Средняя оценка</th>
                <th>Количество оценок</th>
            </tr>
"""
            
            # Добавляем топ студентов (сортируем по средней оценке)
            top_students = sorted(
                student_stats.items(),
                key=lambda x: x[1].get('average_grade', 0),
                reverse=True
            )[:10]
            
            for student_id, stud_stats in top_students:
                avg_grade = stud_stats.get('average_grade', 0)
                if isinstance(avg_grade, (int, float)) and not pd.isna(avg_grade):
                    avg_grade_str = f"{avg_grade:.2f}"
                else:
                    avg_grade_str = 'N/A'
                html_content += f"""
            <tr>
                <td>{student_id}</td>
                <td>{stud_stats.get('student_name', 'N/A')}</td>
                <td>{avg_grade_str}</td>
                <td>{stud_stats.get('total_grades', 0)}</td>
            </tr>
"""
            
            html_content += """
        </table>
    </div>
    
    <div class="footer">
        <p>Сгенерировано автоматически системой Interactive Learning Dashboard</p>
    </div>
</body>
</html>
"""
        else:
            # Если данных нет
            html_content = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Отчет об успеваемости студентов</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            text-align: center;
        }}
        .no-data {{
            background: white;
            padding: 40px;
            border-radius: 10px;
            text-align: center;
            color: #999;
            font-size: 1.2em;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Отчет об успеваемости студентов</h1>
        <p>Дата генерации: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</p>
    </div>
    <div class="no-data">
        <p>Данные для генерации отчета отсутствуют.</p>
        <p>Поместите CSV или Excel файлы в директорию data/raw/</p>
    </div>
</body>
</html>
"""
        
        # Сохраняем отчет
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Отчет успешно сгенерирован: {output_path}")
        return str(output_path)
        
    except Exception as e:
        print(f"❌ Ошибка при генерации отчета: {e}")
        # Создаем отчет с ошибкой
        error_html = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Ошибка генерации отчета</title>
</head>
<body>
    <h1>Ошибка генерации отчета</h1>
    <p>{str(e)}</p>
</body>
</html>
"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(error_html)
        return None


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Генерация HTML отчета о статистике успеваемости')
    parser.add_argument('--output', '-o', type=str, help='Путь для сохранения отчета')
    
    args = parser.parse_args()
    
    output_path = Path(args.output) if args.output else None
    generate_html_report(output_path)
