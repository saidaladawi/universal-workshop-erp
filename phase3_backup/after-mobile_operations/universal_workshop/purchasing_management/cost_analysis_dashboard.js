/**
 * Cost Analysis Dashboard JavaScript Components
 * Universal Workshop ERP - ERPNext v15 Analytics with Arabic Localization
 */

frappe.ready(() => {
    // Initialize dashboard when page is ready
    if (window.location.pathname.includes('cost-analysis-dashboard')) {
        new CostAnalysisDashboard();
    }
});

class CostAnalysisDashboard {
    constructor() {
        this.filters = {};
        this.charts = {};
        this.currency = frappe.defaults.get_global_default("currency") || "OMR";
        this.language = frappe.boot.lang || 'en';

        this.init();
    }

    init() {
        this.setup_page();
        this.setup_filters();
        this.setup_number_cards();
        this.setup_charts();
        this.load_dashboard_data();
    }

    setup_page() {
        // Set page title and breadcrumbs
        frappe.ui.set_title(__('Cost Analysis Dashboard'));

        // Apply RTL if Arabic
        if (this.language === 'ar') {
            $('body').addClass('rtl-layout');
            $('.main-wrapper').css('direction', 'rtl');
        }

        // Create main dashboard container
        const dashboard_html = `
            <div class="cost-analysis-dashboard">
                <div class="dashboard-header">
                    <h2 class="dashboard-title">
                        ${this.language === 'ar' ? 'تحليل تكاليف المشتريات' : __('Procurement Cost Analysis')}
                    </h2>
                    <div class="dashboard-actions">
                        <button class="btn btn-primary btn-export" data-format="excel">
                            <i class="fa fa-download"></i> ${__('Export Excel')}
                        </button>
                        <button class="btn btn-secondary btn-export" data-format="pdf">
                            <i class="fa fa-file-pdf-o"></i> ${__('Export PDF')}
                        </button>
                        <button class="btn btn-success btn-refresh">
                            <i class="fa fa-refresh"></i> ${__('Refresh')}
                        </button>
                    </div>
                </div>
                <div class="dashboard-filters row"></div>
                <div class="dashboard-cards row"></div>
                <div class="dashboard-charts row"></div>
            </div>
        `;

        $('.page-body').html(dashboard_html);

        // Bind action buttons
        this.bind_actions();
    }

    setup_filters() {
        const filters_config = [
            {
                fieldname: 'from_date',
                label: this.language === 'ar' ? 'من تاريخ' : __('From Date'),
                fieldtype: 'Date',
                default: frappe.datetime.add_months(frappe.datetime.get_today(), -6),
                reqd: 1
            },
            {
                fieldname: 'to_date',
                label: this.language === 'ar' ? 'إلى تاريخ' : __('To Date'),
                fieldtype: 'Date',
                default: frappe.datetime.get_today(),
                reqd: 1
            },
            {
                fieldname: 'supplier',
                label: this.language === 'ar' ? 'المورد' : __('Supplier'),
                fieldtype: 'Link',
                options: 'Supplier'
            },
            {
                fieldname: 'item_group',
                label: this.language === 'ar' ? 'مجموعة المواد' : __('Item Group'),
                fieldtype: 'Link',
                options: 'Item Group'
            }
        ];

        let filter_html = '<div class="col-12 filter-section">';
        filter_html += '<div class="row">';

        filters_config.forEach((filter, index) => {
            const col_class = index < 2 ? 'col-md-3' : 'col-md-3';
            filter_html += `
                <div class="${col_class}">
                    <div class="form-group">
                        <label class="control-label">${filter.label}${filter.reqd ? ' *' : ''}</label>
                        <input type="${filter.fieldtype === 'Date' ? 'date' : 'text'}" 
                               class="form-control filter-input" 
                               data-fieldname="${filter.fieldname}"
                               data-fieldtype="${filter.fieldtype}"
                               data-options="${filter.options || ''}"
                               value="${filter.default || ''}"
                               ${this.language === 'ar' ? 'dir="rtl"' : ''}>
                    </div>
                </div>
            `;
        });

        filter_html += '</div>';
        filter_html += `<div class="row">
            <div class="col-12">
                <button class="btn btn-primary btn-apply-filters">
                    <i class="fa fa-filter"></i> ${__('Apply Filters')}
                </button>
                <button class="btn btn-secondary btn-reset-filters">
                    <i class="fa fa-undo"></i> ${__('Reset')}
                </button>
            </div>
        </div>`;
        filter_html += '</div>';

        $('.dashboard-filters').html(filter_html);

        // Set up link fields
        this.setup_link_fields();

        // Bind filter events
        this.bind_filter_events();
    }

    setup_link_fields() {
        $('.filter-input[data-fieldtype="Link"]').each((index, input) => {
            const $input = $(input);
            const options = $input.data('options');

            if (options) {
                $input.autocomplete({
                    source: (request, response) => {
                        frappe.call({
                            method: 'frappe.desk.search.search_link',
                            args: {
                                doctype: options,
                                txt: request.term
                            },
                            callback: (r) => {
                                if (r.message) {
                                    response(r.message.map(item => ({
                                        label: item.description || item.value,
                                        value: item.value
                                    })));
                                }
                            }
                        });
                    },
                    minLength: 1,
                    select: (event, ui) => {
                        $input.val(ui.item.value);
                        return false;
                    }
                });
            }
        });
    }

    setup_number_cards() {
        const cards_config = [
            {
                name: 'total_spend',
                label: this.language === 'ar' ? 'إجمالي الإنفاق' : __('Total Spend'),
                icon: 'fa fa-money',
                color: '#3498db'
            },
            {
                name: 'active_suppliers',
                label: this.language === 'ar' ? 'الموردون النشطون' : __('Active Suppliers'),
                icon: 'fa fa-users',
                color: '#2ecc71'
            },
            {
                name: 'avg_order_value',
                label: this.language === 'ar' ? 'متوسط قيمة الطلب' : __('Avg Order Value'),
                icon: 'fa fa-shopping-cart',
                color: '#f39c12'
            },
            {
                name: 'quality_pass_rate',
                label: this.language === 'ar' ? 'معدل نجاح الجودة' : __('Quality Pass Rate'),
                icon: 'fa fa-check-circle',
                color: '#e74c3c'
            }
        ];

        let cards_html = '';
        cards_config.forEach(card => {
            cards_html += `
                <div class="col-md-3 col-sm-6">
                    <div class="card number-card" data-card="${card.name}">
                        <div class="card-body">
                            <div class="card-icon" style="background-color: ${card.color}">
                                <i class="${card.icon}"></i>
                            </div>
                            <div class="card-content">
                                <h4 class="card-title">${card.label}</h4>
                                <div class="card-value" id="${card.name}-value">
                                    <span class="loading-text">${__('Loading...')}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });

        $('.dashboard-cards').html(cards_html);
    }

    setup_charts() {
        const charts_config = [
            {
                name: 'supplier_spend_chart',
                title: this.language === 'ar' ? 'تحليل إنفاق الموردين' : __('Supplier Spend Analysis'),
                type: 'donut',
                col_class: 'col-md-6'
            },
            {
                name: 'monthly_spend_trend',
                title: this.language === 'ar' ? 'اتجاه الإنفاق الشهري' : __('Monthly Spend Trend'),
                type: 'line',
                col_class: 'col-md-6'
            },
            {
                name: 'item_price_trends',
                title: this.language === 'ar' ? 'اتجاهات أسعار المواد' : __('Item Price Trends'),
                type: 'line',
                col_class: 'col-md-6'
            },
            {
                name: 'supplier_performance',
                title: this.language === 'ar' ? 'أداء الموردين' : __('Supplier Performance'),
                type: 'bar',
                col_class: 'col-md-6'
            },
            {
                name: 'cost_breakdown',
                title: this.language === 'ar' ? 'تصنيف التكاليف حسب الفئة' : __('Cost Breakdown by Category'),
                type: 'pie',
                col_class: 'col-md-12'
            }
        ];

        let charts_html = '';
        charts_config.forEach(chart => {
            charts_html += `
                <div class="${chart.col_class}">
                    <div class="card chart-card">
                        <div class="card-header">
                            <h5 class="card-title">${chart.title}</h5>
                        </div>
                        <div class="card-body">
                            <div class="chart-container" id="${chart.name}">
                                <div class="chart-loading">
                                    <i class="fa fa-spinner fa-spin"></i> ${__('Loading chart...')}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });

        $('.dashboard-charts').html(charts_html);
    }

    bind_actions() {
        // Export buttons
        $('.btn-export').on('click', (e) => {
            const format = $(e.currentTarget).data('format');
            this.export_data(format);
        });

        // Refresh button
        $('.btn-refresh').on('click', () => {
            this.load_dashboard_data();
        });
    }

    bind_filter_events() {
        // Apply filters button
        $('.btn-apply-filters').on('click', () => {
            this.get_filter_values();
            this.load_dashboard_data();
        });

        // Reset filters button
        $('.btn-reset-filters').on('click', () => {
            this.reset_filters();
        });

        // Enter key on filter inputs
        $('.filter-input').on('keypress', (e) => {
            if (e.which === 13) { // Enter key
                this.get_filter_values();
                this.load_dashboard_data();
            }
        });
    }

    get_filter_values() {
        this.filters = {};
        $('.filter-input').each((index, input) => {
            const $input = $(input);
            const fieldname = $input.data('fieldname');
            const value = $input.val();

            if (value) {
                this.filters[fieldname] = value;
            }
        });
    }

    reset_filters() {
        $('.filter-input').each((index, input) => {
            const $input = $(input);
            const fieldname = $input.data('fieldname');

            if (fieldname === 'from_date') {
                $input.val(frappe.datetime.add_months(frappe.datetime.get_today(), -6));
            } else if (fieldname === 'to_date') {
                $input.val(frappe.datetime.get_today());
            } else {
                $input.val('');
            }
        });

        this.get_filter_values();
        this.load_dashboard_data();
    }

    load_dashboard_data() {
        this.load_number_cards();
        this.load_charts();
    }

    load_number_cards() {
        const cards = ['total_spend', 'active_suppliers', 'avg_order_value', 'quality_pass_rate'];

        cards.forEach(card_name => {
            frappe.call({
                method: `universal_workshop.purchasing_management.cost_analysis_dashboard.get_${card_name}_card`,
                args: this.filters,
                callback: (r) => {
                    if (r.message) {
                        this.update_number_card(card_name, r.message);
                    }
                }
            });
        });
    }

    update_number_card(card_name, data) {
        const $card_value = $(`#${card_name}-value`);
        const formatted_value = data.formatted_value || data.value;

        $card_value.html(`<span class="number-value">${formatted_value}</span>`);

        // Add animation
        $card_value.find('.number-value').hide().fadeIn(500);
    }

    load_charts() {
        this.load_supplier_spend_chart();
        this.load_monthly_spend_chart();
        this.load_item_price_trends_chart();
        this.load_supplier_performance_chart();
        this.load_cost_breakdown_chart();
    }

    load_supplier_spend_chart() {
        frappe.call({
            method: 'universal_workshop.purchasing_management.cost_analysis_dashboard.get_supplier_spend_chart_data',
            args: this.filters,
            callback: (r) => {
                if (r.message) {
                    this.render_chart('supplier_spend_chart', {
                        data: r.message,
                        type: 'donut',
                        height: 300,
                        colors: ['#3498db', '#e74c3c', '#f39c12', '#2ecc71', '#9b59b6']
                    });
                }
            }
        });
    }

    load_monthly_spend_chart() {
        frappe.call({
            method: 'universal_workshop.purchasing_management.cost_analysis_dashboard.get_monthly_spend_trend_data',
            args: this.filters,
            callback: (r) => {
                if (r.message) {
                    this.render_chart('monthly_spend_trend', {
                        data: r.message,
                        type: 'line',
                        height: 350,
                        colors: ['#3498db', '#e74c3c']
                    });
                }
            }
        });
    }

    load_item_price_trends_chart() {
        frappe.call({
            method: 'universal_workshop.purchasing_management.cost_analysis_dashboard.get_item_price_trends_data',
            args: this.filters,
            callback: (r) => {
                if (r.message) {
                    this.render_chart('item_price_trends', {
                        data: r.message,
                        type: 'line',
                        height: 350,
                        colors: ['#2ecc71', '#f39c12', '#9b59b6']
                    });
                }
            }
        });
    }

    load_supplier_performance_chart() {
        frappe.call({
            method: 'universal_workshop.purchasing_management.cost_analysis_dashboard.get_supplier_performance_data',
            args: this.filters,
            callback: (r) => {
                if (r.message) {
                    this.render_chart('supplier_performance', {
                        data: r.message,
                        type: 'bar',
                        height: 300,
                        colors: ['#2ecc71', '#e74c3c']
                    });
                }
            }
        });
    }

    load_cost_breakdown_chart() {
        frappe.call({
            method: 'universal_workshop.purchasing_management.cost_analysis_dashboard.get_cost_breakdown_data',
            args: this.filters,
            callback: (r) => {
                if (r.message) {
                    this.render_chart('cost_breakdown', {
                        data: r.message,
                        type: 'pie',
                        height: 300,
                        colors: ['#3498db', '#e74c3c', '#f39c12', '#2ecc71', '#9b59b6', '#e67e22']
                    });
                }
            }
        });
    }

    render_chart(container_id, config) {
        const $container = $(`#${container_id}`);

        // Clear existing content
        $container.empty();

        if (!config.data || !config.data.labels || config.data.labels.length === 0) {
            $container.html(`<div class="no-data-message">${__('No data available')}</div>`);
            return;
        }

        // Create chart using frappe.Chart (Frappe Charts library)
        try {
            this.charts[container_id] = new frappe.Chart(`#${container_id}`, {
                title: config.title || '',
                data: config.data,
                type: config.type,
                height: config.height || 250,
                colors: config.colors || ['#3498db'],
                animate: true,
                truncateLegends: true,
                lineOptions: {
                    regionFill: 1,
                    hideDots: 0,
                    heatline: 1,
                    dotSize: 3
                },
                axisOptions: {
                    xAxisMode: 'tick',
                    yAxisMode: 'tick',
                    xIsSeries: config.type === 'line'
                },
                tooltipOptions: {
                    formatTooltipX: (d) => (d + '').toUpperCase(),
                    formatTooltipY: (d) => {
                        if (container_id.includes('spend') || container_id.includes('cost')) {
                            return `${this.currency} ${d.toFixed(2)}`;
                        }
                        return d;
                    }
                }
            });
        } catch (error) {
            console.error(`Error rendering chart ${container_id}:`, error);
            $container.html(`<div class="chart-error">${__('Error loading chart')}</div>`);
        }
    }

    export_data(format) {
        frappe.call({
            method: 'universal_workshop.purchasing_management.cost_analysis_dashboard.export_dashboard_data',
            args: {
                ...this.filters,
                format_type: format
            },
            callback: (r) => {
                if (r.message && r.message.file_url) {
                    // Download the file
                    window.open(r.message.file_url, '_blank');
                    frappe.show_alert({
                        message: __('Export completed successfully'),
                        indicator: 'green'
                    });
                } else {
                    frappe.show_alert({
                        message: __('Export failed'),
                        indicator: 'red'
                    });
                }
            }
        });
    }
}

// CSS Styles for dashboard
const dashboard_styles = `
<style>
.cost-analysis-dashboard {
    padding: 15px;
}

.dashboard-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 1px solid #e0e6ed;
}

.dashboard-title {
    margin: 0;
    color: #2c3e50;
    font-weight: 600;
}

.dashboard-actions .btn {
    margin-left: 10px;
}

.rtl-layout .dashboard-actions .btn {
    margin-left: 0;
    margin-right: 10px;
}

.filter-section {
    background: #f8f9fa;
    padding: 15px;
    border-radius: 8px;
    margin-bottom: 20px;
}

.number-card {
    margin-bottom: 20px;
    border: none;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    transition: transform 0.2s ease;
}

.number-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.number-card .card-body {
    display: flex;
    align-items: center;
    padding: 20px;
}

.card-icon {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 15px;
    color: white;
    font-size: 24px;
}

.rtl-layout .card-icon {
    margin-right: 0;
    margin-left: 15px;
}

.card-content {
    flex: 1;
}

.card-title {
    margin: 0 0 5px 0;
    font-size: 14px;
    color: #6c757d;
    font-weight: 500;
}

.card-value {
    font-size: 24px;
    font-weight: 700;
    color: #2c3e50;
}

.loading-text {
    font-size: 14px !important;
    color: #6c757d !important;
    font-weight: normal !important;
}

.chart-card {
    margin-bottom: 20px;
    border: none;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.chart-card .card-header {
    background: #f8f9fa;
    border-bottom: 1px solid #e0e6ed;
    padding: 15px 20px;
}

.chart-card .card-title {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: #2c3e50;
}

.chart-container {
    min-height: 250px;
    position: relative;
}

.chart-loading, .no-data-message, .chart-error {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 250px;
    color: #6c757d;
    font-size: 16px;
}

.chart-loading i {
    margin-right: 10px;
}

.rtl-layout .chart-loading i {
    margin-right: 0;
    margin-left: 10px;
}

/* Arabic RTL specific styles */
.rtl-layout .dashboard-header {
    direction: rtl;
}

.rtl-layout .filter-section .form-group label {
    text-align: right;
}

.rtl-layout .filter-input {
    text-align: right;
}

.rtl-layout .card-content {
    text-align: right;
}

/* Responsive design */
@media (max-width: 768px) {
    .dashboard-header {
        flex-direction: column;
        align-items: flex-start;
    }
    
    .dashboard-actions {
        margin-top: 15px;
        width: 100%;
    }
    
    .dashboard-actions .btn {
        width: 100%;
        margin: 5px 0;
    }
    
    .number-card .card-body {
        flex-direction: column;
        text-align: center;
    }
    
    .card-icon {
        margin: 0 0 15px 0;
    }
}
</style>
`;

// Inject styles
$('head').append(dashboard_styles); 