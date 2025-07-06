// Copyright (c) 2025, Universal Workshop ERP and contributors
// For license information, please see license.txt

frappe.ui.form.on('Profit Analysis Dashboard', {
    refresh: function(frm) {
        frm.trigger('setup_dashboard_interface');
        frm.trigger('setup_arabic_localization');
        frm.trigger('setup_custom_buttons');
        frm.trigger('setup_realtime_updates');
        frm.trigger('load_dashboard_charts');
    },
    
    onload: function(frm) {
        frm.trigger('setup_field_dependencies');
        frm.trigger('setup_auto_refresh');
        frm.trigger('initialize_dashboard_data');
    },
    
    setup_dashboard_interface: function(frm) {
        // Set up the main dashboard interface
        if (frm.doc.status === 'Generated') {
            frm.trigger('render_dashboard_summary');
            frm.trigger('setup_metric_cards');
            frm.trigger('setup_interactive_charts');
        }
        
        // Hide/show fields based on status
        if (frm.doc.status === 'Draft') {
            frm.set_df_property('vehicle_analysis_tab', 'hidden', 1);
            frm.set_df_property('parts_analysis_tab', 'hidden', 1);
            frm.set_df_property('marketplace_analysis_tab', 'hidden', 1);
            frm.set_df_property('financial_metrics_tab', 'hidden', 1);
        } else {
            frm.set_df_property('vehicle_analysis_tab', 'hidden', 0);
            frm.set_df_property('parts_analysis_tab', 'hidden', 0);
            frm.set_df_property('marketplace_analysis_tab', 'hidden', 0);
            frm.set_df_property('financial_metrics_tab', 'hidden', 0);
        }
    },
    
    setup_arabic_localization: function(frm) {
        // Setup Arabic RTL support
        if (frappe.boot.lang === 'ar' || frm.doc.rtl_layout_enabled) {
            frm.wrapper.addClass('rtl-layout');
            
            // Set RTL direction for Arabic fields
            const arabic_fields = ['dashboard_name_ar', 'dashboard_title_ar', 
                                 'analysis_notes_ar', 'performance_summary_ar', 'recommendations_ar'];
            
            arabic_fields.forEach(field => {
                if (frm.fields_dict[field]) {
                    frm.fields_dict[field].$input.attr('dir', 'rtl');
                    frm.fields_dict[field].$input.css('text-align', 'right');
                    frm.fields_dict[field].$input.addClass('arabic-text');
                }
            });
            
            // Apply Arabic number formatting
            frm.trigger('apply_arabic_number_formatting');
        }
    },
    
    setup_custom_buttons: function(frm) {
        // Clear existing custom buttons
        frm.clear_custom_buttons();
        
        if (frm.doc.status === 'Generated') {
            // Refresh Dashboard button
            frm.add_custom_button(__('Refresh Dashboard'), function() {
                frm.trigger('refresh_dashboard_data');
            }, __('Actions'));
            
            // Export buttons
            frm.add_custom_button(__('Export to PDF'), function() {
                frm.trigger('export_dashboard', 'PDF');
            }, __('Export'));
            
            frm.add_custom_button(__('Export to Excel'), function() {
                frm.trigger('export_dashboard', 'Excel');
            }, __('Export'));
            
            // Set primary button
            frm.page.set_primary_action(__('Refresh Data'), function() {
                frm.trigger('refresh_dashboard_data');
            });
        }
        
        if (frm.doc.status === 'Draft') {
            frm.page.set_primary_action(__('Generate Dashboard'), function() {
                frm.save().then(() => {
                    frappe.msgprint(__('Dashboard generated successfully'));
                    frm.reload_doc();
                });
            });
        }
    }
});
