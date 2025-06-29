import frappe
from frappe import _


def get_context(context):
	"""Get context data for customer analytics dashboard"""

	# Set page title and meta
	context.title = _("Customer Analytics Dashboard")
	context.page_title = _("Customer Analytics Dashboard")

	# Check permissions
	if not frappe.has_permission("Customer Analytics", "read"):
		frappe.throw(_("Insufficient permissions to view customer analytics"), frappe.PermissionError)

	# Get current language for RTL layout
	context.is_arabic = frappe.local.lang == "ar"
	context.text_direction = "rtl" if context.is_arabic else "ltr"

	# Dashboard configuration
	context.show_create_button = False
	context.no_breadcrumbs = False

	# Include required scripts and styles
	context.include_js = [
		"/assets/frappe/js/lib/frappe-charts.min.iife.js",
		"/assets/universal_workshop/js/customer_analytics_dashboard.js",
	]

	context.include_css = ["/assets/universal_workshop/css/customer_analytics_dashboard.css"]

	return context
