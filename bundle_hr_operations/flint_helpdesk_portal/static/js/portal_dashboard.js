'use strict';

// Store chart instances globally
let charts = new Map();

// Utility function to safely get elements
function getElement(selector) {
    return document.querySelector(selector);
}

// Destroy existing chart if it exists
function destroyChart(chartId) {
    const existingChart = charts.get(chartId);
    if (existingChart) {
        existingChart.destroy();
        charts.delete(chartId);
    }
}

// Create or update a chart
function createChart(elementId, config) {
    // Destroy existing chart if it exists
    destroyChart(elementId);
    
    const element = getElement(`#${elementId}`);
    if (!element) {
        console.warn(`Canvas element #${elementId} not found`);
        return null;
    }

    const ctx = element.getContext('2d');
    const chart = new Chart(ctx, config);
    charts.set(elementId, chart);
    return chart;
}

// Initialize charts when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Charts
    function initializeCharts() {
        // Only proceed if chart configuration exists
        if (!window.chartConfig) {
            console.warn('Chart configuration not found');
            return;
        }

        // Status Distribution Chart
        if (window.chartConfig.status) {
            createChart('statusChart', {
                type: window.chartConfig.status.type || 'doughnut',
                data: window.chartConfig.status.data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '80%',
                    plugins: {
                        legend: {
                            display: true,
                            position: 'bottom',
                            labels: {
                                color: '#ecf0f1',
                                padding: 20,
                                font: {
                                    size: 12
                                }
                            }
                        },
                        tooltip: {
                            backgroundColor: "rgb(255,255,255)",
                            bodyColor: "#858796",
                            borderColor: '#dddfeb',
                            borderWidth: 1,
                            padding: {
                                x: 15,
                                y: 15
                            },
                            displayColors: false,
                            caretPadding: 10,
                        }
                    }
                }
            });
        }

        // Monthly Trends Chart
        if (window.chartConfig.monthly) {
            createChart('monthlyChart', {
                type: window.chartConfig.monthly.type || 'line',
                data: window.chartConfig.monthly.data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            grid: {
                                display: false,
                                drawBorder: false
                            },
                            ticks: {
                                maxTicksLimit: 7,
                                color: '#ecf0f1'
                            }
                        },
                        y: {
                            ticks: {
                                maxTicksLimit: 5,
                                padding: 10,
                                beginAtZero: true,
                                color: '#ecf0f1'
                            },
                            grid: {
                                color: 'rgba(236, 240, 241, 0.1)',
                                zeroLineColor: 'rgba(236, 240, 241, 0.25)',
                                drawBorder: false,
                                borderDash: [2],
                                zeroLineBorderDash: [2]
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: true,
                            position: 'bottom',
                            labels: {
                                color: '#ecf0f1',
                                padding: 20,
                                font: {
                                    size: 12
                                }
                            }
                        },
                        tooltip: {
                            backgroundColor: "rgb(255,255,255)",
                            bodyColor: "#858796",
                            titleMarginBottom: 10,
                            titleColor: '#6e707e',
                            titleFont: {
                                size: 14
                            },
                            borderColor: '#dddfeb',
                            borderWidth: 1,
                            padding: {
                                x: 15,
                                y: 15
                            },
                            displayColors: false,
                            intersect: false,
                            mode: 'index',
                            caretPadding: 10,
                        }
                    }
                }
            });
        }
    }

    // Initialize charts
    try {
        initializeCharts();
    } catch (error) {
        console.error('Error initializing charts:', error);
    }
});
