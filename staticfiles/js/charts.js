// Общие настройки для всех графиков
const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            position: 'top',
        }
    }
};

// Функция для создания цветов для графика
function generateColors(count) {
    const colors = [
        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
        '#FF9F40', '#8AC249', '#EA80FC', '#00B8D4', '#FF6E40'
    ];
    
    if (count <= colors.length) {
        return colors.slice(0, count);
    }
    
    // Если нужно больше цветов, чем есть в массиве, создаем случайные
    const result = [...colors];
    for (let i = colors.length; i < count; i++) {
        const r = Math.floor(Math.random() * 255);
        const g = Math.floor(Math.random() * 255);
        const b = Math.floor(Math.random() * 255);
        result.push(`rgb(${r}, ${g}, ${b})`);
    }
    
    return result;
}

// Создание круговой диаграммы расходов по категориям
function createPieChart(elementId, labels, data) {
    const ctx = document.getElementById(elementId).getContext('2d');
    const colors = generateColors(data.length);
    
    return new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderWidth: 1
            }]
        },
        options: {
            ...chartOptions,
            cutout: '15%'
        }
    });
}

// Создание линейного графика для сравнения доходов и расходов по месяцам
function createLineChart(elementId, labels, incomeData, expenseData) {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Доходы',
                    data: incomeData,
                    backgroundColor: 'rgba(28, 200, 138, 0.1)',
                    borderColor: '#1cc88a',
                    pointBackgroundColor: '#1cc88a',
                    pointBorderColor: '#fff',
                    pointRadius: 4,
                    fill: true,
                    tension: 0.1
                },
                {
                    label: 'Расходы',
                    data: expenseData,
                    backgroundColor: 'rgba(231, 74, 59, 0.1)',
                    borderColor: '#e74a3b',
                    pointBackgroundColor: '#e74a3b',
                    pointBorderColor: '#fff',
                    pointRadius: 4,
                    fill: true,
                    tension: 0.1
                }
            ]
        },
        options: {
            ...chartOptions,
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}