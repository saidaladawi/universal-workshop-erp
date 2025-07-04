/**
 * Quality Control Workflow - Frontend Interface
 * Universal Workshop ERP - Arabic RTL Support
 */

class QualityControlUI {
    constructor() {
        this.currentLanguage = frappe.boot.lang || 'en';
        this.isRTL = this.currentLanguage === 'ar';
        this.currentChecklist = null;
        this.inspectionTimer = null;
        this.dashboardRefreshInterval = null;
        this.init();
    }

    init() {
        this.setupRealTimeUpdates();
        this.bindFormEvents();
        this.loadInspectionDashboard();

        if (this.isRTL) {
            this.setupRTLLayout();
        }
    }

    setupRealTimeUpdates() {
        // Listen for quality inspection updates
        frappe.realtime.on('quality_inspection_update', (data) => {
            this.handleInspectionUpdate(data);
        });

        // Listen for inspection item updates
        frappe.realtime.on('inspection_update', (data) => {
            this.handleItemUpdate(data);
        });
    }

    bindFormEvents() {
        // Service Order form integration
        if (cur_frm && cur_frm.doctype === 'Sales Order') {
            this.setupServiceOrderIntegration();
        }

        // Quality Inspection Checklist form integration
        if (cur_frm && cur_frm.doctype === 'Quality Inspection Checklist') {
            this.setupChecklistFormIntegration();
        }
    }

    setupServiceOrderIntegration() {
        // Add QC buttons to service order
        cur_frm.add_custom_button(__('Create Inspection Checklist'), () => {
            this.createInspectionChecklist(cur_frm.doc.name);
        }, __('Quality Control'));

        cur_frm.add_custom_button(__('View QC Dashboard'), () => {
            this.showInspectionDashboard(cur_frm.doc.name);
        }, __('Quality Control'));

        // Show QC status indicator
        this.showQCStatusIndicator();
    }

    setupChecklistFormIntegration() {
        // Add inspection control buttons
        if (cur_frm.doc.status !== 'approved' && cur_frm.doc.status !== 'rejected') {
            cur_frm.add_custom_button(__('Inspection Dashboard'), () => {
                this.showInspectionDashboard();
            });

            cur_frm.add_custom_button(__('Approve Checklist'), () => {
                this.approveChecklist();
            });

            cur_frm.add_custom_button(__('Reject Checklist'), () => {
                this.rejectChecklist();
            });
        }

        // Setup item grid controls
        this.setupInspectionItemGrid();

        // Auto-refresh dashboard
        this.startDashboardRefresh();
    }

    setupInspectionItemGrid() {
        // Add custom buttons to inspection items grid
        if (cur_frm.fields_dict.inspection_items) {
            cur_frm.fields_dict.inspection_items.grid.add_custom_button(__('Mark as Pass'),
                function (doc) {
                    this.updateInspectionItem(doc.item_code, 'pass');
                }.bind(this)
            );

            cur_frm.fields_dict.inspection_items.grid.add_custom_button(__('Mark as Fail'),
                function (doc) {
                    this.updateInspectionItem(doc.item_code, 'fail');
                }.bind(this)
            );
        }
    }

    createInspectionChecklist(serviceOrder) {
        // Show checklist creation dialog
        const dialog = new frappe.ui.Dialog({
            title: __('Create Inspection Checklist'),
            fields: [
                {
                    fieldtype: 'Select',
                    fieldname: 'checklist_type',
                    label: __('Checklist Type'),
                    options: [
                        'basic',
                        'comprehensive',
                        'safety_only',
                        'custom'
                    ],
                    default: 'comprehensive',
                    reqd: 1
                },
                {
                    fieldtype: 'Select',
                    fieldname: 'vehicle_type',
                    label: __('Vehicle Type'),
                    options: [
                        'passenger',
                        'commercial',
                        'motorcycle',
                        'truck',
                        'bus'
                    ],
                    default: 'passenger',
                    reqd: 1
                }
            ],
            primary_action_label: __('Create Checklist'),
            primary_action: (values) => {
                this.executeChecklistCreation(serviceOrder, values);
                dialog.hide();
            }
        });

        dialog.show();
    }

    executeChecklistCreation(serviceOrder, values) {
        frappe.call({
            method: 'universal_workshop.sales_service.quality_control.create_inspection_checklist',
            args: {
                service_order: serviceOrder,
                checklist_type: values.checklist_type,
                vehicle_type: values.vehicle_type
            },
            callback: (r) => {
                if (r.message && r.message.status === 'success') {
                    frappe.msgprint({
                        title: __('Success'),
                        message: r.message.message,
                        indicator: 'green'
                    });

                    // Open created checklist
                    frappe.set_route('Form', 'Quality Inspection Checklist', r.message.checklist_id);
                } else {
                    frappe.msgprint({
                        title: __('Error'),
                        message: r.message.message || __('Failed to create checklist'),
                        indicator: 'red'
                    });
                }
            },
            error: (xhr) => {
                frappe.msgprint({
                    title: __('Error'),
                    message: __('Failed to create inspection checklist'),
                    indicator: 'red'
                });
            }
        });
    }

    updateInspectionItem(itemCode, status) {
        if (!cur_frm.doc.name) {
            frappe.msgprint(__('Please save the checklist first'));
            return;
        }

        // Show item update dialog
        const dialog = new frappe.ui.Dialog({
            title: __('Update Inspection Item: {0}').format(itemCode),
            fields: [
                {
                    fieldtype: 'Select',
                    fieldname: 'status',
                    label: __('Status'),
                    options: ['pass', 'fail', 'n/a'],
                    default: status,
                    reqd: 1
                },
                {
                    fieldtype: 'Long Text',
                    fieldname: 'notes',
                    label: __('Inspector Notes')
                },
                {
                    fieldtype: 'JSON',
                    fieldname: 'measurements',
                    label: __('Measurements'),
                    description: __('Enter measurements as JSON: {"pressure": "32 PSI", "depth": "5mm"}')
                }
            ],
            primary_action_label: __('Update Item'),
            primary_action: (values) => {
                this.executeItemUpdate(itemCode, values);
                dialog.hide();
            }
        });

        dialog.show();
    }

    executeItemUpdate(itemCode, values) {
        frappe.call({
            method: 'universal_workshop.sales_service.quality_control.update_inspection_item',
            args: {
                checklist_id: cur_frm.doc.name,
                item_code: itemCode,
                status: values.status,
                notes: values.notes || '',
                measurements: values.measurements || null
            },
            callback: (r) => {
                if (r.message && r.message.status === 'success') {
                    frappe.msgprint({
                        title: __('Success'),
                        message: r.message.message,
                        indicator: 'green'
                    });

                    // Refresh form to show updates
                    cur_frm.reload_doc();

                    // Update dashboard
                    this.refreshInspectionProgress();
                } else {
                    frappe.msgprint({
                        title: __('Error'),
                        message: r.message.message || __('Failed to update item'),
                        indicator: 'red'
                    });
                }
            }
        });
    }

    approveChecklist() {
        // Show approval dialog
        const dialog = new frappe.ui.Dialog({
            title: __('Approve Inspection Checklist'),
            fields: [
                {
                    fieldtype: 'Long Text',
                    fieldname: 'approval_notes',
                    label: __('Approval Notes'),
                    description: __('Optional notes for approval')
                }
            ],
            primary_action_label: __('Approve'),
            primary_action: (values) => {
                this.executeApproval(values.approval_notes || '');
                dialog.hide();
            }
        });

        dialog.show();
    }

    executeApproval(approvalNotes) {
        frappe.call({
            method: 'universal_workshop.sales_service.quality_control.approve_inspection',
            args: {
                checklist_id: cur_frm.doc.name,
                approval_notes: approvalNotes
            },
            callback: (r) => {
                if (r.message && r.message.status === 'success') {
                    frappe.msgprint({
                        title: __('Success'),
                        message: r.message.message,
                        indicator: 'green'
                    });

                    // Refresh form
                    cur_frm.reload_doc();
                } else {
                    frappe.msgprint({
                        title: __('Error'),
                        message: r.message.message || __('Failed to approve checklist'),
                        indicator: 'red'
                    });
                }
            }
        });
    }

    rejectChecklist() {
        // Show rejection dialog
        const dialog = new frappe.ui.Dialog({
            title: __('Reject Inspection Checklist'),
            fields: [
                {
                    fieldtype: 'Long Text',
                    fieldname: 'rejection_reason',
                    label: __('Rejection Reason'),
                    description: __('Please provide reason for rejection'),
                    reqd: 1
                }
            ],
            primary_action_label: __('Reject'),
            primary_action: (values) => {
                this.executeRejection(values.rejection_reason);
                dialog.hide();
            }
        });

        dialog.show();
    }

    executeRejection(rejectionReason) {
        frappe.call({
            method: 'universal_workshop.sales_service.quality_control.reject_inspection',
            args: {
                checklist_id: cur_frm.doc.name,
                rejection_reason: rejectionReason
            },
            callback: (r) => {
                if (r.message && r.message.status === 'success') {
                    frappe.msgprint({
                        title: __('Success'),
                        message: r.message.message,
                        indicator: 'orange'
                    });

                    // Refresh form
                    cur_frm.reload_doc();
                } else {
                    frappe.msgprint({
                        title: __('Error'),
                        message: r.message.message || __('Failed to reject checklist'),
                        indicator: 'red'
                    });
                }
            }
        });
    }

    showInspectionDashboard(serviceOrder = null) {
        // Create dashboard dialog
        const dialog = new frappe.ui.Dialog({
            title: __('Quality Control Dashboard'),
            size: 'extra-large',
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'dashboard_content'
                }
            ]
        });

        // Load dashboard data
        this.loadDashboardData(serviceOrder, (data) => {
            const html = this.generateDashboardHTML(data);
            dialog.fields_dict.dashboard_content.$wrapper.html(html);

            // Setup dashboard interactions
            this.setupDashboardControls(dialog);
        });

        dialog.show();
    }

    loadDashboardData(serviceOrder, callback) {
        frappe.call({
            method: 'universal_workshop.sales_service.quality_control.get_inspection_dashboard',
            args: {
                service_order: serviceOrder,
                checklist_id: cur_frm ? cur_frm.doc.name : null
            },
            callback: (r) => {
                if (r.message && r.message.status === 'success') {
                    callback(r.message.data);
                } else {
                    frappe.msgprint({
                        title: __('Error'),
                        message: __('Failed to load dashboard data'),
                        indicator: 'red'
                    });
                }
            }
        });
    }

    generateDashboardHTML(data) {
        if (!data || data.length === 0) {
            return `<div class="text-center p-5">
                <h4>${__('No Inspection Checklists Found')}</h4>
                <p>${__('Create an inspection checklist to get started.')}</p>
            </div>`;
        }

        let html = `<div class="quality-dashboard ${this.isRTL ? 'rtl-layout' : ''}">`;

        data.forEach((checklist, index) => {
            html += this.generateChecklistCard(checklist, index);
        });

        html += '</div>';
        return html;
    }

    generateChecklistCard(checklist, index) {
        const progress = checklist.progress;
        const statusColor = this.getStatusColor(checklist.status);

        let html = `
            <div class="checklist-card mb-4 p-3 border rounded" style="border-left: 4px solid ${statusColor};">
                <div class="row">
                    <div class="col-md-8">
                        <h5>${checklist.checklist_type} - ${checklist.vehicle_type}</h5>
                        <p class="mb-1"><strong>${__('Status')}:</strong> 
                            <span class="badge" style="background-color: ${statusColor};">${checklist.status}</span>
                        </p>
                        <div class="progress mb-2" style="height: 8px;">
                            <div class="progress-bar" style="width: ${progress.completion_percentage}%; background-color: ${statusColor};"></div>
                        </div>
                        <small>${progress.completed_items}/${progress.total_items} ${__('items completed')} 
                               (${progress.completion_percentage.toFixed(1)}%)</small>
                    </div>
                    <div class="col-md-4 text-right">
                        <button class="btn btn-sm btn-primary mb-1" onclick="qualityControlUI.viewChecklistDetails('${checklist.checklist_id}')">
                            ${__('View Details')}
                        </button>
                        <br>
                        <small class="text-muted">${__('Created')}: ${frappe.datetime.str_to_user(checklist.creation_date)}</small>
                    </div>
                </div>
            </div>

            <div class="categories-section mb-4">
                <h6>${__('Inspection Categories')}</h6>
                <div class="row">
        `;

        // Add category breakdown
        Object.keys(checklist.items_by_category).forEach(category => {
            const categoryData = checklist.items_by_category[category];
            const categoryProgress = (categoryData.length > 0) ?
                ((categoryData.filter(item => item.status === 'pass' || item.status === 'fail').length / categoryData.length) * 100) : 0;

            html += `
                <div class="col-md-3 mb-2">
                    <div class="category-card p-2 border rounded">
                        <h6 class="mb-1">${category}</h6>
                        <div class="progress mb-1" style="height: 6px;">
                            <div class="progress-bar bg-info" style="width: ${categoryProgress}%;"></div>
                        </div>
                        <small>${categoryData.length} ${__('items')}</small>
                    </div>
                </div>
            `;
        });

        html += `
                </div>
            </div>
        `;

        return html;
    }

    getStatusColor(status) {
        const colors = {
            'draft': '#6c757d',
            'in_progress': '#007bff',
            'passed': '#28a745',
            'failed': '#dc3545',
            'approved': '#28a745',
            'rejected': '#dc3545'
        };
        return colors[status] || '#6c757d';
    }

    viewChecklistDetails(checklistId) {
        frappe.set_route('Form', 'Quality Inspection Checklist', checklistId);
    }

    setupDashboardControls(dialog) {
        // Add real-time refresh capability
        dialog.$wrapper.find('.quality-dashboard').append(`
            <div class="text-center mt-3">
                <button class="btn btn-sm btn-secondary" onclick="qualityControlUI.refreshDashboard()">
                    ${__('Refresh Dashboard')}
                </button>
            </div>
        `);
    }

    refreshDashboard() {
        if (cur_dialog && cur_dialog.fields_dict.dashboard_content) {
            this.loadDashboardData(null, (data) => {
                const html = this.generateDashboardHTML(data);
                cur_dialog.fields_dict.dashboard_content.$wrapper.html(html);
                this.setupDashboardControls(cur_dialog);
            });
        }
    }

    showQCStatusIndicator() {
        if (!cur_frm.doc.qc_status) return;

        const statusColor = this.getStatusColor(cur_frm.doc.qc_status.toLowerCase());
        const indicator = `
            <div class="qc-status-indicator" style="
                position: absolute;
                top: 10px;
                right: 10px;
                background: ${statusColor};
                color: white;
                padding: 5px 10px;
                border-radius: 15px;
                font-size: 12px;
                font-weight: bold;
            ">
                QC: ${cur_frm.doc.qc_status}
            </div>
        `;

        cur_frm.page.wrapper.find('.page-head').append(indicator);
    }

    refreshInspectionProgress() {
        if (cur_frm.doc.completion_percentage !== undefined) {
            // Update progress bar if exists
            const progressBar = cur_frm.page.wrapper.find('.inspection-progress-bar');
            if (progressBar.length) {
                progressBar.css('width', cur_frm.doc.completion_percentage + '%');
            }

            // Update progress text
            const progressText = cur_frm.page.wrapper.find('.inspection-progress-text');
            if (progressText.length) {
                progressText.text(`${cur_frm.doc.completion_percentage.toFixed(1)}% ${__('Complete')}`);
            }
        }
    }

    startDashboardRefresh() {
        // Auto-refresh every 30 seconds
        if (this.dashboardRefreshInterval) {
            clearInterval(this.dashboardRefreshInterval);
        }

        this.dashboardRefreshInterval = setInterval(() => {
            if (cur_frm && cur_frm.doctype === 'Quality Inspection Checklist') {
                this.refreshInspectionProgress();
            }
        }, 30000);
    }

    handleInspectionUpdate(data) {
        // Handle real-time inspection updates
        if (cur_frm && cur_frm.doc.name === data.checklist_id) {
            // Update form with new data
            cur_frm.doc.status = data.status;
            cur_frm.doc.completion_percentage = data.completion_percentage;
            cur_frm.doc.passed_items = data.passed_items;
            cur_frm.doc.failed_items = data.failed_items;
            cur_frm.doc.total_items = data.total_items;

            // Refresh form display
            cur_frm.refresh_fields();
            this.refreshInspectionProgress();

            // Show notification
            frappe.show_alert({
                message: __('Inspection updated'),
                indicator: 'blue'
            });
        }
    }

    handleItemUpdate(data) {
        // Handle individual item updates
        if (cur_frm && cur_frm.doc.name === data.checklist_id) {
            // Find and update the specific item
            const items = cur_frm.doc.inspection_items || [];
            const item = items.find(i => i.item_code === data.item_code);

            if (item) {
                item.status = data.status;
                cur_frm.refresh_field('inspection_items');
            }

            // Show notification
            frappe.show_alert({
                message: __('Item {0} updated: {1}').format(data.item_code, data.status),
                indicator: data.status === 'pass' ? 'green' : data.status === 'fail' ? 'red' : 'blue'
            });
        }
    }

    setupRTLLayout() {
        // Apply RTL styles for Arabic interface
        $('body').addClass('quality-control-rtl');

        // Adjust form layout for RTL
        cur_frm.page.wrapper.addClass('rtl-layout');

        // RTL-specific adjustments
        $('.quality-dashboard').addClass('rtl-layout');
    }

    generateInspectionReport(checklistId) {
        frappe.call({
            method: 'universal_workshop.sales_service.quality_control.generate_inspection_report',
            args: {
                checklist_id: checklistId
            },
            callback: (r) => {
                if (r.message && r.message.status === 'success') {
                    // Open report in new window or dialog
                    this.showInspectionReport(r.message.report);
                } else {
                    frappe.msgprint({
                        title: __('Error'),
                        message: __('Failed to generate inspection report'),
                        indicator: 'red'
                    });
                }
            }
        });
    }

    showInspectionReport(reportData) {
        // Show comprehensive inspection report
        const dialog = new frappe.ui.Dialog({
            title: __('Inspection Report'),
            size: 'extra-large',
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'report_content'
                }
            ]
        });

        const html = this.generateReportHTML(reportData);
        dialog.fields_dict.report_content.$wrapper.html(html);
        dialog.show();
    }

    generateReportHTML(reportData) {
        // Generate comprehensive report HTML
        return `
            <div class="inspection-report ${this.isRTL ? 'rtl-layout' : ''}">
                <div class="report-header text-center mb-4">
                    <h3>${__('Quality Inspection Report')}</h3>
                    <h4>${reportData.checklist_info.id}</h4>
                    <p>${__('Service Order')}: ${reportData.checklist_info.service_order}</p>
                    <p>${__('Customer')}: ${reportData.checklist_info.customer}</p>
                    <p>${__('Vehicle')}: ${reportData.checklist_info.vehicle_registration}</p>
                </div>

                <div class="report-summary mb-4 p-3 bg-light rounded">
                    <h5>${__('Summary')}</h5>
                    <div class="row">
                        <div class="col-md-3">
                            <strong>${__('Total Items')}: ${reportData.summary.total_items}</strong>
                        </div>
                        <div class="col-md-3">
                            <strong style="color: green;">${__('Passed')}: ${reportData.summary.passed_items}</strong>
                        </div>
                        <div class="col-md-3">
                            <strong style="color: red;">${__('Failed')}: ${reportData.summary.failed_items}</strong>
                        </div>
                        <div class="col-md-3">
                            <strong>${__('Completion')}: ${reportData.summary.completion_percentage.toFixed(1)}%</strong>
                        </div>
                    </div>
                </div>

                ${this.generateCategorySummary(reportData.categories)}
                ${this.generateFailedItemsList(reportData.failed_items)}
                ${this.generateRecommendations(reportData.recommendations)}
            </div>
        `;
    }

    generateCategorySummary(categories) {
        let html = '<div class="category-summary mb-4"><h5>' + __('Category Summary') + '</h5>';

        Object.keys(categories).forEach(category => {
            const data = categories[category];
            html += `
                <div class="category-item mb-2 p-2 border rounded">
                    <strong>${category}</strong>: 
                    ${data.passed}/${data.total} ${__('passed')} 
                    ${data.failed > 0 ? `(${data.failed} ${__('failed')})` : ''}
                </div>
            `;
        });

        html += '</div>';
        return html;
    }

    generateFailedItemsList(failedItems) {
        if (!failedItems || failedItems.length === 0) {
            return '';
        }

        let html = '<div class="failed-items mb-4"><h5 style="color: red;">' + __('Failed Items') + '</h5>';

        failedItems.forEach(item => {
            html += `
                <div class="failed-item mb-2 p-2 border border-danger rounded">
                    <strong>${item.name}</strong> (${item.category})
                    ${item.notes ? `<br><small>${item.notes}</small>` : ''}
                </div>
            `;
        });

        html += '</div>';
        return html;
    }

    generateRecommendations(recommendations) {
        if (!recommendations || recommendations.length === 0) {
            return '';
        }

        let html = '<div class="recommendations mb-4"><h5>' + __('Recommendations') + '</h5>';

        recommendations.forEach(rec => {
            html += `
                <div class="recommendation mb-2 p-2 border border-warning rounded">
                    <strong>${rec.item_name}</strong>: ${rec.action}
                    <br><small>${__('Priority')}: ${rec.priority} | ${__('Estimated Cost')}: ${rec.estimated_cost}</small>
                </div>
            `;
        });

        html += '</div>';
        return html;
    }
}

// Initialize Quality Control UI
let qualityControlUI;

frappe.ready(() => {
    qualityControlUI = new QualityControlUI();
});

// Form-specific integrations
frappe.ui.form.on('Sales Order', {
    refresh: function (frm) {
        if (qualityControlUI) {
            qualityControlUI.setupServiceOrderIntegration();
        }
    }
});

frappe.ui.form.on('Quality Inspection Checklist', {
    refresh: function (frm) {
        if (qualityControlUI) {
            qualityControlUI.setupChecklistFormIntegration();
        }
    },

    onload: function (frm) {
        // Setup inspection progress indicator
        if (frm.doc.completion_percentage !== undefined) {
            const progressHTML = `
                <div class="inspection-progress mt-2">
                    <div class="progress">
                        <div class="progress-bar inspection-progress-bar bg-info" 
                             style="width: ${frm.doc.completion_percentage}%"></div>
                    </div>
                    <small class="inspection-progress-text">${frm.doc.completion_percentage.toFixed(1)}% ${__('Complete')}</small>
                </div>
            `;

            frm.page.wrapper.find('.page-head .title-area').after(progressHTML);
        }
    }
});

frappe.ui.form.on('Quality Inspection Item', {
    status: function (frm, cdt, cdn) {
        // Auto-update parent checklist when item status changes
        if (qualityControlUI && frm.doc.name) {
            setTimeout(() => {
                qualityControlUI.refreshInspectionProgress();
            }, 500);
        }
    }
}); 