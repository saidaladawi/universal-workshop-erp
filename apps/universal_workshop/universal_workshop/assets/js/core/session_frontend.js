/**
 * Session Management Frontend Integration
 * Universal Workshop ERP - User Management
 * 
 * Provides frontend integration for session management including:
 * - User form session controls
 * - Session monitoring dashboard
 * - Real-time session status updates
 * - Admin controls for session management
 */

// =============================================================================
// User Form Integration
// =============================================================================

frappe.ui.form.on('User', {
    refresh: function (frm) {
        if (!frm.is_new()) {
            // Add session management buttons
            frm.trigger('add_session_buttons');

            // Setup session policy fields
            frm.trigger('setup_session_policy_fields');

            // Load current sessions
            frm.trigger('load_user_sessions');
        }
    },

    add_session_buttons: function (frm) {
        // Add "View Sessions" button
        frm.add_custom_button(__('View Sessions'), function () {
            frappe.route_options = {
                "user_email": frm.doc.name
            };
            frappe.set_route("List", "Workshop User Session");
        }, __('Session Management'));

        // Add "Revoke All Sessions" button (for System Managers)
        if (frappe.user_roles.includes('System Manager')) {
            frm.add_custom_button(__('Revoke All Sessions'), function () {
                frm.trigger('revoke_all_sessions');
            }, __('Session Management'));
        }

        // Add "Session Statistics" button
        frm.add_custom_button(__('Session Statistics'), function () {
            frm.trigger('show_session_statistics');
        }, __('Session Management'));
    },

    setup_session_policy_fields: function (frm) {
        // Hide advanced session policy fields for non-System Managers
        if (!frappe.user_roles.includes('System Manager')) {
            frm.toggle_display(['session_policy', 'session_timeout_minutes',
                'max_concurrent_sessions', 'force_single_session'], false);
        }

        // Add help text for session policy fields
        frm.set_df_property('session_timeout_minutes', 'description',
            __('Custom idle timeout in minutes (0 = use role default). Range: 5-120 minutes.'));

        frm.set_df_property('max_concurrent_sessions', 'description',
            __('Maximum allowed concurrent sessions (0 = use role default). Range: 1-10 sessions.'));
    },

    load_user_sessions: function (frm) {
        // Load active sessions for this user
        frappe.call({
            method: 'universal_workshop.user_management.session_manager.get_user_sessions',
            args: {
                user_email: frm.doc.name,
                include_inactive: false
            },
            callback: function (r) {
                if (r.message && r.message.length > 0) {
                    frm.trigger('display_session_summary', [r.message]);
                }
            }
        });
    },

    display_session_summary: function (frm, sessions) {
        // Display session summary in the form
        let session_html = '<div class="session-summary">';
        session_html += `<h5>${__('Active Sessions')} (${sessions.length})</h5>`;

        sessions.forEach(function (session) {
            let device_info = JSON.parse(session.device_info || '{}');
            let last_activity = moment(session.last_activity).fromNow();

            session_html += `
                <div class="session-item" style="margin-bottom: 10px; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                    <strong>${device_info.browser || 'Unknown'}</strong> on ${device_info.os || 'Unknown'}
                    <br><small>IP: ${session.ip_address || 'Unknown'} | Last: ${last_activity}</small>
                    <button class="btn btn-xs btn-danger pull-right" onclick="revoke_session('${session.session_id}')">
                        ${__('Revoke')}
                    </button>
                </div>
            `;
        });

        session_html += '</div>';

        // Add to form sidebar
        frm.sidebar.add_user_action(__('Active Sessions'), function () {
            frappe.msgprint({
                title: __('Active Sessions'),
                message: session_html,
                wide: true
            });
        });
    },

    revoke_all_sessions: function (frm) {
        frappe.confirm(
            __('Are you sure you want to revoke all sessions for this user? They will be logged out immediately.'),
            function () {
                frappe.call({
                    method: 'universal_workshop.user_management.session_manager.revoke_user_sessions',
                    args: {
                        user_email: frm.doc.name,
                        reason: 'Revoked by administrator'
                    },
                    callback: function (r) {
                        if (r.message && r.message.success) {
                            frappe.msgprint(__('All sessions revoked successfully'));
                            frm.trigger('load_user_sessions');
                        }
                    }
                });
            }
        );
    },

    show_session_statistics: function (frm) {
        frappe.call({
            method: 'universal_workshop.user_management.session_manager.get_session_statistics',
            callback: function (r) {
                if (r.message) {
                    let stats = r.message;
                    let stats_html = `
                        <div class="session-statistics">
                            <h5>${__('Session Statistics')}</h5>
                            <table class="table table-bordered">
                                <tr><td><strong>${__('Total Active Sessions')}</strong></td><td>${stats.total_active_sessions}</td></tr>
                                <tr><td><strong>${__('Total Users Online')}</strong></td><td>${stats.total_users_online}</td></tr>
                                <tr><td><strong>${__('Sessions This Hour')}</strong></td><td>${stats.sessions_last_hour}</td></tr>
                                <tr><td><strong>${__('Peak Sessions Today')}</strong></td><td>${stats.peak_sessions_today}</td></tr>
                                <tr><td><strong>${__('Average Session Duration')}</strong></td><td>${stats.avg_session_duration} min</td></tr>
                                <tr><td><strong>${__('Expired Sessions Today')}</strong></td><td>${stats.expired_sessions_today}</td></tr>
                            </table>
                        </div>
                    `;

                    frappe.msgprint({
                        title: __('Session Statistics'),
                        message: stats_html,
                        wide: true
                    });
                }
            }
        });
    },

    // Field validations
    session_timeout_minutes: function (frm) {
        let timeout = frm.doc.session_timeout_minutes;
        if (timeout && (timeout < 5 || timeout > 120)) {
            frappe.msgprint(__('Session timeout must be between 5 and 120 minutes'));
            frm.set_value('session_timeout_minutes', 0);
        }
    },

    max_concurrent_sessions: function (frm) {
        let max_sessions = frm.doc.max_concurrent_sessions;
        if (max_sessions && (max_sessions < 1 || max_sessions > 10)) {
            frappe.msgprint(__('Max concurrent sessions must be between 1 and 10'));
            frm.set_value('max_concurrent_sessions', 0);
        }
    }
});

// =============================================================================
// Global Session Management Functions
// =============================================================================

window.revoke_session = function (session_id) {
    frappe.confirm(
        __('Are you sure you want to revoke this session?'),
        function () {
            frappe.call({
                method: 'universal_workshop.user_management.session_manager.revoke_session',
                args: {
                    session_id: session_id,
                    reason: 'Revoked by administrator'
                },
                callback: function (r) {
                    if (r.message && r.message.success) {
                        frappe.msgprint(__('Session revoked successfully'));
                        // Refresh current form if it's a User form
                        if (cur_frm && cur_frm.doctype === 'User') {
                            cur_frm.trigger('load_user_sessions');
                        }
                    }
                }
            });
        }
    );
};

// =============================================================================
// Workshop User Session List View Customization
// =============================================================================

frappe.listview_settings['Workshop User Session'] = {
    refresh: function (listview) {
        // Add bulk actions
        listview.page.add_action_item(__('Cleanup Expired'), function () {
            frappe.call({
                method: 'universal_workshop.user_management.session_manager.cleanup_expired_sessions',
                callback: function (r) {
                    if (r.message) {
                        frappe.msgprint(__('Cleaned up {0} expired sessions', [r.message.cleaned_count]));
                        listview.refresh();
                    }
                }
            });
        });

        listview.page.add_action_item(__('Session Statistics'), function () {
            frappe.call({
                method: 'universal_workshop.user_management.session_manager.get_session_statistics',
                callback: function (r) {
                    if (r.message) {
                        let stats = r.message;
                        let stats_html = `
                            <div class="session-statistics">
                                <h5>${__('System Session Statistics')}</h5>
                                <div class="row">
                                    <div class="col-md-6">
                                        <table class="table table-bordered">
                                            <tr><td><strong>${__('Total Active Sessions')}</strong></td><td>${stats.total_active_sessions}</td></tr>
                                            <tr><td><strong>${__('Total Users Online')}</strong></td><td>${stats.total_users_online}</td></tr>
                                            <tr><td><strong>${__('Sessions This Hour')}</strong></td><td>${stats.sessions_last_hour}</td></tr>
                                            <tr><td><strong>${__('Peak Sessions Today')}</strong></td><td>${stats.peak_sessions_today}</td></tr>
                                        </table>
                                    </div>
                                    <div class="col-md-6">
                                        <table class="table table-bordered">
                                            <tr><td><strong>${__('Average Session Duration')}</strong></td><td>${stats.avg_session_duration} min</td></tr>
                                            <tr><td><strong>${__('Expired Sessions Today')}</strong></td><td>${stats.expired_sessions_today}</td></tr>
                                            <tr><td><strong>${__('Suspicious Activities')}</strong></td><td>${stats.suspicious_activities || 0}</td></tr>
                                            <tr><td><strong>${__('System Load')}</strong></td><td>${stats.system_load || 'Normal'}</td></tr>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        `;

                        frappe.msgprint({
                            title: __('Session Statistics'),
                            message: stats_html,
                            wide: true
                        });
                    }
                }
            });
        });
    },

    get_indicator: function (doc) {
        if (!doc.is_active) {
            return [__("Inactive"), "red", "is_active,=,0"];
        } else if (new Date(doc.expiry_time) < new Date()) {
            return [__("Expired"), "orange", "expiry_time,<,Today"];
        } else if (doc.revoked_by) {
            return [__("Revoked"), "grey", "revoked_by,!=,"];
        } else {
            return [__("Active"), "green", "is_active,=,1"];
        }
    },

    formatters: {
        user_email: function (value) {
            return `<a href="/app/user/${value}">${value}</a>`;
        },

        device_info: function (value) {
            if (!value) return '';
            try {
                let device = JSON.parse(value);
                return `${device.browser || 'Unknown'} on ${device.os || 'Unknown'}`;
            } catch (e) {
                return 'Unknown Device';
            }
        },

        last_activity: function (value) {
            return value ? moment(value).fromNow() : '';
        },

        login_time: function (value) {
            return value ? moment(value).format('MMM DD, HH:mm') : '';
        }
    }
};

// =============================================================================
// Session Monitoring Widget (for Dashboard)
// =============================================================================

frappe.widgets.SessionMonitor = class SessionMonitor extends frappe.Widget {
    constructor(opts) {
        super(opts);
        this.refresh_interval = 30000; // 30 seconds
    }

    make() {
        super.make();
        this.setup_widget();
        this.start_monitoring();
    }

    setup_widget() {
        this.widget.addClass('session-monitor-widget');
        this.widget_head.html(__('Session Monitor'));

        this.widget_body.html(`
            <div class="session-stats">
                <div class="stats-item">
                    <span class="stats-number" id="active-sessions">-</span>
                    <span class="stats-label">${__('Active Sessions')}</span>
                </div>
                <div class="stats-item">
                    <span class="stats-number" id="users-online">-</span>
                    <span class="stats-label">${__('Users Online')}</span>
                </div>
                <div class="stats-item">
                    <span class="stats-number" id="peak-today">-</span>
                    <span class="stats-label">${__('Peak Today')}</span>
                </div>
            </div>
            <div class="session-actions">
                <button class="btn btn-sm btn-primary" onclick="frappe.set_route('List', 'Workshop User Session')">
                    ${__('View All Sessions')}
                </button>
            </div>
        `);
    }

    start_monitoring() {
        this.update_stats();
        this.monitor_interval = setInterval(() => {
            this.update_stats();
        }, this.refresh_interval);
    }

    update_stats() {
        frappe.call({
            method: 'universal_workshop.user_management.session_manager.get_session_statistics',
            callback: (r) => {
                if (r.message) {
                    let stats = r.message;
                    this.widget_body.find('#active-sessions').text(stats.total_active_sessions || 0);
                    this.widget_body.find('#users-online').text(stats.total_users_online || 0);
                    this.widget_body.find('#peak-today').text(stats.peak_sessions_today || 0);
                }
            }
        });
    }

    destroy() {
        if (this.monitor_interval) {
            clearInterval(this.monitor_interval);
        }
        super.destroy();
    }
};

// =============================================================================
// Auto-Session Timeout Warning
// =============================================================================

$(document).ready(function () {
    // Initialize session timeout warning system
    if (frappe.session && frappe.session.user !== 'Guest') {
        initializeSessionTimeoutWarning();
    }
});

function initializeSessionTimeoutWarning() {
    // Get current session status
    frappe.call({
        method: 'universal_workshop.user_management.session_manager.get_session_status',
        callback: function (r) {
            if (r.message && r.message.policy) {
                let policy = r.message.policy;
                let warning_ms = (policy.session_warning_minutes || 5) * 60 * 1000;
                let timeout_ms = (policy.idle_timeout_minutes || 30) * 60 * 1000;

                // Set warning timer
                setTimeout(function () {
                    showSessionTimeoutWarning(policy.session_warning_minutes || 5);
                }, timeout_ms - warning_ms);
            }
        }
    });
}

function showSessionTimeoutWarning(warning_minutes) {
    let dialog = new frappe.ui.Dialog({
        title: __('Session Timeout Warning'),
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'warning_message',
                options: `
                    <div class="alert alert-warning">
                        <h5>${__('Your session will expire in {0} minutes', [warning_minutes])}</h5>
                        <p>${__('Click "Extend Session" to continue working, or your session will be automatically logged out.')}</p>
                    </div>
                `
            }
        ],
        primary_action_label: __('Extend Session'),
        primary_action: function () {
            // Extend session by making a simple API call
            frappe.call({
                method: 'frappe.auth.get_logged_user',
                callback: function () {
                    frappe.msgprint(__('Session extended successfully'));
                    dialog.hide();
                    // Restart timeout monitoring
                    initializeSessionTimeoutWarning();
                }
            });
        },
        secondary_action_label: __('Logout Now'),
        secondary_action: function () {
            dialog.hide();
            frappe.app.logout();
        }
    });

    dialog.show();
} 