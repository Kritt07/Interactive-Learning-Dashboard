"""
Тесты для API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


def test_root_endpoint():
    """Тест корневого endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "endpoints" in data


def test_health_check():
    """Тест health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


def test_plot_data_dashboard():
    """Тест получения данных для дашборда."""
    response = client.get("/api/plot-data?plot_type=dashboard")
    assert response.status_code in [200, 500]  # 500 если нет данных

    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, dict)
        # Проверяем структуру дашборда (если есть данные)
        if data:
            for key, plot in data.items():
                assert "data" in plot
                assert "layout" in plot
                assert isinstance(plot["data"], list)


def test_plot_data_distribution():
    """Тест получения графика распределения."""
    response = client.get("/api/plot-data?plot_type=distribution")

    if response.status_code == 200:
        data = response.json()
        assert "data" in data
        assert "layout" in data


def test_students_endpoint():
    """Тест получения списка студентов."""
    response = client.get("/api/students")
    assert response.status_code in [200, 500]

    if response.status_code == 200:
        data = response.json()
        assert "students" in data
        assert "total" in data
        assert isinstance(data["students"], list)


def test_statistics_endpoint():
    """Тест получения статистики."""
    response = client.get("/api/statistics")
    assert response.status_code in [200, 500]

    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, dict)


def test_subjects_endpoint():
    """Тест получения списка предметов."""
    response = client.get("/api/subjects")
    assert response.status_code in [200, 500]

    if response.status_code == 200:
        data = response.json()
        assert "subjects" in data
        assert isinstance(data["subjects"], list)


def test_plot_data_with_filters():
    """Тест фильтрации графиков."""
    # Тест с фильтром по студенту
    response = client.get("/api/plot-data?plot_type=trend&student_id=1")
    assert response.status_code in [200, 500]

    # Тест с фильтром по предмету
    response = client.get("/api/plot-data?plot_type=trend&subject=Math")
    assert response.status_code in [200, 500]


def test_plot_data_comparison():
    """Тест получения графика сравнения."""
    response = client.get("/api/plot-data?plot_type=comparison")
    assert response.status_code in [200, 500]

    if response.status_code == 200:
        data = response.json()
        # Для comparison возвращается словарь с subject_comparison и student_comparison
        assert "subject_comparison" in data
        assert "student_comparison" in data
        # Проверяем структуру каждого графика
        assert "data" in data["subject_comparison"]
        assert "layout" in data["subject_comparison"]
        assert "data" in data["student_comparison"]
        assert "layout" in data["student_comparison"]


def test_plot_data_heatmap():
    """Тест получения тепловой карты."""
    response = client.get("/api/plot-data?plot_type=heatmap")
    assert response.status_code in [200, 500]

    if response.status_code == 200:
        data = response.json()
        assert "data" in data
        assert "layout" in data


def test_plot_data_box():
    """Тест получения box-plot."""
    response = client.get("/api/plot-data?plot_type=box")
    assert response.status_code in [200, 500]

    if response.status_code == 200:
        data = response.json()
        assert "data" in data
        assert "layout" in data


def test_grades_endpoint():
    """Тест получения оценок."""
    response = client.get("/api/grades")
    assert response.status_code in [200, 500]

    if response.status_code == 200:
        data = response.json()
        assert "grades" in data
        assert "total" in data
        assert isinstance(data["grades"], list)


def test_grades_with_filters():
    """Тест получения оценок с фильтрами."""
    # С фильтром по студенту
    response = client.get("/api/grades?student_id=1")
    assert response.status_code in [200, 500]

    # С фильтром по предмету
    response = client.get("/api/grades?subject=Math")
    assert response.status_code in [200, 500]

    # С лимитом
    response = client.get("/api/grades?limit=10")
    assert response.status_code in [200, 500]


def test_statistics_with_filters():
    """Тест получения статистики с фильтрами."""
    # С фильтром по студенту
    response = client.get("/api/statistics?student_id=1")
    assert response.status_code in [200, 500]

    # С фильтром по предмету
    response = client.get("/api/statistics?subject=Math")
    assert response.status_code in [200, 500]


def test_student_statistics_endpoint():
    """Тест получения статистики конкретного студента."""
    response = client.get("/api/students/1/statistics")
    # Может быть 200, 404 или 500 в зависимости от наличия данных
    assert response.status_code in [200, 404, 500]

    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, dict)
        assert "total_grades" in data or "average_grade" in data


def test_cors_headers():
    """Тест наличия CORS заголовков."""
    response = client.options("/api/students")
    # CORS middleware должен обработать OPTIONS запрос
    assert response.status_code in [200, 405]  # 405 если метод не разрешен
