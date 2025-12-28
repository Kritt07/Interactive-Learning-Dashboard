# Interactive Student Performance Dashboard

## Description
Web-приложение для визуализации успеваемости студентов на основе интерактивных графиков. Приложение автоматически обрабатывает данные, агрегирует результаты и отображает динамику успеваемости.

## Installation

### Prerequisites
- Python 3.10+
- pip
- Git
- Браузер (Chrome, Firefox, Edge)

### Setup
```bash
git clone <repo-url>
cd <project-name>

# Создание виртуального окружения
python -m venv venv

# Активация виртуального окружения
# Windows (PowerShell): .\venv\Scripts\Activate.ps1
# Windows (CMD): venv\Scripts\activate.bat
# Linux/Mac: source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

### Подготовка данных
При первом запуске приложения отобразится приветственный экран, где вы сможете:
- Импортировать данные из CSV или Excel файла
- Указать систему оценивания (5-балльная, 100-балльная или кастомная)

Файл данных должен содержать следующие колонки: `student_id`, `student_name`, `subject`, `grade`, `date`.

> **Примечание:** В репозитории присутствует демонстрационный файл `data/sample.csv`, который показывает пример правильного формата данных. Этот файл используется только для ознакомления и не обрабатывается приложением напрямую. Для работы с данными поместите ваши CSV или Excel файлы в директорию `data/raw/`.

Если нужно сгенерировать тестовые данные для разработки:
```bash
python scripts/generate_sample_data.py
```

## Usage

### Start Backend

**Важно:** Перед запуском убедитесь, что все зависимости установлены:
```bash
pip install -r requirements.txt
```

Запуск сервера:
```bash
# Убедитесь, что виртуальное окружение активировано
# Вариант 1 (если uvicorn в PATH):
uvicorn src.app:app --reload

# Вариант 2 (универсальный, работает всегда):
python -m uvicorn src.app:app --reload
```

Backend будет доступен на: **http://localhost:8000**

> **Примечание:** Если команда `uvicorn` не распознается, используйте `python -m uvicorn`. Если возникают ошибки типа `ModuleNotFoundError`, убедитесь, что все зависимости установлены командой `pip install -r requirements.txt`

### Проверка работы API

- **http://localhost:8000** - информация об API
- **http://localhost:8000/docs** - интерактивная документация Swagger
- **http://localhost:8000/health** - проверка работоспособности

### Start Frontend

**Вариант 1: Открыть файл напрямую**
1. Убедитесь, что backend запущен
2. Откройте `frontend/index.html` в браузере

**Вариант 2: Локальный HTTP сервер (рекомендуется)**
```bash
cd frontend
python -m http.server 8080
# Откройте в браузере: http://localhost:8080
```

### Примеры использования API

#### Базовый пример - получение данных для графиков
```python
import requests

# Получение данных для построения графиков
response = requests.get("http://localhost:8000/api/plot-data")
print(response.json())
```

#### Проверка статуса данных
```python
import requests

# Проверка наличия данных и системы оценивания
response = requests.get("http://localhost:8000/api/data-status")
status = response.json()
print(f"Данные загружены: {status['has_data']}")
print(f"Всего записей: {status['total_records']}")
```

#### Получение списка студентов
```python
import requests

# Получение списка всех студентов
response = requests.get("http://localhost:8000/api/students")
students = response.json()
print(f"Найдено студентов: {len(students)}")
for student in students:
    print(f"ID: {student['student_id']}, Имя: {student['student_name']}")
```

#### Получение статистики
```python
import requests

# Общая статистика
response = requests.get("http://localhost:8000/api/statistics")
stats = response.json()
print(f"Средняя оценка: {stats['average_grade']:.2f}")
print(f"Всего записей: {stats['total_records']}")

# Статистика по конкретному студенту
student_id = 1
response = requests.get(f"http://localhost:8000/api/students/{student_id}/statistics")
student_stats = response.json()
print(f"Средняя оценка студента: {student_stats['average_grade']:.2f}")
```

#### Настройка системы оценивания
```python
import requests

# Установка 100-балльной системы оценивания
grading_system = {
    "system_type": "100-point",
    "max_grade": 100,
    "min_grade": 0
}
response = requests.post(
    "http://localhost:8000/api/grading-system",
    json=grading_system
)
print(response.json())
```

#### Импорт данных через API
```python
import requests

# Импорт CSV файла
with open('data.csv', 'rb') as f:
    files = {'file': ('data.csv', f, 'text/csv')}
    response = requests.post(
        "http://localhost:8000/api/import",
        files=files
    )
print(response.json())
```

#### Генерация отчета
```python
# Использование скрипта для генерации HTML отчета
import subprocess

subprocess.run(["python", "scripts/generate_report.py", "--output", "reports/report.html"])
print("Отчет сгенерирован в reports/report.html")
```

## Project Structure

```arduino
project/
├── src/
│   ├── app.py
│   ├── data_loader.py
│   ├── preprocess.py
│   ├── analytics.py
│   ├── plots.py
│   └── config.py
│
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
│
├── tests/
│   ├── test_data_loader.py
│   ├── test_preprocess.py
│   ├── test_analytics.py
│   └── test_api.py
│
├── data/
│   ├── sample.csv    # Демонстрационный файл с примером формата данных
│   ├── raw/          # Директория для импортированных пользователем данных
│   └── processed/    # Директория для кешированных и обработанных данных
│
├── scripts/
│   ├── generate_sample_data.py  # Генерация тестовых данных
│   ├── update_data.py            # Обновление данных
│   └── generate_report.py        # Генерация HTML отчетов
│
├── docs/
│   └── architecture.md
│
├── reports/                      # Сгенерированные отчеты
│
├── .github/workflows/
│   └── ci.yml                    # CI/CD pipeline с тестами, проверками и деплоем
│
├── requirements.txt
├── .gitignore
└── README.md
```

## Requirements

Основные зависимости:
- FastAPI - веб-фреймворк для API
- Uvicorn - ASGI сервер
- Pandas - обработка данных
- NumPy - численные вычисления
- Plotly - интерактивные графики
- scikit-learn - машинное обучение (опционально)

Для разработки:
- Pytest - тестирование
- Flake8 - проверка стиля кода
- Black - форматирование кода


## Testing

### Запуск всех тестов
```bash
pytest -v
pytest --cov=src tests/ -v
```

### Запуск конкретных тестов
```bash
pytest tests/test_api.py -v          # Тесты API
pytest tests/test_data_loader.py -v  # Тесты загрузки данных
pytest tests/test_analytics.py -v    # Тесты аналитики
pytest tests/test_preprocess.py -v   # Тесты предобработки
```

### Проверка качества кода
```bash
flake8 src/ tests/  # Проверка стиля
black src/ tests/   # Форматирование кода
```

## CI/CD

Проект использует GitHub Actions для автоматизации проверок, тестирования и деплоя.

### Автоматические проверки

Workflow запускается при:
- Push в ветки `main`, `master`, `develop`
- Создании Pull Request
- По расписанию (каждый день в 2:00 UTC)
- Ручном запуске через GitHub Actions UI

### Что делает CI/CD pipeline:

1. **Code Quality Check** - проверка кода с помощью `flake8` и `black`
2. **Unit Tests** - запуск всех тестов с покрытием кода
3. **Report Generation** - автоматическая генерация HTML отчетов
4. **Deploy to GitHub Pages** - публикация отчетов на GitHub Pages (при scheduled runs)

### Ручной запуск workflow

Вы можете запустить workflow вручную с параметрами:
- `generate_report` - генерировать ли отчет
- `run_tests` - запускать ли тесты
- `deploy` - деплоить ли на GitHub Pages

### Артефакты

После выполнения workflow доступны следующие артефакты:
- `coverage-report` - HTML отчет о покрытии кода тестами
- `performance-report` - HTML отчет об успеваемости студентов
- `statistics-json` - JSON файл со статистикой

Файл конфигурации: `.github/workflows/ci.yml`

## Advanced Usage

### Update data

```bash
python scripts/update_data.py
```

### Generate sample data

```bash
python scripts/generate_sample_data.py
```

### Generate HTML report

Генерация HTML отчета со статистикой успеваемости:

```bash
# Генерация отчета в стандартное место (reports/report.html)
python scripts/generate_report.py

# Генерация отчета в указанное место
python scripts/generate_report.py --output path/to/report.html
```

Скрипт автоматически:
- Загружает данные из `data/raw/`
- Генерирует статистику
- Создает красивый HTML отчет с таблицами и метриками

## Contributing
Pull-requests welcome.

---

## Troubleshooting

### Backend не запускается
- **Установите зависимости:** `pip install -r requirements.txt`
- Проверьте версию Python: `python --version` (должна быть 3.10+)
- Убедитесь, что зависимости установлены: `pip list | findstr fastapi` (Windows) или `pip list | grep fastapi` (Linux/Mac)
- Проверьте, что порт 8000 свободен
- Если ошибка `ModuleNotFoundError: No module named 'plotly'` - выполните `pip install -r requirements.txt`

### Frontend не подключается к API
- Убедитесь, что backend запущен на http://localhost:8000
- Откройте консоль браузера (F12) и проверьте ошибки
- Проверьте URL в `frontend/app.js`

### Данные не загружаются
- Убедитесь, что вы импортировали данные через интерфейс приложения
- Проверьте формат данных в импортируемом файле (колонки: student_id, student_name, subject, grade, date)
- Проверьте, что файл находится в директории `data/raw/`
- Для ознакомления с правильным форматом данных посмотрите демонстрационный файл `data/sample.csv`

## License
MIT License

### Author
Kritt07