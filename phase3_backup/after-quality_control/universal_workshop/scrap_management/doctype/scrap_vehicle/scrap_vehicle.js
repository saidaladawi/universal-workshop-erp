// Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
// For license information, please see license.txt

// Scrap Vehicle Form Script - ERPNext v15 with Arabic Support
frappe.ui.form.on('Scrap Vehicle', {
    refresh: function (frm) {
        frm.trigger('setup_arabic_fields');
        frm.trigger('setup_workflow_buttons');
        frm.trigger('setup_custom_buttons');
        frm.trigger('setup_field_dependencies');
        frm.trigger('update_dashboard_data');
        frm.trigger('setup_dashboard');
        frm.trigger('setup_calculations');
    },

    onload: function (frm) {
        frm.trigger('setup_field_filters');
        frm.trigger('setup_field_formatters');
    },

    setup_arabic_fields: function (frm) {
        // Set RTL direction for Arabic fields
        const arabic_fields = [
            'vehicle_title_ar', 'seller_name_ar', 'assessment_notes',
            'acquisition_notes', 'seller_address', 'owner_name_ar', 'address_ar',
            'assessment_notes_ar', 'dismantling_notes_ar', 'compliance_notes_ar'
        ];

        arabic_fields.forEach(field => {
            if (frm.fields_dict[field] && frm.fields_dict[field].$input) {
                frm.fields_dict[field].$input.attr('dir', 'rtl');
                frm.fields_dict[field].$input.css('text-align', 'right');
                frm.fields_dict[field].$input.addClass('arabic-text');
            }
        });

        // Auto-direction detection for mixed content
        frm.fields_dict.vehicle_title?.$input.on('input', function () {
            const text = $(this).val();
            const direction = frm.events.detect_text_direction(text);
            $(this).attr('dir', direction);
        });

        // Auto-suggest Arabic name if English name is provided
        if (frm.doc.owner_name && !frm.doc.owner_name_ar) {
            frm.set_value('owner_name_ar', '');
            frappe.msgprint(__('Please enter the Arabic name for the vehicle owner'));
        }
    },

    setup_workflow_buttons: function (frm) {
        if (!frm.doc.__islocal) {
            // Start Assessment Button
            if (frm.doc.status === 'Acquired' || frm.doc.status === 'Assessment Pending') {
                frm.add_custom_button(__('Start Assessment'), function () {
                    frm.call('start_condition_assessment').then(() => {
                        frm.reload_doc();
                    });
                }, __('Workflow'));
            }

            // Complete Assessment Button  
            if (frm.doc.status === 'Assessment In Progress') {
                frm.add_custom_button(__('Complete Assessment'), function () {
                    frm.call('complete_condition_assessment').then(() => {
                        frm.reload_doc();
                    });
                }, __('Workflow'));
            }

            // Ready for Dismantling Button
            if (frm.doc.status === 'Assessment Complete') {
                frm.add_custom_button(__('Mark Ready for Dismantling'), function () {
                    frm.call('mark_ready_for_dismantling').then(() => {
                        frm.reload_doc();
                    });
                }, __('Workflow'));
            }
        }
    },

    setup_custom_buttons: function (frm) {
        if (!frm.doc.__islocal) {
            // Remove all existing custom buttons first
            frm.clear_custom_buttons();

            // Add status-specific buttons
            if (frm.doc.status === "Assessed" && !frm.doc.approved_for_scrapping) {
                frm.add_custom_button(__('Approve for Scrapping'), function () {
                    frm.set_value('approved_for_scrapping', 1);
                    frm.set_value('status', 'Approved for Scrapping');
                    frm.save();
                }).addClass('btn-success');
            }

            if (frm.doc.status === "Approved for Scrapping") {
                frm.add_custom_button(__('Start Dismantling'), function () {
                    frm.trigger('start_dismantling_workflow');
                }).addClass('btn-primary');
            }

            if (frm.doc.status === "In Dismantling") {
                frm.add_custom_button(__('Complete Dismantling'), function () {
                    frm.trigger('complete_dismantling_workflow');
                }).addClass('btn-success');

                frm.add_custom_button(__('Add Extracted Part'), function () {
                    frm.trigger('add_extracted_part');
                }).addClass('btn-secondary');
            }

            // Always available buttons
            frm.add_custom_button(__('Generate Assessment Report'), function () {
                frm.trigger('generate_assessment_report');
            });

            frm.add_custom_button(__('Calculate ROI Projection'), function () {
                frm.trigger('calculate_roi_projection');
            });

            frm.add_custom_button(__('Print Barcode'), function () {
                frm.trigger('print_storage_barcode');
            });

            // Photo management buttons
            frm.add_custom_button(__('Photo Gallery'), function () {
                frm.trigger('show_photo_gallery');
            });
        }
    },

    setup_field_dependencies: function (frm) {
        // Show assessment fields only when status allows
        const assessment_fields = [
            'overall_condition', 'assessment_date', 'assessed_by',
            'estimated_dismantling_hours', 'estimated_parts_value'
        ];

        const show_assessment = ['Assessment In Progress', 'Assessment Complete',
            'Dismantling Planned', 'Dismantling In Progress',
            'Parts Extracted'].includes(frm.doc.status);

        assessment_fields.forEach(field => {
            frm.toggle_display(field, show_assessment);
        });

        // Currency field dependency
        frm.toggle_reqd('acquisition_currency', frm.doc.acquisition_cost > 0);
    },

    setup_field_filters: function (frm) {
        // Filter technicians to only show active ones
        frm.set_query('assigned_technician', function () {
            return {
                filters: {
                    'employment_status': 'Active',
                    'department': ['in', ['Engine', 'Body', 'Electrical', 'General']]
                }
            };
        });

        // Filter assessor to workshop staff
        frm.set_query('assessed_by', function () {
            return {
                filters: {
                    'enabled': 1,
                    'role_profile_name': ['in', ['Workshop Manager', 'Workshop Technician']]
                }
            };
        });
    },

    setup_field_formatters: function (frm) {
        // Format currency fields for Oman (3 decimal places)
        const currency_fields = ['acquisition_cost', 'transport_cost',
            'documentation_cost', 'total_acquisition_cost',
            'estimated_parts_value'];

        currency_fields.forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].df.precision = 3;
            }
        });
    },

    update_dashboard_data: function (frm) {
        if (!frm.doc.__islocal && frm.doc.total_acquisition_cost) {
            frappe.call({
                method: 'get_profit_potential',
                doc: frm.doc,
                callback: function (r) {
                    if (r.message) {
                        frm.dashboard.add_indicator(
                            __('Potential Profit: {0} OMR', [r.message.potential_profit.toFixed(3)]),
                            r.message.potential_profit > 0 ? 'green' : 'red'
                        );
                        frm.dashboard.add_indicator(
                            __('Profit Margin: {0}%', [r.message.profit_margin.toFixed(1)]),
                            r.message.profit_margin > 20 ? 'green' : r.message.profit_margin > 0 ? 'yellow' : 'red'
                        );
                    }
                }
            });
        }
    },

    // Field Events
    vehicle_title: function (frm) {
        // Auto-suggest Arabic title when English title is entered
        if (frm.doc.vehicle_title && !frm.doc.vehicle_title_ar) {
            frm.trigger('suggest_arabic_vehicle_title');
        }
    },

    seller_name: function (frm) {
        // Auto-suggest Arabic seller name
        if (frm.doc.seller_name && !frm.doc.seller_name_ar) {
            frm.trigger('suggest_arabic_seller_name');
        }
    },

    acquisition_cost: function (frm) {
        frm.trigger('calculate_totals');
    },

    transport_cost: function (frm) {
        frm.trigger('calculate_totals');
    },

    documentation_cost: function (frm) {
        frm.trigger('calculate_totals');
    },

    overall_condition: function (frm) {
        if (frm.doc.overall_condition) {
            // Auto-set assessment date
            if (!frm.doc.assessment_date) {
                frm.set_value('assessment_date', frappe.datetime.get_today());
            }

            // Auto-set assessor
            if (!frm.doc.assessed_by) {
                frm.set_value('assessed_by', frappe.session.user);
            }

            // Suggest estimated hours based on condition
            frm.trigger('suggest_dismantling_hours');
        }
    },

    vin: function (frm) {
        if (frm.doc.vin) {
            // Convert to uppercase and validate
            frm.set_value('vin', frm.doc.vin.toUpperCase());
            frm.trigger('validate_vin_format');
        }
    },

    seller_phone: function (frm) {
        if (frm.doc.seller_phone) {
            frm.trigger('validate_oman_phone');
        }
    },

    // Helper Functions
    calculate_totals: function (frm) {
        const base_cost = frm.doc.acquisition_cost || 0;
        const transport_cost = frm.doc.transport_cost || 0;
        const documentation_cost = frm.doc.documentation_cost || 0;

        const total = base_cost + transport_cost + documentation_cost;
        frm.set_value('total_acquisition_cost', total);
    },

    suggest_arabic_vehicle_title: function (frm) {
        // Simple transliteration suggestion (could be enhanced with API)
        const english_title = frm.doc.vehicle_title;
        const arabic_suggestion = frm.events.get_arabic_suggestion(english_title);

        if (arabic_suggestion) {
            frm.set_value('vehicle_title_ar', arabic_suggestion);
        }
    },

    suggest_arabic_seller_name: function (frm) {
        const english_name = frm.doc.seller_name;
        const arabic_suggestion = frm.events.get_arabic_suggestion(english_name);

        if (arabic_suggestion) {
            frm.set_value('seller_name_ar', arabic_suggestion);
        }
    },

    suggest_dismantling_hours: function (frm) {
        const condition_hours = {
            'Excellent': 8,
            'Good': 12,
            'Fair': 16,
            'Poor': 24,
            'Salvage Only': 32
        };

        const suggested_hours = condition_hours[frm.doc.overall_condition];
        if (suggested_hours && !frm.doc.estimated_dismantling_hours) {
            frm.set_value('estimated_dismantling_hours', suggested_hours);
        }
    },

    validate_vin_format: function (frm) {
        const vin = frm.doc.vin;
        const vin_pattern = /^[A-HJ-NPR-Z0-9]{17}$/;

        if (vin && !vin_pattern.test(vin)) {
            frappe.msgprint({
                title: __('Invalid VIN'),
                message: __('VIN must be 17 alphanumeric characters (excluding I, O, Q)'),
                indicator: 'red'
            });
        }
    },

    validate_oman_phone: function (frm) {
        const phone = frm.doc.seller_phone;
        const oman_phone_pattern = /^\+968\s?\d{8}$/;

        if (phone && !oman_phone_pattern.test(phone)) {
            frappe.msgprint({
                title: __('Invalid Phone Number'),
                message: __('Oman phone number format: +968 XXXXXXXX'),
                indicator: 'orange'
            });
        }
    },

    show_profit_analysis: function (frm) {
        frappe.call({
            method: 'get_profit_potential',
            doc: frm.doc,
            callback: function (r) {
                if (r.message) {
                    const data = r.message;
                    const dialog = new frappe.ui.Dialog({
                        title: __('Profit Analysis'),
                        fields: [
                            {
                                fieldtype: 'HTML',
                                fieldname: 'profit_analysis',
                                options: `
                                    <div class="profit-analysis">
                                        <table class="table table-bordered">
                                            <tr><td><strong>${__('Total Cost')}</strong></td><td>${data.total_cost.toFixed(3)} OMR</td></tr>
                                            <tr><td><strong>${__('Estimated Value')}</strong></td><td>${data.estimated_value.toFixed(3)} OMR</td></tr>
                                            <tr><td><strong>${__('Potential Profit')}</strong></td><td class="${data.potential_profit > 0 ? 'text-success' : 'text-danger'}">${data.potential_profit.toFixed(3)} OMR</td></tr>
                                            <tr><td><strong>${__('Profit Margin')}</strong></td><td class="${data.profit_margin > 0 ? 'text-success' : 'text-danger'}">${data.profit_margin.toFixed(1)}%</td></tr>
                                        </table>
                                    </div>
                                `
                            }
                        ]
                    });
                    dialog.show();
                }
            }
        });
    },

    open_photo_manager: function (frm) {
        frappe.route_options = { 'scrap_vehicle': frm.doc.name };
        frappe.set_route('List', 'Scrap Vehicle Photo');
    },

    open_document_manager: function (frm) {
        frappe.route_options = { 'parent': frm.doc.name };
        frappe.set_route('List', 'Scrap Vehicle Document');
    },

    detect_text_direction: function (text) {
        // Simple Arabic text detection
        const arabic_pattern = /[\u0600-\u06FF]/;
        const arabic_chars = (text.match(/[\u0600-\u06FF]/g) || []).length;
        const total_chars = text.replace(/\s/g, '').length;

        return (arabic_chars / total_chars > 0.3) ? 'rtl' : 'ltr';
    },

    get_arabic_suggestion: function (english_text) {
        // Simple transliteration mapping (would be enhanced with proper API)
        const transliteration_map = {
            'Toyota': 'تويوتا',
            'Honda': 'هوندا',
            'Nissan': 'نيسان',
            'BMW': 'بي إم دبليو',
            'Mercedes': 'مرسيدس',
            'Hyundai': 'هيونداي',
            'Kia': 'كيا',
            'Ford': 'فورد',
            'Chevrolet': 'شيفروليه'
        };

        // Check if any brand name exists in the text
        for (const [english, arabic] of Object.entries(transliteration_map)) {
            if (english_text.toLowerCase().includes(english.toLowerCase())) {
                return english_text.replace(new RegExp(english, 'gi'), arabic);
            }
        }

        return null;
    },

    setup_dashboard: function (frm) {
        if (frm.doc.__islocal) return;

        // Create dashboard showing key metrics
        const dashboard_html = `
            <div class="row scrap-vehicle-dashboard">
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h5 class="card-title">${__('Total Cost')}</h5>
                            <h3 class="text-danger">OMR ${(frm.doc.total_cost || 0).toFixed(3)}</h3>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h5 class="card-title">${__('Total Revenue')}</h5>
                            <h3 class="text-success">OMR ${(frm.doc.total_revenue || 0).toFixed(3)}</h3>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h5 class="card-title">${__('Gross Profit')}</h5>
                            <h3 class="${frm.doc.gross_profit >= 0 ? 'text-success' : 'text-danger'}">
                                OMR ${(frm.doc.gross_profit || 0).toFixed(3)}
                            </h3>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h5 class="card-title">${__('ROI')}</h5>
                            <h3 class="${frm.doc.roi_percentage >= 0 ? 'text-success' : 'text-danger'}">
                                ${(frm.doc.roi_percentage || 0).toFixed(2)}%
                            </h3>
                        </div>
                    </div>
                </div>
            </div>
        `;

        frm.dashboard.add_section(dashboard_html, __('Financial Summary'));
    },

    setup_calculations: function (frm) {
        // Auto-calculate financial metrics when cost/revenue fields change
        const cost_fields = ['acquisition_cost', 'assessment_cost', 'dismantling_cost', 'storage_cost'];
        const revenue_fields = ['parts_sales_revenue', 'scrap_metal_revenue', 'other_revenue'];

        [...cost_fields, ...revenue_fields].forEach(field => {
            frm.trigger(field);
        });
    },

    // Financial calculation triggers
    assessment_cost: function (frm) {
        frm.trigger('calculate_totals');
    },

    dismantling_cost: function (frm) {
        frm.trigger('calculate_totals');
    },

    storage_cost: function (frm) {
        frm.trigger('calculate_totals');
    },

    parts_sales_revenue: function (frm) {
        frm.trigger('calculate_totals');
    },

    scrap_metal_revenue: function (frm) {
        frm.trigger('calculate_totals');
    },

    other_revenue: function (frm) {
        frm.trigger('calculate_totals');
    },

    calculate_totals: function (frm) {
        // Calculate total costs
        const total_cost = (frm.doc.acquisition_cost || 0) +
            (frm.doc.assessment_cost || 0) +
            (frm.doc.dismantling_cost || 0) +
            (frm.doc.storage_cost || 0);

        // Calculate total revenue
        const total_revenue = (frm.doc.parts_sales_revenue || 0) +
            (frm.doc.scrap_metal_revenue || 0) +
            (frm.doc.other_revenue || 0);

        // Calculate profit metrics
        const gross_profit = total_revenue - total_cost;
        const profit_margin = total_revenue > 0 ? (gross_profit / total_revenue) * 100 : 0;
        const roi_percentage = total_cost > 0 ? (gross_profit / total_cost) * 100 : 0;

        // Update fields
        frm.set_value('total_cost', parseFloat(total_cost.toFixed(3)));
        frm.set_value('total_revenue', parseFloat(total_revenue.toFixed(3)));
        frm.set_value('gross_profit', parseFloat(gross_profit.toFixed(3)));
        frm.set_value('profit_margin', parseFloat(profit_margin.toFixed(2)));
        frm.set_value('roi_percentage', parseFloat(roi_percentage.toFixed(2)));

        // Refresh dashboard
        frm.trigger('setup_dashboard');
    },

    // VIN number validation
    vin_number: function (frm) {
        if (frm.doc.vin_number) {
            const vin = frm.doc.vin_number.toUpperCase().trim();

            // Basic VIN validation
            const vin_pattern = /^[A-HJ-NPR-Z0-9]{17}$/;
            if (!vin_pattern.test(vin)) {
                frappe.msgprint({
                    message: __('Invalid VIN number format. Must be 17 characters, alphanumeric excluding I, O, Q'),
                    indicator: 'red'
                });
                frm.set_value('vin_number', '');
                return;
            }

            // Auto-decode VIN information if possible
            frm.trigger('decode_vin_info');
        }
    },

    decode_vin_info: function (frm) {
        if (frm.doc.vin_number && frm.doc.vin_number.length === 17) {
            // Call VIN decoder API
            frappe.call({
                method: 'universal_workshop.vehicle_management.api.decode_vin',
                args: {
                    vin_number: frm.doc.vin_number
                },
                callback: function (r) {
                    if (r.message && r.message.success) {
                        const vin_data = r.message.data;

                        // Auto-fill vehicle information
                        if (vin_data.make && !frm.doc.make) {
                            frm.set_value('make', vin_data.make);
                        }
                        if (vin_data.model && !frm.doc.model) {
                            frm.set_value('model', vin_data.model);
                        }
                        if (vin_data.year && !frm.doc.year) {
                            frm.set_value('year', vin_data.year);
                        }
                        if (vin_data.engine_type && !frm.doc.engine_type) {
                            frm.set_value('engine_type', vin_data.engine_type);
                        }

                        frappe.msgprint({
                            message: __('VIN decoded successfully. Vehicle information updated.'),
                            indicator: 'green'
                        });
                    }
                }
            });
        }
    },

    // Assessment completion
    assessment_completed: function (frm) {
        if (frm.doc.assessment_completed) {
            if (!frm.doc.assessment_date) {
                frm.set_value('assessment_date', frappe.datetime.get_today());
            }
            if (!frm.doc.assessor) {
                frm.set_value('assessor', frappe.session.user_fullname);
            }

            // Update status
            if (frm.doc.status === 'Draft') {
                frm.set_value('status', 'Assessed');
            }

            frappe.msgprint({
                message: __('Assessment marked complete. Vehicle is ready for approval.'),
                indicator: 'blue'
            });
        }
    },

    // Phone number validation
    owner_phone: function (frm) {
        if (frm.doc.owner_phone) {
            const phone = frm.doc.owner_phone.trim();
            const oman_pattern = /^\+968\s?\d{8}$/;

            if (!oman_pattern.test(phone)) {
                frappe.msgprint({
                    message: __('Invalid Oman phone number format. Use +968 XXXXXXXX'),
                    indicator: 'red'
                });
                frm.set_value('owner_phone', '');
            }
        }
    },

    // Workflow methods
    start_dismantling_workflow: function (frm) {
        frappe.confirm(
            __('Are you sure you want to start the dismantling process? This action cannot be undone.'),
            function () {
                frappe.call({
                    method: 'start_dismantling',
                    doc: frm.doc,
                    callback: function (r) {
                        if (!r.exc) {
                            frm.reload_doc();
                        }
                    }
                });
            }
        );
    },

    complete_dismantling_workflow: function (frm) {
        frappe.confirm(
            __('Mark dismantling as complete? All extracted parts will be moved to storage.'),
            function () {
                frappe.call({
                    method: 'complete_dismantling',
                    doc: frm.doc,
                    callback: function (r) {
                        if (!r.exc) {
                            frm.reload_doc();
                        }
                    }
                });
            }
        );
    },

    add_extracted_part: function (frm) {
        // Open dialog to add extracted part
        const dialog = new frappe.ui.Dialog({
            title: __('Add Extracted Part'),
            fields: [
                {
                    fieldtype: 'Link',
                    fieldname: 'item_code',
                    label: __('Item Code'),
                    options: 'Item',
                    reqd: 1
                },
                {
                    fieldtype: 'Data',
                    fieldname: 'part_name',
                    label: __('Part Name'),
                    reqd: 1
                },
                {
                    fieldtype: 'Data',
                    fieldname: 'part_name_ar',
                    label: __('Part Name (Arabic)')
                },
                {
                    fieldtype: 'Select',
                    fieldname: 'condition_grade',
                    label: __('Condition Grade'),
                    options: '\nA - Like New\nB - Excellent\nC - Good\nD - Fair\nE - Poor\nF - Scrap Only',
                    reqd: 1
                },
                {
                    fieldtype: 'Currency',
                    fieldname: 'estimated_value',
                    label: __('Estimated Value (OMR)'),
                    default: 0
                },
                {
                    fieldtype: 'Link',
                    fieldname: 'storage_location',
                    label: __('Storage Location'),
                    options: 'Warehouse'
                }
            ],
            primary_action: function (values) {
                // Add part to extracted parts table
                const new_part = frm.add_child('extracted_parts');
                Object.assign(new_part, values);
                new_part.extraction_date = frappe.datetime.get_today();
                new_part.part_status = 'Extracted';

                // Generate barcode for the part
                new_part.part_barcode = `${frm.doc.name}-${new_part.item_code}-${Date.now()}`;

                frm.refresh_field('extracted_parts');
                frm.trigger('calculate_totals');
                dialog.hide();

                frappe.msgprint({
                    message: __('Extracted part added successfully'),
                    indicator: 'green'
                });
            },
            primary_action_label: __('Add Part')
        });

        dialog.show();
    },

    generate_assessment_report: function (frm) {
        frappe.call({
            method: 'generate_assessment_report',
            doc: frm.doc,
            callback: function (r) {
                if (r.message) {
                    // Open print dialog with assessment report
                    frappe.ui.form.qr_dialog({
                        report_data: r.message,
                        title: __('Vehicle Assessment Report')
                    });
                }
            }
        });
    },

    calculate_roi_projection: function (frm) {
        const dialog = new frappe.ui.Dialog({
            title: __('ROI Projection Calculator'),
            fields: [
                {
                    fieldtype: 'Percent',
                    fieldname: 'markup_percent',
                    label: __('Parts Markup Percentage'),
                    default: 20,
                    description: __('Expected markup on parts sales')
                }
            ],
            primary_action: function (values) {
                frappe.call({
                    method: 'calculate_roi_projection',
                    doc: frm.doc,
                    args: {
                        parts_markup_percent: values.markup_percent
                    },
                    callback: function (r) {
                        if (r.message) {
                            const data = r.message;
                            frappe.msgprint({
                                title: __('ROI Projection'),
                                message: `
                                    <div class="row">
                                        <div class="col-md-6">
                                            <p><strong>${__('Projected Parts Revenue')}:</strong> OMR ${data.projected_parts_revenue}</p>
                                            <p><strong>${__('Projected Scrap Revenue')}:</strong> OMR ${data.projected_scrap_revenue}</p>
                                            <p><strong>${__('Total Projected Revenue')}:</strong> OMR ${data.total_projected_revenue}</p>
                                        </div>
                                        <div class="col-md-6">
                                            <p><strong>${__('Projected Profit')}:</strong> OMR ${data.projected_profit}</p>
                                            <p><strong>${__('Projected ROI')}:</strong> ${data.projected_roi_percent}%</p>
                                            <p><strong>${__('High Value Parts')}:</strong> ${data.high_value_parts_count}</p>
                                        </div>
                                    </div>
                                `,
                                indicator: 'blue'
                            });
                        }
                    }
                });
                dialog.hide();
            },
            primary_action_label: __('Calculate')
        });

        dialog.show();
    },

    print_storage_barcode: function (frm) {
        if (!frm.doc.storage_barcode) {
            frappe.call({
                method: 'generate_vehicle_barcode',
                args: {
                    vehicle_name: frm.doc.name
                },
                callback: function (r) {
                    if (r.message) {
                        frm.set_value('storage_barcode', r.message);
                        frm.trigger('open_barcode_print');
                    }
                }
            });
        } else {
            frm.trigger('open_barcode_print');
        }
    },

    open_barcode_print: function (frm) {
        // Open barcode print dialog
        const print_html = `
            <div style="text-align: center; padding: 20px;">
                <h3>${frm.doc.name}</h3>
                <div style="font-family: monospace; font-size: 24px; margin: 20px;">
                    ${frm.doc.storage_barcode}
                </div>
                <p>${frm.doc.make} ${frm.doc.model} ${frm.doc.year}</p>
                <p>VIN: ${frm.doc.vin_number}</p>
            </div>
        `;

        const print_window = window.open('', 'Print Barcode', 'width=400,height=300');
        print_window.document.write(print_html);
        print_window.print();
    },

    show_photo_gallery: function (frm) {
        // Collect all photo fields
        const photo_fields = [
            'overall_condition_photo', 'engine_photo', 'interior_photo',
            'exterior_damage_photo', 'parts_photo', 'documentation_photo'
        ];

        const photos = photo_fields
            .filter(field => frm.doc[field])
            .map(field => ({
                title: __(field.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())),
                url: frm.doc[field]
            }));

        if (photos.length === 0) {
            frappe.msgprint(__('No photos available'));
            return;
        }

        // Create photo gallery dialog
        const gallery_html = photos.map(photo => `
            <div class="col-md-4 mb-3">
                <div class="card">
                    <img src="${photo.url}" class="card-img-top" style="height: 200px; object-fit: cover;">
                    <div class="card-body">
                        <p class="card-text">${photo.title}</p>
                    </div>
                </div>
            </div>
        `).join('');

        const dialog = new frappe.ui.Dialog({
            title: __('Vehicle Photo Gallery'),
            size: 'large',
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'gallery',
                    options: `<div class="row">${gallery_html}</div>`
                }
            ]
        });

        dialog.show();
    }
});

// Photo table events
frappe.ui.form.on('Scrap Vehicle Photo', {
    photo_file: function (frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row.photo_file && !row.photo_title) {
            // Auto-generate title based on photo type
            row.photo_title = `${row.photo_type || 'Photo'} - ${frappe.datetime.get_today()}`;
            frm.refresh_field('vehicle_photos');
        }
    },

    photo_type: function (frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row.photo_type && !row.photo_title) {
            row.photo_title = `${row.photo_type} - ${frappe.datetime.get_today()}`;
            frm.refresh_field('vehicle_photos');
        }
    }
});

// Document table events
frappe.ui.form.on('Scrap Vehicle Document', {
    document_file: function (frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row.document_file && !row.document_title) {
            // Auto-generate title based on document type
            row.document_title = `${row.document_type || 'Document'} - ${frappe.datetime.get_today()}`;
            frm.refresh_field('acquisition_documents');
        }
    }
});

// Child table events for extracted parts
frappe.ui.form.on('Scrap Vehicle Extracted Part', {
    sale_price: function (frm, cdt, cdn) {
        frm.trigger('calculate_totals');
    },

    condition_grade: function (frm, cdt, cdn) {
        const row = locals[cdt][cdn];

        // Auto-suggest estimated values based on condition grade
        const grade_multipliers = {
            'A - Like New': 1.0,
            'B - Excellent': 0.8,
            'C - Good': 0.6,
            'D - Fair': 0.4,
            'E - Poor': 0.2,
            'F - Scrap Only': 0.1
        };

        if (row.condition_grade && grade_multipliers[row.condition_grade]) {
            // This would ideally get base part value from item master
            // For now, suggest based on grade
            frappe.msgprint({
                message: __('Condition grade set. Please estimate value based on market conditions.'),
                indicator: 'blue'
            });
        }
    }
});

// Dashboard utilities
frappe.scrap_vehicle = {
    get_dashboard_data: function () {
        frappe.call({
            method: 'universal_workshop.scrap_management.doctype.scrap_vehicle.scrap_vehicle.get_scrap_vehicle_dashboard_data',
            callback: function (r) {
                if (r.message) {
                    console.log('Scrap Vehicle Dashboard Data:', r.message);
                }
            }
        });
    }
}; 