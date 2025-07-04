/**
 * Progress Tracking Dashboard for Universal Workshop ERP
 * Real-time service order progress tracking with Arabic RTL support
 */

class ProgressTrackingDashboard {
    constructor(container, options = {}) {
        this.container = container;
        this.options = {
            service_order: null,
            refresh_interval: 30000,
            enable_realtime: true,
            language: frappe.boot.lang || 'en',
            ...options
        };
        
        this.progress_data = null;
        this.is_arabic = this.options.language === 'ar';
        this.init();
    }

    async init() {
        this.setup_container();
        await this.load_progress_data();
        this.render_dashboard();
    }

    setup_container() {
        this.container.addClass('progress-tracking-dashboard');
        if (this.is_arabic) {
            this.container.addClass('rtl-layout');
        }
        
        this.container.html(`
            <div class="dashboard-header">
                <h3>${this.is_arabic ? 'لوحة تتبع التقدم' : 'Progress Tracking Dashboard'}</h3>
                <button class="btn btn-primary refresh-btn">
                    <i class="fa fa-refresh"></i> ${this.is_arabic ? 'تحديث' : 'Refresh'}
                </button>
            </div>
            <div class="dashboard-content">
                <div class="loading">Loading...</div>
            </div>
        `);

        this.container.find('.refresh-btn').on('click', () => this.refresh_dashboard());
    }

    async load_progress_data() {
        try {
            const response = await frappe.call({
                method: 'universal_workshop.sales_service.progress_tracking.get_progress_dashboard',
                args: { service_order: this.options.service_order }
            });

            if (response.message && response.message.status === 'success') {
                this.progress_data = response.message.data;
            }
        } catch (error) {
            console.error('Error loading progress data:', error);
        }
    }

    render_dashboard() {
        if (!this.progress_data) return;

        const content = this.container.find('.dashboard-content');
        content.html(`
            <div class="progress-overview">
                ${this.render_overview_cards()}
            </div>
            <div class="operations-list">
                ${this.render_operations_list()}
            </div>
        `);
    }

    render_overview_cards() {
        const { overall_progress, current_status } = this.progress_data;
        
        return `
            <div class="overview-cards">
                <div class="card progress-card">
                    <h5>${this.is_arabic ? 'التقدم العام' : 'Overall Progress'}</h5>
                    <div class="progress-circle">
                        <span>${overall_progress.percentage}%</span>
                    </div>
                    <p>${this.is_arabic ? current_status.label_ar : current_status.label}</p>
                </div>
            </div>
        `;
    }

    render_operations_list() {
        const operations = this.progress_data.operations || [];
        
        return `
            <div class="operations-section">
                <h4>${this.is_arabic ? 'قائمة العمليات' : 'Operations List'}</h4>
                ${operations.map(op => this.render_operation_item(op)).join('')}
            </div>
        `;
    }

    render_operation_item(operation) {
        return `
            <div class="operation-item">
                <div class="operation-info">
                    <h6>${this.is_arabic && operation.operation_name_ar ? operation.operation_name_ar : operation.operation_name}</h6>
                    <p>Status: ${operation.status}</p>
                    <div class="progress">
                        <div class="progress-bar" style="width: ${operation.progress_percentage}%"></div>
                    </div>
                    <span>${operation.progress_percentage}%</span>
                </div>
            </div>
        `;
    }

    async refresh_dashboard() {
        await this.load_progress_data();
        this.render_dashboard();
    }
}

// Global function to initialize dashboard
window.init_progress_tracking_dashboard = function(container, options) {
    return new ProgressTrackingDashboard(container, options);
};
