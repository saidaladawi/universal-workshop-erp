// Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
// For license information, please see license.txt

frappe.ui.form.on("Technician", {
	refresh: function (frm) {
		// Set up Arabic fields and RTL support
		frm.trigger("setup_arabic_fields");
		frm.trigger("setup_custom_buttons");
		frm.trigger("setup_performance_indicators");
	},

	setup_arabic_fields: function (frm) {
		// Apply RTL to Arabic fields
		["technician_name_ar"].forEach((field) => {
			if (frm.fields_dict[field]) {
				frm.fields_dict[field].$input.attr("dir", "rtl");
				frm.fields_dict[field].$input.css("text-align", "right");
			}
		});
	},

	setup_custom_buttons: function (frm) {
		if (!frm.doc.__islocal) {
			// Assignment Suggestions Button
			frm.add_custom_button(
				__("Assignment Suggestions"),
				function () {
					frm.trigger("show_assignment_suggestions");
				},
				__("Actions")
			);

			// Performance Report Button
			frm.add_custom_button(
				__("Performance Report"),
				function () {
					frm.trigger("show_performance_report");
				},
				__("Reports")
			);

			// Workload Analytics Button
			frm.add_custom_button(
				__("Workload Analytics"),
				function () {
					frm.trigger("show_workload_analytics");
				},
				__("Reports")
			);
		}
	},

	setup_performance_indicators: function (frm) {
		if (!frm.doc.__islocal) {
			// Show availability indicator
			frm.trigger("update_availability_indicator");

			// Show workload indicator
			frm.trigger("update_workload_indicator");
		}
	},

	update_availability_indicator: function (frm) {
		let availability_html = "";
		let status_class = "";

		if (frm.doc.is_available && frm.doc.employment_status === "Active") {
			status_class = "indicator-pill green";
			availability_html = `<span class="${status_class}">متاح</span>`;
		} else {
			status_class = "indicator-pill red";
			availability_html = `<span class="${status_class}">غير متاح</span>`;
		}

		frm.set_df_property("is_available", "description", availability_html);
	},

	update_workload_indicator: function (frm) {
		let workload_ratio = 0;
		if (frm.doc.capacity_hours_per_day > 0) {
			workload_ratio = frm.doc.current_workload_hours / (frm.doc.capacity_hours_per_day * 5);
		}

		let workload_html = "";
		let workload_class = "";

		if (workload_ratio <= 0.3) {
			workload_class = "indicator-pill green";
			workload_html = `<span class="${workload_class}">حمل عمل خفيف (${Math.round(
				workload_ratio * 100
			)}%)</span>`;
		} else if (workload_ratio <= 0.7) {
			workload_class = "indicator-pill yellow";
			workload_html = `<span class="${workload_class}">حمل عمل متوسط (${Math.round(
				workload_ratio * 100
			)}%)</span>`;
		} else {
			workload_class = "indicator-pill red";
			workload_html = `<span class="${workload_class}">حمل عمل عالي (${Math.round(
				workload_ratio * 100
			)}%)</span>`;
		}

		frm.set_df_property("current_workload_hours", "description", workload_html);
	},

	show_assignment_suggestions: function (frm) {
		frappe.call({
			method: "universal_workshop.workshop_management.utils.technician_assignment.suggest_technician_assignment",
			args: {
				service_order_id: null,
				department: frm.doc.department,
			},
			callback: function (r) {
				if (r.message && r.message.success) {
					frm.trigger("display_assignment_dialog", r.message);
				} else {
					frappe.msgprint(__("No assignment suggestions available"));
				}
			},
		});
	},

	show_performance_report: function (frm) {
		// Generate performance report
		let performance_data = {
			overall_rating: frm.doc.performance_rating || 0,
			efficiency_rating: frm.doc.efficiency_rating || 0,
			quality_rating: frm.doc.quality_rating || 0,
			jobs_completed: frm.doc.total_jobs_completed || 0,
			avg_completion_time: frm.doc.average_job_time_hours || 0,
		};

		let dialog = new frappe.ui.Dialog({
			title: __("Performance Report - {0}", [frm.doc.technician_name]),
			fields: [
				{
					fieldtype: "HTML",
					fieldname: "performance_html",
				},
			],
		});

		let html = frm.trigger("generate_performance_html", performance_data);
		dialog.fields_dict.performance_html.$wrapper.html(html);
		dialog.show();
	},

	generate_performance_html: function (frm, data) {
		return `
            <div class="performance-report">
                <div class="row">
                    <div class="col-md-6">
                        <h4>الأداء العام</h4>
                        <p><strong>تقييم الأداء:</strong> ${data.overall_rating}/5</p>
                        <p><strong>تقييم الكفاءة:</strong> ${data.efficiency_rating}/5</p>
                        <p><strong>تقييم الجودة:</strong> ${data.quality_rating}/5</p>
                    </div>
                    <div class="col-md-6">
                        <h4>الإحصائيات</h4>
                        <p><strong>المهام المكتملة:</strong> ${data.jobs_completed}</p>
                        <p><strong>متوسط وقت الإنجاز:</strong> ${data.avg_completion_time} ساعة</p>
                    </div>
                </div>
            </div>
        `;
	},

	show_workload_analytics: function (frm) {
		frappe.route_options = {
			technician: frm.doc.name,
		};
		frappe.set_route("query-report", "Technician Workload Analytics");
	},

	employment_status: function (frm) {
		// Auto-update availability based on employment status
		if (["Inactive", "OnLeave", "Terminated"].includes(frm.doc.employment_status)) {
			frm.set_value("is_available", 0);
		}
		frm.trigger("update_availability_indicator");
	},

	is_available: function (frm) {
		frm.trigger("update_availability_indicator");
	},

	current_workload_hours: function (frm) {
		frm.trigger("update_workload_indicator");
	},

	capacity_hours_per_day: function (frm) {
		frm.trigger("update_workload_indicator");
	},
});

// Child table events for skills
frappe.ui.form.on("Technician Skills", {
	skill: function (frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.skill) {
			// Fetch Arabic skill name
			frappe.db.get_value("Skill", row.skill, "skill_name_ar", function (value) {
				if (value && value.skill_name_ar) {
					frappe.model.set_value(cdt, cdn, "skill_name_ar", value.skill_name_ar);
				}
			});
		}
	},

	proficiency_level: function (frm, cdt, cdn) {
		let row = locals[cdt][cdn];

		// Suggest minimum experience based on proficiency level
		if (row.proficiency_level && !row.years_experience) {
			let min_experience = {
				Beginner: 0,
				Intermediate: 1,
				Advanced: 3,
				Expert: 5,
			};

			frappe.model.set_value(
				cdt,
				cdn,
				"years_experience",
				min_experience[row.proficiency_level]
			);
		}
	},
});

// Utility functions
function calculate_availability_score(technician_doc) {
	if (!technician_doc.is_available || technician_doc.employment_status !== "Active") {
		return 0;
	}

	let workload_ratio =
		technician_doc.current_workload_hours / (technician_doc.capacity_hours_per_day * 5);
	let availability_score = Math.max(0, 100 - workload_ratio * 100);

	// Adjust based on performance ratings
	let performance_multiplier =
		((technician_doc.performance_rating || 3) +
			(technician_doc.efficiency_rating || 3) +
			(technician_doc.quality_rating || 3)) /
		15;

	return Math.round(availability_score * performance_multiplier);
}
