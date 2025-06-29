// Copyright (c) 2024, Universal Workshop and contributors
// For license information, please see license.txt

frappe.ui.form.on('User Training Path', {
    refresh: function (frm) {
        // Add custom buttons
        if (!frm.doc.__islocal) {
            frm.add_custom_button(__('Learning Analytics'), function () {
                frm.events.show_learning_analytics(frm);
            });

            frm.add_custom_button(__('Progress Timeline'), function () {
                frm.events.show_progress_timeline(frm);
            });

            if (frm.doc.status === 'In Progress') {
                frm.add_custom_button(__('Record Remedial Action'), function () {
                    frm.events.record_remedial_action_dialog(frm);
                });

                frm.add_custom_button(__('Apply Adaptive Adjustment'), function () {
                    frm.events.apply_adaptive_adjustment_dialog(frm);
                });
            }

            if (frm.doc.current_module) {
                frm.add_custom_button(__('Start Current Module'), function () {
                    frm.events.start_current_module(frm);
                }, __('Quick Actions'));
            }

            frm.add_custom_button(__('View Training Path'), function () {
                frappe.set_route('Form', 'Training Path', frm.doc.training_path);
            }, __('Quick Actions'));
        }

        // Set progress indicators
        frm.events.setup_progress_indicators(frm);

        // Load real-time updates
        frm.events.setup_realtime_updates(frm);
    },

    training_path: function (frm) {
        if (frm.doc.training_path) {
            // Auto-populate path details
            frappe.db.get_doc('Training Path', frm.doc.training_path).then(function (doc) {
                frm.set_value('path_name', doc.path_name);
                frm.set_value('total_modules', doc.training_modules ? doc.training_modules.length : 0);
            });
        }
    },

    setup_progress_indicators: function (frm) {
        // Add progress bar to form
        if (frm.doc.progress_percentage !== undefined) {
            let progress_html = `
                <div class="progress mb-3">
                    <div class="progress-bar" role="progressbar" 
                         style="width: ${frm.doc.progress_percentage}%" 
                         aria-valuenow="${frm.doc.progress_percentage}" 
                         aria-valuemin="0" aria-valuemax="100">
                        ${frm.doc.progress_percentage.toFixed(1)}%
                    </div>
                </div>
                <div class="row">
                    <div class="col-sm-4">
                        <small class="text-muted">${__('Modules Completed')}: ${frm.doc.modules_completed || 0}/${frm.doc.total_modules || 0}</small>
                    </div>
                    <div class="col-sm-4">
                        <small class="text-muted">${__('Competency')}: ${__(frm.doc.overall_competency_level || 'Not Assessed')}</small>
                    </div>
                    <div class="col-sm-4">
                        <small class="text-muted">${__('Time Spent')}: ${(frm.doc.total_time_spent_hours || 0).toFixed(1)}h</small>
                    </div>
                </div>
            `;

            // Insert progress bar after the form header
            if (!frm.progress_area) {
                frm.progress_area = $('<div class="progress-section">').insertAfter(frm.layout.header);
            }
            frm.progress_area.html(progress_html);
        }
    },

    setup_realtime_updates: function (frm) {
        // Setup real-time updates for progress
        if (frm.doc.name) {
            frappe.realtime.on('training_progress_update', function (data) {
                if (data.user_training_path === frm.doc.name) {
                    frm.reload_doc();
                }
            });
        }
    },

    show_learning_analytics: function (frm) {
        frappe.call({
            method: 'get_learning_analytics',
            doc: frm.doc,
            callback: function (r) {
                if (r.message) {
                    frm.events.display_analytics_dialog(frm, r.message);
                }
            }
        });
    },

    display_analytics_dialog: function (frm, analytics) {
        let dialog = new frappe.ui.Dialog({
            title: __('Learning Analytics'),
            size: 'extra-large',
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'analytics_html'
                }
            ]
        });

        let modules_table = '';
        if (analytics.module_progress && analytics.module_progress.length > 0) {
            modules_table = analytics.module_progress.map(function (module) {
                return `
                    <tr>
                        <td>${module.module_title || module.training_module}</td>
                        <td><span class="badge badge-${module.status === 'Completed' ? 'success' : module.status === 'In Progress' ? 'warning' : 'secondary'}">${__(module.status || 'Not Started')}</span></td>
                        <td>${module.progress_percentage || 0}%</td>
                        <td>${module.quiz_score !== null ? module.quiz_score + '%' : 'N/A'}</td>
                        <td>${__(module.competency_level || 'Not Assessed')}</td>
                        <td>${module.time_spent_minutes ? (module.time_spent_minutes / 60).toFixed(1) + 'h' : 'N/A'}</td>
                    </tr>
                `;
            }).join('');
        }

        let difficulty_scores = '';
        if (analytics.avg_scores_by_difficulty) {
            Object.keys(analytics.avg_scores_by_difficulty).forEach(function (difficulty) {
                difficulty_scores += `<p><strong>${__(difficulty)}:</strong> ${analytics.avg_scores_by_difficulty[difficulty].toFixed(1)}%</p>`;
            });
        }

        let html = `
            <div class="learning-analytics">
                <div class="row mb-4">
                    <div class="col-sm-6">
                        <div class="card">
                            <div class="card-header"><h6>${__('Overall Performance')}</h6></div>
                            <div class="card-body">
                                <p><strong>${__('Completion Rate')}:</strong> ${analytics.completion_rate}%</p>
                                <p><strong>${__('Total Time')}:</strong> ${analytics.total_time_hours}h</p>
                                <p><strong>${__('Overall Competency')}:</strong> ${__(analytics.overall_competency)}</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-sm-6">
                        <div class="card">
                            <div class="card-header"><h6>${__('Performance by Difficulty')}</h6></div>
                            <div class="card-body">
                                ${difficulty_scores || '<p>' + __('No data available') + '</p>'}
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-sm-6">
                        <canvas id="timeDistributionChart" width="400" height="200"></canvas>
                    </div>
                    <div class="col-sm-6">
                        <canvas id="difficultyScoresChart" width="400" height="200"></canvas>
                    </div>
                </div>

                <h6 class="mt-4">${__('Module Details')}</h6>
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>${__('Module')}</th>
                            <th>${__('Status')}</th>
                            <th>${__('Progress')}</th>
                            <th>${__('Score')}</th>
                            <th>${__('Competency')}</th>
                            <th>${__('Time Spent')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${modules_table || '<tr><td colspan="6" class="text-center">' + __('No modules found') + '</td></tr>'}
                    </tbody>
                </table>
            </div>
        `;

        dialog.fields_dict.analytics_html.$wrapper.html(html);
        dialog.show();

        // Draw charts
        setTimeout(function () {
            frm.events.draw_analytics_charts(analytics);
        }, 500);
    },

    draw_analytics_charts: function (analytics) {
        // Time distribution chart
        const timeCtx = document.getElementById('timeDistributionChart');
        if (timeCtx && analytics.time_per_module) {
            new Chart(timeCtx, {
                type: 'bar',
                data: {
                    labels: Object.keys(analytics.time_per_module),
                    datasets: [{
                        label: __('Hours Spent'),
                        data: Object.values(analytics.time_per_module),
                        backgroundColor: '#007bff'
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        title: {
                            display: true,
                            text: __('Time Spent per Module')
                        }
                    }
                }
            });
        }

        // Difficulty scores chart
        const diffCtx = document.getElementById('difficultyScoresChart');
        if (diffCtx && analytics.avg_scores_by_difficulty) {
            new Chart(diffCtx, {
                type: 'radar',
                data: {
                    labels: Object.keys(analytics.avg_scores_by_difficulty),
                    datasets: [{
                        label: __('Average Score'),
                        data: Object.values(analytics.avg_scores_by_difficulty),
                        backgroundColor: 'rgba(40, 167, 69, 0.2)',
                        borderColor: '#28a745'
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        r: {
                            beginAtZero: true,
                            max: 100
                        }
                    },
                    plugins: {
                        title: {
                            display: true,
                            text: __('Performance by Difficulty Level')
                        }
                    }
                }
            });
        }
    },

    show_progress_timeline: function (frm) {
        // Create timeline view of training progress
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Training Progress',
                filters: {
                    user: frm.doc.user
                },
                fields: ['training_module', 'module_title', 'status', 'started_on', 'completed_on', 'quiz_score'],
                order_by: 'started_on desc'
            },
            callback: function (r) {
                if (r.message) {
                    frm.events.display_timeline_dialog(frm, r.message);
                }
            }
        });
    },

    display_timeline_dialog: function (frm, progress_data) {
        let dialog = new frappe.ui.Dialog({
            title: __('Progress Timeline'),
            size: 'large',
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'timeline_html'
                }
            ]
        });

        let timeline_html = progress_data.map(function (item) {
            let status_class = item.status === 'Completed' ? 'success' : item.status === 'In Progress' ? 'warning' : 'secondary';
            let date_text = item.completed_on || item.started_on || __('Not started');

            return `
                <div class="timeline-item">
                    <div class="timeline-marker bg-${status_class}"></div>
                    <div class="timeline-content">
                        <h6>${item.module_title || item.training_module}</h6>
                        <p class="text-muted">${__(item.status)} - ${date_text}</p>
                        ${item.quiz_score ? `<small class="badge badge-info">Score: ${item.quiz_score}%</small>` : ''}
                    </div>
                </div>
            `;
        }).join('');

        let html = `
            <div class="progress-timeline">
                <style>
                    .timeline-item {
                        display: flex;
                        margin-bottom: 20px;
                    }
                    .timeline-marker {
                        width: 12px;
                        height: 12px;
                        border-radius: 50%;
                        margin-right: 15px;
                        margin-top: 5px;
                    }
                    .timeline-content {
                        flex: 1;
                    }
                </style>
                ${timeline_html || '<p>' + __('No progress data found') + '</p>'}
            </div>
        `;

        dialog.fields_dict.timeline_html.$wrapper.html(html);
        dialog.show();
    },

    record_remedial_action_dialog: function (frm) {
        let dialog = new frappe.ui.Dialog({
            title: __('Record Remedial Action'),
            fields: [
                {
                    fieldtype: 'Select',
                    fieldname: 'action_type',
                    label: __('Action Type'),
                    options: [
                        'Additional Practice',
                        'Mentor Session',
                        'Review Session',
                        'Alternative Material',
                        'Extended Deadline',
                        'Other'
                    ],
                    reqd: 1
                },
                {
                    fieldtype: 'Small Text',
                    fieldname: 'details',
                    label: __('Details')
                }
            ],
            primary_action_label: __('Record'),
            primary_action: function () {
                let values = dialog.get_values();
                if (values) {
                    frappe.call({
                        method: 'record_remedial_action',
                        doc: frm.doc,
                        args: {
                            action_type: values.action_type,
                            details: values.details
                        },
                        callback: function (r) {
                            if (r.message && r.message.status === 'success') {
                                frappe.msgprint(__('Remedial action recorded'));
                                dialog.hide();
                                frm.reload_doc();
                            }
                        }
                    });
                }
            }
        });

        dialog.show();
    },

    apply_adaptive_adjustment_dialog: function (frm) {
        let dialog = new frappe.ui.Dialog({
            title: __('Apply Adaptive Adjustment'),
            fields: [
                {
                    fieldtype: 'Select',
                    fieldname: 'adjustment_type',
                    label: __('Adjustment Type'),
                    options: [
                        'Skip Optional Module',
                        'Add Supplementary Module',
                        'Adjust Difficulty',
                        'Modify Pace',
                        'Change Learning Path',
                        'Other'
                    ],
                    reqd: 1
                },
                {
                    fieldtype: 'Small Text',
                    fieldname: 'notes',
                    label: __('Notes')
                }
            ],
            primary_action_label: __('Apply'),
            primary_action: function () {
                let values = dialog.get_values();
                if (values) {
                    frappe.call({
                        method: 'apply_adaptive_adjustment',
                        doc: frm.doc,
                        args: {
                            adjustment_type: values.adjustment_type,
                            notes: values.notes
                        },
                        callback: function (r) {
                            if (r.message && r.message.status === 'success') {
                                frappe.msgprint(__('Adaptive adjustment applied'));
                                dialog.hide();
                                frm.reload_doc();
                            }
                        }
                    });
                }
            }
        });

        dialog.show();
    },

    start_current_module: function (frm) {
        if (frm.doc.current_module) {
            frappe.set_route('Form', 'Training Module', frm.doc.current_module);
        }
    }
});
