// Copyright (c) 2025, Universal Workshop ERP and contributors
// For license information, please see license.txt

frappe.ui.form.on('Workshop Role', {
    refresh: function (frm) {
        frm.trigger('setup_arabic_fields');
        frm.trigger('setup_custom_buttons');
        frm.trigger('setup_rtl_layout');
    },

    setup_arabic_fields: function (frm) {
        // Set RTL direction for Arabic fields
        ['role_name_ar', 'role_description_ar'].forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.attr('dir', 'rtl');
                frm.fields_dict[field].$input.css('text-align', 'right');
            }
        });
    },

    setup_rtl_layout: function (frm) {
        // RTL layout for Arabic locale
        if (frappe.boot.lang === 'ar') {
            frm.page.main.addClass('rtl-layout');
        }
    },

    setup_custom_buttons: function (frm) {
        if (!frm.doc.__islocal) {
            // Add button to create ERPNext role
            frm.add_custom_button(__('Create ERPNext Role'), function () {
                frm.call('create_erpnext_role').then(r => {
                    if (!r.exc) {
                        frappe.msgprint(__('ERPNext role created successfully'));
                        frm.refresh();
                    }
                });
            });

            // Add button to view role hierarchy
            frm.add_custom_button(__('View Role Hierarchy'), function () {
                frappe.call({
                    method: 'universal_workshop.user_management.doctype.workshop_role.workshop_role.get_role_hierarchy',
                    callback: function (r) {
                        if (r.message) {
                            show_role_hierarchy_dialog(r.message);
                        }
                    }
                });
            });
        }

        // Add button to create default roles
        frm.add_custom_button(__('Create Default Roles'), function () {
            frappe.call({
                method: 'universal_workshop.user_management.doctype.workshop_role.workshop_role.create_default_workshop_roles',
                callback: function (r) {
                    if (r.message && r.message.length > 0) {
                        frappe.msgprint(__('Created roles: {0}', [r.message.join(', ')]));
                        frm.refresh();
                    }
                }
            });
        }, __('Actions'));
    },

    role_name: function (frm) {
        // Auto-suggest Arabic name when English name is entered
        if (frm.doc.role_name && !frm.doc.role_name_ar) {
            frm.trigger('suggest_arabic_name');
        }
    },

    suggest_arabic_name: function (frm) {
        // Provide common Arabic translations for role names
        const arabic_translations = {
            'Workshop Manager': 'مدير الورشة',
            'Service Advisor': 'مستشار الخدمة',
            'Workshop Technician': 'فني الورشة',
            'Parts Manager': 'مدير قطع الغيار',
            'Workshop Receptionist': 'موظف استقبال الورشة',
            'Financial Staff': 'الموظف المالي'
        };

        if (arabic_translations[frm.doc.role_name]) {
            frm.set_value('role_name_ar', arabic_translations[frm.doc.role_name]);
        }
    },

    priority_level: function (frm) {
        // Validate priority level
        if (frm.doc.priority_level && (frm.doc.priority_level < 1 || frm.doc.priority_level > 10)) {
            frappe.msgprint(__('Priority level must be between 1 and 10'));
            frm.set_value('priority_level', 5);
        }
    }
});

// Workshop Role Permission child table events
frappe.ui.form.on('Workshop Role Permission', {
    doctype_name: function (frm, cdt, cdn) {
        // Auto-set common permissions when DocType is selected
        const row = locals[cdt][cdn];
        if (row.doctype_name && !row.permission_type) {
            // Set default permission type based on role type
            if (frm.doc.role_type === 'Management') {
                frappe.model.set_value(cdt, cdn, 'permission_type', 'Write');
                frappe.model.set_value(cdt, cdn, 'permission_level', 0);
            } else if (frm.doc.role_type === 'Technical') {
                frappe.model.set_value(cdt, cdn, 'permission_type', 'Read');
                frappe.model.set_value(cdt, cdn, 'permission_level', 0);
            }
        }
    }
});

function show_role_hierarchy_dialog(hierarchy) {
    const dialog = new frappe.ui.Dialog({
        title: __('Workshop Role Hierarchy'),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'hierarchy_html'
            }
        ]
    });

    let html = '<div class="role-hierarchy">';

    // Generate hierarchy HTML
    Object.keys(hierarchy).forEach(role_type => {
        html += `<div class="role-type-section">
            <h4>${__(role_type)}</h4>
            <div class="role-list">`;

        hierarchy[role_type].forEach(role => {
            const arabic_name = role.role_name_ar || role.role_name;
            html += `<div class="role-item" data-priority="${role.priority_level}">
                <div class="role-name">${role.role_name}</div>
                <div class="role-name-ar" dir="rtl">${arabic_name}</div>
                <div class="role-priority">Priority: ${role.priority_level}</div>
            </div>`;
        });

        html += '</div></div>';
    });

    html += '</div>';

    // Add CSS for hierarchy display
    html += `<style>
        .role-hierarchy { font-family: Arial, sans-serif; }
        .role-type-section { margin-bottom: 20px; }
        .role-type-section h4 { 
            background: #f5f5f5; 
            padding: 8px; 
            margin: 0 0 10px 0; 
            border-radius: 4px; 
        }
        .role-list { display: flex; flex-wrap: wrap; gap: 10px; }
        .role-item { 
            border: 1px solid #ddd; 
            padding: 10px; 
            border-radius: 4px; 
            min-width: 200px; 
            background: white;
        }
        .role-name { font-weight: bold; color: #333; }
        .role-name-ar { 
            font-size: 0.9em; 
            color: #666; 
            margin-top: 2px;
            text-align: right;
        }
        .role-priority { 
            font-size: 0.8em; 
            color: #888; 
            margin-top: 4px; 
        }
    </style>`;

    dialog.fields_dict.hierarchy_html.$wrapper.html(html);
    dialog.show();
} 