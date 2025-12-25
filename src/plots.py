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

# Градиентные цвета для тепловых карт
HEATMAP_COLORS = [
    [0, '#1e40af'],      # Темно-синий
    [0.25, '#3b82f6'],   # Синий
    [0.5, '#60a5fa'],    # Светло-синий
    [0.75, '#93c5fd'],   # Очень светло-синий
    [1, '#dbeafe']       # Почти белый
]


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
                if not pd.isna(grade_val) and 0 <= grade_val <= 5:
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
        
        # Создаем компактный график
        fig = go.Figure()
        
        # Гистограмма
        fig.add_trace(
            go.Histogram(
                x=grades_list,
                nbinsx=20,
                name="Распределение",
                marker_color=COLORS['primary'],
                marker_line_color='white',
                marker_line_width=0.5,
                opacity=0.8,
                histnorm='probability density',
                hovertemplate='Оценка: %{x:.2f}<br>Плотность: %{y:.3f}<extra></extra>',
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
        
        # Вертикальные линии для среднего и медианы (без аннотаций)
        fig.add_vline(
            x=mean_grade,
            line_dash="dash",
            line_color=COLORS['success'],
            line_width=1.5,
            annotation_text="",
            annotation_position="top",
            row=None,
            col=None
        )
        
        fig.add_vline(
            x=median_grade,
            line_dash="dot",
            line_color=COLORS['warning'],
            line_width=1.5,
            annotation_text="",
            annotation_position="top",
            row=None,
            col=None
        )
        
        # Добавляем невидимые точки для легенды со статистикой
        fig.add_trace(
            go.Scatter(
                x=[mean_grade],
                y=[0],
                mode='lines',
                name=f'Среднее: {mean_grade:.2f}',
                line=dict(color=COLORS['success'], width=2, dash='dash'),
                showlegend=True,
                hovertemplate=f'Среднее: {mean_grade:.2f}<extra></extra>'
            )
        )
        
        fig.add_trace(
            go.Scatter(
                x=[median_grade],
                y=[0],
                mode='lines',
                name=f'Медиана: {median_grade:.2f}',
                line=dict(color=COLORS['warning'], width=2, dash='dot'),
                showlegend=True,
                hovertemplate=f'Медиана: {median_grade:.2f}<extra></extra>'
            )
        )
        
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
                range=[max(0, min_grade - 0.2), min(5.5, max_grade + 0.2)],
                dtick=1,  # Упрощаем деления
                showgrid=True,
                gridcolor=COLORS['light'],
                gridwidth=0.5
            ),
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
        min_grade = monthly_stats['mean'].min()
        max_grade = monthly_stats['mean'].max()
        grade_range = max_grade - min_grade
        y_range_padding = grade_range * 0.2 if grade_range > 0 else 0.5
        
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
            yaxis=dict(
                title=dict(
                    text="Оценка",
                    font=dict(size=12, color=COLORS['dark'])
                ),
                range=[max(0, min_grade - y_range_padding), min(5, max_grade + y_range_padding)],
                dtick=0.5,
                autorange=False,
                showgrid=True,
                gridcolor='rgba(0,0,0,0.1)',
                gridwidth=1,
                showline=True,
                linecolor='rgba(0,0,0,0.3)',
                linewidth=1,
                zeroline=False,
                tickmode='linear',
                tick0=0,
                tickfont=dict(size=10, color=COLORS['dark']),
                side='left'
            ),
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


def create_subject_comparison_plot(df: pd.DataFrame) -> Dict:
    """
    Создаёт современный график сравнения средних оценок по предметам.
    
    Args:
        df: DataFrame с данными об оценках
        
    Returns:
        Словарь с данными для Plotly
    """
    try:
        if df.empty or 'subject' not in df.columns:
            return {"data": [], "layout": {}}
        
        subject_stats = df.groupby('subject')['grade'].agg([
            'mean', 'std', 'count', 'median'
        ]).reset_index()
        
        subject_stats = subject_stats.sort_values('mean', ascending=False)
        subject_stats['std'] = subject_stats['std'].fillna(0)
        
        fig = go.Figure()
        
        # Столбчатая диаграмма с ошибками
        colors = px.colors.qualitative.Set3[:len(subject_stats)]
        
        fig.add_trace(go.Bar(
            x=subject_stats['subject'],
            y=subject_stats['mean'],
            name="Средняя оценка",
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
            text=subject_stats['mean'].round(2),
            textposition='auto',  # Автоматическое позиционирование
            textfont=dict(size=10, color=COLORS['dark']),
            hovertemplate='Предмет: %{x}<br>Средняя оценка: %{y:.2f}<br>Ст. отклонение: %{customdata[0]:.2f}<br>Количество: %{customdata[1]}<extra></extra>',
            customdata=subject_stats[['std', 'count']].values
        ))
        
        # Горизонтальная линия для общего среднего
        overall_mean = df['grade'].mean()
        fig.add_hline(
            y=overall_mean,
            line_dash="dash",
            line_color=COLORS['danger'],
            annotation_text=f"Общее среднее: {overall_mean:.2f}",
            annotation_position="right"
        )
        
        fig.update_layout(
            title={
                'text': 'Сравнение средних оценок по предметам',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': COLORS['dark']}
            },
            xaxis_title="Предмет",
            yaxis_title="Средняя оценка",
            template="plotly_white",
            hovermode='x unified',
            xaxis=dict(tickangle=-45),
            yaxis=dict(range=[0, 5.5], dtick=0.5),
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
        
        student_avg = student_avg.sort_values('mean', ascending=False).head(top_n)
        student_avg['std'] = student_avg['std'].fillna(0)
        
        fig = go.Figure()
        
        # Горизонтальная столбчатая диаграмма
        fig.add_trace(go.Bar(
            y=student_avg['student_name'],
            x=student_avg['mean'],
            orientation='h',
            name="Средняя оценка",
            marker=dict(
                color=student_avg['mean'],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Оценка")
            ),
            marker_line_color='white',
            marker_line_width=2,
            text=student_avg['mean'].round(2),
            textposition='auto',  # Автоматическое позиционирование
            textfont=dict(size=10, color=COLORS['dark']),
            hovertemplate='Студент: %{y}<br>Средняя оценка: %{x:.2f}<br>Количество: %{customdata[0]}<br>Ст. отклонение: %{customdata[1]:.2f}<extra></extra>',
            customdata=student_avg[['count', 'std']].values
        ))
        
        title = f"Топ {top_n} студентов по успеваемости"
        if subject is not None:
            title += f" - {subject}"
        
        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': COLORS['dark']}
            },
            xaxis_title="Средняя оценка",
            yaxis_title="Студент",
            template="plotly_white",
            hovermode='y unified',
            xaxis=dict(range=[0, 5.5], dtick=0.5),
            autosize=True,  # Адаптивный размер
            margin=dict(l=100, r=100, t=70, b=70),  # Увеличены отступы для длинных имен
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
            
            fig = go.Figure(data=go.Heatmap(
                z=z_values,
                x=pivot_df.columns.tolist(),
                y=pivot_df.index.tolist(),
                colorscale=HEATMAP_COLORS,
                text=text_values,
                texttemplate='%{text}',
                textfont={"size": 11, "color": "white"},
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
                if not pd.isna(grade_val) and 0 <= grade_val <= 5:
                    grades_list.append(grade_val)
                    days_list.append(row['days_since_start'])
            except (ValueError, TypeError):
                continue
        
        if len(grades_list) < 3:
            return {"data": [], "layout": {}}
        
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
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Оценка"),
                line=dict(width=1, color='white')
            ),
            hovertemplate='День: %{x}<br>Оценка: %{y:.2f}<extra></extra>'
        ))
        
        # Регрессионная линия
        try:
            slope, intercept, r_value, p_value, std_err = stats.linregress(days_list, grades_list)
            x_trend = np.linspace(min(days_list), max(days_list), 100)
            y_trend = slope * x_trend + intercept
            
            fig.add_trace(go.Scatter(
                x=x_trend,
                y=y_trend,
                mode='lines',
                name=f'Тренд (R²={r_value**2:.3f})',
                line=dict(color=COLORS['danger'], width=3),
                hovertemplate='День: %{x:.0f}<br>Тренд: %{y:.2f}<extra></extra>'
            ))
        except Exception as e:
            logger.warning(f"Не удалось построить регрессионную линию: {e}")
        
        title = "Корреляция времени и оценок"
        if subject is not None:
            title += f" - {subject}"
        
        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': COLORS['dark']}
            },
            xaxis_title="Дни с начала периода",
            yaxis_title="Оценка",
            template="plotly_white",
            hovermode='closest',
            yaxis=dict(range=[0, 5.5], dtick=0.5),
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
        "subject_comparison": create_subject_comparison_plot(df),
        "student_comparison": create_student_comparison_plot(df, subject=subject),
        "subject_heatmap": create_subject_heatmap(df, student_id=student_id),
        "scatter_trend": create_scatter_trend_plot(df, subject=subject)
    }
    
    return plots
