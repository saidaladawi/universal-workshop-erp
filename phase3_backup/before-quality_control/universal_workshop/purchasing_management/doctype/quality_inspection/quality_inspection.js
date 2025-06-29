frappe.ui.form.on('Quality Inspection', {
    refresh: function (frm) {
        frm.trigger('setup_arabic_fields');
        frm.trigger('setup_custom_buttons');
        frm.trigger('setup_calculations');
    },

    setup_arabic_fields: function (frm) {
        // Set RTL direction for Arabic fields
        const arabic_fields = [
            'item_name_ar', 'supplier_name_ar', 'inspector_name_ar',
            'inspection_remarks_ar'
        ];

        arabic_fields.forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.attr('dir', 'rtl');
                frm.fields_dict[field].$input.css('text-align', 'right');
            }
        });

        // Apply RTL layout if Arabic language
        if (frappe.boot.lang === 'ar') {
            frm.page.main.addClass('rtl-layout');
        }
    },

    setup_custom_buttons: function (frm) {
        if (frm.doc.docstatus === 1) {
            // Add button to create corrective action
            if (frm.doc.corrective_action_required) {
                frm.add_custom_button(__('Create Corrective Action'), function () {
                    frm.trigger('create_corrective_action');
                }, __('Actions'));
            }

            // Add button to view supplier scorecard
            if (frm.doc.supplier) {
                frm.add_custom_button(__('View Supplier Scorecard'), function () {
                    frappe.set_route('Form', 'Supplier Scorecard', frm.doc.supplier + '-' + new Date().getFullYear());
                }, __('View'));
            }
        }

        // Add calculate quality score button
        if (frm.doc.docstatus === 0) {
            frm.add_custom_button(__('Calculate Quality Score'), function () {
                frm.trigger('calculate_quality_metrics');
            });
        }
    },

    setup_calculations: function (frm) {
        // Auto-calculate quality metrics when criteria change
        frm.trigger('calculate_quality_metrics');
    },

    item_code: function (frm) {
        if (frm.doc.item_code) {
            // Fetch item details
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Item',
                    name: frm.doc.item_code
                },
                callback: function (r) {
                    if (r.message) {
                        frm.set_value('item_name', r.message.item_name);
                        if (r.message.item_name_ar) {
                            frm.set_value('item_name_ar', r.message.item_name_ar);
                        }
                    }
                }
            });

            // Load quality inspection template if available
            frm.trigger('load_quality_template');
        }
    },

    supplier: function (frm) {
        if (frm.doc.supplier) {
            // Fetch supplier details
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Supplier',
                    name: frm.doc.supplier
                },
                callback: function (r) {
                    if (r.message) {
                        frm.set_value('supplier_name', r.message.supplier_name);
                        if (r.message.supplier_name_ar) {
                            frm.set_value('supplier_name_ar', r.message.supplier_name_ar);
                        }
                    }
                }
            });
        }
    },

    inspected_by: function (frm) {
        if (frm.doc.inspected_by) {
            // Fetch inspector details
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Employee',
                    name: frm.doc.inspected_by
                },
                callback: function (r) {
                    if (r.message) {
                        frm.set_value('inspector_name', r.message.employee_name);
                        if (r.message.employee_name_ar) {
                            frm.set_value('inspector_name_ar', r.message.employee_name_ar);
                        }
                    }
                }
            });
        }
    },

    quality_inspection_template: function (frm) {
        if (frm.doc.quality_inspection_template) {
            frm.trigger('load_template_criteria');
        }
    },

    load_quality_template: function (frm) {
        if (frm.doc.item_code) {
            frappe.call({
                method: 'universal_workshop.purchasing_management.doctype.quality_inspection.quality_inspection.get_quality_inspection_template',
                args: {
                    item_code: frm.doc.item_code
                },
                callback: function (r) {
                    if (r.message) {
                        frm.set_value('quality_inspection_template', r.message.template_name);
                        frm.set_value('inspection_criteria', r.message.criteria);
                        frm.refresh_field('inspection_criteria');
                    }
                }
            });
        }
    },

    load_template_criteria: function (frm) {
        if (frm.doc.quality_inspection_template) {
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Quality Inspection Template',
                    name: frm.doc.quality_inspection_template
                },
                callback: function (r) {
                    if (r.message && r.message.inspection_criteria) {
                        frm.set_value('inspection_criteria', r.message.inspection_criteria);
                        frm.refresh_field('inspection_criteria');
                    }
                }
            });
        }
    },

    calculate_quality_metrics: function (frm) {
        if (!frm.doc.inspection_criteria || frm.doc.inspection_criteria.length === 0) {
            return;
        }

        let total_criteria = frm.doc.inspection_criteria.length;
        let passed_criteria = 0;
        let total_score = 0;
        let max_score = 0;
        let defects_found = 0;

        frm.doc.inspection_criteria.forEach(function (criterion) {
            if (criterion.max_value) {
                max_score += flt(criterion.max_value);
            }
            if (criterion.actual_value) {
                total_score += flt(criterion.actual_value);
            }
            if (criterion.result === 'Pass') {
                passed_criteria += 1;
            } else if (criterion.result === 'Fail') {
                defects_found += 1;
            }
        });

        // Calculate pass percentage
        let pass_percentage = total_criteria > 0 ? (passed_criteria / total_criteria) * 100 : 0;

        // Calculate quality score (0-100)
        let quality_score = max_score > 0 ? (total_score / max_score) * 100 : 0;

        // Set calculated values
        frm.set_value('pass_percentage', pass_percentage);
        frm.set_value('quality_score', quality_score);
        frm.set_value('defects_found', defects_found);

        // Determine overall result
        let overall_result = 'Pass';
        let corrective_action_required = 0;

        if (pass_percentage >= 95) {
            overall_result = 'Pass';
        } else if (pass_percentage >= 70) {
            overall_result = 'Partial Pass';
            corrective_action_required = 1;
        } else {
            overall_result = 'Fail';
            corrective_action_required = 1;
        }

        frm.set_value('overall_result', overall_result);
        frm.set_value('corrective_action_required', corrective_action_required);

        // Update inspection status
        if (overall_result === 'Fail') {
            frm.set_value('inspection_status', 'Rejected');
        } else {
            frm.set_value('inspection_status', 'Completed');
        }

        frm.refresh_fields();
    },

    create_corrective_action: function (frm) {
        frappe.new_doc('Corrective Action', {
            quality_inspection: frm.doc.name,
            supplier: frm.doc.supplier,
            item_code: frm.doc.item_code,
            issue_description: `Quality inspection failed for ${frm.doc.item_name}`,
            priority: frm.doc.overall_result === 'Fail' ? 'High' : 'Medium',
            assigned_to: frm.doc.inspected_by
        });
    },

    before_submit: function (frm) {
        // Validate that all criteria have results
        if (frm.doc.inspection_criteria) {
            let incomplete_criteria = frm.doc.inspection_criteria.filter(function (criterion) {
                return !criterion.result || criterion.result === '';
            });

            if (incomplete_criteria.length > 0) {
                frappe.throw(__('Please complete all inspection criteria before submitting'));
            }
        }

        // Ensure quality metrics are calculated
        frm.trigger('calculate_quality_metrics');
    }
});

// Child table events for Quality Inspection Criteria
frappe.ui.form.on('Quality Inspection Criteria', {
    actual_value: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        // Auto-calculate result based on actual value
        if (row.actual_value) {
            let actual = flt(row.actual_value);
            let result = 'Pass';

            // Check against min/max values
            if (row.min_value && actual < flt(row.min_value)) {
                result = 'Fail';
            } else if (row.max_value && actual > flt(row.max_value)) {
                result = 'Fail';
            } else if (row.target_value && row.tolerance) {
                // Check tolerance
                let target = flt(row.target_value);
                let tolerance_value = (target * flt(row.tolerance)) / 100;

                if (Math.abs(actual - target) > tolerance_value) {
                    result = 'Fail';
                }
            }

            frappe.model.set_value(cdt, cdn, 'result', result);
        }

        // Recalculate overall quality metrics
        frm.trigger('calculate_quality_metrics');
    },

    result: function (frm, cdt, cdn) {
        // Recalculate when result is manually changed
        frm.trigger('calculate_quality_metrics');
    },

    inspection_criteria_remove: function (frm) {
        // Recalculate when criteria is removed
        frm.trigger('calculate_quality_metrics');
    }
});

// Custom formatters for Arabic numerals
if (frappe.boot.lang === 'ar') {
    frappe.utils.format_arabic_numbers = function (value) {
        const arabic_numerals = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];
        return value.toString().replace(/[0-9]/g, function (digit) {
            return arabic_numerals[parseInt(digit)];
        });
    };
} 