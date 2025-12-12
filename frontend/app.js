// Конфигурация API
const API_BASE_URL = 'http://localhost:8000';

// Глобальное состояние
let currentFilters = {
    student_id: null,
    subject: null,
    plot_type: 'dashboard'
};

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', async () => {
    await loadInitialData();
    await loadPlotData();
    await loadStatistics();
    setupEventListeners();
});

// Настройка обработчиков событий
function setupEventListeners() {
    document.getElementById('studentFilter').addEventListener('change', handleFilterChange);
    document.getElementById('subjectFilter').addEventListener('change', handleFilterChange);
    document.getElementById('plotTypeFilter').addEventListener('change', handleFilterChange);
    document.getElementById('refreshBtn').addEventListener('click', handleRefresh);
}

// Обработка изменения фильтров
async function handleFilterChange() {
    const studentId = document.getElementById('studentFilter').value;
    const subject = document.getElementById('subjectFilter').value;
    const plotType = document.getElementById('plotTypeFilter').value;

    currentFilters.student_id = studentId || null;
    currentFilters.subject = subject || null;
    currentFilters.plot_type = plotType;

    await loadPlotData();
    await loadStatistics();
}

// Обновление данных
async function handleRefresh() {
    await loadInitialData();
    await loadPlotData();
    await loadStatistics();
}

// Загрузка начальных данных (студенты, предметы)
async function loadInitialData() {
    try {
        showLoading(true);

        // Загрузка студентов
        const studentsResponse = await fetch(`${API_BASE_URL}/api/students`);
        if (!studentsResponse.ok) throw new Error('Ошибка загрузки студентов');
        const studentsData = await studentsResponse.json();

        // Загрузка предметов
        const subjectsResponse = await fetch(`${API_BASE_URL}/api/subjects`);
        if (!subjectsResponse.ok) throw new Error('Ошибка загрузки предметов');
        const subjectsData = await subjectsResponse.json();

        // Заполнение фильтров
        populateStudentFilter(studentsData.students || []);
        populateSubjectFilter(subjectsData.subjects || []);

        showLoading(false);
    } catch (error) {
        showLoading(false);
        showError(`Ошибка загрузки данных: ${error.message}`);
        console.error('Ошибка загрузки начальных данных:', error);
    }
}

// Заполнение фильтра студентов
function populateStudentFilter(students) {
    const select = document.getElementById('studentFilter');
    // Оставляем опцию "Все студенты"
    while (select.children.length > 1) {
        select.removeChild(select.lastChild);
    }

    students.forEach(student => {
        const option = document.createElement('option');
        option.value = student.student_id;
        option.textContent = `${student.student_name} (ID: ${student.student_id})`;
        select.appendChild(option);
    });
}

// Заполнение фильтра предметов
function populateSubjectFilter(subjects) {
    const select = document.getElementById('subjectFilter');
    // Оставляем опцию "Все предметы"
    while (select.children.length > 1) {
        select.removeChild(select.lastChild);
    }

    subjects.forEach(subject => {
        const option = document.createElement('option');
        option.value = subject.subject;
        option.textContent = subject.subject;
        select.appendChild(option);
    });
}

// Загрузка данных для графиков
async function loadPlotData() {
    try {
        showLoading(true);
        hideError();

        const params = new URLSearchParams();
        if (currentFilters.plot_type) {
            params.append('plot_type', currentFilters.plot_type);
        }
        if (currentFilters.student_id) {
            params.append('student_id', currentFilters.student_id);
        }
        if (currentFilters.subject) {
            params.append('subject', currentFilters.subject);
        }

        const url = `${API_BASE_URL}/api/plot-data?${params.toString()}`;
        console.log('Запрос графиков:', url);
        
        const response = await fetch(url);
        
        if (!response.ok) {
            // Попытка получить детали ошибки от сервера
            let errorMessage = `Ошибка ${response.status}: ${response.statusText}`;
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorMessage;
            } catch (e) {
                // Если не удалось распарсить JSON с ошибкой
            }
            throw new Error(errorMessage);
        }
        
        const plotData = await response.json();
        console.log('Получены данные графиков:', plotData);

        // Рендеринг графиков
        renderPlots(plotData);

        showLoading(false);
    } catch (error) {
        showLoading(false);
        const errorMsg = error.message || 'Неизвестная ошибка';
        showError(`Ошибка загрузки графиков: ${errorMsg}`);
        console.error('Ошибка загрузки графиков:', error);
        
        // Показать информацию в консоли для отладки
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            console.error('Возможные причины:');
            console.error('1. Бэкенд не запущен (запустите: uvicorn src.app:app --reload)');
            console.error('2. Неправильный URL API:', API_BASE_URL);
            console.error('3. Проблемы с CORS (если открываете через file://)');
        }
    }
}

// Рендеринг графиков
function renderPlots(plotData) {
    const container = document.getElementById('plotsContainer');
    container.innerHTML = '';

    // Проверка на пустые или некорректные данные
    if (!plotData) {
        container.innerHTML = '<p class="no-data">Нет данных для отображения</p>';
        return;
    }

    // Если plot_type = 'dashboard', то plotData содержит словарь с несколькими графиками
    if (currentFilters.plot_type === 'dashboard' && typeof plotData === 'object' && !Array.isArray(plotData) && !plotData.data) {
        // Дашборд содержит несколько графиков в виде объекта
        const plotNames = {
            'grade_distribution': 'Распределение оценок',
            'performance_trend': 'Динамика успеваемости',
            'subject_comparison': 'Сравнение по предметам',
            'student_comparison': 'Сравнение студентов',
            'subject_heatmap': 'Тепловая карта по предметам',
            'box_plot': 'Box-plot по предметам'
        };

        let plotIndex = 0;
        for (const [key, plot] of Object.entries(plotData)) {
            // Проверяем, что график валидный и содержит данные
            if (plot && plot.data && plot.layout && Array.isArray(plot.data) && plot.data.length > 0) {
                try {
                    const plotDiv = document.createElement('div');
                    plotDiv.className = 'plot-item';
                    
                    // Добавляем заголовок
                    const title = document.createElement('h3');
                    title.className = 'plot-title';
                    title.textContent = plotNames[key] || key;
                    plotDiv.appendChild(title);
                    
                    // Добавляем контейнер для графика с уникальным ID
                    const plotId = `plot-${plotIndex}`;
                    const graphContainer = document.createElement('div');
                    graphContainer.id = plotId;
                    plotDiv.appendChild(graphContainer);
                    
                    container.appendChild(plotDiv);

                    Plotly.newPlot(plotId, plot.data, plot.layout, {
                        responsive: true,
                        displayModeBar: true,
                        modeBarButtonsToRemove: ['pan2d', 'lasso2d']
                    });

                    plotIndex++;
                } catch (plotError) {
                    console.error(`Ошибка рендеринга графика ${key}:`, plotError);
                }
            } else {
                console.warn(`График ${key} пропущен:`, plot);
            }
        }

        if (plotIndex === 0) {
            container.innerHTML = '<p class="no-data">Нет данных для отображения. Проверьте, что данные загружены в систему.</p>';
        }
    } else if (plotData.data && plotData.layout && Array.isArray(plotData.data) && plotData.data.length > 0) {
        // Одиночный график
        try {
            const plotDiv = document.createElement('div');
            plotDiv.className = 'plot-item';
            const plotId = 'plot-main';
            plotDiv.id = plotId;
            container.appendChild(plotDiv);

            Plotly.newPlot(plotId, plotData.data, plotData.layout, {
                responsive: true,
                displayModeBar: true,
                modeBarButtonsToRemove: ['pan2d', 'lasso2d']
            });
        } catch (plotError) {
            console.error('Ошибка рендеринга графика:', plotError);
            container.innerHTML = '<p class="no-data">Ошибка при отображении графика</p>';
        }
    } else {
        console.warn('Некорректные данные графика:', plotData);
        container.innerHTML = '<p class="no-data">Нет данных для отображения</p>';
    }
}

// Загрузка статистики
async function loadStatistics() {
    try {
        const params = new URLSearchParams();
        if (currentFilters.student_id) {
            params.append('student_id', currentFilters.student_id);
        }
        if (currentFilters.subject) {
            params.append('subject', currentFilters.subject);
        }

        const response = await fetch(`${API_BASE_URL}/api/statistics?${params.toString()}`);
        if (!response.ok) throw new Error('Ошибка загрузки статистики');
        
        const stats = await response.json();
        renderStatistics(stats);
    } catch (error) {
        console.error('Ошибка загрузки статистики:', error);
    }
}

// Рендеринг статистики
function renderStatistics(stats) {
    const container = document.getElementById('statsGrid');
    container.innerHTML = '';

    const statsItems = [
        {
            title: 'Средняя оценка',
            value: stats.average_grade ? stats.average_grade.toFixed(2) : 'N/A',
            icon: '📈'
        },
        {
            title: 'Всего оценок',
            value: stats.total_grades || 0,
            icon: '📝'
        },
        {
            title: 'Максимальная оценка',
            value: stats.max_grade || 'N/A',
            icon: '⭐'
        },
        {
            title: 'Минимальная оценка',
            value: stats.min_grade || 'N/A',
            icon: '📊'
        }
    ];

    statsItems.forEach(item => {
        const statCard = document.createElement('div');
        statCard.className = 'stat-card';
        statCard.innerHTML = `
            <div class="stat-icon">${item.icon}</div>
            <div class="stat-content">
                <div class="stat-value">${item.value}</div>
                <div class="stat-title">${item.title}</div>
            </div>
        `;
        container.appendChild(statCard);
    });
}

// Показать/скрыть индикатор загрузки
function showLoading(show) {
    const loader = document.getElementById('loadingIndicator');
    if (show) {
        loader.classList.remove('hidden');
    } else {
        loader.classList.add('hidden');
    }
}

// Показать ошибку
function showError(message) {
    const errorDiv = document.getElementById('errorMessage');
    errorDiv.textContent = message;
    errorDiv.classList.remove('hidden');
    
    // Автоматически скрыть через 5 секунд
    setTimeout(() => {
        hideError();
    }, 5000);
}

// Скрыть ошибку
function hideError() {
    const errorDiv = document.getElementById('errorMessage');
    errorDiv.classList.add('hidden');
}

