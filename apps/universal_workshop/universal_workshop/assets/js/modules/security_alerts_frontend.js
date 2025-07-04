/**
 * Security Alerts Frontend Integration
 * Universal Workshop ERP - User Management
 */

// =============================================================================
// Security Alert Log Form Integration
// =============================================================================

frappe.ui.form.on('Security Alert Log', {
    refresh: function(frm) {
        // Add custom buttons for alert management
        if (!frm.is_new()) {
            if (!frm.doc.is_resolved) {
                frm.add_custom_button(__('Mark as Resolved'), function() {
                    frm.trigger('resolve_alert');
                });
            }
            
            // Show alert details in formatted way
            if (frm.doc.details) {
                try {
                    let details = JSON.parse(frm.doc.details);
                    frm.trigger('format_alert_details', details);
                } catch (e) {
                    console.error('Error parsing alert details:', e);
                }
            }
            
            // Show notifications sent
            if (frm.doc.notifications_sent) {
                try {
                    let notifications = JSON.parse(frm.doc.notifications_sent);
                    frm.trigger('show_notifications_status', notifications);
                } catch (e) {
                    console.error('Error parsing notifications:', e);
                }
            }
        }
        
        // Set form colors based on severity
        frm.trigger('set_severity_styling');
    },
    
    resolve_alert: function(frm) {
        let dialog = new frappe.ui.Dialog({
            title: __('Resolve Security Alert'),
            fields: [
                {
                    fieldname: 'resolution_notes',
                    fieldtype: 'Text',
                    label: __('Resolution Notes'),
                    reqd: 1,
                    description: __('Describe the action taken to resolve this alert')
                }
            ],
            primary_action: function() {
                let values = dialog.get_values();
                
                frappe.call({
                    method: 'universal_workshop.user_management.security_alerts.resolve_security_alert',
                    args: {
                        alert_id: frm.doc.alert_id,
                        resolution_notes: values.resolution_notes
                    },
                    callback: function(r) {
                        if (r.message && r.message.success) {
                            frappe.msgprint(__('Alert resolved successfully'));
                            frm.reload_doc();
                        } else {
                            frappe.msgprint(__('Error resolving alert: ') + (r.message.error || 'Unknown error'));
                        }
                    }
                });
                
                dialog.hide();
            },
            primary_action_label: __('Resolve Alert')
        });
        
        dialog.show();
    },
    
    set_severity_styling: function(frm) {
        // Set form colors based on severity level
        let severity = frm.doc.severity;
        let color = '';
        
        switch (severity) {
            case 'critical':
                color = '#d32f2f'; // Red
                break;
            case 'high':
                color = '#f57c00'; // Orange
                break;
            case 'medium':
                color = '#fbc02d'; // Yellow
                break;
            case 'info':
                color = '#1976d2'; // Blue
                break;
            default:
                color = '#757575'; // Grey
        }
        
        // Apply styling
        frm.page.main.find('.form-layout').css('border-left', `4px solid ${color}`);
        frm.page.main.find('.form-layout').css('padding-left', '15px');
    },
    
    format_alert_details: function(frm, details) {
        // Create formatted display of alert details
        let formatted_html = '<div class="alert-details-container">';
        formatted_html += '<h4>' + __('Alert Details') + '</h4>';
        
        for (let key in details) {
            if (details.hasOwnProperty(key)) {
                formatted_html += `<p><strong>${key}:</strong> ${details[key]}</p>`;
            }
        }
        
        formatted_html += '</div>';
        
        // Add to form
        if (!frm.fields_dict.details_formatted) {
            frm.add_custom_button(__('Show Formatted Details'), function() {
                frappe.msgprint({
                    title: __('Alert Details'),
                    message: formatted_html,
                    indicator: 'blue'
                });
            });
        }
    },
    
    show_notifications_status: function(frm, notifications) {
        // Show which notifications were sent
        let status_html = '<div class="notifications-status">';
        status_html += '<h4>' + __('Notifications Sent') + '</h4>';
        
        if (notifications.length > 0) {
            status_html += '<ul>';
            notifications.forEach(function(channel) {
                status_html += `<li><i class="fa fa-check text-success"></i> ${channel.toUpperCase()}</li>`;
            });
            status_html += '</ul>';
        } else {
            status_html += '<p><i class="fa fa-exclamation-triangle text-warning"></i> ' + __('No notifications sent') + '</p>';
        }
        
        status_html += '</div>';
        
        // Add notification status button
        frm.add_custom_button(__('Notification Status'), function() {
            frappe.msgprint({
                title: __('Notification Status'),
                message: status_html,
                indicator: 'blue'
            });
        });
    }
});

// =============================================================================
// Security Dashboard Integration
// =============================================================================

frappe.pages['security-dashboard'].on_page_load = function(wrapper) {
    // Add security alerts widget to dashboard if not already present
    setTimeout(function() {
        add_security_alerts_widget(wrapper);
    }, 1000);
};

function add_security_alerts_widget(wrapper) {
    // Check if alerts widget already exists
    if ($(wrapper).find('.security-alerts-widget').length > 0) {
        return;
    }
    
    // Create alerts widget
    let alerts_widget = $(`
        <div class="security-alerts-widget col-md-6">
            <div class="card">
                <div class="card-header">
                    <h5><i class="fa fa-exclamation-triangle"></i> ${__('Recent Security Alerts')}</h5>
                </div>
                <div class="card-body">
                    <div id="alerts-summary">
                        <p>${__('Loading alerts...')}</p>
                    </div>
                </div>
            </div>
        </div>
    `);
    
    // Add to dashboard
    $(wrapper).find('.page-content .row').first().append(alerts_widget);
    
    // Load alerts data
    load_security_alerts_summary();
}

function load_security_alerts_summary() {
    frappe.call({
        method: 'universal_workshop.user_management.security_alerts.get_security_alerts_summary',
        args: {
            days: 7
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                display_alerts_summary(r.message.summary);
            } else {
                $('#alerts-summary').html('<p class="text-muted">' + __('Error loading alerts') + '</p>');
            }
        }
    });
}

function display_alerts_summary(summary) {
    let html = '';
    
    // Summary stats
    html += `
        <div class="row">
            <div class="col-md-6">
                <div class="metric">
                    <span class="metric-value">${summary.total_alerts}</span>
                    <span class="metric-label">${__('Total Alerts')}</span>
                </div>
            </div>
            <div class="col-md-6">
                <div class="metric">
                    <span class="metric-value text-danger">${summary.unresolved_alerts}</span>
                    <span class="metric-label">${__('Unresolved')}</span>
                </div>
            </div>
        </div>
    `;
    
    // Recent critical alerts
    if (summary.critical_alerts && summary.critical_alerts.length > 0) {
        html += '<h6 class="mt-3">' + __('Critical Alerts') + '</h6>';
        html += '<div class="alert-list">';
        
        summary.critical_alerts.forEach(function(alert) {
            html += `
                <div class="alert-item">
                    <span class="badge badge-danger">${alert.alert_type}</span>
                    <span class="alert-user">${alert.user_email}</span>
                    <span class="alert-time text-muted">${moment(alert.timestamp).fromNow()}</span>
                </div>
            `;
        });
        
        html += '</div>';
    }
    
    // View all link
    html += `
        <div class="mt-3">
            <a href="/app/security-alert-log" class="btn btn-sm btn-outline-primary">
                ${__('View All Alerts')}
            </a>
        </div>
    `;
    
    $('#alerts-summary').html(html);
}

// =============================================================================
// Real-time Alert Notifications
// =============================================================================

frappe.realtime.on('security_alert', function(data) {
    // Show real-time alert notification
    if (data && data.alert) {
        show_realtime_alert_notification(data.alert);
    }
});

function show_realtime_alert_notification(alert) {
    let indicator = 'red';
    let title = __('Security Alert');
    
    switch (alert.severity) {
        case 'critical':
            indicator = 'red';
            break;
        case 'high':
            indicator = 'orange';
            break;
        case 'medium':
            indicator = 'yellow';
            break;
        case 'info':
            indicator = 'blue';
            break;
    }
    
    // Show notification
    frappe.show_alert({
        message: `${title}: ${alert.description}`,
        indicator: indicator
    }, 10);
    
    // Also show as toast for critical alerts
    if (alert.severity === 'critical') {
        frappe.msgprint({
            title: __('Critical Security Alert'),
            message: `
                <div class="alert alert-danger">
                    <h5>${alert.description}</h5>
                    <p><strong>${__('User')}:</strong> ${alert.user_email}</p>
                    <p><strong>${__('Time')}:</strong> ${moment(alert.timestamp).format('YYYY-MM-DD HH:mm:ss')}</p>
                    <p><strong>${__('Source IP')}:</strong> ${alert.source_ip}</p>
                </div>
            `,
            indicator: 'red'
        });
    }
}

// =============================================================================
// Alert Management Functions
// =============================================================================

function trigger_test_alert() {
    // Function to trigger test alert (for development/testing)
    frappe.call({
        method: 'universal_workshop.user_management.security_alerts.trigger_security_alert',
        args: {
            event_type: 'suspicious_activity',
            user_email: frappe.session.user,
            source_ip: '127.0.0.1',
            details: JSON.stringify({
                test: true,
                description: 'Test alert triggered from frontend'
            })
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.msgprint(__('Test alert triggered successfully'));
                // Refresh alerts if on dashboard
                if (window.location.pathname.includes('security-dashboard')) {
                    load_security_alerts_summary();
                }
            } else {
                frappe.msgprint(__('Error triggering test alert'));
            }
        }
    });
}

// =============================================================================
// CSS Styling for Alerts
// =============================================================================

frappe.ready(function() {
    // Add custom CSS for alert styling
    $('head').append(`
        <style>
            .security-alerts-widget .metric {
                text-align: center;
                padding: 10px;
            }
            
            .security-alerts-widget .metric-value {
                display: block;
                font-size: 24px;
                font-weight: bold;
                line-height: 1;
            }
            
            .security-alerts-widget .metric-label {
                display: block;
                font-size: 12px;
                color: #666;
                margin-top: 5px;
            }
            
            .alert-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 8px 0;
                border-bottom: 1px solid #eee;
            }
            
            .alert-item:last-child {
                border-bottom: none;
            }
            
            .alert-user {
                flex: 1;
                margin: 0 10px;
                font-size: 13px;
            }
            
            .alert-time {
                font-size: 11px;
            }
            
            .alert-details-container {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                margin: 10px 0;
            }
            
            .notifications-status {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                margin: 10px 0;
            }
            
            .notifications-status ul {
                margin: 0;
                padding-left: 20px;
            }
            
            .notifications-status li {
                margin: 5px 0;
            }
        </style>
    `);
});
