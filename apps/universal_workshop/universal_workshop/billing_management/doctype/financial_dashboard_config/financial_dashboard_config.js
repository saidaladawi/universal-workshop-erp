frappe.ui.form.on('Financial Dashboard Config', {
    refresh: function (frm) {
        frm.trigger('setup_custom_buttons');
        frm.trigger('setup_arabic_fields');
    },

    setup_custom_buttons: function (frm) {
        frm.add_custom_button(__('Test Dashboard Access'), function () {
            frm.trigger('test_dashboard_access');
        });

        frm.add_custom_button(__('Preview Dashboard Data'), function () {
            frm.trigger('preview_dashboard_data');
        });
    },

    setup_arabic_fields: function (frm) {
        // Set RTL direction for Arabic fields
        ['dashboard_name_ar'].forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.attr('dir', 'rtl');
                frm.fields_dict[field].$input.css('text-align', 'right');
            }
        });
    },

    restrict_access: function (frm) {
        if (frm.doc.restrict_access) {
            frm.set_df_property('visible_to_roles', 'reqd', 1);
        } else {
            frm.set_df_property('visible_to_roles', 'reqd', 0);
        }
    },

    test_dashboard_access: function (frm) {
        frappe.call({
            method: 'universal_workshop.billing_management.doctype.financial_dashboard_config.financial_dashboard_config.test_dashboard_access',
            args: {
                docname: frm.doc.name
            },
            callback: function (r) {
                if (r.message) {
                    let message = __(`Access: ${r.message.access}<br>
                                    Reason: ${r.message.reason}<br>
                                    User Roles: ${r.message.user_roles.join(', ')}<br>
                                    Visible Roles: ${r.message.visible_roles.join(', ')}`);

                    frappe.msgprint({
                        title: __('Dashboard Access Test'),
                        message: message,
                        indicator: r.message.access === 'allowed' ? 'green' : 'red'
                    });
                }
            }
        });
    },

    preview_dashboard_data: function (frm) {
        frappe.call({
            method: 'universal_workshop.billing_management.doctype.financial_dashboard_config.financial_dashboard_config.get_dashboard_data',
            args: {
                docname: frm.doc.name,
                period: frm.doc.default_period
            },
            callback: function (r) {
                if (r.message && !r.message.error) {
                    let message = __(`Period: ${r.message.period}<br>
                                    Currency: ${r.message.currency}<br>
                                    Widgets: ${Object.keys(r.message.widgets).length}<br>
                                    Charts: ${Object.keys(r.message.charts).length}`);

                    frappe.msgprint({
                        title: __('Dashboard Data Preview'),
                        message: message,
                        indicator: 'blue'
                    });
                } else {
                    frappe.msgprint({
                        title: __('Dashboard Data Preview'),
                        message: r.message.error || __('Failed to load dashboard data'),
                        indicator: 'red'
                    });
                }
            }
        });
    },

    dashboard_type: function (frm) {
        // Update widget selection based on dashboard type
        let widgets = [];

        switch (frm.doc.dashboard_type) {
            case 'Executive':
                widgets = ['revenue_widget', 'profit_widget', 'cash_flow_widget'];
                break;
            case 'Managerial':
                widgets = ['revenue_widget', 'expense_widget', 'profit_widget', 'vat_widget'];
                break;
            case 'Operational':
                widgets = ['receivables_widget', 'payables_widget', 'inventory_widget'];
                break;
            case 'Analytical':
                widgets = ['revenue_widget', 'expense_widget', 'profit_widget', 'cash_flow_widget', 'vat_widget', 'receivables_widget', 'payables_widget', 'inventory_widget'];
                break;
        }

        // Reset all widgets
        ['revenue_widget', 'expense_widget', 'profit_widget', 'cash_flow_widget', 'vat_widget', 'receivables_widget', 'payables_widget', 'inventory_widget'].forEach(widget => {
            frm.set_value(widget, widgets.includes(widget));
        });
    }
}); 