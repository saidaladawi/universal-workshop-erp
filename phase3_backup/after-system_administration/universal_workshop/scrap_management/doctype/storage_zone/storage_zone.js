// Copyright (c) 2024, Universal Workshop and contributors
// For license information, please see license.txt

frappe.ui.form.on('Storage Zone', {
    refresh: function(frm) {
        frm.trigger('setup_arabic_fields');
        frm.trigger('setup_custom_buttons');
        frm.trigger('update_utilization_display');
    },

    setup_arabic_fields: function(frm) {
        // Set RTL direction for Arabic fields
        const arabic_fields = [
            'zone_name_ar', 'location_ar', 'description_ar',
            'safety_requirements_ar', 'access_instructions_ar'
        ];
        
        arabic_fields.forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.attr('dir', 'rtl');
                frm.fields_dict[field].$input.css({
                    'text-align': 'right',
                    'font-family': 'Noto Sans Arabic, Tahoma, Arial Unicode MS'
                });
            }
        });
    },

    setup_custom_buttons: function(frm) {
        if (!frm.is_new()) {
            // Zone Management buttons
            frm.add_custom_button(__('Generate Barcode'), function() {
                frm.trigger('generate_barcode');
            }, __('Zone Actions'));

            frm.add_custom_button(__('Zone Report'), function() {
                frm.trigger('show_zone_report');
            }, __('Reports'));

            frm.add_custom_button(__('Print Labels'), function() {
                frm.trigger('print_zone_labels');
            }, __('Zone Actions'));

            frm.add_custom_button(__('Parts in Zone'), function() {
                frm.trigger('show_parts_in_zone');
            }, __('Reports'));

            // Utilization actions based on status
            if (frm.doc.utilization_percentage >= 95) {
                frm.add_custom_button(__('Manage Overflow'), function() {
                    frm.trigger('manage_overflow');
                }, __('Zone Actions'));
            }
        }
    },

    zone_name: function(frm) {
        // Auto-suggest Arabic name if English is provided
        if (frm.doc.zone_name && !frm.doc.zone_name_ar) {
            frm.trigger('suggest_arabic_name');
        }
    },

    zone_type: function(frm) {
        // Update zone code when type changes
        if (frm.doc.zone_type && !frm.doc.zone_code) {
            frm.trigger('generate_zone_code');
        }
        
        // Update allowed categories based on type
        frm.trigger('update_allowed_categories_for_type');
    },

    max_capacity: function(frm) {
        frm.trigger('calculate_utilization');
    },

    current_capacity: function(frm) {
        frm.trigger('calculate_utilization');
        frm.trigger('validate_capacity');
    },

    height_meters: function(frm) {
        frm.trigger('update_accessibility_flags');
    },

    calculate_utilization: function(frm) {
        if (frm.doc.max_capacity && frm.doc.current_capacity) {
            const utilization = (frm.doc.current_capacity / frm.doc.max_capacity) * 100;
            frm.set_value('utilization_percentage', utilization);
        } else {
            frm.set_value('utilization_percentage', 0);
        }
    },

    update_utilization_display: function(frm) {
        if (frm.doc.utilization_percentage) {
            const utilization = frm.doc.utilization_percentage;
            let status_color = 'green';
            let status_text = __('Low Usage');

            if (utilization >= 95) {
                status_color = 'red';
                status_text = __('Critical - Nearly Full');
            } else if (utilization >= 80) {
                status_color = 'orange';
                status_text = __('High Usage');
            } else if (utilization >= 60) {
                status_color = 'yellow';
                status_text = __('Medium Usage');
            }

            // Update utilization display
            frm.dashboard.add_indicator(
                `${status_text}: ${utilization.toFixed(1)}%`,
                status_color
            );
        }
    },

    validate_capacity: function(frm) {
        if (frm.doc.current_capacity && frm.doc.max_capacity) {
            if (frm.doc.current_capacity > frm.doc.max_capacity) {
                frappe.msgprint({
                    title: __('Capacity Warning'),
                    message: __('Current capacity cannot exceed maximum capacity'),
                    indicator: 'red'
                });
                frm.set_value('current_capacity', frm.doc.max_capacity);
            }
        }
    },

    update_accessibility_flags: function(frm) {
        if (frm.doc.height_meters) {
            if (frm.doc.height_meters > 3.0) {
                frm.set_value('requires_ladder', 1);
            }
            if (frm.doc.height_meters > 5.0) {
                frm.set_value('requires_crane', 1);
            }
        }
    },

    generate_zone_code: function(frm) {
        if (frm.doc.zone_type) {
            frappe.call({
                method: 'universal_workshop.scrap_management.doctype.storage_zone.storage_zone.generate_zone_code',
                args: {
                    zone_type: frm.doc.zone_type
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value('zone_code', r.message);
                    }
                }
            });
        }
    },

    suggest_arabic_name: function(frm) {
        // Simple translation suggestions for common zone names
        const translations = {
            'General Storage': 'مخزن عام',
            'Engine Parts': 'قطع المحركات', 
            'Body Parts': 'قطع الهيكل',
            'Electronics': 'إلكترونيات',
            'Hazmat Storage': 'مخزن المواد الخطرة',
            'Secure Storage': 'مخزن آمن',
            'Climate Controlled': 'مكيف الهواء',
            'Heavy Parts': 'القطع الثقيلة'
        };

        if (translations[frm.doc.zone_name]) {
            frm.set_value('zone_name_ar', translations[frm.doc.zone_name]);
        }
    },

    update_allowed_categories_for_type: function(frm) {
        // Suggest default categories based on zone type
        const type_categories = {
            'Hazmat': ['Fuel System', 'Battery', 'Fluids'],
            'Secure': ['Electronics', 'High Value Parts'],
            'Heavy': ['Engine', 'Transmission', 'Body'],
            'Climate': ['Electronics', 'Interior', 'Electrical']
        };

        if (type_categories[frm.doc.zone_type] && !frm.doc.allowed_categories.length) {
            // Only suggest if no categories are already set
            const categories = type_categories[frm.doc.zone_type];
            frm.clear_table('allowed_categories');
            
            categories.forEach(category => {
                const row = frm.add_child('allowed_categories');
                row.part_category = category;
                row.priority_level = 'Medium';
            });
            
            frm.refresh_field('allowed_categories');
        }
    },

    generate_barcode: function(frm) {
        if (!frm.doc.zone_code) {
            frappe.msgprint(__('Zone code is required to generate barcode'));
            return;
        }

        frappe.call({
            method: 'generate_barcode',
            doc: frm.doc,
            callback: function(r) {
                if (r.message) {
                    frm.set_value('barcode', r.message);
                    frappe.msgprint(__('Barcode generated successfully'));
                }
            }
        });
    },

    show_zone_report: function(frm) {
        frappe.call({
            method: 'get_zone_report',
            doc: frm.doc,
            callback: function(r) {
                if (r.message) {
                    frm.trigger('display_zone_report', r.message);
                }
            }
        });
    },

    display_zone_report: function(frm, report_data) {
        const dialog = new frappe.ui.Dialog({
            title: __('Zone Utilization Report'),
            size: 'large',
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'report_html'
                }
            ]
        });

        // Build report HTML
        let html = `
            <div class="zone-report">
                <h4>${__('Zone Information')}</h4>
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>${__('Zone Code')}:</strong> ${report_data.zone_info.zone_code}</p>
                        <p><strong>${__('Zone Name')}:</strong> ${report_data.zone_info.zone_name}</p>
                        <p><strong>${__('Zone Type')}:</strong> ${report_data.zone_info.zone_type}</p>
                    </div>
                    <div class="col-md-6">
                        <p><strong>${__('Utilization')}:</strong> ${report_data.zone_info.utilization.toFixed(1)}%</p>
                        <p><strong>${__('Status')}:</strong> ${report_data.zone_info.status}</p>
                        <p><strong>${__('Available Capacity')}:</strong> ${report_data.summary.available_capacity}</p>
                    </div>
                </div>
                
                <h4>${__('Summary')}</h4>
                <div class="row">
                    <div class="col-md-4">
                        <p><strong>${__('Total Parts')}:</strong> ${report_data.summary.total_parts}</p>
                    </div>
                    <div class="col-md-4">
                        <p><strong>${__('Total Weight')}:</strong> ${report_data.summary.total_weight_kg} kg</p>
                    </div>
                    <div class="col-md-4">
                        <p><strong>${__('Total Value')}:</strong> ${report_data.summary.total_value_omr.toFixed(3)} OMR</p>
                    </div>
                </div>

                <h4>${__('By Category')}</h4>
                <table class="table table-bordered">
                    <thead>
                        <tr>
                            <th>${__('Category')}</th>
                            <th>${__('Count')}</th>
                            <th>${__('Weight (kg)')}</th>
                            <th>${__('Value (OMR)')}</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        for (const [category, data] of Object.entries(report_data.by_category)) {
            html += `
                <tr>
                    <td>${category}</td>
                    <td>${data.count}</td>
                    <td>${data.total_weight.toFixed(2)}</td>
                    <td>${data.total_value.toFixed(3)}</td>
                </tr>
            `;
        }

        html += `
                    </tbody>
                </table>
            </div>
        `;

        dialog.fields_dict.report_html.$wrapper.html(html);
        dialog.show();
    },

    show_parts_in_zone: function(frm) {
        frappe.set_route('List', 'Part Storage Location', {
            'storage_zone': frm.doc.name,
            'status': 'Stored'
        });
    },

    print_zone_labels: function(frm) {
        frappe.call({
            method: 'generate_zone_labels',
            doc: frm.doc,
            callback: function(r) {
                if (r.message) {
                    // Open print dialog with label data
                    const print_window = window.open('', '_blank');
                    const label_data = r.message;
                    
                    print_window.document.write(`
                        <html>
                        <head>
                            <title>Zone Label - ${label_data.zone_code}</title>
                            <style>
                                body { font-family: Arial, sans-serif; }
                                .label { border: 2px solid #000; padding: 20px; width: 300px; margin: 20px; }
                                .barcode { font-family: 'Courier New', monospace; font-size: 24px; }
                                .arabic { direction: rtl; text-align: right; }
                            </style>
                        </head>
                        <body>
                            <div class="label">
                                <h2>${label_data.zone_code}</h2>
                                <p><strong>Zone:</strong> ${label_data.zone_name}</p>
                                <p class="arabic"><strong>المنطقة:</strong> ${label_data.zone_name_ar}</p>
                                <p><strong>Type:</strong> ${label_data.zone_type}</p>
                                <p><strong>Location:</strong> ${label_data.location}</p>
                                <p><strong>Capacity:</strong> ${label_data.max_capacity}</p>
                                <div class="barcode">${label_data.barcode}</div>
                            </div>
                        </body>
                        </html>
                    `);
                    print_window.document.close();
                    print_window.print();
                }
            }
        });
    },

    manage_overflow: function(frm) {
        // Show dialog to help manage zone overflow
        const dialog = new frappe.ui.Dialog({
            title: __('Manage Zone Overflow'),
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'overflow_info',
                    options: `
                        <p>${__('This zone is at critical capacity')} (${frm.doc.utilization_percentage.toFixed(1)}%).</p>
                        <p>${__('Consider the following actions')}:</p>
                        <ul>
                            <li>${__('Move some parts to other zones')}</li>
                            <li>${__('Prioritize selling high-demand parts')}</li>
                            <li>${__('Review and dispose of low-value parts')}</li>
                            <li>${__('Expand zone capacity if possible')}</li>
                        </ul>
                    `
                },
                {
                    fieldtype: 'Button',
                    fieldname: 'find_alternative_zones',
                    label: __('Find Alternative Zones')
                },
                {
                    fieldtype: 'Button', 
                    fieldname: 'prioritize_sales',
                    label: __('Prioritize Sales')
                }
            ],
            primary_action_label: __('Close'),
            primary_action: function() {
                dialog.hide();
            }
        });

        dialog.fields_dict.find_alternative_zones.$input.click(function() {
            frappe.call({
                method: 'universal_workshop.scrap_management.doctype.storage_zone.storage_zone.get_available_zones',
                callback: function(r) {
                    if (r.message && r.message.length > 0) {
                        let zone_list = r.message.map(z => 
                            `${z.zone_code} - ${z.zone_name} (${z.utilization_percentage || 0}% full)`
                        ).join('<br>');
                        
                        frappe.msgprint({
                            title: __('Available Zones'),
                            message: zone_list,
                            indicator: 'blue'
                        });
                    } else {
                        frappe.msgprint(__('No alternative zones available'));
                    }
                }
            });
        });

        dialog.fields_dict.prioritize_sales.$input.click(function() {
            frappe.set_route('List', 'Part Storage Location', {
                'storage_zone': frm.doc.name,
                'priority_to_sell': 'High',
                'status': 'Stored'
            });
        });

        dialog.show();
    }
});

// Child table events for allowed categories
frappe.ui.form.on('Storage Zone Allowed Category', {
    part_category: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        
        // Auto-translate common part categories to Arabic
        const category_translations = {
            'Engine': 'محرك',
            'Transmission': 'ناقل الحركة',
            'Brakes': 'فرامل',
            'Suspension': 'تعليق',
            'Electrical': 'كهربائي',
            'Electronics': 'إلكترونيات',
            'Body': 'هيكل',
            'Interior': 'داخلي',
            'Safety Systems': 'أنظمة الأمان',
            'Exhaust': 'عادم',
            'Cooling': 'تبريد',
            'Fuel System': 'نظام الوقود',
            'Steering': 'توجيه',
            'Wheels & Tires': 'عجلات وإطارات',
            'Lighting': 'إضاءة',
            'Hazmat': 'مواد خطرة',
            'Other': 'أخرى'
        };

        if (category_translations[row.part_category]) {
            frappe.model.set_value(cdt, cdn, 'part_category_ar', 
                category_translations[row.part_category]);
        }
    },

    is_restricted: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        
        if (row.is_restricted && frm.doc.zone_type === 'General') {
            frappe.msgprint({
                title: __('Warning'),
                message: __('General zones should not have restricted categories'),
                indicator: 'orange'
            });
        }
    }
});
