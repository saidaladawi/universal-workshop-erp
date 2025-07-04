/**
 * Inventory Alerts Dashboard Integration for Universal Workshop ERP
 * Real-time inventory monitoring with Arabic localization support
 */

class InventoryAlertsDashboard {
    constructor(container_selector = '.inventory-alerts-container') {
        this.container = $(container_selector);
        this.alerts_cache = [];
        this.refresh_interval = 30000; // 30 seconds
        this.auto_refresh_timer = null;
        this.socket = null;
        this.language = frappe.boot.lang || 'en';
        this.is_rtl = this.language === 'ar';

        this.init();
    }

    init() {
        this.setup_container();
        this.setup_event_listeners();
        this.setup_websocket();
        this.load_alerts();
        this.start_auto_refresh();
    }

    setup_container() {
        if (!this.container.length) {
            console.warn('Inventory alerts container not found');
            return;
        }

        // Add RTL support if Arabic
        if (this.is_rtl) {
            this.container.addClass('rtl-layout');
            this.container.attr('dir', 'rtl');
        }

        // Initialize container structure
        this.container.html(`
            <div class="inventory-alerts-widget">
                <div class="alerts-header">
                    <h4 class="alerts-title">
                        <i class="fa fa-exclamation-triangle"></i>
                        ${this.is_rtl ? 'تنبيهات المخزون' : 'Inventory Alerts'}
                    </h4>
                    <div class="alerts-controls">
                        <button class="btn btn-sm btn-secondary refresh-alerts">
                            <i class="fa fa-refresh"></i>
                            ${this.is_rtl ? 'تحديث' : 'Refresh'}
                        </button>
                        <button class="btn btn-sm btn-primary configure-alerts">
                            <i class="fa fa-cog"></i>
                            ${this.is_rtl ? 'إعدادات' : 'Settings'}
                        </button>
                    </div>
                </div>
                <div class="alerts-content">
                    <div class="alerts-loading">
                        <div class="loading-spinner"></div>
                        <span>${this.is_rtl ? 'جاري التحميل...' : 'Loading...'}</span>
                    </div>
                    <div class="alerts-list"></div>
                    <div class="alerts-empty" style="display: none;">
                        <div class="empty-state">
                            <i class="fa fa-check-circle text-success"></i>
                            <p>${this.is_rtl ? 'لا توجد تنبيهات حالياً' : 'No alerts at this time'}</p>
                        </div>
                    </div>
                </div>
                <div class="alerts-footer">
                    <div class="alerts-summary">
                        <span class="total-alerts">0</span>
                        <span class="alerts-label">${this.is_rtl ? 'تنبيهات' : 'alerts'}</span>
                    </div>
                    <div class="alerts-actions">
                        <button class="btn btn-sm btn-outline-primary view-all-alerts">
                            ${this.is_rtl ? 'عرض جميع التنبيهات' : 'View All Alerts'}
                        </button>
                    </div>
                </div>
            </div>
        `);
    }

    setup_event_listeners() {
        // Refresh button
        this.container.on('click', '.refresh-alerts', () => {
            this.load_alerts(true);
        });

        // Configure alerts button
        this.container.on('click', '.configure-alerts', () => {
            this.show_configuration_dialog();
        });

        // View all alerts button
        this.container.on('click', '.view-all-alerts', () => {
            this.show_all_alerts();
        });

        // Alert card actions
        this.container.on('click', '.alert-card', (e) => {
            const alert_id = $(e.currentTarget).data('alert-id');
            this.show_alert_details(alert_id);
        });

        // Quick reorder buttons
        this.container.on('click', '.quick-reorder-btn', (e) => {
            e.stopPropagation();
            const alert_id = $(e.currentTarget).data('alert-id');
            this.show_reorder_dialog(alert_id);
        });

        // Dismiss alert buttons
        this.container.on('click', '.dismiss-alert-btn', (e) => {
            e.stopPropagation();
            const alert_id = $(e.currentTarget).data('alert-id');
            this.dismiss_alert(alert_id);
        });
    }

    setup_websocket() {
        // Setup WebSocket for real-time updates
        if (typeof io !== 'undefined') {
            this.socket = io();
            this.socket.on('inventory_alert_update', (data) => {
                this.handle_realtime_update(data);
            });
        }
    }

    load_alerts(force_refresh = false) {
        if (!force_refresh && this.alerts_cache.length > 0) {
            this.render_alerts(this.alerts_cache);
            return;
        }

        this.show_loading();

        frappe.call({
            method: 'universal_workshop.parts_inventory.inventory_alert_engine.get_dashboard_alerts',
            args: {
                limit: 10
            },
            callback: (response) => {
                if (response.message && response.message.status === 'success') {
                    this.alerts_cache = response.message.alerts;
                    this.render_alerts(this.alerts_cache);
                } else {
                    this.show_error('Failed to load alerts');
                }
            },
            error: () => {
                this.show_error('Network error while loading alerts');
            }
        });
    }

    render_alerts(alerts) {
        this.hide_loading();

        const alerts_list = this.container.find('.alerts-list');
        const alerts_empty = this.container.find('.alerts-empty');

        if (!alerts || alerts.length === 0) {
            alerts_list.hide();
            alerts_empty.show();
            this.update_summary(0);
            return;
        }

        alerts_empty.hide();
        alerts_list.show();

        const alerts_html = alerts.map(alert => this.render_alert_card(alert)).join('');
        alerts_list.html(alerts_html);

        this.update_summary(alerts.length);
    }

    render_alert_card(alert) {
        const severity_config = this.get_severity_config(alert.severity);
        const created_time = this.format_relative_time(alert.created_on);

        return `
            <div class="alert-card ${alert.severity}" data-alert-id="${alert.id}" 
                 style="border-left-color: ${severity_config.color}">
                <div class="alert-card-header">
                    <div class="alert-severity-badge" style="background-color: ${severity_config.color}">
                        ${this.is_rtl ? severity_config.label_ar : severity_config.label_en}
                    </div>
                    <div class="alert-type">
                        ${this.is_rtl ? alert.type_ar : alert.type_en}
                    </div>
                    <div class="alert-time" title="${alert.created_on}">
                        ${created_time}
                    </div>
                </div>
                <div class="alert-card-body">
                    <div class="alert-item-info">
                        <strong class="item-code">${alert.item_code}</strong>
                        <div class="item-name" dir="${this.is_rtl ? 'rtl' : 'ltr'}">
                            ${this.is_rtl && alert.item_name_ar ? alert.item_name_ar : alert.item_name}
                        </div>
                    </div>
                    <div class="alert-message" dir="${this.is_rtl ? 'rtl' : 'ltr'}">
                        ${this.is_rtl ? alert.message_ar : alert.message_en}
                    </div>
                    ${alert.current_stock !== undefined ? `
                        <div class="stock-info">
                            <span class="stock-level">
                                ${this.is_rtl ? 'المخزون الحالي:' : 'Current Stock:'} 
                                <strong>${this.format_number(alert.current_stock)}</strong>
                            </span>
                            ${alert.reorder_level ? `
                                <span class="reorder-level">
                                    ${this.is_rtl ? 'نقطة إعادة الطلب:' : 'Reorder Level:'} 
                                    <strong>${this.format_number(alert.reorder_level)}</strong>
                                </span>
                            ` : ''}
                        </div>
                    ` : ''}
                </div>
                <div class="alert-card-actions">
                    ${alert.allow_reorder ? `
                        <button class="btn btn-sm btn-success quick-reorder-btn" 
                                data-alert-id="${alert.id}">
                            <i class="fa fa-shopping-cart"></i>
                            ${this.is_rtl ? 'طلب سريع' : 'Quick Order'}
                        </button>
                    ` : ''}
                    <button class="btn btn-sm btn-outline-secondary dismiss-alert-btn" 
                            data-alert-id="${alert.id}">
                        <i class="fa fa-times"></i>
                        ${this.is_rtl ? 'إخفاء' : 'Dismiss'}
                    </button>
                </div>
            </div>
        `;
    }

    get_severity_config(severity) {
        const configs = {
            'critical': { color: '#dc3545', label_en: 'Critical', label_ar: 'حرج' },
            'high': { color: '#fd7e14', label_en: 'High', label_ar: 'عالي' },
            'medium': { color: '#ffc107', label_en: 'Medium', label_ar: 'متوسط' },
            'low': { color: '#17a2b8', label_en: 'Low', label_ar: 'منخفض' }
        };
        return configs[severity] || configs['medium'];
    }

    format_relative_time(datetime_str) {
        const now = new Date();
        const created = new Date(datetime_str);
        const diff = now - created;
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);

        if (this.is_rtl) {
            if (minutes < 1) return 'الآن';
            if (minutes < 60) return `منذ ${minutes} دقيقة`;
            if (hours < 24) return `منذ ${hours} ساعة`;
            return `منذ ${days} يوم`;
        } else {
            if (minutes < 1) return 'Now';
            if (minutes < 60) return `${minutes}m ago`;
            if (hours < 24) return `${hours}h ago`;
            return `${days}d ago`;
        }
    }

    format_number(number) {
        if (this.is_rtl) {
            // Convert to Arabic-Indic numerals
            return number.toString().replace(/[0-9]/g, (d) => '٠١٢٣٤٥٦٧٨٩'[d]);
        }
        return number.toString();
    }

    show_reorder_dialog(alert_id) {
        const alert = this.alerts_cache.find(a => a.id === alert_id);
        if (!alert) return;

        const dialog = new frappe.ui.Dialog({
            title: this.is_rtl ? 'طلب سريع - ' + alert.item_code : 'Quick Reorder - ' + alert.item_code,
            fields: [
                {
                    fieldtype: 'Float',
                    fieldname: 'quantity',
                    label: this.is_rtl ? 'الكمية' : 'Quantity',
                    reqd: 1,
                    default: alert.suggested_quantity || alert.reorder_level || 1
                },
                {
                    fieldtype: 'Select',
                    fieldname: 'order_type',
                    label: this.is_rtl ? 'نوع الطلب' : 'Order Type',
                    options: [
                        { value: 'purchase', label: this.is_rtl ? 'أمر شراء' : 'Purchase Order' },
                        { value: 'transfer', label: this.is_rtl ? 'طلب نقل' : 'Transfer Request' }
                    ],
                    default: 'purchase'
                }
            ],
            primary_action_label: this.is_rtl ? 'إنشاء الطلب' : 'Create Order',
            primary_action: (values) => {
                this.create_reorder(alert_id, values.quantity, values.order_type);
                dialog.hide();
            }
        });

        dialog.show();
    }

    create_reorder(alert_id, quantity, order_type) {
        frappe.call({
            method: 'universal_workshop.parts_inventory.inventory_alert_engine.create_quick_reorder',
            args: {
                alert_id: alert_id,
                quantity: quantity,
                order_type: order_type
            },
            callback: (response) => {
                if (response.message && response.message.status === 'success') {
                    frappe.show_alert({
                        message: this.is_rtl ? 'تم إنشاء الطلب بنجاح' : 'Order created successfully',
                        indicator: 'green'
                    });
                    this.load_alerts(true); // Refresh alerts
                } else {
                    frappe.show_alert({
                        message: this.is_rtl ? 'فشل في إنشاء الطلب' : 'Failed to create order',
                        indicator: 'red'
                    });
                }
            }
        });
    }

    show_configuration_dialog() {
        frappe.call({
            method: 'universal_workshop.parts_inventory.inventory_alert_engine.get_alert_configuration',
            callback: (response) => {
                if (response.message) {
                    this.render_configuration_dialog(response.message);
                }
            }
        });
    }

    render_configuration_dialog(config) {
        const dialog = new frappe.ui.Dialog({
            title: this.is_rtl ? 'إعدادات التنبيهات' : 'Alert Configuration',
            size: 'large',
            fields: [
                {
                    fieldtype: 'Check',
                    fieldname: 'system_enabled',
                    label: this.is_rtl ? 'تفعيل النظام' : 'System Enabled',
                    default: config.system_enabled
                },
                {
                    fieldtype: 'Select',
                    fieldname: 'notification_frequency',
                    label: this.is_rtl ? 'تكرار الإشعارات' : 'Notification Frequency',
                    options: [
                        { value: 'immediate', label: this.is_rtl ? 'فوري' : 'Immediate' },
                        { value: 'hourly', label: this.is_rtl ? 'كل ساعة' : 'Hourly' },
                        { value: 'daily', label: this.is_rtl ? 'يومي' : 'Daily' }
                    ],
                    default: config.notification_frequency
                },
                {
                    fieldtype: 'Section Break'
                },
                {
                    fieldtype: 'Check',
                    fieldname: 'enable_email',
                    label: this.is_rtl ? 'إشعارات البريد الإلكتروني' : 'Email Notifications',
                    default: config.notification_channels && config.notification_channels.includes('email')
                },
                {
                    fieldtype: 'Check',
                    fieldname: 'enable_in_app',
                    label: this.is_rtl ? 'الإشعارات داخل التطبيق' : 'In-App Notifications',
                    default: config.notification_channels && config.notification_channels.includes('in_app')
                }
            ],
            primary_action_label: this.is_rtl ? 'حفظ' : 'Save',
            primary_action: (values) => {
                this.save_configuration(values);
                dialog.hide();
            }
        });

        dialog.show();
    }

    save_configuration(values) {
        const updates = {
            system_enabled: values.system_enabled,
            notification_frequency: values.notification_frequency,
            notification_channels: []
        };

        if (values.enable_email) updates.notification_channels.push('email');
        if (values.enable_in_app) updates.notification_channels.push('in_app');

        frappe.call({
            method: 'universal_workshop.parts_inventory.inventory_alert_engine.update_alert_configuration',
            args: { updates: updates },
            callback: (response) => {
                if (response.message && response.message.status === 'success') {
                    frappe.show_alert({
                        message: this.is_rtl ? 'تم حفظ الإعدادات' : 'Configuration saved',
                        indicator: 'green'
                    });
                }
            }
        });
    }

    show_all_alerts() {
        frappe.set_route('List', 'Inventory Alert', 'List');
    }

    show_alert_details(alert_id) {
        const alert = this.alerts_cache.find(a => a.id === alert_id);
        if (!alert) return;

        // Open item form or show detailed alert information
        frappe.set_route('Form', 'Item', alert.item_code);
    }

    dismiss_alert(alert_id) {
        // Remove alert from display (could implement server-side dismissal)
        this.alerts_cache = this.alerts_cache.filter(a => a.id !== alert_id);
        this.render_alerts(this.alerts_cache);
    }

    handle_realtime_update(data) {
        if (data.type === 'new_alert') {
            this.alerts_cache.unshift(data.alert);
            this.render_alerts(this.alerts_cache);

            // Show notification for critical alerts
            if (data.alert.severity === 'critical') {
                frappe.show_alert({
                    message: this.is_rtl ?
                        `تنبيه حرج: ${data.alert.item_code}` :
                        `Critical Alert: ${data.alert.item_code}`,
                    indicator: 'red'
                });
            }
        } else if (data.type === 'alert_resolved') {
            this.alerts_cache = this.alerts_cache.filter(a => a.id !== data.alert_id);
            this.render_alerts(this.alerts_cache);
        }
    }

    start_auto_refresh() {
        this.auto_refresh_timer = setInterval(() => {
            this.load_alerts(true);
        }, this.refresh_interval);
    }

    stop_auto_refresh() {
        if (this.auto_refresh_timer) {
            clearInterval(this.auto_refresh_timer);
            this.auto_refresh_timer = null;
        }
    }

    show_loading() {
        this.container.find('.alerts-loading').show();
        this.container.find('.alerts-list, .alerts-empty').hide();
    }

    hide_loading() {
        this.container.find('.alerts-loading').hide();
    }

    show_error(message) {
        this.hide_loading();
        this.container.find('.alerts-list').html(`
            <div class="alert alert-danger">
                <i class="fa fa-exclamation-circle"></i>
                ${message}
            </div>
        `).show();
    }

    update_summary(count) {
        this.container.find('.total-alerts').text(this.format_number(count));
    }

    destroy() {
        this.stop_auto_refresh();
        if (this.socket) {
            this.socket.disconnect();
        }
        this.container.off();
    }
}

// Global initialization function
window.InventoryAlertsDashboard = InventoryAlertsDashboard;

// Auto-initialize if container exists
$(document).ready(() => {
    if ($('.inventory-alerts-container').length > 0) {
        window.inventory_alerts_dashboard = new InventoryAlertsDashboard();
    }
});

// Frappe integration for dashboard pages
frappe.ready(() => {
    // Initialize in dashboard context
    if (frappe.get_route()[0] === 'dashboard') {
        setTimeout(() => {
            if ($('.inventory-alerts-container').length > 0) {
                window.inventory_alerts_dashboard = new InventoryAlertsDashboard();
            }
        }, 1000);
    }
}); 