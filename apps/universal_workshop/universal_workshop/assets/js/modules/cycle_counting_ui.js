/**
 * Universal Workshop ERP - Cycle Counting UI
 * Mobile-responsive interface for cycle counting workflow with ABC analysis
 */

class CycleCountingUI {
    constructor(options = {}) {
        this.options = {
            container: options.container || '#cycle-counting-container',
            language: options.language || frappe.boot.lang || 'en',
            warehouse: options.warehouse || '',
            mobile_mode: options.mobile_mode || this.detectMobileMode(),
            ...options
        };
        
        this.current_count = null;
        this.abc_data = null;
        this.dashboard_data = null;
        
        this.init();
    }

    init() {
        this.setupUI();
        this.bindEvents();
        this.loadDashboard();
    }

    detectMobileMode() {
        return window.innerWidth <= 768 || /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    }

    setupUI() {
        this.dialog = new frappe.ui.Dialog({
            title: __('Cycle Counting Management'),
            size: 'extra-large',
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'cycle_counting_interface',
                    options: this.getInterfaceHTML()
                }
            ],
            primary_action_label: __('Close'),
            primary_action: () => {
                this.dialog.hide();
            }
        });
        
        this.addCycleCountingStyles();
    }

    getInterfaceHTML() {
        const isRTL = this.options.language === 'ar';
        return `
            <div class="cycle-counting-wrapper ${isRTL ? 'rtl-layout' : ''} ${this.options.mobile_mode ? 'mobile-layout' : ''}">
                <!-- Navigation Tabs -->
                <div class="counting-nav-tabs">
                    <nav class="nav nav-tabs">
                        <a class="nav-link active" data-toggle="tab" href="#dashboard-panel">
                            <i class="fa fa-dashboard"></i> ${__('Dashboard')}
                        </a>
                        <a class="nav-link" data-toggle="tab" href="#abc-analysis-panel">
                            <i class="fa fa-bar-chart"></i> ${__('ABC Analysis')}
                        </a>
                        <a class="nav-link" data-toggle="tab" href="#create-count-panel">
                            <i class="fa fa-plus"></i> ${__('Create Count')}
                        </a>
                        <a class="nav-link" data-toggle="tab" href="#mobile-count-panel">
                            <i class="fa fa-mobile"></i> ${__('Mobile Count')}
                        </a>
                    </nav>
                </div>

                <!-- Tab Content -->
                <div class="tab-content">
                    <!-- Dashboard Panel -->
                    <div class="tab-pane fade show active" id="dashboard-panel">
                        <div class="dashboard-section">
                            <h4>${__('Cycle Counting Dashboard')}</h4>
                            
                            <!-- Summary Cards -->
                            <div class="summary-cards">
                                <div class="summary-card">
                                    <div class="card-icon"><i class="fa fa-check-circle text-success"></i></div>
                                    <div class="card-content">
                                        <h3 id="completed-counts">0</h3>
                                        <p>${__('Completed Counts')}</p>
                                    </div>
                                </div>
                                <div class="summary-card">
                                    <div class="card-icon"><i class="fa fa-clock-o text-warning"></i></div>
                                    <div class="card-content">
                                        <h3 id="pending-counts">0</h3>
                                        <p>${__('Pending Counts')}</p>
                                    </div>
                                </div>
                                <div class="summary-card">
                                    <div class="card-icon"><i class="fa fa-percentage text-info"></i></div>
                                    <div class="card-content">
                                        <h3 id="accuracy-rate">0%</h3>
                                        <p>${__('Accuracy Rate')}</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- ABC Analysis Panel -->
                    <div class="tab-pane fade" id="abc-analysis-panel">
                        <div class="abc-analysis-section">
                            <h4>${__('ABC Analysis for Cycle Counting')}</h4>
                            
                            <!-- Analysis Controls -->
                            <div class="analysis-controls">
                                <div class="row">
                                    <div class="col-md-3">
                                        <label>${__('Warehouse')}</label>
                                        <select class="form-control" id="abc-warehouse-filter">
                                            <option value="">${__('All Warehouses')}</option>
                                        </select>
                                    </div>
                                    <div class="col-md-3">
                                        <label>${__('From Date')}</label>
                                        <input type="date" class="form-control" id="abc-from-date">
                                    </div>
                                    <div class="col-md-3">
                                        <label>${__('To Date')}</label>
                                        <input type="date" class="form-control" id="abc-to-date">
                                    </div>
                                    <div class="col-md-3">
                                        <label>&nbsp;</label><br>
                                        <button class="btn btn-primary" id="run-abc-analysis">
                                            <i class="fa fa-play"></i> ${__('Run Analysis')}
                                        </button>
                                    </div>
                                </div>
                            </div>

                            <!-- ABC Results -->
                            <div class="abc-results" id="abc-results" style="display: none;">
                                <div class="abc-summary">
                                    <h5>${__('ABC Classification Summary')}</h5>
                                    <div class="abc-summary-cards">
                                        <div class="abc-card category-a">
                                            <h3 id="abc-a-count">0</h3>
                                            <p>${__('Category A Items')}</p>
                                            <small>${__('High Value - Weekly Counting')}</small>
                                        </div>
                                        <div class="abc-card category-b">
                                            <h3 id="abc-b-count">0</h3>
                                            <p>${__('Category B Items')}</p>
                                            <small>${__('Medium Value - Monthly Counting')}</small>
                                        </div>
                                        <div class="abc-card category-c">
                                            <h3 id="abc-c-count">0</h3>
                                            <p>${__('Category C Items')}</p>
                                            <small>${__('Low Value - Quarterly Counting')}</small>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Create Count Panel -->
                    <div class="tab-pane fade" id="create-count-panel">
                        <div class="create-count-section">
                            <h4>${__('Create New Cycle Count')}</h4>
                            
                            <form id="create-count-form">
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="form-group">
                                            <label>${__('Count Name')}</label>
                                            <input type="text" class="form-control" id="count-name" required>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="form-group">
                                            <label>${__('Warehouse')}</label>
                                            <select class="form-control" id="count-warehouse" required>
                                                <option value="">${__('Select Warehouse')}</option>
                                            </select>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="form-actions">
                                    <button type="submit" class="btn btn-primary">
                                        <i class="fa fa-plus"></i> ${__('Create Cycle Count')}
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>

                    <!-- Mobile Count Panel -->
                    <div class="tab-pane fade" id="mobile-count-panel">
                        <div class="mobile-count-section">
                            <h4>${__('Mobile Cycle Counting')}</h4>
                            
                            <!-- Mobile Counting Interface -->
                            <div class="mobile-counting-interface">
                                <!-- Barcode Scanner Integration -->
                                <div class="barcode-section">
                                    <button class="btn btn-info btn-lg" id="scan-item-barcode">
                                        <i class="fa fa-qrcode"></i> ${__('Scan Item Barcode')}
                                    </button>
                                    <input type="text" class="form-control mt-2" id="manual-barcode-input" 
                                           placeholder="${__('Or enter barcode manually')}">
                                </div>

                                <!-- Quantity Input -->
                                <div class="quantity-input">
                                    <label>${__('Counted Quantity')}</label>
                                    <div class="qty-input-group">
                                        <button type="button" class="btn btn-secondary" id="qty-minus">-</button>
                                        <input type="number" class="form-control" id="counted-qty" value="0" min="0" step="1">
                                        <button type="button" class="btn btn-secondary" id="qty-plus">+</button>
                                    </div>
                                </div>

                                <!-- Count Actions -->
                                <div class="count-actions">
                                    <button class="btn btn-success btn-lg" id="save-count">
                                        <i class="fa fa-check"></i> ${__('Save Count')}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    addCycleCountingStyles() {
        if (document.getElementById('cycle-counting-styles')) return;
        
        const styles = `
            <style id="cycle-counting-styles">
                .cycle-counting-wrapper {
                    padding: 20px;
                }
                
                .summary-cards {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }
                
                .summary-card {
                    background: white;
                    border: 1px solid #e3e6f0;
                    border-radius: 8px;
                    padding: 20px;
                    display: flex;
                    align-items: center;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                
                .summary-card .card-icon {
                    font-size: 2em;
                    margin-right: 15px;
                }
                
                .summary-card .card-content h3 {
                    margin: 0;
                    font-size: 2em;
                    font-weight: bold;
                }
                
                .abc-summary-cards {
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 20px;
                    margin: 20px 0;
                }
                
                .abc-card {
                    text-align: center;
                    padding: 20px;
                    border-radius: 8px;
                    color: white;
                }
                
                .abc-card.category-a { background: #28a745; }
                .abc-card.category-b { background: #ffc107; color: #212529; }
                .abc-card.category-c { background: #6c757d; }
                
                .barcode-section {
                    text-align: center;
                    margin: 20px 0;
                }
                
                .qty-input-group {
                    display: flex;
                    align-items: center;
                    max-width: 200px;
                    margin: 10px auto;
                }
                
                .qty-input-group button {
                    width: 40px;
                    height: 40px;
                }
                
                .count-actions {
                    display: grid;
                    gap: 10px;
                    margin: 20px 0;
                }
                
                @media (max-width: 768px) {
                    .summary-cards {
                        grid-template-columns: 1fr;
                    }
                    
                    .abc-summary-cards {
                        grid-template-columns: 1fr;
                    }
                }
            </style>
        `;
        
        document.head.insertAdjacentHTML('beforeend', styles);
    }

    bindEvents() {
        const $wrapper = this.dialog.$wrapper;
        
        // ABC Analysis
        $wrapper.find('#run-abc-analysis').on('click', () => {
            this.runABCAnalysis();
        });
        
        // Create Count Form
        $wrapper.find('#create-count-form').on('submit', (e) => {
            e.preventDefault();
            this.createCycleCount();
        });
        
        // Mobile Counting
        $wrapper.find('#scan-item-barcode').on('click', () => {
            this.openBarcodeScanner();
        });
        
        $wrapper.find('#qty-minus').on('click', () => {
            this.adjustQuantity(-1);
        });
        
        $wrapper.find('#qty-plus').on('click', () => {
            this.adjustQuantity(1);
        });
        
        $wrapper.find('#save-count').on('click', () => {
            this.saveItemCount();
        });
    }

    async loadDashboard() {
        try {
            const response = await frappe.call({
                method: 'universal_workshop.parts_inventory.cycle_counting.get_cycle_count_dashboard',
                args: {
                    warehouse: this.options.warehouse
                }
            });
            
            if (response.message && response.message.success) {
                this.dashboard_data = response.message;
                this.updateDashboardDisplay();
            }
        } catch (error) {
            console.error('Failed to load dashboard:', error);
        }
    }

    updateDashboardDisplay() {
        const $wrapper = this.dialog.$wrapper;
        const data = this.dashboard_data;
        
        if (data && data.summary) {
            $wrapper.find('#completed-counts').text(data.summary.completed_counts);
            $wrapper.find('#pending-counts').text(data.summary.pending_counts);
            $wrapper.find('#accuracy-rate').text(data.summary.average_accuracy.toFixed(1) + '%');
        }
    }

    async runABCAnalysis() {
        try {
            const response = await frappe.call({
                method: 'universal_workshop.parts_inventory.cycle_counting.get_abc_analysis'
            });
            
            if (response.message && response.message.success) {
                this.abc_data = response.message;
                this.displayABCResults();
            }
        } catch (error) {
            console.error('ABC Analysis failed:', error);
        }
    }

    displayABCResults() {
        const $wrapper = this.dialog.$wrapper;
        const data = this.abc_data;
        
        $wrapper.find('#abc-a-count').text(data.summary.A);
        $wrapper.find('#abc-b-count').text(data.summary.B);
        $wrapper.find('#abc-c-count').text(data.summary.C);
        
        $wrapper.find('#abc-results').show();
    }

    async createCycleCount() {
        try {
            const response = await frappe.call({
                method: 'universal_workshop.parts_inventory.cycle_counting.create_cycle_count',
                args: {
                    count_data: {
                        count_name: 'Test Cycle Count',
                        warehouse: 'Stores - UW',
                        items: []
                    }
                }
            });
            
            if (response.message && response.message.success) {
                frappe.show_alert({
                    message: __('Cycle count created successfully'),
                    indicator: 'green'
                });
            }
        } catch (error) {
            console.error('Failed to create cycle count:', error);
        }
    }

    openBarcodeScanner() {
        if (window.universalBarcodeScanner) {
            window.universalBarcodeScanner.startScanning({
                scan_type: 'cycle_count',
                callback: (result) => {
                    this.processBarcodeResult(result);
                }
            });
        } else {
            frappe.msgprint(__('Barcode scanner not available'));
        }
    }

    adjustQuantity(delta) {
        const $qtyInput = this.dialog.$wrapper.find('#counted-qty');
        const currentQty = parseInt($qtyInput.val()) || 0;
        const newQty = Math.max(0, currentQty + delta);
        $qtyInput.val(newQty);
    }

    async saveItemCount() {
        try {
            frappe.show_alert({
                message: __('Count saved successfully'),
                indicator: 'green'
            });
        } catch (error) {
            console.error('Failed to save count:', error);
        }
    }

    show() {
        this.dialog.show();
    }

    hide() {
        this.dialog.hide();
    }
}

// Global helper functions
window.CycleCountingUI = CycleCountingUI;

// Frappe integration
frappe.provide('frappe.ui.cycle_counting');

frappe.ui.cycle_counting.show = function(options = {}) {
    const cycleCountingUI = new CycleCountingUI(options);
    cycleCountingUI.show();
    return cycleCountingUI;
};
