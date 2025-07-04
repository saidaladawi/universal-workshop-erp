/**
 * Universal Workshop ERP - ABC Analysis UI
 * Comprehensive ABC analysis interface with advanced analytics and optimization recommendations
 * Arabic/English localization support for Omani automotive workshops
 */

class ABCAnalysisUI {
    constructor() {
        this.currentView = 'dashboard';
        this.analysisData = null;
        this.selectedWarehouse = null;
        this.analysisConfig = {
            type: 'value',
            threshold_a: 80,
            threshold_b: 95,
            period_days: 365
        };
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadDashboard();
    }

    setupEventListeners() {
        // Tab navigation
        $(document).on('click', '.abc-tab-btn', (e) => {
            const tab = $(e.target).data('tab');
            this.switchTab(tab);
        });

        // Analysis controls
        $(document).on('change', '#abc-warehouse-filter', (e) => {
            this.selectedWarehouse = $(e.target).val();
            this.refreshCurrentView();
        });

        $(document).on('change', '#abc-analysis-type', (e) => {
            this.analysisConfig.type = $(e.target).val();
        });

        $(document).on('click', '#run-abc-analysis', () => {
            this.runAnalysis();
        });

        $(document).on('click', '#save-abc-classification', () => {
            this.saveClassification();
        });
    }

    switchTab(tab) {
        this.currentView = tab;
        
        // Update tab buttons
        $('.abc-tab-btn').removeClass('active');
        $(`.abc-tab-btn[data-tab="${tab}"]`).addClass('active');
        
        // Show/hide content
        $('.abc-tab-content').hide();
        $(`#abc-${tab}-tab`).show();
        
        // Load content
        switch(tab) {
            case 'dashboard':
                this.loadDashboard();
                break;
            case 'analysis':
                this.loadAnalysisView();
                break;
            case 'recommendations':
                this.loadRecommendations();
                break;
        }
    }

    async loadDashboard() {
        try {
            const response = await frappe.call({
                method: 'universal_workshop.parts_inventory.abc_analysis.get_abc_dashboard',
                args: {
                    warehouse: this.selectedWarehouse,
                    period: 30
                }
            });

            if (response.message && response.message.success) {
                this.renderDashboard(response.message);
            } else {
                this.showError(__('Failed to load ABC dashboard'));
            }
        } catch (error) {
            console.error('Dashboard load error:', error);
            this.showError(__('Error loading dashboard data'));
        }
    }

    renderDashboard(data) {
        const dashboardHtml = `
            <div class="abc-dashboard">
                <div class="row">
                    <div class="col-md-12">
                        <div class="abc-filters">
                            <div class="row">
                                <div class="col-md-6">
                                    <label for="abc-warehouse-filter">${__('Warehouse')}</label>
                                    <select id="abc-warehouse-filter" class="form-control">
                                        <option value="">${__('All Warehouses')}</option>
                                        ${this.getWarehouseOptions()}
                                    </select>
                                </div>
                                <div class="col-md-6">
                                    <label>&nbsp;</label>
                                    <button class="btn btn-primary btn-block" onclick="window.abcAnalysis.refreshDashboard()">
                                        <i class="fa fa-refresh"></i> ${__('Refresh')}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="row mt-3">
                    ${this.renderSummaryCards(data.summary)}
                </div>
            </div>
        `;

        $('#abc-dashboard-tab').html(dashboardHtml);
        
        // Set selected warehouse
        if (this.selectedWarehouse) {
            $('#abc-warehouse-filter').val(this.selectedWarehouse);
        }
    }

    renderSummaryCards(summary) {
        const totalValue = summary.total_stock_value || 0;
        const totalItems = summary.total_items || 0;
        
        return `
            <div class="col-md-3">
                <div class="card bg-primary text-white">
                    <div class="card-body">
                        <div class="d-flex justify-content-between">
                            <div>
                                <h4 class="mb-0">${totalItems}</h4>
                                <p class="mb-0">${__('Total Items')}</p>
                            </div>
                            <div class="align-self-center">
                                <i class="fa fa-cubes fa-2x"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-success text-white">
                    <div class="card-body">
                        <div class="d-flex justify-content-between">
                            <div>
                                <h4 class="mb-0">${this.formatCurrency(totalValue)}</h4>
                                <p class="mb-0">${__('Total Stock Value')}</p>
                            </div>
                            <div class="align-self-center">
                                <i class="fa fa-money fa-2x"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-warning text-white">
                    <div class="card-body">
                        <div class="d-flex justify-content-between">
                            <div>
                                <h4 class="mb-0">${summary.category_distribution?.A || 0}</h4>
                                <p class="mb-0">${__('Category A Items')}</p>
                            </div>
                            <div class="align-self-center">
                                <i class="fa fa-star fa-2x"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-info text-white">
                    <div class="card-body">
                        <div class="d-flex justify-content-between">
                            <div>
                                <h4 class="mb-0">${summary.last_analysis ? 'Recent' : 'Never'}</h4>
                                <p class="mb-0">${__('Last Analysis')}</p>
                            </div>
                            <div class="align-self-center">
                                <i class="fa fa-calendar fa-2x"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    loadAnalysisView() {
        const analysisHtml = `
            <div class="abc-analysis-view">
                <div class="row">
                    <div class="col-md-12">
                        <div class="card">
                            <div class="card-header">
                                <h5>${__('ABC Analysis Configuration')}</h5>
                            </div>
                            <div class="card-body">
                                <div class="row">
                                    <div class="col-md-4">
                                        <label for="abc-analysis-type">${__('Analysis Type')}</label>
                                        <select id="abc-analysis-type" class="form-control">
                                            <option value="value">${__('Annual Value')}</option>
                                            <option value="volume">${__('Movement Volume')}</option>
                                            <option value="frequency">${__('Transaction Frequency')}</option>
                                        </select>
                                    </div>
                                    <div class="col-md-2">
                                        <label for="abc-threshold-a">${__('Category A %')}</label>
                                        <input type="number" id="abc-threshold-a" class="form-control" value="80" min="1" max="99">
                                    </div>
                                    <div class="col-md-2">
                                        <label for="abc-threshold-b">${__('Category B %')}</label>
                                        <input type="number" id="abc-threshold-b" class="form-control" value="95" min="1" max="99">
                                    </div>
                                    <div class="col-md-2">
                                        <label>&nbsp;</label>
                                        <button id="run-abc-analysis" class="btn btn-primary btn-block">
                                            <i class="fa fa-play"></i> ${__('Run Analysis')}
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div id="abc-analysis-results" style="display: none;">
                    <div class="row mt-4">
                        <div class="col-md-12">
                            <div class="card">
                                <div class="card-header d-flex justify-content-between">
                                    <h5>${__('Analysis Results')}</h5>
                                    <div>
                                        <button id="save-abc-classification" class="btn btn-success">
                                            <i class="fa fa-save"></i> ${__('Save Classification')}
                                        </button>
                                    </div>
                                </div>
                                <div class="card-body">
                                    <div id="abc-results-summary"></div>
                                    <div id="abc-results-table"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        $('#abc-analysis-tab').html(analysisHtml);
    }

    async runAnalysis() {
        try {
            // Show loading state
            $('#run-abc-analysis').prop('disabled', true).html('<i class="fa fa-spinner fa-spin"></i> ' + __('Analyzing...'));

            // Get configuration
            this.analysisConfig = {
                type: $('#abc-analysis-type').val(),
                threshold_a: parseFloat($('#abc-threshold-a').val()),
                threshold_b: parseFloat($('#abc-threshold-b').val())
            };

            const response = await frappe.call({
                method: 'universal_workshop.parts_inventory.abc_analysis.perform_abc_analysis',
                args: {
                    warehouse: this.selectedWarehouse,
                    analysis_type: this.analysisConfig.type,
                    threshold_a: this.analysisConfig.threshold_a,
                    threshold_b: this.analysisConfig.threshold_b
                }
            });

            if (response.message && response.message.success) {
                this.analysisData = response.message;
                this.renderAnalysisResults();
                $('#abc-analysis-results').show();
            } else {
                this.showError(response.message?.message || __('Analysis failed'));
            }
        } catch (error) {
            console.error('Analysis error:', error);
            this.showError(__('Error running ABC analysis'));
        } finally {
            // Reset button
            $('#run-abc-analysis').prop('disabled', false).html('<i class="fa fa-play"></i> ' + __('Run Analysis'));
        }
    }

    renderAnalysisResults() {
        if (!this.analysisData) return;

        const { items, summary, recommendations } = this.analysisData;

        // Render summary
        const summaryHtml = `
            <div class="row mb-4">
                <div class="col-md-4">
                    <div class="alert alert-primary">
                        <h6>${__('Category A')}</h6>
                        <strong>${summary.A.count} ${__('items')} (${summary.A.percentage}%)</strong><br>
                        <small>${summary.A.value_percentage}% ${__('of total value')}</small>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="alert alert-warning">
                        <h6>${__('Category B')}</h6>
                        <strong>${summary.B.count} ${__('items')} (${summary.B.percentage}%)</strong><br>
                        <small>${summary.B.value_percentage}% ${__('of total value')}</small>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="alert alert-info">
                        <h6>${__('Category C')}</h6>
                        <strong>${summary.C.count} ${__('items')} (${summary.C.percentage}%)</strong><br>
                        <small>${summary.C.value_percentage}% ${__('of total value')}</small>
                    </div>
                </div>
            </div>
        `;

        $('#abc-results-summary').html(summaryHtml);

        // Render results table
        this.renderResultsTable(items);
    }

    renderResultsTable(items) {
        const tableHtml = `
            <div class="table-responsive">
                <table class="table table-bordered abc-results-table">
                    <thead>
                        <tr>
                            <th>${__('Item Code')}</th>
                            <th>${__('Item Name')}</th>
                            <th>${__('Category')}</th>
                            <th>${__('Annual Value')}</th>
                            <th>${__('Cumulative %')}</th>
                            <th>${__('Management Strategy')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${items.slice(0, 50).map(item => `
                            <tr class="abc-category-${item.abc_category}">
                                <td><strong>${item.item_code}</strong></td>
                                <td>
                                    ${item.item_name}
                                    ${item.item_name_ar ? `<br><small class="text-muted">${item.item_name_ar}</small>` : ''}
                                </td>
                                <td>
                                    <span class="badge badge-${this.getCategoryBadgeClass(item.abc_category)}">
                                        ${item.abc_category}
                                    </span>
                                </td>
                                <td>${this.formatCurrency(item.annual_value)}</td>
                                <td>${item.cumulative_percentage}%</td>
                                <td>
                                    <small>${item.management_strategy}</small><br>
                                    <small class="text-muted">${__('Review')}: ${item.review_frequency}</small>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
            ${items.length > 50 ? `<p class="text-muted text-center">${__('Showing top 50 items')}</p>` : ''}
        `;

        $('#abc-results-table').html(tableHtml);
    }

    getCategoryBadgeClass(category) {
        switch(category) {
            case 'A': return 'danger';
            case 'B': return 'warning';
            case 'C': return 'info';
            default: return 'secondary';
        }
    }

    async saveClassification() {
        if (!this.analysisData || !this.analysisData.items) {
            this.showError(__('No analysis data to save'));
            return;
        }

        try {
            const response = await frappe.call({
                method: 'universal_workshop.parts_inventory.abc_analysis.save_abc_classification',
                args: {
                    items_data: this.analysisData.items,
                    analysis_config: this.analysisData.analysis_config
                }
            });

            if (response.message && response.message.success) {
                frappe.show_alert({
                    message: response.message.message,
                    indicator: 'green'
                });
            } else {
                this.showError(response.message?.message || __('Failed to save classification'));
            }
        } catch (error) {
            console.error('Save error:', error);
            this.showError(__('Error saving classification'));
        }
    }

    formatCurrency(amount) {
        return `${(amount || 0).toFixed(2)} OMR`;
    }

    getWarehouseOptions() {
        return '<option value="Main Store">Main Store</option><option value="Service Bay">Service Bay</option>';
    }

    refreshCurrentView() {
        if (this.currentView === 'dashboard') {
            this.loadDashboard();
        }
    }

    refreshDashboard() {
        this.loadDashboard();
    }

    showError(message) {
        frappe.show_alert({
            message: message,
            indicator: 'red'
        });
    }
}

// Initialize ABC Analysis UI
frappe.ready(() => {
    window.abcAnalysis = new ABCAnalysisUI();
});
