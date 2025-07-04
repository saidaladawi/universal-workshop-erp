/**
 * Demand Forecasting Interface Components
 * Interactive forecasting tools for inventory optimization
 */

class DemandForecastingUI {
    constructor() {
        this.currentForecast = null;
        this.chartInstance = null;
        this.initializeForecastingTools();
    }

    initializeForecastingTools() {
        // Add forecasting button to Item form
        $(document).on('form_ready', function(frm) {
            if (frm.doctype === 'Item' && frm.doc.is_stock_item) {
                frm.add_custom_button(__('Demand Forecast'), () => {
                    new DemandForecastDialog(frm.doc.item_code).show();
                }, __('Analytics'));
            }
        });

        // Add forecasting dashboard to workspace
        this.setupForecastingDashboard();
    }

    setupForecastingDashboard() {
        // Create dashboard shortcut
        if (frappe.pages['parts-inventory']) {
            let page = frappe.pages['parts-inventory'];
            
            page.add_action_item(__('Demand Forecasting'), () => {
                this.showForecastingDashboard();
            });
        }
    }

    showForecastingDashboard() {
        let dialog = new frappe.ui.Dialog({
            title: __('Demand Forecasting Dashboard'),
            size: 'extra-large',
            fields: [
                {
                    fieldname: 'warehouse_filter',
                    fieldtype: 'Link',
                    options: 'Warehouse',
                    label: __('Warehouse'),
                    change: () => this.loadDashboardData(dialog)
                },
                {
                    fieldname: 'dashboard_html',
                    fieldtype: 'HTML',
                    options: '<div id="forecast-dashboard-container"></div>'
                }
            ],
            primary_action_label: __('Refresh'),
            primary_action: () => this.loadDashboardData(dialog)
        });

        dialog.show();
        this.loadDashboardData(dialog);
    }

    loadDashboardData(dialog) {
        let warehouse = dialog.get_value('warehouse_filter');
        
        frappe.call({
            method: 'universal_workshop.parts_inventory.demand_forecasting.get_forecast_dashboard_data',
            args: {
                warehouse: warehouse,
                top_items: 20
            },
            callback: (r) => {
                if (r.message && r.message.success) {
                    this.renderDashboard(r.message.dashboard_data);
                } else {
                    frappe.msgprint(__('Failed to load forecast data'));
                }
            }
        });
    }

    renderDashboard(data) {
        let container = document.getElementById('forecast-dashboard-container');
        if (!container) return;

        container.innerHTML = `
            <div class="forecast-dashboard">
                <div class="dashboard-header">
                    <h4>${__('Top Items Demand Forecast')}</h4>
                    <p class="text-muted">${__('Showing forecasts for top 20 consumed items')}</p>
                </div>
                <div class="forecast-grid">
                    ${data.map(item => this.renderForecastCard(item)).join('')}
                </div>
            </div>
        `;

        // Add click handlers
        container.querySelectorAll('.forecast-card').forEach(card => {
            card.addEventListener('click', (e) => {
                let itemCode = e.currentTarget.dataset.itemCode;
                new DemandForecastDialog(itemCode).show();
            });
        });
    }

    renderForecastCard(item) {
        let forecast = item.forecast_summary;
        let seasonalIcon = forecast.has_seasonality ? 
            '<i class="fa fa-calendar text-info" title="Seasonal Pattern Detected"></i>' : 
            '<i class="fa fa-minus text-muted" title="No Seasonality"></i>';

        return `
            <div class="forecast-card" data-item-code="${item.item_code}">
                <div class="card-header">
                    <strong>${item.item_name}</strong>
                    <span class="item-code text-muted">${item.item_code}</span>
                </div>
                <div class="card-body">
                    <div class="forecast-metric">
                        <span class="metric-label">${__('Next Period Forecast')}</span>
                        <span class="metric-value">${forecast.next_period_forecast}</span>
                    </div>
                    <div class="forecast-details">
                        <div class="detail-item">
                            <span>${__('Method')}</span>
                            <span class="method-badge">${forecast.forecast_method}</span>
                        </div>
                        <div class="detail-item">
                            <span>${__('Seasonality')}</span>
                            ${seasonalIcon}
                        </div>
                        <div class="detail-item">
                            <span>${__('Historical Consumption')}</span>
                            <span>${item.total_consumption}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
}

class DemandForecastDialog {
    constructor(itemCode) {
        this.itemCode = itemCode;
        this.dialog = null;
        this.chartData = null;
    }

    show() {
        this.dialog = new frappe.ui.Dialog({
            title: __('Demand Forecast for {0}', [this.itemCode]),
            size: 'extra-large',
            fields: [
                {
                    fieldname: 'forecast_params',
                    fieldtype: 'Section Break',
                    label: __('Forecast Parameters')
                },
                {
                    fieldname: 'forecast_periods',
                    fieldtype: 'Int',
                    label: __('Forecast Periods'),
                    default: 12,
                    description: __('Number of periods to forecast')
                },
                {
                    fieldname: 'forecast_method',
                    fieldtype: 'Select',
                    label: __('Forecast Method'),
                    options: [
                        'auto',
                        'simple_moving_average',
                        'weighted_moving_average', 
                        'exponential_smoothing',
                        'seasonal',
                        'seasonal_trend'
                    ],
                    default: 'auto',
                    description: __('Auto selects optimal method based on data')
                },
                {
                    fieldname: 'warehouse',
                    fieldtype: 'Link',
                    options: 'Warehouse',
                    label: __('Warehouse'),
                    description: __('Leave blank for all warehouses')
                },
                {
                    fieldname: 'include_seasonality',
                    fieldtype: 'Check',
                    label: __('Include Seasonality Analysis'),
                    default: 1
                },
                {
                    fieldname: 'confidence_level',
                    fieldtype: 'Select',
                    label: __('Confidence Level'),
                    options: ['0.90', '0.95', '0.99'],
                    default: '0.95'
                },
                {
                    fieldname: 'results_section',
                    fieldtype: 'Section Break',
                    label: __('Forecast Results')
                },
                {
                    fieldname: 'forecast_chart',
                    fieldtype: 'HTML',
                    options: '<div id="forecast-chart-container" style="height: 400px;"></div>'
                },
                {
                    fieldname: 'forecast_analysis',
                    fieldtype: 'HTML',
                    options: '<div id="forecast-analysis-container"></div>'
                }
            ],
            primary_action_label: __('Generate Forecast'),
            primary_action: () => this.generateForecast()
        });

        this.dialog.show();
        
        // Auto-generate forecast on load
        setTimeout(() => this.generateForecast(), 500);
    }

    generateForecast() {
        let params = {
            item_code: this.itemCode,
            forecast_periods: this.dialog.get_value('forecast_periods') || 12,
            forecast_method: this.dialog.get_value('forecast_method') || 'auto',
            warehouse: this.dialog.get_value('warehouse'),
            include_seasonality: this.dialog.get_value('include_seasonality'),
            confidence_level: parseFloat(this.dialog.get_value('confidence_level') || 0.95)
        };

        frappe.call({
            method: 'universal_workshop.parts_inventory.demand_forecasting.generate_item_demand_forecast',
            args: params,
            freeze: true,
            freeze_message: __('Generating forecast...'),
            callback: (r) => {
                if (r.message && r.message.success) {
                    this.renderForecastResults(r.message);
                } else {
                    frappe.msgprint({
                        title: __('Forecast Generation Failed'),
                        message: r.message?.error || __('Unable to generate forecast'),
                        indicator: 'red'
                    });
                }
            }
        });
    }

    renderForecastResults(forecast) {
        this.chartData = forecast;
        this.renderChart(forecast);
        this.renderAnalysis(forecast);
    }

    renderChart(forecast) {
        let chartContainer = document.getElementById('forecast-chart-container');
        if (!chartContainer) return;

        // Prepare data for Chart.js
        let periods = [];
        for (let i = 1; i <= forecast.forecast_periods; i++) {
            periods.push(`Period ${i}`);
        }

        let chartData = {
            labels: periods,
            datasets: [
                {
                    label: __('Forecast'),
                    data: forecast.forecasts,
                    borderColor: 'rgb(54, 162, 235)',
                    backgroundColor: 'rgba(54, 162, 235, 0.1)',
                    borderWidth: 2,
                    fill: false
                }
            ]
        };

        // Add confidence intervals if available
        if (forecast.confidence_intervals) {
            chartData.datasets.push({
                label: __('Upper Confidence'),
                data: forecast.confidence_intervals.upper,
                borderColor: 'rgba(255, 99, 132, 0.5)',
                backgroundColor: 'rgba(255, 99, 132, 0.1)',
                borderWidth: 1,
                borderDash: [5, 5],
                fill: false
            });

            chartData.datasets.push({
                label: __('Lower Confidence'),
                data: forecast.confidence_intervals.lower,
                borderColor: 'rgba(255, 99, 132, 0.5)',
                backgroundColor: 'rgba(255, 99, 132, 0.1)',
                borderWidth: 1,
                borderDash: [5, 5],
                fill: '-1'
            });
        }

        // Create chart using Chart.js (if available) or fallback to simple table
        if (typeof Chart !== 'undefined') {
            chartContainer.innerHTML = '<canvas id="forecastChart"></canvas>';
            let ctx = document.getElementById('forecastChart').getContext('2d');
            
            new Chart(ctx, {
                type: 'line',
                data: chartData,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: __('Demand Quantity')
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: __('Time Period')
                            }
                        }
                    },
                    plugins: {
                        title: {
                            display: true,
                            text: __('Demand Forecast - {0}', [forecast.forecast_method])
                        },
                        legend: {
                            display: true
                        }
                    }
                }
            });
        } else {
            // Fallback to table display
            this.renderForecastTable(chartContainer, forecast);
        }
    }

    renderForecastTable(container, forecast) {
        let table = `
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>${__('Period')}</th>
                        <th>${__('Forecast')}</th>
                        ${forecast.confidence_intervals ? '<th>' + __('Confidence Range') + '</th>' : ''}
                    </tr>
                </thead>
                <tbody>
        `;

        forecast.forecasts.forEach((value, index) => {
            let confidenceRange = '';
            if (forecast.confidence_intervals) {
                let lower = forecast.confidence_intervals.lower[index];
                let upper = forecast.confidence_intervals.upper[index];
                confidenceRange = `<td>${lower} - ${upper}</td>`;
            }

            table += `
                <tr>
                    <td>Period ${index + 1}</td>
                    <td><strong>${value}</strong></td>
                    ${confidenceRange}
                </tr>
            `;
        });

        table += '</tbody></table>';
        container.innerHTML = table;
    }

    renderAnalysis(forecast) {
        let analysisContainer = document.getElementById('forecast-analysis-container');
        if (!analysisContainer) return;

        let analysis = `
            <div class="forecast-analysis">
                <div class="row">
                    <div class="col-md-6">
                        <div class="analysis-section">
                            <h5>${__('Forecast Summary')}</h5>
                            <div class="summary-grid">
                                <div class="summary-item">
                                    <span class="label">${__('Method Used')}</span>
                                    <span class="value">${forecast.forecast_method}</span>
                                </div>
                                <div class="summary-item">
                                    <span class="label">${__('Forecast Periods')}</span>
                                    <span class="value">${forecast.forecast_periods}</span>
                                </div>
                                <div class="summary-item">
                                    <span class="label">${__('Average Forecast')}</span>
                                    <span class="value">${this.calculateAverage(forecast.forecasts)}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="analysis-section">
                            <h5>${__('Historical Statistics')}</h5>
                            <div class="summary-grid">
                                ${this.renderHistoricalStats(forecast.historical_stats)}
                            </div>
                        </div>
                    </div>
                </div>
                
                ${forecast.seasonal_analysis ? this.renderSeasonalAnalysis(forecast.seasonal_analysis) : ''}
                
                <div class="insights-section">
                    <h5>${__('Insights & Recommendations')}</h5>
                    ${this.renderInsights(forecast.insights)}
                </div>
            </div>
        `;

        analysisContainer.innerHTML = analysis;
    }

    renderHistoricalStats(stats) {
        if (!stats) return '';

        return `
            <div class="summary-item">
                <span class="label">${__('Mean Demand')}</span>
                <span class="value">${stats.mean}</span>
            </div>
            <div class="summary-item">
                <span class="label">${__('Total Periods')}</span>
                <span class="value">${stats.total_periods}</span>
            </div>
            <div class="summary-item">
                <span class="label">${__('Standard Deviation')}</span>
                <span class="value">${stats.std_dev}</span>
            </div>
        `;
    }

    renderSeasonalAnalysis(seasonal) {
        if (!seasonal || !seasonal.has_seasonality) return '';

        return `
            <div class="row">
                <div class="col-md-12">
                    <div class="analysis-section seasonal-analysis">
                        <h5>${__('Seasonal Analysis')}</h5>
                        <div class="alert alert-info">
                            <strong>${__('Seasonality Detected')}</strong><br>
                            ${__('Peak Month')}: ${this.getMonthName(seasonal.peak_month)} (${seasonal.peak_index}x average)<br>
                            ${__('Low Month')}: ${this.getMonthName(seasonal.low_month)} (${seasonal.low_index}x average)<br>
                            ${__('Seasonal Variation')}: ${(seasonal.seasonal_variation * 100).toFixed(1)}%
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderInsights(insights) {
        if (!insights) return '';

        let html = '';

        if (insights.recommendations && insights.recommendations.length > 0) {
            html += `
                <div class="insight-group recommendations">
                    <h6><i class="fa fa-lightbulb text-success"></i> ${__('Recommendations')}</h6>
                    <ul>
                        ${insights.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        if (insights.risk_factors && insights.risk_factors.length > 0) {
            html += `
                <div class="insight-group risk-factors">
                    <h6><i class="fa fa-exclamation-triangle text-warning"></i> ${__('Risk Factors')}</h6>
                    <ul>
                        ${insights.risk_factors.map(risk => `<li>${risk}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        if (insights.opportunities && insights.opportunities.length > 0) {
            html += `
                <div class="insight-group opportunities">
                    <h6><i class="fa fa-arrow-up text-info"></i> ${__('Opportunities')}</h6>
                    <ul>
                        ${insights.opportunities.map(opp => `<li>${opp}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        return html;
    }

    calculateAverage(values) {
        if (!values || values.length === 0) return 0;
        let sum = values.reduce((a, b) => a + b, 0);
        return (sum / values.length).toFixed(2);
    }

    getMonthName(monthNum) {
        const months = [
            __('January'), __('February'), __('March'), __('April'),
            __('May'), __('June'), __('July'), __('August'),
            __('September'), __('October'), __('November'), __('December')
        ];
        return months[monthNum - 1] || monthNum;
    }
}

// Initialize when DOM is ready
$(document).ready(function() {
    new DemandForecastingUI();
});

// Add CSS styles
frappe.require([
    '/assets/universal_workshop/css/demand_forecasting.css'
]); 