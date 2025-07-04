/**
 * Universal Workshop ERP - Performance Visualizations Frontend
 * Chart.js integration with Arabic RTL support and auto-refresh logic
 */

class PerformanceVisualizationManager {
    constructor(options = {}) {
        this.containerId = options.containerId || 'performance-charts-container';
        this.language = frappe.boot.lang || 'en';
        this.isRTL = document.documentElement.dir === 'rtl' || this.language === 'ar';
        this.charts = new Map();
        this.refreshIntervals = new Map();
        this.chartInstances = new Map();

        // Chart.js configuration
        this.chartDefaults = {
            responsive: true,
            maintainAspectRatio: false,
            locale: this.language,
            font: {
                family: this.isRTL ? 'Cairo, Tahoma, Arial, sans-serif' : 'system-ui, sans-serif'
            }
        };

        // Auto-refresh settings
        this.autoRefreshEnabled = options.autoRefresh !== false;
        this.defaultRefreshInterval = options.refreshInterval || 300000; // 5 minutes

        this.init();
    }

    async init() {
        try {
            // Load Chart.js if not already loaded
            await this.loadChartJS();

            // Setup Chart.js defaults for Arabic RTL
            this.setupChartJSDefaults();

            // Create container structure
            this.createContainer();

            // Load initial charts
            await this.loadAllCharts();

            // Setup auto-refresh
            if (this.autoRefreshEnabled) {
                this.setupAutoRefresh();
            }

            // Setup WebSocket for real-time updates
            this.setupWebSocketUpdates();

            console.log('Performance Visualization Manager initialized successfully');
        } catch (error) {
            console.error('Failed to initialize Performance Visualization Manager:', error);
            this.showError('Failed to initialize charts');
        }
    }

    async loadChartJS() {
        // Check if Chart.js is already loaded
        if (typeof Chart !== 'undefined') {
            return;
        }

        // Load Chart.js from CDN
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js';
            script.onload = () => {
                // Load Chart.js adapters for date/time
                const adapterScript = document.createElement('script');
                adapterScript.src = 'https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3.0.0/dist/chartjs-adapter-date-fns.bundle.min.js';
                adapterScript.onload = resolve;
                adapterScript.onerror = reject;
                document.head.appendChild(adapterScript);
            };
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    setupChartJSDefaults() {
        if (typeof Chart === 'undefined') return;

        // Register Arabic number formatting function globally
        window.formatArabicNumber = (value) => {
            if (!this.isRTL) return value;

            const arabicNumerals = {
                '0': '٠', '1': '١', '2': '٢', '3': '٣', '4': '٤',
                '5': '٥', '6': '٦', '7': '٧', '8': '٨', '9': '٩'
            };

            let formattedValue = String(value);
            if (typeof value === 'number') {
                formattedValue = value.toLocaleString('en-US', {
                    minimumFractionDigits: 0,
                    maximumFractionDigits: 2
                });
            }

            for (const [western, arabic] of Object.entries(arabicNumerals)) {
                formattedValue = formattedValue.replace(new RegExp(western, 'g'), arabic);
            }

            return formattedValue;
        };

        // Set Chart.js defaults
        Chart.defaults.font.family = this.chartDefaults.font.family;
        Chart.defaults.locale = this.language;

        // Set RTL defaults
        if (this.isRTL) {
            Chart.defaults.plugins.legend.rtl = true;
            Chart.defaults.plugins.tooltip.rtl = true;
        }
    }

    createContainer() {
        const container = document.getElementById(this.containerId);
        if (!container) {
            console.error(`Container with ID ${this.containerId} not found`);
            return;
        }

        container.innerHTML = `
            <div class="performance-visualizations-wrapper" dir="${this.isRTL ? 'rtl' : 'ltr'}">
                <div class="charts-header">
                    <div class="d-flex justify-content-between align-items-center mb-4">
                        <h3 class="charts-title">
                            ${this.isRTL ? 'مؤشرات الأداء' : 'Performance Analytics'}
                        </h3>
                        <div class="charts-controls">
                            <div class="btn-group" role="group">
                                <button type="button" class="btn btn-outline-primary btn-sm" id="refresh-all-charts">
                                    <i class="fa fa-sync-alt"></i>
                                    ${this.isRTL ? 'تحديث الكل' : 'Refresh All'}
                                </button>
                                <button type="button" class="btn btn-outline-secondary btn-sm" id="export-charts">
                                    <i class="fa fa-download"></i>
                                    ${this.isRTL ? 'تصدير' : 'Export'}
                                </button>
                                <button type="button" class="btn btn-outline-info btn-sm" id="charts-settings">
                                    <i class="fa fa-cog"></i>
                                    ${this.isRTL ? 'إعدادات' : 'Settings'}
                                </button>
                            </div>
                        </div>
                    </div>
                    
                    <div class="time-range-selector mb-3">
                        <div class="btn-group" role="group" aria-label="Time Range">
                            <input type="radio" class="btn-check" name="timeRange" id="time-7days" value="7days">
                            <label class="btn btn-outline-secondary btn-sm" for="time-7days">
                                ${this.isRTL ? '٧ أيام' : '7 Days'}
                            </label>
                            
                            <input type="radio" class="btn-check" name="timeRange" id="time-30days" value="30days" checked>
                            <label class="btn btn-outline-secondary btn-sm" for="time-30days">
                                ${this.isRTL ? '٣٠ يوم' : '30 Days'}
                            </label>
                            
                            <input type="radio" class="btn-check" name="timeRange" id="time-6months" value="6months">
                            <label class="btn btn-outline-secondary btn-sm" for="time-6months">
                                ${this.isRTL ? '٦ أشهر' : '6 Months'}
                            </label>
                        </div>
                    </div>
                </div>
                
                <div class="charts-grid" id="charts-grid">
                    <!-- Charts will be inserted here -->
                </div>
                
                <div class="charts-footer mt-4">
                    <div class="d-flex justify-content-between align-items-center">
                        <small class="text-muted">
                            ${this.isRTL ? 'آخر تحديث:' : 'Last Updated:'} 
                            <span id="charts-last-updated">--</span>
                        </small>
                        <div class="auto-refresh-status">
                            <span class="badge bg-success" id="auto-refresh-indicator">
                                <i class="fa fa-circle pulse"></i>
                                ${this.isRTL ? 'التحديث التلقائي مفعل' : 'Auto-refresh Active'}
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        `;

        this.bindEventListeners();
    }

    bindEventListeners() {
        // Refresh all charts
        document.getElementById('refresh-all-charts')?.addEventListener('click', () => {
            this.refreshAllCharts();
        });

        // Export charts
        document.getElementById('export-charts')?.addEventListener('click', () => {
            this.showExportDialog();
        });

        // Charts settings
        document.getElementById('charts-settings')?.addEventListener('click', () => {
            this.showSettingsDialog();
        });

        // Time range selection
        document.querySelectorAll('input[name="timeRange"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.changeTimeRange(e.target.value);
                }
            });
        });
    }

    async loadAllCharts() {
        try {
            // Show loading state
            this.showLoading();

            // Get all charts configuration
            const response = await frappe.call({
                method: 'universal_workshop.dashboard.performance_visualizations.get_all_charts_config',
                args: {
                    time_range: '30days'
                }
            });

            if (response.message && response.message.charts) {
                await this.renderAllCharts(response.message.charts);
                this.updateLastUpdated(response.message.last_updated);
            }
        } catch (error) {
            console.error('Failed to load charts:', error);
            this.showError('Failed to load performance charts');
        } finally {
            this.hideLoading();
        }
    }

    async renderAllCharts(chartsData) {
        const grid = document.getElementById('charts-grid');
        if (!grid) return;

        // Clear existing charts
        this.destroyAllCharts();
        grid.innerHTML = '';

        // Chart grid layout configuration
        const chartLayout = [
            { id: 'revenue_trend', size: 'col-12 col-lg-8', height: '400px' },
            { id: 'service_completion', size: 'col-12 col-lg-4', height: '400px' },
            { id: 'technician_performance', size: 'col-12 col-lg-6', height: '350px' },
            { id: 'customer_satisfaction', size: 'col-12 col-lg-6', height: '350px' },
            { id: 'inventory_turnover', size: 'col-12 col-lg-8', height: '300px' },
            { id: 'service_type_distribution', size: 'col-12 col-lg-4', height: '300px' },
            { id: 'monthly_targets', size: 'col-12', height: '400px' }
        ];

        for (const layout of chartLayout) {
            const chartData = chartsData[layout.id];
            if (chartData) {
                const chartElement = this.createChartElement(layout, chartData);
                grid.appendChild(chartElement);

                // Render chart after element is in DOM
                setTimeout(() => {
                    this.renderChart(layout.id, chartData);
                }, 100);
            }
        }
    }

    createChartElement(layout, chartData) {
        const chartContainer = document.createElement('div');
        chartContainer.className = layout.size + ' mb-4';

        chartContainer.innerHTML = `
            <div class="card chart-card h-100">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h6 class="card-title mb-0">${chartData.title}</h6>
                    <div class="chart-actions">
                        <button class="btn btn-sm btn-outline-secondary" onclick="window.performanceViz.refreshChart('${layout.id}')">
                            <i class="fa fa-sync-alt"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-primary" onclick="window.performanceViz.exportChart('${layout.id}')">
                            <i class="fa fa-download"></i>
                        </button>
                    </div>
                </div>
                <div class="card-body d-flex flex-column">
                    <div class="chart-container flex-grow-1" style="height: ${layout.height};">
                        <canvas id="chart-${layout.id}"></canvas>
                    </div>
                    <div class="chart-info mt-2">
                        <small class="text-muted">
                            ${this.isRTL ? 'آخر تحديث:' : 'Updated:'} 
                            <span class="chart-timestamp" id="timestamp-${layout.id}">--</span>
                        </small>
                    </div>
                </div>
            </div>
        `;

        return chartContainer;
    }

    renderChart(chartId, chartData) {
        const canvas = document.getElementById(`chart-${chartId}`);
        if (!canvas) return;

        const ctx = canvas.getContext('2d');

        // Destroy existing chart if it exists
        if (this.chartInstances.has(chartId)) {
            this.chartInstances.get(chartId).destroy();
        }

        let chartConfig;

        // Handle different chart types
        switch (chartData.type) {
            case 'gauge':
                chartConfig = this.createGaugeChart(chartData);
                break;
            case 'mixed':
                chartConfig = this.createMixedChart(chartData);
                break;
            default:
                chartConfig = this.createStandardChart(chartData);
                break;
        }

        // Create chart instance
        const chartInstance = new Chart(ctx, chartConfig);
        this.chartInstances.set(chartId, chartInstance);

        // Update timestamp
        this.updateChartTimestamp(chartId, chartData.last_updated);

        // Setup auto-refresh for this chart
        if (this.autoRefreshEnabled && chartData.refresh_interval) {
            this.setupChartAutoRefresh(chartId, chartData.refresh_interval);
        }
    }

    createStandardChart(chartData) {
        const config = {
            type: chartData.type,
            data: chartData.data,
            options: {
                ...this.chartDefaults,
                ...chartData.options,
                plugins: {
                    ...chartData.options.plugins,
                    tooltip: {
                        ...chartData.options.plugins?.tooltip,
                        callbacks: {
                            label: function (context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                label += window.formatArabicNumber(context.parsed.y || context.parsed);
                                return label;
                            }
                        }
                    }
                }
            }
        };

        // Handle RTL scaling for axes
        if (this.isRTL && config.options.scales) {
            Object.keys(config.options.scales).forEach(axisKey => {
                const axis = config.options.scales[axisKey];
                if (axis.ticks && axis.ticks.callback) {
                    // Convert string callback to function for RTL formatting
                    if (typeof axis.ticks.callback === 'string') {
                        axis.ticks.callback = function (value) {
                            return window.formatArabicNumber(value);
                        };
                    }
                }
            });
        }

        return config;
    }

    createGaugeChart(chartData) {
        const value = chartData.data.value || 0;
        const max = chartData.data.max || 100;
        const percentage = (value / max) * 180; // 180 degrees for semicircle

        return {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [value, max - value],
                    backgroundColor: [
                        chartData.data.color || '#28a745',
                        '#e9ecef'
                    ],
                    borderWidth: 0,
                    cutout: '75%'
                }]
            },
            options: {
                ...this.chartDefaults,
                circumference: 180,
                rotation: 270,
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: false }
                },
                onHover: (event, activeElements) => {
                    event.native.target.style.cursor = 'pointer';
                }
            },
            plugins: [{
                id: 'gaugeText',
                beforeDraw: (chart) => {
                    const { ctx, chartArea } = chart;
                    const centerX = (chartArea.left + chartArea.right) / 2;
                    const centerY = (chartArea.top + chartArea.bottom) / 2;

                    ctx.save();
                    ctx.font = 'bold 24px ' + this.chartDefaults.font.family;
                    ctx.fillStyle = '#333';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';

                    const displayValue = window.formatArabicNumber(value.toFixed(1)) + '%';
                    ctx.fillText(displayValue, centerX, centerY);

                    // Add label below
                    ctx.font = '14px ' + this.chartDefaults.font.family;
                    ctx.fillStyle = '#666';
                    ctx.fillText(chartData.title, centerX, centerY + 30);

                    ctx.restore();
                }
            }]
        };
    }

    createMixedChart(chartData) {
        return {
            type: 'bar',
            data: chartData.data,
            options: {
                ...this.chartDefaults,
                ...chartData.options,
                plugins: {
                    ...chartData.options.plugins,
                    tooltip: {
                        ...chartData.options.plugins?.tooltip,
                        callbacks: {
                            label: function (context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                label += window.formatArabicNumber(context.parsed.y);
                                return label;
                            }
                        }
                    }
                }
            }
        };
    }

    setupAutoRefresh() {
        // Clear existing intervals
        this.refreshIntervals.forEach(interval => clearInterval(interval));
        this.refreshIntervals.clear();

        if (!this.autoRefreshEnabled) return;

        // Setup global refresh interval
        const globalInterval = setInterval(() => {
            this.refreshAllCharts();
        }, this.defaultRefreshInterval);

        this.refreshIntervals.set('global', globalInterval);
    }

    setupChartAutoRefresh(chartId, interval) {
        if (!this.autoRefreshEnabled) return;

        // Clear existing interval for this chart
        if (this.refreshIntervals.has(chartId)) {
            clearInterval(this.refreshIntervals.get(chartId));
        }

        // Setup new interval
        const chartInterval = setInterval(() => {
            this.refreshChart(chartId);
        }, interval);

        this.refreshIntervals.set(chartId, chartInterval);
    }

    setupWebSocketUpdates() {
        // Setup WebSocket connection for real-time updates
        if (typeof frappe.realtime !== 'undefined') {
            frappe.realtime.on('dashboard_update', (data) => {
                if (data.chart_id && this.chartInstances.has(data.chart_id)) {
                    this.updateChartData(data.chart_id, data.chart_data);
                }
            });
        }
    }

    async refreshAllCharts() {
        try {
            const timeRange = document.querySelector('input[name="timeRange"]:checked')?.value || '30days';

            const response = await frappe.call({
                method: 'universal_workshop.dashboard.performance_visualizations.get_all_charts_config',
                args: { time_range: timeRange }
            });

            if (response.message && response.message.charts) {
                // Update existing charts with new data
                Object.entries(response.message.charts).forEach(([chartId, chartData]) => {
                    if (this.chartInstances.has(chartId)) {
                        this.updateChartData(chartId, chartData);
                    }
                });

                this.updateLastUpdated(response.message.last_updated);
            }
        } catch (error) {
            console.error('Failed to refresh charts:', error);
            this.showError('Failed to refresh charts');
        }
    }

    async refreshChart(chartId) {
        try {
            const timeRange = document.querySelector('input[name="timeRange"]:checked')?.value || '30days';

            const response = await frappe.call({
                method: 'universal_workshop.dashboard.performance_visualizations.refresh_chart_data',
                args: { chart_id: chartId, time_range: timeRange }
            });

            if (response.message && response.message.data) {
                this.updateChartData(chartId, response.message);
            }
        } catch (error) {
            console.error(`Failed to refresh chart ${chartId}:`, error);
        }
    }

    updateChartData(chartId, chartData) {
        const chartInstance = this.chartInstances.get(chartId);
        if (!chartInstance) return;

        // Update chart data
        chartInstance.data = chartData.data;
        chartInstance.update('active');

        // Update timestamp
        this.updateChartTimestamp(chartId, chartData.last_updated);
    }

    async changeTimeRange(timeRange) {
        try {
            this.showLoading();

            const response = await frappe.call({
                method: 'universal_workshop.dashboard.performance_visualizations.get_all_charts_config',
                args: { time_range: timeRange }
            });

            if (response.message && response.message.charts) {
                Object.entries(response.message.charts).forEach(([chartId, chartData]) => {
                    if (this.chartInstances.has(chartId)) {
                        this.updateChartData(chartId, chartData);
                    }
                });

                this.updateLastUpdated(response.message.last_updated);
            }
        } catch (error) {
            console.error('Failed to change time range:', error);
            this.showError('Failed to update charts');
        } finally {
            this.hideLoading();
        }
    }

    updateLastUpdated(timestamp) {
        const element = document.getElementById('charts-last-updated');
        if (element && timestamp) {
            const date = new Date(timestamp);
            element.textContent = date.toLocaleString(this.language);
        }
    }

    updateChartTimestamp(chartId, timestamp) {
        const element = document.getElementById(`timestamp-${chartId}`);
        if (element && timestamp) {
            const date = new Date(timestamp);
            element.textContent = date.toLocaleTimeString(this.language);
        }
    }

    async exportChart(chartId) {
        try {
            const response = await frappe.call({
                method: 'universal_workshop.dashboard.performance_visualizations.get_chart_export_data',
                args: {
                    chart_id: chartId,
                    export_format: 'pdf'
                }
            });

            if (response.message && response.message.pdf_url) {
                window.open(response.message.pdf_url, '_blank');
            }
        } catch (error) {
            console.error(`Failed to export chart ${chartId}:`, error);
            this.showError('Failed to export chart');
        }
    }

    showExportDialog() {
        const dialog = new frappe.ui.Dialog({
            title: this.isRTL ? 'تصدير المخططات' : 'Export Charts',
            fields: [
                {
                    fieldtype: 'Select',
                    fieldname: 'export_format',
                    label: this.isRTL ? 'تنسيق التصدير' : 'Export Format',
                    options: [
                        { value: 'pdf', label: 'PDF' },
                        { value: 'excel', label: 'Excel' },
                        { value: 'png', label: 'PNG Images' }
                    ],
                    default: 'pdf'
                },
                {
                    fieldtype: 'MultiSelectPills',
                    fieldname: 'chart_selection',
                    label: this.isRTL ? 'اختيار المخططات' : 'Select Charts',
                    options: Array.from(this.chartInstances.keys()).map(id => ({
                        value: id,
                        label: this.getChartTitle(id)
                    }))
                }
            ],
            primary_action_label: this.isRTL ? 'تصدير' : 'Export',
            primary_action: (values) => {
                this.executeExport(values.export_format, values.chart_selection);
                dialog.hide();
            }
        });

        dialog.show();
    }

    showSettingsDialog() {
        const dialog = new frappe.ui.Dialog({
            title: this.isRTL ? 'إعدادات المخططات' : 'Chart Settings',
            fields: [
                {
                    fieldtype: 'Check',
                    fieldname: 'auto_refresh',
                    label: this.isRTL ? 'التحديث التلقائي' : 'Auto Refresh',
                    default: this.autoRefreshEnabled
                },
                {
                    fieldtype: 'Select',
                    fieldname: 'refresh_interval',
                    label: this.isRTL ? 'فترة التحديث' : 'Refresh Interval',
                    options: [
                        { value: 60000, label: this.isRTL ? 'دقيقة واحدة' : '1 Minute' },
                        { value: 300000, label: this.isRTL ? '٥ دقائق' : '5 Minutes' },
                        { value: 600000, label: this.isRTL ? '١٠ دقائق' : '10 Minutes' },
                        { value: 1800000, label: this.isRTL ? '٣٠ دقيقة' : '30 Minutes' }
                    ],
                    default: this.defaultRefreshInterval
                }
            ],
            primary_action_label: this.isRTL ? 'حفظ' : 'Save',
            primary_action: (values) => {
                this.updateSettings(values);
                dialog.hide();
            }
        });

        dialog.show();
    }

    updateSettings(settings) {
        this.autoRefreshEnabled = settings.auto_refresh;
        this.defaultRefreshInterval = settings.refresh_interval;

        // Update auto-refresh
        if (this.autoRefreshEnabled) {
            this.setupAutoRefresh();
            document.getElementById('auto-refresh-indicator').className = 'badge bg-success';
            document.getElementById('auto-refresh-indicator').innerHTML = `
                <i class="fa fa-circle pulse"></i>
                ${this.isRTL ? 'التحديث التلقائي مفعل' : 'Auto-refresh Active'}
            `;
        } else {
            this.refreshIntervals.forEach(interval => clearInterval(interval));
            this.refreshIntervals.clear();
            document.getElementById('auto-refresh-indicator').className = 'badge bg-secondary';
            document.getElementById('auto-refresh-indicator').innerHTML = `
                <i class="fa fa-circle"></i>
                ${this.isRTL ? 'التحديث التلقائي معطل' : 'Auto-refresh Disabled'}
            `;
        }
    }

    getChartTitle(chartId) {
        const chartInstance = this.chartInstances.get(chartId);
        return chartInstance?.options?.plugins?.title?.text || chartId;
    }

    showLoading() {
        const grid = document.getElementById('charts-grid');
        if (grid) {
            grid.classList.add('loading');
            grid.style.opacity = '0.5';
        }
    }

    hideLoading() {
        const grid = document.getElementById('charts-grid');
        if (grid) {
            grid.classList.remove('loading');
            grid.style.opacity = '1';
        }
    }

    showError(message) {
        frappe.msgprint({
            title: this.isRTL ? 'خطأ' : 'Error',
            message: message,
            indicator: 'red'
        });
    }

    destroyAllCharts() {
        this.chartInstances.forEach(chart => chart.destroy());
        this.chartInstances.clear();

        this.refreshIntervals.forEach(interval => clearInterval(interval));
        this.refreshIntervals.clear();
    }

    destroy() {
        this.destroyAllCharts();

        // Remove global reference
        delete window.performanceViz;
    }
}

// Initialize when DOM is ready
frappe.ready(() => {
    // Create global instance
    window.performanceViz = new PerformanceVisualizationManager({
        containerId: 'performance-charts-container',
        autoRefresh: true,
        refreshInterval: 300000 // 5 minutes
    });
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PerformanceVisualizationManager;
} 