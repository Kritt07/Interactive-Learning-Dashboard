# Interactive Student Performance Dashboard

## Description
Web-приложение для визуализации успеваемости студентов на основе интерактивных графиков. Приложение автоматически обрабатывает данные, агрегирует результаты и отображает динамику успеваемости.

## Installation

### Prerequisites
- Python 3.10+
- pip
- Git

### Setup
```bash
git clone <repo-url>
cd <project-name>

python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

## Usage

### Start backed

```bash
uvicorn src.app:app --reload
```

### Open in browser
```arduino
http://localhost:8000
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

- FastAPI
- Uvicom
- Pandas
- NumPy
- Plotly
- Pytest
- Flake8
- Black
- scikit-learn


## Testing

```bash
pytest -v
pytest --cov=src test/
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

### Lisense
MIT License

### Author
Kritt07