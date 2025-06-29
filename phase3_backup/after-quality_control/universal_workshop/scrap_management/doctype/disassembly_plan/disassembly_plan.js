// Disassembly Plan JavaScript - Arabic/RTL Enhancement with Workflow Management
// Enhanced UI for virtual dismantling planning system

frappe.ui.form.on('Disassembly Plan', {
    refresh: function (frm) {
        // Setup form enhancements
        frm.trigger('setup_arabic_fields');
        frm.trigger('setup_custom_buttons');
        frm.trigger('setup_plan_dashboard');
        frm.trigger('update_step_indicators');
    },

    setup_arabic_fields: function (frm) {
        // Configure Arabic fields with RTL support
        const arabic_fields = [
            'vehicle_title_ar', 'dismantling_notes', 'special_instructions',
            'safety_warnings'
        ];

        arabic_fields.forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.attr('dir', 'rtl');
                frm.fields_dict[field].$input.addClass('arabic-text');
            }
        });

        // Auto-detect direction for mixed content fields
        ['dismantling_notes', 'special_instructions'].forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.on('input', function () {
                    const text = $(this).val();
                    const direction = detect_text_direction(text);
                    $(this).attr('dir', direction);
                });
            }
        });
    },

    setup_custom_buttons: function (frm) {
        // Remove existing custom buttons
        frm.page.clear_inner_toolbar();

        if (frm.doc.status === "Draft") {
            frm.add_custom_button(__('Generate Optimal Plan'), function () {
                frm.trigger('generate_plan');
            }, __('Actions')).addClass('btn-primary');
        }

        if (frm.doc.status === "Planned") {
            frm.add_custom_button(__('Start Dismantling'), function () {
                frm.trigger('start_dismantling');
            }, __('Actions')).addClass('btn-success');
        }

        if (frm.doc.status === "In Progress") {
            frm.add_custom_button(__('View Mobile Checklist'), function () {
                frm.trigger('show_mobile_checklist');
            }, __('Actions'));

            frm.add_custom_button(__('Complete Current Step'), function () {
                frm.trigger('complete_current_step');
            }, __('Actions')).addClass('btn-success');
        }

        if (frm.doc.scrap_vehicle) {
            frm.add_custom_button(__('View Vehicle Details'), function () {
                frappe.set_route('Form', 'Scrap Vehicle', frm.doc.scrap_vehicle);
            }, __('Navigate'));
        }

        // Always available actions
        frm.add_custom_button(__('Profit Analysis'), function () {
            frm.trigger('show_profit_analysis');
        }, __('Reports'));
    },

    setup_plan_dashboard: function (frm) {
        // Create visual progress dashboard
        if (frm.doc.disassembly_steps && frm.doc.disassembly_steps.length > 0) {
            const dashboard_html = `
                <div class="plan-dashboard" style="margin: 15px 0; padding: 15px; border: 1px solid #d1d8dd; border-radius: 6px;">
                    <div class="row">
                        <div class="col-md-3">
                            <div class="progress-card">
                                <h6>${__('Progress')}</h6>
                                <div class="progress" style="height: 25px;">
                                    <div class="progress-bar ${frm.doc.progress_percentage > 75 ? 'bg-success' :
                    frm.doc.progress_percentage > 50 ? 'bg-info' :
                        frm.doc.progress_percentage > 25 ? 'bg-warning' : 'bg-danger'}" 
                                         style="width: ${frm.doc.progress_percentage || 0}%">
                                        ${(frm.doc.progress_percentage || 0).toFixed(1)}%
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <h6>${__('Steps')}</h6>
                            <p class="text-muted">${frm.doc.completed_steps || 0} / ${frm.doc.total_steps || 0}</p>
                        </div>
                        <div class="col-md-3">
                            <h6>${__('Est. Time')}</h6>
                            <p class="text-muted">${(frm.doc.estimated_total_time || 0).toFixed(1)}h</p>
                        </div>
                        <div class="col-md-3">
                            <h6>${__('Expected Profit')}</h6>
                            <p class="text-success">${format_currency(frm.doc.expected_profit || 0, 'OMR')}</p>
                        </div>
                    </div>
                </div>
            `;

            frm.layout.wrapper.find('.plan-dashboard').remove();
            frm.layout.wrapper.find('[data-fieldname="disassembly_steps_section"]').before(dashboard_html);
        }
    },

    update_step_indicators: function (frm) {
        // Add status indicators to step table
        if (frm.doc.disassembly_steps) {
            setTimeout(() => {
                frm.fields_dict.disassembly_steps.grid.wrapper.find('.grid-row').each(function (idx) {
                    const step = frm.doc.disassembly_steps[idx];
                    if (step) {
                        const $row = $(this);
                        const status_icon = get_status_icon(step.status);

                        // Add status indicator
                        $row.find('.row-index').prepend(`<span class="step-status">${status_icon}</span>`);

                        // Add safety level indicator
                        if (step.safety_level) {
                            const safety_color = get_safety_color(step.safety_level);
                            $row.css('border-left', `4px solid ${safety_color}`);
                        }
                    }
                });
            }, 500);
        }
    },

    generate_plan: function (frm) {
        if (!frm.doc.scrap_vehicle) {
            frappe.msgprint(__('Please select a Scrap Vehicle first'));
            return;
        }

        frappe.confirm(
            __('This will replace any existing steps. Continue?'),
            function () {
                frappe.call({
                    method: 'generate_optimal_plan',
                    doc: frm.doc,
                    callback: function (r) {
                        frm.reload_doc();
                        frm.trigger('setup_plan_dashboard');
                    }
                });
            }
        );
    },

    start_dismantling: function (frm) {
        frappe.confirm(
            __('Start the dismantling process? This will mark the first step as In Progress.'),
            function () {
                frappe.call({
                    method: 'start_dismantling',
                    doc: frm.doc,
                    callback: function (r) {
                        frm.reload_doc();
                    }
                });
            }
        );
    },

    complete_current_step: function (frm) {
        // Find current step in progress
        let current_step = null;
        if (frm.doc.disassembly_steps) {
            current_step = frm.doc.disassembly_steps.find(step => step.status === 'In Progress');
        }

        if (!current_step) {
            frappe.msgprint(__('No step is currently in progress'));
            return;
        }

        // Show completion dialog
        const dialog = new frappe.ui.Dialog({
            title: __('Complete Step {0}: {1}', [current_step.step_number, current_step.step_title]),
            fields: [
                {
                    fieldtype: 'Int',
                    fieldname: 'actual_time',
                    label: __('Actual Time (Minutes)'),
                    default: current_step.estimated_time_minutes
                },
                {
                    fieldtype: 'Text',
                    fieldname: 'notes',
                    label: __('Completion Notes')
                }
            ],
            primary_action: function () {
                const values = dialog.get_values();
                frappe.call({
                    method: 'complete_step',
                    doc: frm.doc,
                    args: {
                        step_number: current_step.step_number,
                        actual_time_minutes: values.actual_time,
                        technician_notes: values.notes
                    },
                    callback: function (r) {
                        dialog.hide();
                        frm.reload_doc();
                    }
                });
            },
            primary_action_label: __('Complete Step')
        });

        dialog.show();
    },

    show_mobile_checklist: function (frm) {
        frappe.call({
            method: 'get_mobile_checklist',
            doc: frm.doc,
            callback: function (r) {
                if (r.message) {
                    show_mobile_checklist_dialog(r.message);
                }
            }
        });
    },

    show_profit_analysis: function (frm) {
        if (!frm.doc.disassembly_steps || frm.doc.disassembly_steps.length === 0) {
            frappe.msgprint(__('No disassembly steps to analyze'));
            return;
        }

        // Calculate profit analysis data
        const analysis = calculate_profit_analysis(frm.doc);
        show_profit_analysis_dialog(analysis);
    },

    scrap_vehicle: function (frm) {
        if (frm.doc.scrap_vehicle) {
            // Auto-populate vehicle information
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Scrap Vehicle',
                    name: frm.doc.scrap_vehicle
                },
                callback: function (r) {
                    if (r.message) {
                        frm.set_value('vehicle_title', r.message.vehicle_title);
                        frm.set_value('vehicle_title_ar', r.message.vehicle_title_ar);
                    }
                }
            });
        }
    },

    extraction_strategy: function (frm) {
        if (frm.doc.extraction_strategy && frm.doc.scrap_vehicle && frm.doc.disassembly_steps.length === 0) {
            frappe.msgprint(__('Strategy changed. Generate optimal plan to apply new strategy.'));
        }
    }
});

// Child table events for Disassembly Steps
frappe.ui.form.on('Disassembly Step', {
    disassembly_steps_add: function (frm, cdt, cdn) {
        const row = locals[cdt][cdn];

        // Set default values for new step
        row.status = 'Pending';
        row.priority_level = 'Medium';
        row.extraction_method = 'Manual Removal';
        row.technician_skill_level = 'Intermediate';
        row.safety_level = 'Standard';

        // Auto-assign step number
        if (frm.doc.disassembly_steps) {
            row.step_number = frm.doc.disassembly_steps.length;
        }

        frm.refresh_field('disassembly_steps');
    },

    target_part: function (frm, cdt, cdn) {
        const row = locals[cdt][cdn];

        // Auto-suggest Arabic translation for common parts
        if (row.target_part && !row.target_part_ar) {
            const arabic_translation = get_part_arabic_translation(row.target_part);
            if (arabic_translation) {
                frappe.model.set_value(cdt, cdn, 'target_part_ar', arabic_translation);
            }
        }
    },

    estimated_part_value: function (frm, cdt, cdn) {
        calculate_step_totals(frm, cdt, cdn);
    },

    labor_cost: function (frm, cdt, cdn) {
        calculate_step_totals(frm, cdt, cdn);
    }
});

// Utility Functions
function detect_text_direction(text) {
    const arabic_chars = (text.match(/[\u0600-\u06FF]/g) || []).length;
    const total_chars = text.replace(/\s/g, '').length;
    return (arabic_chars / total_chars > 0.3) ? 'rtl' : 'ltr';
}

function get_status_icon(status) {
    const icons = {
        'Pending': '<i class="fa fa-clock-o text-muted"></i>',
        'In Progress': '<i class="fa fa-spinner fa-spin text-warning"></i>',
        'Completed': '<i class="fa fa-check-circle text-success"></i>',
        'Skipped': '<i class="fa fa-ban text-muted"></i>',
        'Failed': '<i class="fa fa-times-circle text-danger"></i>'
    };
    return icons[status] || icons['Pending'];
}

function get_safety_color(safety_level) {
    const colors = {
        'Standard': '#17a2b8',    // info blue
        'Elevated': '#ffc107',    // warning yellow
        'High-Risk': '#fd7e14',   // warning orange
        'Hazardous': '#dc3545'    // danger red
    };
    return colors[safety_level] || colors['Standard'];
}

function calculate_step_totals(frm, cdt, cdn) {
    const row = locals[cdt][cdn];

    // Calculate total step cost
    const part_value = row.estimated_part_value || 0;
    const labor_cost = row.labor_cost || 0;
    row.total_step_cost = part_value + labor_cost;

    // Calculate value ratio
    if (labor_cost > 0) {
        row.value_ratio = (part_value / labor_cost) * 100;
    }

    frm.refresh_field('disassembly_steps');

    // Trigger recalculation of main totals
    setTimeout(() => {
        frm.trigger('calculate_totals');
    }, 100);
}

function calculate_profit_analysis(doc) {
    const steps = doc.disassembly_steps || [];

    let total_value = 0;
    let total_labor = 0;
    let high_value_parts = [];
    let risky_steps = [];

    steps.forEach(step => {
        total_value += step.estimated_part_value || 0;
        total_labor += step.labor_cost || 0;

        if ((step.estimated_part_value || 0) > 100) {
            high_value_parts.push(step);
        }

        if (step.safety_level === 'High-Risk' || step.safety_level === 'Hazardous') {
            risky_steps.push(step);
        }
    });

    return {
        total_value,
        total_labor,
        expected_profit: doc.expected_profit || 0,
        profit_margin: doc.profit_margin_percentage || 0,
        high_value_parts,
        risky_steps,
        roi: doc.expected_profit ? (doc.expected_profit / (doc.total_estimated_cost || 1)) * 100 : 0
    };
}

function show_profit_analysis_dialog(analysis) {
    const dialog = new frappe.ui.Dialog({
        title: __('Profit Analysis'),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                options: `
                    <div class="profit-analysis">
                        <div class="row">
                            <div class="col-md-6">
                                <h5>${__('Financial Summary')}</h5>
                                <table class="table table-sm">
                                    <tr><td>${__('Total Parts Value')}</td><td class="text-right">${format_currency(analysis.total_value, 'OMR')}</td></tr>
                                    <tr><td>${__('Total Labor Cost')}</td><td class="text-right">${format_currency(analysis.total_labor, 'OMR')}</td></tr>
                                    <tr><td><strong>${__('Expected Profit')}</strong></td><td class="text-right text-success"><strong>${format_currency(analysis.expected_profit, 'OMR')}</strong></td></tr>
                                    <tr><td>${__('Profit Margin')}</td><td class="text-right">${analysis.profit_margin.toFixed(1)}%</td></tr>
                                    <tr><td>${__('ROI')}</td><td class="text-right">${analysis.roi.toFixed(1)}%</td></tr>
                                </table>
                            </div>
                            <div class="col-md-6">
                                <h5>${__('High Value Parts')} (>${format_currency(100, 'OMR')})</h5>
                                <ul class="list-unstyled">
                                    ${analysis.high_value_parts.map(part =>
                    `<li>• ${part.target_part} - ${format_currency(part.estimated_part_value, 'OMR')}</li>`
                ).join('')}
                                </ul>
                                
                                <h5 class="text-warning">${__('High Risk Steps')}</h5>
                                <ul class="list-unstyled">
                                    ${analysis.risky_steps.map(step =>
                    `<li>• ${step.target_part} (${step.safety_level})</li>`
                ).join('')}
                                </ul>
                            </div>
                        </div>
                    </div>
                `
            }
        ]
    });

    dialog.show();
}

function show_mobile_checklist_dialog(checklist) {
    const dialog = new frappe.ui.Dialog({
        title: __('Mobile Checklist - {0}', [checklist.vehicle]),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                options: `
                    <div class="mobile-checklist">
                        <div class="progress mb-3">
                            <div class="progress-bar bg-success" style="width: ${checklist.progress}%">
                                ${checklist.progress.toFixed(1)}% Complete
                            </div>
                        </div>
                        
                        <div class="checklist-steps">
                            ${checklist.steps.map(step => `
                                <div class="card mb-2 ${step.status === 'Completed' ? 'border-success' :
                        step.status === 'In Progress' ? 'border-warning' :
                            step.can_start ? 'border-info' : 'border-light'}">
                                    <div class="card-body">
                                        <div class="d-flex justify-content-between align-items-center">
                                            <h6 class="card-title mb-1">
                                                ${get_status_icon(step.status)} 
                                                ${step.number}. ${step.title}
                                                ${step.title_ar ? `<br><small class="text-muted" dir="rtl">${step.title_ar}</small>` : ''}
                                            </h6>
                                            <span class="badge badge-${get_safety_badge_color(step.safety_level)}">${step.safety_level}</span>
                                        </div>
                                        <p class="card-text small">
                                            <strong>${__('Part')}:</strong> ${step.part} ${step.part_ar ? `(${step.part_ar})` : ''}<br>
                                            <strong>${__('Est. Time')}:</strong> ${step.estimated_time} min<br>
                                            <strong>${__('Tools')}:</strong> ${step.required_tools}
                                        </p>
                                        ${step.safety_instructions ? `
                                            <div class="alert alert-warning alert-sm">
                                                <strong>⚠️ ${__('Safety')}:</strong> ${step.safety_instructions}
                                                ${step.safety_instructions_ar ? `<br><div dir="rtl">${step.safety_instructions_ar}</div>` : ''}
                                            </div>
                                        ` : ''}
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `
            }
        ]
    });

    dialog.show();
}

function get_safety_badge_color(safety_level) {
    const colors = {
        'Standard': 'info',
        'Elevated': 'warning',
        'High-Risk': 'warning',
        'Hazardous': 'danger'
    };
    return colors[safety_level] || 'secondary';
}

function get_part_arabic_translation(english_part) {
    const translations = {
        'Battery': 'البطارية',
        'Engine': 'المحرك',
        'Transmission': 'ناقل الحركة',
        'Airbag System': 'نظام الوسائد الهوائية',
        'Catalytic Converter': 'المحول الحفاز',
        'Alternator': 'المولد',
        'Starter Motor': 'محرك البداية',
        'Radiator': 'الرديتر',
        'Front Bumper': 'الصادم الأمامي',
        'Rear Bumper': 'الصادم الخلفي',
        'Headlights': 'المصابيح الأمامية',
        'Taillights': 'المصابيح الخلفية',
        'Wheels': 'العجلات',
        'Tires': 'الإطارات',
        'Seats': 'المقاعد',
        'Dashboard': 'لوحة القيادة',
        'Steering Wheel': 'عجلة القيادة',
        'Doors': 'الأبواب',
        'Windows': 'النوافذ',
        'Mirrors': 'المرايا'
    };

    return translations[english_part] || null;
}

// Auto-resize text areas for better UX
frappe.ui.form.on('Disassembly Plan', {
    onload: function (frm) {
        // Auto-resize text areas
        ['dismantling_notes', 'special_instructions', 'safety_warnings'].forEach(field => {
            if (frm.fields_dict[field] && frm.fields_dict[field].$input) {
                frm.fields_dict[field].$input.css('min-height', '80px');
            }
        });
    }
}); 