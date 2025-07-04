/**
 * Quick Action Toolbar for Universal Workshop ERP
 * Floating action toolbar with modal dialogs for common workshop operations
 * Supports Arabic localization and barcode scanning integration
 */

class QuickActionToolbar {
    constructor() {
        this.language = frappe.boot.lang || 'en';
        this.is_rtl = this.language === 'ar';
        this.toolbar_visible = false;
        this.toolbar_container = null;
        this.scanner_active = false;

        this.actions = this.get_available_actions();
        this.init();
    }

    init() {
        this.create_toolbar();
        this.setup_event_listeners();
        this.setup_keyboard_shortcuts();
        this.check_permissions();
    }

    get_available_actions() {
        return [
            {
                id: 'create_service_order',
                label_en: 'New Service Order',
                label_ar: 'أمر خدمة جديد',
                icon: 'fa-wrench',
                color: '#007bff',
                permission: 'Service Order',
                shortcut: 'Ctrl+Shift+S'
            },
            {
                id: 'register_customer',
                label_en: 'Register Customer',
                label_ar: 'تسجيل عميل',
                icon: 'fa-user-plus',
                color: '#28a745',
                permission: 'Customer',
                shortcut: 'Ctrl+Shift+C'
            },
            {
                id: 'add_inventory',
                label_en: 'Add Inventory',
                label_ar: 'إضافة مخزون',
                icon: 'fa-plus-square',
                color: '#fd7e14',
                permission: 'Stock Entry',
                shortcut: 'Ctrl+Shift+I'
            },
            {
                id: 'process_payment',
                label_en: 'Process Payment',
                label_ar: 'معالجة دفع',
                icon: 'fa-credit-card',
                color: '#20c997',
                permission: 'Payment Entry',
                shortcut: 'Ctrl+Shift+P'
            },
            {
                id: 'generate_invoice',
                label_en: 'Generate Invoice',
                label_ar: 'إنشاء فاتورة',
                icon: 'fa-file-invoice',
                color: '#6610f2',
                permission: 'Sales Invoice',
                shortcut: 'Ctrl+Shift+V'
            },
            {
                id: 'schedule_appointment',
                label_en: 'Schedule Appointment',
                label_ar: 'حجز موعد',
                icon: 'fa-calendar-plus',
                color: '#e83e8c',
                permission: 'Event',
                shortcut: 'Ctrl+Shift+A'
            },
            {
                id: 'scan_barcode',
                label_en: 'Scan Barcode',
                label_ar: 'مسح الرمز الشريطي',
                icon: 'fa-qrcode',
                color: '#6c757d',
                permission: 'Item',
                shortcut: 'Ctrl+Shift+B'
            }
        ];
    }

    create_toolbar() {
        const toolbar_html = `
            <div class="quick-action-toolbar ${this.is_rtl ? 'rtl-layout' : ''}" dir="${this.is_rtl ? 'rtl' : 'ltr'}">
                <div class="toolbar-toggle" title="${this.is_rtl ? 'إجراءات سريعة' : 'Quick Actions'}">
                    <i class="fa fa-plus"></i>
                </div>
                <div class="toolbar-actions">
                    ${this.actions.map(action => this.render_action_button(action)).join('')}
                </div>
                <div class="toolbar-backdrop"></div>
            </div>
        `;

        $('body').append(toolbar_html);
        this.toolbar_container = $('.quick-action-toolbar');
    }

    render_action_button(action) {
        const label = this.is_rtl ? action.label_ar : action.label_en;
        return `
            <div class="action-button" 
                 data-action="${action.id}" 
                 data-permission="${action.permission}"
                 style="background-color: ${action.color}"
                 title="${label} (${action.shortcut})">
                <i class="fa ${action.icon}"></i>
                <span class="action-label">${label}</span>
            </div>
        `;
    }

    setup_event_listeners() {
        // Toggle toolbar
        $(document).on('click', '.toolbar-toggle', () => {
            this.toggle_toolbar();
        });

        // Action button clicks
        $(document).on('click', '.action-button', (e) => {
            const action_id = $(e.currentTarget).data('action');
            this.execute_action(action_id);
        });

        // Close toolbar on backdrop click
        $(document).on('click', '.toolbar-backdrop', () => {
            this.hide_toolbar();
        });

        // Close toolbar on ESC key
        $(document).on('keydown', (e) => {
            if (e.key === 'Escape' && this.toolbar_visible) {
                this.hide_toolbar();
            }
        });

        // Auto-hide on scroll
        let scroll_timeout;
        $(window).on('scroll', () => {
            if (this.toolbar_visible) {
                clearTimeout(scroll_timeout);
                scroll_timeout = setTimeout(() => {
                    this.hide_toolbar();
                }, 2000);
            }
        });
    }

    setup_keyboard_shortcuts() {
        this.actions.forEach(action => {
            $(document).on('keydown', (e) => {
                if (this.match_shortcut(e, action.shortcut)) {
                    e.preventDefault();
                    this.execute_action(action.id);
                }
            });
        });
    }

    match_shortcut(event, shortcut) {
        const parts = shortcut.split('+');
        const key = parts.pop().toLowerCase();
        const modifiers = parts.map(m => m.toLowerCase());

        if (event.key.toLowerCase() !== key) return false;

        const required_ctrl = modifiers.includes('ctrl');
        const required_shift = modifiers.includes('shift');
        const required_alt = modifiers.includes('alt');

        return (
            event.ctrlKey === required_ctrl &&
            event.shiftKey === required_shift &&
            event.altKey === required_alt
        );
    }

    toggle_toolbar() {
        if (this.toolbar_visible) {
            this.hide_toolbar();
        } else {
            this.show_toolbar();
        }
    }

    show_toolbar() {
        this.toolbar_container.addClass('visible');
        this.toolbar_visible = true;

        // Animate action buttons
        const buttons = $('.action-button');
        buttons.each((index, button) => {
            setTimeout(() => {
                $(button).addClass('visible');
            }, index * 50);
        });
    }

    hide_toolbar() {
        this.toolbar_container.removeClass('visible');
        $('.action-button').removeClass('visible');
        this.toolbar_visible = false;
    }

    check_permissions() {
        this.actions.forEach(action => {
            const has_permission = this.check_permission(action.permission);
            const button = $(`.action-button[data-action="${action.id}"]`);

            if (!has_permission) {
                button.addClass('disabled').attr('title',
                    this.is_rtl ? 'ليس لديك صلاحية لهذا الإجراء' : 'You do not have permission for this action'
                );
            }
        });
    }

    check_permission(doctype) {
        return frappe.model.can_create(doctype);
    }

    execute_action(action_id) {
        if (!this.toolbar_visible) {
            this.show_toolbar();
            return;
        }

        const action = this.actions.find(a => a.id === action_id);
        if (!action) return;

        const button = $(`.action-button[data-action="${action_id}"]`);
        if (button.hasClass('disabled')) {
            frappe.show_alert({
                message: this.is_rtl ? 'ليس لديك صلاحية لهذا الإجراء' : 'You do not have permission for this action',
                indicator: 'red'
            });
            return;
        }

        this.hide_toolbar();

        switch (action_id) {
            case 'create_service_order':
                this.create_service_order_dialog();
                break;
            case 'register_customer':
                this.register_customer_dialog();
                break;
            case 'add_inventory':
                this.add_inventory_dialog();
                break;
            case 'process_payment':
                this.process_payment_dialog();
                break;
            case 'generate_invoice':
                this.generate_invoice_dialog();
                break;
            case 'schedule_appointment':
                this.schedule_appointment_dialog();
                break;
            case 'scan_barcode':
                this.activate_barcode_scanner();
                break;
        }
    }

    create_service_order_dialog() {
        const dialog = new frappe.ui.Dialog({
            title: this.is_rtl ? 'إنشاء أمر خدمة جديد' : 'Create New Service Order',
            size: 'large',
            fields: [
                {
                    fieldtype: 'Link',
                    fieldname: 'customer',
                    label: this.is_rtl ? 'العميل' : 'Customer',
                    options: 'Customer',
                    reqd: 1,
                    get_query: () => {
                        return {
                            filters: { disabled: 0 }
                        };
                    }
                },
                {
                    fieldtype: 'Link',
                    fieldname: 'vehicle',
                    label: this.is_rtl ? 'المركبة' : 'Vehicle',
                    options: 'Vehicle',
                    reqd: 1,
                    get_query: () => {
                        const customer = dialog.get_value('customer');
                        return {
                            filters: customer ? { customer: customer } : {}
                        };
                    }
                },
                {
                    fieldtype: 'Column Break'
                },
                {
                    fieldtype: 'Select',
                    fieldname: 'service_type',
                    label: this.is_rtl ? 'نوع الخدمة' : 'Service Type',
                    options: [
                        '',
                        { value: 'Maintenance', label: this.is_rtl ? 'صيانة' : 'Maintenance' },
                        { value: 'Repair', label: this.is_rtl ? 'إصلاح' : 'Repair' },
                        { value: 'Inspection', label: this.is_rtl ? 'فحص' : 'Inspection' },
                        { value: 'Oil Change', label: this.is_rtl ? 'تغيير زيت' : 'Oil Change' }
                    ].filter(Boolean).map(opt => typeof opt === 'string' ? opt : `${opt.value}\n${opt.label}`).join('\n'),
                    reqd: 1
                },
                {
                    fieldtype: 'Date',
                    fieldname: 'scheduled_date',
                    label: this.is_rtl ? 'تاريخ الموعد' : 'Scheduled Date',
                    default: frappe.datetime.add_days(frappe.datetime.nowdate(), 1),
                    reqd: 1
                },
                {
                    fieldtype: 'Section Break'
                },
                {
                    fieldtype: 'Small Text',
                    fieldname: 'description',
                    label: this.is_rtl ? 'وصف الخدمة' : 'Service Description'
                },
                {
                    fieldtype: 'Select',
                    fieldname: 'priority',
                    label: this.is_rtl ? 'الأولوية' : 'Priority',
                    options: [
                        { value: 'Low', label: this.is_rtl ? 'منخفضة' : 'Low' },
                        { value: 'Medium', label: this.is_rtl ? 'متوسطة' : 'Medium' },
                        { value: 'High', label: this.is_rtl ? 'عالية' : 'High' },
                        { value: 'Urgent', label: this.is_rtl ? 'عاجل' : 'Urgent' }
                    ].map(opt => `${opt.value}\n${opt.label}`).join('\n'),
                    default: 'Medium'
                }
            ],
            primary_action_label: this.is_rtl ? 'إنشاء أمر الخدمة' : 'Create Service Order',
            primary_action: (values) => {
                this.create_service_order(values);
                dialog.hide();
            }
        });

        // Setup customer change handler
        dialog.fields_dict.customer.df.onchange = () => {
            const customer = dialog.get_value('customer');
            if (customer) {
                dialog.set_value('vehicle', '');
                dialog.fields_dict.vehicle.get_query = () => ({
                    filters: { customer: customer }
                });
            }
        };

        dialog.show();
    }

    register_customer_dialog() {
        const dialog = new frappe.ui.Dialog({
            title: this.is_rtl ? 'تسجيل عميل جديد' : 'Register New Customer',
            size: 'large',
            fields: [
                {
                    fieldtype: 'Data',
                    fieldname: 'customer_name',
                    label: this.is_rtl ? 'اسم العميل (إنجليزي)' : 'Customer Name (English)',
                    reqd: 1
                },
                {
                    fieldtype: 'Data',
                    fieldname: 'customer_name_ar',
                    label: this.is_rtl ? 'اسم العميل (عربي)' : 'Customer Name (Arabic)'
                },
                {
                    fieldtype: 'Column Break'
                },
                {
                    fieldtype: 'Data',
                    fieldname: 'phone',
                    label: this.is_rtl ? 'رقم الهاتف' : 'Phone Number',
                    reqd: 1
                },
                {
                    fieldtype: 'Data',
                    fieldname: 'email',
                    label: this.is_rtl ? 'البريد الإلكتروني' : 'Email Address'
                },
                {
                    fieldtype: 'Section Break'
                },
                {
                    fieldtype: 'Small Text',
                    fieldname: 'address',
                    label: this.is_rtl ? 'العنوان (إنجليزي)' : 'Address (English)'
                },
                {
                    fieldtype: 'Small Text',
                    fieldname: 'address_ar',
                    label: this.is_rtl ? 'العنوان (عربي)' : 'Address (Arabic)'
                },
                {
                    fieldtype: 'Column Break'
                },
                {
                    fieldtype: 'Select',
                    fieldname: 'customer_group',
                    label: this.is_rtl ? 'مجموعة العملاء' : 'Customer Group',
                    options: 'Individual\nCorporate',
                    default: 'Individual'
                },
                {
                    fieldtype: 'Link',
                    fieldname: 'territory',
                    label: this.is_rtl ? 'المنطقة' : 'Territory',
                    options: 'Territory',
                    default: 'All Territories'
                }
            ],
            primary_action_label: this.is_rtl ? 'تسجيل العميل' : 'Register Customer',
            primary_action: (values) => {
                this.register_customer(values);
                dialog.hide();
            }
        });

        dialog.show();
    }

    add_inventory_dialog() {
        const dialog = new frappe.ui.Dialog({
            title: this.is_rtl ? 'إضافة مخزون' : 'Add Inventory',
            size: 'large',
            fields: [
                {
                    fieldtype: 'Link',
                    fieldname: 'item_code',
                    label: this.is_rtl ? 'رمز الصنف' : 'Item Code',
                    options: 'Item',
                    reqd: 1,
                    get_query: () => ({
                        filters: { is_stock_item: 1, disabled: 0 }
                    })
                },
                {
                    fieldtype: 'Link',
                    fieldname: 'warehouse',
                    label: this.is_rtl ? 'المستودع' : 'Warehouse',
                    options: 'Warehouse',
                    reqd: 1
                },
                {
                    fieldtype: 'Column Break'
                },
                {
                    fieldtype: 'Float',
                    fieldname: 'qty',
                    label: this.is_rtl ? 'الكمية' : 'Quantity',
                    reqd: 1,
                    default: 1
                },
                {
                    fieldtype: 'Currency',
                    fieldname: 'basic_rate',
                    label: this.is_rtl ? 'السعر' : 'Rate',
                    reqd: 1
                },
                {
                    fieldtype: 'Section Break'
                },
                {
                    fieldtype: 'Small Text',
                    fieldname: 'remarks',
                    label: this.is_rtl ? 'ملاحظات' : 'Remarks'
                }
            ],
            primary_action_label: this.is_rtl ? 'إضافة للمخزون' : 'Add to Inventory',
            primary_action: (values) => {
                this.add_inventory(values);
                dialog.hide();
            }
        });

        dialog.show();
    }

    process_payment_dialog() {
        const dialog = new frappe.ui.Dialog({
            title: this.is_rtl ? 'معالجة دفع' : 'Process Payment',
            size: 'large',
            fields: [
                {
                    fieldtype: 'Link',
                    fieldname: 'party',
                    label: this.is_rtl ? 'العميل/المورد' : 'Customer/Supplier',
                    options: 'Customer',
                    reqd: 1
                },
                {
                    fieldtype: 'Currency',
                    fieldname: 'paid_amount',
                    label: this.is_rtl ? 'المبلغ المدفوع' : 'Paid Amount',
                    reqd: 1
                },
                {
                    fieldtype: 'Column Break'
                },
                {
                    fieldtype: 'Select',
                    fieldname: 'mode_of_payment',
                    label: this.is_rtl ? 'طريقة الدفع' : 'Mode of Payment',
                    options: [
                        { value: 'Cash', label: this.is_rtl ? 'نقدي' : 'Cash' },
                        { value: 'Bank Transfer', label: this.is_rtl ? 'تحويل بنكي' : 'Bank Transfer' },
                        { value: 'Credit Card', label: this.is_rtl ? 'بطاقة ائتمان' : 'Credit Card' },
                        { value: 'Debit Card', label: this.is_rtl ? 'بطاقة مدين' : 'Debit Card' }
                    ].map(opt => `${opt.value}\n${opt.label}`).join('\n'),
                    default: 'Cash',
                    reqd: 1
                },
                {
                    fieldtype: 'Date',
                    fieldname: 'posting_date',
                    label: this.is_rtl ? 'تاريخ الدفع' : 'Payment Date',
                    default: frappe.datetime.nowdate(),
                    reqd: 1
                },
                {
                    fieldtype: 'Section Break'
                },
                {
                    fieldtype: 'Small Text',
                    fieldname: 'remarks',
                    label: this.is_rtl ? 'ملاحظات' : 'Remarks'
                }
            ],
            primary_action_label: this.is_rtl ? 'معالجة الدفع' : 'Process Payment',
            primary_action: (values) => {
                this.process_payment(values);
                dialog.hide();
            }
        });

        dialog.show();
    }

    generate_invoice_dialog() {
        const dialog = new frappe.ui.Dialog({
            title: this.is_rtl ? 'إنشاء فاتورة' : 'Generate Invoice',
            size: 'large',
            fields: [
                {
                    fieldtype: 'Link',
                    fieldname: 'customer',
                    label: this.is_rtl ? 'العميل' : 'Customer',
                    options: 'Customer',
                    reqd: 1
                },
                {
                    fieldtype: 'Link',
                    fieldname: 'service_order',
                    label: this.is_rtl ? 'أمر الخدمة' : 'Service Order',
                    options: 'Service Order',
                    get_query: () => {
                        const customer = dialog.get_value('customer');
                        return {
                            filters: {
                                customer: customer || '',
                                status: ['!=', 'Cancelled']
                            }
                        };
                    }
                },
                {
                    fieldtype: 'Column Break'
                },
                {
                    fieldtype: 'Date',
                    fieldname: 'posting_date',
                    label: this.is_rtl ? 'تاريخ الفاتورة' : 'Invoice Date',
                    default: frappe.datetime.nowdate(),
                    reqd: 1
                },
                {
                    fieldtype: 'Date',
                    fieldname: 'due_date',
                    label: this.is_rtl ? 'تاريخ الاستحقاق' : 'Due Date',
                    default: frappe.datetime.add_days(frappe.datetime.nowdate(), 30)
                },
                {
                    fieldtype: 'Section Break'
                },
                {
                    fieldtype: 'Check',
                    fieldname: 'auto_generate_items',
                    label: this.is_rtl ? 'إنشاء العناصر تلقائياً من أمر الخدمة' : 'Auto-generate items from Service Order',
                    default: 1
                }
            ],
            primary_action_label: this.is_rtl ? 'إنشاء الفاتورة' : 'Generate Invoice',
            primary_action: (values) => {
                this.generate_invoice(values);
                dialog.hide();
            }
        });

        dialog.show();
    }

    schedule_appointment_dialog() {
        const dialog = new frappe.ui.Dialog({
            title: this.is_rtl ? 'حجز موعد' : 'Schedule Appointment',
            size: 'large',
            fields: [
                {
                    fieldtype: 'Link',
                    fieldname: 'customer',
                    label: this.is_rtl ? 'العميل' : 'Customer',
                    options: 'Customer',
                    reqd: 1
                },
                {
                    fieldtype: 'Data',
                    fieldname: 'subject',
                    label: this.is_rtl ? 'الموضوع' : 'Subject',
                    reqd: 1
                },
                {
                    fieldtype: 'Column Break'
                },
                {
                    fieldtype: 'Datetime',
                    fieldname: 'starts_on',
                    label: this.is_rtl ? 'يبدأ في' : 'Starts On',
                    reqd: 1,
                    default: frappe.datetime.add_to_date(frappe.datetime.now_datetime(), { hours: 1 })
                },
                {
                    fieldtype: 'Datetime',
                    fieldname: 'ends_on',
                    label: this.is_rtl ? 'ينتهي في' : 'Ends On',
                    reqd: 1,
                    default: frappe.datetime.add_to_date(frappe.datetime.now_datetime(), { hours: 2 })
                },
                {
                    fieldtype: 'Section Break'
                },
                {
                    fieldtype: 'Small Text',
                    fieldname: 'description',
                    label: this.is_rtl ? 'الوصف' : 'Description'
                }
            ],
            primary_action_label: this.is_rtl ? 'حجز الموعد' : 'Schedule Appointment',
            primary_action: (values) => {
                this.schedule_appointment(values);
                dialog.hide();
            }
        });

        dialog.show();
    }

    activate_barcode_scanner() {
        if (this.scanner_active) return;

        frappe.show_alert({
            message: this.is_rtl ? 'تفعيل ماسح الرمز الشريطي...' : 'Activating barcode scanner...',
            indicator: 'blue'
        });

        // Check if barcode scanner utility exists
        if (typeof frappe.barcode_scanner !== 'undefined') {
            frappe.barcode_scanner.scan((code) => {
                this.handle_barcode_scan(code);
            });
        } else {
            // Fallback to manual input dialog
            this.manual_barcode_input_dialog();
        }
    }

    manual_barcode_input_dialog() {
        const dialog = new frappe.ui.Dialog({
            title: this.is_rtl ? 'إدخال الرمز الشريطي' : 'Enter Barcode',
            fields: [
                {
                    fieldtype: 'Data',
                    fieldname: 'barcode',
                    label: this.is_rtl ? 'الرمز الشريطي' : 'Barcode',
                    reqd: 1
                }
            ],
            primary_action_label: this.is_rtl ? 'بحث' : 'Search',
            primary_action: (values) => {
                this.handle_barcode_scan(values.barcode);
                dialog.hide();
            }
        });

        dialog.show();
        dialog.fields_dict.barcode.input.focus();
    }

    handle_barcode_scan(code) {
        if (!code) return;

        frappe.call({
            method: 'universal_workshop.parts_inventory.api.get_item_by_barcode',
            args: { barcode: code },
            callback: (response) => {
                if (response.message) {
                    this.show_barcode_result(response.message);
                } else {
                    frappe.show_alert({
                        message: this.is_rtl ? 'لم يتم العثور على صنف بهذا الرمز' : 'No item found with this barcode',
                        indicator: 'red'
                    });
                }
            }
        });
    }

    show_barcode_result(item) {
        const message = this.is_rtl ?
            `تم العثور على: ${item.item_name}` :
            `Found: ${item.item_name}`;

        frappe.show_alert({
            message: message,
            indicator: 'green'
        });

        // Open item form or perform action based on context
        frappe.set_route('Form', 'Item', item.item_code);
    }

    // Action execution methods
    create_service_order(values) {
        frappe.new_doc('Service Order', values);
    }

    register_customer(values) {
        frappe.new_doc('Customer', values);
    }

    add_inventory(values) {
        const stock_entry = {
            stock_entry_type: 'Material Receipt',
            items: [{
                item_code: values.item_code,
                qty: values.qty,
                basic_rate: values.basic_rate,
                t_warehouse: values.warehouse
            }],
            remarks: values.remarks
        };
        frappe.new_doc('Stock Entry', stock_entry);
    }

    process_payment(values) {
        const payment_entry = {
            payment_type: 'Receive',
            party_type: 'Customer',
            party: values.party,
            paid_amount: values.paid_amount,
            mode_of_payment: values.mode_of_payment,
            posting_date: values.posting_date,
            remarks: values.remarks
        };
        frappe.new_doc('Payment Entry', payment_entry);
    }

    generate_invoice(values) {
        const invoice_data = {
            customer: values.customer,
            posting_date: values.posting_date,
            due_date: values.due_date
        };

        if (values.service_order && values.auto_generate_items) {
            // Get items from service order
            frappe.call({
                method: 'universal_workshop.api.get_service_order_items',
                args: { service_order: values.service_order },
                callback: (response) => {
                    if (response.message) {
                        invoice_data.items = response.message;
                    }
                    frappe.new_doc('Sales Invoice', invoice_data);
                }
            });
        } else {
            frappe.new_doc('Sales Invoice', invoice_data);
        }
    }

    schedule_appointment(values) {
        const event_data = {
            subject: values.subject,
            starts_on: values.starts_on,
            ends_on: values.ends_on,
            description: values.description,
            event_participants: [{
                reference_doctype: 'Customer',
                reference_docname: values.customer
            }]
        };
        frappe.new_doc('Event', event_data);
    }

    destroy() {
        if (this.toolbar_container) {
            this.toolbar_container.remove();
        }
        $(document).off('.quick-action-toolbar');
    }
}

// Global initialization
window.QuickActionToolbar = QuickActionToolbar;

// Auto-initialize on document ready
$(document).ready(() => {
    // Only initialize on main dashboard/desk pages
    if (frappe.get_route()[0] === 'dashboard' || !frappe.get_route()[0]) {
        setTimeout(() => {
            if (!window.quick_action_toolbar) {
                window.quick_action_toolbar = new QuickActionToolbar();
            }
        }, 1000);
    }
});

// Initialize when navigating to dashboard
frappe.router.on('change', () => {
    const route = frappe.get_route();
    if ((route[0] === 'dashboard' || !route[0]) && !window.quick_action_toolbar) {
        setTimeout(() => {
            window.quick_action_toolbar = new QuickActionToolbar();
        }, 500);
    }
}); 