// Конфигурация API
const API_BASE_URL = 'http://localhost:8000';

// Глобальное состояние
let currentFilters = {
    student_id: null,
    subject: null,
    start_date: null,
    end_date: null,
    plot_type: 'dashboard'
};

// Хранилище информации о графиках для экспорта
let availablePlots = [];

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', async () => {
    setupEventListeners();
    await checkDataStatus();
});

// Настройка обработчиков событий
function setupEventListeners() {
    // Обработчики для основного контента (могут быть недоступны, если данных нет)
    const studentFilter = document.getElementById('studentFilter');
    const subjectFilter = document.getElementById('subjectFilter');
    const startDateFilter = document.getElementById('startDateFilter');
    const endDateFilter = document.getElementById('endDateFilter');
    const refreshBtn = document.getElementById('refreshBtn');
    const exportCsvBtn = document.getElementById('exportCsvBtn');
    const exportPdfBtn = document.getElementById('exportPdfBtn');
    
    if (studentFilter) studentFilter.addEventListener('change', handleFilterChange);
    if (subjectFilter) subjectFilter.addEventListener('change', handleFilterChange);
    if (startDateFilter) startDateFilter.addEventListener('change', handleFilterChange);
    if (endDateFilter) endDateFilter.addEventListener('change', handleFilterChange);
    if (refreshBtn) refreshBtn.addEventListener('click', handleRefresh);
    if (exportCsvBtn) exportCsvBtn.addEventListener('click', handleExportCsv);
    if (exportPdfBtn) exportPdfBtn.addEventListener('click', handleExportPdf);
    
    // Обработчики для приветственного блока
    const welcomeFileInput = document.getElementById('welcomeFileInput');
    const startImportBtn = document.getElementById('startImportBtn');
    const gradingSystemRadios = document.querySelectorAll('input[name="gradingSystem"]');
    
    if (welcomeFileInput) {
        welcomeFileInput.addEventListener('change', handleWelcomeFileSelect);
        
        // Обработчик для кнопки выбора файла
        const welcomeFileButton = welcomeFileInput.parentElement?.querySelector('.file-input-button');
        if (welcomeFileButton) {
            welcomeFileButton.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                welcomeFileInput.click();
            });
        }
    }
    
    if (startImportBtn) {
        startImportBtn.addEventListener('click', handleWelcomeImport);
    }
    
    if (gradingSystemRadios.length > 0) {
        gradingSystemRadios.forEach(radio => {
            radio.addEventListener('change', handleGradingSystemChange);
        });
    }
    
    // Обработчики для полей кастомной системы оценивания
    const minGradeInput = document.getElementById('minGrade');
    const maxGradeInput = document.getElementById('maxGrade');
    
    if (minGradeInput) {
        minGradeInput.addEventListener('input', handleGradingSystemChange);
    }
    if (maxGradeInput) {
        maxGradeInput.addEventListener('input', handleGradingSystemChange);
    }
    
    // Обработчики для модального окна импорта (могут быть недоступны)
    const importBtn = document.getElementById('importBtn');
    const closeImportModalBtn = document.getElementById('closeImportModalBtn');
    const cancelImportBtn = document.getElementById('cancelImportBtn');
    const confirmImportBtn = document.getElementById('confirmImportBtn');
    const fileInput = document.getElementById('fileInput');
    
    if (importBtn) importBtn.addEventListener('click', openImportModal);
    if (closeImportModalBtn) closeImportModalBtn.addEventListener('click', closeImportModal);
    if (cancelImportBtn) cancelImportBtn.addEventListener('click', closeImportModal);
    if (confirmImportBtn) confirmImportBtn.addEventListener('click', handleImport);
    if (fileInput) fileInput.addEventListener('change', handleFileSelect);
    
    // Обработчик клика на кнопку "Выбрать файл" в модальном окне
    const fileInputButton = document.querySelector('#fileInput')?.parentElement?.querySelector('.file-input-button');
    if (fileInputButton && fileInput) {
        fileInputButton.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            fileInput.click();
        });
    }
    
    // Обработчики для модального окна экспорта (могут быть недоступны)
    const exportBtn = document.getElementById('exportBtn');
    const closeModalBtn = document.getElementById('closeModalBtn');
    const cancelExportBtn = document.getElementById('cancelExportBtn');
    const confirmExportBtn = document.getElementById('confirmExportBtn');
    const selectAllPlots = document.getElementById('selectAllPlots');
    const selectAllFormats = document.getElementById('selectAllFormats');
    
    if (exportBtn) exportBtn.addEventListener('click', openExportModal);
    if (closeModalBtn) closeModalBtn.addEventListener('click', closeExportModal);
    if (cancelExportBtn) cancelExportBtn.addEventListener('click', closeExportModal);
    if (confirmExportBtn) confirmExportBtn.addEventListener('click', handleExport);
    if (selectAllPlots) selectAllPlots.addEventListener('change', toggleSelectAllPlots);
    if (selectAllFormats) selectAllFormats.addEventListener('change', toggleSelectAllFormats);
    
    // Закрытие модальных окон при клике вне их
    const importModal = document.getElementById('importModal');
    const exportModal = document.getElementById('exportModal');
    
    if (importModal) {
        importModal.addEventListener('click', (e) => {
            if (e.target.id === 'importModal') {
                closeImportModal();
            }
        });
    }
    
    if (exportModal) {
        exportModal.addEventListener('click', (e) => {
            if (e.target.id === 'exportModal') {
                closeExportModal();
            }
        });
    }
    
    // Обработчик изменения размера окна для адаптации графиков
    let resizeTimeout;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            // Находим все контейнеры графиков и перерисовываем их
            document.querySelectorAll('.plot-item [id^="plot-"]').forEach(plotDiv => {
                if (plotDiv.id && typeof Plotly !== 'undefined') {
                    Plotly.Plots.resize(plotDiv.id);
                }
            });
            // Также проверяем основной график
            const mainPlot = document.getElementById('plot-main');
            if (mainPlot && typeof Plotly !== 'undefined') {
                Plotly.Plots.resize('plot-main');
            }
        }, 150); // Небольшая задержка для оптимизации
    });
}

// Проверка статуса данных
async function checkDataStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/data-status`);
        if (!response.ok) throw new Error('Ошибка проверки статуса данных');
        
        const status = await response.json();
        
        if (status.has_data && status.total_records > 0) {
            // Данные есть - показываем основной контент
            showMainContent();
            await loadInitialData();
            await loadPlotData();
            await loadStatistics();
        } else {
            // Данных нет - показываем приветственный блок
            showWelcomeBlock();
            
            // Если есть сохраненная система оценивания, загружаем её
            if (status.grading_system) {
                const systemType = status.grading_system.system_type;
                const radio = document.querySelector(`input[name="gradingSystem"][value="${systemType}"]`);
                if (radio) {
                    radio.checked = true;
                    handleGradingSystemChange();
                    
                    if (systemType === 'custom') {
                        const minGradeInput = document.getElementById('minGrade');
                        const maxGradeInput = document.getElementById('maxGrade');
                        if (minGradeInput && status.grading_system.min_grade) {
                            minGradeInput.value = status.grading_system.min_grade;
                        }
                        if (maxGradeInput && status.grading_system.max_grade) {
                            maxGradeInput.value = status.grading_system.max_grade;
                        }
                    }
                }
            }
        }
    } catch (error) {
        console.error('Ошибка проверки статуса данных:', error);
        // В случае ошибки показываем приветственный блок
        showWelcomeBlock();
    }
}

// Показать приветственный блок
function showWelcomeBlock() {
    const welcomeBlock = document.getElementById('welcomeBlock');
    const mainContent = document.getElementById('mainContent');
    
    if (welcomeBlock) welcomeBlock.classList.remove('hidden');
    if (mainContent) mainContent.classList.add('hidden');
}

// Показать основной контент
function showMainContent() {
    const welcomeBlock = document.getElementById('welcomeBlock');
    const mainContent = document.getElementById('mainContent');
    
    if (welcomeBlock) welcomeBlock.classList.add('hidden');
    if (mainContent) mainContent.classList.remove('hidden');
}

// Обработка выбора файла в приветственном блоке
function handleWelcomeFileSelect(event) {
    const file = event.target.files[0];
    const fileName = document.getElementById('welcomeFileName');
    const startBtn = document.getElementById('startImportBtn');
    
    if (file) {
        fileName.textContent = file.name;
        // Проверяем, выбран ли тип системы оценивания
        const selectedSystem = document.querySelector('input[name="gradingSystem"]:checked');
        if (selectedSystem) {
            startBtn.disabled = false;
        }
    } else {
        fileName.textContent = 'Файл не выбран';
        startBtn.disabled = true;
    }
}

// Обработка изменения системы оценивания
function handleGradingSystemChange() {
    const selectedSystem = document.querySelector('input[name="gradingSystem"]:checked');
    const customInputs = document.getElementById('customGradingInputs');
    const startBtn = document.getElementById('startImportBtn');
    const welcomeFileInput = document.getElementById('welcomeFileInput');
    
    if (selectedSystem && selectedSystem.value === 'custom') {
        customInputs.classList.remove('hidden');
    } else {
        customInputs.classList.add('hidden');
    }
    
    // Проверяем, можно ли активировать кнопку
    if (selectedSystem && welcomeFileInput && welcomeFileInput.files.length > 0) {
        if (selectedSystem.value === 'custom') {
            const minGrade = document.getElementById('minGrade').value;
            const maxGrade = document.getElementById('maxGrade').value;
            startBtn.disabled = !(minGrade && maxGrade);
        } else {
            startBtn.disabled = false;
        }
    }
}

// Обработка импорта в приветственном блоке
async function handleWelcomeImport() {
    const fileInput = document.getElementById('welcomeFileInput');
    const selectedSystem = document.querySelector('input[name="gradingSystem"]:checked');
    
    if (!fileInput || !fileInput.files[0]) {
        showError('Пожалуйста, выберите файл для импорта');
        return;
    }
    
    if (!selectedSystem) {
        showError('Пожалуйста, выберите систему оценивания');
        return;
    }
    
    const file = fileInput.files[0];
    const fileExt = file.name.split('.').pop().toLowerCase();
    if (!['csv', 'xlsx', 'xls'].includes(fileExt)) {
        showError('Неподдерживаемый формат файла. Поддерживаются только CSV, XLSX и XLS');
        return;
    }
    
    // Подготавливаем данные системы оценивания
    let gradingSystemData = {
        system_type: selectedSystem.value
    };
    
    if (selectedSystem.value === 'custom') {
        const minGrade = parseFloat(document.getElementById('minGrade').value);
        const maxGrade = parseFloat(document.getElementById('maxGrade').value);
        
        if (!minGrade || !maxGrade || minGrade >= maxGrade) {
            showError('Пожалуйста, укажите корректные минимальную и максимальную оценки');
            return;
        }
        
        gradingSystemData.min_grade = minGrade;
        gradingSystemData.max_grade = maxGrade;
    }
    
    // Показываем индикатор загрузки
    showLoading(true);
    
    try {
        // Сначала сохраняем систему оценивания
        const gradingResponse = await fetch(`${API_BASE_URL}/api/grading-system`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(gradingSystemData)
        });
        
        if (!gradingResponse.ok) {
            throw new Error('Ошибка сохранения системы оценивания');
        }
        
        // Затем импортируем файл
        const formData = new FormData();
        formData.append('file', file);
        
        const importResponse = await fetch(`${API_BASE_URL}/api/import`, {
            method: 'POST',
            body: formData
        });
        
        if (!importResponse.ok) {
            let errorMessage = `Ошибка ${importResponse.status}: ${importResponse.statusText}`;
            try {
                const errorData = await importResponse.json();
                errorMessage = errorData.detail || errorMessage;
            } catch (e) {
                try {
                    const text = await importResponse.text();
                    if (text) {
                        errorMessage = text;
                    }
                } catch (textError) {
                    // Оставляем стандартное сообщение об ошибке
                }
            }
            throw new Error(errorMessage);
        }
        
        const result = await importResponse.json();
        showLoading(false);
        showSuccess(`Данные успешно импортированы! Загружено ${result.rows} строк.`);
        
        // Переключаемся на основной контент
        showMainContent();
        
        // Загружаем данные
        await loadInitialData();
        await loadPlotData();
        await loadStatistics();
        
    } catch (error) {
        showLoading(false);
        showError(`Ошибка при импорте: ${error.message}`);
        console.error('Ошибка импорта:', error);
    }
}

// Обработка изменения фильтров
async function handleFilterChange() {
    const studentId = document.getElementById('studentFilter').value;
    const subject = document.getElementById('subjectFilter').value;
    const startDate = document.getElementById('startDateFilter').value;
    const endDate = document.getElementById('endDateFilter').value;

    currentFilters.student_id = studentId || null;
    currentFilters.subject = subject || null;
    currentFilters.start_date = startDate || null;
    currentFilters.end_date = endDate || null;
    // plot_type всегда 'dashboard'
    currentFilters.plot_type = 'dashboard';

    await loadPlotData();
    await loadStatistics();
}

// Обновление данных
async function handleRefresh() {
    try {
        showLoading(true);
        
        // Сбрасываем все фильтры в UI
        document.getElementById('studentFilter').value = '';
        document.getElementById('subjectFilter').value = '';
        document.getElementById('startDateFilter').value = '';
        document.getElementById('endDateFilter').value = '';
        
        // Сбрасываем состояние фильтров
        currentFilters = {
            student_id: null,
            subject: null,
            start_date: null,
            end_date: null,
            plot_type: 'dashboard'
        };
        
        // Очищаем контейнер графиков (правильно удаляем Plotly графики)
        const plotsContainer = document.getElementById('plotsContainer');
        const existingPlots = plotsContainer.querySelectorAll('[id^="plot-"]');
        existingPlots.forEach(plotDiv => {
            if (plotDiv.id && typeof Plotly !== 'undefined') {
                try {
                    Plotly.purge(plotDiv.id);
                } catch (e) {
                    console.warn(`Ошибка при удалении графика ${plotDiv.id}:`, e);
                }
            }
        });
        plotsContainer.innerHTML = '';
        availablePlots = [];
        
        // Загружаем данные заново
        await loadInitialData();
        await loadPlotData();
        await loadStatistics();
        
        showLoading(false);
        showSuccess('Данные успешно обновлены!');
    } catch (error) {
        showLoading(false);
        showError(`Ошибка при обновлении данных: ${error.message}`);
        console.error('Ошибка обновления данных:', error);
    }
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

    // Сортируем студентов по ID по возрастанию
    const sortedStudents = [...students].sort((a, b) => {
        const idA = parseInt(a.student_id) || 0;
        const idB = parseInt(b.student_id) || 0;
        return idA - idB;
    });

    sortedStudents.forEach(student => {
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
        if (currentFilters.start_date) {
            params.append('start_date', currentFilters.start_date);
        }
        if (currentFilters.end_date) {
            params.append('end_date', currentFilters.end_date);
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
    
    // Правильно удаляем все существующие графики Plotly перед очисткой
    const existingPlots = container.querySelectorAll('[id^="plot-"]');
    existingPlots.forEach(plotDiv => {
        if (plotDiv.id && typeof Plotly !== 'undefined') {
            try {
                Plotly.purge(plotDiv.id);
            } catch (e) {
                console.warn(`Ошибка при удалении графика ${plotDiv.id}:`, e);
            }
        }
    });
    
    container.innerHTML = '';
    availablePlots = []; // Очищаем список графиков

    // Проверка на пустые или некорректные данные
    if (!plotData) {
        container.innerHTML = '<p class="no-data">Нет данных для отображения</p>';
        return;
    }

    // Если plotData содержит словарь с несколькими графиками (dashboard)
    if (typeof plotData === 'object' && !Array.isArray(plotData) && !plotData.data) {
        // Дашборд или сравнение содержат несколько графиков в виде объекта
        const plotNames = {
            'grade_distribution': 'Распределение оценок',
            'performance_trend': 'Динамика успеваемости',
            'subject_comparison': 'Сравнение средних оценок по предметам',
            'student_comparison': 'Сравнение студентов',
            'subject_heatmap': 'Тепловая карта по предметам',
            'scatter_trend': 'Корреляция времени и оценок'
        };

        let plotIndex = 0;
        for (const [key, plot] of Object.entries(plotData)) {
            // Пропускаем box_plot, так как он удален из дашборда
            if (key === 'box_plot') {
                continue;
            }
            // Проверяем, что график валидный и содержит данные
            if (plot && plot.data && plot.layout && Array.isArray(plot.data)) {
                // Проверяем, есть ли хотя бы один trace с данными
                const hasData = plot.data.some(trace => {
                    if (trace && (trace.x || trace.y || trace.z || trace.values)) {
                        const xLen = Array.isArray(trace.x) ? trace.x.length : 0;
                        const yLen = Array.isArray(trace.y) ? trace.y.length : 0;
                        const zLen = Array.isArray(trace.z) ? trace.z.length : 0;
                        const valuesLen = Array.isArray(trace.values) ? trace.values.length : 0;
                        return xLen > 0 || yLen > 0 || zLen > 0 || valuesLen > 0;
                    }
                    return false;
                });
                
                if (hasData || plot.data.length > 0) {
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
                        graphContainer.style.width = '100%';
                        graphContainer.style.minHeight = '400px';
                        graphContainer.style.height = '450px';
                        plotDiv.appendChild(graphContainer);
                        
                        container.appendChild(plotDiv);

                        Plotly.newPlot(plotId, plot.data, plot.layout, {
                            responsive: true,
                            displayModeBar: true,
                            modeBarButtonsToRemove: ['pan2d', 'lasso2d'],
                            useResizeHandler: true
                        });
                        
                        // Сохраняем информацию о графике для экспорта
                        availablePlots.push({
                            id: plotId,
                            title: plotNames[key] || key,
                            key: key
                        });
                        
                        // Принудительно изменяем размер после рендеринга для корректной адаптации
                        setTimeout(() => {
                            Plotly.Plots.resize(plotId);
                        }, 100);
                        
                        // Дополнительный resize после полной загрузки
                        setTimeout(() => {
                            Plotly.Plots.resize(plotId);
                        }, 300);

                        plotIndex++;
                    } catch (plotError) {
                        console.error(`Ошибка рендеринга графика ${key}:`, plotError);
                        // Показываем сообщение об ошибке
                        const errorDiv = document.createElement('div');
                        errorDiv.className = 'plot-item';
                        errorDiv.innerHTML = `<h3 class="plot-title">${plotNames[key] || key}</h3><p class="no-data">Ошибка отображения графика: ${plotError.message}</p>`;
                        container.appendChild(errorDiv);
                    }
                } else {
                    console.warn(`График ${key} не содержит данных:`, plot);
                    // Показываем сообщение об отсутствии данных
                    const noDataDiv = document.createElement('div');
                    noDataDiv.className = 'plot-item';
                    noDataDiv.innerHTML = `<h3 class="plot-title">${plotNames[key] || key}</h3><p class="no-data">Нет данных для отображения</p>`;
                    container.appendChild(noDataDiv);
                }
            } else {
                console.warn(`График ${key} имеет некорректную структуру:`, plot);
                // Показываем сообщение об ошибке структуры
                const errorDiv = document.createElement('div');
                errorDiv.className = 'plot-item';
                errorDiv.innerHTML = `<h3 class="plot-title">${plotNames[key] || key}</h3><p class="no-data">Ошибка структуры данных графика</p>`;
                container.appendChild(errorDiv);
            }
        }

        if (plotIndex === 0) {
            container.innerHTML = '<p class="no-data">Нет данных для отображения. Проверьте, что данные загружены в систему.</p>';
        }
    } else if (plotData.data && plotData.layout && Array.isArray(plotData.data)) {
        // Одиночный график
        // Проверяем, есть ли хотя бы один trace с данными
        const hasData = plotData.data.some(trace => {
            if (trace && (trace.x || trace.y || trace.z || trace.values)) {
                const xLen = Array.isArray(trace.x) ? trace.x.length : 0;
                const yLen = Array.isArray(trace.y) ? trace.y.length : 0;
                const zLen = Array.isArray(trace.z) ? trace.z.length : 0;
                const valuesLen = Array.isArray(trace.values) ? trace.values.length : 0;
                return xLen > 0 || yLen > 0 || zLen > 0 || valuesLen > 0;
            }
            return false;
        });
        
        if (hasData && plotData.data.length > 0) {
            try {
                const plotDiv = document.createElement('div');
                plotDiv.className = 'plot-item';
                
                // Добавляем заголовок из layout, если он есть
                if (plotData.layout && plotData.layout.title) {
                    const title = document.createElement('h3');
                    title.className = 'plot-title';
                    title.textContent = typeof plotData.layout.title === 'string' 
                        ? plotData.layout.title 
                        : (plotData.layout.title.text || 'График');
                    plotDiv.appendChild(title);
                }
                
                const plotId = 'plot-main';
                const graphContainer = document.createElement('div');
                graphContainer.id = plotId;
                graphContainer.style.width = '100%';
                graphContainer.style.minHeight = '400px';
                graphContainer.style.height = '450px';
                plotDiv.appendChild(graphContainer);
                container.appendChild(plotDiv);

                Plotly.newPlot(plotId, plotData.data, plotData.layout, {
                    responsive: true,
                    displayModeBar: true,
                    modeBarButtonsToRemove: ['pan2d', 'lasso2d'],
                    useResizeHandler: true
                });
                
                // Сохраняем информацию о графике для экспорта
                const title = (plotData.layout && plotData.layout.title) 
                    ? (typeof plotData.layout.title === 'string' 
                        ? plotData.layout.title 
                        : (plotData.layout.title.text || 'График'))
                    : 'График';
                availablePlots.push({
                    id: plotId,
                    title: title,
                    key: 'main'
                });
                
                // Принудительно изменяем размер после рендеринга для корректной адаптации
                setTimeout(() => {
                    Plotly.Plots.resize(plotId);
                }, 100);
                
                // Дополнительный resize после полной загрузки
                setTimeout(() => {
                    Plotly.Plots.resize(plotId);
                }, 300);
            } catch (plotError) {
                console.error('Ошибка рендеринга графика:', plotError);
                container.innerHTML = `<p class="no-data">Ошибка при отображении графика: ${plotError.message}</p>`;
            }
        } else {
            console.warn('График не содержит данных:', plotData);
            const title = (plotData.layout && plotData.layout.title) 
                ? (typeof plotData.layout.title === 'string' 
                    ? plotData.layout.title 
                    : (plotData.layout.title.text || 'График'))
                : 'График';
            container.innerHTML = `<div class="plot-item"><h3 class="plot-title">${title}</h3><p class="no-data">Нет данных для отображения</p></div>`;
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
        if (currentFilters.start_date) {
            params.append('start_date', currentFilters.start_date);
        }
        if (currentFilters.end_date) {
            params.append('end_date', currentFilters.end_date);
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
            value: (stats.average_grade != null && stats.average_grade !== undefined) ? stats.average_grade.toFixed(2) : 'N/A',
            icon: '📈'
        },
        {
            title: 'Всего оценок',
            value: stats.total_grades || 0,
            icon: '📝'
        },
        {
            title: 'Максимальная оценка',
            value: (stats.max_grade != null && stats.max_grade !== undefined) ? stats.max_grade : 'N/A',
            icon: '⭐'
        },
        {
            title: 'Минимальная оценка',
            value: (stats.min_grade != null && stats.min_grade !== undefined) ? stats.min_grade : 'N/A',
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

// Открыть модальное окно экспорта
function openExportModal() {
    const modal = document.getElementById('exportModal');
    const plotsContainer = document.getElementById('plotsCheckboxes');
    
    // Очищаем предыдущие чекбоксы
    plotsContainer.innerHTML = '';
    
    // Проверяем, есть ли графики для экспорта
    if (availablePlots.length === 0) {
        plotsContainer.innerHTML = '<p class="no-data">Нет графиков для экспорта. Загрузите данные сначала.</p>';
        modal.classList.remove('hidden');
        return;
    }
    
    // Создаем чекбоксы для каждого графика
    availablePlots.forEach(plot => {
        const label = document.createElement('label');
        label.className = 'checkbox-label';
        label.innerHTML = `
            <input type="checkbox" name="plot" value="${plot.id}" data-title="${plot.title}" checked>
            <span>${plot.title}</span>
        `;
        plotsContainer.appendChild(label);
    });
    
    // Сбрасываем выбор форматов (PNG по умолчанию выбран)
    document.getElementById('selectAllPlots').checked = true;
    document.getElementById('selectAllFormats').checked = false;
    
    modal.classList.remove('hidden');
}

// Закрыть модальное окно экспорта
function closeExportModal() {
    const modal = document.getElementById('exportModal');
    modal.classList.add('hidden');
}

// Переключить выбор всех графиков
function toggleSelectAllPlots(e) {
    const checkboxes = document.querySelectorAll('input[name="plot"]');
    checkboxes.forEach(cb => cb.checked = e.target.checked);
}

// Переключить выбор всех форматов
function toggleSelectAllFormats(e) {
    const checkboxes = document.querySelectorAll('input[name="format"]');
    checkboxes.forEach(cb => cb.checked = e.target.checked);
}

// Обработка экспорта в ZIP
async function handleExport() {
    const selectedPlots = Array.from(document.querySelectorAll('input[name="plot"]:checked'));
    const selectedFormats = Array.from(document.querySelectorAll('input[name="format"]:checked'));
    
    // Проверка выбора
    if (selectedPlots.length === 0) {
        showError('Пожалуйста, выберите хотя бы один график для экспорта');
        return;
    }
    
    if (selectedFormats.length === 0) {
        showError('Пожалуйста, выберите хотя бы один формат экспорта');
        return;
    }
    
    // Показываем индикатор загрузки
    showLoading(true);
    closeExportModal();
    
    try {
        await exportPlotsToZip(selectedPlots, selectedFormats);
        showLoading(false);
        showSuccess(`Успешно экспортировано ${selectedPlots.length} график(ов) в ${selectedFormats.length} формате(ах) в ZIP архив`);
    } catch (error) {
        showLoading(false);
        showError(`Ошибка при экспорте: ${error.message}`);
        console.error('Ошибка экспорта:', error);
    }
}

// Экспорт графиков в ZIP архив
async function exportPlotsToZip(selectedPlots, selectedFormats) {
    const zip = new JSZip();
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    
    // Определяем, нужно ли организовывать по папкам
    // Если выбрано больше одного графика И больше одного формата - организуем по папкам форматов
    const shouldOrganizeByFolders = selectedPlots.length > 1 && selectedFormats.length > 1;
    
    // Экспортируем каждый выбранный график в каждом выбранном формате
    for (const plotCheckbox of selectedPlots) {
        const plotId = plotCheckbox.value;
        const plotTitle = plotCheckbox.dataset.title;
        const plotDiv = document.getElementById(plotId);
        
        if (!plotDiv) {
            console.warn(`График ${plotId} не найден`);
            continue;
        }
        
        const sanitizedTitle = plotTitle.replace(/[^a-zа-яё0-9]/gi, '_').toLowerCase();
        
        for (const formatCheckbox of selectedFormats) {
            const format = formatCheckbox.value;
            
            // Определяем путь к файлу: в папке формата или в корне
            const filename = shouldOrganizeByFolders 
                ? `${format}/${sanitizedTitle}.${format}`
                : `${sanitizedTitle}.${format}`;
            
            try {
                if (format === 'png' || format === 'svg') {
                    // Экспорт изображения
                    const dataUrl = await Plotly.toImage(plotDiv, {
                        format: format,
                        width: 1200,
                        height: 800,
                        scale: 2
                    });
                    
                    // Преобразуем data URL в blob и добавляем в ZIP
                    const response = await fetch(dataUrl);
                    const blob = await response.blob();
                    zip.file(filename, blob);
                } else if (format === 'html') {
                    // Экспорт HTML
                    const htmlContent = `<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${plotTitle}</title>
    <script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>
</head>
<body>
    <div id="plot" style="width: 100%; height: 100vh;"></div>
    <script>
        const plotData = ${JSON.stringify({
            data: plotDiv.data || [],
            layout: plotDiv.layout || {},
            config: plotDiv.config || {}
        })};
        Plotly.newPlot('plot', plotData.data, plotData.layout, plotData.config);
    </script>
</body>
</html>`;
                    zip.file(filename, htmlContent);
                } else if (format === 'json') {
                    // Экспорт JSON
                    const plotData = {
                        data: plotDiv.data || [],
                        layout: plotDiv.layout || {},
                        config: plotDiv.config || {}
                    };
                    const jsonString = JSON.stringify(plotData, null, 2);
                    zip.file(filename, jsonString);
                }
            } catch (error) {
                console.error(`Ошибка экспорта графика ${plotTitle} в формате ${format}:`, error);
                // Продолжаем экспорт других файлов
            }
        }
    }
    
    // Генерируем ZIP файл
    const zipBlob = await zip.generateAsync({ 
        type: 'blob',
        compression: 'DEFLATE',
        compressionOptions: { level: 6 }
    });
    
    // Скачиваем ZIP файл
    const url = URL.createObjectURL(zipBlob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `graphs_export_${timestamp}.zip`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Показать сообщение об успехе
function showSuccess(message) {
    const successDiv = document.createElement('div');
    successDiv.className = 'success-message';
    successDiv.textContent = message;
    successDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: var(--secondary-color);
        color: white;
        padding: 15px 25px;
        border-radius: 6px;
        box-shadow: var(--shadow-hover);
        z-index: 1001;
        max-width: 400px;
        animation: slideIn 0.3s ease-out;
    `;
    document.body.appendChild(successDiv);
    
    setTimeout(() => {
        successDiv.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => {
            if (document.body.contains(successDiv)) {
                document.body.removeChild(successDiv);
            }
        }, 300);
    }, 3000);
}

// Открыть модальное окно импорта
function openImportModal() {
    const modal = document.getElementById('importModal');
    const fileInput = document.getElementById('fileInput');
    const fileName = document.getElementById('fileName');
    const confirmBtn = document.getElementById('confirmImportBtn');
    const preview = document.getElementById('importPreview');
    
    if (!modal || !fileInput || !fileName || !confirmBtn || !preview) {
        console.error('Не найдены элементы модального окна импорта');
        return;
    }
    
    // Сброс состояния
    fileInput.value = '';
    fileName.textContent = 'Файл не выбран';
    confirmBtn.disabled = true;
    preview.classList.add('hidden');
    preview.innerHTML = '';
    
    modal.classList.remove('hidden');
}

// Закрыть модальное окно импорта
function closeImportModal() {
    const modal = document.getElementById('importModal');
    modal.classList.add('hidden');
}

// Обработка выбора файла
function handleFileSelect(event) {
    const file = event.target.files[0];
    const fileName = document.getElementById('fileName');
    const confirmBtn = document.getElementById('confirmImportBtn');
    const preview = document.getElementById('importPreview');
    
    if (file) {
        fileName.textContent = file.name;
        confirmBtn.disabled = false;
        
        // Показываем информацию о файле
        const fileSize = (file.size / 1024).toFixed(2);
        preview.innerHTML = `
            <div class="file-info">
                <p><strong>Имя файла:</strong> ${file.name}</p>
                <p><strong>Размер:</strong> ${fileSize} KB</p>
                <p><strong>Тип:</strong> ${file.type || 'Неизвестно'}</p>
            </div>
        `;
        preview.classList.remove('hidden');
    } else {
        fileName.textContent = 'Файл не выбран';
        confirmBtn.disabled = true;
        preview.classList.add('hidden');
    }
}

// Обработка импорта файла
async function handleImport() {
    const fileInput = document.getElementById('fileInput');
    
    if (!fileInput) {
        showError('Ошибка: элемент выбора файла не найден');
        return;
    }
    
    const file = fileInput.files[0];
    
    if (!file) {
        showError('Пожалуйста, выберите файл для импорта');
        return;
    }
    
    // Проверка расширения файла
    const fileExt = file.name.split('.').pop().toLowerCase();
    if (!['csv', 'xlsx', 'xls'].includes(fileExt)) {
        showError('Неподдерживаемый формат файла. Поддерживаются только CSV, XLSX и XLS');
        return;
    }
    
    // Показываем индикатор загрузки
    showLoading(true);
    closeImportModal();
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${API_BASE_URL}/api/import`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            let errorMessage = `Ошибка ${response.status}: ${response.statusText}`;
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorMessage;
            } catch (e) {
                // Если ответ не JSON, используем текст ответа
                try {
                    const text = await response.text();
                    if (text) {
                        errorMessage = text;
                    }
                } catch (textError) {
                    // Оставляем стандартное сообщение об ошибке
                }
            }
            throw new Error(errorMessage);
        }
        
        const result = await response.json();
        showLoading(false);
        showSuccess(`Файл успешно импортирован! Загружено ${result.rows} строк.`);
        
        // Обновляем данные на странице
        await loadInitialData();
        await loadPlotData();
        await loadStatistics();
        
    } catch (error) {
        showLoading(false);
        showError(`Ошибка при импорте: ${error.message}`);
        console.error('Ошибка импорта:', error);
    }
}

// Обработка экспорта CSV (без показа сообщений - используется в handleExport)
async function handleExportCsv() {
    const params = new URLSearchParams();
    if (currentFilters.student_id) {
        params.append('student_id', currentFilters.student_id);
    }
    if (currentFilters.subject) {
        params.append('subject', currentFilters.subject);
    }
    if (currentFilters.start_date) {
        params.append('start_date', currentFilters.start_date);
    }
    if (currentFilters.end_date) {
        params.append('end_date', currentFilters.end_date);
    }
    
    const response = await fetch(`${API_BASE_URL}/api/export/csv?${params.toString()}`);
    
    if (!response.ok) {
        let errorMessage = `Ошибка ${response.status}: ${response.statusText}`;
        try {
            const errorData = await response.json();
            errorMessage = errorData.detail || errorMessage;
        } catch (e) {
            // Если ответ не JSON
        }
        throw new Error(errorMessage);
    }
    
    // Скачиваем файл
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `grades_export_${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

// Обработка экспорта PDF
async function handleExportPdf() {
    try {
        showLoading(true);
        
        const params = new URLSearchParams();
        if (currentFilters.student_id) {
            params.append('student_id', currentFilters.student_id);
        }
        if (currentFilters.subject) {
            params.append('subject', currentFilters.subject);
        }
        if (currentFilters.start_date) {
            params.append('start_date', currentFilters.start_date);
        }
        if (currentFilters.end_date) {
            params.append('end_date', currentFilters.end_date);
        }
        
        const response = await fetch(`${API_BASE_URL}/api/export/pdf?${params.toString()}`);
        
        if (!response.ok) {
            let errorMessage = `Ошибка ${response.status}: ${response.statusText}`;
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorMessage;
            } catch (e) {
                // Если ответ не JSON
            }
            throw new Error(errorMessage);
        }
        
        // Скачиваем файл
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `report_${new Date().toISOString().slice(0, 10)}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        showLoading(false);
        showSuccess('PDF отчет успешно экспортирован!');
    } catch (error) {
        showLoading(false);
        showError(`Ошибка при экспорте PDF: ${error.message}`);
        console.error('Ошибка экспорта PDF:', error);
    }
}

