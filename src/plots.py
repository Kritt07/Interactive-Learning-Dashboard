"""
Модуль для создания интерактивных графиков с использованием Plotly.
"""
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


def create_grade_distribution_plot(df: pd.DataFrame) -> Dict:
    """
    Создаёт график распределения оценок.
    
    Args:
        df: DataFrame с данными об оценках
        
    Returns:
        Словарь с данными для Plotly (data и layout)
    """
    if df.empty or 'grade' not in df.columns:
        return {"data": [], "layout": {}}
    
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=df['grade'],
        nbinsx=20,
        name="Распределение оценок",
        marker_color='#3498db',
        opacity=0.7
    ))
    
    fig.update_layout(
        title="Распределение оценок",
        xaxis_title="Оценка",
        yaxis_title="Количество",
        template="plotly_white",
        hovermode='x unified'
    )
    
    return fig.to_dict()


def create_performance_trend_plot(df: pd.DataFrame, student_id: Optional[int] = None,
                                  subject: Optional[str] = None) -> Dict:
    """
    Создаёт график динамики успеваемости по времени.
    
    Args:
        df: DataFrame с данными об оценках
        student_id: ID студента (если None, по всем студентам)
        subject: Предмет (если None, по всем предметам)
        
    Returns:
        Словарь с данными для Plotly
    """
    if df.empty or 'date' not in df.columns:
        return {"data": [], "layout": {}}
    
    filtered_df = df.copy()
    
    if student_id is not None:
        filtered_df = filtered_df[filtered_df['student_id'] == student_id]
    
    if subject is not None:
        filtered_df = filtered_df[filtered_df['subject'].str.lower() == subject.lower()]
    
    if filtered_df.empty:
        return {"data": [], "layout": {}}
    
    # Преобразуем дату
    filtered_df['date'] = pd.to_datetime(filtered_df['date'])
    filtered_df = filtered_df.sort_values('date')
    
    # Агрегируем по месяцам
    filtered_df['month'] = filtered_df['date'].dt.to_period('M')
    monthly_avg = filtered_df.groupby('month')['grade'].mean().reset_index()
    monthly_avg['month'] = monthly_avg['month'].astype(str)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=monthly_avg['month'],
        y=monthly_avg['grade'],
        mode='lines+markers',
        name='Средняя оценка',
        line=dict(color='#2ecc71', width=2),
        marker=dict(size=8)
    ))
    
    title = "Динамика успеваемости"
    if student_id is not None:
        student_name = filtered_df['student_name'].iloc[0] if 'student_name' in filtered_df.columns else f"Студент {student_id}"
        title += f" - {student_name}"
    if subject is not None:
        title += f" - {subject}"
    
    fig.update_layout(
        title=title,
        xaxis_title="Период",
        yaxis_title="Средняя оценка",
        template="plotly_white",
        hovermode='x unified',
        xaxis=dict(tickangle=-45)
    )
    
    return fig.to_dict()


def create_subject_comparison_plot(df: pd.DataFrame) -> Dict:
    """
    Создаёт график сравнения средних оценок по предметам.
    
    Args:
        df: DataFrame с данными об оценках
        
    Returns:
        Словарь с данными для Plotly
    """
    if df.empty or 'subject' not in df.columns:
        return {"data": [], "layout": {}}
    
    subject_avg = df.groupby('subject')['grade'].mean().sort_values(ascending=False).reset_index()
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=subject_avg['subject'],
        y=subject_avg['grade'],
        name="Средняя оценка",
        marker_color='#9b59b6',
        text=subject_avg['grade'].round(2),
        textposition='auto'
    ))
    
    fig.update_layout(
        title="Средние оценки по предметам",
        xaxis_title="Предмет",
        yaxis_title="Средняя оценка",
        template="plotly_white",
        hovermode='x unified'
    )
    
    return fig.to_dict()


def create_student_comparison_plot(df: pd.DataFrame, subject: Optional[str] = None,
                                   top_n: int = 10) -> Dict:
    """
    Создаёт график сравнения студентов по средним оценкам.
    
    Args:
        df: DataFrame с данными об оценках
        subject: Предмет (если None, по всем предметам)
        top_n: Количество студентов для отображения
        
    Returns:
        Словарь с данными для Plotly
    """
    if df.empty:
        return {"data": [], "layout": {}}
    
    filtered_df = df.copy()
    
    if subject is not None:
        filtered_df = filtered_df[filtered_df['subject'].str.lower() == subject.lower()]
    
    if filtered_df.empty:
        return {"data": [], "layout": {}}
    
    # Вычисляем средний балл по каждому студенту
    student_avg = filtered_df.groupby(['student_id', 'student_name'])['grade'].mean().reset_index()
    student_avg = student_avg.sort_values('grade', ascending=False).head(top_n)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=student_avg['student_name'],
        y=student_avg['grade'],
        name="Средняя оценка",
        marker_color='#e74c3c',
        text=student_avg['grade'].round(2),
        textposition='auto'
    ))
    
    title = f"Топ {top_n} студентов по успеваемости"
    if subject is not None:
        title += f" - {subject}"
    
    fig.update_layout(
        title=title,
        xaxis_title="Студент",
        yaxis_title="Средняя оценка",
        template="plotly_white",
        hovermode='x unified',
        xaxis=dict(tickangle=-45)
    )
    
    return fig.to_dict()


def create_subject_heatmap(df: pd.DataFrame, student_id: Optional[int] = None) -> Dict:
    """
    Создаёт тепловую карту успеваемости по предметам и времени.
    
    Args:
        df: DataFrame с данными об оценках
        student_id: ID студента (если None, по всем студентам)
        
    Returns:
        Словарь с данными для Plotly
    """
    if df.empty or 'date' not in df.columns or 'subject' not in df.columns:
        return {"data": [], "layout": {}}
    
    filtered_df = df.copy()
    
    if student_id is not None:
        filtered_df = filtered_df[filtered_df['student_id'] == student_id]
    
    if filtered_df.empty:
        return {"data": [], "layout": {}}
    
    # Преобразуем дату
    filtered_df['date'] = pd.to_datetime(filtered_df['date'])
    filtered_df['month'] = filtered_df['date'].dt.to_period('M').astype(str)
    
    # Создаём сводную таблицу
    pivot_df = filtered_df.pivot_table(
        values='grade',
        index='subject',
        columns='month',
        aggfunc='mean'
    )
    
    # Убеждаемся, что все колонки - строки
    pivot_df.columns = [str(col) for col in pivot_df.columns]
    pivot_df.index = pivot_df.index.astype(str)
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot_df.values,
        x=pivot_df.columns,
        y=pivot_df.index,
        colorscale='RdYlGn',
        text=pivot_df.values.round(2),
        texttemplate='%{text}',
        textfont={"size": 10},
        colorbar=dict(title="Оценка")
    ))
    
    title = "Тепловая карта успеваемости"
    if student_id is not None:
        student_name = filtered_df['student_name'].iloc[0] if 'student_name' in filtered_df.columns else f"Студент {student_id}"
        title += f" - {student_name}"
    
    fig.update_layout(
        title=title,
        xaxis_title="Период",
        yaxis_title="Предмет",
        template="plotly_white"
    )
    
    return fig.to_dict()


def create_box_plot_by_subject(df: pd.DataFrame) -> Dict:
    """
    Создаёт box plot оценок по предметам.
    
    Args:
        df: DataFrame с данными об оценках
        
    Returns:
        Словарь с данными для Plotly
    """
    if df.empty or 'subject' not in df.columns:
        return {"data": [], "layout": {}}
    
    fig = go.Figure()
    
    subjects = df['subject'].unique()
    
    for subject in subjects:
        subject_data = df[df['subject'] == subject]['grade']
        fig.add_trace(go.Box(
            y=subject_data,
            name=subject,
            boxmean='sd'
        ))
    
    fig.update_layout(
        title="Распределение оценок по предметам",
        xaxis_title="Предмет",
        yaxis_title="Оценка",
        template="plotly_white",
        hovermode='x unified'
    )
    
    return fig.to_dict()


def create_dashboard_plots(df: pd.DataFrame) -> Dict:
    """
    Создаёт набор графиков для дашборда.
    
    Args:
        df: DataFrame с данными об оценках
        
    Returns:
        Словарь с несколькими графиками
    """
    plots = {
        "grade_distribution": create_grade_distribution_plot(df),
        "performance_trend": create_performance_trend_plot(df),
        "subject_comparison": create_subject_comparison_plot(df),
        "student_comparison": create_student_comparison_plot(df),
        "subject_heatmap": create_subject_heatmap(df),
        "box_plot": create_box_plot_by_subject(df)
    }
    
    return plots

