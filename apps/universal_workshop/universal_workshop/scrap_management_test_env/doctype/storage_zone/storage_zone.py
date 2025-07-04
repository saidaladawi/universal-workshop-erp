# Copyright (c) 2024, Universal Workshop and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, now_datetime, today


class StorageZone(Document):
	# pylint: disable=no-member
	# Frappe framework dynamically adds DocType fields to Document class

	def validate(self):
		"""Validate storage zone data before saving"""
		self.validate_zone_code()
		self.validate_arabic_fields()
		self.validate_capacity()
		self.validate_allowed_categories()
		self.calculate_utilization()

	def before_save(self):
		"""Set default values before saving"""
		if not self.created_by:
			self.created_by = frappe.session.user
		if not self.created_date:
			self.created_date = now_datetime()

		# Update metadata
		self.last_modified_by = frappe.session.user
		self.last_modified_date = now_datetime()

		# Auto-generate zone code if not provided
		if not self.zone_code:
			self.zone_code = self.generate_zone_code()

		# Set accessibility based on height
		if self.height_meters and self.height_meters > 3.0:
			self.requires_ladder = 1
		if self.height_meters and self.height_meters > 5.0:
			self.requires_crane = 1

	def validate_zone_code(self):
		"""Validate zone code format"""
		if self.zone_code:
			if not re.match(r"^[A-Z]{1,3}-\d{2,3}$", self.zone_code):
				frappe.throw(_("Zone code must be in format 'A-01' or 'ABC-123'"))

	def validate_arabic_fields(self):
		"""Validate Arabic language fields"""
		if not self.zone_name_ar:
			frappe.throw(_("Arabic zone name is required"))

		# Validate Arabic characters
		if self.zone_name_ar and not self.contains_arabic(self.zone_name_ar):
			frappe.throw(_("Zone name Arabic field must contain Arabic characters"))

	def contains_arabic(self, text):
		"""Check if text contains Arabic characters"""
		if not text:
			return False
		arabic_pattern = re.compile(r"[\u0600-\u06FF\u0750-\u077F]")
		return bool(arabic_pattern.search(text))

	def validate_capacity(self):
		"""Validate capacity and dimensions"""
		if self.max_capacity and self.max_capacity <= 0:
			frappe.throw(_("Maximum capacity must be greater than 0"))

		if self.current_capacity and self.current_capacity < 0:
			frappe.throw(_("Current capacity cannot be negative"))

		if self.max_capacity and self.current_capacity:
			if self.current_capacity > self.max_capacity:
				frappe.throw(_("Current capacity cannot exceed maximum capacity"))

		# Validate dimensions
		if self.length_meters and self.length_meters <= 0:
			frappe.throw(_("Length must be greater than 0"))
		if self.width_meters and self.width_meters <= 0:
			frappe.throw(_("Width must be greater than 0"))
		if self.height_meters and self.height_meters <= 0:
			frappe.throw(_("Height must be greater than 0"))

	def validate_allowed_categories(self):
		"""Validate allowed part categories"""
		if not self.allowed_categories:
			frappe.throw(_("At least one allowed part category is required"))

		# Check for duplicates
		categories = [cat.part_category for cat in self.allowed_categories]
		if len(categories) != len(set(categories)):
			frappe.throw(_("Duplicate part categories are not allowed"))

		# Validate restricted categories
		restricted_count = sum(1 for cat in self.allowed_categories if cat.is_restricted)
		if self.zone_type == "General" and restricted_count > 0:
			frappe.throw(_("General zones cannot have restricted part categories"))

	def calculate_utilization(self):
		"""Calculate zone utilization percentage"""
		if self.max_capacity and self.current_capacity:
			self.utilization_percentage = (self.current_capacity / self.max_capacity) * 100
		else:
			self.utilization_percentage = 0

	def generate_zone_code(self):
		"""Generate unique zone code"""
		# Get zone type prefix
		zone_prefixes = {"General": "GEN", "Hazmat": "HAZ", "Secure": "SEC", "Climate": "CLI", "Heavy": "HVY"}

		prefix = zone_prefixes.get(self.zone_type, "GEN")

		# Get next number for this prefix
		existing_zones = frappe.db.sql(
			"""
            SELECT zone_code FROM `tabStorage Zone`
            WHERE zone_code LIKE %s
            ORDER BY zone_code DESC LIMIT 1
        """,
			[f"{prefix}-%"],
		)

		if existing_zones:
			last_code = existing_zones[0][0]
			last_num = int(last_code.split("-")[1])
			new_num = last_num + 1
		else:
			new_num = 1

		return f"{prefix}-{new_num:02d}"

	def generate_barcode(self):
		"""Generate barcode for zone identification"""
		if not self.zone_code:
			frappe.throw(_("Zone code is required to generate barcode"))

		# Use zone code as barcode
		self.barcode = self.zone_code
		return self.barcode

	def get_available_capacity(self):
		"""Get available capacity in the zone"""
		if not self.max_capacity:
			return 0
		return self.max_capacity - (self.current_capacity or 0)

	def get_utilization_status(self):
		"""Get utilization status description"""
		utilization = self.utilization_percentage or 0

		if utilization >= 95:
			return "Critical"
		elif utilization >= 80:
			return "High"
		elif utilization >= 60:
			return "Medium"
		elif utilization >= 30:
			return "Low"
		else:
			return "Very Low"

	def can_accommodate_part(self, part_category, weight_kg=0):
		"""Check if zone can accommodate a part"""
		# Check if category is allowed
		allowed_categories = [cat.part_category for cat in self.allowed_categories]
		if part_category not in allowed_categories:
			return False, _("Part category not allowed in this zone")

		# Check capacity
		if self.get_available_capacity() <= 0:
			return False, _("Zone is at maximum capacity")

		# Check weight limits
		if self.max_weight_kg and weight_kg > self.max_weight_kg:
			return False, _("Part exceeds zone weight limit")

		return True, _("Zone can accommodate this part")

	def add_part_to_zone(self, part_storage_location):
		"""Add a part to this zone"""
		can_add, message = self.can_accommodate_part(
			part_storage_location.part_category, part_storage_location.weight_kg or 0
		)

		if not can_add:
			frappe.throw(message)

		# Update current capacity
		self.current_capacity = (self.current_capacity or 0) + 1
		self.save()

		# Log the addition
		self.log_activity(f"Part {part_storage_location.part_code} added to zone")

	def remove_part_from_zone(self, part_storage_location):
		"""Remove a part from this zone"""
		if self.current_capacity and self.current_capacity > 0:
			self.current_capacity -= 1
			self.save()

			# Log the removal
			self.log_activity(f"Part {part_storage_location.part_code} removed from zone")

	def log_activity(self, description):
		"""Log zone activity"""
		frappe.get_doc(
			{
				"doctype": "Storage Zone Activity Log",
				"storage_zone": self.name,
				"activity_date": now_datetime(),
				"activity_type": "Part Movement",
				"description": description,
				"performed_by": frappe.session.user,
			}
		).insert(ignore_permissions=True)

	def get_zone_report(self):
		"""Generate zone utilization report"""
		# Get parts in this zone
		parts_in_zone = frappe.get_list(
			"Part Storage Location",
			filters={"storage_zone": self.name, "status": "Stored"},
			fields=["part_category", "weight_kg", "estimated_value"],
		)

		# Group by category
		category_summary = {}
		total_value = 0
		total_weight = 0

		for part in parts_in_zone:
			category = part.part_category
			if category not in category_summary:
				category_summary[category] = {"count": 0, "total_weight": 0, "total_value": 0}

			category_summary[category]["count"] += 1
			category_summary[category]["total_weight"] += part.weight_kg or 0
			category_summary[category]["total_value"] += part.estimated_value or 0

			total_weight += part.weight_kg or 0
			total_value += part.estimated_value or 0

		return {
			"zone_info": {
				"zone_code": self.zone_code,
				"zone_name": self.zone_name,
				"zone_type": self.zone_type,
				"utilization": self.utilization_percentage,
				"status": self.get_utilization_status(),
			},
			"summary": {
				"total_parts": len(parts_in_zone),
				"total_weight_kg": total_weight,
				"total_value_omr": total_value,
				"available_capacity": self.get_available_capacity(),
			},
			"by_category": category_summary,
		}

	@frappe.whitelist()
	def generate_zone_labels(self):
		"""Generate printable zone labels"""
		return {
			"zone_code": self.zone_code,
			"zone_name": self.zone_name,
			"zone_name_ar": self.zone_name_ar,
			"barcode": self.barcode or self.generate_barcode(),
			"location": self.location,
			"zone_type": self.zone_type,
			"max_capacity": self.max_capacity,
			"safety_notes": self.safety_requirements,
		}


# Utility functions for zone management
@frappe.whitelist()
def get_available_zones(part_category=None, weight_kg=0):
	"""Get list of zones that can accommodate a part"""
	filters = {"status": "Active"}

	zones = frappe.get_list(
		"Storage Zone",
		filters=filters,
		fields=[
			"name",
			"zone_code",
			"zone_name",
			"zone_type",
			"max_capacity",
			"current_capacity",
			"utilization_percentage",
		],
	)

	available_zones = []
	for zone_data in zones:
		zone = frappe.get_doc("Storage Zone", zone_data.name)
		if part_category:
			can_accommodate, _ = zone.can_accommodate_part(part_category, weight_kg)
			if can_accommodate:
				available_zones.append(zone_data)
		else:
			if zone.get_available_capacity() > 0:
				available_zones.append(zone_data)

	return available_zones


@frappe.whitelist()
def get_zone_utilization_summary():
	"""Get overall zone utilization summary"""
	zones = frappe.get_all(
		"Storage Zone",
		filters={"status": "Active"},
		fields=[
			"zone_code",
			"zone_name",
			"zone_type",
			"max_capacity",
			"current_capacity",
			"utilization_percentage",
		],
	)

	summary = {
		"total_zones": len(zones),
		"total_capacity": sum(z.max_capacity or 0 for z in zones),
		"total_used": sum(z.current_capacity or 0 for z in zones),
		"by_type": {},
		"utilization_bands": {
			"critical": 0,  # 95%+
			"high": 0,  # 80-94%
			"medium": 0,  # 60-79%
			"low": 0,  # 30-59%
			"very_low": 0,  # <30%
		},
	}

	for zone in zones:
		# Group by type
		zone_type = zone.zone_type
		if zone_type not in summary["by_type"]:
			summary["by_type"][zone_type] = {"count": 0, "capacity": 0, "used": 0}

		summary["by_type"][zone_type]["count"] += 1
		summary["by_type"][zone_type]["capacity"] += zone.max_capacity or 0
		summary["by_type"][zone_type]["used"] += zone.current_capacity or 0

		# Group by utilization
		utilization = zone.utilization_percentage or 0
		if utilization >= 95:
			summary["utilization_bands"]["critical"] += 1
		elif utilization >= 80:
			summary["utilization_bands"]["high"] += 1
		elif utilization >= 60:
			summary["utilization_bands"]["medium"] += 1
		elif utilization >= 30:
			summary["utilization_bands"]["low"] += 1
		else:
			summary["utilization_bands"]["very_low"] += 1

	# Calculate overall utilization
	if summary["total_capacity"] > 0:
		summary["overall_utilization"] = (summary["total_used"] / summary["total_capacity"]) * 100
	else:
		summary["overall_utilization"] = 0

	return summary
