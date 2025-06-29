// Copyright (c) 2024, Universal Workshop and contributors
// For license information, please see license.txt

frappe.ui.form.on('Training Path', {
    refresh: function (frm) {
        // Add custom buttons
        if (!frm.doc.__islocal) {
            frm.add_custom_button(__('View Statistics'), function () {
                frm.events.show_path_statistics(frm);
            });

            frm.add_custom_button(__('Enroll Users'), function () {
                frm.events.enroll_users_dialog(frm);
            });

            frm.add_custom_button(__('Preview Path'), function () {
                frm.events.preview_training_path(frm);
            });

            // Add action buttons group
            frm.add_custom_button(__('Export Path'), function () {
                frm.events.export_training_path(frm);
            }, __('Actions'));

            frm.add_custom_button(__('Duplicate Path'), function () {
                frm.events.duplicate_training_path(frm);
            }, __('Actions'));
        }

        // Set field dependencies
        frm.events.setup_field_dependencies(frm);

        // Real-time validation
        frm.events.setup_realtime_validation(frm);
    },

    role: function (frm) {
        // Auto-populate role-specific defaults
        if (frm.doc.role) {
            frm.events.set_role_defaults(frm);
        }
    },

    enable_adaptive_learning: function (frm) {
        // Show/hide adaptive learning fields
        frm.toggle_display(['performance_threshold', 'remedial_action'], frm.doc.enable_adaptive_learning);
    },

    auto_enrollment: function (frm) {
        // Show/hide enrollment criteria fields
        frm.toggle_display(['department_filter'], frm.doc.auto_enrollment);
    },

    setup_field_dependencies: function (frm) {
        // Setup conditional field display
        frm.toggle_display(['performance_threshold', 'remedial_action'], frm.doc.enable_adaptive_learning);
        frm.toggle_display(['department_filter'], frm.doc.auto_enrollment);

        // Make fields mandatory based on conditions
        frm.toggle_reqd('performance_threshold', frm.doc.enable_adaptive_learning);
        frm.toggle_reqd('remedial_action', frm.doc.enable_adaptive_learning);
    },

    setup_realtime_validation: function (frm) {
        // Real-time validation for modules
        if (frm.doc.training_modules) {
            frm.doc.training_modules.forEach(function (module, idx) {
                frm.fields_dict.training_modules.grid.grid_rows[idx].on_form_rendered = function () {
                    frm.events.validate_module_sequence(frm);
                };
            });
        }
    },

    validate_module_sequence: function (frm) {
        // Check for duplicate sequence orders
        let sequences = [];
        let has_duplicates = false;

        frm.doc.training_modules.forEach(function (module) {
            if (module.sequence_order && sequences.includes(module.sequence_order)) {
                has_duplicates = true;
            }
            if (module.sequence_order) {
                sequences.push(module.sequence_order);
            }
        });

        if (has_duplicates) {
            frappe.msgprint({
                title: __('Validation Error'),
                message: __('Duplicate sequence orders found. Please ensure each module has a unique sequence order.'),
                indicator: 'red'
            });
        }
    },

    set_role_defaults: function (frm) {
        // Set default values based on selected role
        const role_defaults = {
            'Workshop Manager': {
                difficulty_level: 'Advanced',
                mandatory_completion: 1,
                review_frequency_months: 12
            },
            'Technician': {
                difficulty_level: 'Intermediate',
                mandatory_completion: 1,
                review_frequency_months: 6
            },
            'Administrative Staff': {
                difficulty_level: 'Beginner',
                mandatory_completion: 0,
                review_frequency_months: 12
            }
        };

        const defaults = role_defaults[frm.doc.role];
        if (defaults && !frm.doc.difficulty_level) {
            Object.keys(defaults).forEach(function (field) {
                frm.set_value(field, defaults[field]);
            });
        }
    },

    show_path_statistics: function (frm) {
        frappe.call({
            method: 'get_path_statistics',
            doc: frm.doc,
            callback: function (r) {
                if (r.message) {
                    frm.events.display_statistics_dialog(frm, r.message);
                }
            }
        });
    },

    display_statistics_dialog: function (frm, stats) {
        let dialog = new frappe.ui.Dialog({
            title: __('Training Path Statistics'),
            size: 'large',
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'stats_html'
                }
            ]
        });

        let html = `
            <div class="training-path-stats">
                <div class="row">
                    <div class="col-sm-6">
                        <div class="card">
                            <div class="card-header"><h5>${__('Enrollment Summary')}</h5></div>
                            <div class="card-body">
                                <p><strong>${__('Total Enrolled')}:</strong> ${stats.total_enrolled}</p>
                                <p><strong>${__('Completed')}:</strong> ${stats.completed}</p>
                                <p><strong>${__('In Progress')}:</strong> ${stats.in_progress}</p>
                                <p><strong>${__('Not Started')}:</strong> ${stats.not_started}</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-sm-6">
                        <div class="card">
                            <div class="card-header"><h5>${__('Performance Metrics')}</h5></div>
                            <div class="card-body">
                                <p><strong>${__('Completion Rate')}:</strong> ${stats.completion_rate}%</p>
                                <p><strong>${__('Avg. Completion Time')}:</strong> ${stats.avg_completion_days} ${__('days')}</p>
                            </div>
                        </div>
                    </div>
                </div>
                <canvas id="pathStatsChart" width="400" height="200"></canvas>
            </div>
        `;

        dialog.fields_dict.stats_html.$wrapper.html(html);
        dialog.show();

        // Draw chart
        setTimeout(function () {
            frm.events.draw_statistics_chart(stats);
        }, 500);
    },

    draw_statistics_chart: function (stats) {
        const ctx = document.getElementById('pathStatsChart');
        if (ctx) {
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: [__('Completed'), __('In Progress'), __('Not Started')],
                    datasets: [{
                        data: [stats.completed, stats.in_progress, stats.not_started],
                        backgroundColor: ['#28a745', '#ffc107', '#dc3545']
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        title: {
                            display: true,
                            text: __('Training Path Progress Distribution')
                        }
                    }
                }
            });
        }
    },

    enroll_users_dialog: function (frm) {
        let dialog = new frappe.ui.Dialog({
            title: __('Enroll Users'),
            fields: [
                {
                    fieldtype: 'Link',
                    fieldname: 'user',
                    label: __('User'),
                    options: 'User',
                    reqd: 1,
                    get_query: function () {
                        return {
                            filters: {
                                enabled: 1,
                                name: ['not in', ['Administrator', 'Guest']]
                            }
                        };
                    }
                },
                {
                    fieldtype: 'Check',
                    fieldname: 'check_prerequisites',
                    label: __('Check Prerequisites'),
                    default: 1
                }
            ],
            primary_action_label: __('Enroll'),
            primary_action: function () {
                let values = dialog.get_values();
                if (values) {
                    frappe.call({
                        method: 'universal_workshop.training_management.doctype.training_path.training_path.enroll_user_in_path',
                        args: {
                            user: values.user,
                            training_path: frm.doc.name
                        },
                        callback: function (r) {
                            if (r.message && r.message.status === 'success') {
                                frappe.msgprint(__('User enrolled successfully'));
                                dialog.hide();
                            }
                        }
                    });
                }
            }
        });

        dialog.show();
    },

    preview_training_path: function (frm) {
        // Open training path preview in a modal
        let html = frm.events.generate_path_preview_html(frm);

        frappe.msgprint({
            title: __('Training Path Preview'),
            message: html,
            wide: true
        });
    },

    generate_path_preview_html: function (frm) {
        let modules_html = '';
        if (frm.doc.training_modules && frm.doc.training_modules.length > 0) {
            modules_html = frm.doc.training_modules.map(function (module, index) {
                return `
                    <div class="module-preview">
                        <h6>${index + 1}. ${module.module_title || module.training_module}</h6>
                        <p><strong>${__('Duration')}:</strong> ${module.estimated_duration_hours || 0} ${__('hours')}</p>
                        <p><strong>${__('Mandatory')}:</strong> ${module.is_mandatory ? __('Yes') : __('No')}</p>
                        ${module.passing_score_required ? `<p><strong>${__('Passing Score')}:</strong> ${module.passing_score_required}%</p>` : ''}
                    </div>
                `;
            }).join('');
        }

        return `
            <div class="training-path-preview">
                <h4>${frm.doc.path_name}</h4>
                <p><strong>${__('Target Role')}:</strong> ${frm.doc.role}</p>
                <p><strong>${__('Difficulty')}:</strong> ${__(frm.doc.difficulty_level || 'Not Set')}</p>
                <p><strong>${__('Total Duration')}:</strong> ${frm.doc.estimated_duration_hours || 0} ${__('hours')}</p>
                <p><strong>${__('Description')}:</strong> ${frm.doc.description || __('No description provided')}</p>
                
                <h5>${__('Training Modules')}</h5>
                ${modules_html || '<p>' + __('No modules defined') + '</p>'}
            </div>
        `;
    },

    export_training_path: function (frm) {
        // Export training path configuration
        frappe.call({
            method: 'frappe.desk.form.utils.get_doc_html',
            args: {
                doctype: 'Training Path',
                name: frm.doc.name
            },
            callback: function (r) {
                if (r.message) {
                    frappe.utils.print_format(r.message);
                }
            }
        });
    },

    duplicate_training_path: function (frm) {
        frappe.model.open_mapped_doc({
            method: 'frappe.model.mapper.make_mapped_doc',
            frm: frm,
            args: {
                source_doctype: 'Training Path',
                source_name: frm.doc.name,
                target_doctype: 'Training Path'
            }
        });
    }
});

// Training Modules child table events
frappe.ui.form.on('Training Path Module', {
    training_module: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.training_module) {
            // Auto-populate module details
            frappe.db.get_doc('Training Module', row.training_module).then(function (doc) {
                frappe.model.set_value(cdt, cdn, 'module_title', doc.title);
                frappe.model.set_value(cdt, cdn, 'estimated_duration_hours', doc.estimated_duration_hours || 1);
            });
        }
    },

    sequence_order: function (frm, cdt, cdn) {
        // Validate sequence order uniqueness
        frm.events.validate_module_sequence(frm);
    }
});
