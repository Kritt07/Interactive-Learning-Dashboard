"""
Модуль для предобработки и очистки данных об оценках студентов.
Выполняет нормализацию, фильтрацию ошибок, преобразование типов и объединение данных.
"""
import pandas as pd
import numpy as np
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """
    Выполняет полную предобработку данных: нормализация, фильтрация ошибок,
    преобразование дат, сортировка и объединение данных по студентам.
    
    Args:
        df: Исходный DataFrame с данными об оценках
        
    Returns:
        Обработанный DataFrame
    """
    if df.empty:
        logger.warning("Получен пустой DataFrame")
        return df
    
    # Создаем копию для избежания изменений исходных данных
    df = df.copy()
    
    # 1. Нормализация названий столбцов
    df = _normalize_column_names(df)
    
    # 2. Фильтрация ошибок
    df = _filter_errors(df)
    
    # 3. Преобразование дат (str → datetime)
    df = _convert_dates(df)
    
    # 4. Объединение данных по студентам (нормализация имен студентов)
    df = _merge_student_data(df)
    
    # 5. Сортировка данных
    df = _sort_data(df)
    
    logger.info(f"Предобработка завершена: {len(df)} записей")
    return df


def _normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Нормализует названия столбцов: приводит к нижнему регистру,
    удаляет пробелы, заменяет специальные символы.
    
    Args:
        df: Исходный DataFrame
        
    Returns:
        DataFrame с нормализованными названиями столбцов
    """
    # Приводим к нижнему регистру и удаляем пробелы
    df.columns = df.columns.str.lower().str.strip()
    
    # Заменяем пробелы и специальные символы на подчеркивания
    df.columns = df.columns.str.replace(r'[\s\-\.]+', '_', regex=True)
    df.columns = df.columns.str.replace(r'[^\w]', '_', regex=True)
    
    # Удаляем множественные подчеркивания
    df.columns = df.columns.str.replace(r'_+', '_', regex=True)
    df.columns = df.columns.str.strip('_')
    
    # Маппинг возможных вариантов названий к стандартным
    column_mapping = {
        'studentid': 'student_id',
        'student_id': 'student_id',
        'id': 'student_id',
        'studentname': 'student_name',
        'student_name': 'student_name',
        'name': 'student_name',
        'full_name': 'student_name',
        'subject': 'subject',
        'course': 'subject',
        'discipline': 'subject',
        'grade': 'grade',
        'score': 'grade',
        'mark': 'grade',
        'rating': 'grade',
        'date': 'date',
        'date_': 'date',
        'date_of_grade': 'date',
        'grade_date': 'date',
        'teacher': 'teacher',
        'instructor': 'teacher',
        'assignment': 'assignment',
        'task': 'assignment',
        'notes': 'notes',
        'note': 'notes',
        'comment': 'notes'
    }
    
    # Применяем маппинг
    df.columns = [column_mapping.get(col, col) for col in df.columns]
    
    logger.debug(f"Нормализованы названия столбцов: {list(df.columns)}")
    return df


def _filter_errors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Фильтрует ошибки в данных: удаляет некорректные записи,
    обрабатывает пропущенные значения, валидирует типы данных.
    
    Args:
        df: DataFrame для фильтрации
        
    Returns:
        Отфильтрованный DataFrame
    """
    initial_count = len(df)
    
    # Удаляем полностью пустые строки
    df = df.dropna(how='all')
    
    # Удаляем дубликаты
    df = df.drop_duplicates()
    
    # Валидация и очистка student_id
    if 'student_id' in df.columns:
        # Преобразуем в числовой тип, невалидные значения -> NaN
        df['student_id'] = pd.to_numeric(df['student_id'], errors='coerce')
        # Удаляем строки с отсутствующим или некорректным student_id
        df = df.dropna(subset=['student_id'])
        # Преобразуем в целое число
        df['student_id'] = df['student_id'].astype(int)
        # Удаляем отрицательные или нулевые ID
        df = df[df['student_id'] > 0]
    
    # Валидация и очистка student_name
    if 'student_name' in df.columns:
        # Преобразуем в строку и удаляем пробелы
        df['student_name'] = df['student_name'].astype(str).str.strip()
        # Удаляем строки с пустыми именами или служебными значениями
        invalid_names = ['', 'nan', 'none', 'null', 'n/a', 'na']
        df = df[~df['student_name'].str.lower().isin(invalid_names)]
        df = df[df['student_name'].str.len() > 0]
    
    # Валидация и очистка subject
    if 'subject' in df.columns:
        df['subject'] = df['subject'].astype(str).str.strip()
        df = df[df['subject'].str.len() > 0]
        df = df[~df['subject'].str.lower().isin(['nan', 'none', 'null', 'n/a', 'na'])]
    
    # Валидация и очистка grade
    if 'grade' in df.columns:
        # Преобразуем в числовой тип
        df['grade'] = pd.to_numeric(df['grade'], errors='coerce')
        # Удаляем строки с отсутствующими оценками
        df = df.dropna(subset=['grade'])
        # Фильтруем оценки по разумному диапазону (например, 0-100 или 1-5)
        # Проверяем диапазон и оставляем только валидные
        # Если оценки в диапазоне 0-100, оставляем их
        # Если в диапазоне 1-5, тоже оставляем
        # Удаляем только явно некорректные (отрицательные или слишком большие)
        df = df[(df['grade'] >= 0) & (df['grade'] <= 100)]
    
    # Валидация и очистка опциональных полей
    if 'teacher' in df.columns:
        df['teacher'] = df['teacher'].astype(str).str.strip()
        df['teacher'] = df['teacher'].replace(['nan', 'None', 'null', 'n/a', 'na', ''], np.nan)
    
    if 'assignment' in df.columns:
        df['assignment'] = df['assignment'].astype(str).str.strip()
        df['assignment'] = df['assignment'].replace(['nan', 'None', 'null', 'n/a', 'na', ''], np.nan)
    
    if 'notes' in df.columns:
        df['notes'] = df['notes'].astype(str).str.strip()
        df['notes'] = df['notes'].replace(['nan', 'None', 'null', 'n/a', 'na'], '')
    
    # Удаляем строки, где отсутствуют все обязательные поля
    required_cols = ['student_id', 'student_name', 'subject', 'grade']
    available_required = [col for col in required_cols if col in df.columns]
    if available_required:
        df = df.dropna(subset=available_required, how='all')
    
    filtered_count = len(df)
    removed_count = initial_count - filtered_count
    
    if removed_count > 0:
        logger.info(f"Отфильтровано {removed_count} некорректных записей (было {initial_count}, стало {filtered_count})")
    
    return df


def _convert_dates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Преобразует столбец с датами из строкового формата в datetime.
    
    Args:
        df: DataFrame для преобразования
        
    Returns:
        DataFrame с преобразованными датами
    """
    if 'date' not in df.columns:
        logger.warning("Столбец 'date' не найден, пропуск преобразования дат")
        return df
    
    # Пробуем различные форматы дат
    date_formats = [
        '%Y-%m-%d',
        '%d.%m.%Y',
        '%d/%m/%Y',
        '%Y/%m/%d',
        '%d-%m-%Y',
        '%Y.%m.%d',
        '%d %m %Y',
        '%Y %m %d',
        '%d.%m.%y',
        '%d/%m/%y',
        '%d-%m-%y'
    ]
    
    # Преобразуем даты, пробуя автоматическое определение формата
    df['date'] = pd.to_datetime(df['date'], errors='coerce', infer_datetime_format=True)
    
    # Удаляем строки с невалидными датами
    invalid_dates_count = df['date'].isna().sum()
    if invalid_dates_count > 0:
        logger.warning(f"Найдено {invalid_dates_count} записей с невалидными датами, они будут удалены")
        df = df.dropna(subset=['date'])
    
    # Проверяем разумность дат (не слишком старые и не в будущем)
    current_year = pd.Timestamp.now().year
    # Удаляем даты раньше 1900 года или позже текущего года + 1
    df = df[(df['date'].dt.year >= 1900) & (df['date'].dt.year <= current_year + 1)]
    
    logger.debug(f"Преобразовано дат: {len(df)} записей")
    return df


def _merge_student_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Объединяет данные по студентам: нормализует имена студентов
    для одинаковых student_id, удаляет дубликаты.
    
    Args:
        df: DataFrame для обработки
        
    Returns:
        DataFrame с объединенными данными по студентам
    """
    if 'student_id' not in df.columns:
        logger.warning("Столбец 'student_id' не найден, пропуск объединения по студентам")
        return df
    
    # Нормализация имен студентов для одинаковых ID
    if 'student_name' in df.columns:
        # Группируем по student_id и берем наиболее частое имя
        # (или первое непустое, если все уникальны)
        student_name_mapping = df.groupby('student_id')['student_name'].apply(
            lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else x.iloc[0]
        ).to_dict()
        
        # Применяем нормализованные имена
        df['student_name'] = df['student_id'].map(student_name_mapping)
        
        # Дополнительная нормализация имен (приведение к единому формату)
        df['student_name'] = df['student_name'].str.title()  # Первая буква заглавная
    
    # Удаляем дубликаты по комбинации ключевых полей
    # (студент, предмет, дата, оценка)
    key_columns = ['student_id', 'subject', 'date', 'grade']
    available_keys = [col for col in key_columns if col in df.columns]
    
    if len(available_keys) >= 2:  # Минимум 2 ключевых поля для проверки дубликатов
        # Удаляем полные дубликаты
        initial_count = len(df)
        df = df.drop_duplicates(subset=available_keys)
        duplicates_removed = initial_count - len(df)
        if duplicates_removed > 0:
            logger.info(f"Удалено {duplicates_removed} дубликатов при объединении данных по студентам")
    
    logger.debug(f"Объединение данных по студентам завершено: {len(df)} записей")
    return df


def _sort_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Сортирует данные по дате, затем по student_id, затем по subject.
    
    Args:
        df: DataFrame для сортировки
        
    Returns:
        Отсортированный DataFrame
    """
    sort_columns = []
    
    # Приоритет сортировки: date -> student_id -> subject
    if 'date' in df.columns:
        sort_columns.append('date')
    if 'student_id' in df.columns:
        sort_columns.append('student_id')
    if 'subject' in df.columns:
        sort_columns.append('subject')
    
    if sort_columns:
        df = df.sort_values(by=sort_columns, ascending=[True] * len(sort_columns))
        # Сбрасываем индекс
        df = df.reset_index(drop=True)
        logger.debug(f"Данные отсортированы по: {sort_columns}")
    
    return df

