"""
Модуль для загрузки и обработки данных об оценках студентов.
Поддерживает чтение CSV и Excel файлов, проверку структуры,
автоматический поиск новых оценок и кеширование данных.
"""

import pandas as pd
import os
import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DataLoader:
    """Класс для загрузки и обработки данных об оценках студентов."""

    # Ожидаемые колонки в данных
    REQUIRED_COLUMNS = ["student_id", "student_name", "subject", "grade", "date"]
    OPTIONAL_COLUMNS = ["teacher", "assignment", "notes"]

    def __init__(self, data_dir: str = "data/raw", cache_dir: str = "data/processed"):
        """
        Инициализация DataLoader.

        Args:
            data_dir: Директория с исходными данными (CSV/Excel)
            cache_dir: Директория для кешированных данных
        """
        self.data_dir = Path(data_dir)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "data_cache.json"
        self.last_processed_hash = None

    def _calculate_file_hash(self, file_path: Path) -> str:
        """
        Вычисляет хеш файла для отслеживания изменений.

        Args:
            file_path: Путь к файлу

        Returns:
            SHA256 хеш файла
        """
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def _load_cache(self) -> Optional[Dict]:
        """
        Загружает кеш обработанных данных.

        Returns:
            Словарь с кешированными данными или None
        """
        if not self.cache_file.exists():
            return None

        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                cache = json.load(f)
            return cache
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Ошибка загрузки кеша: {e}")
            return None

    def _save_cache(self, data: pd.DataFrame, file_hash: str, metadata: Dict):
        """
        Сохраняет обработанные данные в кеш.

        Args:
            data: DataFrame с обработанными данными
            file_hash: Хеш исходного файла
            metadata: Метаданные о данных
        """
        try:
            cache_data = {
                "file_hash": file_hash,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata,
                "data_path": str(self.cache_dir / "cached_data.csv"),
            }

            # Сохраняем DataFrame в CSV
            data_path = self.cache_dir / "cached_data.csv"
            data.to_csv(data_path, index=False, encoding="utf-8")

            # Сохраняем метаданные
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)

            logger.info(f"Данные сохранены в кеш: {data_path}")
        except Exception as e:
            logger.error(f"Ошибка сохранения кеша: {e}")

    def _validate_structure(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Проверяет структуру данных на соответствие ожидаемым колонкам.

        Args:
            df: DataFrame для проверки

        Returns:
            Кортеж (валидность, список ошибок)
        """
        errors = []

        # Проверка наличия обязательных колонок
        missing_columns = set(self.REQUIRED_COLUMNS) - set(df.columns)
        if missing_columns:
            errors.append(f"Отсутствуют обязательные колонки: {missing_columns}")

        # Проверка на пустой DataFrame
        if df.empty:
            errors.append("DataFrame пустой")
            return False, errors

        # Проверка типов данных
        if "student_id" in df.columns:
            if not pd.api.types.is_numeric_dtype(df["student_id"]):
                errors.append("Колонка 'student_id' должна быть числовой")

        if "grade" in df.columns:
            if not pd.api.types.is_numeric_dtype(df["grade"]):
                errors.append("Колонка 'grade' должна быть числовой")

        if "date" in df.columns:
            try:
                pd.to_datetime(df["date"])
            except (ValueError, TypeError):
                errors.append("Колонка 'date' должна содержать валидные даты")

        # Проверка на дубликаты
        if df.duplicated().any():
            errors.append("Обнаружены дублирующиеся записи")

        # Проверка на пропущенные значения в обязательных колонках
        for col in self.REQUIRED_COLUMNS:
            if col in df.columns and df[col].isna().any():
                errors.append(f"Обнаружены пропущенные значения в колонке '{col}'")

        is_valid = len(errors) == 0
        return is_valid, errors

    def _normalize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Нормализует данные: приводит к единому формату.

        Args:
            df: Исходный DataFrame

        Returns:
            Нормализованный DataFrame
        """
        df = df.copy()

        # Приведение названий колонок к нижнему регистру
        df.columns = df.columns.str.lower().str.strip()

        # Нормализация дат
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")

        # Нормализация числовых колонок
        if "student_id" in df.columns:
            df["student_id"] = pd.to_numeric(df["student_id"], errors="coerce")

        if "grade" in df.columns:
            df["grade"] = pd.to_numeric(df["grade"], errors="coerce")

        # Удаление пробелов в строковых колонках
        string_columns = df.select_dtypes(include=["object"]).columns
        for col in string_columns:
            df[col] = df[col].astype(str).str.strip()

        # Удаление дубликатов
        df = df.drop_duplicates()

        # Сортировка по дате
        if "date" in df.columns:
            df = df.sort_values("date")

        return df

    def read_file(self, file_path: Optional[str] = None) -> pd.DataFrame:
        """
        Читает CSV или Excel файл.

        Args:
            file_path: Путь к файлу. Если None, ищет файлы в data_dir

        Returns:
            DataFrame с данными

        Raises:
            FileNotFoundError: Если файл не найден
            ValueError: Если формат файла не поддерживается
        """
        if file_path is None:
            # Поиск файлов в директории
            files = (
                list(self.data_dir.glob("*.csv"))
                + list(self.data_dir.glob("*.xlsx"))
                + list(self.data_dir.glob("*.xls"))
            )

            if not files:
                raise FileNotFoundError(f"Файлы данных не найдены в {self.data_dir}")

            # Используем самый новый файл
            file_path = max(files, key=os.path.getmtime)
            logger.info(f"Найден файл: {file_path}")

        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Файл не найден: {file_path}")

        # Определение формата и чтение
        file_ext = file_path.suffix.lower()

        try:
            if file_ext == ".csv":
                # Пробуем разные кодировки
                for encoding in ["utf-8", "cp1251", "latin-1"]:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding)
                        logger.info(f"Файл прочитан с кодировкой {encoding}")
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise ValueError(
                        f"Не удалось прочитать файл с доступными кодировками"
                    )

            elif file_ext in [".xlsx", ".xls"]:
                df = pd.read_excel(
                    file_path, engine="openpyxl" if file_ext == ".xlsx" else None
                )
                logger.info(f"Excel файл прочитан успешно")

            else:
                raise ValueError(f"Неподдерживаемый формат файла: {file_ext}")

            logger.info(f"Загружено строк: {len(df)}, колонок: {len(df.columns)}")
            return df

        except Exception as e:
            logger.error(f"Ошибка чтения файла {file_path}: {e}")
            raise

    def load_data(
        self, file_path: Optional[str] = None, use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Загружает данные с проверкой структуры и кешированием.

        Args:
            file_path: Путь к файлу данных
            use_cache: Использовать ли кеш

        Returns:
            DataFrame с обработанными данными
        """
        # Определяем путь к файлу
        if file_path is None:
            files = (
                list(self.data_dir.glob("*.csv"))
                + list(self.data_dir.glob("*.xlsx"))
                + list(self.data_dir.glob("*.xls"))
            )
            if not files:
                raise FileNotFoundError(f"Файлы данных не найдены в {self.data_dir}")
            file_path = max(files, key=os.path.getmtime)

        file_path = Path(file_path)
        file_hash = self._calculate_file_hash(file_path)

        # Проверка кеша
        if use_cache:
            cache = self._load_cache()
            if cache and cache.get("file_hash") == file_hash:
                cached_data_path = Path(cache["data_path"])
                if cached_data_path.exists():
                    logger.info("Загрузка данных из кеша")
                    df = pd.read_csv(cached_data_path)
                    self.last_processed_hash = file_hash
                    return df

        # Чтение и обработка данных
        logger.info(f"Загрузка данных из файла: {file_path}")
        df = self.read_file(file_path)

        # Нормализация
        df = self._normalize_data(df)

        # Проверка структуры
        is_valid, errors = self._validate_structure(df)
        if not is_valid:
            error_msg = "Ошибки валидации структуры данных:\n" + "\n".join(errors)
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Сохранение в кеш
        if use_cache:
            metadata = {
                "rows": len(df),
                "columns": list(df.columns),
                "date_range": (
                    {
                        "min": str(df["date"].min()) if "date" in df.columns else None,
                        "max": str(df["date"].max()) if "date" in df.columns else None,
                    }
                    if "date" in df.columns
                    else None
                ),
            }
            self._save_cache(df, file_hash, metadata)
            self.last_processed_hash = file_hash

        logger.info(f"Данные успешно загружены и обработаны: {len(df)} записей")
        return df

    def find_new_grades(
        self, current_data: pd.DataFrame, previous_hash: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Находит новые оценки, сравнивая текущие данные с предыдущими.

        Args:
            current_data: Текущий DataFrame с данными
            previous_hash: Хеш предыдущей версии данных (если None, используется кеш)

        Returns:
            DataFrame только с новыми оценками
        """
        if previous_hash is None:
            cache = self._load_cache()
            if cache:
                previous_hash = cache.get("file_hash")

        # Если нет предыдущих данных, все данные считаются новыми
        if previous_hash is None or previous_hash != self.last_processed_hash:
            logger.info("Предыдущие данные не найдены, все данные считаются новыми")
            return current_data

        # Загружаем предыдущие данные из кеша
        cache = self._load_cache()
        if not cache:
            return current_data

        cached_data_path = Path(cache["data_path"])
        if not cached_data_path.exists():
            return current_data

        try:
            previous_data = pd.read_csv(cached_data_path)

            # Находим новые записи
            # Используем комбинацию ключевых полей для определения уникальности
            key_columns = ["student_id", "subject", "date", "grade"]
            available_keys = [
                col
                for col in key_columns
                if col in current_data.columns and col in previous_data.columns
            ]

            if not available_keys:
                logger.warning(
                    "Недостаточно колонок для сравнения, все данные считаются новыми"
                )
                return current_data

            # Создаем индикаторные колонки для сравнения
            current_keys = current_data[available_keys].apply(
                lambda x: "|".join(x.astype(str)), axis=1
            )
            previous_keys = previous_data[available_keys].apply(
                lambda x: "|".join(x.astype(str)), axis=1
            )

            # Находим новые записи
            new_mask = ~current_keys.isin(previous_keys)
            new_grades = current_data[new_mask].copy()

            logger.info(
                f"Найдено новых оценок: {len(new_grades)} из {len(current_data)}"
            )
            return new_grades

        except Exception as e:
            logger.error(f"Ошибка при поиске новых оценок: {e}")
            return current_data

    def get_students_list(self, df: pd.DataFrame) -> List[Dict]:
        """
        Получает список уникальных студентов из данных.

        Args:
            df: DataFrame с данными

        Returns:
            Список словарей с информацией о студентах
        """
        if "student_id" not in df.columns or "student_name" not in df.columns:
            return []

        students = df[["student_id", "student_name"]].drop_duplicates()
        students_list = students.to_dict("records")

        return students_list

    def get_grades(
        self,
        df: pd.DataFrame,
        student_id: Optional[int] = None,
        subject: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Получает оценки с опциональной фильтрацией.

        Args:
            df: DataFrame с данными
            student_id: Фильтр по ID студента
            subject: Фильтр по предмету
            start_date: Начальная дата (формат: YYYY-MM-DD)
            end_date: Конечная дата (формат: YYYY-MM-DD)

        Returns:
            Отфильтрованный DataFrame
        """
        filtered_df = df.copy()

        if student_id is not None:
            if "student_id" in filtered_df.columns:
                filtered_df = filtered_df[filtered_df["student_id"] == student_id]

        if subject is not None:
            if "subject" in filtered_df.columns:
                filtered_df = filtered_df[
                    filtered_df["subject"].str.lower() == subject.lower()
                ]

        # Фильтрация по датам
        if "date" in filtered_df.columns:
            if start_date is not None:
                try:
                    start_dt = pd.to_datetime(start_date)
                    filtered_df = filtered_df[
                        pd.to_datetime(filtered_df["date"]) >= start_dt
                    ]
                except (ValueError, TypeError):
                    logger.warning(f"Некорректная начальная дата: {start_date}")

            if end_date is not None:
                try:
                    end_dt = pd.to_datetime(end_date)
                    filtered_df = filtered_df[
                        pd.to_datetime(filtered_df["date"]) <= end_dt
                    ]
                except (ValueError, TypeError):
                    logger.warning(f"Некорректная конечная дата: {end_date}")

        return filtered_df


# Глобальный экземпляр для удобства использования
_loader_instance: Optional[DataLoader] = None


def get_data_loader(
    data_dir: str = "data/raw", cache_dir: str = "data/processed"
) -> DataLoader:
    """
    Получает экземпляр DataLoader.

    Args:
        data_dir: Директория с исходными данными
        cache_dir: Директория для кеша

    Returns:
        Экземпляр DataLoader
    """
    # Создаем новый экземпляр, так как параметры могут отличаться
    return DataLoader(data_dir=data_dir, cache_dir=cache_dir)
