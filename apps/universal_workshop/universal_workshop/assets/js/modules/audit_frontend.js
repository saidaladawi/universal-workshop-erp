/**
 * Audit Trail Frontend Integration
 * Universal Workshop ERP - User Management
 */

// =============================================================================
// Security Audit Log Form Integration
// =============================================================================

frappe.ui.form.on('Security Audit Log', {
    refresh: function(frm) {
        // Add custom buttons for audit log management
        if (!frm.is_new()) {
            frm.add_custom_button(__('Mark as Reviewed'), function() {
                frm.set_value('reviewed', 1);
                frm.set_value('reviewed_by', frappe.session.user);
                frm.save();
            });
            
            // Show details in formatted way
            if (frm.doc.details) {
                try {
                    let details = JSON.parse(frm.doc.details);
                    let formatted_details = '';
                    
                    for (let key in details) {
                        formatted_details += `<strong>${key}:</strong> ${details[key]}<br>`;
                    }
                    
                    frm.set_df_property('details', 'description', formatted_details);
                } catch (e) {
                    console.log('Error parsing audit details:', e);
                }
            }
        }
        
        // Apply severity-based styling
        frm.trigger('apply_severity_styling');
    },
    
    apply_severity_styling: function(frm) {
        // Apply color coding based on severity
        let severity_colors = {
            'critical': '#d73527',
            'high': '#ff8c00',
            'medium': '#ffa500',
            'info': '#28a745'
        };
        
        if (frm.doc.severity && severity_colors[frm.doc.severity]) {
            frm.dashboard.add_indicator(
                __('Severity: {0}', [frm.doc.severity.toUpperCase()]), 
                severity_colors[frm.doc.severity]
            );
        }
    }
});

// =============================================================================
// User Form Audit Integration
// =============================================================================

frappe.ui.form.on('User', {
    refresh: function(frm) {
        if (!frm.is_new()) {
            // Add button to view user's audit trail
            frm.add_custom_button(__('View Audit Trail'), function() {
                frappe.route_options = {
                    'user_email': frm.doc.email
                };
                frappe.set_route('List', 'Security Audit Log');
            });
        }
    }
});

// =============================================================================
// Audit Event Logging Utilities
// =============================================================================

// Global function to log audit events from client side
window.log_audit_event = function(event_type, severity, description, details) {
    return frappe.call({
        method: 'universal_workshop.user_management.audit_trail_extension.log_audit_event',
        args: {
            event_type: event_type,
            severity: severity,
            description: description,
            details: details ? JSON.stringify(details) : null
        }
    });
};

// Hook into form saves to log document modifications
$(document).on('app_ready', function() {
    // Monitor sensitive DocType modifications
    let sensitive_doctypes = [
        'User', 'Role', 'Role Permission', 'User Role',
        'DocPerm', 'Custom Field', 'Property Setter'
    ];
    
    sensitive_doctypes.forEach(function(doctype) {
        frappe.ui.form.on(doctype, {
            after_save: function(frm) {
                if (frm.is_new()) {
                    // Document created
                    log_audit_event(
                        'role_assigned',
                        'medium',
                        `Created new ${doctype}: ${frm.doc.name}`,
                        {
                            doctype: doctype,
                            docname: frm.doc.name,
                            action: 'create'
                        }
                    );
                } else {
                    // Document modified
                    log_audit_event(
                        'permission_granted',
                        'medium',
                        `Modified ${doctype}: ${frm.doc.name}`,
                        {
                            doctype: doctype,
                            docname: frm.doc.name,
                            action: 'modify'
                        }
                    );
                }
            }
        });
    });
});

// =============================================================================
// List View Customizations
// =============================================================================

frappe.listview_settings['Security Audit Log'] = {
    onload: function(listview) {
        // Add filters for common audit queries
        listview.page.add_menu_item(__('Show Critical Events'), function() {
            listview.filter_area.add([[
                'Security Audit Log', 'severity', 'in', ['critical', 'high']
            ]]);
        });
        
        listview.page.add_menu_item(__('Show Recent Activity'), function() {
            let today = frappe.datetime.get_today();
            listview.filter_area.add([[
                'Security Audit Log', 'timestamp', '>=', today
            ]]);
        });
        
        listview.page.add_menu_item(__('Show Failed Logins'), function() {
            listview.filter_area.add([[
                'Security Audit Log', 'event_type', '=', 'login_failed'
            ]]);
        });
    },
    
    get_indicator: function(doc) {
        // Color coding for list view
        let severity_colors = {
            'critical': 'red',
            'high': 'orange',
            'medium': 'yellow',
            'info': 'green'
        };
        
        return [__(doc.severity.charAt(0).toUpperCase() + doc.severity.slice(1)), 
                severity_colors[doc.severity] || 'gray', 
                'severity,=,' + doc.severity];
    }
};

// =============================================================================
// Dashboard Integration
// =============================================================================

// Add audit metrics to security dashboard
if (frappe.pages && frappe.pages['security-dashboard']) {
    // This would integrate with the existing security dashboard
    // Adding audit trail metrics and charts
}

console.log('Audit Trail Frontend loaded successfully');
