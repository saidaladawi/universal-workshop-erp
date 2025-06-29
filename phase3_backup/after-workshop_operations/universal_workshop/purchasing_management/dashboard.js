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
                truncateLegends: true
            });
        } catch (error) {
            console.error(`Error rendering chart ${container_id}:`, error);
            $container.html(`<div class="chart-error">${__('Error loading chart')}</div>`);
        }
    }
} 