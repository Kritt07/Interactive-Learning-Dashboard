"""
FastAPI application for Interactive Student Performance Dashboard.
"""
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

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


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Interactive Student Performance Dashboard API",
        "version": "1.0.0",
        "endpoints": {
            "plot_data": "/api/plot-data",
            "students": "/api/students",
            "grades": "/api/grades"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/api/plot-data")
async def get_plot_data():
    """Выдаёт данные для графиков."""
    # TODO: Implement plot data generation using plots.py
    return {
        "data": [],
        "layout": {}
    }


@app.get("/api/students")
async def get_students():
    """Список студентов."""
    # TODO: Implement data loading from data_loader
    return {
        "students": []
    }


@app.get("/api/grades")
async def get_grades(
    student_id: Optional[int] = Query(None, description="Filter by student ID"),
    subject: Optional[str] = Query(None, description="Filter by subject")
):
    """Данные оценок."""
    # TODO: Implement grades data loading
    return {
        "grades": [],
        "student_id": student_id,
        "subject": subject
    }
