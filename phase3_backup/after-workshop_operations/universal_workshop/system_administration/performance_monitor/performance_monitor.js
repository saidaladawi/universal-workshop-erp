// -*- coding: utf-8 -*-
// Universal Workshop ERP - Performance Monitor JavaScript

frappe.ui.form.on('Performance Monitor', {
    refresh: function(frm) {
        frm.trigger('setup_arabic_fields');
        frm.trigger('setup_custom_buttons');
        frm.trigger('setup_metric_display');
        frm.trigger('setup_field_dependencies');
        
        if (!frm.doc.__islocal) {
            frm.trigger('setup_real_time_monitoring');
        }
    },
    
    setup_arabic_fields: function(frm) {
        // Set RTL direction for Arabic fields
        const arabic_fields = [
            'monitor_name_ar', 'alert_message_ar', 'monitoring_log_ar',
            'error_log_ar', 'performance_notes_ar', 'alert_log_ar'
        ];
        
        arabic_fields.forEach(field => {
            if (frm.fields_dict[field]) {
                const $field = frm.fields_dict[field].$input || 
                             frm.fields_dict[field].$wrapper.find('textarea, input');
                $field.attr('dir', 'rtl').css('text-align', 'right');
            }
        });
    },
    
    setup_custom_buttons: function(frm) {
        if (!frm.doc.__islocal) {
            // Collect Metrics Button
            frm.add_custom_button(__('Collect Metrics'), function() {
                frm.call('collect_all_metrics').then(r => {
                    if (r.message) {
                        frappe.msgprint({
                            title: __('Metrics Collected'),
                            message: r.message.message,
                            indicator: 'green'
                        });
                        frm.refresh();
                    }
                });
            }, __('Actions'));
            
            // Performance Dashboard Button
            frm.add_custom_button(__('Performance Dashboard'), function() {
                frm.trigger('show_dashboard');
            }, __('Actions'));
            
            // Export Metrics Button
            frm.add_custom_button(__('Export Metrics'), function() {
                frm.trigger('export_metrics');
            }, __('Actions'));
            
            // View Historical Data Button
            frm.add_custom_button(__('Historical Data'), function() {
                frm.trigger('show_historical_data');
            }, __('Actions'));
        }
    },
    
    setup_metric_display: function(frm) {
        // Setup metric display formatting
        if (frm.doc.cpu_usage_percent) {
            frm.fields_dict.cpu_usage_percent.$wrapper.find('.control-value')
                .css('color', frm.doc.cpu_usage_percent > 80 ? 'red' : 'green');
        }
        
        if (frm.doc.memory_usage_percent) {
            frm.fields_dict.memory_usage_percent.$wrapper.find('.control-value')
                .css('color', frm.doc.memory_usage_percent > 80 ? 'red' : 'green');
        }
        
        if (frm.doc.disk_usage_percent) {
            frm.fields_dict.disk_usage_percent.$wrapper.find('.control-value')
                .css('color', frm.doc.disk_usage_percent > 80 ? 'red' : 'green');
        }
    },
    
    setup_field_dependencies: function(frm) {
        // Show/hide alert fields based on status
        const alert_fields = ['alert_message', 'alert_message_ar', 'alert_severity', 'alert_recipients', 'alert_cooldown_minutes'];
        
        alert_fields.forEach(field => {
            frm.toggle_display(field, frm.doc.alert_status !== 'No Alert');
        });
        
        // Show/hide monitoring fields based on enabled status
        frm.toggle_display('monitoring_interval_seconds', frm.doc.monitoring_enabled);
        frm.toggle_display('last_check_time', frm.doc.monitoring_enabled);
    },
    
    setup_real_time_monitoring: function(frm) {
        if (frm.doc.monitoring_enabled && !frm.doc.__islocal) {
            // Setup real-time monitoring refresh
            frm.monitoring_interval = setInterval(() => {
                frappe.call({
                    method: 'universal_workshop.api.get_system_metrics',
                    callback: function(r) {
                        if (r.message && !r.message.error) {
                            frm.trigger('update_real_time_metrics', r.message);
                        }
                    }
                });
            }, (frm.doc.monitoring_interval_seconds || 30) * 1000);
        }
        
        // Clear interval when form is closed
        $(window).on('beforeunload', function() {
            if (frm.monitoring_interval) {
                clearInterval(frm.monitoring_interval);
            }
        });
    },
    
    update_real_time_metrics: function(frm, metrics) {
        // Update metric displays without saving
        if (metrics.cpu && metrics.cpu.cpu_usage_percent) {
            frm.set_df_property('cpu_usage_percent', 'description', 
                `${__('Current')}: ${metrics.cpu.cpu_usage_percent}%`);
        }
        
        if (metrics.memory && metrics.memory.memory_usage_percent) {
            frm.set_df_property('memory_usage_percent', 'description', 
                `${__('Current')}: ${metrics.memory.memory_usage_percent}%`);
        }
        
        if (metrics.disk && metrics.disk.disk_usage_percent) {
            frm.set_df_property('disk_usage_percent', 'description', 
                `${__('Current')}: ${metrics.disk.disk_usage_percent}%`);
        }
    },
    
    show_dashboard: function(frm) {
        const dialog = new frappe.ui.Dialog({
            title: __('Performance Dashboard'),
            size: 'large',
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'dashboard_html'
                }
            ]
        });
        
        // Build dashboard HTML
        const dashboard_html = `
            <div class="performance-dashboard">
                <div class="row">
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-header">
                                <h5>${__('CPU Usage')}</h5>
                            </div>
                            <div class="card-body text-center">
                                <div class="metric-value" style="font-size: 2em; color: ${frm.doc.cpu_usage_percent > 80 ? 'red' : 'green'}">
                                    ${frm.doc.cpu_usage_percent || 0}%
                                </div>
                                <div class="metric-label">${frm.doc.cpu_core_count || 0} ${__('cores')}</div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-header">
                                <h5>${__('Memory Usage')}</h5>
                            </div>
                            <div class="card-body text-center">
                                <div class="metric-value" style="font-size: 2em; color: ${frm.doc.memory_usage_percent > 80 ? 'red' : 'green'}">
                                    ${frm.doc.memory_usage_percent || 0}%
                                </div>
                                <div class="metric-label">${frm.doc.memory_used_gb || 0} / ${frm.doc.memory_total_gb || 0} GB</div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-header">
                                <h5>${__('Disk Usage')}</h5>
                            </div>
                            <div class="card-body text-center">
                                <div class="metric-value" style="font-size: 2em; color: ${frm.doc.disk_usage_percent > 80 ? 'red' : 'green'}">
                                    ${frm.doc.disk_usage_percent || 0}%
                                </div>
                                <div class="metric-label">${frm.doc.disk_used_gb || 0} / ${frm.doc.disk_total_gb || 0} GB</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                ${frm.doc.alert_status !== 'No Alert' ? `
                    <div class="row mt-3">
                        <div class="col-12">
                            <div class="alert alert-${frm.doc.alert_severity === 'Critical' ? 'danger' : 'warning'}">
                                <h6>${__('Active Alerts')}</h6>
                                <p>${frm.doc.alert_message}</p>
                                ${frappe.boot.lang === 'ar' && frm.doc.alert_message_ar ? 
                                    `<p dir="rtl">${frm.doc.alert_message_ar}</p>` : ''}
                            </div>
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
        
        dialog.fields_dict.dashboard_html.$wrapper.html(dashboard_html);
        dialog.show();
    },
    
    export_metrics: function(frm) {
        const metrics_data = {
            monitor_name: frm.doc.monitor_name,
            server_name: frm.doc.server_name,
            timestamp: frm.doc.last_check_time,
            cpu: {
                usage_percent: frm.doc.cpu_usage_percent,
                core_count: frm.doc.cpu_core_count,
                load_average: frm.doc.cpu_load_average_1min
            },
            memory: {
                usage_percent: frm.doc.memory_usage_percent,
                total_gb: frm.doc.memory_total_gb,
                used_gb: frm.doc.memory_used_gb
            },
            disk: {
                usage_percent: frm.doc.disk_usage_percent,
                total_gb: frm.doc.disk_total_gb,
                used_gb: frm.doc.disk_used_gb
            },
            alerts: {
                status: frm.doc.alert_status,
                message: frm.doc.alert_message
            }
        };
        
        const dataStr = JSON.stringify(metrics_data, null, 2);
        const dataBlob = new Blob([dataStr], {type: 'application/json'});
        const url = URL.createObjectURL(dataBlob);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = `performance_metrics_${frm.doc.name}_${frappe.datetime.now_datetime()}.json`;
        link.click();
        
        frappe.msgprint(__('Metrics exported successfully'));
    },
    
    show_historical_data: function(frm) {
        frappe.route_options = {
            "monitor_name": frm.doc.monitor_name,
            "server_name": frm.doc.server_name
        };
        frappe.set_route('List', 'Performance Monitor');
    },
    
    monitoring_enabled: function(frm) {
        frm.trigger('setup_field_dependencies');
        if (frm.doc.monitoring_enabled && !frm.doc.__islocal) {
            frm.trigger('setup_real_time_monitoring');
        } else if (frm.monitoring_interval) {
            clearInterval(frm.monitoring_interval);
        }
    },
    
    monitor_type: function(frm) {
        // Adjust fields based on monitor type
        if (frm.doc.monitor_type === 'System Performance') {
            frm.toggle_display(['cpu_section', 'memory_section', 'disk_section'], true);
            frm.toggle_display(['network_section', 'database_section', 'application_section'], false);
        } else if (frm.doc.monitor_type === 'Network Performance') {
            frm.toggle_display(['network_section'], true);
            frm.toggle_display(['cpu_section', 'memory_section', 'disk_section', 'database_section', 'application_section'], false);
        } else if (frm.doc.monitor_type === 'Database Performance') {
            frm.toggle_display(['database_section'], true);
            frm.toggle_display(['cpu_section', 'memory_section', 'disk_section', 'network_section', 'application_section'], false);
        } else if (frm.doc.monitor_type === 'Application Performance') {
            frm.toggle_display(['application_section'], true);
            frm.toggle_display(['cpu_section', 'memory_section', 'disk_section', 'network_section', 'database_section'], false);
        }
    },
    
    onload: function(frm) {
        // Set default values
        if (frm.doc.__islocal) {
            frm.set_value('monitoring_enabled', 1);
            frm.set_value('alert_enabled', 1);
            frm.set_value('monitoring_interval_seconds', 30);
            frm.set_value('cpu_threshold_warning', 70);
            frm.set_value('cpu_threshold_critical', 90);
            frm.set_value('memory_threshold_warning', 75);
            frm.set_value('memory_threshold_critical', 90);
            frm.set_value('disk_threshold_warning', 80);
            frm.set_value('disk_threshold_critical', 95);
        }
        
        frm.trigger('monitor_type');
    }
});
