// Copyright (c) 2024, Universal Workshop and contributors
// For license information, please see license.txt

frappe.ui.form.on('Interactive Dashboard', {
    refresh: function(frm) {
        frm.trigger('setup_arabic_fields');
        frm.trigger('setup_custom_buttons');
        frm.trigger('setup_layout_preview');
        frm.trigger('setup_real_time_data');
    },

    setup_arabic_fields: function(frm) {
        // Set RTL direction for Arabic fields
        const arabic_fields = [
            'dashboard_name_ar', 'description_ar', 'category_ar'
        ];
        
        arabic_fields.forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.attr('dir', 'rtl');
                frm.fields_dict[field].$input.addClass('arabic-text');
            }
        });

        // Apply RTL layout if Arabic mode
        if (frappe.boot.lang === 'ar' || frm.doc.enable_rtl_mode) {
            frm.page.main.addClass('rtl-layout');
        }
    },

    setup_custom_buttons: function(frm) {
        if (frm.doc.name && frm.doc.status === 'Active') {
            // Dashboard Builder Button
            frm.add_custom_button(__('Dashboard Builder'), function() {
                frm.trigger('open_dashboard_builder');
            }, __('Tools'));

            // Preview Dashboard Button
            frm.add_custom_button(__('Preview Dashboard'), function() {
                frm.trigger('preview_dashboard');
            }, __('Tools'));

            // Export Dashboard Button
            frm.add_custom_button(__('Export Dashboard'), function() {
                frm.trigger('export_dashboard');
            }, __('Export'));

            // Performance Analysis
            frm.add_custom_button(__('Performance Analysis'), function() {
                frm.trigger('show_performance_analysis');
            }, __('Analytics'));
        }

        // Clone Dashboard Button
        if (frm.doc.name) {
            frm.add_custom_button(__('Clone Dashboard'), function() {
                frm.trigger('clone_dashboard');
            }, __('Actions'));
        }
    },

    open_dashboard_builder: function(frm) {
        const d = new frappe.ui.Dialog({
            title: __('Interactive Dashboard Builder'),
            size: 'extra-large',
            fields: [
                {
                    label: __('Dashboard Canvas'),
                    fieldname: 'dashboard_canvas',
                    fieldtype: 'HTML'
                }
            ],
            primary_action_label: __('Save Layout'),
            primary_action: function() {
                frappe.msgprint(__('Dashboard layout saved'));
                d.hide();
            }
        });

        d.$wrapper.find('[data-fieldname="dashboard_canvas"]').html(`
            <div class="dashboard-builder-container">
                <div class="widget-palette">
                    <h5>${__('Available Widgets')}</h5>
                    <div class="widget-list">
                        <div class="widget-item" data-type="chart">${__('Chart Widget')}</div>
                        <div class="widget-item" data-type="kpi">${__('KPI Widget')}</div>
                        <div class="widget-item" data-type="table">${__('Table Widget')}</div>
                        <div class="widget-item" data-type="gauge">${__('Gauge Widget')}</div>
                    </div>
                </div>
                <div class="dashboard-canvas" style="min-height: 600px; border: 2px dashed #ccc;">
                    <div class="canvas-grid" id="dashboard-grid"></div>
                </div>
            </div>
        `);

        d.show();
    },

    preview_dashboard: function(frm) {
        frappe.call({
            method: 'universal_workshop.reports_analytics.doctype.interactive_dashboard.interactive_dashboard.generate_dashboard_preview',
            args: {
                dashboard_name: frm.doc.name
            },
            callback: function(r) {
                if (r.message && r.message.success) {
                    frappe.msgprint(__('Dashboard preview generated successfully'));
                } else {
                    frappe.msgprint(__('Failed to generate dashboard preview'));
                }
            }
        });
    },

    show_performance_analysis: function(frm) {
        frappe.call({
            method: 'universal_workshop.reports_analytics.doctype.interactive_dashboard.interactive_dashboard.get_performance_metrics',
            args: {
                dashboard_name: frm.doc.name
            },
            callback: function(r) {
                if (r.message) {
                    const metrics = r.message;
                    
                    const d = new frappe.ui.Dialog({
                        title: __('Dashboard Performance Analysis'),
                        size: 'large',
                        fields: [
                            {
                                label: __('Performance Metrics'),
                                fieldname: 'metrics_html',
                                fieldtype: 'HTML'
                            }
                        ]
                    });

                    const metrics_html = `
                        <div class="performance-metrics">
                            <div class="metric-card">
                                <h6>${__('Load Time')}</h6>
                                <div class="metric-value">${metrics.load_time || 0}s</div>
                            </div>
                            <div class="metric-card">
                                <h6>${__('Memory Usage')}</h6>
                                <div class="metric-value">${metrics.memory_usage || 0}MB</div>
                            </div>
                            <div class="metric-card">
                                <h6>${__('Performance Score')}</h6>
                                <div class="metric-value">${metrics.performance_score || 0}/10</div>
                            </div>
                        </div>
                    `;

                    d.fields_dict.metrics_html.$wrapper.html(metrics_html);
                    d.show();
                }
            }
        });
    },

    export_dashboard: function(frm) {
        frappe.call({
            method: 'universal_workshop.reports_analytics.doctype.interactive_dashboard.interactive_dashboard.export_dashboard_config',
            args: {
                dashboard_name: frm.doc.name,
                include_data: true
            },
            callback: function(r) {
                if (r.message && r.message.download_url) {
                    window.open(r.message.download_url, '_blank');
                } else {
                    frappe.msgprint(__('Failed to export dashboard'));
                }
            }
        });
    },

    clone_dashboard: function(frm) {
        frappe.prompt([
            {
                label: __('New Dashboard Name'),
                fieldname: 'new_name',
                fieldtype: 'Data',
                reqd: 1
            },
            {
                label: __('New Dashboard Name (Arabic)'),
                fieldname: 'new_name_ar',
                fieldtype: 'Data'
            }
        ], function(data) {
            frappe.call({
                method: 'universal_workshop.reports_analytics.doctype.interactive_dashboard.interactive_dashboard.clone_dashboard',
                args: {
                    source_dashboard: frm.doc.name,
                    new_name: data.new_name,
                    new_name_ar: data.new_name_ar
                },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.msgprint(__('Dashboard cloned successfully'));
                        frappe.set_route('Form', 'Interactive Dashboard', r.message.new_dashboard_name);
                    }
                }
            });
        }, __('Clone Dashboard'), __('Clone'));
    },

    enable_realtime: function(frm) {
        if (frm.doc.enable_realtime) {
            frm.toggle_reqd('realtime_refresh_interval', true);
        } else {
            frm.toggle_reqd('realtime_refresh_interval', false);
        }
    },

    layout_type: function(frm) {
        const layout_type = frm.doc.layout_type;
        
        if (layout_type === 'Grid') {
            frm.toggle_display('grid_columns', true);
            frm.toggle_display('grid_gap', true);
        } else {
            frm.toggle_display('grid_columns', false);
            frm.toggle_display('grid_gap', false);
        }
    }
});

// Child table events
frappe.ui.form.on('Dashboard Widget Config', {
    widget_type: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row.widget_type) {
            frappe.call({
                method: 'universal_workshop.reports_analytics.doctype.interactive_dashboard.interactive_dashboard.get_widget_defaults',
                args: {
                    widget_type: row.widget_type
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.model.set_value(cdt, cdn, 'width', r.message.default_width);
                        frappe.model.set_value(cdt, cdn, 'height', r.message.default_height);
                    }
                }
            });
        }
    }
});
