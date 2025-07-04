// Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
// For license information, please see license.txt

frappe.ui.form.on('Service Order', {
	refresh: function(frm) {
		// Setup Arabic RTL layout
		frm.trigger('setup_arabic_layout');
		
		// Add custom buttons based on status
		frm.trigger('setup_custom_buttons');
		
		// Setup field visibility and properties
		frm.trigger('setup_field_properties');
		
		// Setup auto-calculations
		frm.trigger('setup_calculations');
		
		// Setup status indicators
		frm.trigger('setup_status_indicators');
		
		// Auto-refresh if in progress
		if (frm.doc.status === 'In Progress') {
			frm.trigger('setup_auto_refresh');
		}
	},
	
	setup_arabic_layout: function(frm) {
		// Apply RTL layout for Arabic locale
		if (frappe.boot.lang === 'ar') {
			frm.page.main.addClass('rtl-layout');
			
			// Set Arabic direction for Arabic fields
			['customer_name_ar', 'service_type_ar', 'description_ar'].forEach(field => {
				if (frm.fields_dict[field]) {
					frm.fields_dict[field].$input.attr('dir', 'rtl');
					frm.fields_dict[field].$input.addClass('arabic-text');
				}
			});
		}
	},
	
	setup_custom_buttons: function(frm) {
		// Clear existing custom buttons
		frm.page.clear_custom_actions();
		
		if (frm.doc.docstatus === 1) {
			// Status-specific buttons
			switch(frm.doc.status) {
				case 'Scheduled':
					frm.add_custom_button(__('Start Service'), function() {
						frm.trigger('start_service_action');
					}, __('Actions'));
					break;
					
				case 'In Progress':
					frm.add_custom_button(__('Quality Check'), function() {
						frm.trigger('quality_check_action');
					}, __('Actions'));
					
					frm.add_custom_button(__('Complete Service'), function() {
						frm.trigger('complete_service_action');
					}, __('Actions'));
					break;
					
				case 'Quality Check':
					frm.add_custom_button(__('Approve & Complete'), function() {
						frm.trigger('complete_service_action');
					}, __('Actions'));
					
					frm.add_custom_button(__('Return to Progress'), function() {
						frm.trigger('return_to_progress');
					}, __('Actions'));
					break;
					
				case 'Completed':
					frm.add_custom_button(__('Deliver Vehicle'), function() {
						frm.trigger('deliver_vehicle_action');
					}, __('Actions'));
					break;
			}
			
			// Always available actions
			if (frm.doc.status !== 'Delivered' && frm.doc.status !== 'Cancelled') {
				frm.add_custom_button(__('Print Service Report'), function() {
					frm.trigger('print_service_report');
				}, __('Print'));
				
				frm.add_custom_button(__('Send SMS Update'), function() {
					frm.trigger('send_sms_update');
				}, __('Communication'));
			}
		}
		
		// Dashboard button
		frm.add_custom_button(__('Service Dashboard'), function() {
			frappe.set_route('query-report', 'Service Order Dashboard');
		});
	},
	
	setup_field_properties: function(frm) {
		// Make fields read-only based on status
		const readonly_after_submit = [
			'customer', 'vehicle', 'service_type', 'service_date'
		];
		
		if (frm.doc.docstatus === 1) {
			readonly_after_submit.forEach(field => {
				frm.set_df_property(field, 'read_only', 1);
			});
		}
		
		// Conditional field display
		frm.toggle_display('approved_by', frm.doc.requires_approval);
		frm.toggle_display('approved_on', frm.doc.requires_approval && frm.doc.approved_by);
		frm.toggle_display('quality_check_notes', frm.doc.status === 'Quality Check');
	},
	
	setup_calculations: function(frm) {
		// Auto-calculate when parts or labor change
		frm.refresh_field('parts_used');
		frm.refresh_field('labor_entries');
	},
	
	setup_status_indicators: function(frm) {
		// Add status indicator colors
		const status_colors = {
			'Draft': 'grey',
			'Scheduled': 'blue', 
			'In Progress': 'orange',
			'Quality Check': 'purple',
			'Completed': 'green',
			'Delivered': 'darkgreen',
			'Cancelled': 'red'
		};
		
		if (frm.doc.status) {
			frm.page.set_indicator(frm.doc.status, status_colors[frm.doc.status] || 'grey');
		}
		
		// Add progress bar for workflow
		if (frm.doc.docstatus === 1) {
			frm.trigger('add_progress_bar');
		}
	},
	
	setup_auto_refresh: function(frm) {
		// Auto-refresh every 30 seconds for in-progress orders
		if (!frm.auto_refresh_timer) {
			frm.auto_refresh_timer = setInterval(function() {
				if (frm.doc.status === 'In Progress' && !frm.is_dirty()) {
					frm.reload_doc();
				}
			}, 30000);
		}
	},
	
	add_progress_bar: function(frm) {
		const statuses = ['Draft', 'Scheduled', 'In Progress', 'Quality Check', 'Completed', 'Delivered'];
		const current_index = statuses.indexOf(frm.doc.status);
		const progress_percent = ((current_index + 1) / statuses.length) * 100;
		
		const progress_html = `
			<div class="progress" style="margin-bottom: 15px;">
				<div class="progress-bar" role="progressbar" 
					 style="width: ${progress_percent}%;" 
					 aria-valuenow="${progress_percent}" 
					 aria-valuemin="0" 
					 aria-valuemax="100">
					${Math.round(progress_percent)}%
				</div>
			</div>
		`;
		
		frm.dashboard.add_section(progress_html, __('Service Progress'));
	},
	
	// Field change handlers
	customer: function(frm) {
		if (frm.doc.customer) {
			// Filter vehicles for selected customer
			frm.set_query('vehicle', function() {
				return {
					filters: {
						'customer': frm.doc.customer
					}
				};
			});
			
			// Clear vehicle if customer changed
			if (frm.doc.vehicle) {
				frm.set_value('vehicle', '');
			}
		}
	},
	
	vehicle: function(frm) {
		if (frm.doc.vehicle) {
			// Fetch and set vehicle details
			frappe.call({
				method: 'frappe.client.get',
				args: {
					doctype: 'Vehicle',
					name: frm.doc.vehicle
				},
				callback: function(r) {
					if (r.message) {
						const vehicle = r.message;
						frm.set_value('current_mileage', vehicle.current_mileage || 0);
						
						// Set estimated completion based on service type
						if (frm.doc.service_type) {
							frm.trigger('estimate_completion_time');
						}
					}
				}
			});
		}
	},
	
	service_type: function(frm) {
		if (frm.doc.service_type) {
			// Set Arabic translation
			frm.trigger('set_service_type_arabic');
			
			// Estimate completion time
			frm.trigger('estimate_completion_time');
			
			// Suggest common parts for service type
			frm.trigger('suggest_common_parts');
		}
	},
	
	set_service_type_arabic: function(frm) {
		const translations = {
			'Oil Change': 'تغيير الزيت',
			'Brake Service': 'خدمة الفرامل',
			'Transmission Service': 'خدمة ناقل الحركة',
			'Engine Repair': 'إصلاح المحرك',
			'Air Conditioning': 'تكييف الهواء',
			'Electrical': 'كهرباء',
			'Tire Service': 'خدمة الإطارات',
			'General Maintenance': 'صيانة عامة',
			'Inspection': 'فحص',
			'Emergency Repair': 'إصلاح طارئ',
			'Custom Service': 'خدمة مخصصة'
		};
		
		frm.set_value('service_type_ar', translations[frm.doc.service_type] || frm.doc.service_type);
	},
	
	estimate_completion_time: function(frm) {
		// Estimate completion time based on service type
		const service_durations = {
			'Oil Change': 1, // hours
			'Brake Service': 3,
			'Transmission Service': 6,
			'Engine Repair': 8,
			'Air Conditioning': 4,
			'Electrical': 5,
			'Tire Service': 2,
			'General Maintenance': 4,
			'Inspection': 1,
			'Emergency Repair': 6,
			'Custom Service': 4
		};
		
		const duration = service_durations[frm.doc.service_type] || 4;
		const service_date = frm.doc.service_date ? new Date(frm.doc.service_date) : new Date();
		
		// Add duration to service date (assuming 8 AM start time)
		service_date.setHours(8, 0, 0, 0);
		service_date.setHours(service_date.getHours() + duration);
		
		frm.set_value('estimated_completion_date', service_date);
	},
	
	suggest_common_parts: function(frm) {
		// Suggest common parts for the service type
		const common_parts = {
			'Oil Change': ['Engine Oil', 'Oil Filter'],
			'Brake Service': ['Brake Pads', 'Brake Fluid'],
			'Transmission Service': ['Transmission Oil', 'Transmission Filter'],
			'Air Conditioning': ['AC Filter', 'Refrigerant'],
			'Tire Service': ['Tire', 'Valve Stem'],
			'General Maintenance': ['Engine Oil', 'Oil Filter', 'Air Filter']
		};
		
		const suggested_parts = common_parts[frm.doc.service_type];
		if (suggested_parts && suggested_parts.length > 0) {
			frappe.msgprint({
				title: __('Suggested Parts'),
				message: __('Common parts for {0}: {1}', [frm.doc.service_type, suggested_parts.join(', ')]),
				indicator: 'blue'
			});
		}
	},
	
	// Calculation triggers
	discount_percentage: function(frm) {
		frm.trigger('calculate_totals');
	},
	
	vat_rate: function(frm) {
		frm.trigger('calculate_totals');
	},
	
	calculate_totals: function(frm) {
		// This will be handled by the server-side calculation
		// but we can provide immediate feedback
		setTimeout(function() {
			frm.save();
		}, 500);
	},
	
	// Action handlers
	start_service_action: function(frm) {
		frappe.call({
			method: 'start_service',
			doc: frm.doc,
			callback: function(r) {
				if (!r.exc) {
					frm.reload_doc();
					frappe.show_alert({
						message: __('Service started successfully'),
						indicator: 'green'
					});
				}
			}
		});
	},
	
	quality_check_action: function(frm) {
		const dialog = new frappe.ui.Dialog({
			title: __('Quality Check'),
			fields: [
				{
					fieldtype: 'Text',
					fieldname: 'quality_notes',
					label: __('Quality Check Notes'),
					reqd: 1
				},
				{
					fieldtype: 'Link',
					fieldname: 'quality_checker',
					label: __('Quality Checked By'),
					options: 'User',
					default: frappe.session.user,
					reqd: 1
				}
			],
			primary_action_label: __('Submit Quality Check'),
			primary_action: function(data) {
				frappe.call({
					method: 'quality_check',
					doc: frm.doc,
					args: {
						quality_notes: data.quality_notes,
						quality_checker: data.quality_checker
					},
					callback: function(r) {
						if (!r.exc) {
							dialog.hide();
							frm.reload_doc();
							frappe.show_alert({
								message: __('Quality check completed'),
								indicator: 'green'
							});
						}
					}
				});
			}
		});
		
		dialog.show();
	},
	
	complete_service_action: function(frm) {
		frappe.call({
			method: 'complete_service',
			doc: frm.doc,
			callback: function(r) {
				if (!r.exc) {
					frm.reload_doc();
					frappe.show_alert({
						message: __('Service completed successfully'),
						indicator: 'green'
					});
				}
			}
		});
	},
	
	deliver_vehicle_action: function(frm) {
		frappe.confirm(
			__('Are you sure you want to mark this vehicle as delivered?'),
			function() {
				frappe.call({
					method: 'deliver_vehicle',
					doc: frm.doc,
					callback: function(r) {
						if (!r.exc) {
							frm.reload_doc();
							frappe.show_alert({
								message: __('Vehicle delivered successfully'),
								indicator: 'green'
							});
						}
					}
				});
			}
		);
	},
	
	return_to_progress: function(frm) {
		frappe.call({
			method: 'frappe.client.set_value',
			args: {
				doctype: 'Service Order',
				name: frm.doc.name,
				fieldname: 'status',
				value: 'In Progress'
			},
			callback: function(r) {
				if (!r.exc) {
					frm.reload_doc();
				}
			}
		});
	},
	
	print_service_report: function(frm) {
		// Open print dialog for service report
		frappe.ui.get_print_settings(false, function(print_settings) {
			var w = window.open(
				frappe.urllib.get_full_url("/api/method/frappe.utils.print_format.download_pdf"
					+ "?doctype=" + encodeURIComponent('Service Order')
					+ "&name=" + encodeURIComponent(frm.doc.name)
					+ "&format=" + encodeURIComponent('Service Report')
					+ "&no_letterhead=" + (print_settings.with_letterhead ? "0" : "1")
				)
			);
			if (!w) {
				frappe.msgprint(__("Please enable pop-ups"));
				return;
			}
		});
	},
	
	send_sms_update: function(frm) {
		frappe.call({
			method: 'universal_workshop.utils.sms.send_service_update',
			args: {
				service_order: frm.doc.name,
				customer: frm.doc.customer,
				status: frm.doc.status
			},
			callback: function(r) {
				if (!r.exc) {
					frappe.show_alert({
						message: __('SMS sent successfully'),
						indicator: 'green'
					});
				}
			}
		});
	}
});

// Parts table handling
frappe.ui.form.on('Service Order Parts', {
	parts_used_add: function(frm, cdt, cdn) {
		// Set default values for new part row
		const row = locals[cdt][cdn];
		if (!row.quantity) {
			frappe.model.set_value(cdt, cdn, 'quantity', 1);
		}
	},
	
	item: function(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.item) {
			// Fetch item details
			frappe.call({
				method: 'frappe.client.get',
				args: {
					doctype: 'Item',
					name: row.item
				},
				callback: function(r) {
					if (r.message) {
						const item = r.message;
						frappe.model.set_value(cdt, cdn, 'item_name', item.item_name);
						frappe.model.set_value(cdt, cdn, 'item_name_ar', item.item_name_ar || item.item_name);
						frappe.model.set_value(cdt, cdn, 'description', item.description);
						frappe.model.set_value(cdt, cdn, 'description_ar', item.description_ar || item.description);
						
						// Get current price
						frappe.call({
							method: 'erpnext.stock.get_item_details.get_item_price',
							args: {
								item_code: row.item,
								price_list: 'Standard Selling',
								customer: frm.doc.customer,
								company: frappe.defaults.get_default('company')
							},
							callback: function(price_r) {
								if (price_r.message && price_r.message.price_list_rate) {
									frappe.model.set_value(cdt, cdn, 'unit_price', price_r.message.price_list_rate);
								}
							}
						});
					}
				}
			});
		}
	},
	
	quantity: function(frm, cdt, cdn) {
		calculate_part_total(frm, cdt, cdn);
	},
	
	unit_price: function(frm, cdt, cdn) {
		calculate_part_total(frm, cdt, cdn);
	}
});

// Labor table handling
frappe.ui.form.on('Service Order Labor', {
	labor_entries_add: function(frm, cdt, cdn) {
		// Set default values for new labor row
		const row = locals[cdt][cdn];
		if (!row.hours) {
			frappe.model.set_value(cdt, cdn, 'hours', 1);
		}
		if (!row.hourly_rate) {
			// Get standard hourly rate
			frappe.call({
				method: 'universal_workshop.utils.get_standard_hourly_rate',
				callback: function(r) {
					if (r.message) {
						frappe.model.set_value(cdt, cdn, 'hourly_rate', r.message);
					}
				}
			});
		}
	},
	
	technician: function(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.technician) {
			// Get technician's hourly rate from Employee record
			frappe.call({
				method: 'frappe.client.get_value',
				args: {
					doctype: 'Employee',
					filters: {user_id: row.technician},
					fieldname: 'hourly_rate'
				},
				callback: function(r) {
					if (r.message && r.message.hourly_rate) {
						frappe.model.set_value(cdt, cdn, 'hourly_rate', r.message.hourly_rate);
					}
				}
			});
		}
	},
	
	hours: function(frm, cdt, cdn) {
		calculate_labor_total(frm, cdt, cdn);
	},
	
	hourly_rate: function(frm, cdt, cdn) {
		calculate_labor_total(frm, cdt, cdn);
	}
});

// Helper functions
function calculate_part_total(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	if (row.quantity && row.unit_price) {
		const total = flt(row.quantity) * flt(row.unit_price);
		frappe.model.set_value(cdt, cdn, 'total_amount', total);
		
		// Recalculate form totals
		setTimeout(function() {
			frm.trigger('calculate_totals');
		}, 100);
	}
}

function calculate_labor_total(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	if (row.hours && row.hourly_rate) {
		const total = flt(row.hours) * flt(row.hourly_rate);
		frappe.model.set_value(cdt, cdn, 'total_amount', total);
		
		// Recalculate form totals
		setTimeout(function() {
			frm.trigger('calculate_totals');
		}, 100);
	}
}

// Cleanup function
frappe.ui.form.on('Service Order', {
	before_unload: function(frm) {
		// Clear auto-refresh timer
		if (frm.auto_refresh_timer) {
			clearInterval(frm.auto_refresh_timer);
		}
	}
}); 