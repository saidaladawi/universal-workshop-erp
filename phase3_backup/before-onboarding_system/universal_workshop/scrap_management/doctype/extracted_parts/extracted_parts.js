// Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
// For license information, please see license.txt

frappe.ui.form.on('Extracted Parts', {
    refresh: function (frm) {
        frm.trigger('setup_arabic_fields');
        frm.trigger('setup_custom_buttons');
        frm.trigger('setup_grading_interface');
        frm.trigger('setup_photo_gallery');
        frm.trigger('update_ui_based_on_status');
    },

    onload: function (frm) {
        frm.trigger('setup_filters');
        frm.trigger('load_quality_standards');
    },

    setup_arabic_fields: function (frm) {
        // Auto-direction for Arabic fields
        ['part_name_ar', 'grade_description_ar'].forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.attr('dir', 'rtl');
                frm.fields_dict[field].$input.css('text-align', 'right');
                frm.fields_dict[field].$input.addClass('arabic-text');
            }
        });
    },

    setup_custom_buttons: function (frm) {
        if (frm.doc.docstatus === 1) {
            // Pricing Analysis Button
            frm.add_custom_button(__('Pricing Analysis'), () => {
                frm.trigger('show_pricing_analysis');
            }, __('Analysis'));

            // Generate Barcode Button
            frm.add_custom_button(__('Generate Barcode'), () => {
                frm.trigger('generate_barcode_label');
            }, __('Documents'));

            // Quality Inspection Button
            frm.add_custom_button(__('Quality Inspection'), () => {
                frm.trigger('show_quality_inspection');
            }, __('Quality'));

            // Market Comparison Button
            frm.add_custom_button(__('Market Comparison'), () => {
                frm.trigger('show_market_comparison');
            }, __('Analysis'));
        }

        if (frm.doc.quality_grade && !frm.doc.certification_status) {
            frm.add_custom_button(__('Certify Quality'), () => {
                frm.trigger('certify_quality_grade');
            }, __('Quality'));
        }
    },

    setup_grading_interface: function (frm) {
        if (frm.fields_dict.quality_grade) {
            // Add grade descriptions as help text
            const grade_help = {
                'Grade A - Excellent': __('Like-new condition, 60-80% of new part value'),
                'Grade B - Good': __('Good condition, minor wear, 40-60% of new part value'),
                'Grade C - Average': __('Average condition, may need repairs, 20-40% of new part value'),
                'Grade D - Poor/Scrap': __('Damaged, scrap value only')
            };

            frm.set_df_property('quality_grade', 'description',
                Object.entries(grade_help).map(([k, v]) => `<b>${k}:</b> ${v}`).join('<br>'));
        }
    },

    setup_photo_gallery: function (frm) {
        if (frm.fields_dict.photo_gallery) {
            // Add quick photo upload buttons
            const photo_types = [
                'Front View', 'Back View', 'Left Side', 'Right Side',
                'Overall Condition', 'Close-up Detail'
            ];

            let buttons_html = '<div class=\"photo-quick-buttons\" style=\"margin: 10px 0;\">';
            buttons_html += '<p><b>' + __('Quick Photo Types:') + '</b></p>';

            photo_types.forEach(type => {
                buttons_html += `<button class=\"btn btn-xs btn-default photo-type-btn\" 
                                data-type=\"${type}\" style=\"margin: 2px;\">${__(type)}</button>`;
            });
            buttons_html += '</div>';

            if (frm.fields_dict.photo_gallery.$wrapper) {
                frm.fields_dict.photo_gallery.$wrapper.prepend(buttons_html);

                // Handle quick photo type selection
                frm.fields_dict.photo_gallery.$wrapper.find('.photo-type-btn').on('click', function () {
                    const photo_type = $(this).data('type');
                    frm.trigger('add_photo_row', { photo_type: photo_type });
                });
            }
        }
    },

    setup_filters: function (frm) {
        // Set filters for link fields
        frm.set_query('scrap_vehicle', () => {
            return {
                filters: {
                    'vehicle_status': ['in', ['Acquired', 'Processing']]
                }
            };
        });

        frm.set_query('disassembly_plan', () => {
            return {
                filters: {
                    'scrap_vehicle': frm.doc.scrap_vehicle,
                    'plan_status': ['!=', 'Cancelled']
                }
            };
        });

        frm.set_query('warehouse', () => {
            return {
                filters: {
                    'is_group': 0
                }
            };
        });
    },

    load_quality_standards: function (frm) {
        // Load quality standards reference data
        if (frm.is_new()) {
            frm.doc.currency = 'OMR';
            frm.doc.extraction_date = frappe.datetime.now_date();
            frm.doc.certification_status = 'Pending Inspection';
            frm.refresh_fields();
        }
    },

    update_ui_based_on_status: function (frm) {
        // Update UI based on workflow state
        if (frm.doc.workflow_state) {
            const state_colors = {
                'Extracted': 'blue',
                'Inspected': 'orange',
                'Certified': 'green',
                'Listed': 'purple',
                'Sold': 'gray',
                'Scrapped': 'red'
            };

            if (state_colors[frm.doc.workflow_state]) {
                frm.dashboard.set_headline_color(state_colors[frm.doc.workflow_state]);
            }
        }

        // Show quality grade badge
        if (frm.doc.quality_grade) {
            const grade_colors = {
                'Grade A - Excellent': 'green',
                'Grade B - Good': 'blue',
                'Grade C - Average': 'orange',
                'Grade D - Poor/Scrap': 'red'
            };

            const grade_short = frm.doc.quality_grade.split(' - ')[0];
            frm.dashboard.add_indicator(grade_short, grade_colors[frm.doc.quality_grade] || 'gray');
        }
    },

    // Field Events
    scrap_vehicle: function (frm) {
        if (frm.doc.scrap_vehicle) {
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Scrap Vehicle',
                    name: frm.doc.scrap_vehicle
                },
                callback: function (r) {
                    if (r.message) {
                        frm.set_value('vehicle_vin', r.message.vin_number);
                        frm.set_value('vehicle_make_model',
                            `${r.message.make} ${r.message.model} (${r.message.year})`);
                    }
                }
            });
        }
    },

    quality_grade: function (frm) {
        frm.trigger('update_grade_description');
        frm.trigger('calculate_suggested_price');
        frm.trigger('update_ui_based_on_status');
    },

    base_price_new: function (frm) {
        frm.trigger('calculate_suggested_price');
    },

    physical_condition: function (frm) {
        frm.trigger('calculate_suggested_price');
    },

    functional_status: function (frm) {
        frm.trigger('calculate_suggested_price');
    },

    estimated_repair_cost: function (frm) {
        frm.trigger('calculate_suggested_price');
    },

    part_name: function (frm) {
        if (frm.doc.part_name && !frm.doc.part_name_ar) {
            frm.trigger('suggest_arabic_translation');
        }
    },

    // Custom Methods
    update_grade_description: function (frm) {
        if (frm.doc.quality_grade) {
            const descriptions = {
                'Grade A - Excellent': {
                    en: 'Like-new condition, minimal usage signs, 60-80% of new part value',
                    ar: 'حالة شبه جديدة، علامات استخدام قليلة، 60-80% من قيمة القطعة الجديدة'
                },
                'Grade B - Good': {
                    en: 'Good condition with minor surface wear, no repairs needed, 40-60% of new part value',
                    ar: 'حالة جيدة مع تآكل سطحي بسيط، لا تحتاج إصلاحات، 40-60% من قيمة القطعة الجديدة'
                },
                'Grade C - Average': {
                    en: 'Average condition, may need minor repairs before use, 20-40% of new part value',
                    ar: 'حالة متوسطة، قد تحتاج إصلاحات بسيطة قبل الاستخدام، 20-40% من قيمة القطعة الجديدة'
                },
                'Grade D - Poor/Scrap': {
                    en: 'Damaged, only suitable for recycling or partial use, scrap value',
                    ar: 'متضررة، مناسبة فقط لإعادة التدوير أو الاستخدام الجزئي، قيمة الخردة'
                }
            };

            if (descriptions[frm.doc.quality_grade]) {
                if (!frm.doc.grade_description) {
                    frm.set_value('grade_description', descriptions[frm.doc.quality_grade].en);
                }
                if (!frm.doc.grade_description_ar) {
                    frm.set_value('grade_description_ar', descriptions[frm.doc.quality_grade].ar);
                }
            }
        }
    },

    calculate_suggested_price: function (frm) {
        if (frm.doc.base_price_new && frm.doc.quality_grade) {
            frappe.call({
                method: 'universal_workshop.scrap_management.doctype.extracted_parts.extracted_parts.get_part_pricing_analysis',
                args: {
                    part_name: frm.doc.part_name,
                    quality_grade: frm.doc.quality_grade,
                    base_price_new: frm.doc.base_price_new
                },
                callback: function (r) {
                    if (r.message) {
                        frm.set_value('suggested_price', r.message.suggested_price);
                        if (!frm.doc.final_price) {
                            frm.set_value('final_price', r.message.suggested_price);
                        }

                        // Show pricing range information
                        const range = r.message.price_range;
                        frappe.show_alert({
                            message: __('Suggested Price Range: {0} - {1} {2}',
                                [range.min.toFixed(3), range.max.toFixed(3), frm.doc.currency || 'OMR']),
                            indicator: 'blue'
                        });
                    }
                }
            });
        }
    },

    suggest_arabic_translation: function (frm) {
        // Common automotive parts translations
        const part_translations = {
            'Engine': 'محرك',
            'Transmission': 'ناقل الحركة',
            'Battery': 'بطارية',
            'Radiator': 'المبرد',
            'Alternator': 'المولد',
            'Starter': 'بادئ الحركة',
            'Brake Pad': 'قطعة الفرامل',
            'Air Filter': 'فلتر الهواء',
            'Oil Filter': 'فلتر الزيت',
            'Spark Plug': 'شمعة الإشعال',
            'Headlight': 'المصباح الأمامي',
            'Taillight': 'المصباح الخلفي',
            'Mirror': 'المرآة',
            'Wheel': 'العجلة',
            'Tire': 'الإطار',
            'Door': 'الباب',
            'Window': 'النافذة',
            'Seat': 'المقعد',
            'Steering Wheel': 'عجلة القيادة',
            'Dashboard': 'لوحة القيادة'
        };

        if (part_translations[frm.doc.part_name]) {
            frm.set_value('part_name_ar', part_translations[frm.doc.part_name]);
        }
    },

    add_photo_row: function (frm, args) {
        const photo_row = frm.add_child('photo_gallery');
        photo_row.photo_type = args.photo_type;
        frm.refresh_field('photo_gallery');

        // Scroll to the new row and focus on photo upload
        setTimeout(() => {
            const rows = frm.fields_dict.photo_gallery.grid.grid_rows;
            const last_row = rows[rows.length - 1];
            if (last_row) {
                last_row.toggle_view(true);
                const photo_field = last_row.grid_form.fields_dict.photo_attachment;
                if (photo_field) {
                    photo_field.$input.focus();
                }
            }
        }, 100);
    },

    show_pricing_analysis: function (frm) {
        frappe.call({
            method: 'universal_workshop.scrap_management.doctype.extracted_parts.extracted_parts.get_part_pricing_analysis',
            args: {
                part_name: frm.doc.part_name,
                quality_grade: frm.doc.quality_grade,
                base_price_new: frm.doc.base_price_new
            },
            callback: function (r) {
                if (r.message) {
                    const analysis = r.message;

                    let dialog_content = `
                        <div class=\"pricing-analysis\">
                            <h4>${__('Pricing Analysis for')} ${frm.doc.part_name}</h4>
                            <table class=\"table table-bordered\">
                                <tr><td><b>${__('Base Price (New)')}</b></td><td>${analysis.base_price_new.toFixed(3)} ${frm.doc.currency}</td></tr>
                                <tr><td><b>${__('Quality Grade')}</b></td><td>${frm.doc.quality_grade}</td></tr>
                                <tr><td><b>${__('Grade Multiplier')}</b></td><td>${(analysis.multiplier * 100).toFixed(1)}%</td></tr>
                                <tr><td><b>${__('Suggested Price')}</b></td><td>${analysis.suggested_price.toFixed(3)} ${frm.doc.currency}</td></tr>
                                <tr><td><b>${__('Price Range')}</b></td><td>${analysis.price_range.min.toFixed(3)} - ${analysis.price_range.max.toFixed(3)} ${frm.doc.currency}</td></tr>
                                <tr><td><b>${__('Market Position')}</b></td><td>${analysis.market_position}</td></tr>
                                <tr><td><b>${__('Target Buyers')}</b></td><td>${analysis.target_buyers}</td></tr>
                            </table>
                        </div>
                    `;

                    frappe.msgprint({
                        title: __('Pricing Analysis'),
                        message: dialog_content,
                        wide: true
                    });
                }
            }
        });
    },

    generate_barcode_label: function (frm) {
        frappe.call({
            method: 'universal_workshop.scrap_management.doctype.extracted_parts.extracted_parts.create_barcode_labels',
            args: {
                extracted_parts_list: [frm.doc.name]
            },
            callback: function (r) {
                if (r.message && r.message.length > 0) {
                    const label_data = r.message[0];

                    // Create printable barcode label
                    const print_content = `
                        <div style=\"text-align: center; padding: 20px; font-family: Arial, sans-serif;\">
                            <h3>${label_data.part_name}</h3>
                            <h4 style=\"color: #666;\">${label_data.part_name_ar}</h4>
                            <div style=\"font-size: 24px; font-family: 'Courier New', monospace; margin: 20px 0;\">
                                ${label_data.barcode}
                            </div>
                            <table style=\"margin: 20px auto; text-align: left;\">
                                <tr><td><b>Part Code:</b></td><td>${label_data.part_code}</td></tr>
                                <tr><td><b>Grade:</b></td><td>${label_data.quality_grade}</td></tr>
                                <tr><td><b>Price:</b></td><td>${label_data.final_price} ${label_data.currency}</td></tr>
                                <tr><td><b>Location:</b></td><td>${label_data.shelf_location || 'Not Set'}</td></tr>
                                <tr><td><b>VIN:</b></td><td>${label_data.vehicle_vin}</td></tr>
                                <tr><td><b>Date:</b></td><td>${label_data.extraction_date}</td></tr>
                            </table>
                        </div>
                    `;

                    const print_window = window.open('', '_blank');
                    print_window.document.write(`
                        <html>
                            <head><title>Barcode Label - ${label_data.part_name}</title></head>
                            <body>${print_content}</body>
                        </html>
                    `);
                    print_window.document.close();
                    print_window.print();
                }
            }
        });
    },

    show_quality_inspection: function (frm) {
        frappe.call({
            method: 'universal_workshop.scrap_management.doctype.extracted_parts.extracted_parts.generate_quality_inspection_checklist',
            args: {
                part_name: frm.doc.part_name,
                quality_grade: frm.doc.quality_grade
            },
            callback: function (r) {
                if (r.message) {
                    const checklist = r.message;

                    let checklist_html = `
                        <div class=\"quality-checklist\">
                            <h4>${__('Quality Inspection Checklist')}</h4>
                            <p><b>${__('Part')}:</b> ${checklist.part_name}</p>
                            <p><b>${__('Target Grade')}:</b> ${checklist.target_grade}</p>
                            <p><b>${__('Estimated Time')}:</b> ${checklist.estimated_time_minutes} ${__('minutes')}</p>
                            <br>
                            <table class=\"table table-striped\">
                                <thead>
                                    <tr>
                                        <th width=\"5%\">#</th>
                                        <th width=\"35%\">${__('Inspection Point')}</th>
                                        <th width=\"35%\">${__('Arabic')}</th>
                                        <th width=\"15%\">${__('Critical')}</th>
                                        <th width=\"10%\">${__('Status')}</th>
                                    </tr>
                                </thead>
                                <tbody>
                    `;

                    checklist.checklist.forEach((item, index) => {
                        checklist_html += `
                            <tr>
                                <td>${index + 1}</td>
                                <td>${item.point}</td>
                                <td style=\"direction: rtl; text-align: right;\">${item.point_ar}</td>
                                <td>${item.critical ? '⚠️ Critical' : 'Standard'}</td>
                                <td><input type=\"checkbox\" /></td>
                            </tr>
                        `;
                    });

                    checklist_html += `
                                </tbody>
                            </table>
                        </div>
                    `;

                    frappe.msgprint({
                        title: __('Quality Inspection Checklist'),
                        message: checklist_html,
                        wide: true
                    });
                }
            }
        });
    },

    show_market_comparison: function (frm) {
        frappe.call({
            method: 'universal_workshop.scrap_management.doctype.extracted_parts.extracted_parts.get_market_price_comparison',
            args: {
                part_name: frm.doc.part_name,
                quality_grade: frm.doc.quality_grade,
                region: 'Oman'
            },
            callback: function (r) {
                if (r.message) {
                    const comparison = r.message;

                    let comparison_html = `
                        <div class=\"market-comparison\">
                            <h4>${__('Market Price Comparison')}</h4>
                            <table class=\"table table-bordered\">
                                <tr><td><b>${__('Part Name')}</b></td><td>${comparison.part_name}</td></tr>
                                <tr><td><b>${__('Quality Grade')}</b></td><td>${comparison.quality_grade}</td></tr>
                                <tr><td><b>${__('Region')}</b></td><td>${comparison.region}</td></tr>
                                <tr><td><b>${__('Market Price')}</b></td><td>${comparison.estimated_market_price.toFixed(3)} ${comparison.currency}</td></tr>
                                <tr><td><b>${__('Price Range')}</b></td><td>${comparison.price_range.low.toFixed(3)} - ${comparison.price_range.high.toFixed(3)} ${comparison.currency}</td></tr>
                                <tr><td><b>${__('Demand Level')}</b></td><td>${comparison.demand_level}</td></tr>
                                <tr><td><b>${__('Recommendation')}</b></td><td>${comparison.recommendation}</td></tr>
                            </table>
                            <p><small><b>${__('Data Sources')}:</b> ${comparison.data_sources.join(', ')}</small></p>
                        </div>
                    `;

                    frappe.msgprint({
                        title: __('Market Comparison'),
                        message: comparison_html,
                        wide: true
                    });
                }
            }
        });
    },

    certify_quality_grade: function (frm) {
        frappe.confirm(
            __('Are you sure you want to certify this part as {0}?', [frm.doc.quality_grade]),
            () => {
                frm.set_value('certification_status', 'Certified');
                frm.set_value('inspector', frappe.session.user);
                frm.set_value('inspection_date', frappe.datetime.now_datetime());
                frm.save();

                frappe.show_alert({
                    message: __('Part quality certified successfully'),
                    indicator: 'green'
                });
            }
        );
    }
});

// Photo Gallery Events
frappe.ui.form.on('Part Photo', {
    photo_type: function (frm, cdt, cdn) {
        const row = locals[cdt][cdn];

        // Auto-translate photo type
        const translations = {
            'Front View': 'المنظر الأمامي',
            'Back View': 'المنظر الخلفي',
            'Left Side': 'الجانب الأيسر',
            'Right Side': 'الجانب الأيمن',
            'Top View': 'المنظر العلوي',
            'Bottom View': 'المنظر السفلي',
            'Close-up Detail': 'تفاصيل مقربة',
            'Defect/Damage': 'عيب/ضرر',
            'Serial Number': 'الرقم التسلسلي',
            'Before Cleaning': 'قبل التنظيف',
            'After Cleaning': 'بعد التنظيف',
            'Installation Point': 'نقطة التركيب',
            'Internal View': 'المنظر الداخلي',
            'Connections': 'التوصيلات',
            'Overall Condition': 'الحالة العامة'
        };

        if (translations[row.photo_type]) {
            frappe.model.set_value(cdt, cdn, 'photo_type_ar', translations[row.photo_type]);
        }

        // Auto-set defect flag for defect photos
        if (row.photo_type === 'Defect/Damage') {
            frappe.model.set_value(cdt, cdn, 'shows_defect', 1);
        }
    },

    shows_defect: function (frm, cdt, cdn) {
        const row = locals[cdt][cdn];

        if (row.shows_defect) {
            // Show defect fields
            frm.script_manager.trigger('defect_severity', cdt, cdn);
        }
    }
});

// Arabic Language Support
$(document).ready(function () {
    if (frappe.boot.lang === 'ar') {
        // Apply RTL styles for Arabic interface
        $('body').addClass('rtl-layout');

        // Format currency fields for Arabic locale
        $(document).on('focus', '[data-fieldtype=\"Currency\"]', function () {
            if ($(this).val()) {
                $(this).val($(this).val().replace(/\d/g, function (match) {
                    return '٠١٢٣٤٥٦٧٨٩'[parseInt(match)];
                }));
            }
        });
    }
}); 