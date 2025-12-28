"""
Модуль для создания интерактивных графиков с использованием Plotly.
Полностью переработанная версия с современным дизайном и новыми типами визуализаций.
"""
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Dict, List, Optional
import logging
import numpy as np
from scipy import stats
from collections import Counter
import json
from pathlib import Path
from src.config import PROCESSED_DIR

logger = logging.getLogger(__name__)

# Современная цветовая палитра
COLORS = {
    'primary': '#6366f1',      # Индиго
    'secondary': '#8b5cf6',    # Фиолетовый
    'success': '#10b981',      # Зеленый
    'warning': '#f59e0b',      # Оранжевый
    'danger': '#ef4444',       # Красный
    'info': '#3b82f6',         # Синий
    'light': '#e5e7eb',         # Светло-серый
    'dark': '#1f2937',         # Темно-серый
}

# Градиентные цвета для тепловых карт (от зеленого для отличных оценок к желтому и красному для плохих)
HEATMAP_COLORS = [
    [0, '#dc2626'],      # Красный (плохие оценки)
    [0.33, '#f59e0b'],   # Желтый/оранжевый (удовлетворительно)
    [0.66, '#eab308'],   # Ярко-желтый (хорошо)
    [1, '#22c55e']       # Зеленый (отличные оценки)
]


def get_max_grade_from_grading_system() -> Optional[float]:
    """
    Получает максимальную оценку из системы оценивания.
    
    Returns:
        Максимальная оценка или None, если система оценивания не настроена
    """
    try:
        grading_system_file = PROCESSED_DIR / "grading_system.json"
        if not grading_system_file.exists():
            return None
        
        with open(grading_system_file, 'r', encoding='utf-8') as f:
            grading_system = json.load(f)
        
        system_type = grading_system.get('system_type')
        
        if system_type == '5-point':
            return 5.0
        elif system_type == '100-point':
            return 100.0
        elif system_type == 'custom':
            max_grade = grading_system.get('max_grade')
            if max_grade is not None:
                return float(max_grade)
        
        return None
    except Exception as e:
        logger.warning(f"Ошибка загрузки системы оценивания: {e}")
        return None


def create_grade_distribution_plot(df: pd.DataFrame, student_id: Optional[int] = None, 
                                   subject: Optional[str] = None) -> Dict:
    """
    Создаёт современный график распределения оценок с KDE кривой.
    
    Args:
        df: DataFrame с данными об оценках
        student_id: ID студента (если None, по всем студентам)
        subject: Предмет (если None, по всем предметам)
        
    Returns:
        Словарь с данными для Plotly (data и layout)
    """
    try:
        if df.empty or 'grade' not in df.columns:
            logger.warning("Нет данных для графика распределения оценок")
            return {"data": [], "layout": {"title": "Распределение оценок"}}
        
        # Применяем фильтры
        filtered_df = df.copy()
        
        if student_id is not None:
            try:
                student_id_int = int(student_id)
                if 'student_id' in filtered_df.columns:
                    filtered_df['student_id'] = pd.to_numeric(filtered_df['student_id'], errors='coerce')
                    filtered_df = filtered_df[filtered_df['student_id'] == student_id_int]
            except (ValueError, TypeError):
                logger.warning(f"Некорректный student_id: {student_id}")
        
        if subject is not None and subject.strip():
            if 'subject' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['subject'].str.lower() == subject.lower().strip()]
        
        if filtered_df.empty:
            logger.warning("Нет данных после фильтрации для графика распределения")
            return {"data": [], "layout": {"title": "Распределение оценок - Нет данных"}}
        
        # Формируем заголовок с учетом фильтров
        if student_id is not None and 'student_name' in filtered_df.columns:
            student_names = filtered_df['student_name'].unique()
            if len(student_names) > 0:
                if subject is not None and subject.strip():
                    title_text = f"Распределение оценок студента {student_names[0]} по предмету {subject.strip()}"
                else:
                    title_text = f"Распределение оценок студента {student_names[0]}"
        elif subject is not None and subject.strip():
            title_text = f"Распределение оценок по предмету {subject.strip()}"
        else:
            title_text = "Распределение оценок"
        
        # Обработка данных
        grades = filtered_df['grade'].dropna()
        grades_list = []
        for g in grades.tolist():
            try:
                grade_val = float(g)
                if not pd.isna(grade_val):
                    grades_list.append(grade_val)
            except (ValueError, TypeError):
                continue
        
        if not grades_list or len(grades_list) == 0:
            logger.warning("Нет валидных оценок для графика распределения")
            return {"data": [], "layout": {"title": "Распределение оценок"}}
        
        # Статистика
        mean_grade = np.mean(grades_list)
        median_grade = np.median(grades_list)
        std_grade = np.std(grades_list)
        min_grade = min(grades_list)
        max_grade = max(grades_list)
        
        # Подсчитываем частоту каждой уникальной оценки
        grade_counts = Counter(grades_list)
        
        # Сортируем оценки по значению
        unique_grades_sorted = sorted(grade_counts.keys())
        frequencies = [grade_counts[grade] for grade in unique_grades_sorted]
        num_unique_grades = len(unique_grades_sorted)
        
        # Вычисляем плотность (вероятность) для каждой оценки
        total_count = len(grades_list)
        densities = [freq / total_count for freq in frequencies]
        
        # Всегда используем категориальную ось X - она показывает только те оценки, которые есть в данных
        # Столбцы будут одинаковой ширины и автоматически растянутся по всей ширине графика
        # bargap контролирует промежуток между столбцами: меньше bargap = шире столбцы
        # Используем очень маленькие значения для максимально широких столбцов
        if num_unique_grades == 1:
            bargap = 0.0   # Максимально широкие столбцы для 1 оценки (без промежутков)
        elif num_unique_grades <= 3:
            bargap = 0.02  # Очень широкие столбцы для 2-3 оценок
        elif num_unique_grades <= 5:
            bargap = 0.03  # Широкие столбцы для 4-5 оценок
        elif num_unique_grades <= 8:
            bargap = 0.05  # Средне-широкие столбцы для 6-8 оценок
        elif num_unique_grades <= 12:
            bargap = 0.06  # Средние столбцы для 9-12 оценок (значительно уменьшено)
        elif num_unique_grades <= 15:
            bargap = 0.08  # Средне-узкие столбцы для 13-15 оценок
        elif num_unique_grades <= 20:
            bargap = 0.1   # Узкие столбцы для 16-20 оценок (значительно уменьшено)
        else:
            # Для большого количества оценок используем формулу для плавной адаптации
            bargap = min(0.2, 0.08 + (num_unique_grades - 20) * 0.002)
        
        # Создаем компактный график
        fig = go.Figure()
        
        # Столбчатая диаграмма - по одной для каждой уникальной оценки
        # Категориальная ось X автоматически покажет только существующие оценки
        # и распределит столбцы равномерно с одинаковой шириной
        fig.add_trace(
            go.Bar(
                x=unique_grades_sorted,
                y=densities,
                name="Распределение",
                marker_color=COLORS['primary'],
                marker_line_color='white',
                marker_line_width=0.5,
                opacity=0.8,
                hovertemplate='Оценка: %{x}<br>Плотность: %{y:.3f}<br>Количество: %{customdata}<extra></extra>',
                customdata=frequencies,
                showlegend=False
            )
        )
        
        # KDE кривая (оценка плотности) - упрощенная версия
        try:
            x_kde = np.linspace(min_grade, max_grade, 150)
            kde = stats.gaussian_kde(grades_list)
            y_kde = kde(x_kde)
            
            fig.add_trace(
                go.Scatter(
                    x=x_kde,
                    y=y_kde,
                    mode='lines',
                    name='KDE',
                    line=dict(color=COLORS['danger'], width=2),
                    fill='tozeroy',
                    fillcolor=f"rgba(239, 68, 68, 0.1)",
                    hovertemplate='Оценка: %{x:.2f}<br>Плотность: %{y:.3f}<extra></extra>',
                    showlegend=False
                )
            )
        except Exception as e:
            logger.warning(f"Не удалось построить KDE кривую: {e}")
        
        
        # Компактный layout (без фиксированной высоты для адаптивности)
        fig.update_layout(
            title={
                'text': title_text,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 14, 'color': COLORS['dark']},
                'y': 0.98,
                'pad': {'b': 5}
            },
            template="plotly_white",
            hovermode='x unified',
            showlegend=True,
            autosize=True,  # Включаем автоподстройку размера
            margin=dict(l=55, r=15, t=45, b=55),  # Компактные отступы для dashboard
            font=dict(family="Arial, sans-serif", size=10, color=COLORS['dark']),
            plot_bgcolor='white',
            paper_bgcolor='white',
            legend=dict(
                x=0.99,  # Правее
                y=0.99,  # Выше
                xanchor='right',
                yanchor='top',
                bgcolor='rgba(255,255,255,0.9)',
                bordercolor=COLORS['light'],
                borderwidth=1,
                font=dict(size=9),
                itemwidth=30,
                tracegroupgap=3
            ),
            xaxis=dict(
                title=dict(text="Оценка", font=dict(size=11)),
                type='category',  # Всегда категориальная ось - показывает только существующие оценки
                showgrid=True,
                gridcolor=COLORS['light'],
                gridwidth=0.5,
                domain=[0, 1]  # Ось X занимает всю ширину графика (от 0 до 1)
            ),
            bargap=bargap,  # Промежуток между столбцами (контролирует ширину столбцов)
            bargroupgap=0,  # Убираем промежутки между группами столбцов (если есть)
            yaxis=dict(
                title=dict(text="Плотность", font=dict(size=11)),
                showgrid=True,
                gridcolor=COLORS['light'],
                gridwidth=0.5,
                rangemode='tozero'
            )
        )
        
        # Добавляем статистику в подзаголовок через аннотацию
        fig.add_annotation(
            x=0.02,
            y=0.98,
            xref='paper',
            yref='paper',
            text=f'μ={mean_grade:.2f} | σ={std_grade:.2f}',
            showarrow=False,
            font=dict(size=9, color=COLORS['dark']),
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor=COLORS['light'],
            borderwidth=1,
            xanchor='left',
            yanchor='top'
        )
        
        return fig.to_dict()
    except Exception as e:
        logger.error(f"Ошибка создания графика распределения оценок: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"data": [], "layout": {"title": "Распределение оценок - Ошибка"}}


def create_performance_trend_plot(df: pd.DataFrame, student_id: Optional[int] = None,
                                  subject: Optional[str] = None) -> Dict:
    """
    Создаёт современный график динамики успеваемости с областями доверия.
    Автоматически масштабируется под доступные данные.
    
    Args:
        df: DataFrame с данными об оценках
        student_id: ID студента (если None, по всем студентам)
        subject: Предмет (если None, по всем предметам)
        
    Returns:
        Словарь с данными для Plotly
    """
    try:
        # Проверка входных данных
        if df.empty or 'date' not in df.columns or 'grade' not in df.columns:
            logger.warning("Нет данных для графика динамики успеваемости")
            return {"data": [], "layout": {"title": "Динамика успеваемости"}}
        
        filtered_df = df.copy()
        
        # Применяем фильтры по студенту
        if student_id is not None:
            try:
                student_id_int = int(student_id)
                if 'student_id' in filtered_df.columns:
                    filtered_df['student_id'] = pd.to_numeric(filtered_df['student_id'], errors='coerce')
                    filtered_df = filtered_df[filtered_df['student_id'] == student_id_int]
            except (ValueError, TypeError):
                logger.warning(f"Некорректный student_id: {student_id}")
        
        # Применяем фильтры по предмету
        if subject is not None and subject.strip():
            if 'subject' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['subject'].str.lower() == subject.lower().strip()]
        
        if filtered_df.empty:
            logger.warning("Нет данных после фильтрации для графика динамики")
            return {"data": [], "layout": {"title": "Динамика успеваемости - Нет данных"}}
        
        # Обработка дат
        filtered_df['date'] = pd.to_datetime(filtered_df['date'], errors='coerce')
        filtered_df = filtered_df.dropna(subset=['date', 'grade'])
        
        if filtered_df.empty:
            logger.warning("Нет валидных дат для графика динамики")
            return {"data": [], "layout": {"title": "Динамика успеваемости"}}
        
        # Сортируем по дате и создаем периоды
        filtered_df = filtered_df.sort_values('date')
        filtered_df['year_month'] = filtered_df['date'].dt.to_period('M')
        
        # Агрегация по месяцам
        monthly_stats = filtered_df.groupby('year_month')['grade'].agg([
            'mean', 'median', 'std', 'count', 'min', 'max'
        ]).reset_index()
        
        # Фильтруем месяцы с достаточным количеством данных (минимум 1 оценка)
        monthly_stats = monthly_stats[monthly_stats['count'] >= 1]
        
        if monthly_stats.empty:
            logger.warning("Нет месяцев с данными")
            return {"data": [], "layout": {"title": "Динамика успеваемости - Недостаточно данных"}}
        
        # Сортируем по периоду
        monthly_stats = monthly_stats.sort_values('year_month')
        
        # Адаптивный выбор периода: если данных больше 12 месяцев, показываем последние 12
        max_months_to_show = 12
        if len(monthly_stats) > max_months_to_show:
            monthly_stats = monthly_stats.tail(max_months_to_show).copy()
            logger.info(f"Ограничен период до последних {max_months_to_show} месяцев для лучшей читаемости графика")
        
        # Создаем строковые метки для месяцев
        monthly_stats['month_str'] = monthly_stats['year_month'].apply(
            lambda x: x.strftime('%b %Y') if pd.notna(x) else str(x)
        )
        
        # Заполняем NaN в std
        monthly_stats['std'] = monthly_stats['std'].fillna(0)
        
        # Проверяем, что есть данные для отображения
        if len(monthly_stats) == 0:
            logger.warning("Нет данных для отображения на графике")
            return {"data": [], "layout": {"title": "Динамика успеваемости - Нет данных"}}
        
        # Получаем список месяцев для оси X
        month_labels = monthly_stats['month_str'].tolist()
        
        # Проверяем, что все значения валидны
        if monthly_stats['mean'].isna().any() or monthly_stats['median'].isna().any():
            logger.warning("Обнаружены NaN значения в данных")
            monthly_stats = monthly_stats.dropna(subset=['mean', 'median'])
            if monthly_stats.empty:
                return {"data": [], "layout": {"title": "Динамика успеваемости - Нет валидных данных"}}
            month_labels = monthly_stats['month_str'].tolist()
        
        logger.info(f"Создание графика с {len(monthly_stats)} точками данных")
        
        fig = go.Figure()
        
        # Область доверия (std) - преобразуем в списки Python
        upper_bound = (monthly_stats['mean'] + monthly_stats['std']).tolist()
        lower_bound = (monthly_stats['mean'] - monthly_stats['std']).tolist()
        
        fig.add_trace(go.Scatter(
            x=month_labels,
            y=upper_bound,
            mode='lines',
            name='+1σ',
            line=dict(width=0),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        fig.add_trace(go.Scatter(
            x=month_labels,
            y=lower_bound,
            mode='lines',
            name='Область доверия',
            fill='tonexty',
            fillcolor=f"rgba(99, 102, 241, 0.2)",
            line=dict(width=0),
            hovertemplate='Период: %{x}<br>Нижняя граница: %{y:.2f}<extra></extra>'
        ))
        
        # Основная линия (среднее) - преобразуем в список Python
        mean_values = monthly_stats['mean'].tolist()
        count_values = monthly_stats['count'].tolist()
        
        fig.add_trace(go.Scatter(
            x=month_labels,
            y=mean_values,
            mode='lines+markers',
            name='Средняя оценка',
            line=dict(color=COLORS['primary'], width=3),
            marker=dict(size=10, color=COLORS['primary'], line=dict(width=2, color='white')),
            hovertemplate='Период: %{x}<br>Средняя оценка: %{y:.2f}<br>Количество: %{customdata}<extra></extra>',
            customdata=count_values
        ))
        
        # Линия медианы - преобразуем в список Python
        median_values = monthly_stats['median'].tolist()
        
        fig.add_trace(go.Scatter(
            x=month_labels,
            y=median_values,
            mode='lines',
            name='Медианная оценка',
            line=dict(color=COLORS['success'], width=2, dash='dash'),
            hovertemplate='Период: %{x}<br>Медианная оценка: %{y:.2f}<extra></extra>'
        ))
        
        # Трендовая линия (линейная регрессия)
        try:
            if len(monthly_stats) >= 2:
                x_numeric = np.arange(len(monthly_stats))
                slope, intercept, r_value, p_value, std_err = stats.linregress(
                    x_numeric, monthly_stats['mean']
                )
                trend_line = (slope * x_numeric + intercept).tolist()
                
                fig.add_trace(go.Scatter(
                    x=month_labels,
                    y=trend_line,
                    mode='lines',
                    name=f'Тренд (R²={r_value**2:.3f})',
                    line=dict(color=COLORS['danger'], width=2, dash='dot'),
                    hovertemplate='Период: %{x}<br>Тренд: %{y:.2f}<extra></extra>'
                ))
        except Exception as e:
            logger.warning(f"Не удалось построить трендовую линию: {e}")
        
        # Формируем заголовок
        title = "Динамика успеваемости"
        if student_id is not None:
            if not filtered_df.empty and 'student_name' in filtered_df.columns:
                student_names = filtered_df['student_name'].unique()
                if len(student_names) > 0:
                    title += f" - {student_names[0]}"
                else:
                    title += f" - Студент {student_id}"
            else:
                title += f" - Студент {student_id}"
        if subject is not None and subject.strip():
            title += f" - {subject}"
        
        # Вычисляем диапазон для оси Y
        # Учитываем не только средние значения, но и границы области доверия
        min_mean = monthly_stats['mean'].min()
        max_mean = monthly_stats['mean'].max()
        min_lower = (monthly_stats['mean'] - monthly_stats['std']).min()
        max_upper = (monthly_stats['mean'] + monthly_stats['std']).max()
        
        # Находим реальные минимальные и максимальные значения с учетом области доверия
        data_min = min(min_mean, min_lower)
        data_max = max(max_mean, max_upper)
        
        # Добавляем отступы (15% от диапазона или минимум 0.3)
        data_range = data_max - data_min
        padding = max(data_range * 0.15, 0.3)
        
        # Вычисляем финальный диапазон оси Y (убираем ограничение до 5, чтобы поддерживать любой диапазон)
        y_min = max(0, data_min - padding)  # Минимум не ниже 0
        y_max = data_max + padding  # Убираем ограничение min(5, ...), чтобы поддерживать любые значения
        y_full_range = y_max - y_min
        
        # Настройка оси Y с автоматическим масштабированием и ограничением меток
        # Используем autorange=True для автоматического масштабирования
        # и tickmode='auto' с nticks для скрытия части меток, чтобы избежать "мешанины"
        yaxis_config = dict(
            title=dict(
                text="Оценка",
                font=dict(size=12, color=COLORS['dark'])
            ),
            autorange=True,  # Автоматическое масштабирование
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)',
            gridwidth=1,
            showline=True,
            linecolor='rgba(0,0,0,0.3)',
            linewidth=1,
            zeroline=False,
            tickmode='auto',  # Автоматический режим - Plotly сам выберет метки
            nticks=6,  # Ограничиваем количество меток максимум 6 - лишние будут скрыты
            tickfont=dict(size=10, color=COLORS['dark']),
            side='left',
            rangemode='normal'  # Нормальный режим масштабирования (не принудительно от 0)
        )
        
        # Настройка layout с правильным автомасштабированием
        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': COLORS['dark']}
            },
            xaxis_title="Период",
            template="plotly_white",
            hovermode='x unified',
            xaxis=dict(
                type='category',
                categoryorder='array',
                categoryarray=month_labels,
                tickangle=-45
            ),
            yaxis=yaxis_config,
            legend=dict(
                x=0.98,
                y=0.98,
                xanchor='right',
                yanchor='top',
                bgcolor='rgba(255,255,255,0.95)',
                bordercolor=COLORS['light'],
                borderwidth=1,
                font=dict(size=9)
            ),
            autosize=True,
            margin=dict(l=70, r=80, t=70, b=100),  # Увеличен нижний отступ для наклонных меток
            font=dict(family="Arial, sans-serif", size=11, color=COLORS['dark']),
            plot_bgcolor='white',
            paper_bgcolor='white',
        )
        
        return fig.to_dict()
    except Exception as e:
        logger.error(f"Ошибка создания графика динамики успеваемости: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"data": [], "layout": {"title": "Динамика успеваемости - Ошибка"}}


def create_subject_comparison_plot(df: pd.DataFrame, student_id: Optional[int] = None) -> Dict:
    """
    Создаёт современный график сравнения средних оценок по предметам.
    
    Args:
        df: DataFrame с данными об оценках
        student_id: Опциональный фильтр по ID студента. Если указан, показываются средние оценки только этого студента
        
    Returns:
        Словарь с данными для Plotly
    """
    try:
        if df.empty or 'subject' not in df.columns:
            return {"data": [], "layout": {}}
        
        # Фильтруем данные по студенту, если указан
        filtered_df = df.copy()
        student_name = None
        if student_id is not None:
            if 'student_id' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['student_id'] == student_id]
                # Получаем имя студента для заголовка
                if 'student_name' in filtered_df.columns and not filtered_df.empty:
                    student_name = filtered_df['student_name'].iloc[0]
        
        if filtered_df.empty:
            return {"data": [], "layout": {}}
        
        subject_stats = filtered_df.groupby('subject')['grade'].agg([
            'mean', 'std', 'count', 'median'
        ]).reset_index()
        
        subject_stats = subject_stats.sort_values('mean', ascending=False)
        subject_stats['std'] = subject_stats['std'].fillna(0)
        
        fig = go.Figure()
        
        # Столбчатая диаграмма с ошибками
        colors = px.colors.qualitative.Set3[:len(subject_stats)]
        
        # Вертикальные столбцы: предметы на оси X, оценки на оси Y
        # Высота столбцов напрямую соответствует средним оценкам по предмету
        mean_values = subject_stats['mean'].tolist()  # Преобразуем в список для точной передачи значений
        
        fig.add_trace(go.Bar(
            x=subject_stats['subject'].tolist(),  # Предметы на горизонтальной оси X
            y=mean_values,  # Средние оценки на вертикальной оси Y - высота столбца = значение оценки
            name="Средняя оценка",
            orientation='v',  # Явно указываем вертикальную ориентацию
            marker_color=COLORS['primary'],
            marker_line_color='white',
            marker_line_width=2,
            error_y=dict(
                type='data',
                array=subject_stats['std'],
                visible=True,
                color=COLORS['dark'],
                thickness=2
            ),
            text=[f"{val:.2f}" for val in mean_values],  # Форматирование с 2 знаками после запятой - соответствует высоте столбца
            textposition='auto',  # Автоматическое позиционирование
            textfont=dict(size=10, color=COLORS['dark']),
            hovertemplate='Предмет: %{x}<br>Средняя оценка: %{y:.2f}<br>Ст. отклонение: %{customdata[0]:.2f}<br>Количество: %{customdata[1]}<extra></extra>',
            customdata=subject_stats[['std', 'count']].values
        ))
        
        # Горизонтальная линия для общего среднего (вычисляется на основе отфильтрованных данных)
        overall_mean = filtered_df['grade'].mean()
        if student_name:
            annotation_text = f"Среднее студента: {overall_mean:.2f}"
        else:
            annotation_text = f"Общее среднее: {overall_mean:.2f}"
        fig.add_hline(
            y=overall_mean,
            line_dash="dash",
            line_color=COLORS['danger'],
            annotation_text=annotation_text,
            annotation_position="right"
        )
        
        # Вычисляем диапазон данных для максимальной наглядности
        # Используем только средние значения для определения границ столбцов
        # (ошибки std отображаются как линии, они не должны влиять на масштаб)
        max_grade = float(subject_stats['mean'].max())
        min_grade = float(subject_stats['mean'].min())
        
        # Вычисляем диапазон данных
        data_range = max_grade - min_grade
        
        # Для максимальной наглядности: минимальные отступы
        # Меньший столбец должен быть у самого низа, больший - почти у потолка
        # Нижний отступ должен быть достаточным, чтобы минимальный столбец был виден хотя бы на пару шагов по оси Y
        if data_range > 0:
            # Адаптивный нижний отступ: 15% от диапазона или минимум для видимости столбца (увеличен в 3 раза)
            # Это гарантирует, что минимальный столбец будет виден хотя бы на пару шагов по оси Y
            padding_bottom = max(data_range * 0.15, 0.6)  # Увеличенный в 3 раза отступ снизу для видимости
            padding_top = max(data_range * 0.02, 0.1)  # Очень маленький отступ сверху
        else:
            # Если все значения одинаковые, добавляем небольшой отступ для визуализации
            padding_bottom = 0.6
            padding_top = 0.1
        
        # Вычисляем финальный диапазон оси Y для максимальной наглядности
        # Минимум с достаточным отступом, чтобы минимальный столбец был виден
        y_min = max(0, min_grade - padding_bottom)
        # Максимум очень близко к максимальному значению (почти касается потолка)
        y_max = max_grade + padding_top
        
        # Адаптивное вычисление оптимального количества меток на основе диапазона
        # Для маленьких диапазонов (1-5) используем меньше меток, для больших (0-100) - больше
        if data_range <= 5:
            # Маленький диапазон (например, оценки от 1 до 5)
            optimal_nticks = max(4, min(6, int(data_range * 1.5) + 2))
        elif data_range <= 20:
            # Средний диапазон (например, оценки от 0 до 20)
            optimal_nticks = max(5, min(8, int(data_range / 3) + 3))
        elif data_range <= 50:
            # Большой диапазон (например, баллы от 0 до 50)
            optimal_nticks = max(6, min(10, int(data_range / 8) + 4))
        else:
            # Очень большой диапазон (например, баллы от 0 до 100)
            optimal_nticks = max(6, min(12, int(data_range / 12) + 5))
        
        # Формируем заголовок в зависимости от того, выбран ли конкретный студент
        if student_name:
            title_text = f'Сравнение средних оценок по предметам - {student_name}'
        else:
            title_text = 'Сравнение средних оценок по предметам'
        
        # Настройка оси Y с вычисленным диапазоном для максимизации визуальной разницы
        yaxis_config = dict(
            title=dict(
                text="Средняя оценка",
                font=dict(size=12, color=COLORS['dark'])
            ),
            range=[y_min, y_max],  # Явно задаем диапазон для максимизации разницы
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)',
            gridwidth=1,
            showline=True,
            linecolor='rgba(0,0,0,0.3)',
            linewidth=1,
            zeroline=False,
            tickmode='auto',  # Автоматический режим - Plotly сам выберет метки
            nticks=optimal_nticks,  # Адаптивное ограничение количества меток
            tickfont=dict(size=10, color=COLORS['dark']),
            side='left',
            rangemode='normal'  # Нормальный режим масштабирования (не принудительно от 0)
        )
        
        fig.update_layout(
            title={
                'text': title_text,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': COLORS['dark']}
            },
            xaxis_title="Предмет",
            template="plotly_white",
            hovermode='x unified',
            xaxis=dict(tickangle=-45),
            yaxis=yaxis_config,
            autosize=True,  # Адаптивный размер
            margin=dict(l=70, r=80, t=70, b=100),  # Увеличен нижний отступ для повернутых меток
            font=dict(family="Arial, sans-serif", size=11, color=COLORS['dark']),
            plot_bgcolor='white',
            paper_bgcolor='white',
        )
        
        return fig.to_dict()
    except Exception as e:
        logger.error(f"Ошибка создания графика сравнения предметов: {e}")
        return {"data": [], "layout": {}}


def create_student_comparison_plot(df: pd.DataFrame, subject: Optional[str] = None,
                                   top_n: int = 10) -> Dict:
    """
    Создаёт современный график сравнения студентов с radar chart.
    
    Args:
        df: DataFrame с данными об оценках
        subject: Предмет (если None, по всем предметам)
        top_n: Количество студентов для отображения
        
    Returns:
        Словарь с данными для Plotly
    """
    try:
        if df.empty:
            return {"data": [], "layout": {}}
        
        filtered_df = df.copy()
        
        if subject is not None:
            filtered_df = filtered_df[filtered_df['subject'].str.lower() == subject.lower()]
        
        if filtered_df.empty:
            return {"data": [], "layout": {}}
        
        # Вычисляем средний балл по каждому студенту
        student_avg = filtered_df.groupby(['student_id', 'student_name'])['grade'].agg([
            'mean', 'count', 'std'
        ]).reset_index()
        
        # Берем top_n студентов по среднему баллу, затем сортируем по возрастанию слева направо
        student_avg = student_avg.nlargest(top_n, 'mean')
        # Сортируем по возрастанию, чтобы столбцы шли по возрастанию слева направо
        student_avg = student_avg.sort_values('mean', ascending=True).reset_index(drop=True)
        student_avg['std'] = student_avg['std'].fillna(0)
        
        # Явно преобразуем данные в списки Python с правильными типами
        student_names = student_avg['student_name'].tolist()
        mean_values = [float(val) for val in student_avg['mean'].tolist()]
        std_values = [float(val) for val in student_avg['std'].tolist()]
        count_values = [int(val) for val in student_avg['count'].tolist()]
        
        fig = go.Figure()
        
        # Вертикальная столбчатая диаграмма: имена на X, оценки на Y
        fig.add_trace(go.Bar(
            x=student_names,
            y=mean_values,
            orientation='v',
            name="Средняя оценка",
            marker_color=COLORS['primary'],
            marker_line_color='white',
            marker_line_width=2,
            text=[f"{val:.2f}" for val in mean_values],  # Форматирование с 2 знаками после запятой
            textposition='auto',  # Автоматическое позиционирование
            textfont=dict(size=10, color=COLORS['dark']),
            hovertemplate='Студент: %{x}<br>Средняя оценка: %{y:.2f}<br>Количество: %{customdata[0]}<br>Ст. отклонение: %{customdata[1]:.2f}<extra></extra>',
            customdata=list(zip(count_values, std_values))
        ))
        
        # Вычисляем диапазон данных для максимальной наглядности
        # Используем только средние значения для определения границ столбцов
        # (ошибки std отображаются как линии, они не должны влиять на масштаб)
        max_grade = float(max(mean_values)) if mean_values else 0
        min_grade = float(min(mean_values)) if mean_values else 0
        
        # Вычисляем диапазон данных
        data_range = max_grade - min_grade
        
        # Для максимальной наглядности: минимальные отступы
        # Меньший столбец должен быть у самого низа, больший - почти у потолка
        # Нижний отступ должен быть достаточным, чтобы минимальный столбец был виден хотя бы на пару шагов по оси Y
        if data_range > 0:
            # Адаптивный нижний отступ: 15% от диапазона или минимум для видимости столбца (увеличен в 3 раза)
            # Это гарантирует, что минимальный столбец будет виден хотя бы на пару шагов по оси Y
            padding_bottom = max(data_range * 0.15, 0.6)  # Увеличенный в 3 раза отступ снизу для видимости
            padding_top = max(data_range * 0.02, 0.1)  # Очень маленький отступ сверху
        else:
            # Если все значения одинаковые, добавляем небольшой отступ для визуализации
            padding_bottom = 0.6
            padding_top = 0.1
        
        # Вычисляем финальный диапазон оси Y для максимальной наглядности
        # Минимум с достаточным отступом, чтобы минимальный столбец был виден
        y_min = max(0, min_grade - padding_bottom)
        # Максимум очень близко к максимальному значению (почти касается потолка)
        y_max = max_grade + padding_top
        
        # Адаптивное вычисление оптимального количества меток на основе диапазона
        # Для маленьких диапазонов (1-5) используем меньше меток, для больших (0-100) - больше
        if data_range <= 5:
            # Маленький диапазон (например, оценки от 1 до 5)
            optimal_nticks = max(4, min(6, int(data_range * 1.5) + 2))
        elif data_range <= 20:
            # Средний диапазон (например, оценки от 0 до 20)
            optimal_nticks = max(5, min(8, int(data_range / 3) + 3))
        elif data_range <= 50:
            # Большой диапазон (например, баллы от 0 до 50)
            optimal_nticks = max(6, min(10, int(data_range / 8) + 4))
        else:
            # Очень большой диапазон (например, баллы от 0 до 100)
            optimal_nticks = max(6, min(12, int(data_range / 12) + 5))
        
        title = "Сравнение студентов"
        if subject is not None:
            title += f" - {subject}"
        else:
            title += " (по всем предметам)"
        
        # Настройка оси Y с вычисленным диапазоном для максимизации визуальной разницы
        yaxis_config = dict(
            title=dict(
                text="Средняя оценка",
                font=dict(size=12, color=COLORS['dark'])
            ),
            range=[y_min, y_max],  # Явно задаем диапазон для максимизации разницы
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)',
            gridwidth=1,
            showline=True,
            linecolor='rgba(0,0,0,0.3)',
            linewidth=1,
            zeroline=False,
            tickmode='auto',  # Автоматический режим - Plotly сам выберет метки
            nticks=optimal_nticks,  # Адаптивное ограничение количества меток
            tickfont=dict(size=10, color=COLORS['dark']),
            side='left',
            rangemode='normal'  # Нормальный режим масштабирования (не принудительно от 0)
        )
        
        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': COLORS['dark']}
            },
            xaxis_title="Студент",
            template="plotly_white",
            hovermode='x unified',
            xaxis=dict(
                tickangle=-45,  # Наклон меток для лучшей читаемости
                categoryorder='array',
                categoryarray=student_names
            ),
            yaxis=yaxis_config,
            autosize=True,  # Адаптивный размер
            margin=dict(l=70, r=100, t=70, b=150),  # Увеличен нижний отступ для наклонных имен
            font=dict(family="Arial, sans-serif", size=11, color=COLORS['dark']),
            plot_bgcolor='white',
            paper_bgcolor='white',
        )
        
        return fig.to_dict()
    except Exception as e:
        logger.error(f"Ошибка создания графика сравнения студентов: {e}")
        return {"data": [], "layout": {}}


def create_subject_heatmap(df: pd.DataFrame, student_id: Optional[int] = None) -> Dict:
    """
    Создаёт улучшенную тепловую карту успеваемости по предметам и времени.
    
    Args:
        df: DataFrame с данными об оценках
        student_id: ID студента (если None, по всем студентам)
        
    Returns:
        Словарь с данными для Plotly
    """
    try:
        if df.empty or 'date' not in df.columns or 'subject' not in df.columns:
            logger.warning("Нет данных для тепловой карты")
            return {"data": [], "layout": {"title": "Тепловая карта по предметам"}}
        
        filtered_df = df.copy()
        
        if student_id is not None:
            try:
                student_id_int = int(student_id)
                if 'student_id' in filtered_df.columns:
                    filtered_df['student_id'] = pd.to_numeric(filtered_df['student_id'], errors='coerce')
                    filtered_df = filtered_df[filtered_df['student_id'] == student_id_int]
            except (ValueError, TypeError):
                logger.warning(f"Некорректный student_id: {student_id}")
        
        if filtered_df.empty:
            logger.warning("Нет данных после фильтрации для тепловой карты")
            return {"data": [], "layout": {"title": "Тепловая карта по предметам"}}
        
        filtered_df = filtered_df.dropna(subset=['date', 'subject', 'grade'])
        
        if filtered_df.empty:
            logger.warning("Нет валидных данных для тепловой карты")
            return {"data": [], "layout": {"title": "Тепловая карта по предметам"}}
        
        try:
            filtered_df['date'] = pd.to_datetime(filtered_df['date'], errors='coerce')
            filtered_df = filtered_df.dropna(subset=['date'])
            
            if filtered_df.empty:
                logger.warning("Нет валидных дат для тепловой карты")
                return {"data": [], "layout": {"title": "Тепловая карта по предметам"}}
            
            filtered_df['month'] = filtered_df['date'].dt.to_period('M').astype(str)
        except Exception as e:
            logger.error(f"Ошибка обработки дат для тепловой карты: {e}")
            return {"data": [], "layout": {"title": "Тепловая карта по предметам - Ошибка"}}
        
        try:
            pivot_df = filtered_df.pivot_table(
                values='grade',
                index='subject',
                columns='month',
                aggfunc='mean',
                fill_value=None
            )
            
            if pivot_df.empty:
                logger.warning("Сводная таблица для тепловой карты пуста")
                return {"data": [], "layout": {"title": "Тепловая карта по предметам"}}
            
            pivot_df.columns = [str(col) for col in pivot_df.columns]
            pivot_df.index = pivot_df.index.astype(str)
            
            z_values = pivot_df.values.tolist()
            for i in range(len(z_values)):
                for j in range(len(z_values[i])):
                    if pd.isna(z_values[i][j]):
                        z_values[i][j] = None
            
            text_values = []
            for row in z_values:
                text_row = []
                for val in row:
                    if val is not None and not pd.isna(val):
                        try:
                            text_row.append(f"{float(val):.2f}")
                        except (ValueError, TypeError):
                            text_row.append("")
                    else:
                        text_row.append("")
                text_values.append(text_row)
            
            # Вычисляем реальный минимум и максимум из данных (исключая None)
            all_values = [val for row in z_values for val in row if val is not None and not pd.isna(val)]
            if not all_values:
                logger.warning("Нет валидных значений для тепловой карты")
                return {"data": [], "layout": {"title": "Тепловая карта по предметам"}}
            
            z_min = 0  # Минимум всегда 0
            
            # Получаем максимальную оценку из системы оценивания
            max_grade_from_system = get_max_grade_from_grading_system()
            if max_grade_from_system is not None:
                z_max = max_grade_from_system
            else:
                # Если система оценивания не настроена, используем максимум из данных
                z_max = max(all_values)
            
            # Если максимум меньше 1, устанавливаем его в 1 для корректного отображения
            if z_max < 1:
                z_max = 1
            
            fig = go.Figure(data=go.Heatmap(
                z=z_values,
                x=pivot_df.columns.tolist(),
                y=pivot_df.index.tolist(),
                colorscale=HEATMAP_COLORS,
                zmin=z_min,  # Минимум для градиента
                zmax=z_max,  # Максимум для градиента (динамический)
                text=text_values,
                texttemplate='%{text}',
                textfont={"size": 11, "color": "#1f2937"},  # Темно-серый цвет для лучшей видимости на светлых цветах (желтый, зеленый)
                colorbar=dict(
                    title=dict(text="Оценка", font=dict(size=14)),
                    tickfont=dict(size=12)
                ),
                hovertemplate='Предмет: %{y}<br>Период: %{x}<br>Оценка: %{z:.2f}<extra></extra>'
            ))
            
            title = "Тепловая карта успеваемости по предметам"
            if student_id is not None:
                student_name = filtered_df['student_name'].iloc[0] if 'student_name' in filtered_df.columns and len(filtered_df) > 0 else f"Студент {student_id}"
                title += f" - {student_name}"
            
            fig.update_layout(
                title={
                    'text': title,
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'size': 18, 'color': COLORS['dark']}
                },
                xaxis_title="Период",
                yaxis_title="Предмет",
                template="plotly_white",
                autosize=True,  # Адаптивный размер
                margin=dict(l=100, r=100, t=70, b=100),  # Отступы для colorbar и меток
                font=dict(family="Arial, sans-serif", size=11, color=COLORS['dark']),
                plot_bgcolor='white',
                paper_bgcolor='white',
            )
            
            return fig.to_dict()
        except Exception as e:
            logger.error(f"Ошибка создания сводной таблицы для тепловой карты: {e}")
            return {"data": [], "layout": {"title": "Тепловая карта по предметам - Ошибка"}}
    except Exception as e:
        logger.error(f"Ошибка создания тепловой карты: {e}")
        return {"data": [], "layout": {"title": "Тепловая карта по предметам - Ошибка"}}


def create_box_plot_by_subject(df: pd.DataFrame) -> Dict:
    """
    Создаёт улучшенный violin plot оценок по предметам.
    
    Args:
        df: DataFrame с данными об оценках
        
    Returns:
        Словарь с данными для Plotly
    """
    try:
        if df.empty or 'subject' not in df.columns or 'grade' not in df.columns:
            logger.warning("Нет данных для violin plot по предметам")
            return {"data": [], "layout": {"title": "Violin-plot по предметам"}}
        
        filtered_df = df.dropna(subset=['subject', 'grade'])
        
        if filtered_df.empty:
            logger.warning("Нет валидных данных для violin plot")
            return {"data": [], "layout": {"title": "Violin-plot по предметам"}}
        
        subjects = filtered_df['subject'].unique()
        
        if len(subjects) == 0:
            logger.warning("Нет предметов для violin plot")
            return {"data": [], "layout": {"title": "Violin-plot по предметам"}}
        
        fig = go.Figure()
        
        # Используем violin plot вместо box plot для лучшей визуализации распределения
        for subject in subjects:
            subject_data = filtered_df[filtered_df['subject'] == subject]['grade'].dropna()
            
            grades_list = []
            for g in subject_data.tolist():
                try:
                    grade_val = float(g)
                    if not pd.isna(grade_val) and 0 <= grade_val <= 5:
                        grades_list.append(grade_val)
                except (ValueError, TypeError):
                    continue
            
            if len(grades_list) > 0:
                fig.add_trace(go.Violin(
                    y=grades_list,
                    name=str(subject),
                    box_visible=True,
                    meanline_visible=True,
                    fillcolor=COLORS['primary'],
                    line_color=COLORS['dark'],
                    opacity=0.7,
                    hovertemplate='Предмет: %{fullData.name}<br>Оценка: %{y:.2f}<extra></extra>'
                ))
        
        if len(fig.data) == 0:
            logger.warning("Нет данных для отображения в violin plot")
            return {"data": [], "layout": {"title": "Violin-plot по предметам"}}
        
        fig.update_layout(
            title={
                'text': 'Распределение оценок по предметам (Violin Plot)',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': COLORS['dark']}
            },
            xaxis_title="Предмет",
            yaxis_title="Оценка",
            template="plotly_white",
            hovermode='x unified',
            showlegend=False,
            yaxis=dict(range=[0, 5.5], dtick=0.5),
            autosize=True,  # Адаптивный размер
            margin=dict(l=70, r=80, t=70, b=100),  # Отступы для повернутых меток
            font=dict(family="Arial, sans-serif", size=11, color=COLORS['dark']),
            plot_bgcolor='white',
            paper_bgcolor='white',
        )
        
        return fig.to_dict()
    except Exception as e:
        logger.error(f"Ошибка создания violin plot по предметам: {e}")
        return {"data": [], "layout": {"title": "Violin-plot по предметам - Ошибка"}}


def create_scatter_trend_plot(df: pd.DataFrame, subject: Optional[str] = None) -> Dict:
    """
    Создаёт scatter plot с регрессионной линией для анализа корреляции.
    
    Args:
        df: DataFrame с данными об оценках
        subject: Предмет (если None, по всем предметам)
        
    Returns:
        Словарь с данными для Plotly
    """
    try:
        if df.empty or 'date' not in df.columns or 'grade' not in df.columns:
            return {"data": [], "layout": {}}
        
        filtered_df = df.copy()
        
        if subject is not None:
            filtered_df = filtered_df[filtered_df['subject'].str.lower() == subject.lower()]
        
        if filtered_df.empty:
            return {"data": [], "layout": {}}
        
        filtered_df['date'] = pd.to_datetime(filtered_df['date'], errors='coerce')
        filtered_df = filtered_df.dropna(subset=['date', 'grade'])
        
        if filtered_df.empty:
            return {"data": [], "layout": {}}
        
        filtered_df = filtered_df.sort_values('date')
        filtered_df['days_since_start'] = (filtered_df['date'] - filtered_df['date'].min()).dt.days
        
        grades_list = []
        days_list = []
        for _, row in filtered_df.iterrows():
            try:
                grade_val = float(row['grade'])
                # Принимаем любые валидные числовые оценки (не только 0-5)
                if not pd.isna(grade_val) and grade_val >= 0:
                    grades_list.append(grade_val)
                    days_list.append(row['days_since_start'])
            except (ValueError, TypeError):
                continue
        
        if len(grades_list) < 2:
            return {"data": [], "layout": {}}
        
        # Определяем диапазон оценок для настройки colorbar
        min_grade = min(grades_list) if grades_list else 0
        max_grade = max(grades_list) if grades_list else 100
        grade_range = max_grade - min_grade
        
        # Определяем, используется ли шкала 0-5 или 0-100
        is_percentage_scale = max_grade > 10
        
        fig = go.Figure()
        
        # Scatter plot
        fig.add_trace(go.Scatter(
            x=days_list,
            y=grades_list,
            mode='markers',
            name='Оценки',
            marker=dict(
                size=8,
                color=grades_list,
                colorscale=HEATMAP_COLORS,
                cmin=min_grade,
                cmax=max_grade,
                showscale=True,
                colorbar=dict(title="Оценка"),
                line=dict(width=1, color='white')
            ),
            hovertemplate='День: %{x}<br>Оценка: %{y:.2f}<extra></extra>'
        ))
        
        # Регрессионная линия (только если есть вариация в днях)
        min_days = min(days_list) if days_list else 0
        max_days = max(days_list) if days_list else 0
        days_range = max_days - min_days
        
        if len(grades_list) >= 2:
            try:
                # Проверяем, что есть вариация в днях для построения регрессии
                if days_range > 0 and len(set(days_list)) > 1:
                    slope, intercept, r_value, p_value, std_err = stats.linregress(days_list, grades_list)
                    x_trend = np.linspace(min_days, max_days, 100)
                    y_trend = slope * x_trend + intercept
                    
                    fig.add_trace(go.Scatter(
                        x=x_trend,
                        y=y_trend,
                        mode='lines',
                        name=f'Тренд (R²={r_value**2:.3f})',
                        line=dict(color=COLORS['danger'], width=3),
                        hovertemplate='День: %{x:.0f}<br>Тренд: %{y:.2f}<extra></extra>'
                    ))
                elif days_range == 0:
                    # Если все даты одинаковые, показываем горизонтальную линию среднего
                    avg_grade = np.mean(grades_list)
                    fig.add_trace(go.Scatter(
                        x=[min_days - 1, max_days + 1] if max_days >= min_days else [0, 1],
                        y=[avg_grade, avg_grade],
                        mode='lines',
                        name=f'Среднее: {avg_grade:.2f}',
                        line=dict(color=COLORS['danger'], width=3, dash='dash'),
                        hovertemplate='Средняя оценка: %{y:.2f}<extra></extra>'
                    ))
            except Exception as e:
                logger.warning(f"Не удалось построить регрессионную линию: {e}")
        
        title = "Корреляция времени и оценок"
        if subject is not None:
            title += f" - {subject}"
        
        # Вычисляем диапазоны с отступами для лучшей визуализации
        
        # Адаптивные отступы для оси Y (оценки)
        if grade_range > 0:
            y_padding = max(grade_range * 0.1, max_grade * 0.05)  # 10% от диапазона или 5% от максимума
        else:
            # Если все оценки одинаковые, добавляем небольшой отступ
            y_padding = max_grade * 0.1 if max_grade > 0 else 1
        
        y_min = max(0, min_grade - y_padding)  # Минимум не ниже 0
        y_max = max_grade + y_padding
        
        # Адаптивные отступы для оси X (дни)
        if days_range > 0:
            x_padding = max(days_range * 0.05, 5)  # 5% от диапазона или минимум 5 дней
        else:
            x_padding = 10  # Если все даты одинаковые
        
        x_min = max(0, min_days - x_padding)
        x_max = max_days + x_padding
        
        # Адаптивное количество меток на основе диапазона
        if grade_range <= 5:
            y_nticks = max(4, min(8, int(grade_range * 2) + 2))
        elif grade_range <= 100:
            y_nticks = max(5, min(10, int(grade_range / 10) + 2))
        else:
            y_nticks = 8
        
        if days_range <= 30:
            x_nticks = max(4, min(8, int(days_range / 5) + 2))
        elif days_range <= 365:
            x_nticks = max(5, min(10, int(days_range / 30) + 3))
        else:
            x_nticks = max(6, min(12, int(days_range / 60) + 4))
        
        # Настройка осей с автоматическим масштабированием
        xaxis_config = dict(
            title=dict(
                text="Дни с начала периода",
                font=dict(size=12, color=COLORS['dark'])
            ),
            autorange=True,  # Автоматическое масштабирование
            range=[x_min, x_max] if days_range > 0 else [0, max(1, x_max)],  # Устанавливаем диапазон только если есть данные
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)',
            gridwidth=1,
            showline=True,
            linecolor='rgba(0,0,0,0.3)',
            linewidth=1,
            tickmode='auto',
            nticks=x_nticks,
            tickfont=dict(size=10, color=COLORS['dark'])
        )
        
        # Определяем диапазон для оси Y
        if grade_range > 0:
            y_range = [y_min, y_max]
        elif is_percentage_scale:
            y_range = [0, 100]
        else:
            y_range = [0, 5.5]
        
        yaxis_config = dict(
            title=dict(
                text="Оценка",
                font=dict(size=12, color=COLORS['dark'])
            ),
            autorange=True,  # Автоматическое масштабирование
            range=y_range,
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)',
            gridwidth=1,
            showline=True,
            linecolor='rgba(0,0,0,0.3)',
            linewidth=1,
            zeroline=False,
            tickmode='auto',
            nticks=y_nticks,
            tickfont=dict(size=10, color=COLORS['dark']),
            rangemode='normal'  # Нормальный режим масштабирования
        )
        
        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': COLORS['dark']}
            },
            template="plotly_white",
            hovermode='closest',
            xaxis=xaxis_config,
            yaxis=yaxis_config,
            autosize=True,  # Адаптивный размер
            margin=dict(l=70, r=100, t=70, b=70),  # Увеличен правый отступ для colorbar
            font=dict(family="Arial, sans-serif", size=11, color=COLORS['dark']),
            plot_bgcolor='white',
            paper_bgcolor='white',
        )
        
        return fig.to_dict()
    except Exception as e:
        logger.error(f"Ошибка создания scatter plot: {e}")
        return {"data": [], "layout": {}}


def create_dashboard_plots(df: pd.DataFrame, student_id: Optional[int] = None, 
                           subject: Optional[str] = None) -> Dict:
    """
    Создаёт набор полностью переработанных графиков для дашборда.
    
    Args:
        df: DataFrame с данными об оценках
        student_id: ID студента (если None, по всем студентам)
        subject: Предмет (если None, по всем предметам)
        
    Returns:
        Словарь с несколькими графиками
    """
    plots = {
        "grade_distribution": create_grade_distribution_plot(df, student_id=student_id, subject=subject),
        "performance_trend": create_performance_trend_plot(df, student_id=student_id, subject=subject),
        "subject_comparison": create_subject_comparison_plot(df, student_id=student_id),
        "student_comparison": create_student_comparison_plot(df, subject=subject),
        "subject_heatmap": create_subject_heatmap(df, student_id=student_id),
        "scatter_trend": create_scatter_trend_plot(df, subject=subject)
    }
    
    return plots
