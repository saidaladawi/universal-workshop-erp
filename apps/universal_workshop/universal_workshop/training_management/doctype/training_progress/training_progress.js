frappe.ui.form.on('Training Progress', {
	refresh: function (frm) {
		// Add custom buttons
		add_custom_buttons(frm);

		// Set up progress visualization
		setup_progress_visualization(frm);

		// Add milestone indicators
		add_milestone_indicators(frm);

		// Setup real-time updates
		setup_realtime_updates(frm);

		// Add dashboard link
		add_dashboard_link(frm);
	},

	progress_percentage: function (frm) {
		// Update status based on progress
		update_status_from_progress(frm);

		// Show milestone achievement
		check_milestone_achievement(frm);

		// Update progress visualization
		update_progress_bar(frm);
	},

	quiz_score: function (frm) {
		// Auto-calculate competency level
		calculate_competency_level(frm);

		// Show score feedback
		show_score_feedback(frm);
	},

	user: function (frm) {
		// Auto-populate user details
		if (frm.doc.user) {
			populate_user_details(frm);
		}
	},

	training_module: function (frm) {
		// Auto-populate module details
		if (frm.doc.training_module) {
			populate_module_details(frm);
		}
	}
});

function add_custom_buttons(frm) {
	if (!frm.is_new()) {
		// Update Progress button
		frm.add_custom_button(__('Update Progress'), function () {
			update_progress_dialog(frm);
		}, __('Actions'));

		// Record Quiz Attempt button
		if (frm.doc.has_assessment) {
			frm.add_custom_button(__('Record Quiz Attempt'), function () {
				quiz_attempt_dialog(frm);
			}, __('Actions'));
		}

		// Skill Gap Analysis button
		frm.add_custom_button(__('Analyze Skill Gaps'), function () {
			analyze_skill_gaps(frm);
		}, __('Actions'));

		// View Certificate button (if certified)
		if (frm.doc.certification_issued) {
			frm.add_custom_button(__('View Certificate'), function () {
				view_certificate(frm);
			}, __('Actions'));
		}
	}
}

function setup_progress_visualization(frm) {
	if (frm.doc.progress_percentage !== undefined) {
		// Create progress bar HTML
		const progress_html = `
            <div class="progress-container" style="margin: 15px 0;">
                <div class="progress-header" style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span style="font-weight: bold;">Training Progress</span>
                    <span style="color: #667eea;">${frm.doc.progress_percentage}%</span>
                </div>
                <div class="progress-bar-wrapper" style="background: #e9ecef; border-radius: 20px; height: 20px; overflow: hidden;">
                    <div class="progress-bar-fill" style="
                        height: 100%;
                        background: linear-gradient(90deg, #667eea, #764ba2);
                        width: ${frm.doc.progress_percentage}%;
                        transition: width 0.5s ease;
                        border-radius: 20px;
                    "></div>
                </div>
            </div>
        `;

		// Add progress bar after the progress_percentage field
		frm.get_field('progress_percentage').$wrapper.after(progress_html);
	}
}

function add_milestone_indicators(frm) {
	const milestones = [25, 50, 75, 100];
	const current_progress = frm.doc.progress_percentage || 0;

	let milestone_html = '<div class="milestone-indicators" style="margin: 10px 0; display: flex; justify-content: space-between;">';

	milestones.forEach(milestone => {
		const achieved = current_progress >= milestone;
		const color = achieved ? '#28a745' : '#dee2e6';
		const icon = achieved ? '✓' : milestone;

		milestone_html += `
            <div class="milestone" style="
                width: 40px;
                height: 40px;
                border-radius: 50%;
                background: ${color};
                color: white;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
                font-size: 12px;
            " title="${__('Milestone')}: ${milestone}%">
                ${achieved ? icon : milestone + '%'}
            </div>
        `;
	});

	milestone_html += '</div>';

	// Add milestone indicators after progress visualization
	frm.get_field('progress_percentage').$wrapper.siblings('.progress-container').after(milestone_html);
}

function setup_realtime_updates(frm) {
	// Listen for real-time progress updates
	frappe.realtime.on('training_progress_update', function (data) {
		if (data.training_progress === frm.doc.name) {
			// Update form fields
			frm.set_value('progress_percentage', data.progress_percentage);
			frm.set_value('time_spent_minutes', data.time_spent_minutes);
			frm.set_value('last_accessed', data.last_accessed);

			// Refresh visualizations
			update_progress_bar(frm);
			add_milestone_indicators(frm);
		}
	});

	// Listen for milestone notifications
	frappe.realtime.on('training_milestone', function (data) {
		if (data.user === frappe.session.user) {
			frappe.show_alert({
				message: data.message,
				indicator: 'green'
			}, 5);
		}
	});
}

function add_dashboard_link(frm) {
	// Add link to training dashboard
	const dashboard_link = `
        <div style="margin: 15px 0; padding: 10px; background: #f8f9fa; border-radius: 5px;">
            <a href="/training-dashboard" target="_blank" style="color: #667eea; text-decoration: none;">
                <i class="fa fa-dashboard"></i> ${__('View Training Dashboard')}
            </a>
        </div>
    `;

	frm.get_field('notes').$wrapper.before(dashboard_link);
}

function update_status_from_progress(frm) {
	const progress = frm.doc.progress_percentage || 0;

	if (progress >= 100 && frm.doc.status !== 'Completed') {
		frm.set_value('status', 'Completed');
		frappe.show_alert({
			message: __('Training module completed! Congratulations!'),
			indicator: 'green'
		}, 3);
	} else if (progress > 0 && frm.doc.status === 'Not Started') {
		frm.set_value('status', 'In Progress');
	}
}

function check_milestone_achievement(frm) {
	const progress = frm.doc.progress_percentage || 0;
	const milestones = [25, 50, 75, 100];

	milestones.forEach(milestone => {
		if (progress >= milestone && progress < milestone + 5) { // Check if just reached
			frappe.show_alert({
				message: __('Milestone achieved: {0}% complete!', [milestone]),
				indicator: 'green'
			}, 4);
		}
	});
}

function update_progress_bar(frm) {
	const progress_fill = frm.$wrapper.find('.progress-bar-fill');
	if (progress_fill.length) {
		progress_fill.css('width', (frm.doc.progress_percentage || 0) + '%');
	}

	// Update percentage display
	frm.$wrapper.find('.progress-header span:last-child').text((frm.doc.progress_percentage || 0) + '%');
}

function calculate_competency_level(frm) {
	const score = frm.doc.quiz_score || 0;
	const status = frm.doc.status;

	if (status === 'Completed' && frm.doc.passed_assessment) {
		if (score >= 90) {
			frm.set_value('competency_level', 'Expert');
		} else if (score >= 80) {
			frm.set_value('competency_level', 'Advanced');
		} else if (score >= 70) {
			frm.set_value('competency_level', 'Intermediate');
		} else {
			frm.set_value('competency_level', 'Beginner');
		}
	}
}

function show_score_feedback(frm) {
	const score = frm.doc.quiz_score || 0;
	const passing_score = frm.doc.passing_score_required || 70;

	let message, indicator;

	if (score >= 90) {
		message = __('Excellent! Outstanding performance.');
		indicator = 'green';
	} else if (score >= passing_score) {
		message = __('Good job! You passed the assessment.');
		indicator = 'blue';
	} else {
		message = __('Score below passing threshold. Additional training recommended.');
		indicator = 'orange';
	}

	frappe.show_alert({ message, indicator }, 3);
}

function populate_user_details(frm) {
	frappe.call({
		method: 'frappe.client.get',
		args: {
			doctype: 'User',
			name: frm.doc.user
		},
		callback: function (r) {
			if (r.message) {
				frm.set_value('full_name', r.message.full_name || r.message.first_name);

				// Get primary role
				if (r.message.roles && r.message.roles.length > 0) {
					frm.set_value('role', r.message.roles[0].role);
				}
			}
		}
	});
}

function populate_module_details(frm) {
	frappe.call({
		method: 'frappe.client.get',
		args: {
			doctype: 'Training Module',
			name: frm.doc.training_module
		},
		callback: function (r) {
			if (r.message) {
				frm.set_value('module_title', r.message.title);
				frm.set_value('has_assessment', r.message.has_quiz);
				frm.set_value('passing_score_required', r.message.passing_score || 70);
			}
		}
	});
}

function update_progress_dialog(frm) {
	const dialog = new frappe.ui.Dialog({
		title: __('Update Training Progress'),
		fields: [
			{
				fieldtype: 'Percent',
				fieldname: 'progress_percentage',
				label: __('Progress Percentage'),
				reqd: 1,
				default: frm.doc.progress_percentage || 0
			},
			{
				fieldtype: 'Int',
				fieldname: 'time_spent',
				label: __('Additional Time Spent (minutes)'),
				default: 0
			}
		],
		primary_action_label: __('Update'),
		primary_action: function (values) {
			frappe.call({
				method: 'update_progress',
				doc: frm.doc,
				args: {
					progress_percentage: values.progress_percentage,
					time_spent: values.time_spent
				},
				callback: function (r) {
					if (r.message && r.message.status === 'success') {
						frm.reload_doc();
						frappe.show_alert({
							message: r.message.message,
							indicator: 'green'
						});
					}
				}
			});
			dialog.hide();
		}
	});

	dialog.show();
}

function quiz_attempt_dialog(frm) {
	const dialog = new frappe.ui.Dialog({
		title: __('Record Quiz Attempt'),
		fields: [
			{
				fieldtype: 'Percent',
				fieldname: 'quiz_score',
				label: __('Quiz Score (%)'),
				reqd: 1,
				default: frm.doc.quiz_score || 0
			},
			{
				fieldtype: 'Int',
				fieldname: 'attempt_number',
				label: __('Attempt Number'),
				default: (frm.doc.quiz_attempts || 0) + 1
			}
		],
		primary_action_label: __('Record'),
		primary_action: function (values) {
			frappe.call({
				method: 'record_quiz_attempt',
				doc: frm.doc,
				args: {
					score: values.quiz_score,
					attempt_number: values.attempt_number
				},
				callback: function (r) {
					if (r.message && r.message.status === 'success') {
						frm.reload_doc();
						frappe.show_alert({
							message: r.message.message + (r.message.passed ? ' ✓' : ''),
							indicator: r.message.passed ? 'green' : 'orange'
						});
					}
				}
			});
			dialog.hide();
		}
	});

	dialog.show();
}

function analyze_skill_gaps(frm) {
	frappe.call({
		method: 'identify_skill_gaps',
		doc: frm.doc,
		callback: function (r) {
			if (r.message) {
				const gaps = r.message.gaps;
				if (gaps.length > 0) {
					frappe.msgprint({
						title: __('Skill Gap Analysis'),
						message: __('Identified Areas for Improvement:') + '<ul><li>' + gaps.join('</li><li>') + '</li></ul>',
						indicator: 'orange'
					});
				} else {
					frappe.show_alert({
						message: __('No skill gaps identified. Great work!'),
						indicator: 'green'
					});
				}

				frm.reload_doc();
			}
		}
	});
}

function view_certificate(frm) {
	frappe.call({
		method: 'frappe.client.get_list',
		args: {
			doctype: 'Training Certification',
			filters: {
				training_progress: frm.doc.name
			},
			fields: ['name', 'certificate_file', 'certificate_number']
		},
		callback: function (r) {
			if (r.message && r.message.length > 0) {
				const cert = r.message[0];
				if (cert.certificate_file) {
					window.open(cert.certificate_file, '_blank');
				} else {
					frappe.msgprint(__('Certificate file not found'));
				}
			} else {
				frappe.msgprint(__('Certificate not found'));
			}
		}
	});
}
