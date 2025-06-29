# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.model.document import Document


class CustomerValidator:
	"""Customer validation class for workshop-specific validations"""

	@staticmethod
	def validate_civil_id(civil_id):
		"""Validate Oman Civil ID format (8 digits)"""
		if not civil_id:
			return True  # Optional field

		# Remove any spaces or dashes
		clean_civil_id = re.sub(r"[\s-]", "", civil_id)

		# Check if it's exactly 8 digits
		if not re.match(r"^\d{8}$", clean_civil_id):
			frappe.throw(_("Civil ID must be exactly 8 digits"))

		return True

	@staticmethod
	def validate_emergency_contact(emergency_contact):
		"""Validate emergency contact number for Oman format"""
		if not emergency_contact:
			return True  # Optional field

		# Oman phone number formats:
		# +968 XXXXXXXX (international)
		# 968 XXXXXXXX (without +)
		# XXXXXXXX (local, 8 digits)
		oman_patterns = [
			r"^\+968\s?\d{8}$",  # +968 XXXXXXXX
			r"^968\s?\d{8}$",  # 968 XXXXXXXX
			r"^\d{8}$",  # XXXXXXXX (local)
		]

		is_valid = any(re.match(pattern, emergency_contact.strip()) for pattern in oman_patterns)

		if not is_valid:
			frappe.throw(_("Emergency contact must be a valid Oman phone number (+968 XXXXXXXX)"))

		return True

	@staticmethod
	def validate_arabic_name(customer_name_ar):
		"""Validate Arabic customer name"""
		if not customer_name_ar:
			return True  # Optional field

		# Check if contains Arabic characters
		arabic_pattern = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+")

		if not arabic_pattern.search(customer_name_ar):
			frappe.throw(_("Arabic name must contain Arabic characters"))

		# Check for minimum length
		if len(customer_name_ar.strip()) < 2:
			frappe.throw(_("Arabic name must be at least 2 characters long"))

		return True

	@staticmethod
	def validate_preferred_language(preferred_language):
		"""Validate preferred language selection"""
		valid_languages = ["Arabic", "English", "Both"]

		if preferred_language not in valid_languages:
			frappe.throw(_("Preferred language must be one of: {0}").format(", ".join(valid_languages)))

		return True

	@staticmethod
	def validate_communication_channels(communication_channels):
		"""Validate communication channels data"""
		if not communication_channels:
			return True

		valid_channel_types = ["SMS", "WhatsApp", "Email", "Phone Call", "In Person"]
		primary_count = 0

		for channel in communication_channels:
			# Validate channel type
			if channel.channel_type not in valid_channel_types:
				frappe.throw(_("Invalid communication channel type: {0}").format(channel.channel_type))

			# Count primary channels
			if channel.is_primary:
				primary_count += 1

			# Validate contact value based on channel type
			if channel.channel_type in ["SMS", "WhatsApp", "Phone Call"]:
				CustomerValidator.validate_emergency_contact(channel.contact_value)
			elif channel.channel_type == "Email":
				if channel.contact_value and not re.match(r"^[^@]+@[^@]+\.[^@]+$", channel.contact_value):
					frappe.throw(_("Invalid email address in communication channels"))

		# Ensure only one primary channel
		if primary_count > 1:
			frappe.throw(_("Only one communication channel can be marked as primary"))

		return True

	@staticmethod
	def validate_vehicle_ownership(vehicle_ownership):
		"""Validate vehicle ownership data"""
		if not vehicle_ownership:
			return True

		primary_count = 0

		for vehicle in vehicle_ownership:
			# Count primary vehicles
			if vehicle.primary_vehicle:
				primary_count += 1

			# Validate ownership type
			valid_ownership_types = ["Owner", "Family Member", "Company Vehicle", "Rental"]
			if vehicle.ownership_type not in valid_ownership_types:
				frappe.throw(_("Invalid ownership type: {0}").format(vehicle.ownership_type))

		# Ensure only one primary vehicle
		if primary_count > 1:
			frappe.throw(_("Only one vehicle can be marked as primary"))

		return True

	@staticmethod
	def validate_service_preferences(service_preferences):
		"""Validate service preferences format"""
		if not service_preferences:
			return True

		# Check length
		if len(service_preferences) > 500:
			frappe.throw(_("Service preferences cannot exceed 500 characters"))

		return True

	@staticmethod
	def validate_preferred_service_days(preferred_service_days):
		"""Validate preferred service days"""
		if not preferred_service_days:
			return True

		valid_days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

		for day_pref in preferred_service_days:
			if day_pref.day_of_week not in valid_days:
				frappe.throw(_("Invalid day of week: {0}").format(day_pref.day_of_week))

			valid_preferences = ["Preferred", "Acceptable", "Not Preferred"]
			if day_pref.preference_level not in valid_preferences:
				frappe.throw(_("Invalid preference level: {0}").format(day_pref.preference_level))

		return True

	@staticmethod
	def validate_customer_status(customer_status):
		"""Validate customer status"""
		valid_statuses = ["Active", "Inactive", "VIP", "Blacklisted"]

		if customer_status not in valid_statuses:
			frappe.throw(_("Invalid customer status: {0}").format(customer_status))

		return True


def validate_customer_document(doc, method):
	"""Main validation function called from Customer DocType hooks"""

	# Validate basic fields
	if hasattr(doc, "civil_id"):
		CustomerValidator.validate_civil_id(doc.civil_id)

	if hasattr(doc, "emergency_contact"):
		CustomerValidator.validate_emergency_contact(doc.emergency_contact)

	if hasattr(doc, "customer_name_ar"):
		CustomerValidator.validate_arabic_name(doc.customer_name_ar)

	if hasattr(doc, "preferred_language"):
		CustomerValidator.validate_preferred_language(doc.preferred_language)

	if hasattr(doc, "customer_status"):
		CustomerValidator.validate_customer_status(doc.customer_status)

	# Validate child table data
	if hasattr(doc, "communication_channels"):
		CustomerValidator.validate_communication_channels(doc.communication_channels)

	if hasattr(doc, "vehicle_ownership"):
		CustomerValidator.validate_vehicle_ownership(doc.vehicle_ownership)

	if hasattr(doc, "service_preferences"):
		CustomerValidator.validate_service_preferences(doc.service_preferences)

	if hasattr(doc, "preferred_service_days"):
		CustomerValidator.validate_preferred_service_days(doc.preferred_service_days)


def update_customer_analytics(doc, method):
	"""Update customer analytics when customer is saved"""

	# Set customer since date if not set
	if not getattr(doc, "customer_since_date", None):
		doc.customer_since_date = doc.creation.date() if doc.creation else frappe.utils.today()

	# Calculate analytics (will be implemented in background job for performance)
	calculate_customer_metrics(doc.name)


def calculate_customer_metrics(customer_name):
	"""Calculate customer metrics in background"""
	try:
		# Get all sales invoices for this customer
		sales_data = frappe.db.sql(
			"""
            SELECT
                COUNT(*) as total_services,
                SUM(grand_total) as lifetime_value,
                AVG(grand_total) as average_service_value,
                MAX(posting_date) as last_service_date
            FROM `tabSales Invoice`
            WHERE customer = %s AND docstatus = 1
        """,
			(customer_name,),
			as_dict=True,
		)

		if sales_data and sales_data[0]:
			metrics = sales_data[0]

			# Update customer record
			frappe.db.set_value(
				"Customer",
				customer_name,
				{
					"total_services_count": metrics.total_services or 0,
					"customer_lifetime_value": metrics.lifetime_value or 0.0,
					"average_service_value": metrics.average_service_value or 0.0,
					"last_service_date": metrics.last_service_date,
				},
			)

	except Exception as e:
		frappe.log_error(f"Error calculating customer metrics for {customer_name}: {e!s}")


def add_communication_history_entry(customer, communication_type, subject, summary, direction="Outgoing"):
	"""Add entry to customer communication history"""
	try:
		customer_doc = frappe.get_doc("Customer", customer)

		# Initialize communication_history if not exists
		if not hasattr(customer_doc, "communication_history"):
			return

		# Add new entry
		customer_doc.append(
			"communication_history",
			{
				"communication_date": frappe.utils.now(),
				"communication_type": communication_type,
				"direction": direction,
				"subject": subject,
				"summary": summary,
				"user": frappe.session.user,
			},
		)

		customer_doc.save(ignore_permissions=True)

	except Exception as e:
		frappe.log_error(f"Error adding communication history for {customer}: {e!s}")


@frappe.whitelist()
def get_customer_summary(customer_name):
	"""Get customer summary for dashboard/quick view"""
	try:
		customer = frappe.get_doc("Customer", customer_name)

		# Get recent communications
		recent_communications = []
		if hasattr(customer, "communication_history"):
			recent_communications = sorted(
				customer.communication_history, key=lambda x: x.communication_date, reverse=True
			)[:5]

		# Get vehicle information
		vehicles = []
		if hasattr(customer, "vehicle_ownership"):
			for vehicle_ownership in customer.vehicle_ownership:
				vehicle_info = frappe.get_doc("Vehicle", vehicle_ownership.vehicle)
				vehicles.append(
					{
						"vehicle_name": vehicle_info.name,
						"make_model": f"{vehicle_info.make} {vehicle_info.model}",
						"license_plate": vehicle_info.license_plate,
						"ownership_type": vehicle_ownership.ownership_type,
						"is_primary": vehicle_ownership.primary_vehicle,
					}
				)

		return {
			"customer_name": customer.customer_name,
			"customer_name_ar": getattr(customer, "customer_name_ar", ""),
			"preferred_language": getattr(customer, "preferred_language", "Arabic"),
			"customer_status": getattr(customer, "customer_status", "Active"),
			"total_services": getattr(customer, "total_services_count", 0),
			"lifetime_value": getattr(customer, "customer_lifetime_value", 0.0),
			"last_service_date": getattr(customer, "last_service_date", None),
			"vehicles": vehicles,
			"recent_communications": recent_communications,
		}

	except Exception as e:
		frappe.log_error(f"Error getting customer summary for {customer_name}: {e!s}")
		return {"error": str(e)}
