"""
FastAPI application for Interactive Student Performance Dashboard.
"""

from fastapi import FastAPI, Query, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, Response
from typing import Optional, List, Dict
import logging
import pandas as pd
import numpy as np
import json
from datetime import datetime, date
import shutil
from pathlib import Path
import io

from src.data_loader import get_data_loader
from src.config import DATA_DIR, PROCESSED_DIR
from src import plots
from src import analytics
from pydantic import BaseModel

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
    if isinstance(obj, float) and (
        obj != obj or obj == float("inf") or obj == float("-inf")
    ):
        if obj != obj:  # NaN
            return None
        elif obj == float("inf"):
            return None  # или можно вернуть "Infinity"
        elif obj == float("-inf"):
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
    version="1.0.0",
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
# Используем data/raw как директорию с исходными данными
data_loader = get_data_loader(
    data_dir=str(DATA_DIR / "raw"), cache_dir=str(PROCESSED_DIR)
)


# Модель для системы оценивания
class GradingSystem(BaseModel):
    system_type: str  # "5-point", "100-point", "custom"
    max_grade: Optional[float] = None  # Для кастомной системы
    min_grade: Optional[float] = None  # Для кастомной системы


# Файл для хранения настроек системы оценивания
GRADING_SYSTEM_FILE = PROCESSED_DIR / "grading_system.json"


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
            "student_statistics": "/api/students/{student_id}/statistics",
        },
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


@app.get("/api/data-status")
async def get_data_status():
    """Проверка наличия данных в системе."""
    try:
        df = data_loader.load_data(use_cache=True)
        has_data = not df.empty and len(df) > 0

        # Загружаем настройки системы оценивания
        grading_system = None
        if GRADING_SYSTEM_FILE.exists():
            try:
                with open(GRADING_SYSTEM_FILE, "r", encoding="utf-8") as f:
                    grading_system = json.load(f)
            except Exception as e:
                logger.warning(f"Ошибка загрузки настроек системы оценивания: {e}")

        return {
            "has_data": has_data,
            "total_records": len(df) if has_data else 0,
            "grading_system": grading_system,
        }
    except FileNotFoundError:
        return {"has_data": False, "total_records": 0, "grading_system": None}
    except Exception as e:
        logger.error(f"Ошибка проверки статуса данных: {e}")
        return {
            "has_data": False,
            "total_records": 0,
            "grading_system": None,
            "error": str(e),
        }


@app.post("/api/grading-system")
async def set_grading_system(grading_system: GradingSystem):
    """Установка системы оценивания."""
    try:
        # Сохраняем настройки в файл
        grading_data = grading_system.dict()
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

        with open(GRADING_SYSTEM_FILE, "w", encoding="utf-8") as f:
            json.dump(grading_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Система оценивания установлена: {grading_data}")

        return {
            "message": "Система оценивания успешно установлена",
            "grading_system": grading_data,
        }
    except Exception as e:
        logger.error(f"Ошибка сохранения системы оценивания: {e}")
        raise HTTPException(
            status_code=500, detail=f"Ошибка сохранения системы оценивания: {str(e)}"
        )


@app.get("/api/grading-system")
async def get_grading_system():
    """Получение текущей системы оценивания."""
    try:
        if GRADING_SYSTEM_FILE.exists():
            with open(GRADING_SYSTEM_FILE, "r", encoding="utf-8") as f:
                grading_system = json.load(f)
            return {"grading_system": grading_system}
        else:
            return {"grading_system": None}
    except Exception as e:
        logger.error(f"Ошибка загрузки системы оценивания: {e}")
        return {"grading_system": None}


@app.get("/api/plot-data")
async def get_plot_data(
    plot_type: Optional[str] = Query(
        None,
        description="Тип графика: distribution, trend, comparison, heatmap, box, dashboard",
    ),
    student_id: Optional[str] = Query(None, description="Фильтр по ID студента"),
    subject: Optional[str] = Query(None, description="Фильтр по предмету"),
    start_date: Optional[str] = Query(None, description="Начальная дата (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Конечная дата (YYYY-MM-DD)"),
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

        # Применяем фильтры по датам
        df = data_loader.get_grades(
            df,
            student_id=student_id_int,
            subject=subject,
            start_date=start_date,
            end_date=end_date,
        )

        if df.empty:
            return {"data": [], "layout": {}}

        if plot_type == "distribution":
            plot_dict = plots.create_grade_distribution_plot(
                df, student_id=student_id_int, subject=subject
            )
        elif plot_type == "trend":
            plot_dict = plots.create_performance_trend_plot(
                df, student_id=student_id_int, subject=subject
            )
        elif plot_type == "comparison":
            # Возвращаем оба графика сравнения: по предметам и по студентам
            plot_dict = {
                "subject_comparison": plots.create_subject_comparison_plot(
                    df, student_id=student_id_int
                ),
                "student_comparison": plots.create_student_comparison_plot(
                    df, subject=subject
                ),
            }
        elif plot_type == "heatmap":
            plot_dict = plots.create_subject_heatmap(df, student_id=student_id_int)
        elif plot_type == "box":
            plot_dict = plots.create_box_plot_by_subject(df)
        elif plot_type == "dashboard":
            plot_dict = plots.create_dashboard_plots(
                df, student_id=student_id_int, subject=subject
            )
        else:
            plot_dict = plots.create_dashboard_plots(
                df, student_id=student_id_int, subject=subject
            )

        # Преобразуем все numpy типы в стандартные Python типы для сериализации
        plot_dict = convert_to_serializable(plot_dict)

        return plot_dict
    except Exception as e:
        import traceback

        error_detail = traceback.format_exc()
        logger.error(f"Error generating plot data: {e}\n{error_detail}")
        raise HTTPException(
            status_code=500, detail=f"Ошибка генерации графика: {str(e)}"
        )


@app.get("/api/students")
async def get_students():
    """Список студентов."""
    try:
        df = data_loader.load_data(use_cache=True)
        students = data_loader.get_students_list(df)

        # Добавляем базовую статистику для каждого студента
        students_with_stats = []
        for student in students:
            student_id = student.get("student_id")
            student_stats = analytics.get_student_statistics(df, student_id)
            students_with_stats.append(
                {
                    "student_id": student.get("student_id"),
                    "student_name": student.get("student_name"),
                    "average_grade": student_stats.get("average_grade", 0.0),
                    "total_grades": student_stats.get("total_grades", 0),
                }
            )

        return {"students": students_with_stats, "total": len(students_with_stats)}
    except Exception as e:
        logger.error(f"Error loading students: {e}")
        raise HTTPException(
            status_code=500, detail=f"Ошибка загрузки студентов: {str(e)}"
        )


@app.get("/api/grades")
async def get_grades(
    student_id: Optional[int] = Query(None, description="Filter by student ID"),
    subject: Optional[str] = Query(None, description="Filter by subject"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: Optional[int] = Query(None, description="Limit number of results"),
):
    """Данные оценок."""
    try:
        df = data_loader.load_data(use_cache=True)
        filtered_df = data_loader.get_grades(
            df,
            student_id=student_id,
            subject=subject,
            start_date=start_date,
            end_date=end_date,
        )

        # Ограничение количества результатов
        if limit is not None and limit > 0:
            filtered_df = filtered_df.head(limit)

        # Конвертируем в список словарей для JSON
        grades_list = []
        for _, row in filtered_df.iterrows():
            grade_dict = row.to_dict()
            # Преобразуем дату в строку и обрабатываем NaN
            if "date" in grade_dict and pd.notna(grade_dict["date"]):
                grade_dict["date"] = str(grade_dict["date"])
            # Преобразуем все значения для JSON-совместимости
            grade_dict = convert_to_serializable(grade_dict)
            grades_list.append(grade_dict)

        result = {
            "grades": grades_list,
            "total": len(grades_list),
            "filters": {
                "student_id": student_id,
                "subject": subject,
                "start_date": start_date,
                "end_date": end_date,
            },
        }

        # Дополнительная обработка всего результата
        return convert_to_serializable(result)
    except Exception as e:
        logger.error(f"Error loading grades: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки оценок: {str(e)}")


@app.get("/api/statistics")
async def get_statistics(
    student_id: Optional[int] = Query(None, description="Фильтр по ID студента"),
    subject: Optional[str] = Query(None, description="Фильтр по предмету"),
    start_date: Optional[str] = Query(None, description="Начальная дата (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Конечная дата (YYYY-MM-DD)"),
):
    """Общая статистика."""
    try:
        df = data_loader.load_data(use_cache=True)

        # Применяем фильтры через get_grades для единообразия
        df = data_loader.get_grades(
            df,
            student_id=student_id,
            subject=subject,
            start_date=start_date,
            end_date=end_date,
        )

        stats = analytics.calculate_statistics(df)

        # Добавляем дополнительную информацию
        if subject is None and "subject" in df.columns:
            stats["subject_comparison"] = analytics.get_subject_comparison(df)

        return stats
    except Exception as e:
        logger.error(f"Error calculating statistics: {e}")
        raise HTTPException(
            status_code=500, detail=f"Ошибка вычисления статистики: {str(e)}"
        )


@app.get("/api/students/{student_id}/statistics")
async def get_student_statistics(student_id: int):
    """Статистика по конкретному студенту."""
    try:
        df = data_loader.load_data(use_cache=True)
        stats = analytics.get_student_statistics(df, student_id)

        if stats.get("total_grades") == 0:
            raise HTTPException(
                status_code=404, detail=f"Студент с ID {student_id} не найден"
            )

        # Добавляем динамику успеваемости
        trend = analytics.get_performance_trend(df, student_id=student_id)
        if not trend.empty:
            trend_list = trend.to_dict("records")
            stats["trend"] = convert_to_serializable(trend_list)
        else:
            stats["trend"] = []

        # Преобразуем статистику для JSON-совместимости (включая NaN)
        stats = convert_to_serializable(stats)

        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating student statistics: {e}")
        raise HTTPException(
            status_code=500, detail=f"Ошибка вычисления статистики студента: {str(e)}"
        )


@app.get("/api/subjects")
async def get_subjects():
    """Список предметов с статистикой."""
    try:
        df = data_loader.load_data(use_cache=True)

        if df.empty or "subject" not in df.columns:
            return {"subjects": []}

        subjects = df["subject"].unique().tolist()
        subjects_with_stats = []

        for subject in subjects:
            stats = analytics.get_subject_statistics(df, subject)
            subjects_with_stats.append(stats)

        return {"subjects": subjects_with_stats, "total": len(subjects_with_stats)}
    except Exception as e:
        logger.error(f"Error loading subjects: {e}")
        raise HTTPException(
            status_code=500, detail=f"Ошибка загрузки предметов: {str(e)}"
        )


@app.post("/api/import")
async def import_data(file: UploadFile = File(...)):
    """Импорт данных из CSV или Excel файла."""
    try:
        # Проверка наличия имени файла
        if not file.filename:
            raise HTTPException(status_code=400, detail="Имя файла не указано")

        # Проверка расширения файла
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in [".csv", ".xlsx", ".xls"]:
            raise HTTPException(
                status_code=400,
                detail="Неподдерживаемый формат файла. Поддерживаются только CSV, XLSX и XLS",
            )

        # Создаем директорию для загрузки, если её нет
        upload_dir = DATA_DIR / "raw"
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Генерируем уникальное имя файла (добавляем timestamp, если файл уже существует)
        base_name = Path(file.filename).stem
        file_path = upload_dir / file.filename
        if file_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = upload_dir / f"{base_name}_{timestamp}{file_ext}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"Файл загружен: {file_path}")

        # Пробуем загрузить и проверить данные
        try:
            # Пробуем прочитать файл
            df = data_loader.read_file(str(file_path))

            # Проверяем структуру
            is_valid, errors = data_loader._validate_structure(df)
            if not is_valid:
                # Удаляем файл при ошибке валидации
                if file_path.exists():
                    file_path.unlink()
                raise HTTPException(
                    status_code=400,
                    detail=f"Ошибка валидации данных: {', '.join(errors)}",
                )

            # Очищаем кеш, чтобы при следующей загрузке использовались новые данные
            cache_file = PROCESSED_DIR / "data_cache.json"
            cached_data_file = PROCESSED_DIR / "cached_data.csv"

            if cache_file.exists():
                cache_file.unlink()
                logger.info("Кеш data_cache.json удален")
            if cached_data_file.exists():
                cached_data_file.unlink()
                logger.info("Кеш cached_data.csv удален")

            # Сбрасываем состояние глобального data_loader
            data_loader.last_processed_hash = None

            # Принудительно перезагружаем данные, чтобы убедиться, что используется новый файл
            try:
                data_loader.load_data(use_cache=False)
                logger.info("Данные успешно перезагружены после импорта")
            except Exception as reload_error:
                logger.warning(
                    f"Предупреждение при перезагрузке данных: {reload_error}"
                )

            return {
                "message": "Файл успешно загружен и проверен",
                "filename": file.filename,
                "rows": len(df),
                "columns": list(df.columns),
            }
        except HTTPException:
            # Перебрасываем HTTPException без изменений
            raise
        except Exception as e:
            # Удаляем файл при ошибке обработки
            if file_path.exists():
                file_path.unlink()
            logger.error(f"Ошибка обработки файла: {e}")
            raise HTTPException(
                status_code=400, detail=f"Ошибка обработки файла: {str(e)}"
            )

    except HTTPException:
        # Перебрасываем HTTPException без изменений
        raise
    except Exception as e:
        logger.error(f"Ошибка импорта файла: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка импорта файла: {str(e)}")


@app.get("/api/export/csv")
async def export_csv(
    student_id: Optional[int] = Query(None, description="Filter by student ID"),
    subject: Optional[str] = Query(None, description="Filter by subject"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
):
    """Экспорт данных в CSV."""
    try:
        df = data_loader.load_data(use_cache=True)
        filtered_df = data_loader.get_grades(
            df,
            student_id=student_id,
            subject=subject,
            start_date=start_date,
            end_date=end_date,
        )

        # Создаем CSV в памяти
        output = io.StringIO()
        filtered_df.to_csv(output, index=False, encoding="utf-8")
        output.seek(0)

        # Генерируем имя файла
        filename = f"grades_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        logger.error(f"Ошибка экспорта CSV: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка экспорта CSV: {str(e)}")


@app.get("/api/export/pdf")
async def export_pdf(
    student_id: Optional[int] = Query(None, description="Filter by student ID"),
    subject: Optional[str] = Query(None, description="Filter by subject"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
):
    """Экспорт отчета в PDF."""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            Table,
            TableStyle,
            PageBreak,
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        import plotly.graph_objects as go
        import plotly.io as pio
        import os

        # Регистрируем шрифт с поддержкой кириллицы
        font_registered = False
        font_name = "Helvetica"  # По умолчанию

        try:

            # Пути к шрифтам с поддержкой кириллицы
            font_paths = [
                "C:/Windows/Fonts/arial.ttf",  # Windows - Arial
                "C:/Windows/Fonts/calibri.ttf",  # Windows - Calibri
                "C:/Windows/Fonts/times.ttf",  # Windows - Times New Roman
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",  # Linux
                "/System/Library/Fonts/Supplemental/Arial.ttf",  # macOS
            ]

            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont("CyrillicFont", font_path))
                        # Пробуем зарегистрировать жирный вариант
                        try:
                            # Ищем жирный вариант шрифта
                            bold_path = font_path.replace(".ttf", "bd.ttf").replace(
                                "Regular", "Bold"
                            )
                            if os.path.exists(bold_path):
                                pdfmetrics.registerFont(
                                    TTFont("CyrillicFont-Bold", bold_path)
                                )
                        except:
                            pass  # Если жирный вариант не найден, используем обычный
                        font_registered = True
                        font_name = "CyrillicFont"
                        logger.info(
                            f"Зарегистрирован шрифт с поддержкой кириллицы: {font_path}"
                        )
                        break
                    except Exception as e:
                        logger.warning(
                            f"Не удалось зарегистрировать шрифт {font_path}: {e}"
                        )
                        continue

            if not font_registered:
                logger.warning(
                    "Не найден системный шрифт с поддержкой кириллицы. Кириллица может отображаться некорректно."
                )
        except ImportError:
            logger.warning("Не удалось импортировать модули для работы со шрифтами")
        except Exception as e:
            logger.warning(f"Ошибка при регистрации шрифта: {e}")

        df = data_loader.load_data(use_cache=True)
        filtered_df = data_loader.get_grades(
            df,
            student_id=student_id,
            subject=subject,
            start_date=start_date,
            end_date=end_date,
        )

        if filtered_df.empty:
            raise HTTPException(status_code=404, detail="Нет данных для экспорта")

        # Создаем PDF в памяти
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()

        # Создаем стили с правильным шрифтом для кириллицы
        normal_style = ParagraphStyle(
            "CustomNormal", parent=styles["Normal"], fontName=font_name, fontSize=11
        )

        heading2_style = ParagraphStyle(
            "CustomHeading2", parent=styles["Heading2"], fontName=font_name, fontSize=16
        )

        # Заголовок
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontName=font_name,
            fontSize=24,
            textColor=colors.HexColor("#6366f1"),
            spaceAfter=30,
            alignment=1,  # Center
        )
        story.append(Paragraph("Отчет об успеваемости студентов", title_style))
        story.append(Spacer(1, 0.2 * inch))

        # Информация о фильтрах
        filter_text = "Фильтры: "
        filters = []
        if student_id:
            student_name = (
                filtered_df[filtered_df["student_id"] == student_id][
                    "student_name"
                ].iloc[0]
                if not filtered_df[filtered_df["student_id"] == student_id].empty
                else f"ID {student_id}"
            )
            filters.append(f"Студент: {student_name}")
        if subject:
            filters.append(f"Предмет: {subject}")
        if start_date:
            filters.append(f"С: {start_date}")
        if end_date:
            filters.append(f"По: {end_date}")
        if not filters:
            filter_text += "Все данные"
        else:
            filter_text += ", ".join(filters)

        story.append(Paragraph(filter_text, normal_style))
        story.append(Spacer(1, 0.3 * inch))

        # Статистика
        stats = analytics.calculate_statistics(filtered_df)
        stats_data = [
            ["Метрика", "Значение"],
            ["Всего оценок", str(stats.get("total_grades", 0))],
            [
                "Средний балл",
                (
                    f"{stats.get('average_grade', 0):.2f}"
                    if stats.get("average_grade")
                    else "N/A"
                ),
            ],
            [
                "Медиана",
                (
                    f"{stats.get('median_grade', 0):.2f}"
                    if stats.get("median_grade")
                    else "N/A"
                ),
            ],
            ["Минимальная оценка", str(stats.get("min_grade", "N/A"))],
            ["Максимальная оценка", str(stats.get("max_grade", "N/A"))],
            ["Количество студентов", str(stats.get("total_students", 0))],
            ["Количество предметов", str(stats.get("total_subjects", 0))],
        ]

        stats_table = Table(stats_data, colWidths=[3 * inch, 2 * inch])
        # Используем правильный шрифт для заголовка таблицы
        # Для TTF шрифтов используем обычный шрифт, если жирный не зарегистрирован
        if font_registered:
            try:
                # Проверяем, зарегистрирован ли жирный вариант
                pdfmetrics.getFont("CyrillicFont-Bold")
                header_font = "CyrillicFont-Bold"
            except:
                header_font = (
                    "CyrillicFont"  # Используем обычный, если жирный недоступен
                )
        else:
            header_font = "Helvetica-Bold"
        stats_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), header_font),
                    ("FONTNAME", (0, 1), (-1, -1), font_name),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("FONTSIZE", (0, 1), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.lightgrey],
                    ),
                ]
            )
        )

        story.append(Paragraph("Общая статистика", heading2_style))
        story.append(Spacer(1, 0.1 * inch))
        story.append(stats_table)
        story.append(PageBreak())

        # Таблица с данными (первые 50 строк)
        if len(filtered_df) > 0:
            story.append(Paragraph("Данные об оценках", heading2_style))
            story.append(Spacer(1, 0.1 * inch))

            # Сортируем данные по ID студента по возрастанию
            if "student_id" in filtered_df.columns:
                filtered_df = filtered_df.sort_values("student_id", ascending=True)

            # Подготавливаем данные для таблицы
            display_df = filtered_df.head(50)  # Ограничиваем для PDF
            table_data = [["ID", "Студент", "Предмет", "Оценка", "Дата"]]

            for _, row in display_df.iterrows():
                table_data.append(
                    [
                        str(row.get("student_id", "")),
                        str(row.get("student_name", "")),
                        str(row.get("subject", "")),
                        str(row.get("grade", "")),
                        (
                            str(row.get("date", ""))[:10]
                            if pd.notna(row.get("date"))
                            else ""
                        ),
                    ]
                )

            data_table = Table(
                table_data,
                colWidths=[0.5 * inch, 2 * inch, 1.5 * inch, 0.8 * inch, 1.2 * inch],
            )
            data_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (-1, 0), header_font),
                        ("FONTNAME", (0, 1), (-1, -1), font_name),
                        ("FONTSIZE", (0, 0), (-1, 0), 10),
                        ("FONTSIZE", (0, 1), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -1),
                            [colors.white, colors.lightgrey],
                        ),
                    ]
                )
            )

            story.append(data_table)

            if len(filtered_df) > 50:
                story.append(Spacer(1, 0.1 * inch))
                story.append(
                    Paragraph(
                        f"<i>Показано 50 из {len(filtered_df)} записей</i>",
                        styles["Normal"],
                    )
                )

        # Собираем PDF
        doc.build(story)
        buffer.seek(0)

        # Генерируем имя файла
        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        return Response(
            content=buffer.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except ImportError:
        logger.error("ReportLab не установлен. Установите: pip install reportlab")
        raise HTTPException(
            status_code=500,
            detail="PDF экспорт недоступен. Установите reportlab: pip install reportlab",
        )
    except Exception as e:
        logger.error(f"Ошибка экспорта PDF: {e}")
        import traceback

        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Ошибка экспорта PDF: {str(e)}")
