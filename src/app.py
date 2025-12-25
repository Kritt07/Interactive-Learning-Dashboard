"""
FastAPI application for Interactive Student Performance Dashboard.
"""
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict
import logging
import pandas as pd
import numpy as np
import json
from datetime import datetime, date

from src.data_loader import get_data_loader
from src.config import DATA_DIR, PROCESSED_DIR
from src import plots
from src import analytics

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def convert_to_serializable(obj):
    """Преобразует объекты в сериализуемый формат для JSON."""
    # Проверка на NaN должна быть первой
    try:
        if pd.isna(obj):
            return None
    except (ValueError, TypeError):
        pass
    
    # Проверка на float NaN
    if isinstance(obj, float) and (obj != obj or obj == float('inf') or obj == float('-inf')):
        if obj != obj:  # NaN
            return None
        elif obj == float('inf'):
            return None  # или можно вернуть "Infinity"
        elif obj == float('-inf'):
            return None  # или можно вернуть "-Infinity"
    
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
        val = float(obj)
        # Проверяем на NaN после преобразования
        if val != val:  # NaN
            return None
        return val
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: convert_to_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(item) for item in obj]
    elif isinstance(obj, (str, int, float, bool)) or obj is None:
        # Дополнительная проверка для float
        if isinstance(obj, float) and obj != obj:  # NaN
            return None
        return obj
    else:
        # Последняя попытка - преобразовать в строку
        return str(obj)

app = FastAPI(
    title="Interactive Student Performance Dashboard",
    description="Web-приложение для визуализации успеваемости студентов",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация DataLoader
data_loader = get_data_loader(
    data_dir=str(DATA_DIR),
    cache_dir=str(PROCESSED_DIR)
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Interactive Student Performance Dashboard API",
        "version": "1.0.0",
        "endpoints": {
            "plot_data": "/api/plot-data",
            "students": "/api/students",
            "grades": "/api/grades",
            "statistics": "/api/statistics",
            "student_statistics": "/api/students/{student_id}/statistics"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Пробуем загрузить данные для проверки работоспособности
        data_loader.load_data(use_cache=True)
        return {"status": "healthy"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


@app.get("/api/plot-data")
async def get_plot_data(
    plot_type: Optional[str] = Query(None, description="Тип графика: distribution, trend, comparison, heatmap, box, dashboard"),
    student_id: Optional[str] = Query(None, description="Фильтр по ID студента"),
    subject: Optional[str] = Query(None, description="Фильтр по предмету")
):
    """Выдаёт данные для графиков."""
    try:
        df = data_loader.load_data(use_cache=True)
        
        if df.empty:
            return {"data": [], "layout": {}}
        
        plot_type = plot_type or "dashboard"
        
        # Конвертируем student_id в int, если он передан
        student_id_int = None
        if student_id is not None:
            try:
                student_id_int = int(student_id)
            except (ValueError, TypeError):
                logger.warning(f"Некорректный student_id: {student_id}")
                student_id_int = None
        
        if plot_type == "distribution":
            plot_dict = plots.create_grade_distribution_plot(df, student_id=student_id_int, subject=subject)
        elif plot_type == "trend":
            plot_dict = plots.create_performance_trend_plot(df, student_id=student_id_int, subject=subject)
        elif plot_type == "comparison":
            if student_id_int is not None:
                plot_dict = plots.create_student_comparison_plot(df, subject=subject)
            else:
                plot_dict = plots.create_subject_comparison_plot(df)
        elif plot_type == "heatmap":
            plot_dict = plots.create_subject_heatmap(df, student_id=student_id_int)
        elif plot_type == "box":
            plot_dict = plots.create_box_plot_by_subject(df)
        elif plot_type == "dashboard":
            plot_dict = plots.create_dashboard_plots(df, student_id=student_id_int, subject=subject)
        else:
            plot_dict = plots.create_dashboard_plots(df, student_id=student_id_int, subject=subject)
        
        # Преобразуем все numpy типы в стандартные Python типы для сериализации
        plot_dict = convert_to_serializable(plot_dict)
        
        return plot_dict
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"Error generating plot data: {e}\n{error_detail}")
        raise HTTPException(status_code=500, detail=f"Ошибка генерации графика: {str(e)}")


@app.get("/api/students")
async def get_students():
    """Список студентов."""
    try:
        df = data_loader.load_data(use_cache=True)
        students = data_loader.get_students_list(df)
        
        # Добавляем базовую статистику для каждого студента
        students_with_stats = []
        for student in students:
            student_id = student.get('student_id')
            student_stats = analytics.get_student_statistics(df, student_id)
            students_with_stats.append({
                "student_id": student.get('student_id'),
                "student_name": student.get('student_name'),
                "average_grade": student_stats.get('average_grade', 0.0),
                "total_grades": student_stats.get('total_grades', 0)
            })
        
        return {
            "students": students_with_stats,
            "total": len(students_with_stats)
        }
    except Exception as e:
        logger.error(f"Error loading students: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки студентов: {str(e)}")


@app.get("/api/grades")
async def get_grades(
    student_id: Optional[int] = Query(None, description="Filter by student ID"),
    subject: Optional[str] = Query(None, description="Filter by subject"),
    limit: Optional[int] = Query(None, description="Limit number of results")
):
    """Данные оценок."""
    try:
        df = data_loader.load_data(use_cache=True)
        filtered_df = data_loader.get_grades(df, student_id=student_id, subject=subject)
        
        # Ограничение количества результатов
        if limit is not None and limit > 0:
            filtered_df = filtered_df.head(limit)
        
        # Конвертируем в список словарей для JSON
        grades_list = []
        for _, row in filtered_df.iterrows():
            grade_dict = row.to_dict()
            # Преобразуем дату в строку и обрабатываем NaN
            if 'date' in grade_dict and pd.notna(grade_dict['date']):
                grade_dict['date'] = str(grade_dict['date'])
            # Преобразуем все значения для JSON-совместимости
            grade_dict = convert_to_serializable(grade_dict)
            grades_list.append(grade_dict)
        
        result = {
            "grades": grades_list,
            "total": len(grades_list),
            "filters": {
                "student_id": student_id,
                "subject": subject
            }
        }
        
        # Дополнительная обработка всего результата
        return convert_to_serializable(result)
    except Exception as e:
        logger.error(f"Error loading grades: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки оценок: {str(e)}")


@app.get("/api/statistics")
async def get_statistics(
    student_id: Optional[int] = Query(None, description="Фильтр по ID студента"),
    subject: Optional[str] = Query(None, description="Фильтр по предмету")
):
    """Общая статистика."""
    try:
        df = data_loader.load_data(use_cache=True)
        
        # Применяем фильтры
        if student_id is not None:
            df = df[df['student_id'] == student_id]
        if subject is not None:
            df = df[df['subject'].str.lower() == subject.lower()]
        
        stats = analytics.calculate_statistics(df)
        
        # Добавляем дополнительную информацию
        if subject is None and 'subject' in df.columns:
            stats['subject_comparison'] = analytics.get_subject_comparison(df)
        
        return stats
    except Exception as e:
        logger.error(f"Error calculating statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка вычисления статистики: {str(e)}")


@app.get("/api/students/{student_id}/statistics")
async def get_student_statistics(student_id: int):
    """Статистика по конкретному студенту."""
    try:
        df = data_loader.load_data(use_cache=True)
        stats = analytics.get_student_statistics(df, student_id)
        
        if stats.get('total_grades') == 0:
            raise HTTPException(status_code=404, detail=f"Студент с ID {student_id} не найден")
        
        # Добавляем динамику успеваемости
        trend = analytics.get_performance_trend(df, student_id=student_id)
        if not trend.empty:
            trend_list = trend.to_dict('records')
            stats['trend'] = convert_to_serializable(trend_list)
        else:
            stats['trend'] = []
        
        # Преобразуем статистику для JSON-совместимости (включая NaN)
        stats = convert_to_serializable(stats)
        
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating student statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка вычисления статистики студента: {str(e)}")


@app.get("/api/subjects")
async def get_subjects():
    """Список предметов с статистикой."""
    try:
        df = data_loader.load_data(use_cache=True)
        
        if df.empty or 'subject' not in df.columns:
            return {"subjects": []}
        
        subjects = df['subject'].unique().tolist()
        subjects_with_stats = []
        
        for subject in subjects:
            stats = analytics.get_subject_statistics(df, subject)
            subjects_with_stats.append(stats)
        
        return {
            "subjects": subjects_with_stats,
            "total": len(subjects_with_stats)
        }
    except Exception as e:
        logger.error(f"Error loading subjects: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки предметов: {str(e)}")
