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
Данные уже находятся в `data/raw/students_raw.csv`. Если нужно сгенерировать новые тестовые данные:
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

### Example API call
```python
import requests
print(requests.get("http://localhost:8000/api/plot-data").json())
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
│   ├── raw/
│   ├── processed/
│   └── sample.csv
│
├── scripts/
│   ├── generate_sample_data.py
│   └── update_data.py
│
├── docs/
│   └── architecture.md
│
├── .github/workflows/
│   └── tests.yml
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
GitHub Actions тестирует проект, проверяет стиль, запускает тесты и может обновлять данные по расписанию.

Файл:
```bash
.github/workflows/tests.yml
```

## Advanced Usage

### Update data

```bash
python scripts/update_data.py
```

### Generate sample data

```bash
python scripts/generate_sample_data.py
```

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
- Проверьте наличие файла `data/raw/students_raw.csv`
- Проверьте формат данных (колонки: student_id, student_name, subject, grade, date)

## License
MIT License

### Author
Kritt07