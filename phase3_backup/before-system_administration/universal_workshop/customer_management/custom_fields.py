# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def create_customer_custom_fields():
	"""Create custom fields for ERPNext Customer DocType"""

	customer_custom_fields = {
		"Customer": [
			# Workshop Information Section
			{
				"fieldname": "workshop_information_section",
				"fieldtype": "Section Break",
				"label": _("Workshop Information"),
				"insert_after": "customer_details",
			},
			# Customer Names in Arabic
			{
				"fieldname": "customer_name_ar",
				"fieldtype": "Data",
				"label": _("Customer Name (Arabic)"),
				"insert_after": "workshop_information_section",
				"translatable": 1,
				"in_list_view": 1,
				"description": _("Customer name in Arabic"),
			},
			# Civil ID (Oman)
			{
				"fieldname": "civil_id",
				"fieldtype": "Data",
				"label": _("Civil ID"),
				"insert_after": "customer_name_ar",
				"description": _("Oman Civil ID (8 digits)"),
				"length": 8,
			},
			# Nationality
			{
				"fieldname": "nationality",
				"fieldtype": "Link",
				"label": _("Nationality"),
				"options": "Country",
				"insert_after": "civil_id",
				"default": "Oman",
			},
			{
				"fieldname": "column_break_workshop_1",
				"fieldtype": "Column Break",
				"insert_after": "nationality",
			},
			# Preferred Language
			{
				"fieldname": "preferred_language",
				"fieldtype": "Select",
				"label": _("Preferred Language"),
				"options": "Arabic\nEnglish\nBoth",
				"insert_after": "column_break_workshop_1",
				"default": "Arabic",
				"reqd": 1,
			},
			# Communication Channels
			{
				"fieldname": "communication_channels",
				"fieldtype": "Table",
				"label": _("Communication Channels"),
				"options": "Customer Communication Channel",
				"insert_after": "preferred_language",
				"description": _("Preferred communication methods"),
			},
			# Emergency Contact
			{
				"fieldname": "emergency_contact",
				"fieldtype": "Data",
				"label": _("Emergency Contact"),
				"insert_after": "communication_channels",
				"description": _("Emergency contact number (+968 format)"),
			},
			# Vehicle Information Section
			{
				"fieldname": "vehicle_information_section",
				"fieldtype": "Section Break",
				"label": _("Vehicle Information"),
				"insert_after": "emergency_contact",
			},
			# Vehicle Ownership Table
			{
				"fieldname": "vehicle_ownership",
				"fieldtype": "Table",
				"label": _("Vehicle Ownership"),
				"options": "Customer Vehicle Ownership",
				"insert_after": "vehicle_information_section",
				"description": _("Vehicles owned by this customer"),
			},
			# Service Preferences Section
			{
				"fieldname": "service_preferences_section",
				"fieldtype": "Section Break",
				"label": _("Service Preferences"),
				"insert_after": "vehicle_ownership",
			},
			# Service Preferences
			{
				"fieldname": "service_preferences",
				"fieldtype": "Small Text",
				"label": _("Service Preferences"),
				"insert_after": "service_preferences_section",
				"description": _("Customer service preferences and special requirements"),
			},
			# Preferred Service Days
			{
				"fieldname": "preferred_service_days",
				"fieldtype": "Table",
				"label": _("Preferred Service Days"),
				"options": "Customer Service Day",
				"insert_after": "service_preferences",
			},
			{
				"fieldname": "column_break_service_1",
				"fieldtype": "Column Break",
				"insert_after": "preferred_service_days",
			},
			# Preferred Service Time
			{
				"fieldname": "preferred_service_time",
				"fieldtype": "Select",
				"label": _("Preferred Service Time"),
				"options": "Morning (8AM-12PM)\nAfternoon (12PM-4PM)\nEvening (4PM-8PM)\nAny Time",
				"insert_after": "column_break_service_1",
				"default": "Any Time",
			},
			# Service Reminders
			{
				"fieldname": "service_reminders_enabled",
				"fieldtype": "Check",
				"label": _("Enable Service Reminders"),
				"insert_after": "preferred_service_time",
				"default": 1,
			},
			# Communication History Section
			{
				"fieldname": "communication_history_section",
				"fieldtype": "Section Break",
				"label": _("Communication History"),
				"insert_after": "service_reminders_enabled",
			},
			# Communication History Table
			{
				"fieldname": "communication_history",
				"fieldtype": "Table",
				"label": _("Communication History"),
				"options": "Customer Communication History",
				"insert_after": "communication_history_section",
				"description": _("History of communications with customer"),
			},
			# Customer Analytics Section
			{
				"fieldname": "customer_analytics_section",
				"fieldtype": "Section Break",
				"label": _("Customer Analytics"),
				"insert_after": "communication_history",
			},
			# Last Service Date
			{
				"fieldname": "last_service_date",
				"fieldtype": "Date",
				"label": _("Last Service Date"),
				"insert_after": "customer_analytics_section",
				"read_only": 1,
			},
			# Total Services Count
			{
				"fieldname": "total_services_count",
				"fieldtype": "Int",
				"label": _("Total Services"),
				"insert_after": "last_service_date",
				"read_only": 1,
				"default": 0,
			},
			# Customer Since
			{
				"fieldname": "customer_since_date",
				"fieldtype": "Date",
				"label": _("Customer Since"),
				"insert_after": "total_services_count",
				"read_only": 1,
			},
			{
				"fieldname": "column_break_analytics_1",
				"fieldtype": "Column Break",
				"insert_after": "customer_since_date",
			},
			# Lifetime Value
			{
				"fieldname": "customer_lifetime_value",
				"fieldtype": "Currency",
				"label": _("Lifetime Value (OMR)"),
				"insert_after": "column_break_analytics_1",
				"read_only": 1,
				"default": 0.0,
			},
			# Average Service Value
			{
				"fieldname": "average_service_value",
				"fieldtype": "Currency",
				"label": _("Average Service Value (OMR)"),
				"insert_after": "customer_lifetime_value",
				"read_only": 1,
				"default": 0.0,
			},
			# Customer Status
			{
				"fieldname": "customer_status",
				"fieldtype": "Select",
				"label": _("Customer Status"),
				"options": "Active\nInactive\nVIP\nBlacklisted",
				"insert_after": "average_service_value",
				"default": "Active",
			},
			# Notes Section
			{
				"fieldname": "customer_notes_section",
				"fieldtype": "Section Break",
				"label": _("Customer Notes"),
				"insert_after": "customer_status",
			},
			# Customer Notes
			{
				"fieldname": "customer_notes",
				"fieldtype": "Text Editor",
				"label": _("Customer Notes"),
				"insert_after": "customer_notes_section",
				"description": _("Internal notes about the customer"),
			},
			# Special Instructions
			{
				"fieldname": "special_instructions",
				"fieldtype": "Small Text",
				"label": _("Special Instructions"),
				"insert_after": "customer_notes",
				"description": _("Special handling instructions for this customer"),
			},
		]
	}

	return customer_custom_fields


def install_customer_custom_fields():
	"""Install custom fields for Customer DocType"""
	try:
		custom_fields = create_customer_custom_fields()
		create_custom_fields(custom_fields, update=True)
		frappe.msgprint(_("Customer custom fields installed successfully"))
		return True
	except Exception as e:
		frappe.log_error(f"Error installing customer custom fields: {e!s}")
		frappe.throw(_("Failed to install customer custom fields: {0}").format(str(e)))
		return False


def create_child_doctypes():
	"""Create child DocTypes for Customer custom fields"""

	# Customer Vehicle Ownership Child Table
	vehicle_ownership_doctype = {
		"doctype": "DocType",
		"name": "Customer Vehicle Ownership",
		"module": "Selling",
		"istable": 1,
		"fields": [
			{
				"fieldname": "vehicle",
				"fieldtype": "Link",
				"label": _("Vehicle"),
				"options": "Vehicle",
				"in_list_view": 1,
				"reqd": 1,
			},
			{
				"fieldname": "ownership_type",
				"fieldtype": "Select",
				"label": _("Ownership Type"),
				"options": "Owner\nFamily Member\nCompany Vehicle\nRental",
				"in_list_view": 1,
				"default": "Owner",
			},
			{
				"fieldname": "primary_vehicle",
				"fieldtype": "Check",
				"label": _("Primary Vehicle"),
				"default": 0,
			},
			{
				"fieldname": "relationship",
				"fieldtype": "Data",
				"label": _("Relationship"),
				"description": _("Relationship to vehicle owner"),
			},
			{"fieldname": "notes", "fieldtype": "Small Text", "label": _("Notes")},
		],
	}

	# Customer Communication Channel Child Table
	communication_channel_doctype = {
		"doctype": "DocType",
		"name": "Customer Communication Channel",
		"module": "Selling",
		"istable": 1,
		"fields": [
			{
				"fieldname": "channel_type",
				"fieldtype": "Select",
				"label": _("Channel Type"),
				"options": "SMS\nWhatsApp\nEmail\nPhone Call\nIn Person",
				"in_list_view": 1,
				"reqd": 1,
			},
			{
				"fieldname": "contact_value",
				"fieldtype": "Data",
				"label": _("Contact Value"),
				"in_list_view": 1,
			},
			{"fieldname": "is_primary", "fieldtype": "Check", "label": _("Primary"), "default": 0},
			{"fieldname": "notes", "fieldtype": "Small Text", "label": _("Notes")},
		],
	}

	# Customer Service Day Child Table
	service_day_doctype = {
		"doctype": "DocType",
		"name": "Customer Service Day",
		"module": "Selling",
		"istable": 1,
		"fields": [
			{
				"fieldname": "day_of_week",
				"fieldtype": "Select",
				"label": _("Day of Week"),
				"options": "Sunday\nMonday\nTuesday\nWednesday\nThursday\nFriday\nSaturday",
				"in_list_view": 1,
				"reqd": 1,
			},
			{
				"fieldname": "preference_level",
				"fieldtype": "Select",
				"label": _("Preference"),
				"options": "Preferred\nAcceptable\nNot Preferred",
				"default": "Preferred",
			},
		],
	}

	# Customer Communication History Child Table
	communication_history_doctype = {
		"doctype": "DocType",
		"name": "Customer Communication History",
		"module": "Selling",
		"istable": 1,
		"fields": [
			{
				"fieldname": "communication_date",
				"fieldtype": "Datetime",
				"label": _("Date & Time"),
				"in_list_view": 1,
				"reqd": 1,
				"default": "now",
			},
			{
				"fieldname": "communication_type",
				"fieldtype": "Select",
				"label": _("Type"),
				"options": "Phone Call\nSMS\nWhatsApp\nEmail\nIn Person\nService Reminder\nComplaint\nFeedback",
				"in_list_view": 1,
				"reqd": 1,
			},
			{
				"fieldname": "direction",
				"fieldtype": "Select",
				"label": _("Direction"),
				"options": "Incoming\nOutgoing",
				"in_list_view": 1,
				"default": "Outgoing",
			},
			{"fieldname": "subject", "fieldtype": "Data", "label": _("Subject"), "in_list_view": 1},
			{"fieldname": "summary", "fieldtype": "Small Text", "label": _("Summary"), "reqd": 1},
			{
				"fieldname": "follow_up_required",
				"fieldtype": "Check",
				"label": _("Follow-up Required"),
				"default": 0,
			},
			{"fieldname": "follow_up_date", "fieldtype": "Date", "label": _("Follow-up Date")},
			{
				"fieldname": "user",
				"fieldtype": "Link",
				"label": _("User"),
				"options": "User",
				"default": "user",
			},
		],
	}

	# Create DocTypes
	doctypes_to_create = [
		vehicle_ownership_doctype,
		communication_channel_doctype,
		service_day_doctype,
		communication_history_doctype,
	]

	for doctype_dict in doctypes_to_create:
		if not frappe.db.exists("DocType", doctype_dict["name"]):
			doctype = frappe.new_doc("DocType")
			doctype.update(doctype_dict)
			doctype.insert()
			frappe.db.commit()


def setup_customer_extensions():
	"""Main setup function for customer extensions"""
	try:
		# Create child DocTypes first
		create_child_doctypes()

		# Install custom fields
		install_customer_custom_fields()

		frappe.msgprint(_("Customer management extensions installed successfully"))
		return True

	except Exception as e:
		frappe.log_error(f"Error setting up customer extensions: {e!s}")
		frappe.throw(_("Failed to setup customer extensions: {0}").format(str(e)))
		return False
