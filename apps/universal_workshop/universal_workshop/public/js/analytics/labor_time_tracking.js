// Labor Time Tracking Interface for Universal Workshop ERP
// Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors

frappe.provide('universal_workshop.labor_tracking');

// Main Labor Time Tracking Class
universal_workshop.labor_tracking.LaborTimeTracker = class {
    constructor(service_order_id) {
        this.service_order_id = service_order_id;
        this.active_sessions = [];
        this.refresh_interval = null;
        this.init();
    }

    init() {
        this.setup_rtl_support();
        this.load_active_sessions();
        this.setup_auto_refresh();
    }

    setup_rtl_support() {
        // Arabic RTL support
        if (frappe.boot.lang === 'ar') {
            $('body').addClass('labor-tracking-rtl');
        }
    }

    load_active_sessions() {
        frappe.call({
            method: 'universal_workshop.sales_service.labor_time_tracking.get_active_labor_tracking',
            args: {
                service_order_id: this.service_order_id
            },
            callback: (r) => {
                if (r.message) {
                    this.active_sessions = r.message;
                    this.render_tracking_interface();
                }
            }
        });
    }

    render_tracking_interface() {
        const container = $('<div class="labor-tracking-container">');
        
        const header = $(`
            <div class="labor-tracking-header">
                <h4>${__('Labor Time Tracking')}</h4>
                <button class="btn btn-primary btn-sm start-session-btn">
                    <i class="fa fa-play"></i> ${__('Start New Session')}
                </button>
            </div>
        `);
        
        const sessions_list = $(`
            <div class="active-sessions-list">
                ${this.render_active_sessions()}
            </div>
        `);
        
        const summary = $(`
            <div class="tracking-summary">
                ${this.render_summary()}
            </div>
        `);

        container.append(header, sessions_list, summary);

        // Bind events
        container.find('.start-session-btn').on('click', () => {
            this.start_new_session();
        });

        // Replace or append to form
        if ($('.labor-tracking-container').length) {
            $('.labor-tracking-container').replaceWith(container);
        } else {
            cur_frm.$wrapper.find('.layout-main-section').append(container);
        }
    }

    render_active_sessions() {
        if (!this.active_sessions.length) {
            return `<div class="text-center text-muted">${__('No active time tracking sessions')}</div>`;
        }

        return this.active_sessions.map(session => `
            <div class="time-session-card" data-session-id="${session.name}">
                <div class="session-header">
                    <div class="technician-info">
                        <strong>${session.technician}</strong>
                        <span class="activity-type">${session.activity_type}</span>
                    </div>
                    <div class="session-status status-${session.status.toLowerCase()}">
                        ${__(session.status)}
                    </div>
                </div>
                <div class="session-details">
                    <div class="time-info">
                        <span class="start-time">
                            <i class="fa fa-clock-o"></i>
                            ${__('Started')}: ${moment(session.start_time).format('HH:mm')}
                        </span>
                        <span class="elapsed-time">
                            <i class="fa fa-hourglass-half"></i>
                            ${__('Elapsed')}: ${this.format_duration(session.total_hours)}
                        </span>
                    </div>
                    <div class="session-controls">
                        ${this.render_session_controls(session)}
                    </div>
                </div>
            </div>
        `).join('');
    }

    render_session_controls(session) {
        const controls = [];

        if (session.status === 'Active') {
            controls.push(`
                <button class="btn btn-warning btn-xs pause-btn" data-session="${session.name}">
                    <i class="fa fa-pause"></i> ${__('Pause')}
                </button>
            `);
            controls.push(`
                <button class="btn btn-success btn-xs complete-btn" data-session="${session.name}">
                    <i class="fa fa-stop"></i> ${__('Complete')}
                </button>
            `);
        } else if (session.status === 'Paused') {
            controls.push(`
                <button class="btn btn-primary btn-xs resume-btn" data-session="${session.name}">
                    <i class="fa fa-play"></i> ${__('Resume')}
                </button>
            `);
            controls.push(`
                <button class="btn btn-success btn-xs complete-btn" data-session="${session.name}">
                    <i class="fa fa-stop"></i> ${__('Complete')}
                </button>
            `);
        }

        return controls.join(' ');
    }

    render_summary() {
        const total_hours = this.active_sessions.reduce((sum, session) => sum + (session.total_hours || 0), 0);
        const total_cost = this.active_sessions.reduce((sum, session) => 
            sum + ((session.total_hours || 0) * (session.hourly_rate || 0)), 0);

        return `
            <div class="tracking-summary-content">
                <div class="summary-item">
                    <span class="summary-label">${__('Active Sessions')}:</span>
                    <span class="summary-value">${this.active_sessions.length}</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">${__('Total Hours')}:</span>
                    <span class="summary-value">${this.format_duration(total_hours)}</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">${__('Estimated Cost')}:</span>
                    <span class="summary-value">${format_currency(total_cost, 'OMR')}</span>
                </div>
            </div>
        `;
    }

    format_duration(hours) {
        if (!hours) return '0h 0m';
        const h = Math.floor(hours);
        const m = Math.floor((hours - h) * 60);
        return `${h}h ${m}m`;
    }

    setup_auto_refresh() {
        // Refresh every 30 seconds
        this.refresh_interval = setInterval(() => {
            this.load_active_sessions();
        }, 30000);
    }

    start_new_session() {
        const d = new frappe.ui.Dialog({
            title: __('Start Time Tracking Session'),
            fields: [
                {
                    fieldtype: 'Link',
                    fieldname: 'technician',
                    label: __('Technician'),
                    options: 'Technician',
                    reqd: 1
                },
                {
                    fieldtype: 'Select',
                    fieldname: 'activity_type',
                    label: __('Activity Type'),
                    options: 'Service Work\nDiagnostics\nRepair\nMaintenance\nInspection\nTesting\nInstallation\nParts Replacement\nCustomization\nWarranty Work',
                    default: 'Service Work',
                    reqd: 1
                },
                {
                    fieldtype: 'Small Text',
                    fieldname: 'notes',
                    label: __('Initial Notes')
                }
            ],
            primary_action_label: __('Start Tracking'),
            primary_action: (values) => {
                frappe.call({
                    method: 'universal_workshop.sales_service.labor_time_tracking.start_labor_tracking',
                    args: {
                        service_order_id: this.service_order_id,
                        technician_id: values.technician,
                        activity_type: values.activity_type,
                        notes: values.notes
                    },
                    callback: (r) => {
                        if (r.message && r.message.success) {
                            frappe.show_alert({
                                message: r.message.message,
                                indicator: 'green'
                            });
                            d.hide();
                            this.load_active_sessions();
                        } else {
                            frappe.msgprint(r.message.message || __('Failed to start time tracking'));
                        }
                    }
                });
            }
        });

        d.show();
    }

    destroy() {
        if (this.refresh_interval) {
            clearInterval(this.refresh_interval);
        }
    }
};

// Initialize for Service Order form
if (typeof cur_frm !== 'undefined' && cur_frm.doctype === 'Service Order') {
    cur_frm.cscript.onload = function(frm) {
        // Add labor tracking section
        frm.add_custom_button(__('Labor Tracking'), function() {
            if (!frm.labor_tracker) {
                frm.labor_tracker = new universal_workshop.labor_tracking.LaborTimeTracker(frm.doc.name);
            } else {
                frm.labor_tracker.load_active_sessions();
            }
        }, __('Tools'));
    };
}

// Global functions for time tracking operations
universal_workshop.labor_tracking.pause_session = function (log_id) {
    frappe.prompt([
        {
            fieldtype: 'Data',
            fieldname: 'pause_reason',
            label: __('Pause Reason'),
            reqd: 1
        }
    ], function (values) {
        frappe.call({
            method: 'universal_workshop.sales_service.labor_time_tracking.pause_labor_tracking',
            args: {
                log_id: log_id,
                pause_reason: values.pause_reason
            },
            callback: function (r) {
                if (r.message && r.message.success) {
                    frappe.show_alert({
                        message: __('Time tracking paused'),
                        indicator: 'orange'
                    });
                    if (window.labor_tracker) {
                        window.labor_tracker.load_active_sessions();
                    }
                }
            }
        });
    }, __('Pause Time Tracking'), __('Pause'));
};

universal_workshop.labor_tracking.resume_session = function (log_id) {
    frappe.call({
        method: 'universal_workshop.sales_service.labor_time_tracking.resume_labor_tracking',
        args: {
            log_id: log_id
        },
        callback: function (r) {
            if (r.message && r.message.success) {
                frappe.show_alert({
                    message: __('Time tracking resumed'),
                    indicator: 'blue'
                });
                if (window.labor_tracker) {
                    window.labor_tracker.load_active_sessions();
                }
            }
        }
    });
};

universal_workshop.labor_tracking.complete_session = function (log_id) {
    frappe.prompt([
        {
            fieldtype: 'Small Text',
            fieldname: 'completion_notes',
            label: __('Completion Notes')
        }
    ], function (values) {
        frappe.call({
            method: 'universal_workshop.sales_service.labor_time_tracking.stop_labor_tracking',
            args: {
                log_id: log_id,
                completion_notes: values.completion_notes
            },
            callback: function (r) {
                if (r.message && r.message.success) {
                    frappe.show_alert({
                        message: __('Time tracking completed'),
                        indicator: 'green'
                    });
                    if (window.labor_tracker) {
                        window.labor_tracker.load_active_sessions();
                    }
                }
            }
        });
    }, __('Complete Time Tracking'), __('Complete'));
};

// Labor Time Tracking Dashboard
universal_workshop.labor_tracking.show_dashboard = function () {
    const d = new frappe.ui.Dialog({
        title: __('Labor Time Tracking Dashboard'),
        size: 'extra-large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'dashboard_html'
            }
        ]
    });

    d.fields_dict.dashboard_html.$wrapper.html(`
        <div class="labor-dashboard">
            <div class="dashboard-header">
                <h3>${__('Labor Time Tracking Overview')}</h3>
                <div class="dashboard-filters">
                    <input type="date" id="from_date" class="form-control" style="width: 150px; display: inline-block;">
                    <span style="margin: 0 10px;">${__('to')}</span>
                    <input type="date" id="to_date" class="form-control" style="width: 150px; display: inline-block;">
                    <button class="btn btn-primary btn-sm" onclick="universal_workshop.labor_tracking.load_dashboard_data()">
                        ${__('Refresh')}
                    </button>
                </div>
            </div>
            <div class="dashboard-content" id="dashboard_content">
                <div class="text-center">${__('Loading...')}</div>
            </div>
        </div>
    `);

    d.show();

    // Set default dates (last 7 days)
    const today = moment().format('YYYY-MM-DD');
    const week_ago = moment().subtract(7, 'days').format('YYYY-MM-DD');
    d.$wrapper.find('#from_date').val(week_ago);
    d.$wrapper.find('#to_date').val(today);

    // Load initial data
    setTimeout(() => {
        universal_workshop.labor_tracking.load_dashboard_data();
    }, 500);
};

universal_workshop.labor_tracking.load_dashboard_data = function () {
    const from_date = $('#from_date').val();
    const to_date = $('#to_date').val();

    frappe.call({
        method: 'universal_workshop.sales_service.labor_time_tracking.get_technician_productivity',
        args: {
            from_date: from_date,
            to_date: to_date
        },
        callback: function (r) {
            if (r.message) {
                universal_workshop.labor_tracking.render_dashboard(r.message);
            }
        }
    });
};

universal_workshop.labor_tracking.render_dashboard = function (data) {
    // Render dashboard content with charts and tables
    // This would include productivity metrics, charts, etc.
    $('#dashboard_content').html(`
        <div class="row">
            <div class="col-md-6">
                <div class="dashboard-widget">
                    <h4>${__('Productivity Metrics')}</h4>
                    <p>${__('Total Hours')}: ${data.metrics.total_hours}</p>
                    <p>${__('Total Revenue')}: ${format_currency(data.metrics.total_revenue, 'OMR')}</p>
                    <p>${__('Average per Hour')}: ${format_currency(data.metrics.avg_revenue_per_hour, 'OMR')}</p>
                </div>
            </div>
            <div class="col-md-6">
                <div class="dashboard-widget">
                    <h4>${__('Time Logs')}</h4>
                    <div class="time-logs-table">
                        ${data.time_logs.map(log => `
                            <div class="log-row">
                                <span>${log.service_order}</span>
                                <span>${log.total_hours}h</span>
                                <span>${format_currency(log.total_cost, 'OMR')}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        </div>
    `);
}; 