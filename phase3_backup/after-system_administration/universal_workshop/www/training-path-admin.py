# Copyright (c) 2024, Universal Workshop and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate, now_datetime


def get_context(context):
	"""Get context for training path administration page"""
	context.title = _("Training Path Administration")
	context.show_sidebar = True

	# Check permissions
	if not frappe.has_permission("Training Path", "read"):
		frappe.throw(_("You don't have permission to access training path administration"))

	return context


@frappe.whitelist()
def get_admin_dashboard_data():
	"""Get dashboard data for training path administration"""

	# Get overview statistics
	total_paths = frappe.db.count("Training Path", {"is_active": 1})
	total_enrollments = frappe.db.count("User Training Path")
	completed_enrollments = frappe.db.count("User Training Path", {"status": "Completed"})
	completion_rate = (completed_enrollments / total_enrollments * 100) if total_enrollments > 0 else 0

	# Get active users (users with at least one enrollment)
	active_users = frappe.db.sql("""
		SELECT COUNT(DISTINCT user) as count
		FROM `tabUser Training Path`
		WHERE status IN ('In Progress', 'Completed')
	""")[0][0]

	# Get paths by role
	paths_by_role = frappe.db.sql("""
		SELECT
			tp.role,
			COUNT(tp.name) as path_count,
			COUNT(utp.name) as enrollment_count,
			SUM(CASE WHEN utp.status = 'Completed' THEN 1 ELSE 0 END) as completed_count
		FROM `tabTraining Path` tp
		LEFT JOIN `tabUser Training Path` utp ON tp.name = utp.training_path
		WHERE tp.is_active = 1
		GROUP BY tp.role
		ORDER BY path_count DESC
	""", as_dict=True)

	# Get enrollment trends (last 6 months)
	enrollment_trends = frappe.db.sql("""
		SELECT
			DATE_FORMAT(enrolled_on, '%Y-%m') as month,
			COUNT(*) as enrollments,
			SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completions
		FROM `tabUser Training Path`
		WHERE enrolled_on >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
		GROUP BY DATE_FORMAT(enrolled_on, '%Y-%m')
		ORDER BY month
	""", as_dict=True)

	# Get training paths with statistics
	training_paths = frappe.db.sql("""
		SELECT
			tp.name,
			tp.path_name,
			tp.path_name_ar,
			tp.role,
			tp.difficulty_level,
			tp.estimated_duration_hours,
			tp.mandatory_completion,
			tp.auto_enrollment,
			tp.is_active,
			COUNT(utp.name) as total_enrolled,
			SUM(CASE WHEN utp.status = 'Completed' THEN 1 ELSE 0 END) as completed,
			SUM(CASE WHEN utp.status = 'In Progress' THEN 1 ELSE 0 END) as in_progress,
			AVG(utp.progress_percentage) as avg_progress,
			AVG(utp.total_time_spent_hours) as avg_time_spent
		FROM `tabTraining Path` tp
		LEFT JOIN `tabUser Training Path` utp ON tp.name = utp.training_path
		WHERE tp.is_active = 1
		GROUP BY tp.name
		ORDER BY tp.role, tp.path_name
	""", as_dict=True)

	return {
		"overview": {
			"total_paths": total_paths,
			"total_enrollments": total_enrollments,
			"completion_rate": round(completion_rate, 1),
			"active_users": active_users
		},
		"paths_by_role": paths_by_role,
		"enrollment_trends": enrollment_trends,
		"training_paths": training_paths
	}


@frappe.whitelist()
def create_training_path(path_data):
	"""Create a new training path"""
	import json

	if isinstance(path_data, str):
		path_data = json.loads(path_data)

	# Create new training path
	path_doc = frappe.new_doc("Training Path")
	path_doc.update(path_data)
	path_doc.insert()

	return {"status": "success", "name": path_doc.name, "message": _("Training path created successfully")}


@frappe.whitelist()
def bulk_enroll_users(training_path, criteria_type, criteria_value):
	"""Bulk enroll users in a training path"""
	path_doc = frappe.get_doc("Training Path", training_path)
	enrolled_count = 0
	skipped_count = 0
	errors = []

	try:
		# Get users based on criteria
		users = get_users_by_criteria(criteria_type, criteria_value)

		for user in users:
			try:
				# Check if user meets enrollment criteria
				if path_doc.meets_enrollment_criteria(user):
					# Check if already enrolled
					existing = frappe.db.exists("User Training Path", {
						"user": user,
						"training_path": training_path
					})

					if not existing:
						path_doc.create_user_enrollment(user)
						enrolled_count += 1
					else:
						skipped_count += 1
				else:
					skipped_count += 1
			except Exception as e:
				errors.append(f"User {user}: {str(e)}")

	except Exception as e:
		return {"status": "error", "message": str(e)}

	return {
		"status": "success",
		"enrolled": enrolled_count,
		"skipped": skipped_count,
		"errors": errors,
		"message": _("Bulk enrollment completed. {0} users enrolled, {1} skipped").format(
			enrolled_count, skipped_count
		)
	}


def get_users_by_criteria(criteria_type, criteria_value):
	"""Get users based on enrollment criteria"""
	if criteria_type == "by_role":
		return frappe.get_all(
			"Has Role",
			filters={"role": criteria_value},
			fields=["parent as user"],
			pluck="user"
		)
	elif criteria_type == "by_department":
		employees = frappe.get_all(
			"Employee",
			filters={"department": criteria_value, "status": "Active"},
			fields=["user_id"]
		)
		return [emp.user_id for emp in employees if emp.user_id]
	elif criteria_type == "manual_select":
		# criteria_value should be a list of user IDs
		return criteria_value if isinstance(criteria_value, list) else [criteria_value]
	else:
		return []


@frappe.whitelist()
def get_path_enrollment_details(training_path):
	"""Get detailed enrollment information for a training path"""
	enrollments = frappe.db.sql("""
		SELECT
			utp.user,
			u.full_name,
			u.email,
			utp.status,
			utp.progress_percentage,
			utp.modules_completed,
			utp.total_modules,
			utp.overall_competency_level,
			utp.enrolled_on,
			utp.started_on,
			utp.completed_on,
			utp.total_time_spent_hours,
			utp.average_score,
			e.department
		FROM `tabUser Training Path` utp
		JOIN `tabUser` u ON utp.user = u.name
		LEFT JOIN `tabEmployee` e ON u.name = e.user_id
		WHERE utp.training_path = %s
		ORDER BY utp.enrolled_on DESC
	""", [training_path], as_dict=True)

	# Get path details
	path_doc = frappe.get_doc("Training Path", training_path)

	return {
		"path": {
			"name": path_doc.name,
			"path_name": path_doc.path_name,
			"role": path_doc.role,
			"description": path_doc.description,
			"difficulty_level": path_doc.difficulty_level,
			"estimated_duration_hours": path_doc.estimated_duration_hours
		},
		"enrollments": enrollments
	}


@frappe.whitelist()
def get_role_recommendations():
	"""Get recommendations for training path improvements"""
	recommendations = []

	# Find roles without training paths
	all_roles = frappe.get_all("Role", fields=["name"])
	roles_with_paths = frappe.get_all(
		"Training Path",
		filters={"is_active": 1},
		fields=["role"],
		distinct=True,
		pluck="role"
	)

	roles_without_paths = [r.name for r in all_roles if r.name not in roles_with_paths]

	for role in roles_without_paths:
		user_count = frappe.db.count("Has Role", {"role": role})
		if user_count > 0:
			recommendations.append({
				"type": "missing_path",
				"role": role,
				"user_count": user_count,
				"message": _("Role '{0}' has {1} users but no training paths").format(role, user_count),
				"priority": "high" if user_count > 10 else "medium"
			})

	# Find paths with low completion rates
	low_completion_paths = frappe.db.sql("""
		SELECT
			tp.name,
			tp.path_name,
			tp.role,
			COUNT(utp.name) as total_enrolled,
			SUM(CASE WHEN utp.status = 'Completed' THEN 1 ELSE 0 END) as completed,
			ROUND(SUM(CASE WHEN utp.status = 'Completed' THEN 1 ELSE 0 END) / COUNT(utp.name) * 100, 1) as completion_rate
		FROM `tabTraining Path` tp
		JOIN `tabUser Training Path` utp ON tp.name = utp.training_path
		WHERE tp.is_active = 1
		GROUP BY tp.name
		HAVING COUNT(utp.name) >= 5 AND completion_rate < 50
		ORDER BY completion_rate
	""", as_dict=True)

	for path in low_completion_paths:
		recommendations.append({
			"type": "low_completion",
			"path": path.name,
			"path_name": path.path_name,
			"role": path.role,
			"completion_rate": path.completion_rate,
			"message": _("Path '{0}' has low completion rate ({1}%)").format(
				path.path_name, path.completion_rate
			),
			"priority": "high" if path.completion_rate < 30 else "medium"
		})

	# Find users not enrolled in any paths for their roles
	users_without_paths = frappe.db.sql("""
		SELECT
			hr.parent as user,
			u.full_name,
			hr.role,
			COUNT(tp.name) as available_paths,
			COUNT(utp.name) as enrolled_paths
		FROM `tabHas Role` hr
		JOIN `tabUser` u ON hr.parent = u.name
		JOIN `tabTraining Path` tp ON hr.role = tp.role AND tp.is_active = 1
		LEFT JOIN `tabUser Training Path` utp ON hr.parent = utp.user
		WHERE u.enabled = 1 AND u.name NOT IN ('Administrator', 'Guest')
		GROUP BY hr.parent, hr.role
		HAVING available_paths > 0 AND enrolled_paths = 0
		LIMIT 10
	""", as_dict=True)

	if users_without_paths:
		recommendations.append({
			"type": "unenrolled_users",
			"count": len(users_without_paths),
			"users": users_without_paths,
			"message": _("{0} users have roles with available training paths but are not enrolled").format(
				len(users_without_paths)
			),
			"priority": "medium"
		})

	return recommendations


@frappe.whitelist()
def export_paths_report():
	"""Export training paths report"""
	from frappe.utils.xlsxutils import make_xlsx

	# Get data
	dashboard_data = get_admin_dashboard_data()

	# Prepare data for export
	data = []
	data.append([
		_("Path Name"), _("Role"), _("Difficulty"), _("Duration (Hours)"),
		_("Total Enrolled"), _("Completed"), _("In Progress"),
		_("Completion Rate"), _("Avg Progress"), _("Avg Time Spent")
	])

	for path in dashboard_data["training_paths"]:
		completion_rate = (path.completed / path.total_enrolled * 100) if path.total_enrolled > 0 else 0
		data.append([
			path.path_name,
			path.role,
			path.difficulty_level or "",
			path.estimated_duration_hours or 0,
			path.total_enrolled or 0,
			path.completed or 0,
			path.in_progress or 0,
			f"{completion_rate:.1f}%",
			f"{path.avg_progress or 0:.1f}%",
			f"{path.avg_time_spent or 0:.1f}h"
		])

	# Create Excel file
	xlsx_file = make_xlsx(data, "Training Paths Report")

	frappe.local.response.filename = f"training_paths_report_{getdate().strftime('%Y%m%d')}.xlsx"
	frappe.local.response.filecontent = xlsx_file.getvalue()
	frappe.local.response.type = "binary"
