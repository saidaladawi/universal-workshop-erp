// -*- coding: utf-8 -*-
// Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
// For license information, please see license.txt

frappe.ui.form.on('System Health Monitor', {
    refresh: function(frm) {
        frm.trigger('setup_arabic_fields');
        frm.trigger('setup_custom_buttons');
        frm.trigger('setup_realtime_monitoring');
        frm.trigger('setup_field_dependencies');
        frm.trigger('update_status_indicators');
    },
    
    onload: function(frm) {
        frm.trigger('setup_arabic_interface');
        frm.trigger('load_dashboard_data');
    },
    
    setup_arabic_fields: function(frm) {
        // Set RTL direction for Arabic fields
        const arabic_fields = [
            'monitor_name_ar', 'alert_message_ar', 'notification_recipients',
            'alert_recipients', 'escalation_recipients'
        ];
        
        arabic_fields.forEach(field => {
            if (frm.fields_dict[field] && frm.fields_dict[field].$input) {
                frm.fields_dict[field].$input.attr('dir', 'rtl');
                frm.fields_dict[field].$input.css('text-align', 'right');
            }
        });
        
        // Apply RTL layout if Arabic is the primary language
        if (frappe.boot.lang === 'ar') {
            frm.page.main.addClass('rtl-layout');
        }
    },
    
    setup_custom_buttons: function(frm) {
        if (!frm.doc.__islocal) {
            // Health Check Actions
            frm.add_custom_button(__('Run Health Check / تشغيل فحص الصحة'), function() {
                frm.trigger('run_health_check');
            }, __('Actions / الإجراءات'));
            
            frm.add_custom_button(__('View Dashboard / عرض لوحة التحكم'), function() {
                frm.trigger('show_dashboard');
            }, __('Actions / الإجراءات'));
            
            frm.add_custom_button(__('Export Report / تصدير التقرير'), function() {
                frm.trigger('export_health_report');
            }, __('Actions / الإجراءات'));
            
            // Service Management
            if (frm.doc.auto_restart_services) {
                frm.add_custom_button(__('Restart Services / إعادة تشغيل الخدمات'), function() {
                    frm.trigger('show_service_restart_dialog');
                }, __('Service Management / إدارة الخدمات'));
            }
            
            frm.add_custom_button(__('System Info / معلومات النظام'), function() {
                frm.trigger('show_system_info');
            }, __('Service Management / إدارة الخدمات'));
            
            // Real-time Monitoring
            frm.add_custom_button(__('Start Monitoring / بدء المراقبة'), function() {
                frm.trigger('start_realtime_monitoring');
            }, __('Monitoring / المراقبة'));
            
            frm.add_custom_button(__('Stop Monitoring / إيقاف المراقبة'), function() {
                frm.trigger('stop_realtime_monitoring');
            }, __('Monitoring / المراقبة'));
            
            // Maintenance Actions
            if (frm.doc.maintenance_mode) {
                frm.add_custom_button(__('Exit Maintenance / الخروج من الصيانة'), function() {
                    frm.set_value('maintenance_mode', 0);
                    frm.save();
                }, __('Maintenance / الصيانة'));
            } else {
                frm.add_custom_button(__('Enter Maintenance / دخول الصيانة'), function() {
                    frm.set_value('maintenance_mode', 1);
                    frm.save();
                }, __('Maintenance / الصيانة'));
            }
        }
        
        // Create Default Monitor
        if (frm.doc.__islocal) {
            frm.add_custom_button(__('Create Default Monitor / إنشاء مراقب افتراضي'), function() {
                frm.trigger('create_default_monitor');
            });
        }
    },
    
    setup_realtime_monitoring: function(frm) {
        // Initialize real-time monitoring variables
        frm.realtime_monitoring = false;
        frm.monitoring_interval = null;
        frm.chart_data = {
            cpu: [],
            memory: [],
            disk: [],
            timestamps: []
        };
        
        // Create monitoring dashboard container
        if (!frm.dashboard_wrapper) {
            frm.dashboard_wrapper = $('<div class="system-health-dashboard" style="margin: 20px 0;"></div>');
            frm.dashboard_wrapper.insertAfter(frm.layout.wrapper.find('.form-page'));
        }
    },
    
    setup_field_dependencies: function(frm) {
        // Hardware monitoring dependencies
        frm.toggle_display(['cpu_usage_percent', 'cpu_threshold_warning', 'cpu_threshold_critical',
                           'memory_usage_percent', 'memory_total_gb', 'memory_used_gb',
                           'memory_threshold_warning', 'memory_threshold_critical',
                           'disk_usage_percent', 'disk_total_gb', 'disk_used_gb',
                           'disk_threshold_warning', 'disk_threshold_critical',
                           'cpu_temperature', 'system_load_1min', 'system_load_5min', 'system_load_15min'],
                          frm.doc.hardware_monitoring_enabled);
        
        // Software monitoring dependencies
        frm.toggle_display(['frappe_process_status', 'database_status', 'database_connection_count',
                           'database_slow_queries', 'background_jobs_running', 'background_jobs_pending',
                           'background_jobs_failed', 'redis_status', 'nginx_status', 'supervisor_status',
                           'python_version', 'frappe_version', 'erpnext_version', 'universal_workshop_version',
                           'last_backup_time'],
                          frm.doc.software_monitoring_enabled);
        
        // Network monitoring dependencies
        frm.toggle_display(['internet_connectivity', 'dns_resolution_time', 'api_endpoints_status',
                           'external_services_status', 'network_latency_ms', 'packet_loss_percent',
                           'email_service_status', 'sms_service_status', 'cloud_storage_status',
                           'license_server_status', 'vin_decoder_status', 'payment_gateway_status'],
                          frm.doc.network_monitoring_enabled);
        
        // Alert dependencies
        frm.toggle_display(['alert_level', 'alert_message', 'alert_message_ar', 'alert_count_today',
                           'last_alert_time', 'escalation_required', 'escalation_level'],
                          frm.doc.alerting_enabled);
        
        // Notification dependencies
        frm.toggle_display(['notification_recipients'], frm.doc.send_notifications);
        frm.toggle_display(['alert_recipients', 'escalation_recipients', 'alert_frequency_limit'],
                          frm.doc.alerting_enabled && frm.doc.send_notifications);
        
        // Maintenance dependencies
        frm.toggle_display(['maintenance_window_start', 'maintenance_window_end'],
                          frm.doc.scheduled_maintenance);
    },
    
    update_status_indicators: function(frm) {
        // Update health status indicator
        if (frm.doc.health_status) {
            let status_color = 'gray';
            if (frm.doc.health_status.includes('Healthy') || frm.doc.health_status.includes('سليم')) {
                status_color = 'green';
            } else if (frm.doc.health_status.includes('Warning') || frm.doc.health_status.includes('تحذير')) {
                status_color = 'orange';
            } else if (frm.doc.health_status.includes('Critical') || frm.doc.health_status.includes('حرج')) {
                status_color = 'red';
            } else if (frm.doc.health_status.includes('Down') || frm.doc.health_status.includes('متوقف')) {
                status_color = 'darkred';
            }
            
            frm.dashboard.add_indicator(__('Health Status / حالة الصحة'), status_color);
        }
        
        // Update overall score indicator
        if (frm.doc.overall_score !== undefined) {
            let score_color = 'gray';
            if (frm.doc.overall_score >= 90) {
                score_color = 'green';
            } else if (frm.doc.overall_score >= 70) {
                score_color = 'orange';
            } else if (frm.doc.overall_score >= 50) {
                score_color = 'red';
            } else {
                score_color = 'darkred';
            }
            
            frm.dashboard.add_indicator(`${__('Health Score / النتيجة الصحية')}: ${frm.doc.overall_score}%`, score_color);
        }
        
        // Update alert indicator
        if (frm.doc.alert_level && !frm.doc.alert_level.includes('None') && !frm.doc.alert_level.includes('لا شيء')) {
            let alert_color = 'yellow';
            if (frm.doc.alert_level.includes('Critical') || frm.doc.alert_level.includes('حرج')) {
                alert_color = 'red';
            } else if (frm.doc.alert_level.includes('Warning') || frm.doc.alert_level.includes('تحذير')) {
                alert_color = 'orange';
            }
            
            frm.dashboard.add_indicator(__('Active Alert / تنبيه نشط'), alert_color);
        }
    },
    
    setup_arabic_interface: function(frm) {
        // Set up Arabic interface elements
        if (frappe.boot.lang === 'ar') {
            // Add Arabic CSS class
            frm.wrapper.addClass('arabic-interface');
            
            // Adjust form layout for RTL
            frm.layout.wrapper.css('direction', 'rtl');
            
            // Set Arabic fonts
            frm.wrapper.find('input, textarea, select').css({
                'font-family': 'Tahoma, Arial, sans-serif',
                'direction': 'rtl',
                'text-align': 'right'
            });
        }
    },
    
    load_dashboard_data: function(frm) {
        if (!frm.doc.__islocal) {
            // Load system health dashboard data
            frappe.call({
                method: 'universal_workshop.workshop_management.doctype.system_health_monitor.system_health_monitor.get_system_health_dashboard',
                callback: function(r) {
                    if (r.message && !r.message.error) {
                        frm.system_health_data = r.message;
                        frm.trigger('render_dashboard_summary');
                    }
                }
            });
        }
    },
    
    render_dashboard_summary: function(frm) {
        if (frm.system_health_data && frm.dashboard_wrapper) {
            const data = frm.system_health_data;
            
            const dashboard_html = `
                <div class="row system-health-summary">
                    <div class="col-sm-12">
                        <h4>${__('System Health Summary / ملخص حالة النظام')}</h4>
                    </div>
                    <div class="col-sm-3">
                        <div class="health-metric">
                            <div class="metric-value">${data.summary.total_monitors}</div>
                            <div class="metric-label">${__('Total Monitors / إجمالي المراقبات')}</div>
                        </div>
                    </div>
                    <div class="col-sm-3">
                        <div class="health-metric healthy">
                            <div class="metric-value">${data.summary.healthy_monitors}</div>
                            <div class="metric-label">${__('Healthy / سليم')}</div>
                        </div>
                    </div>
                    <div class="col-sm-3">
                        <div class="health-metric warning">
                            <div class="metric-value">${data.summary.warning_monitors}</div>
                            <div class="metric-label">${__('Warning / تحذير')}</div>
                        </div>
                    </div>
                    <div class="col-sm-3">
                        <div class="health-metric critical">
                            <div class="metric-value">${data.summary.critical_monitors}</div>
                            <div class="metric-label">${__('Critical / حرج')}</div>
                        </div>
                    </div>
                </div>
                <style>
                    .health-metric {
                        text-align: center;
                        padding: 15px;
                        border: 1px solid #ddd;
                        border-radius: 4px;
                        margin-bottom: 10px;
                    }
                    .health-metric.healthy { border-color: #5cb85c; }
                    .health-metric.warning { border-color: #f0ad4e; }
                    .health-metric.critical { border-color: #d9534f; }
                    .metric-value {
                        font-size: 24px;
                        font-weight: bold;
                        margin-bottom: 5px;
                    }
                    .metric-label {
                        font-size: 12px;
                        color: #666;
                    }
                    .rtl-layout .health-metric {
                        text-align: center;
                    }
                </style>
            `;
            
            frm.dashboard_wrapper.html(dashboard_html);
        }
    },
    
    run_health_check: function(frm) {
        frappe.show_alert({
            message: __('Starting health check... / بدء فحص الصحة...'),
            indicator: 'blue'
        });
        
        frappe.call({
            method: 'run_health_check',
            doc: frm.doc,
            callback: function(r) {
                if (r.message) {
                    frappe.show_alert({
                        message: __('Health check completed / اكتمل فحص الصحة'),
                        indicator: 'green'
                    });
                    frm.reload_doc();
                } else {
                    frappe.show_alert({
                        message: __('Health check failed / فشل فحص الصحة'),
                        indicator: 'red'
                    });
                }
            }
        });
    },
    
    show_dashboard: function(frm) {
        const dashboard_dialog = new frappe.ui.Dialog({
            title: __('System Health Dashboard / لوحة تحكم صحة النظام'),
            size: 'extra-large',
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'dashboard_content'
                }
            ]
        });
        
        // Create comprehensive dashboard
        frm.trigger('create_health_dashboard', dashboard_dialog);
        dashboard_dialog.show();
    },
    
    create_health_dashboard: function(frm, dialog) {
        const dashboard_content = `
            <div class="system-health-dashboard">
                <div class="row">
                    <div class="col-sm-12">
                        <h3>${__('Real-time System Monitoring / المراقبة الفورية للنظام')}</h3>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-sm-4">
                        <div class="metric-card">
                            <h4>${__('CPU Usage / استخدام المعالج')}</h4>
                            <div class="metric-display">
                                <span class="metric-value" id="cpu-usage">${frm.doc.cpu_usage_percent || 0}%</span>
                                <div class="metric-bar">
                                    <div class="metric-fill" id="cpu-bar" style="width: ${frm.doc.cpu_usage_percent || 0}%"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-sm-4">
                        <div class="metric-card">
                            <h4>${__('Memory Usage / استخدام الذاكرة')}</h4>
                            <div class="metric-display">
                                <span class="metric-value" id="memory-usage">${frm.doc.memory_usage_percent || 0}%</span>
                                <div class="metric-bar">
                                    <div class="metric-fill" id="memory-bar" style="width: ${frm.doc.memory_usage_percent || 0}%"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-sm-4">
                        <div class="metric-card">
                            <h4>${__('Disk Usage / استخدام القرص')}</h4>
                            <div class="metric-display">
                                <span class="metric-value" id="disk-usage">${frm.doc.disk_usage_percent || 0}%</span>
                                <div class="metric-bar">
                                    <div class="metric-fill" id="disk-bar" style="width: ${frm.doc.disk_usage_percent || 0}%"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-sm-6">
                        <div class="status-card">
                            <h4>${__('Service Status / حالة الخدمات')}</h4>
                            <div class="service-list">
                                <div class="service-item">
                                    <span class="service-name">Frappe:</span>
                                    <span class="service-status ${frm.get_service_status_class(frm.doc.frappe_process_status)}">${frm.doc.frappe_process_status || 'Unknown'}</span>
                                </div>
                                <div class="service-item">
                                    <span class="service-name">${__('Database / قاعدة البيانات')}:</span>
                                    <span class="service-status ${frm.get_service_status_class(frm.doc.database_status)}">${frm.doc.database_status || 'Unknown'}</span>
                                </div>
                                <div class="service-item">
                                    <span class="service-name">Redis:</span>
                                    <span class="service-status ${frm.get_service_status_class(frm.doc.redis_status)}">${frm.doc.redis_status || 'Unknown'}</span>
                                </div>
                                <div class="service-item">
                                    <span class="service-name">Nginx:</span>
                                    <span class="service-status ${frm.get_service_status_class(frm.doc.nginx_status)}">${frm.doc.nginx_status || 'Unknown'}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-sm-6">
                        <div class="status-card">
                            <h4>${__('Network Status / حالة الشبكة')}</h4>
                            <div class="network-list">
                                <div class="network-item">
                                    <span class="network-name">${__('Internet / الإنترنت')}:</span>
                                    <span class="network-status ${frm.get_service_status_class(frm.doc.internet_connectivity)}">${frm.doc.internet_connectivity || 'Unknown'}</span>
                                </div>
                                <div class="network-item">
                                    <span class="network-name">${__('DNS Resolution / حل DNS')}:</span>
                                    <span class="network-value">${frm.doc.dns_resolution_time || 0}ms</span>
                                </div>
                                <div class="network-item">
                                    <span class="network-name">${__('Network Latency / زمن الاستجابة')}:</span>
                                    <span class="network-value">${frm.doc.network_latency_ms || 0}ms</span>
                                </div>
                                <div class="network-item">
                                    <span class="network-name">${__('Email Service / خدمة البريد')}:</span>
                                    <span class="network-status ${frm.get_service_status_class(frm.doc.email_service_status)}">${frm.doc.email_service_status || 'Unknown'}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-sm-12">
                        <div class="chart-card">
                            <h4>${__('Performance History / تاريخ الأداء')}</h4>
                            <div id="performance-chart" style="height: 300px;"></div>
                        </div>
                    </div>
                </div>
            </div>
            
            <style>
                .metric-card, .status-card, .chart-card {
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 15px;
                    margin-bottom: 15px;
                    background: #fff;
                }
                .metric-display {
                    text-align: center;
                }
                .metric-value {
                    font-size: 24px;
                    font-weight: bold;
                    display: block;
                    margin-bottom: 10px;
                }
                .metric-bar {
                    height: 20px;
                    background: #f5f5f5;
                    border-radius: 10px;
                    overflow: hidden;
                }
                .metric-fill {
                    height: 100%;
                    background: linear-gradient(to right, #5cb85c, #f0ad4e, #d9534f);
                    transition: width 0.3s ease;
                }
                .service-item, .network-item {
                    display: flex;
                    justify-content: space-between;
                    padding: 5px 0;
                    border-bottom: 1px solid #eee;
                }
                .service-status.online { color: #5cb85c; }
                .service-status.offline { color: #d9534f; }
                .service-status.error { color: #d9534f; }
                .service-status.running { color: #5cb85c; }
                .service-status.stopped { color: #d9534f; }
                .service-status.connected { color: #5cb85c; }
                .service-status.disconnected { color: #d9534f; }
                .network-value {
                    color: #337ab7;
                    font-weight: bold;
                }
                .rtl-layout .service-item, .rtl-layout .network-item {
                    direction: rtl;
                }
            </style>
        `;
        
        dialog.fields_dict.dashboard_content.$wrapper.html(dashboard_content);
        
        // Initialize performance chart
        frm.trigger('init_performance_chart');
    },
    
    get_service_status_class: function(status) {
        if (!status) return '';
        
        const status_lower = status.toLowerCase();
        if (status_lower.includes('running') || status_lower.includes('online') || 
            status_lower.includes('connected') || status_lower.includes('يعمل') || 
            status_lower.includes('متصل')) {
            return 'running';
        } else if (status_lower.includes('stopped') || status_lower.includes('offline') || 
                  status_lower.includes('disconnected') || status_lower.includes('متوقف') || 
                  status_lower.includes('منقطع')) {
            return 'stopped';
        } else if (status_lower.includes('error') || status_lower.includes('خطأ')) {
            return 'error';
        }
        return '';
    },
    
    init_performance_chart: function(frm) {
        // Initialize performance chart (would use Chart.js or similar)
        // For now, just placeholder
        const chart_container = $('#performance-chart');
        if (chart_container.length) {
            chart_container.html('<div style="text-align: center; padding: 50px; color: #999;">' +
                               __('Performance chart will be displayed here / سيتم عرض مخطط الأداء هنا') + '</div>');
        }
    },
    
    start_realtime_monitoring: function(frm) {
        if (frm.realtime_monitoring) {
            frappe.show_alert({
                message: __('Real-time monitoring is already active / المراقبة الفورية نشطة بالفعل'),
                indicator: 'blue'
            });
            return;
        }
        
        frm.realtime_monitoring = true;
        frm.monitoring_interval = setInterval(function() {
            frm.trigger('update_realtime_metrics');
        }, 5000); // Update every 5 seconds
        
        frappe.show_alert({
            message: __('Real-time monitoring started / بدأت المراقبة الفورية'),
            indicator: 'green'
        });
    },
    
    stop_realtime_monitoring: function(frm) {
        if (!frm.realtime_monitoring) {
            frappe.show_alert({
                message: __('Real-time monitoring is not active / المراقبة الفورية غير نشطة'),
                indicator: 'blue'
            });
            return;
        }
        
        frm.realtime_monitoring = false;
        if (frm.monitoring_interval) {
            clearInterval(frm.monitoring_interval);
            frm.monitoring_interval = null;
        }
        
        frappe.show_alert({
            message: __('Real-time monitoring stopped / توقفت المراقبة الفورية'),
            indicator: 'orange'
        });
    },
    
    update_realtime_metrics: function(frm) {
        if (!frm.realtime_monitoring) return;
        
        frappe.call({
            method: 'get_real_time_metrics',
            doc: frm.doc,
            callback: function(r) {
                if (r.message) {
                    const metrics = r.message;
                    
                    // Update CPU metric
                    if (metrics.cpu_usage !== undefined) {
                        $('#cpu-usage').text(metrics.cpu_usage.toFixed(1) + '%');
                        $('#cpu-bar').css('width', metrics.cpu_usage + '%');
                    }
                    
                    // Update Memory metric
                    if (metrics.memory_usage !== undefined) {
                        $('#memory-usage').text(metrics.memory_usage.toFixed(1) + '%');
                        $('#memory-bar').css('width', metrics.memory_usage + '%');
                    }
                    
                    // Update Disk metric
                    if (metrics.disk_usage !== undefined) {
                        $('#disk-usage').text(metrics.disk_usage.toFixed(1) + '%');
                        $('#disk-bar').css('width', metrics.disk_usage + '%');
                    }
                    
                    // Store data for chart
                    frm.chart_data.cpu.push(metrics.cpu_usage);
                    frm.chart_data.memory.push(metrics.memory_usage);
                    frm.chart_data.disk.push(metrics.disk_usage);
                    frm.chart_data.timestamps.push(new Date().toLocaleTimeString());
                    
                    // Keep only last 20 data points
                    if (frm.chart_data.cpu.length > 20) {
                        frm.chart_data.cpu.shift();
                        frm.chart_data.memory.shift();
                        frm.chart_data.disk.shift();
                        frm.chart_data.timestamps.shift();
                    }
                }
            }
        });
    },
    
    show_service_restart_dialog: function(frm) {
        const restart_dialog = new frappe.ui.Dialog({
            title: __('Restart Services / إعادة تشغيل الخدمات'),
            fields: [
                {
                    fieldtype: 'Select',
                    fieldname: 'service_name',
                    label: __('Service to Restart / الخدمة المراد إعادة تشغيلها'),
                    options: 'frappe\nredis\nnginx\nsupervisor',
                    reqd: 1
                },
                {
                    fieldtype: 'Small Text',
                    fieldname: 'restart_reason',
                    label: __('Restart Reason / سبب إعادة التشغيل'),
                    description: __('Provide reason for service restart / قدم سبب إعادة تشغيل الخدمة')
                }
            ],
            primary_action_label: __('Restart Service / إعادة تشغيل الخدمة'),
            primary_action: function(values) {
                frappe.call({
                    method: 'restart_service',
                    doc: frm.doc,
                    args: {
                        service_name: values.service_name
                    },
                    callback: function(r) {
                        if (r.message && r.message.success) {
                            frappe.show_alert({
                                message: r.message.message,
                                indicator: 'green'
                            });
                            frm.trigger('run_health_check');
                        } else {
                            frappe.show_alert({
                                message: r.message ? r.message.message : __('Service restart failed / فشل في إعادة تشغيل الخدمة'),
                                indicator: 'red'
                            });
                        }
                    }
                });
                restart_dialog.hide();
            }
        });
        
        restart_dialog.show();
    },
    
    show_system_info: function(frm) {
        const info_dialog = new frappe.ui.Dialog({
            title: __('System Information / معلومات النظام'),
            size: 'large',
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'system_info_content'
                }
            ]
        });
        
        const system_info_html = `
            <div class="system-info">
                <div class="row">
                    <div class="col-sm-6">
                        <h4>${__('Software Versions / إصدارات البرمجيات')}</h4>
                        <table class="table table-bordered">
                            <tr><td>Python:</td><td>${frm.doc.python_version || 'Unknown'}</td></tr>
                            <tr><td>Frappe:</td><td>${frm.doc.frappe_version || 'Unknown'}</td></tr>
                            <tr><td>ERPNext:</td><td>${frm.doc.erpnext_version || 'Unknown'}</td></tr>
                            <tr><td>Universal Workshop:</td><td>${frm.doc.universal_workshop_version || 'Unknown'}</td></tr>
                        </table>
                    </div>
                    <div class="col-sm-6">
                        <h4>${__('System Resources / موارد النظام')}</h4>
                        <table class="table table-bordered">
                            <tr><td>${__('Total Memory / إجمالي الذاكرة')}:</td><td>${frm.doc.memory_total_gb || 0} GB</td></tr>
                            <tr><td>${__('Used Memory / الذاكرة المستخدمة')}:</td><td>${frm.doc.memory_used_gb || 0} GB</td></tr>
                            <tr><td>${__('Total Disk / إجمالي القرص')}:</td><td>${frm.doc.disk_total_gb || 0} GB</td></tr>
                            <tr><td>${__('Used Disk / القرص المستخدم')}:</td><td>${frm.doc.disk_used_gb || 0} GB</td></tr>
                        </table>
                    </div>
                </div>
                <div class="row">
                    <div class="col-sm-12">
                        <h4>${__('Background Jobs / المهام الخلفية')}</h4>
                        <table class="table table-bordered">
                            <tr><td>${__('Running Jobs / المهام قيد التشغيل')}:</td><td>${frm.doc.background_jobs_running || 0}</td></tr>
                            <tr><td>${__('Pending Jobs / المهام المعلقة')}:</td><td>${frm.doc.background_jobs_pending || 0}</td></tr>
                            <tr><td>${__('Failed Jobs / المهام الفاشلة')}:</td><td>${frm.doc.background_jobs_failed || 0}</td></tr>
                        </table>
                    </div>
                </div>
            </div>
        `;
        
        info_dialog.fields_dict.system_info_content.$wrapper.html(system_info_html);
        info_dialog.show();
    },
    
    export_health_report: function(frm) {
        frappe.call({
            method: 'export_health_report',
            doc: frm.doc,
            callback: function(r) {
                if (r.message) {
                    // Create downloadable JSON file
                    const data = JSON.stringify(r.message, null, 2);
                    const blob = new Blob([data], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);
                    
                    const link = document.createElement('a');
                    link.href = url;
                    link.download = `system_health_report_${frm.doc.name}_${frappe.datetime.now_date()}.json`;
                    link.click();
                    
                    URL.revokeObjectURL(url);
                    
                    frappe.show_alert({
                        message: __('Health report exported / تم تصدير تقرير الصحة'),
                        indicator: 'green'
                    });
                }
            }
        });
    },
    
    create_default_monitor: function(frm) {
        frappe.call({
            method: 'universal_workshop.workshop_management.doctype.system_health_monitor.system_health_monitor.create_default_system_monitor',
            callback: function(r) {
                if (r.message && !r.message.error) {
                    frappe.show_alert({
                        message: r.message.message,
                        indicator: 'green'
                    });
                    
                    if (r.message.monitor_name) {
                        frappe.set_route('Form', 'System Health Monitor', r.message.monitor_name);
                    }
                } else {
                    frappe.show_alert({
                        message: r.message ? r.message.error : __('Failed to create default monitor / فشل في إنشاء المراقب الافتراضي'),
                        indicator: 'red'
                    });
                }
            }
        });
    },
    
    // Field event handlers
    monitoring_enabled: function(frm) {
        frm.trigger('setup_field_dependencies');
    },
    
    hardware_monitoring_enabled: function(frm) {
        frm.trigger('setup_field_dependencies');
    },
    
    software_monitoring_enabled: function(frm) {
        frm.trigger('setup_field_dependencies');
    },
    
    network_monitoring_enabled: function(frm) {
        frm.trigger('setup_field_dependencies');
    },
    
    alerting_enabled: function(frm) {
        frm.trigger('setup_field_dependencies');
    },
    
    send_notifications: function(frm) {
        frm.trigger('setup_field_dependencies');
    },
    
    scheduled_maintenance: function(frm) {
        frm.trigger('setup_field_dependencies');
    },
    
    monitor_name: function(frm) {
        // Auto-suggest Arabic name
        if (frm.doc.monitor_name && !frm.doc.monitor_name_ar) {
            const arabic_suggestions = {
                'Main System Monitor': 'مراقب النظام الرئيسي',
                'Hardware Monitor': 'مراقب الأجهزة',
                'Software Monitor': 'مراقب البرمجيات',
                'Network Monitor': 'مراقب الشبكة',
                'Database Monitor': 'مراقب قاعدة البيانات',
                'Application Monitor': 'مراقب التطبيق'
            };
            
            const arabic_name = arabic_suggestions[frm.doc.monitor_name];
            if (arabic_name) {
                frm.set_value('monitor_name_ar', arabic_name);
            }
        }
    },
    
    check_interval_minutes: function(frm) {
        // Validate check interval
        if (frm.doc.check_interval_minutes && frm.doc.check_interval_minutes < 1) {
            frappe.msgprint(__('Check interval must be at least 1 minute / يجب أن تكون فترة الفحص دقيقة واحدة على الأقل'));
            frm.set_value('check_interval_minutes', 5);
        }
    }
});

// List view customizations
frappe.listview_settings['System Health Monitor'] = {
    add_fields: ['health_status', 'overall_score', 'monitoring_enabled', 'last_check_time'],
    
    get_indicator: function(doc) {
        if (!doc.monitoring_enabled) {
            return [__('Disabled / معطل'), 'grey', 'monitoring_enabled,=,0'];
        }
        
        if (doc.health_status) {
            if (doc.health_status.includes('Healthy') || doc.health_status.includes('سليم')) {
                return [__('Healthy / سليم'), 'green', 'health_status,like,Healthy'];
            } else if (doc.health_status.includes('Warning') || doc.health_status.includes('تحذير')) {
                return [__('Warning / تحذير'), 'orange', 'health_status,like,Warning'];
            } else if (doc.health_status.includes('Critical') || doc.health_status.includes('حرج')) {
                return [__('Critical / حرج'), 'red', 'health_status,like,Critical'];
            } else if (doc.health_status.includes('Down') || doc.health_status.includes('متوقف')) {
                return [__('Down / متوقف'), 'darkred', 'health_status,like,Down'];
            }
        }
        
        return [__('Unknown / غير معروف'), 'grey', 'health_status,like,Unknown'];
    },
    
    button: {
        show: function(doc) {
            return doc.monitoring_enabled;
        },
        get_label: function() {
            return __('Run Check / تشغيل الفحص');
        },
        get_description: function(doc) {
            return __('Run health check for {0} / تشغيل فحص الصحة لـ {0}', [doc.monitor_name]);
        },
        action: function(doc) {
            frappe.call({
                method: 'universal_workshop.workshop_management.doctype.system_health_monitor.system_health_monitor.run_all_health_checks',
                callback: function(r) {
                    if (r.message) {
                        frappe.show_alert({
                            message: __('Health checks completed / اكتملت فحوصات الصحة'),
                            indicator: 'green'
                        });
                        cur_list.refresh();
                    }
                }
            });
        }
    }
}; 