// Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
// For license information, please see license.txt

frappe.ui.form.on('Environmental Compliance Record', {
    refresh: function(frm) {
        frm.trigger('setup_arabic_fields');
        frm.trigger('setup_custom_buttons');
        frm.trigger('setup_compliance_indicators');
        frm.trigger('setup_real_time_monitoring');
        frm.trigger('setup_field_dependencies');
        
        // Set up auto-refresh for monitoring status
        if (frm.doc.monitoring_frequency && !frm.is_new()) {
            frm.trigger('setup_auto_refresh');
        }
    },
    
    setup_arabic_fields: function(frm) {
        // Set RTL direction for Arabic fields
        const arabic_fields = [
            'remarks', 'corrective_actions', 'preventive_measures',
            'lessons_learned', 'recommendations', 'environmental_impact_assessment',
            'mitigation_measures', 'pollution_prevention_measures'
        ];
        
        arabic_fields.forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.attr('dir', 'rtl');
                frm.fields_dict[field].$input.css('text-align', 'right');
            }
        });
        
        // Auto-detect Arabic text and set direction
        arabic_fields.forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.on('input', function() {
                    const text = $(this).val();
                    const direction = detect_text_direction(text);
                    $(this).attr('dir', direction);
                });
            }
        });
    },
    
    setup_custom_buttons: function(frm) {
        if (!frm.is_new()) {
            // Compliance Summary Button
            frm.add_custom_button(__('Compliance Summary'), function() {
                frm.trigger('show_compliance_summary');
            }, __('Reports'));
            
            // Generate Report Button
            frm.add_custom_button(__('Generate Report'), function() {
                frm.trigger('generate_compliance_report');
            }, __('Reports'));
            
            // Create Follow-up Task Button
            if (frm.doc.status !== 'Compliant' && frm.doc.status !== 'Closed') {
                frm.add_custom_button(__('Create Follow-up Task'), function() {
                    frm.trigger('create_follow_up_task');
                });
            }
            
            // Refresh Monitoring Status Button
            frm.add_custom_button(__('Refresh Monitoring'), function() {
                frm.trigger('refresh_monitoring_status');
            }, __('Actions'));
            
            // Validate Compliance Button
            frm.add_custom_button(__('Validate Compliance'), function() {
                frm.trigger('validate_compliance_checklist');
            }, __('Actions'));
        }
        
        // Create from Scrap Vehicle Button
        if (frm.is_new()) {
            frm.add_custom_button(__('From Scrap Vehicle'), function() {
                frm.trigger('create_from_scrap_vehicle');
            }, __('Get Items From'));
        }
    },
    
    setup_compliance_indicators: function(frm) {
        if (!frm.is_new()) {
            // Create compliance percentage indicator
            const compliance_percentage = calculate_compliance_percentage(frm);
            
            // Add indicator to form
            const indicator_html = `
                <div class="compliance-indicator" style="margin: 10px 0;">
                    <div class="row">
                        <div class="col-md-6">
                            <div class="progress" style="height: 25px;">
                                <div class="progress-bar ${get_progress_bar_class(compliance_percentage)}" 
                                     role="progressbar" 
                                     style="width: ${compliance_percentage}%"
                                     aria-valuenow="${compliance_percentage}" 
                                     aria-valuemin="0" 
                                     aria-valuemax="100">
                                    ${compliance_percentage.toFixed(1)}% Compliant
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="compliance-status-badge">
                                <span class="badge badge-${get_status_badge_class(frm.doc.status)}">
                                    ${frm.doc.status || 'Draft'}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Insert after the title
            if (!frm.page.main.find('.compliance-indicator').length) {
                frm.page.main.find('.form-layout').prepend(indicator_html);
            }
        }
    },
    
    compliance_type: function(frm) {
        frm.trigger('toggle_fields_by_compliance_type');
        frm.trigger('set_default_values_by_type');
    },
    
    toggle_fields_by_compliance_type: function(frm) {
        const compliance_type = frm.doc.compliance_type;
        
        // Reset all field requirements
        frm.toggle_reqd('reference_document', false);
        frm.toggle_reqd('waste_type', false);
        frm.toggle_reqd('disposal_method', false);
        frm.toggle_reqd('disposal_contractor', false);
        
        // Set requirements based on compliance type
        if (compliance_type === 'Vehicle Processing') {
            frm.toggle_reqd('reference_document', true);
            frm.toggle_display('reference_doctype', true);
            frm.toggle_display('reference_document', true);
            
        } else if (compliance_type === 'Waste Disposal') {
            frm.toggle_reqd('waste_type', true);
            frm.toggle_reqd('disposal_method', true);
            frm.toggle_display('waste_quantity', true);
            
        } else if (compliance_type === 'Hazardous Material') {
            frm.toggle_reqd('waste_type', true);
            frm.toggle_reqd('disposal_contractor', true);
            frm.set_value('waste_type', 'Hazardous Waste');
        }
    },
    
    calculate_total_cost: function(frm) {
        const total = (frm.doc.compliance_cost || 0) +
                     (frm.doc.fine_amount || 0) +
                     (frm.doc.disposal_cost || 0) +
                     (frm.doc.certification_cost || 0);
        
        frm.set_value('total_compliance_cost', total);
    }
});

// Utility functions
function calculate_compliance_percentage(frm) {
    const checklist_fields = [
        'location_compliance', 'license_valid', 'documentation_complete',
        'waste_properly_segregated', 'hazardous_materials_handled',
        'spill_containment_in_place', 'pollution_prevention_active', 'staff_trained'
    ];
    
    const total_checks = checklist_fields.length;
    const passed_checks = checklist_fields.filter(field => frm.doc[field]).length;
    
    return (passed_checks / total_checks) * 100;
}

function get_progress_bar_class(percentage) {
    if (percentage >= 80) return 'progress-bar-success';
    if (percentage >= 60) return 'progress-bar-warning';
    return 'progress-bar-danger';
}

function get_status_badge_class(status) {
    const status_classes = {
        'Compliant': 'success',
        'Non-Compliant': 'danger',
        'Overdue': 'danger',
        'Pending Review': 'warning',
        'Under Investigation': 'info',
        'Draft': 'secondary',
        'Closed': 'dark'
    };
    return status_classes[status] || 'secondary';
}

function detect_text_direction(text) {
    // Simple Arabic text detection
    const arabicPattern = /[\u0600-\u06FF]/;
    const arabicChars = (text.match(/[\u0600-\u06FF]/g) || []).length;
    const totalChars = text.replace(/\s/g, '').length;
    
    return (arabicChars / totalChars > 0.3) ? 'rtl' : 'ltr';
}
