"""
Конфигурация приложения.
"""
from pathlib import Path

# Пути к данным
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
CACHE_DIR = BASE_DIR / "data" / "processed"

# Настройки DataLoader
REQUIRED_COLUMNS = ['student_id', 'student_name', 'subject', 'grade', 'date']
OPTIONAL_COLUMNS = ['teacher', 'assignment', 'notes']

# Настройки API
API_TITLE = "Interactive Student Performance Dashboard"
API_VERSION = "1.0.0"

