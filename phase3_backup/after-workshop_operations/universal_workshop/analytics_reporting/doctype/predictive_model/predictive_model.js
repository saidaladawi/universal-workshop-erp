// Predictive Model Form JavaScript
// Enhanced form functionality with Arabic RTL support and ML model management

frappe.ui.form.on('Predictive Model', {
    refresh: function(frm) {
        frm.trigger('setup_arabic_fields');
        frm.trigger('setup_custom_buttons');
        frm.trigger('setup_field_dependencies');
        frm.trigger('check_ml_dependencies');
    },

    setup_arabic_fields: function(frm) {
        // Set RTL direction for Arabic fields
        const arabic_fields = ['model_name_ar'];
        arabic_fields.forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.attr('dir', 'rtl');
                frm.fields_dict[field].$input.css('text-align', 'right');
            }
        });

        // Apply RTL layout if Arabic language is selected
        if (frappe.boot.lang === 'ar') {
            frm.page.main.addClass('rtl-layout');
        }
    },

    setup_custom_buttons: function(frm) {
        if (!frm.doc.__islocal) {
            // Train Model Button
            if (frm.doc.model_status !== 'Training') {
                frm.add_custom_button(__('Train Model'), function() {
                    frm.trigger('train_model');
                }, __('Actions'));
            }

            // Generate Predictions Button
            if (frm.doc.model_status === 'Trained' || frm.doc.model_status === 'Deployed') {
                frm.add_custom_button(__('Generate Predictions'), function() {
                    frm.trigger('generate_predictions');
                }, __('Actions'));
            }

            // View Performance Button
            if (frm.doc.last_training_date) {
                frm.add_custom_button(__('View Performance'), function() {
                    frm.trigger('show_performance_dialog');
                }, __('Reports'));
            }

            // Check Dependencies Button
            frm.add_custom_button(__('Check ML Dependencies'), function() {
                frm.trigger('show_dependencies_dialog');
            }, __('System'));
        }
    },

    setup_field_dependencies: function(frm) {
        // Show/hide fields based on algorithm type
        frm.trigger('toggle_algorithm_fields');
        
        // Show/hide fields based on prediction type
        frm.trigger('toggle_prediction_fields');
    },

    algorithm_type: function(frm) {
        frm.trigger('toggle_algorithm_fields');
        frm.trigger('set_default_parameters');
    },

    prediction_type: function(frm) {
        frm.trigger('toggle_prediction_fields');
    },

    model_name: function(frm) {
        // Auto-suggest Arabic name when English name is entered
        if (frm.doc.model_name && !frm.doc.model_name_ar) {
            frm.trigger('suggest_arabic_name');
        }
    },

    toggle_algorithm_fields: function(frm) {
        const time_series_algorithms = ['ARIMA', 'Seasonal ARIMA', 'Prophet'];
        const is_time_series = time_series_algorithms.includes(frm.doc.algorithm_type);
        
        frm.toggle_display('seasonality_adjustment', is_time_series);
        frm.toggle_display('trend_smoothing', is_time_series);
    },

    toggle_prediction_fields: function(frm) {
        const time_series_types = ['Time Series Forecast', 'Trend Analysis'];
        const is_time_series = time_series_types.includes(frm.doc.prediction_type);
        
        frm.toggle_display('prediction_horizon_days', is_time_series);
        frm.toggle_display('seasonality_adjustment', is_time_series);
    },

    set_default_parameters: function(frm) {
        if (!frm.doc.model_parameters && frm.doc.algorithm_type) {
            let default_params = {};
            
            switch (frm.doc.algorithm_type) {
                case 'Random Forest':
                    default_params = {
                        "n_estimators": 100,
                        "max_depth": 10,
                        "random_state": 42
                    };
                    break;
                case 'Gradient Boosting':
                    default_params = {
                        "n_estimators": 100,
                        "learning_rate": 0.1,
                        "max_depth": 6,
                        "random_state": 42
                    };
                    break;
            }
            
            if (Object.keys(default_params).length > 0) {
                frm.set_value('model_parameters', JSON.stringify(default_params, null, 2));
            }
        }
    },

    suggest_arabic_name: function(frm) {
        // Simple Arabic name suggestions based on common ML terms
        const arabic_translations = {
            'revenue': 'الإيرادات',
            'forecast': 'التنبؤ',
            'prediction': 'التوقع',
            'demand': 'الطلب',
            'customer': 'العميل',
            'inventory': 'المخزون',
            'service': 'الخدمة'
        };
        
        let arabic_name = frm.doc.model_name.toLowerCase();
        
        Object.keys(arabic_translations).forEach(eng => {
            arabic_name = arabic_name.replace(eng, arabic_translations[eng]);
        });
        
        if (arabic_name !== frm.doc.model_name.toLowerCase()) {
            frm.set_value('model_name_ar', arabic_name);
        }
    },

    train_model: function(frm) {
        frappe.confirm(
            __('This will train the model using historical data. Continue?'),
            function() {
                frappe.show_progress(__('Training Model'), 50, 100, __('Training in progress...'));
                
                frappe.call({
                    method: 'universal_workshop.analytics_reporting.doctype.predictive_model.predictive_model.train_model',
                    args: {
                        model_code: frm.doc.name
                    },
                    callback: function(r) {
                        frappe.hide_progress();
                        
                        if (r.message && r.message.status === 'success') {
                            frappe.show_alert({
                                message: __('Model training completed successfully!'),
                                indicator: 'green'
                            });
                            frm.reload_doc();
                        } else {
                            frappe.msgprint({
                                title: __('Training Failed'),
                                message: r.message?.message || __('Model training failed'),
                                indicator: 'red'
                            });
                        }
                    }
                });
            }
        );
    },

    show_performance_dialog: function(frm) {
        frappe.call({
            method: 'universal_workshop.analytics_reporting.doctype.predictive_model.predictive_model.get_model_performance',
            args: {
                model_code: frm.doc.name
            },
            callback: function(r) {
                if (r.message && r.message.status === 'success') {
                    const perf = r.message.performance;
                    
                    const html = `
                        <div class="performance-metrics">
                            <h4>${__('Model Performance Metrics')}</h4>
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="metric-card">
                                        <h5>${__('Accuracy')}</h5>
                                        <div class="metric-value" style="color: ${perf.accuracy >= 70 ? 'green' : 'red'}">
                                            ${perf.accuracy ? perf.accuracy.toFixed(2) : 'N/A'}%
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="metric-card">
                                        <h5>${__('Model Status')}</h5>
                                        <div class="metric-value">
                                            ${perf.model_status}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <style>
                            .metric-card { padding: 15px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }
                            .metric-value { font-size: 1.2em; font-weight: bold; margin-top: 5px; }
                        </style>
                    `;

                    const dialog = new frappe.ui.Dialog({
                        title: __('Model Performance'),
                        fields: [
                            {
                                fieldname: 'performance_html',
                                fieldtype: 'HTML',
                                options: html
                            }
                        ]
                    });

                    dialog.show();
                }
            }
        });
    },

    show_dependencies_dialog: function(frm) {
        frappe.call({
            method: 'universal_workshop.analytics_reporting.doctype.predictive_model.predictive_model.check_ml_dependencies',
            callback: function(r) {
                if (r.message) {
                    const deps = r.message;
                    
                    const html = `
                        <div class="dependencies-status">
                            <h4>${__('ML Dependencies Status')}</h4>
                            <div class="dependency-item">
                                <span class="indicator ${deps.scikit_learn ? 'green' : 'red'}">
                                    scikit-learn: ${deps.scikit_learn ? __('Installed') : __('Not Installed')}
                                </span>
                            </div>
                        </div>
                    `;

                    const dialog = new frappe.ui.Dialog({
                        title: __('ML Dependencies'),
                        fields: [
                            {
                                fieldname: 'dependencies_html',
                                fieldtype: 'HTML',
                                options: html
                            }
                        ]
                    });

                    dialog.show();
                }
            }
        });
    },

    check_ml_dependencies: function(frm) {
        // Check dependencies on form load
        frappe.call({
            method: 'universal_workshop.analytics_reporting.doctype.predictive_model.predictive_model.check_ml_dependencies',
            callback: function(r) {
                if (r.message && !r.message.scikit_learn) {
                    frm.dashboard.add_comment(
                        __('Warning: ML libraries not installed. Some features may not work.'),
                        'orange', true
                    );
                }
            }
        });
    }
});
