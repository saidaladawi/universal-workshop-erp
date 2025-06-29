// Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
// For license information, please see license.txt

frappe.ui.form.on('Custom Report Builder', {
    refresh: function(frm) {
        frm.trigger('setup_custom_buttons');
        frm.trigger('setup_arabic_fields');
        frm.trigger('setup_drag_drop_interface');
        frm.trigger('setup_chart_preview');
        frm.trigger('load_external_libraries');
    },
    
    setup_custom_buttons: function(frm) {
        // Report Builder Interface button
        frm.add_custom_button(__('Open Report Builder'), function() {
            frm.trigger('open_report_builder');
        }, __('Builder'));
        
        // Preview Report button
        if (frm.doc.status === 'Active' && frm.doc.primary_data_source) {
            frm.add_custom_button(__('Preview Report'), function() {
                frm.trigger('preview_report');
            }, __('Actions'));
        }
        
        // Test Query button
        if (frm.doc.sql_query && !frm.doc.sql_query.startsWith('--')) {
            frm.add_custom_button(__('Test Query'), function() {
                frm.trigger('test_query');
            }, __('Actions'));
        }
        
        // Export buttons
        if (frm.doc.status === 'Active') {
            frm.add_custom_button(__('Export Excel'), function() {
                frm.trigger('export_report', 'excel');
            }, __('Export'));
            
            frm.add_custom_button(__('Export PDF'), function() {
                frm.trigger('export_report', 'pdf');
            }, __('Export'));
        }
        
        // Template buttons
        if (frm.is_new()) {
            frm.add_custom_button(__('Load Template'), function() {
                frm.trigger('load_template');
            }, __('Templates'));
        }
    },
    
    setup_arabic_fields: function(frm) {
        // Set RTL direction for Arabic fields
        const arabic_fields = ['report_name_ar', 'description_ar'];
        
        arabic_fields.forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.attr('dir', 'rtl');
                frm.fields_dict[field].$input.css({
                    'text-align': 'right',
                    'font-family': 'Noto Sans Arabic, Tahoma, Arial'
                });
            }
        });
        
        // Auto-detect RTL mode
        if (frappe.boot.lang === 'ar' && !frm.doc.rtl_mode) {
            frm.set_value('rtl_mode', 1);
            frm.set_value('language_direction', 'RTL');
            frm.set_value('arabic_font_family', 'Noto Sans Arabic');
        }
    },
    
    setup_drag_drop_interface: function(frm) {
        // Add drag-drop interface container
        if (!frm.doc.__islocal) {
            frm.trigger('create_drag_drop_container');
        }
    },
    
    create_drag_drop_container: function(frm) {
        // Create drag-drop interface HTML
        const container_html = `
            <div class="report-builder-container" style="display: none;">
                <div class="row">
                    <div class="col-md-3">
                        <div class="fields-panel">
                            <h5>${__('Available Fields')}</h5>
                            <div class="fields-list" id="fields-list">
                                <div class="loading">${__('Loading fields...')}</div>
                            </div>
                        </div>
                        <div class="chart-options-panel mt-3">
                            <h5>${__('Chart Options')}</h5>
                            <div class="chart-types">
                                <div class="chart-type" data-type="Table">${__('Table')}</div>
                                <div class="chart-type" data-type="Bar Chart">${__('Bar Chart')}</div>
                                <div class="chart-type" data-type="Line Chart">${__('Line Chart')}</div>
                                <div class="chart-type" data-type="Pie Chart">${__('Pie Chart')}</div>
                                <div class="chart-type" data-type="KPI Card">${__('KPI Card')}</div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="canvas-panel">
                            <h5>${__('Report Canvas')}</h5>
                            <div class="report-canvas" id="report-canvas">
                                <div class="canvas-placeholder">
                                    ${__('Drag fields here to build your report')}
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="preview-panel">
                            <h5>${__('Preview')}</h5>
                            <div class="chart-preview" id="chart-preview">
                                <div class="preview-placeholder">
                                    ${__('Chart preview will appear here')}
                                </div>
                            </div>
                        </div>
                        <div class="filters-panel mt-3">
                            <h5>${__('Filters')}</h5>
                            <div class="filters-container" id="filters-container">
                                <button class="btn btn-sm btn-primary add-filter">
                                    ${__('Add Filter')}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Add to form
        frm.fields_dict.field_configuration.$wrapper.after(container_html);
        
        // Load fields when data source changes
        if (frm.doc.primary_data_source) {
            frm.trigger('load_available_fields');
        }
        
        // Setup drag and drop
        frm.trigger('setup_sortable');
    },
    
    setup_sortable: function(frm) {
        // Setup Sortable.js for drag and drop
        if (typeof Sortable !== 'undefined') {
            // Fields list sortable
            const fieldsList = document.getElementById('fields-list');
            if (fieldsList) {
                new Sortable(fieldsList, {
                    group: {
                        name: 'fields',
                        pull: 'clone',
                        put: false
                    },
                    sort: false,
                    onEnd: function(evt) {
                        frm.trigger('handle_field_drop', evt);
                    }
                });
            }
            
            // Canvas sortable
            const canvas = document.getElementById('report-canvas');
            if (canvas) {
                new Sortable(canvas, {
                    group: 'fields',
                    onAdd: function(evt) {
                        frm.trigger('handle_field_add', evt);
                    },
                    onUpdate: function(evt) {
                        frm.trigger('update_field_configuration');
                    }
                });
            }
        } else {
            // Load Sortable.js if not available
            frappe.require('/assets/frappe/js/lib/sortable.min.js').then(() => {
                frm.trigger('setup_sortable');
            });
        }
    },
    
    load_available_fields: function(frm) {
        if (!frm.doc.primary_data_source) return;
        
        frappe.call({
            method: 'universal_workshop.reports_analytics.doctype.custom_report_builder.custom_report_builder.get_available_fields',
            args: {
                data_source: frm.doc.primary_data_source
            },
            callback: function(r) {
                if (r.message && r.message.success) {
                    frm.trigger('render_fields_list', r.message.fields);
                } else {
                    frappe.msgprint(__('Failed to load fields: {0}', [r.message.error || 'Unknown error']));
                }
            }
        });
    },
    
    render_fields_list: function(frm, fields) {
        const fieldsList = document.getElementById('fields-list');
        if (!fieldsList) return;
        
        let html = '';
        fields.forEach(field => {
            const icon = frm.trigger('get_field_icon', field.type);
            html += `
                <div class="field-item" data-field="${field.name}" data-type="${field.type}">
                    <i class="${icon}"></i>
                    <span class="field-label">${field.label}</span>
                    <span class="field-type">(${field.type})</span>
                </div>
            `;
        });
        
        fieldsList.innerHTML = html;
        
        // Apply RTL if needed
        if (frm.doc.rtl_mode) {
            fieldsList.style.direction = 'rtl';
            fieldsList.style.textAlign = 'right';
        }
    },
    
    get_field_icon: function(frm, field_type) {
        const icons = {
            'Data': 'fa fa-font',
            'Int': 'fa fa-hashtag',
            'Float': 'fa fa-calculator',
            'Currency': 'fa fa-money',
            'Date': 'fa fa-calendar',
            'Datetime': 'fa fa-clock-o',
            'Check': 'fa fa-check-square',
            'Select': 'fa fa-list',
            'Link': 'fa fa-link',
            'Text': 'fa fa-align-left'
        };
        return icons[field_type] || 'fa fa-question';
    },
    
    handle_field_add: function(frm, evt) {
        const fieldName = evt.item.dataset.field;
        const fieldType = evt.item.dataset.type;
        
        // Update field configuration
        let config = {};
        try {
            config = frm.doc.field_configuration ? JSON.parse(frm.doc.field_configuration) : {};
        } catch (e) {
            config = {};
        }
        
        if (!config.fields) config.fields = [];
        
        // Add field if not already present
        if (!config.fields.find(f => f.name === fieldName)) {
            config.fields.push({
                name: fieldName,
                type: fieldType,
                selected: true,
                position: config.fields.length
            });
            
            frm.set_value('field_configuration', JSON.stringify(config, null, 2));
            
            // Update preview
            frm.trigger('update_chart_preview');
        }
        
        // Style the dropped item
        evt.item.classList.add('field-selected');
    },
    
    setup_chart_preview: function(frm) {
        // Setup chart preview area
        frm.chart_preview_container = document.getElementById('chart-preview');
    },
    
    load_external_libraries: function(frm) {
        // Load Chart.js if selected
        if (frm.doc.chart_library === 'Chart.js' && typeof Chart === 'undefined') {
            frappe.require([
                '/assets/frappe/js/lib/chart.min.js'
            ]).then(() => {
                console.log('Chart.js loaded');
            });
        }
        
        // Load D3.js if selected
        if (frm.doc.chart_library === 'D3.js' && typeof d3 === 'undefined') {
            frappe.require([
                '/assets/frappe/js/lib/d3.min.js'
            ]).then(() => {
                console.log('D3.js loaded');
            });
        }
    },
    
    open_report_builder: function(frm) {
        // Toggle report builder interface
        const container = document.querySelector('.report-builder-container');
        if (container) {
            container.style.display = container.style.display === 'none' ? 'block' : 'none';
            
            if (container.style.display === 'block') {
                frm.trigger('load_available_fields');
            }
        }
    },
    
    preview_report: function(frm) {
        frappe.call({
            method: 'execute_report',
            doc: frm.doc,
            args: {
                limit: 100
            },
            callback: function(r) {
                if (r.message && r.message.success) {
                    frm.trigger('show_report_preview', r.message);
                } else {
                    frappe.msgprint({
                        title: __('Preview Failed'),
                        message: r.message ? r.message.error : __('Unknown error'),
                        indicator: 'red'
                    });
                }
            }
        });
    },
    
    show_report_preview: function(frm, result) {
        const dialog = new frappe.ui.Dialog({
            title: __('Report Preview'),
            size: 'extra-large',
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'preview_html',
                    options: frm.trigger('format_preview_html', result)
                }
            ]
        });
        dialog.show();
    },
    
    format_preview_html: function(frm, result) {
        let html = `
            <div class="report-preview">
                <p><strong>${__('Execution Time')}:</strong> ${result.execution_time || 0}s</p>
                <p><strong>${__('Row Count')}:</strong> ${result.row_count}</p>
                <hr>
        `;
        
        if (result.data && result.data.length > 0) {
            // Create table
            const headers = Object.keys(result.data[0]);
            
            html += '<table class="table table-bordered">';
            html += '<thead><tr>';
            headers.forEach(header => {
                html += `<th>${header}</th>`;
            });
            html += '</tr></thead><tbody>';
            
            // Show first 10 rows
            result.data.slice(0, 10).forEach(row => {
                html += '<tr>';
                headers.forEach(header => {
                    html += `<td>${row[header] || ''}</td>`;
                });
                html += '</tr>';
            });
            
            html += '</tbody></table>';
            
            if (result.data.length > 10) {
                html += `<p><em>${__('Showing first 10 of {0} rows', [result.data.length])}</em></p>`;
            }
        } else {
            html += '<p><em>' + __('No data found') + '</em></p>';
        }
        
        html += '</div>';
        return html;
    },
    
    test_query: function(frm) {
        frappe.call({
            method: 'test_query',
            doc: frm.doc,
            args: {
                limit: 10
            },
            callback: function(r) {
                if (r.message && r.message.success) {
                    frappe.msgprint({
                        title: __('Query Test Successful'),
                        message: __('Query executed successfully. Found {0} rows.', [r.message.row_count]),
                        indicator: 'green'
                    });
                } else {
                    frappe.msgprint({
                        title: __('Query Test Failed'),
                        message: r.message ? r.message.error : __('Unknown error'),
                        indicator: 'red'
                    });
                }
            }
        });
    },
    
    export_report: function(frm, format) {
        frappe.call({
            method: 'export_report',
            doc: frm.doc,
            args: {
                format_type: format
            },
            callback: function(r) {
                if (r.message && r.message.success) {
                    frappe.msgprint({
                        title: __('Export Successful'),
                        message: r.message.message,
                        indicator: 'green'
                    });
                } else {
                    frappe.msgprint({
                        title: __('Export Failed'),
                        message: r.message ? r.message.error : __('Unknown error'),
                        indicator: 'red'
                    });
                }
            }
        });
    },
    
    load_template: function(frm) {
        frappe.call({
            method: 'universal_workshop.reports_analytics.doctype.custom_report_builder.custom_report_builder.get_report_templates',
            callback: function(r) {
                if (r.message && r.message.success) {
                    frm.trigger('show_template_dialog', r.message.templates);
                }
            }
        });
    },
    
    show_template_dialog: function(frm, templates) {
        const dialog = new frappe.ui.Dialog({
            title: __('Select Report Template'),
            fields: [
                {
                    fieldtype: 'Select',
                    fieldname: 'template',
                    label: __('Template'),
                    options: templates.map(t => t.name).join('\n'),
                    reqd: 1
                },
                {
                    fieldtype: 'Data',
                    fieldname: 'report_name',
                    label: __('Report Name'),
                    reqd: 1
                },
                {
                    fieldtype: 'Data',
                    fieldname: 'report_name_ar',
                    label: __('Arabic Report Name'),
                    reqd: 1
                }
            ],
            primary_action_label: __('Create Report'),
            primary_action: function() {
                const values = dialog.get_values();
                
                const template = templates.find(t => t.name === values.template);
                if (template) {
                    // Set template values
                    frm.set_value('report_name', values.report_name);
                    frm.set_value('report_name_ar', values.report_name_ar);
                    frm.set_value('report_category', template.category);
                    frm.set_value('chart_type', template.chart_type);
                    frm.set_value('description', template.description);
                    
                    dialog.hide();
                    frappe.msgprint(__('Template loaded successfully'));
                }
            }
        });
        
        dialog.show();
    },
    
    update_chart_preview: function(frm) {
        if (!frm.doc.primary_data_source || !frm.chart_preview_container) return;
        
        frappe.call({
            method: 'get_chart_data',
            doc: frm.doc,
            callback: function(r) {
                if (r.message && r.message.success) {
                    frm.trigger('render_chart_preview', r.message.chart_data);
                }
            }
        });
    },
    
    render_chart_preview: function(frm, chart_data) {
        if (!frm.chart_preview_container) return;
        
        // Clear previous chart
        frm.chart_preview_container.innerHTML = '<canvas id="preview-chart"></canvas>';
        
        const canvas = document.getElementById('preview-chart');
        if (!canvas || typeof Chart === 'undefined') return;
        
        // Create chart based on type
        const ctx = canvas.getContext('2d');
        
        let config = {
            type: chart_data.type || 'bar',
            data: chart_data,
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top'
                    }
                }
            }
        };
        
        // Apply RTL adjustments
        if (frm.doc.rtl_mode) {
            config.options.plugins.legend.rtl = true;
            config.options.plugins.legend.textDirection = 'rtl';
        }
        
        new Chart(ctx, config);
    },
    
    // Field change handlers
    primary_data_source: function(frm) {
        if (frm.doc.primary_data_source) {
            frm.trigger('load_available_fields');
        }
    },
    
    rtl_mode: function(frm) {
        if (frm.doc.rtl_mode) {
            frm.set_value('language_direction', 'RTL');
            if (!frm.doc.arabic_font_family) {
                frm.set_value('arabic_font_family', 'Noto Sans Arabic');
            }
        } else {
            frm.set_value('language_direction', 'LTR');
        }
        
        frm.trigger('setup_arabic_fields');
    },
    
    chart_type: function(frm) {
        if (frm.doc.chart_type && frm.doc.chart_type !== 'Table') {
            if (!frm.doc.chart_library) {
                frm.set_value('chart_library', 'Chart.js');
            }
        }
        
        frm.trigger('update_chart_preview');
    },
    
    chart_library: function(frm) {
        frm.trigger('load_external_libraries');
    },
    
    report_name: function(frm) {
        // Auto-suggest Arabic name
        if (frm.doc.report_name && !frm.doc.report_name_ar) {
            const translations = {
                'Financial': 'مالي',
                'Service': 'خدمة',
                'Customer': 'عميل',
                'Inventory': 'مخزون',
                'Report': 'تقرير',
                'Dashboard': 'لوحة تحكم',
                'Analysis': 'تحليل'
            };
            
            let arabic_suggestion = '';
            Object.keys(translations).forEach(key => {
                if (frm.doc.report_name.toLowerCase().includes(key.toLowerCase())) {
                    arabic_suggestion = translations[key];
                }
            });
            
            if (arabic_suggestion) {
                frm.set_value('report_name_ar', arabic_suggestion);
            }
        }
    }
});

// Add CSS for drag-drop interface
frappe.ready(function() {
    if (!document.getElementById('report-builder-styles')) {
        const styles = `
            <style id="report-builder-styles">
                .report-builder-container {
                    margin: 20px 0;
                    padding: 15px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    background: #f9f9f9;
                }
                
                .fields-panel, .chart-options-panel, .preview-panel, .filters-panel {
                    background: white;
                    padding: 10px;
                    border-radius: 3px;
                    border: 1px solid #eee;
                }
                
                .field-item {
                    padding: 8px;
                    margin: 5px 0;
                    background: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 3px;
                    cursor: move;
                    display: flex;
                    align-items: center;
                }
                
                .field-item:hover {
                    background: #e9ecef;
                }
                
                .field-item.field-selected {
                    background: #d4edda;
                    border-color: #c3e6cb;
                }
                
                .field-item i {
                    margin-right: 8px;
                    color: #6c757d;
                }
                
                .field-label {
                    flex-grow: 1;
                    font-weight: 500;
                }
                
                .field-type {
                    font-size: 0.8em;
                    color: #6c757d;
                }
                
                .chart-type {
                    padding: 10px;
                    margin: 5px 0;
                    background: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 3px;
                    cursor: pointer;
                    text-align: center;
                }
                
                .chart-type:hover {
                    background: #e9ecef;
                }
                
                .chart-type.selected {
                    background: #007bff;
                    color: white;
                }
                
                .report-canvas {
                    min-height: 300px;
                    border: 2px dashed #dee2e6;
                    border-radius: 5px;
                    padding: 20px;
                    text-align: center;
                    background: white;
                }
                
                .canvas-placeholder {
                    color: #6c757d;
                    font-style: italic;
                    margin-top: 100px;
                }
                
                .chart-preview {
                    min-height: 200px;
                    background: white;
                    border: 1px solid #dee2e6;
                    border-radius: 3px;
                    padding: 10px;
                }
                
                .preview-placeholder {
                    color: #6c757d;
                    font-style: italic;
                    text-align: center;
                    margin-top: 80px;
                }
                
                .add-filter {
                    width: 100%;
                }
                
                /* RTL Support */
                .rtl .field-item {
                    direction: rtl;
                    text-align: right;
                }
                
                .rtl .field-item i {
                    margin-right: 0;
                    margin-left: 8px;
                }
            </style>
        `;
        document.head.insertAdjacentHTML('beforeend', styles);
    }
});
