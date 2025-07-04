// Copyright (c) 2024, Universal Workshop and contributors
// For license information, please see license.txt

frappe.ui.form.on('Part Quality Assessment', {
    refresh: function(frm) {
        frm.trigger('setup_arabic_fields');
        frm.trigger('setup_custom_buttons');
        frm.trigger('setup_field_dependencies');
        frm.trigger('calculate_assessment_score');
    },
    
    onload: function(frm) {
        // Set default values
        if (!frm.doc.assessment_date) {
            frm.set_value('assessment_date', frappe.datetime.get_today());
        }
        if (!frm.doc.inspector_employee) {
            frm.set_value('inspector_employee', frappe.session.user);
        }
        if (!frm.doc.assessment_status) {
            frm.set_value('assessment_status', 'Draft');
        }
    },
    
    setup_arabic_fields: function(frm) {
        // Set RTL direction for Arabic fields
        const arabic_fields = [
            'assessment_title_ar', 'part_name_ar', 'visual_notes_ar',
            'functional_notes_ar', 'grade_justification_ar',
            'grade_discrepancy_notes_ar', 'final_grade_rationale_ar',
            'market_notes_ar', 'compliance_notes_ar', 'approval_notes_ar',
            'quality_manager_notes_ar'
        ];
        
        arabic_fields.forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.attr('dir', 'rtl');
                frm.fields_dict[field].$input.css({
                    'text-align': 'right',
                    'font-family': 'Tahoma, Arial Unicode MS, sans-serif'
                });
            }
        });
        
        // Handle mixed content direction
        frm.fields_dict.assessment_title.$input.on('input', function() {
            const text = $(this).val();
            const direction = frm.get_text_direction(text);
            $(this).attr('dir', direction);
        });
    },
    
    setup_custom_buttons: function(frm) {
        // Add custom buttons based on status
        frm.page.clear_inner_toolbar();
        
        if (frm.doc.assessment_status === 'Completed' && !frm.doc.assessment_approved) {
            frm.add_custom_button(__('Approve Assessment'), function() {
                frm.trigger('approve_assessment');
            }, __('Actions'));
            
            frm.add_custom_button(__('Reject Assessment'), function() {
                frm.trigger('reject_assessment');
            }, __('Actions'));
        }
        
        if (frm.doc.name && frm.doc.final_grade) {
            frm.add_custom_button(__('Generate Report'), function() {
                frm.trigger('generate_assessment_report');
            }, __('Reports'));
        }
        
        if (frm.doc.name) {
            frm.add_custom_button(__('Print Assessment'), function() {
                frm.print_doc();
            }, __('Print'));
        }
        
        // Add photo upload helpers
        if (!frm.is_new()) {
            frm.add_custom_button(__('Upload Photos'), function() {
                frm.trigger('show_photo_upload_dialog');
            }, __('Photos'));
        }
    },
    
    setup_field_dependencies: function(frm) {
        // Show/hide fields based on selections
        frm.toggle_display('second_inspector', frm.doc.requires_second_opinion);
        frm.toggle_display('grade_discrepancy_notes', frm.doc.requires_second_opinion);
        frm.toggle_display('grade_discrepancy_notes_ar', frm.doc.requires_second_opinion);
        
        frm.toggle_display('estimated_refurbishment_cost', frm.doc.refurbishment_required);
        
        // Approval section visibility
        frm.toggle_display('approved_by', frm.doc.assessment_approved);
        frm.toggle_display('approval_date', frm.doc.assessment_approved);
        frm.toggle_display('approval_notes', frm.doc.assessment_approved);
        frm.toggle_display('approval_notes_ar', frm.doc.assessment_approved);
        
        // Quality manager review
        frm.toggle_display('quality_manager_notes', frm.doc.quality_manager_review);
        frm.toggle_display('quality_manager_notes_ar', frm.doc.quality_manager_review);
    },
    
    // Field event handlers
    part_category: function(frm) {
        frm.trigger('validate_inspector_qualification');
        frm.trigger('set_category_specific_requirements');
    },
    
    inspector_qualification: function(frm) {
        frm.trigger('set_default_confidence_level');
    },
    
    overall_visual_condition: function(frm) {
        frm.trigger('calculate_assessment_score');
        frm.trigger('suggest_grade_based_on_condition');
    },
    
    operational_status: function(frm) {
        frm.trigger('calculate_assessment_score');
    },
    
    safety_compliance: function(frm) {
        frm.trigger('calculate_assessment_score');
    },
    
    market_demand_assessment: function(frm) {
        frm.trigger('calculate_assessment_score');
        frm.trigger('suggest_time_to_sell');
    },
    
    suggested_selling_price: function(frm) {
        frm.trigger('validate_pricing_logic');
    },
    
    minimum_acceptable_price: function(frm) {
        frm.trigger('validate_pricing_logic');
    },
    
    requires_second_opinion: function(frm) {
        frm.trigger('setup_field_dependencies');
        if (frm.doc.requires_second_opinion) {
            frm.set_value('inspector_confidence_level', 'Low');
        }
    },
    
    refurbishment_required: function(frm) {
        frm.trigger('setup_field_dependencies');
    },
    
    assessment_approved: function(frm) {
        frm.trigger('setup_field_dependencies');
    },
    
    quality_manager_review: function(frm) {
        frm.trigger('setup_field_dependencies');
    },
    
    // Validation and calculation methods
    validate_inspector_qualification: function(frm) {
        const safety_critical_parts = ['Brakes', 'Suspension', 'Safety', 'Electronics'];
        
        if (safety_critical_parts.includes(frm.doc.part_category)) {
            if (!['Advanced', 'Certified Expert'].includes(frm.doc.inspector_qualification)) {
                frappe.msgprint({
                    title: __('Inspector Qualification Required'),
                    message: __('Safety critical parts require Advanced or Certified Expert inspector qualification.'),
                    indicator: 'orange'
                });
            }
        }
    },
    
    set_category_specific_requirements: function(frm) {
        // Set category-specific field requirements
        if (frm.doc.part_category === 'Electrical') {
            frm.set_df_property('electrical_continuity', 'reqd', 1);
        } else {
            frm.set_df_property('electrical_continuity', 'reqd', 0);
        }
        
        if (frm.doc.part_category === 'Engine') {
            if (!frm.doc.functional_test_performed) {
                frappe.msgprint({
                    title: __('Recommendation'),
                    message: __('Engine parts should have functional testing performed for accurate assessment.'),
                    indicator: 'blue'
                });
            }
        }
    },
    
    set_default_confidence_level: function(frm) {
        const confidence_mapping = {
            'Basic': 'Medium',
            'Intermediate': 'High',
            'Advanced': 'High',
            'Certified Expert': 'Very High'
        };
        
        if (frm.doc.inspector_qualification && !frm.doc.inspector_confidence_level) {
            frm.set_value('inspector_confidence_level', 
                confidence_mapping[frm.doc.inspector_qualification] || 'Medium');
        }
    },
    
    calculate_assessment_score: function(frm) {
        // Real-time assessment score calculation
        let score = 0;
        let weight_total = 0;
        
        // Visual assessment score (30% weight)
        const visual_scores = {
            'Excellent': 10, 'Very Good': 8, 'Good': 6,
            'Fair': 4, 'Poor': 2, 'Very Poor': 1
        };
        if (frm.doc.overall_visual_condition) {
            score += (visual_scores[frm.doc.overall_visual_condition] || 0) * 0.3;
            weight_total += 0.3;
        }
        
        // Functional assessment score (40% weight)
        if (frm.doc.functional_test_performed) {
            const functional_scores = {
                'Fully Functional': 10, 'Mostly Functional': 7,
                'Partially Functional': 4, 'Non-Functional': 1, 'Not Testable': 5
            };
            if (frm.doc.operational_status) {
                score += (functional_scores[frm.doc.operational_status] || 0) * 0.4;
                weight_total += 0.4;
            }
        }
        
        // Safety compliance score (20% weight)
        const safety_scores = {
            'Compliant': 10, 'Minor Issues': 6,
            'Major Issues': 3, 'Non-Compliant': 1, 'Unknown': 5
        };
        if (frm.doc.safety_compliance) {
            score += (safety_scores[frm.doc.safety_compliance] || 0) * 0.2;
            weight_total += 0.2;
        }
        
        // Market demand score (10% weight)
        const demand_scores = {
            'Very High': 10, 'High': 8, 'Medium': 6,
            'Low': 4, 'Very Low': 2
        };
        if (frm.doc.market_demand_assessment) {
            score += (demand_scores[frm.doc.market_demand_assessment] || 0) * 0.1;
            weight_total += 0.1;
        }
        
        // Calculate and display final score
        const final_score = weight_total > 0 ? Math.round((score / weight_total) * 100) / 100 : 0;
        
        // Display score in a custom field or message
        if (final_score > 0) {
            frm.dashboard.set_headline(__('Assessment Score: {0}/10', [final_score]));
        }
    },
    
    suggest_grade_based_on_condition: function(frm) {
        // Suggest preliminary grade based on visual condition
        const grade_suggestions = {
            'Excellent': 'A',
            'Very Good': 'B', 
            'Good': 'C',
            'Fair': 'D',
            'Poor': 'E',
            'Very Poor': 'F'
        };
        
        if (frm.doc.overall_visual_condition && !frm.doc.preliminary_grade) {
            const suggested_grade = grade_suggestions[frm.doc.overall_visual_condition];
            if (suggested_grade) {
                frappe.msgprint({
                    title: __('Grade Suggestion'),
                    message: __('Based on visual condition, suggested preliminary grade: {0}', [suggested_grade]),
                    indicator: 'blue'
                });
            }
        }
    },
    
    suggest_time_to_sell: function(frm) {
        // Suggest time to sell based on market demand
        const time_suggestions = {
            'Very High': '1-7 days',
            'High': '1-2 weeks',
            'Medium': '2-4 weeks',
            'Low': '1-3 months',
            'Very Low': '3-6 months'
        };
        
        if (frm.doc.market_demand_assessment && !frm.doc.time_to_sell_estimate) {
            const suggested_time = time_suggestions[frm.doc.market_demand_assessment];
            if (suggested_time) {
                frm.set_value('time_to_sell_estimate', suggested_time);
            }
        }
    },
    
    validate_pricing_logic: function(frm) {
        // Validate pricing logic
        if (frm.doc.suggested_selling_price && frm.doc.minimum_acceptable_price) {
            if (parseFloat(frm.doc.minimum_acceptable_price) > parseFloat(frm.doc.suggested_selling_price)) {
                frappe.msgprint({
                    title: __('Pricing Error'),
                    message: __('Minimum acceptable price cannot exceed suggested selling price.'),
                    indicator: 'red'
                });
                frm.set_value('minimum_acceptable_price', '');
            }
        }
        
        // Check refurbishment cost vs selling price
        if (frm.doc.refurbishment_required && frm.doc.estimated_refurbishment_cost && frm.doc.suggested_selling_price) {
            if (parseFloat(frm.doc.estimated_refurbishment_cost) > parseFloat(frm.doc.suggested_selling_price)) {
                frappe.msgprint({
                    title: __('Cost Warning'),
                    message: __('Refurbishment cost exceeds suggested selling price. Review pricing strategy.'),
                    indicator: 'orange'
                });
            }
        }
    },
    
    // Custom button actions
    approve_assessment: function(frm) {
        frappe.prompt({
            label: 'Approval Notes',
            fieldname: 'approval_notes',
            fieldtype: 'Text',
            reqd: 0
        }, function(values) {
            frappe.call({
                method: 'approve_assessment',
                doc: frm.doc,
                args: {
                    approver_notes: values.approval_notes
                },
                callback: function(r) {
                    if (r.message) {
                        frm.reload_doc();
                    }
                }
            });
        }, __('Approve Assessment'), __('Approve'));
    },
    
    reject_assessment: function(frm) {
        frappe.prompt({
            label: 'Rejection Notes',
            fieldname: 'rejection_notes',
            fieldtype: 'Text',
            reqd: 1,
            description: 'Please provide detailed reasons for rejection'
        }, function(values) {
            frappe.call({
                method: 'reject_assessment',
                doc: frm.doc,
                args: {
                    rejection_notes: values.rejection_notes
                },
                callback: function(r) {
                    if (r.message) {
                        frm.reload_doc();
                    }
                }
            });
        }, __('Reject Assessment'), __('Reject'));
    },
    
    generate_assessment_report: function(frm) {
        frappe.call({
            method: 'generate_assessment_report',
            doc: frm.doc,
            callback: function(r) {
                if (r.message) {
                    // Open report in new window or download
                    const report_data = r.message;
                    const report_window = window.open('', '_blank');
                    report_window.document.write(frm.format_assessment_report(report_data));
                    report_window.document.close();
                }
            }
        });
    },
    
    show_photo_upload_dialog: function(frm) {
        const photo_fields = [
            'overview_photo', 'detail_photo_1', 'detail_photo_2', 'detail_photo_3', 'detail_photo_4',
            'serial_number_photo', 'damage_photo_1', 'damage_photo_2', 'test_result_photo', 'packaging_photo'
        ];
        
        let dialog_fields = [];
        photo_fields.forEach(field => {
            const meta = frm.get_docfield(field);
            dialog_fields.push({
                label: meta.label,
                fieldname: field,
                fieldtype: 'Attach Image',
                default: frm.doc[field] || ''
            });
        });
        
        const dialog = new frappe.ui.Dialog({
            title: __('Upload Assessment Photos'),
            fields: dialog_fields,
            primary_action_label: __('Update Photos'),
            primary_action: function(values) {
                // Update photo fields
                Object.keys(values).forEach(field => {
                    if (values[field]) {
                        frm.set_value(field, values[field]);
                    }
                });
                dialog.hide();
                frm.save();
            }
        });
        
        dialog.show();
    },
    
    // Utility methods
    get_text_direction: function(text) {
        // Simple Arabic text detection for RTL direction
        const arabic_pattern = /[\u0600-\u06FF]/;
        const arabic_chars = (text.match(/[\u0600-\u06FF]/g) || []).length;
        const total_chars = text.replace(/\s/g, '').length;
        
        return (arabic_chars / total_chars > 0.3) ? 'rtl' : 'ltr';
    },
    
    format_assessment_report: function(report_data) {
        // Format assessment report for display/printing
        return `
            <html>
            <head>
                <title>Part Quality Assessment Report</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .header { text-align: center; margin-bottom: 30px; }
                    .section { margin-bottom: 20px; border: 1px solid #ddd; padding: 15px; }
                    .field { margin-bottom: 10px; }
                    .label { font-weight: bold; }
                    .photos { display: flex; flex-wrap: wrap; gap: 10px; }
                    .photo { max-width: 200px; max-height: 150px; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Part Quality Assessment Report</h1>
                    <h3>${report_data.assessment_title}</h3>
                    <p>Assessment ID: ${report_data.assessment_id}</p>
                </div>
                
                <div class="section">
                    <h3>Part Information</h3>
                    <div class="field"><span class="label">Name:</span> ${report_data.part_information.name}</div>
                    <div class="field"><span class="label">Category:</span> ${report_data.part_information.category}</div>
                    <div class="field"><span class="label">Vehicle:</span> ${report_data.part_information.vehicle_make} ${report_data.part_information.vehicle_model} ${report_data.part_information.vehicle_year}</div>
                </div>
                
                <div class="section">
                    <h3>Assessment Results</h3>
                    <div class="field"><span class="label">Final Grade:</span> ${report_data.grading.final_grade}</div>
                    <div class="field"><span class="label">Assessment Score:</span> ${report_data.assessment_score}/10</div>
                    <div class="field"><span class="label">Confidence Level:</span> ${report_data.grading.confidence_level}</div>
                    <div class="field"><span class="label">Justification:</span> ${report_data.grading.justification}</div>
                </div>
                
                <div class="section">
                    <h3>Market Analysis</h3>
                    <div class="field"><span class="label">Market Demand:</span> ${report_data.market_analysis.demand_assessment}</div>
                    <div class="field"><span class="label">Suggested Price:</span> OMR ${report_data.market_analysis.suggested_price}</div>
                    <div class="field"><span class="label">Time to Sell:</span> ${report_data.market_analysis.time_to_sell}</div>
                </div>
                
                <div class="section">
                    <h3>Photos</h3>
                    <div class="photos">
                        ${Object.values(report_data.photos).filter(photo => photo).map(photo => 
                            `<img src="${photo}" class="photo" alt="Assessment Photo">`
                        ).join('')}
                    </div>
                </div>
                
                <div style="margin-top: 40px; text-align: center; font-size: 12px; color: #666;">
                    Generated on: ${report_data.generated_on}<br>
                    Universal Workshop ERP - Part Quality Assessment System
                </div>
            </body>
            </html>
        `;
    }
});
