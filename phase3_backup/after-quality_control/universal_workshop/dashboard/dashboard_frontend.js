/**
 * Universal Workshop ERP - Dashboard Frontend
 * Responsive dashboard with Arabic RTL support and real-time updates
 */

class WorkshopDashboard {
    constructor() {
        this.data = {};
        this.widgets = {};
        this.refreshIntervals = {};
        this.isRTL = document.documentElement.dir === 'rtl';
        this.language = frappe.boot.lang || 'en';
        this.settings = {};
        
        this.init();
    }
    
    async init() {
        try {
            // Load initial dashboard data
            await this.loadDashboardData();
            
            // Create dashboard layout
            this.createLayout();
            
            // Initialize widgets
            this.initializeWidgets();
            
            // Setup real-time updates
            this.setupRealTimeUpdates();
            
            // Setup auto-refresh
            this.setupAutoRefresh();
            
            console.log('Workshop Dashboard initialized successfully');
        } catch (error) {
            console.error('Dashboard initialization failed:', error);
            this.showError('Failed to initialize dashboard');
        }
    }
    
    async loadDashboardData() {
        const response = await frappe.call({
            method: 'universal_workshop.dashboard.workshop_dashboard.get_dashboard_data',
            freeze: true,
            freeze_message: this.language === 'ar' ? 'جاري تحميل لوحة التحكم...' : 'Loading Dashboard...'
        });
        
        if (response.message) {
            this.data = response.message;
            this.settings = this.data.settings || {};
        }
    }
    
    createLayout() {
        const container = document.querySelector('.layout-main-section');
        if (!container) return;
        
        // Clear existing content
        container.innerHTML = '';
        
        // Create dashboard wrapper
        const dashboardWrapper = document.createElement('div');
        dashboardWrapper.className = 'workshop-dashboard';
        dashboardWrapper.dir = this.data.layout?.direction || 'ltr';
        
        // Create dashboard HTML structure
        dashboardWrapper.innerHTML = `
            <div class="dashboard-header">
                <div class="container-fluid">
                    <div class="row align-items-center">
                        <div class="col-md-6">
                            <h1 class="dashboard-title">
                                ${this.language === 'ar' ? 'لوحة تحكم الورشة' : 'Workshop Dashboard'}
                            </h1>
                        </div>
                        <div class="col-md-6 text-end">
                            <div class="dashboard-controls">
                                <button class="btn btn-sm btn-outline-primary refresh-btn">
                                    <i class="fa fa-sync-alt"></i>
                                    ${this.language === 'ar' ? 'تحديث' : 'Refresh'}
                                </button>
                                <button class="btn btn-sm btn-outline-secondary settings-btn">
                                    <i class="fa fa-cog"></i>
                                    ${this.language === 'ar' ? 'إعدادات' : 'Settings'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="dashboard-content">
                <div class="container-fluid">
                    <!-- KPI Cards Row -->
                    <div class="row kpi-cards-row" id="kpi-cards">
                        <!-- KPI cards will be inserted here -->
                    </div>
                    
                    <!-- Main Widgets Row -->
                    <div class="row widgets-row" id="main-widgets">
                        <!-- Main widgets will be inserted here -->
                    </div>
                    
                    <!-- Secondary Widgets Row -->
                    <div class="row secondary-widgets-row" id="secondary-widgets">
                        <!-- Secondary widgets will be inserted here -->
                    </div>
                </div>
            </div>
            
            <div class="dashboard-footer">
                <div class="container-fluid">
                    <div class="row">
                        <div class="col-md-6">
                            <span class="last-update">
                                ${this.language === 'ar' ? 'آخر تحديث:' : 'Last Updated:'} 
                                <span id="last-update-time">${this.formatDateTime(new Date())}</span>
                            </span>
                        </div>
                        <div class="col-md-6 text-end">
                            <span class="system-status">
                                <i class="fa fa-circle text-success"></i>
                                ${this.language === 'ar' ? 'النظام متصل' : 'System Online'}
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        container.appendChild(dashboardWrapper);
        
        // Bind event listeners
        this.bindEventListeners();
    }
    
    initializeWidgets() {
        // Initialize KPI cards
        this.createKPICards();
        
        // Initialize main widgets
        this.createMainWidgets();
        
        // Initialize secondary widgets
        this.createSecondaryWidgets();
    }
    
    createKPICards() {
        const kpiContainer = document.getElementById('kpi-cards');
        if (!kpiContainer || !this.data.kpis) return;
        
        kpiContainer.innerHTML = '';
        
        this.data.kpis.forEach(kpi => {
            const cardHTML = this.createKPICardHTML(kpi);
            kpiContainer.insertAdjacentHTML('beforeend', cardHTML);
        });
    }
    
    createKPICardHTML(kpi) {
        const trendIcon = kpi.trend ? 
            `<i class="fa fa-arrow-${kpi.trend.direction} text-${kpi.trend.color}"></i>` : '';
        
        const trendText = kpi.trend ? 
            `<small class="text-${kpi.trend.color}">
                ${trendIcon} ${kpi.trend.percentage.toFixed(1)}%
            </small>` : '';
        
        const formattedValue = this.formatValue(kpi.value, kpi.format, kpi.currency);
        
        return `
            <div class="${kpi.grid_size}">
                <div class="card kpi-card border-${kpi.color}" data-kpi-id="${kpi.id}">
                    <div class="card-body">
                        <div class="d-flex align-items-center">
                            <div class="kpi-icon text-${kpi.color}">
                                <i class="fa ${kpi.icon}"></i>
                            </div>
                            <div class="kpi-content flex-grow-1 ${this.isRTL ? 'me-3' : 'ms-3'}">
                                <h6 class="kpi-title text-muted mb-1">${kpi.title}</h6>
                                <h4 class="kpi-value mb-0">${formattedValue}</h4>
                                ${kpi.subtitle ? `<small class="text-muted">${kpi.subtitle}</small>` : ''}
                                ${trendText}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    createMainWidgets() {
        const widgetsContainer = document.getElementById('main-widgets');
        if (!widgetsContainer || !this.data.widgets) return;
        
        // Filter main widgets (service board, quick actions)
        const mainWidgets = this.data.widgets.filter(w => 
            ['service_status_board', 'quick_actions'].includes(w.id)
        );
        
        widgetsContainer.innerHTML = '';
        
        mainWidgets.forEach(widget => {
            const widgetHTML = this.createWidgetHTML(widget);
            widgetsContainer.insertAdjacentHTML('beforeend', widgetHTML);
            
            // Initialize widget-specific functionality
            this.initializeWidget(widget);
        });
    }
    
    createSecondaryWidgets() {
        const widgetsContainer = document.getElementById('secondary-widgets');
        if (!widgetsContainer || !this.data.widgets) return;
        
        // Filter secondary widgets (charts, activities)
        const secondaryWidgets = this.data.widgets.filter(w => 
            !['service_status_board', 'quick_actions'].includes(w.id)
        );
        
        widgetsContainer.innerHTML = '';
        
        secondaryWidgets.forEach(widget => {
            const widgetHTML = this.createWidgetHTML(widget);
            widgetsContainer.insertAdjacentHTML('beforeend', widgetHTML);
            
            // Initialize widget-specific functionality
            this.initializeWidget(widget);
        });
    }
    
    createWidgetHTML(widget) {
        return `
            <div class="${widget.grid_size}">
                <div class="card widget-card" data-widget-id="${widget.id}">
                    <div class="card-header">
                        <h6 class="card-title mb-0">${widget.title}</h6>
                        <div class="card-actions">
                            <button class="btn btn-sm btn-outline-secondary refresh-widget" 
                                    data-widget-id="${widget.id}">
                                <i class="fa fa-sync-alt"></i>
                            </button>
                        </div>
                    </div>
                    <div class="card-body widget-content" style="height: ${widget.height}">
                        <div class="widget-loading text-center">
                            <div class="spinner-border text-primary" role="status">
                                <span class="visually-hidden">
                                    ${this.language === 'ar' ? 'جاري التحميل...' : 'Loading...'}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    async initializeWidget(widget) {
        const widgetElement = document.querySelector(`[data-widget-id="${widget.id}"]`);
        if (!widgetElement) return;
        
        const contentElement = widgetElement.querySelector('.widget-content');
        
        try {
            switch (widget.type) {
                case 'kanban':
                    await this.initializeKanbanWidget(widget, contentElement);
                    break;
                case 'action_grid':
                    await this.initializeActionGridWidget(widget, contentElement);
                    break;
                case 'chart':
                    await this.initializeChartWidget(widget, contentElement);
                    break;
                case 'gauge':
                    await this.initializeGaugeWidget(widget, contentElement);
                    break;
                case 'timeline':
                    await this.initializeTimelineWidget(widget, contentElement);
                    break;
                default:
                    contentElement.innerHTML = `
                        <div class="alert alert-warning">
                            ${this.language === 'ar' ? 'نوع الودجت غير مدعوم' : 'Unsupported widget type'}
                        </div>
                    `;
            }
            
            // Setup auto-refresh for widget
            if (widget.refresh_interval) {
                this.setupWidgetRefresh(widget);
            }
            
        } catch (error) {
            console.error(`Failed to initialize widget ${widget.id}:`, error);
            contentElement.innerHTML = `
                <div class="alert alert-danger">
                    ${this.language === 'ar' ? 'فشل في تحميل الودجت' : 'Failed to load widget'}
                </div>
            `;
        }
    }
    
    async initializeKanbanWidget(widget, container) {
        // Create Kanban board for service orders
        container.innerHTML = `
            <div class="kanban-board" dir="${this.isRTL ? 'rtl' : 'ltr'}">
                <div class="kanban-columns">
                    ${widget.columns.map(col => `
                        <div class="kanban-column" data-status="${col.id}">
                            <div class="kanban-header bg-${col.color}">
                                <i class="fa ${col.icon}"></i>
                                <span class="column-title">${col.title}</span>
                                <span class="column-count badge bg-white text-dark">0</span>
                            </div>
                            <div class="kanban-items" data-status="${col.id}">
                                <!-- Service order cards will be loaded here -->
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        
        // Load service orders data
        await this.loadKanbanData(widget);
    }
    
    async initializeActionGridWidget(widget, container) {
        // Create quick actions grid
        const actionsHTML = widget.actions.map(action => `
            <div class="col-md-6 col-lg-12 mb-3">
                <button class="btn btn-${action.color} btn-lg w-100 action-btn" 
                        data-action="${action.action}">
                    <i class="fa ${action.icon}"></i>
                    <span class="action-title">${action.title}</span>
                </button>
            </div>
        `).join('');
        
        container.innerHTML = `
            <div class="actions-grid">
                <div class="row">
                    ${actionsHTML}
                </div>
            </div>
        `;
        
        // Bind action handlers
        this.bindActionHandlers(container);
    }
    
    async initializeChartWidget(widget, container) {
        // Placeholder for chart initialization
        container.innerHTML = `
            <div class="chart-container">
                <canvas id="chart-${widget.id}"></canvas>
            </div>
        `;
        
        // Chart implementation will be added in next subtask
        console.log(`Chart widget ${widget.id} placeholder created`);
    }
    
    async initializeGaugeWidget(widget, container) {
        // Placeholder for gauge initialization
        container.innerHTML = `
            <div class="gauge-container text-center">
                <div class="gauge-placeholder">
                    <i class="fa fa-tachometer-alt fa-3x text-muted"></i>
                    <p class="mt-2 text-muted">
                        ${this.language === 'ar' ? 'مقياس رضا العملاء' : 'Customer Satisfaction Gauge'}
                    </p>
                </div>
            </div>
        `;
        
        console.log(`Gauge widget ${widget.id} placeholder created`);
    }
    
    async initializeTimelineWidget(widget, container) {
        // Create timeline for recent activities
        container.innerHTML = `
            <div class="timeline-container">
                <div class="timeline-items">
                    <!-- Timeline items will be loaded here -->
                </div>
            </div>
        `;
        
        await this.loadTimelineData(widget, container);
    }
    
    async loadKanbanData(widget) {
        // Simplified kanban data loading
        const columns = document.querySelectorAll('.kanban-items');
        columns.forEach(column => {
            const status = column.dataset.status;
            column.innerHTML = `
                <div class="kanban-item">
                    <div class="service-card">
                        <h6>Sample Service Order</h6>
                        <p class="text-muted">Customer: Ahmed Al-Rashid</p>
                        <p class="text-muted">Vehicle: Toyota Camry 2020</p>
                        <span class="badge bg-primary">Oil Change</span>
                    </div>
                </div>
            `;
        });
    }
    
    async loadTimelineData(widget, container) {
        // Simplified timeline data
        const timelineHTML = `
            <div class="timeline-item">
                <div class="timeline-marker bg-success"></div>
                <div class="timeline-content">
                    <h6>Service Order Completed</h6>
                    <p class="text-muted">Toyota Camry - Oil Change</p>
                    <small class="text-muted">5 minutes ago</small>
                </div>
            </div>
            <div class="timeline-item">
                <div class="timeline-marker bg-warning"></div>
                <div class="timeline-content">
                    <h6>New Customer Registered</h6>
                    <p class="text-muted">Ahmed Al-Rashid</p>
                    <small class="text-muted">15 minutes ago</small>
                </div>
            </div>
        `;
        
        container.querySelector('.timeline-items').innerHTML = timelineHTML;
    }
    
    bindEventListeners() {
        // Refresh button
        document.querySelector('.refresh-btn')?.addEventListener('click', () => {
            this.refreshDashboard();
        });
        
        // Settings button
        document.querySelector('.settings-btn')?.addEventListener('click', () => {
            this.showSettingsDialog();
        });
        
        // Widget refresh buttons
        document.querySelectorAll('.refresh-widget').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const widgetId = e.target.closest('[data-widget-id]').dataset.widgetId;
                this.refreshWidget(widgetId);
            });
        });
    }
    
    bindActionHandlers(container) {
        container.querySelectorAll('.action-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = e.currentTarget.dataset.action;
                this.executeAction(action);
            });
        });
    }
    
    executeAction(action) {
        switch (action) {
            case 'create_service_order':
                frappe.new_doc('Work Order');
                break;
            case 'register_customer':
                frappe.new_doc('Customer');
                break;
            case 'inventory_adjustment':
                frappe.new_doc('Stock Entry');
                break;
            case 'process_payment':
                frappe.new_doc('Payment Entry');
                break;
            default:
                frappe.msgprint(`Action ${action} not implemented yet`);
        }
    }
    
    setupRealTimeUpdates() {
        // Setup WebSocket listeners for real-time updates
        if (frappe.realtime) {
            frappe.realtime.on('dashboard_update', (data) => {
                this.handleRealTimeUpdate(data);
            });
            
            frappe.realtime.on('service_order_update', (data) => {
                this.updateKanbanBoard(data);
            });
        }
    }
    
    setupAutoRefresh() {
        if (this.settings.auto_refresh) {
            const interval = (this.settings.refresh_interval || 30) * 1000;
            
            this.refreshIntervals.main = setInterval(() => {
                this.refreshKPICards();
            }, interval);
        }
    }
    
    setupWidgetRefresh(widget) {
        const interval = widget.refresh_interval * 1000;
        
        this.refreshIntervals[widget.id] = setInterval(() => {
            this.refreshWidget(widget.id);
        }, interval);
    }
    
    async refreshDashboard() {
        try {
            await this.loadDashboardData();
            this.createKPICards();
            this.updateLastRefreshTime();
            
            frappe.show_alert({
                message: this.language === 'ar' ? 'تم تحديث لوحة التحكم' : 'Dashboard refreshed',
                indicator: 'green'
            });
        } catch (error) {
            console.error('Dashboard refresh failed:', error);
            frappe.show_alert({
                message: this.language === 'ar' ? 'فشل في تحديث لوحة التحكم' : 'Dashboard refresh failed',
                indicator: 'red'
            });
        }
    }
    
    async refreshKPICards() {
        try {
            const response = await frappe.call({
                method: 'universal_workshop.dashboard.workshop_dashboard.get_kpi_metrics'
            });
            
            if (response.message) {
                this.data.kpis = response.message;
                this.createKPICards();
                this.updateLastRefreshTime();
            }
        } catch (error) {
            console.error('KPI refresh failed:', error);
        }
    }
    
    async refreshWidget(widgetId) {
        const widgetElement = document.querySelector(`[data-widget-id="${widgetId}"]`);
        if (!widgetElement) return;
        
        const contentElement = widgetElement.querySelector('.widget-content');
        contentElement.innerHTML = `
            <div class="widget-loading text-center">
                <div class="spinner-border text-primary" role="status"></div>
            </div>
        `;
        
        // Find widget configuration
        const widget = this.data.widgets.find(w => w.id === widgetId);
        if (widget) {
            await this.initializeWidget(widget);
        }
    }
    
    handleRealTimeUpdate(data) {
        // Handle real-time updates from server
        if (data.type === 'kpi_update') {
            this.refreshKPICards();
        } else if (data.type === 'widget_update') {
            this.refreshWidget(data.widget_id);
        }
    }
    
    updateKanbanBoard(data) {
        // Update Kanban board with real-time service order changes
        // Implementation will be enhanced in next subtask
        console.log('Kanban update:', data);
    }
    
    formatValue(value, format, currency) {
        switch (format) {
            case 'currency':
                return this.formatCurrency(value, currency);
            case 'percentage':
                return `${value}%`;
            case 'number':
                return this.formatNumber(value);
            default:
                return value;
        }
    }
    
    formatCurrency(amount, currency = 'OMR') {
        const formatter = new Intl.NumberFormat(this.language === 'ar' ? 'ar-OM' : 'en-OM', {
            style: 'currency',
            currency: currency,
            minimumFractionDigits: 2
        });
        return formatter.format(amount);
    }
    
    formatNumber(number) {
        const formatter = new Intl.NumberFormat(this.language === 'ar' ? 'ar-OM' : 'en-OM');
        return formatter.format(number);
    }
    
    formatDateTime(date) {
        const formatter = new Intl.DateTimeFormat(this.language === 'ar' ? 'ar-OM' : 'en-OM', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        return formatter.format(date);
    }
    
    updateLastRefreshTime() {
        const timeElement = document.getElementById('last-update-time');
        if (timeElement) {
            timeElement.textContent = this.formatDateTime(new Date());
        }
    }
    
    showSettingsDialog() {
        // Dashboard settings dialog
        const dialog = new frappe.ui.Dialog({
            title: this.language === 'ar' ? 'إعدادات لوحة التحكم' : 'Dashboard Settings',
            fields: [
                {
                    fieldtype: 'Check',
                    fieldname: 'auto_refresh',
                    label: this.language === 'ar' ? 'التحديث التلقائي' : 'Auto Refresh',
                    default: this.settings.auto_refresh
                },
                {
                    fieldtype: 'Int',
                    fieldname: 'refresh_interval',
                    label: this.language === 'ar' ? 'فترة التحديث (ثانية)' : 'Refresh Interval (seconds)',
                    default: this.settings.refresh_interval || 30
                },
                {
                    fieldtype: 'Check',
                    fieldname: 'sound_notifications',
                    label: this.language === 'ar' ? 'التنبيهات الصوتية' : 'Sound Notifications',
                    default: this.settings.sound_notifications
                }
            ],
            primary_action_label: this.language === 'ar' ? 'حفظ' : 'Save',
            primary_action: (values) => {
                this.updateSettings(values);
                dialog.hide();
            }
        });
        
        dialog.show();
    }
    
    updateSettings(newSettings) {
        this.settings = { ...this.settings, ...newSettings };
        
        // Clear existing intervals
        Object.values(this.refreshIntervals).forEach(interval => {
            clearInterval(interval);
        });
        this.refreshIntervals = {};
        
        // Setup new auto-refresh
        this.setupAutoRefresh();
        
        frappe.show_alert({
            message: this.language === 'ar' ? 'تم حفظ الإعدادات' : 'Settings saved',
            indicator: 'green'
        });
    }
    
    showError(message) {
        frappe.show_alert({
            message: message,
            indicator: 'red'
        });
    }
    
    destroy() {
        // Cleanup intervals and event listeners
        Object.values(this.refreshIntervals).forEach(interval => {
            clearInterval(interval);
        });
        
        if (frappe.realtime) {
            frappe.realtime.off('dashboard_update');
            frappe.realtime.off('service_order_update');
        }
    }
}

// Initialize dashboard when page loads
frappe.ready(() => {
    if (frappe.get_route()[0] === 'workshop-dashboard') {
        window.workshopDashboard = new WorkshopDashboard();
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.workshopDashboard) {
        window.workshopDashboard.destroy();
    }
}); 