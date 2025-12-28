"""
Модуль аналитики для анализа успеваемости студентов.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def calculate_statistics(df: pd.DataFrame) -> Dict:
    """
    Вычисляет общую статистику по данным.

    Args:
        df: DataFrame с данными об оценках

    Returns:
        Словарь со статистикой
    """
    if df.empty:
        return {
            "total_students": 0,
            "total_grades": 0,
            "total_subjects": 0,
            "average_grade": 0.0,
            "date_range": None,
        }

    # Вычисляем статистику по оценкам с обработкой NaN
    if "grade" in df.columns:
        grade_series = df["grade"].dropna()
        if len(grade_series) > 0:
            stats = {
                "total_students": (
                    df["student_id"].nunique() if "student_id" in df.columns else 0
                ),
                "total_grades": len(df),
                "total_subjects": (
                    df["subject"].nunique() if "subject" in df.columns else 0
                ),
                "average_grade": float(grade_series.mean()),
                "median_grade": float(grade_series.median()),
                "min_grade": float(grade_series.min()),
                "max_grade": float(grade_series.max()),
                "std_grade": (
                    float(grade_series.std()) if len(grade_series) > 1 else 0.0
                ),
            }
        else:
            # Если все оценки NaN
            stats = {
                "total_students": (
                    df["student_id"].nunique() if "student_id" in df.columns else 0
                ),
                "total_grades": len(df),
                "total_subjects": (
                    df["subject"].nunique() if "subject" in df.columns else 0
                ),
                "average_grade": None,
                "median_grade": None,
                "min_grade": None,
                "max_grade": None,
                "std_grade": None,
            }
    else:
        stats = {
            "total_students": (
                df["student_id"].nunique() if "student_id" in df.columns else 0
            ),
            "total_grades": len(df),
            "total_subjects": df["subject"].nunique() if "subject" in df.columns else 0,
            "average_grade": None,
            "median_grade": None,
            "min_grade": None,
            "max_grade": None,
            "std_grade": None,
        }

    if "date" in df.columns:
        # Преобразуем даты в datetime, если они еще не в этом формате
        date_series = pd.to_datetime(df["date"], errors="coerce")
        min_date = date_series.min()
        max_date = date_series.max()

        stats["date_range"] = {
            "start": min_date.isoformat() if pd.notna(min_date) else None,
            "end": max_date.isoformat() if pd.notna(max_date) else None,
        }
    else:
        stats["date_range"] = None

    return stats


def get_student_statistics(df: pd.DataFrame, student_id: int) -> Dict:
    """
    Вычисляет статистику по конкретному студенту.

    Args:
        df: DataFrame с данными об оценках
        student_id: ID студента

    Returns:
        Словарь со статистикой студента
    """
    student_df = df[df["student_id"] == student_id].copy()

    if student_df.empty:
        return {
            "student_id": student_id,
            "student_name": None,
            "total_grades": 0,
            "average_grade": 0.0,
            "subjects": [],
        }

    student_name = (
        student_df["student_name"].iloc[0]
        if "student_name" in student_df.columns
        else None
    )

    # Статистика по предметам
    subject_stats = []
    if "subject" in student_df.columns:
        for subject in student_df["subject"].unique():
            subject_df = student_df[student_df["subject"] == subject]
            subject_stats.append(
                {
                    "subject": subject,
                    "average_grade": float(subject_df["grade"].mean()),
                    "total_grades": len(subject_df),
                    "grades": subject_df["grade"].tolist(),
                }
            )

    # Вычисляем статистику по оценкам с обработкой NaN
    if "grade" in student_df.columns:
        grade_series = student_df["grade"].dropna()
        if len(grade_series) > 0:
            return {
                "student_id": student_id,
                "student_name": student_name,
                "total_grades": len(student_df),
                "average_grade": float(grade_series.mean()),
                "median_grade": float(grade_series.median()),
                "min_grade": float(grade_series.min()),
                "max_grade": float(grade_series.max()),
                "subjects": subject_stats,
            }
        else:
            # Если все оценки NaN
            return {
                "student_id": student_id,
                "student_name": student_name,
                "total_grades": len(student_df),
                "average_grade": None,
                "median_grade": None,
                "min_grade": None,
                "max_grade": None,
                "subjects": subject_stats,
            }
    else:
        return {
            "student_id": student_id,
            "student_name": student_name,
            "total_grades": len(student_df),
            "average_grade": None,
            "median_grade": None,
            "min_grade": None,
            "max_grade": None,
            "subjects": subject_stats,
        }


def get_subject_statistics(df: pd.DataFrame, subject: Optional[str] = None) -> Dict:
    """
    Вычисляет статистику по предмету(ам).

    Args:
        df: DataFrame с данными об оценках
        subject: Название предмета (если None, статистика по всем предметам)

    Returns:
        Словарь со статистикой
    """
    if subject:
        filtered_df = df[df["subject"].str.lower() == subject.lower()].copy()
    else:
        filtered_df = df.copy()

    if filtered_df.empty:
        return {
            "subject": subject,
            "total_students": 0,
            "total_grades": 0,
            "average_grade": 0.0,
        }

    # Вычисляем статистику по оценкам с обработкой NaN
    if "grade" in filtered_df.columns:
        grade_series = filtered_df["grade"].dropna()
        if len(grade_series) > 0:
            stats = {
                "subject": subject if subject else "all",
                "total_students": (
                    filtered_df["student_id"].nunique()
                    if "student_id" in filtered_df.columns
                    else 0
                ),
                "total_grades": len(filtered_df),
                "average_grade": float(grade_series.mean()),
                "median_grade": float(grade_series.median()),
                "min_grade": float(grade_series.min()),
                "max_grade": float(grade_series.max()),
                "std_grade": (
                    float(grade_series.std()) if len(grade_series) > 1 else 0.0
                ),
            }
        else:
            # Если все оценки NaN
            stats = {
                "subject": subject if subject else "all",
                "total_students": (
                    filtered_df["student_id"].nunique()
                    if "student_id" in filtered_df.columns
                    else 0
                ),
                "total_grades": len(filtered_df),
                "average_grade": None,
                "median_grade": None,
                "min_grade": None,
                "max_grade": None,
                "std_grade": None,
            }
    else:
        stats = {
            "subject": subject if subject else "all",
            "total_students": (
                filtered_df["student_id"].nunique()
                if "student_id" in filtered_df.columns
                else 0
            ),
            "total_grades": len(filtered_df),
            "average_grade": None,
            "median_grade": None,
            "min_grade": None,
            "max_grade": None,
            "std_grade": None,
        }

    return stats


def get_performance_trend(
    df: pd.DataFrame,
    student_id: Optional[int] = None,
    subject: Optional[str] = None,
    period: str = "month",
) -> pd.DataFrame:
    """
    Вычисляет динамику успеваемости по времени.

    Args:
        df: DataFrame с данными об оценках
        student_id: ID студента (если None, по всем студентам)
        subject: Предмет (если None, по всем предметам)
        period: Период агрегации ('day', 'week', 'month', 'year')

    Returns:
        DataFrame с динамикой
    """
    filtered_df = df.copy()

    if student_id is not None:
        filtered_df = filtered_df[filtered_df["student_id"] == student_id]

    if subject is not None:
        filtered_df = filtered_df[filtered_df["subject"].str.lower() == subject.lower()]

    if filtered_df.empty or "date" not in filtered_df.columns:
        return pd.DataFrame()

    # Преобразуем дату
    filtered_df["date"] = pd.to_datetime(filtered_df["date"])

    # Агрегация по периоду
    period_map = {"day": "D", "week": "W", "month": "M", "year": "Y"}

    freq = period_map.get(period, "M")
    filtered_df["period"] = filtered_df["date"].dt.to_period(freq)

    # Группировка и агрегация
    trend = (
        filtered_df.groupby("period")
        .agg({"grade": ["mean", "count", "std"]})
        .reset_index()
    )

    trend.columns = ["period", "average_grade", "grade_count", "std_grade"]
    trend["period"] = trend["period"].astype(str)

    return trend


def get_top_students(
    df: pd.DataFrame, n: int = 10, subject: Optional[str] = None
) -> List[Dict]:
    """
    Получает список лучших студентов.

    Args:
        df: DataFrame с данными об оценках
        n: Количество студентов в топе
        subject: Предмет (если None, по всем предметам)

    Returns:
        Список словарей с информацией о студентах
    """
    filtered_df = df.copy()

    if subject is not None:
        filtered_df = filtered_df[filtered_df["subject"].str.lower() == subject.lower()]

    if filtered_df.empty:
        return []

    # Вычисляем средний балл по каждому студенту
    student_stats = (
        filtered_df.groupby(["student_id", "student_name"])
        .agg({"grade": ["mean", "count"]})
        .reset_index()
    )

    student_stats.columns = [
        "student_id",
        "student_name",
        "average_grade",
        "grade_count",
    ]

    # Сортируем по среднему баллу
    student_stats = student_stats.sort_values("average_grade", ascending=False)

    # Берём топ N
    top_students = student_stats.head(n)

    return top_students.to_dict("records")


def get_subject_comparison(df: pd.DataFrame) -> List[Dict]:
    """
    Сравнивает средние оценки по предметам.

    Args:
        df: DataFrame с данными об оценках

    Returns:
        Список словарей с данными по каждому предмету
    """
    if df.empty or "subject" not in df.columns:
        return []

    comparison = (
        df.groupby("subject")
        .agg({"grade": ["mean", "count", "std", "min", "max"], "student_id": "nunique"})
        .reset_index()
    )

    comparison.columns = [
        "subject",
        "average_grade",
        "total_grades",
        "std_grade",
        "min_grade",
        "max_grade",
        "total_students",
    ]

    comparison = comparison.sort_values("average_grade", ascending=False)

    return comparison.to_dict("records")
