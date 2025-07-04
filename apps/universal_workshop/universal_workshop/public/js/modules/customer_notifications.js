/**
 * Customer Notification System - Frontend Interface
 * Universal Workshop ERP - Arabic RTL Support
 */

class CustomerNotificationUI {
    constructor() {
        this.currentLanguage = frappe.boot.lang || 'en';
        this.isRTL = this.currentLanguage === 'ar';
        this.notificationHistory = [];
        this.realTimeSocket = null;
        this.init();
    }

    init() {
        this.setupRealTimeNotifications();
        this.loadNotificationHistory();
        this.bindFormEvents();

        if (this.isRTL) {
            this.setupRTLLayout();
        }
    }

    setupRealTimeNotifications() {
        // Connect to Frappe's real-time system
        if (typeof frappe.realtime !== 'undefined') {
            frappe.realtime.on('customer_notification', (data) => {
                this.handleRealTimeNotification(data);
            });
        }
    }

    handleRealTimeNotification(data) {
        const { notification_type, stage, service_order, customer, data: notificationData } = data;

        // Show real-time notification popup
        this.showNotificationPopup({
            type: notification_type,
            stage: stage,
            service_order: service_order,
            message: this.getNotificationMessage(notification_type, stage, notificationData),
            timestamp: notificationData.timestamp
        });

        // Update notification history
        this.addToNotificationHistory(data);

        // Play notification sound
        this.playNotificationSound();
    }

    showNotificationPopup(notification) {
        const isArabic = this.currentLanguage === 'ar';
        const direction = isArabic ? 'rtl' : 'ltr';

        const popup = $(`
            <div class="notification-popup ${isArabic ? 'rtl-layout' : ''}" 
                 style="direction: ${direction};">
                <div class="notification-content">
                    <div class="notification-header">
                        <i class="fa fa-bell notification-icon"></i>
                        <span class="notification-title">
                            ${isArabic ? 'إشعار جديد' : 'New Notification'}
                        </span>
                        <button class="close-notification" aria-label="Close">
                            <i class="fa fa-times"></i>
                        </button>
                    </div>
                    <div class="notification-body">
                        <div class="notification-type">
                            ${this.getNotificationTypeLabel(notification.type)}
                        </div>
                        <div class="notification-message">
                            ${notification.message}
                        </div>
                        <div class="notification-meta">
                            <span class="service-order">
                                ${isArabic ? 'رقم الطلب:' : 'Order:'} ${notification.service_order}
                            </span>
                            <span class="timestamp">
                                ${this.formatDateTime(notification.timestamp)}
                            </span>
                        </div>
                    </div>
                    <div class="notification-actions">
                        <button class="btn btn-sm btn-primary view-details">
                            ${isArabic ? 'عرض التفاصيل' : 'View Details'}
                        </button>
                        <button class="btn btn-sm btn-secondary mark-read">
                            ${isArabic ? 'تم القراءة' : 'Mark as Read'}
                        </button>
                    </div>
                </div>
            </div>
        `);

        // Add to page
        $('body').append(popup);

        // Show with animation
        setTimeout(() => {
            popup.addClass('show');
        }, 100);

        // Auto-hide after 10 seconds
        setTimeout(() => {
            this.hideNotificationPopup(popup);
        }, 10000);

        // Bind events
        popup.find('.close-notification, .mark-read').on('click', () => {
            this.hideNotificationPopup(popup);
        });

        popup.find('.view-details').on('click', () => {
            this.viewNotificationDetails(notification);
            this.hideNotificationPopup(popup);
        });
    }

    hideNotificationPopup(popup) {
        popup.removeClass('show');
        setTimeout(() => {
            popup.remove();
        }, 300);
    }

    getNotificationMessage(type, stage, data) {
        const isArabic = this.currentLanguage === 'ar';

        const messages = {
            'service_estimate': {
                'created': {
                    'en': `Service estimate created for ${data.vehicle_registration}`,
                    'ar': `تم إنشاء تقدير خدمة للمركبة ${data.vehicle_registration}`
                },
                'approved': {
                    'en': 'Service estimate approved - work starting',
                    'ar': 'تمت الموافقة على التقدير - العمل سيبدأ'
                }
            },
            'service_progress': {
                'started': {
                    'en': `Work started on ${data.vehicle_registration}`,
                    'ar': `بدأ العمل على المركبة ${data.vehicle_registration}`
                },
                'progress_update': {
                    'en': `Service ${data.progress_percentage}% complete`,
                    'ar': `الخدمة مكتملة ${data.progress_percentage}%`
                },
                'completed': {
                    'en': `${data.vehicle_registration} ready for pickup!`,
                    'ar': `${data.vehicle_registration} جاهزة للاستلام!`
                },
                'on_hold': {
                    'en': 'Service temporarily on hold',
                    'ar': 'الخدمة متوقفة مؤقتاً'
                }
            },
            'payment': {
                'reminder': {
                    'en': `Payment reminder: ${data.amount_due}`,
                    'ar': `تذكير بالدفع: ${data.amount_due}`
                },
                'received': {
                    'en': 'Payment received - Thank you!',
                    'ar': 'تم استلام الدفع - شكراً!'
                }
            },
            'appointment': {
                'scheduled': {
                    'en': 'Service appointment scheduled',
                    'ar': 'تم تحديد موعد الخدمة'
                },
                'reminder': {
                    'en': 'Service appointment reminder',
                    'ar': 'تذكير بموعد الخدمة'
                }
            }
        };

        const typeMessages = messages[type] || {};
        const stageMessage = typeMessages[stage] || {};

        return stageMessage[isArabic ? 'ar' : 'en'] ||
            `${type} - ${stage}`;
    }

    getNotificationTypeLabel(type) {
        const isArabic = this.currentLanguage === 'ar';

        const labels = {
            'service_estimate': {
                'en': 'Service Estimate',
                'ar': 'تقدير الخدمة'
            },
            'service_progress': {
                'en': 'Service Progress',
                'ar': 'تقدم الخدمة'
            },
            'payment': {
                'en': 'Payment',
                'ar': 'الدفع'
            },
            'appointment': {
                'en': 'Appointment',
                'ar': 'الموعد'
            }
        };

        const typeLabel = labels[type] || {};
        return typeLabel[isArabic ? 'ar' : 'en'] || type;
    }

    setupNotificationDashboard() {
        const isArabic = this.currentLanguage === 'ar';

        const dashboard = new frappe.ui.Dialog({
            title: isArabic ? 'إدارة الإشعارات' : 'Notification Management',
            size: 'large',
            fields: [
                {
                    fieldtype: 'Section Break',
                    label: isArabic ? 'إرسال إشعار جديد' : 'Send New Notification'
                },
                {
                    fieldname: 'notification_type',
                    fieldtype: 'Select',
                    label: isArabic ? 'نوع الإشعار' : 'Notification Type',
                    options: [
                        'service_estimate',
                        'service_progress',
                        'payment',
                        'appointment'
                    ],
                    reqd: 1
                },
                {
                    fieldname: 'stage',
                    fieldtype: 'Select',
                    label: isArabic ? 'المرحلة' : 'Stage',
                    depends_on: 'notification_type',
                    reqd: 1
                },
                {
                    fieldname: 'service_order',
                    fieldtype: 'Link',
                    options: 'Sales Order',
                    label: isArabic ? 'أمر الخدمة' : 'Service Order'
                },
                {
                    fieldname: 'customer',
                    fieldtype: 'Link',
                    options: 'Customer',
                    label: isArabic ? 'العميل' : 'Customer'
                },
                {
                    fieldtype: 'Column Break'
                },
                {
                    fieldname: 'send_email',
                    fieldtype: 'Check',
                    label: isArabic ? 'إرسال بريد إلكتروني' : 'Send Email',
                    default: 1
                },
                {
                    fieldname: 'send_sms',
                    fieldtype: 'Check',
                    label: isArabic ? 'إرسال رسالة نصية' : 'Send SMS',
                    default: 1
                },
                {
                    fieldtype: 'Section Break',
                    label: isArabic ? 'بيانات إضافية' : 'Additional Data'
                },
                {
                    fieldname: 'custom_data',
                    fieldtype: 'Code',
                    label: isArabic ? 'بيانات مخصصة (JSON)' : 'Custom Data (JSON)',
                    options: 'JSON',
                    description: isArabic ?
                        'بيانات إضافية لتخصيص الإشعار (تنسيق JSON)' :
                        'Additional data for notification customization (JSON format)'
                }
            ],
            primary_action_label: isArabic ? 'إرسال الإشعار' : 'Send Notification',
            primary_action: (values) => {
                this.sendNotificationFromDialog(values);
                dashboard.hide();
            }
        });

        // Update stage options based on notification type
        dashboard.fields_dict.notification_type.$input.on('change', function () {
            const type = $(this).val();
            const stageOptions = this.getStageOptions(type);
            dashboard.set_df_property('stage', 'options', stageOptions);
        }.bind(this));

        dashboard.show();
    }

    getStageOptions(notificationType) {
        const stageMap = {
            'service_estimate': ['created', 'approved'],
            'service_progress': ['started', 'progress_update', 'on_hold', 'completed'],
            'payment': ['reminder', 'received'],
            'appointment': ['scheduled', 'reminder']
        };

        return stageMap[notificationType] || [];
    }

    sendNotificationFromDialog(values) {
        let customData = {};

        if (values.custom_data) {
            try {
                customData = JSON.parse(values.custom_data);
            } catch (e) {
                frappe.msgprint(__('Invalid JSON in custom data'));
                return;
            }
        }

        const method = values.service_order ?
            'universal_workshop.sales_service.customer_notifications.send_service_notification' :
            'universal_workshop.sales_service.customer_notifications.send_customer_notification';

        const args = {
            notification_type: values.notification_type,
            stage: values.stage,
            custom_data: JSON.stringify(customData)
        };

        if (values.service_order) {
            args.service_order = values.service_order;
        } else if (values.customer) {
            args.customer = values.customer;
        }

        frappe.call({
            method: method,
            args: args,
            callback: (r) => {
                if (r.message && r.message.status === 'success') {
                    frappe.msgprint({
                        title: __('Success'),
                        message: r.message.message,
                        indicator: 'green'
                    });
                } else {
                    frappe.msgprint({
                        title: __('Error'),
                        message: r.message ? r.message.message : __('Failed to send notification'),
                        indicator: 'red'
                    });
                }
            }
        });
    }

    loadNotificationHistory() {
        // Load recent notifications for current user
        frappe.call({
            method: 'universal_workshop.sales_service.customer_notifications.get_customer_notification_history',
            args: {
                customer: frappe.session.user,
                limit: 20
            },
            callback: (r) => {
                if (r.message && r.message.status === 'success') {
                    this.notificationHistory = r.message.history;
                    this.updateNotificationBadge();
                }
            }
        });
    }

    updateNotificationBadge() {
        const unreadCount = this.notificationHistory.filter(n => !n.read).length;

        if (unreadCount > 0) {
            $('.notification-badge').text(unreadCount).show();
        } else {
            $('.notification-badge').hide();
        }
    }

    showNotificationHistory() {
        const isArabic = this.currentLanguage === 'ar';

        const historyDialog = new frappe.ui.Dialog({
            title: isArabic ? 'سجل الإشعارات' : 'Notification History',
            size: 'large',
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'notification_list'
                }
            ]
        });

        // Generate notification list HTML
        const listHTML = this.generateNotificationListHTML();
        historyDialog.fields_dict.notification_list.$wrapper.html(listHTML);

        historyDialog.show();
    }

    generateNotificationListHTML() {
        const isArabic = this.currentLanguage === 'ar';

        if (this.notificationHistory.length === 0) {
            return `
                <div class="notification-empty ${isArabic ? 'rtl-layout' : ''}">
                    <i class="fa fa-bell-slash fa-3x"></i>
                    <p>${isArabic ? 'لا توجد إشعارات' : 'No notifications'}</p>
                </div>
            `;
        }

        let html = `<div class="notification-history ${isArabic ? 'rtl-layout' : ''}">`;

        this.notificationHistory.forEach(notification => {
            const isRead = notification.read;
            const readClass = isRead ? 'read' : 'unread';

            html += `
                <div class="notification-item ${readClass}">
                    <div class="notification-item-header">
                        <h5>${notification.subject}</h5>
                        <span class="timestamp">
                            ${this.formatDateTime(notification.creation)}
                        </span>
                    </div>
                    <div class="notification-item-meta">
                        <span class="type-badge">${notification.type}</span>
                        ${!isRead ? `<span class="unread-badge">${isArabic ? 'جديد' : 'New'}</span>` : ''}
                    </div>
                </div>
            `;
        });

        html += '</div>';
        return html;
    }

    playNotificationSound() {
        // Play subtle notification sound
        try {
            const audio = new Audio('/assets/universal_workshop/sounds/notification.mp3');
            audio.volume = 0.3;
            audio.play().catch(() => {
                // Ignore audio play errors (browser restrictions)
            });
        } catch (e) {
            // Audio not available
        }
    }

    formatDateTime(datetime) {
        if (!datetime) return '';

        const date = new Date(datetime);
        const isArabic = this.currentLanguage === 'ar';

        const options = {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        };

        return date.toLocaleDateString(isArabic ? 'ar-SA' : 'en-US', options);
    }

    setupRTLLayout() {
        // Add RTL-specific styles
        $('body').addClass('notification-rtl');

        // Adjust notification positioning for RTL
        const style = $(`
            <style>
                .notification-popup.rtl-layout {
                    left: 20px !important;
                    right: auto !important;
                }
                .notification-rtl .notification-popup {
                    text-align: right;
                }
                .notification-rtl .notification-actions {
                    flex-direction: row-reverse;
                }
            </style>
        `);

        $('head').append(style);
    }

    bindFormEvents() {
        // Auto-send notifications on form events
        $(document).on('doc_save', (e, doctype, docname) => {
            if (doctype === 'Sales Order') {
                this.handleSalesOrderSave(docname);
            }
        });

        $(document).on('doc_submit', (e, doctype, docname) => {
            if (doctype === 'Sales Order') {
                this.handleSalesOrderSubmit(docname);
            }
        });
    }

    handleSalesOrderSave(salesOrderName) {
        // Check if this is a service order
        frappe.db.get_value('Sales Order', salesOrderName, 'service_estimate_reference')
            .then(r => {
                if (r.message && r.message.service_estimate_reference) {
                    // Send estimate created notification
                    this.sendAutoNotification(salesOrderName, 'service_estimate', 'created');
                }
            });
    }

    handleSalesOrderSubmit(salesOrderName) {
        // Send estimate approved notification
        this.sendAutoNotification(salesOrderName, 'service_estimate', 'approved');
    }

    sendAutoNotification(serviceOrder, type, stage) {
        frappe.call({
            method: 'universal_workshop.sales_service.customer_notifications.send_service_notification',
            args: {
                service_order: serviceOrder,
                notification_type: type,
                stage: stage
            },
            callback: (r) => {
                if (r.message && r.message.status === 'success') {
                    console.log('Auto notification sent:', r.message);
                }
            }
        });
    }

    viewNotificationDetails(notification) {
        if (notification.service_order) {
            frappe.set_route('Form', 'Sales Order', notification.service_order);
        }
    }

    addToNotificationHistory(data) {
        this.notificationHistory.unshift({
            subject: `${data.notification_type} - ${data.stage}`,
            creation: data.timestamp,
            read: false,
            type: data.notification_type
        });

        // Keep only last 50 notifications
        if (this.notificationHistory.length > 50) {
            this.notificationHistory = this.notificationHistory.slice(0, 50);
        }

        this.updateNotificationBadge();
    }
}

// Initialize Customer Notification UI
frappe.ready(() => {
    if (!window.customerNotificationUI) {
        window.customerNotificationUI = new CustomerNotificationUI();
    }
});

// Add notification management to workspace
frappe.ui.toolbar.add_button = function (opts) {
    const originalFn = frappe.ui.toolbar.add_button;

    // Add notification button to toolbar
    if (frappe.user.has_role(['Workshop Manager', 'System Manager'])) {
        originalFn.call(this, {
            icon: 'fa fa-bell',
            label: __('Notifications'),
            action: () => {
                window.customerNotificationUI.setupNotificationDashboard();
            }
        });
    }
};

// Export for use in other modules
window.CustomerNotificationUI = CustomerNotificationUI; 