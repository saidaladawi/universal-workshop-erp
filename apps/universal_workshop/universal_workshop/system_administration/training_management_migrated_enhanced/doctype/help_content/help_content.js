// Copyright (c) 2024, Universal Workshop and contributors
// For license information, please see license.txt

frappe.ui.form.on('Help Content', {
	refresh: function (frm) {
		// Add custom buttons
		if (!frm.doc.__islocal) {
			frm.add_custom_button(__('Preview Help'), function () {
				frm.events.preview_help_content(frm);
			});

			frm.add_custom_button(__('Test Context'), function () {
				frm.events.test_contextual_help(frm);
			});

			frm.add_custom_button(__('View Analytics'), function () {
				frm.events.show_analytics(frm);
			});

			frm.add_custom_button(__('Clone Content'), function () {
				frm.events.clone_help_content(frm);
			}, __('Actions'));

			frm.add_custom_button(__('Export Content'), function () {
				frm.events.export_help_content(frm);
			}, __('Actions'));
		}

		// Set field dependencies
		frm.events.setup_field_dependencies(frm);

		// Setup real-time validation
		frm.events.setup_realtime_validation(frm);

		// Setup preview
		frm.events.setup_content_preview(frm);
	},

	title: function (frm) {
		// Auto-generate content key from title
		if (frm.doc.title && !frm.doc.content_key) {
			frm.set_value('content_key',
				frm.doc.title.toLowerCase()
					.replace(/[^a-z0-9\s]/g, '')
					.replace(/\s+/g, '-')
					.substring(0, 50)
			);
		}
	},

	help_type: function (frm) {
		frm.events.setup_help_type_fields(frm);
	},

	target_doctype: function (frm) {
		frm.events.load_doctype_fields(frm);
	},

	setup_field_dependencies: function (frm) {
		// Show/hide fields based on help type
		frm.events.setup_help_type_fields(frm);

		// Show/hide target field based on target doctype
		frm.toggle_display(['target_field'], frm.doc.target_doctype);

		// Make Arabic fields optional but recommended
		frm.set_df_property('title_ar', 'description', __('Arabic title for RTL support'));
		frm.set_df_property('content_ar', 'description', __('Arabic content for RTL support'));
	},

	setup_help_type_fields: function (frm) {
		const help_type = frm.doc.help_type;

		// Show/hide fields based on help type
		if (help_type === 'Tooltip') {
			frm.toggle_display(['tooltip_text', 'tooltip_text_ar'], true);
			frm.toggle_display(['content', 'content_ar'], false);
			frm.toggle_reqd('tooltip_text', true);
			frm.toggle_reqd('content', false);
		} else {
			frm.toggle_display(['tooltip_text', 'tooltip_text_ar'], false);
			frm.toggle_display(['content', 'content_ar'], true);
			frm.toggle_reqd('tooltip_text', false);
			frm.toggle_reqd('content', true);
		}

		// Special handling for guided tours
		if (help_type === 'Guided Tour') {
			frm.set_df_property('content', 'description',
				__('Use JSON format to define tour steps: [{"selector": ".btn", "content": "Click here", "position": "bottom"}]')
			);
		}
	},

	setup_realtime_validation: function (frm) {
		// Validate content key uniqueness
		frm.get_field('content_key').$input.on('blur', function () {
			if (frm.doc.content_key) {
				frappe.call({
					method: 'frappe.client.get_value',
					args: {
						doctype: 'Help Content',
						filters: {
							content_key: frm.doc.content_key,
							name: ['!=', frm.doc.name || '']
						},
						fieldname: 'name'
					},
					callback: function (r) {
						if (r.message && r.message.name) {
							frappe.msgprint({
								title: __('Validation Error'),
								message: __('Content Key already exists'),
								indicator: 'red'
							});
						}
					}
				});
			}
		});

		// Validate JSON in trigger conditions
		frm.get_field('trigger_conditions').$input.on('blur', function () {
			if (frm.doc.trigger_conditions) {
				try {
					JSON.parse(frm.doc.trigger_conditions);
				} catch (e) {
					frappe.msgprint({
						title: __('JSON Error'),
						message: __('Invalid JSON format in trigger conditions'),
						indicator: 'red'
					});
				}
			}
		});
	},

	setup_content_preview: function (frm) {
		if (frm.doc.content || frm.doc.tooltip_text) {
			// Add preview section
			if (!frm.preview_wrapper) {
				frm.preview_wrapper = $('<div class="help-content-preview">').insertAfter(frm.layout.wrapper.find('.form-section').last());
			}

			frm.events.update_preview(frm);
		}
	},

	update_preview: function (frm) {
		if (!frm.preview_wrapper) return;

		const content = frm.doc.content || frm.doc.tooltip_text || '';
		const help_type = frm.doc.help_type || 'Modal';

		let preview_html = `
            <div class="form-section">
                <div class="section-head">${__('Preview')}</div>
                <div class="help-preview-${help_type.toLowerCase()}">
                    ${content}
                </div>
            </div>
        `;

		frm.preview_wrapper.html(preview_html);
	},

	content: function (frm) {
		frm.events.update_preview(frm);
	},

	tooltip_text: function (frm) {
		frm.events.update_preview(frm);
	},

	load_doctype_fields: function (frm) {
		if (frm.doc.target_doctype) {
			frappe.call({
				method: 'frappe.client.get',
				args: {
					doctype: 'DocType',
					name: frm.doc.target_doctype
				},
				callback: function (r) {
					if (r.message) {
						const fields = r.message.fields || [];
						const field_options = fields.map(f => f.fieldname).join('\n');

						frm.set_df_property('target_field', 'options', field_options);
						frm.refresh_field('target_field');
					}
				}
			});
		}
	},

	preview_help_content: function (frm) {
		const content = frm.doc.content || frm.doc.tooltip_text || '';
		const help_type = frm.doc.help_type || 'Modal';

		if (help_type === 'Tooltip') {
			// Show tooltip preview
			frappe.show_alert({
				message: content,
				indicator: 'blue'
			});
		} else if (help_type === 'Modal') {
			// Show modal preview
			frappe.msgprint({
				title: frm.doc.title,
				message: content,
				wide: true
			});
		} else if (help_type === 'Popover') {
			// Show popover preview
			const d = new frappe.ui.Dialog({
				title: frm.doc.title,
				fields: [
					{
						fieldtype: 'HTML',
						fieldname: 'content_html',
						options: content
					}
				]
			});
			d.show();
		} else {
			// Default preview
			frappe.msgprint({
				title: __('Help Content Preview'),
				message: `
                    <div class="help-preview">
                        <h5>${frm.doc.title}</h5>
                        <div>${content}</div>
                    </div>
                `,
				wide: true
			});
		}
	},

	test_contextual_help: function (frm) {
		// Test contextual help in current context
		frappe.call({
			method: 'universal_workshop.training_management.doctype.help_content.help_content.get_contextual_help',
			args: {
				route: window.location.pathname,
				doctype: frm.doc.target_doctype,
				field: frm.doc.target_field
			},
			callback: function (r) {
				if (r.message) {
					let message = '<h5>' + __('Contextual Help Results') + '</h5>';

					if (r.message.length === 0) {
						message += '<p>' + __('No contextual help found for current context') + '</p>';
					} else {
						message += '<ul>';
						r.message.forEach(function (item) {
							message += `<li><strong>${item.title}</strong> (${item.help_type}) - ${item.priority}</li>`;
						});
						message += '</ul>';
					}

					frappe.msgprint({
						title: __('Test Results'),
						message: message,
						wide: true
					});
				}
			}
		});
	},

	show_analytics: function (frm) {
		frappe.route_options = { "help_content": frm.doc.name };
		frappe.set_route("query-report", "Help Content Analytics");
	},

	clone_help_content: function (frm) {
		frappe.model.open_mapped_doc({
			method: 'frappe.model.mapper.make_mapped_doc',
			frm: frm,
			args: {
				source_doctype: 'Help Content',
				source_name: frm.doc.name,
				target_doctype: 'Help Content'
			}
		});
	},

	export_help_content: function (frm) {
		// Export help content as JSON
		const export_data = {
			title: frm.doc.title,
			title_ar: frm.doc.title_ar,
			content_key: frm.doc.content_key,
			help_type: frm.doc.help_type,
			priority: frm.doc.priority,
			content: frm.doc.content,
			content_ar: frm.doc.content_ar,
			tooltip_text: frm.doc.tooltip_text,
			tooltip_text_ar: frm.doc.tooltip_text_ar,
			target_doctype: frm.doc.target_doctype,
			target_page: frm.doc.target_page,
			target_field: frm.doc.target_field,
			trigger_conditions: frm.doc.trigger_conditions,
			application_routes: frm.doc.application_routes,
			user_roles: frm.doc.user_roles
		};

		const dataStr = JSON.stringify(export_data, null, 2);
		const dataBlob = new Blob([dataStr], { type: 'application/json' });

		const link = document.createElement('a');
		link.href = URL.createObjectURL(dataBlob);
		link.download = `help_content_${frm.doc.content_key}.json`;
		link.click();
	}
});

// Child table events
frappe.ui.form.on('Help Content Route', {
	route: function (frm, cdt, cdn) {
		// Validate route format
		const row = locals[cdt][cdn];
		if (row.route && !row.route.startsWith('/')) {
			frappe.model.set_value(cdt, cdn, 'route', '/' + row.route);
		}
	}
});

frappe.ui.form.on('Help Content Documentation', {
	knowledge_base_article: function (frm, cdt, cdn) {
		// Auto-populate article title
		const row = locals[cdt][cdn];
		if (row.knowledge_base_article) {
			frappe.db.get_value('Knowledge Base Article', row.knowledge_base_article, 'title')
				.then(r => {
					if (r.message) {
						frappe.model.set_value(cdt, cdn, 'article_title', r.message.title);
					}
				});
		}
	}
});

frappe.ui.form.on('Help Content Training', {
	training_module: function (frm, cdt, cdn) {
		// Auto-populate module title
		const row = locals[cdt][cdn];
		if (row.training_module) {
			frappe.db.get_value('Training Module', row.training_module, 'title')
				.then(r => {
					if (r.message) {
						frappe.model.set_value(cdt, cdn, 'module_title', r.message.title);
					}
				});
		}
	}
});
