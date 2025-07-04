/**
 * Stock Transfer UI for Universal Workshop ERP
 * Mobile-responsive interface with barcode integration and approval workflow
 */

class StockTransferUI {
    constructor() {
        this.current_transfer = null;
        this.scan_mode = false;
        this.scanner = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeUI();
    }

    setupEventListeners() {
        // Mobile-responsive navigation
        $(document).on('click', '.stock-transfer-nav', (e) => {
            e.preventDefault();
            const section = $(e.target).data('section');
            this.showSection(section);
        });

        // Transfer creation
        $(document).on('click', '#create-transfer-btn', () => {
            this.showCreateTransferModal();
        });

        // Transfer approval
        $(document).on('click', '.approve-transfer-btn', (e) => {
            const transferId = $(e.target).data('transfer-id');
            this.showApprovalModal(transferId);
        });

        // Barcode scanning
        $(document).on('click', '.scan-item-btn', (e) => {
            const transferId = $(e.target).data('transfer-id');
            const location = $(e.target).data('location');
            this.startBarcodeScanning(transferId, location);
        });

        // Complete transfer
        $(document).on('click', '.complete-transfer-btn', (e) => {
            const transferId = $(e.target).data('transfer-id');
            this.completeTransfer(transferId);
        });

        // Real-time updates
        this.setupRealTimeUpdates();
    }

    initializeUI() {
        this.createMainInterface();
        this.loadPendingTransfers();
        this.loadDashboardData();
    }

    createMainInterface() {
        const html = `
            <div class="stock-transfer-container">
                <!-- Mobile Navigation -->
                <div class="stock-transfer-nav-bar">
                    <div class="nav-item active" data-section="dashboard">
                        <i class="fa fa-dashboard"></i>
                        <span>${__('Dashboard')}</span>
                    </div>
                    <div class="nav-item" data-section="pending">
                        <i class="fa fa-clock-o"></i>
                        <span>${__('Pending')}</span>
                        <span class="badge" id="pending-count">0</span>
                    </div>
                    <div class="nav-item" data-section="create">
                        <i class="fa fa-plus"></i>
                        <span>${__('Create')}</span>
                    </div>
                    <div class="nav-item" data-section="scan">
                        <i class="fa fa-qrcode"></i>
                        <span>${__('Scan')}</span>
                    </div>
                </div>

                <!-- Dashboard Section -->
                <div class="transfer-section" id="dashboard-section">
                    <div class="dashboard-header">
                        <h3>${__('Stock Transfer Dashboard')}</h3>
                        <div class="dashboard-actions">
                            <button class="btn btn-primary" id="create-transfer-btn">
                                <i class="fa fa-plus"></i> ${__('New Transfer')}
                            </button>
                        </div>
                    </div>
                    
                    <div class="dashboard-cards">
                        <div class="metric-card">
                            <div class="metric-value" id="total-transfers">-</div>
                            <div class="metric-label">${__('Total Transfers')}</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value" id="pending-transfers">-</div>
                            <div class="metric-label">${__('Pending')}</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value" id="completion-rate">-</div>
                            <div class="metric-label">${__('Completion Rate')}</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value" id="total-value">-</div>
                            <div class="metric-label">${__('Total Value')}</div>
                        </div>
                    </div>

                    <div class="recent-activity">
                        <h4>${__('Recent Transfer Activity')}</h4>
                        <div id="recent-transfers"></div>
                    </div>
                </div>

                <!-- Pending Transfers Section -->
                <div class="transfer-section" id="pending-section" style="display: none;">
                    <div class="section-header">
                        <h3>${__('Pending Transfers')}</h3>
                        <div class="filter-controls">
                            <select id="warehouse-filter" class="form-control">
                                <option value="">${__('All Warehouses')}</option>
                            </select>
                            <select id="status-filter" class="form-control">
                                <option value="">${__('All Status')}</option>
                                <option value="Draft">${__('Draft')}</option>
                                <option value="Source Approved">${__('Source Approved')}</option>
                            </select>
                        </div>
                    </div>
                    <div id="pending-transfers-list"></div>
                </div>

                <!-- Create Transfer Section -->
                <div class="transfer-section" id="create-section" style="display: none;">
                    <div class="section-header">
                        <h3>${__('Create Stock Transfer')}</h3>
                    </div>
                    <div class="create-transfer-form">
                        <div class="form-row">
                            <div class="form-group col-md-6">
                                <label>${__('Source Warehouse')}</label>
                                <select id="source-warehouse" class="form-control" required>
                                    <option value="">${__('Select Source Warehouse')}</option>
                                </select>
                            </div>
                            <div class="form-group col-md-6">
                                <label>${__('Target Warehouse')}</label>
                                <select id="target-warehouse" class="form-control" required>
                                    <option value="">${__('Select Target Warehouse')}</option>
                                </select>
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group col-md-6">
                                <label>${__('Priority')}</label>
                                <select id="transfer-priority" class="form-control">
                                    <option value="Medium">${__('Medium')}</option>
                                    <option value="High">${__('High')}</option>
                                    <option value="Low">${__('Low')}</option>
                                </select>
                            </div>
                            <div class="form-group col-md-6">
                                <label>${__('Remarks')}</label>
                                <input type="text" id="transfer-remarks" class="form-control" 
                                       placeholder="${__('Transfer remarks')}">
                            </div>
                        </div>
                        
                        <div class="items-section">
                            <div class="items-header">
                                <h4>${__('Items to Transfer')}</h4>
                                <button type="button" class="btn btn-sm btn-primary" id="add-item-btn">
                                    <i class="fa fa-plus"></i> ${__('Add Item')}
                                </button>
                            </div>
                            <div id="transfer-items-list"></div>
                        </div>
                        
                        <div class="form-actions">
                            <button type="button" class="btn btn-success" id="submit-transfer-btn">
                                <i class="fa fa-check"></i> ${__('Create Transfer')}
                            </button>
                            <button type="button" class="btn btn-secondary" id="clear-form-btn">
                                <i class="fa fa-times"></i> ${__('Clear')}
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Scan Section -->
                <div class="transfer-section" id="scan-section" style="display: none;">
                    <div class="section-header">
                        <h3>${__('Scan Items')}</h3>
                    </div>
                    <div class="scan-interface">
                        <div class="scan-controls">
                            <select id="scan-transfer-select" class="form-control">
                                <option value="">${__('Select Transfer to Scan')}</option>
                            </select>
                            <div class="scan-location-toggle">
                                <label class="radio-inline">
                                    <input type="radio" name="scan-location" value="source" checked>
                                    ${__('Source')}
                                </label>
                                <label class="radio-inline">
                                    <input type="radio" name="scan-location" value="target">
                                    ${__('Target')}
                                </label>
                            </div>
                        </div>
                        
                        <div class="barcode-scanner-container">
                            <div id="barcode-scanner" style="display: none;"></div>
                            <div class="manual-input">
                                <input type="text" id="manual-barcode" class="form-control" 
                                       placeholder="${__('Scan or enter barcode')}" autofocus>
                                <button type="button" class="btn btn-primary" id="process-barcode-btn">
                                    <i class="fa fa-search"></i> ${__('Process')}
                                </button>
                            </div>
                        </div>
                        
                        <div id="scan-results"></div>
                    </div>
                </div>
            </div>

            <!-- Modals -->
            <div class="modal fade" id="transfer-details-modal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h4 class="modal-title">${__('Transfer Details')}</h4>
                            <button type="button" class="close" data-dismiss="modal">&times;</button>
                        </div>
                        <div class="modal-body" id="transfer-details-content"></div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-dismiss="modal">
                                ${__('Close')}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Append to appropriate container
        if ($('.stock-transfer-container').length === 0) {
            $('body').append(html);
        }
    }

    showSection(section) {
        // Update navigation
        $('.nav-item').removeClass('active');
        $(`.nav-item[data-section="${section}"]`).addClass('active');

        // Show section
        $('.transfer-section').hide();
        $(`#${section}-section`).show();

        // Load section-specific data
        switch (section) {
            case 'dashboard':
                this.loadDashboardData();
                break;
            case 'pending':
                this.loadPendingTransfers();
                break;
            case 'create':
                this.initializeCreateForm();
                break;
            case 'scan':
                this.initializeScanInterface();
                break;
        }
    }

    loadDashboardData() {
        frappe.call({
            method: 'universal_workshop.parts_inventory.stock_transfer.get_transfer_dashboard_data',
            callback: (r) => {
                if (r.message) {
                    const data = r.message;
                    $('#total-transfers').text(data.total_transfers || 0);
                    $('#pending-transfers').text(data.pending_transfers || 0);
                    $('#completion-rate').text(`${data.completion_rate || 0}%`);
                    $('#total-value').text(`OMR ${(data.total_value || 0).toLocaleString()}`);
                    $('#pending-count').text(data.pending_transfers || 0);
                }
            }
        });
    }

    loadPendingTransfers() {
        const warehouse = $('#warehouse-filter').val();
        const status = $('#status-filter').val();

        frappe.call({
            method: 'universal_workshop.parts_inventory.stock_transfer.get_pending_transfers',
            args: {
                warehouse: warehouse,
                status: status,
                limit: 50
            },
            callback: (r) => {
                if (r.message) {
                    this.renderPendingTransfers(r.message);
                }
            }
        });
    }

    renderPendingTransfers(transfers) {
        const container = $('#pending-transfers-list');
        container.empty();

        if (transfers.length === 0) {
            container.html(`
                <div class="no-transfers">
                    <i class="fa fa-inbox"></i>
                    <p>${__('No pending transfers found')}</p>
                </div>
            `);
            return;
        }

        transfers.forEach(transfer => {
            const urgencyClass = transfer.urgency === 'High' ? 'danger' : 
                               transfer.urgency === 'Medium' ? 'warning' : 'info';
            
            const html = `
                <div class="transfer-card" data-transfer-id="${transfer.name}">
                    <div class="transfer-header">
                        <div class="transfer-id">
                            <strong>${transfer.name}</strong>
                            <span class="badge badge-${urgencyClass}">${transfer.urgency}</span>
                        </div>
                        <div class="transfer-date">
                            ${frappe.datetime.str_to_user(transfer.posting_date)}
                        </div>
                    </div>
                    
                    <div class="transfer-body">
                        <div class="transfer-route">
                            <span class="warehouse-from">${transfer.from_warehouse}</span>
                            <i class="fa fa-arrow-right"></i>
                            <span class="warehouse-to">${transfer.to_warehouse}</span>
                        </div>
                        
                        <div class="transfer-details">
                            <span class="item-count">${transfer.item_count} ${__('items')}</span>
                            <span class="transfer-value">OMR ${(transfer.total_outgoing_value || 0).toLocaleString()}</span>
                            <span class="transfer-status status-${transfer.workflow_state.toLowerCase().replace(' ', '-')}">
                                ${__(transfer.workflow_state)}
                            </span>
                        </div>
                    </div>
                    
                    <div class="transfer-actions">
                        <button class="btn btn-sm btn-outline-primary view-details-btn" 
                                data-transfer-id="${transfer.name}">
                            <i class="fa fa-eye"></i> ${__('View')}
                        </button>
                        
                        ${this.getTransferActionButtons(transfer)}
                    </div>
                </div>
            `;
            
            container.append(html);
        });

        // Bind action events
        this.bindTransferActions();
    }

    getTransferActionButtons(transfer) {
        const status = transfer.workflow_state;
        let buttons = '';

        if (status === 'Draft') {
            buttons += `
                <button class="btn btn-sm btn-success approve-transfer-btn" 
                        data-transfer-id="${transfer.name}">
                    <i class="fa fa-check"></i> ${__('Approve')}
                </button>
            `;
        } else if (status === 'Source Approved') {
            buttons += `
                <button class="btn btn-sm btn-primary scan-item-btn" 
                        data-transfer-id="${transfer.name}" data-location="target">
                    <i class="fa fa-qrcode"></i> ${__('Scan')}
                </button>
                <button class="btn btn-sm btn-success complete-transfer-btn" 
                        data-transfer-id="${transfer.name}">
                    <i class="fa fa-check-circle"></i> ${__('Complete')}
                </button>
            `;
        }

        return buttons;
    }

    bindTransferActions() {
        $('.view-details-btn').off('click').on('click', (e) => {
            const transferId = $(e.target).closest('.view-details-btn').data('transfer-id');
            this.showTransferDetails(transferId);
        });
    }

    showTransferDetails(transferId) {
        frappe.call({
            method: 'universal_workshop.parts_inventory.stock_transfer.get_transfer_details',
            args: { transfer_id: transferId },
            callback: (r) => {
                if (r.message) {
                    this.renderTransferDetails(r.message);
                    $('#transfer-details-modal').modal('show');
                }
            }
        });
    }

    renderTransferDetails(transfer) {
        const html = `
            <div class="transfer-details-view">
                <div class="transfer-summary">
                    <h5>${transfer.transfer_id}</h5>
                    <div class="summary-grid">
                        <div class="summary-item">
                            <label>${__('From')}</label>
                            <span>${transfer.from_warehouse}</span>
                        </div>
                        <div class="summary-item">
                            <label>${__('To')}</label>
                            <span>${transfer.to_warehouse}</span>
                        </div>
                        <div class="summary-item">
                            <label>${__('Status')}</label>
                            <span class="badge badge-info">${__(transfer.status)}</span>
                        </div>
                        <div class="summary-item">
                            <label>${__('Priority')}</label>
                            <span>${transfer.priority}</span>
                        </div>
                        <div class="summary-item">
                            <label>${__('Total Value')}</label>
                            <span>OMR ${(transfer.total_value || 0).toLocaleString()}</span>
                        </div>
                        <div class="summary-item">
                            <label>${__('Requested By')}</label>
                            <span>${transfer.requested_by}</span>
                        </div>
                    </div>
                </div>

                <div class="transfer-items">
                    <h6>${__('Items')}</h6>
                    <div class="table-responsive">
                        <table class="table table-sm">
                            <thead>
                                <tr>
                                    <th>${__('Item')}</th>
                                    <th>${__('Qty')}</th>
                                    <th>${__('UOM')}</th>
                                    <th>${__('Rate')}</th>
                                    <th>${__('Amount')}</th>
                                    <th>${__('Scanned')}</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${transfer.items.map(item => `
                                    <tr>
                                        <td>
                                            <strong>${item.item_code}</strong><br>
                                            <small>${item.item_name}</small>
                                        </td>
                                        <td>${item.qty}</td>
                                        <td>${item.uom}</td>
                                        <td>OMR ${item.basic_rate.toFixed(3)}</td>
                                        <td>OMR ${item.basic_amount.toFixed(3)}</td>
                                        <td>
                                            <div class="scan-status">
                                                <span class="scan-indicator ${item.source_scanned ? 'scanned' : 'not-scanned'}">
                                                    <i class="fa fa-circle"></i> ${__('Source')}
                                                </span>
                                                <span class="scan-indicator ${item.target_scanned ? 'scanned' : 'not-scanned'}">
                                                    <i class="fa fa-circle"></i> ${__('Target')}
                                                </span>
                                            </div>
                                        </td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>

                ${transfer.logs && transfer.logs.length > 0 ? `
                    <div class="transfer-logs">
                        <h6>${__('Activity Log')}</h6>
                        <div class="timeline">
                            ${transfer.logs.map(log => `
                                <div class="timeline-item">
                                    <div class="timeline-marker"></div>
                                    <div class="timeline-content">
                                        <div class="timeline-header">
                                            <strong>${__(log.status)}</strong>
                                            <small>${frappe.datetime.str_to_user(log.timestamp)}</small>
                                        </div>
                                        <div class="timeline-body">
                                            ${log.remarks}
                                            <small class="text-muted">by ${log.user}</small>
                                        </div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
            </div>
        `;

        $('#transfer-details-content').html(html);
    }

    startBarcodeScanning(transferId, location) {
        this.current_transfer = transferId;
        this.scan_location = location;
        
        // Show scan section
        this.showSection('scan');
        
        // Set transfer in dropdown
        $('#scan-transfer-select').val(transferId);
        $(`input[name="scan-location"][value="${location}"]`).prop('checked', true);
        
        // Focus on manual input
        $('#manual-barcode').focus();
    }

    processBarcodeInput() {
        const barcode = $('#manual-barcode').val().trim();
        const transferId = $('#scan-transfer-select').val();
        const location = $('input[name="scan-location"]:checked').val();

        if (!barcode || !transferId || !location) {
            frappe.msgprint(__('Please enter barcode and select transfer'));
            return;
        }

        frappe.call({
            method: 'universal_workshop.parts_inventory.stock_transfer.scan_item_for_transfer',
            args: {
                transfer_id: transferId,
                barcode: barcode,
                location: location
            },
            callback: (r) => {
                if (r.message && r.message.success) {
                    this.showScanResult(r.message, true);
                    $('#manual-barcode').val('').focus();
                } else {
                    this.showScanResult(r.message, false);
                }
            }
        });
    }

    showScanResult(result, success) {
        const resultClass = success ? 'success' : 'danger';
        const icon = success ? 'check-circle' : 'exclamation-triangle';
        
        const html = `
            <div class="scan-result alert alert-${resultClass}">
                <div class="scan-result-header">
                    <i class="fa fa-${icon}"></i>
                    <strong>${success ? __('Scan Successful') : __('Scan Failed')}</strong>
                </div>
                <div class="scan-result-body">
                    ${success ? `
                        <div class="scanned-item">
                            <strong>${result.item_code}</strong> - ${result.item_name}<br>
                            <small>
                                ${__('Qty')}: ${result.qty} | 
                                ${__('Scanned')}: ${result.scanned_qty} | 
                                ${__('Remaining')}: ${result.remaining_qty}
                            </small>
                        </div>
                    ` : `
                        <p>${result.message}</p>
                    `}
                </div>
            </div>
        `;
        
        $('#scan-results').prepend(html);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            $('#scan-results .scan-result').first().fadeOut();
        }, 5000);
    }

    completeTransfer(transferId) {
        frappe.confirm(
            __('Are you sure you want to complete this transfer?'),
            () => {
                frappe.call({
                    method: 'universal_workshop.parts_inventory.stock_transfer.complete_transfer',
                    args: {
                        transfer_id: transferId,
                        target_remarks: ''
                    },
                    callback: (r) => {
                        if (r.message && r.message.success) {
                            frappe.msgprint({
                                title: __('Success'),
                                message: r.message.message,
                                indicator: 'green'
                            });
                            this.loadPendingTransfers();
                            this.loadDashboardData();
                        } else {
                            frappe.msgprint({
                                title: __('Error'),
                                message: r.message.message,
                                indicator: 'red'
                            });
                        }
                    }
                });
            }
        );
    }

    setupRealTimeUpdates() {
        // Poll for updates every 30 seconds
        setInterval(() => {
            const activeSection = $('.transfer-section:visible').attr('id');
            if (activeSection === 'dashboard-section') {
                this.loadDashboardData();
            } else if (activeSection === 'pending-section') {
                this.loadPendingTransfers();
            }
        }, 30000);
    }

    // Initialize form components
    initializeCreateForm() {
        this.loadWarehouses();
        this.setupCreateFormEvents();
    }

    loadWarehouses() {
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Warehouse',
                fields: ['name', 'warehouse_name'],
                filters: { 'is_group': 0 },
                limit_page_length: 100
            },
            callback: (r) => {
                if (r.message) {
                    const options = r.message.map(w => 
                        `<option value="${w.name}">${w.warehouse_name || w.name}</option>`
                    ).join('');
                    
                    $('#source-warehouse, #target-warehouse, #warehouse-filter').html(
                        `<option value="">${__('Select Warehouse')}</option>` + options
                    );
                }
            }
        });
    }

    setupCreateFormEvents() {
        $('#add-item-btn').off('click').on('click', () => {
            this.addItemRow();
        });

        $('#submit-transfer-btn').off('click').on('click', () => {
            this.submitTransfer();
        });

        $('#clear-form-btn').off('click').on('click', () => {
            this.clearCreateForm();
        });

        $('#process-barcode-btn').off('click').on('click', () => {
            this.processBarcodeInput();
        });

        $('#manual-barcode').off('keypress').on('keypress', (e) => {
            if (e.which === 13) {
                this.processBarcodeInput();
            }
        });
    }

    addItemRow() {
        const rowHtml = `
            <div class="item-row">
                <div class="row">
                    <div class="col-md-4">
                        <input type="text" class="form-control item-code" placeholder="${__('Item Code')}" required>
                    </div>
                    <div class="col-md-2">
                        <input type="number" class="form-control item-qty" placeholder="${__('Qty')}" step="0.001" required>
                    </div>
                    <div class="col-md-3">
                        <input type="number" class="form-control item-rate" placeholder="${__('Rate')}" step="0.001">
                    </div>
                    <div class="col-md-2">
                        <span class="item-amount">0.000</span>
                    </div>
                    <div class="col-md-1">
                        <button type="button" class="btn btn-sm btn-danger remove-item-btn">
                            <i class="fa fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        $('#transfer-items-list').append(rowHtml);
        
        // Bind events for new row
        this.bindItemRowEvents();
    }

    bindItemRowEvents() {
        $('.remove-item-btn').off('click').on('click', (e) => {
            $(e.target).closest('.item-row').remove();
        });

        $('.item-qty, .item-rate').off('input').on('input', (e) => {
            const row = $(e.target).closest('.item-row');
            const qty = parseFloat(row.find('.item-qty').val()) || 0;
            const rate = parseFloat(row.find('.item-rate').val()) || 0;
            const amount = qty * rate;
            row.find('.item-amount').text(amount.toFixed(3));
        });
    }

    submitTransfer() {
        const sourceWarehouse = $('#source-warehouse').val();
        const targetWarehouse = $('#target-warehouse').val();
        const priority = $('#transfer-priority').val();
        const remarks = $('#transfer-remarks').val();

        if (!sourceWarehouse || !targetWarehouse) {
            frappe.msgprint(__('Please select source and target warehouses'));
            return;
        }

        if (sourceWarehouse === targetWarehouse) {
            frappe.msgprint(__('Source and target warehouses cannot be the same'));
            return;
        }

        const items = [];
        $('.item-row').each(function() {
            const itemCode = $(this).find('.item-code').val();
            const qty = parseFloat($(this).find('.item-qty').val());
            const rate = parseFloat($(this).find('.item-rate').val());

            if (itemCode && qty > 0) {
                items.push({
                    item_code: itemCode,
                    qty: qty,
                    rate: rate || 0
                });
            }
        });

        if (items.length === 0) {
            frappe.msgprint(__('Please add at least one item'));
            return;
        }

        frappe.call({
            method: 'universal_workshop.parts_inventory.stock_transfer.create_stock_transfer',
            args: {
                source_warehouse: sourceWarehouse,
                target_warehouse: targetWarehouse,
                items: items,
                remarks: remarks,
                priority: priority
            },
            callback: (r) => {
                if (r.message && r.message.success) {
                    frappe.msgprint({
                        title: __('Success'),
                        message: r.message.message,
                        indicator: 'green'
                    });
                    this.clearCreateForm();
                    this.showSection('pending');
                } else {
                    frappe.msgprint({
                        title: __('Error'),
                        message: r.message.message,
                        indicator: 'red'
                    });
                }
            }
        });
    }

    clearCreateForm() {
        $('#source-warehouse, #target-warehouse').val('');
        $('#transfer-priority').val('Medium');
        $('#transfer-remarks').val('');
        $('#transfer-items-list').empty();
    }

    initializeScanInterface() {
        // Load transfers available for scanning
        this.loadTransfersForScanning();
    }

    loadTransfersForScanning() {
        frappe.call({
            method: 'universal_workshop.parts_inventory.stock_transfer.get_pending_transfers',
            args: {
                status: 'Source Approved',
                limit: 50
            },
            callback: (r) => {
                if (r.message) {
                    const options = r.message.map(t => 
                        `<option value="${t.name}">${t.name} - ${t.from_warehouse} → ${t.to_warehouse}</option>`
                    ).join('');
                    
                    $('#scan-transfer-select').html(
                        `<option value="">${__('Select Transfer to Scan')}</option>` + options
                    );
                }
            }
        });
    }
}

// CSS Styles for Stock Transfer UI
const stockTransferCSS = `
<style>
.stock-transfer-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

.stock-transfer-nav-bar {
    display: flex;
    background: #f8f9fa;
    border-radius: 8px;
    padding: 8px;
    margin-bottom: 20px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.nav-item {
    flex: 1;
    text-align: center;
    padding: 12px 8px;
    cursor: pointer;
    border-radius: 6px;
    transition: all 0.3s ease;
    position: relative;
}

.nav-item:hover {
    background: #e9ecef;
}

.nav-item.active {
    background: #007bff;
    color: white;
}

.nav-item .badge {
    position: absolute;
    top: 5px;
    right: 5px;
    font-size: 10px;
    min-width: 18px;
    height: 18px;
    line-height: 18px;
    border-radius: 9px;
}

.dashboard-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}

.dashboard-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
}

.metric-card {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    text-align: center;
}

.metric-value {
    font-size: 2rem;
    font-weight: bold;
    color: #007bff;
    margin-bottom: 5px;
}

.metric-label {
    color: #6c757d;
    font-size: 0.9rem;
}

.transfer-card {
    background: white;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    border-left: 4px solid #007bff;
}

.transfer-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}

.transfer-id {
    display: flex;
    align-items: center;
    gap: 8px;
}

.transfer-route {
    margin-bottom: 8px;
    font-weight: 500;
}

.transfer-route .fa-arrow-right {
    margin: 0 8px;
    color: #007bff;
}

.transfer-details {
    display: flex;
    gap: 16px;
    margin-bottom: 12px;
    font-size: 0.9rem;
    color: #6c757d;
}

.transfer-actions {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}

.scan-interface {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.scan-controls {
    margin-bottom: 20px;
}

.scan-location-toggle {
    margin-top: 10px;
}

.manual-input {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
}

.manual-input input {
    flex: 1;
}

.scan-result {
    margin-bottom: 10px;
    border-radius: 6px;
}

.scan-result-header {
    font-weight: bold;
    margin-bottom: 5px;
}

.create-transfer-form {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.items-section {
    margin: 20px 0;
}

.items-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
}

.item-row {
    background: #f8f9fa;
    padding: 15px;
    border-radius: 6px;
    margin-bottom: 10px;
}

.item-amount {
    font-weight: bold;
    color: #007bff;
    line-height: 38px;
}

.form-actions {
    text-align: center;
    margin-top: 20px;
}

.scan-indicator.scanned {
    color: #28a745;
}

.scan-indicator.not-scanned {
    color: #dc3545;
}

.timeline {
    position: relative;
    padding-left: 30px;
}

.timeline-item {
    position: relative;
    margin-bottom: 20px;
}

.timeline-marker {
    position: absolute;
    left: -35px;
    top: 5px;
    width: 10px;
    height: 10px;
    background: #007bff;
    border-radius: 50%;
}

.timeline-marker::before {
    content: '';
    position: absolute;
    left: 4px;
    top: 15px;
    width: 2px;
    height: 30px;
    background: #dee2e6;
}

.timeline-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 5px;
}

.no-transfers {
    text-align: center;
    padding: 40px;
    color: #6c757d;
}

.no-transfers i {
    font-size: 3rem;
    margin-bottom: 10px;
}

/* Mobile Responsive */
@media (max-width: 768px) {
    .stock-transfer-nav-bar {
        flex-wrap: wrap;
    }
    
    .nav-item {
        min-width: 80px;
        font-size: 0.8rem;
    }
    
    .dashboard-cards {
        grid-template-columns: repeat(2, 1fr);
    }
    
    .transfer-header {
        flex-direction: column;
        gap: 8px;
        align-items: flex-start;
    }
    
    .transfer-details {
        flex-direction: column;
        gap: 4px;
    }
    
    .transfer-actions {
        justify-content: space-between;
    }
    
    .manual-input {
        flex-direction: column;
    }
    
    .item-row .row {
        margin: 0;
    }
    
    .item-row .col-md-1,
    .item-row .col-md-2,
    .item-row .col-md-3,
    .item-row .col-md-4 {
        padding: 2px;
        margin-bottom: 8px;
    }
}

/* RTL Support */
[dir="rtl"] .transfer-route .fa-arrow-right {
    transform: scaleX(-1);
}

[dir="rtl"] .timeline {
    padding-left: 0;
    padding-right: 30px;
}

[dir="rtl"] .timeline-marker {
    left: auto;
    right: -35px;
}
</style>
`;

// Initialize Stock Transfer UI
frappe.ready(() => {
    if (frappe.boot.lang === 'ar') {
        $('html').attr('dir', 'rtl');
    }
    
    // Inject CSS
    if (!$('#stock-transfer-css').length) {
        $('head').append(`<style id="stock-transfer-css">${stockTransferCSS}</style>`);
    }
    
    // Initialize UI when needed
    window.stockTransferUI = new StockTransferUI();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = StockTransferUI;
} 