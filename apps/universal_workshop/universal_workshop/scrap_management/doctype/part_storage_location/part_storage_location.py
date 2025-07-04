# Copyright (c) 2024, Universal Workshop and contributors
# For license information, please see license.txt

import re
import uuid

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, now_datetime, today


class PartStorageLocation(Document):
	# pylint: disable=no-member
	# Frappe framework dynamically adds DocType fields to Document class

	def validate(self):
		"""Validate part storage location data before saving"""
		self.validate_part_code()
		self.validate_barcode_uniqueness()
		self.validate_storage_zone_compatibility()
		self.validate_financial_data()
		self.update_current_location()

	def before_save(self):
		"""Set default values before saving"""
		if not self.created_by:
			self.created_by = frappe.session.user
		if not self.created_date:
			self.created_date = now_datetime()

		# Update metadata
		self.last_modified_by = frappe.session.user
		self.last_modified_date = now_datetime()

		# Generate barcode and QR code if not provided
		if not self.barcode:
			self.barcode = self.generate_barcode()
		if not self.qr_code:
			self.qr_code = self.generate_qr_code()

		# Set next inspection date (30 days from storage)
		if not self.next_inspection_date and self.date_stored:
			from frappe.utils import add_days, getdate

			self.next_inspection_date = add_days(getdate(self.date_stored), 30)

	def after_insert(self):
		"""Actions after part is stored"""
		self.update_zone_capacity()
		self.log_movement("Initial Storage", None, self.get_full_location())

	def before_cancel(self):
		"""Actions before part storage is cancelled"""
		self.update_zone_capacity(remove=True)

	def validate_part_code(self):
		"""Validate part code format and uniqueness"""
		if not self.part_code:
			frappe.throw(_("Part code is required"))

		# Validate format (e.g., PSL-2024-00001)
		if not re.match(r"^PSL-\d{4}-\d{5}$", self.part_code):
			frappe.throw(_("Part code must be in format 'PSL-YYYY-NNNNN'"))

	def validate_barcode_uniqueness(self):
		"""Ensure barcode is unique across all parts"""
		if self.barcode:
			existing = frappe.db.exists(
				"Part Storage Location", {"barcode": self.barcode, "name": ("!=", self.name or "")}
			)
			if existing:
				frappe.throw(_("Barcode must be unique"))

	def validate_storage_zone_compatibility(self):
		"""Validate part can be stored in selected zone"""
		if self.storage_zone and self.part_category:
			zone = frappe.get_doc("Storage Zone", self.storage_zone)
			can_accommodate, message = zone.can_accommodate_part(self.part_category, self.weight_kg or 0)
			if not can_accommodate:
				frappe.throw(message)

	def validate_financial_data(self):
		"""Validate financial information"""
		if self.estimated_value and self.estimated_value < 0:
			frappe.throw(_("Estimated value cannot be negative"))

		if self.storage_cost_per_month and self.storage_cost_per_month < 0:
			frappe.throw(_("Storage cost cannot be negative"))

		if self.insurance_value and self.insurance_value < 0:
			frappe.throw(_("Insurance value cannot be negative"))

		if self.depreciation_rate:
			if self.depreciation_rate < 0 or self.depreciation_rate > 100:
				frappe.throw(_("Depreciation rate must be between 0 and 100"))

	def update_current_location(self):
		"""Update current location description"""
		location_parts = []

		if self.storage_zone:
			zone_name = frappe.db.get_value("Storage Zone", self.storage_zone, "zone_name")
			location_parts.append(zone_name)

		if self.rack_number:
			location_parts.append(f"Rack {self.rack_number}")

		if self.shelf_level:
			location_parts.append(f"Shelf {self.shelf_level}")

		if self.bin_position:
			location_parts.append(f"Bin {self.bin_position}")

		self.current_location = " | ".join(location_parts)

	def generate_barcode(self):
		"""Generate unique barcode for the part"""
		if not self.part_code:
			return None

		# Use part code as base for barcode
		return self.part_code.replace("-", "")

	def generate_qr_code(self):
		"""Generate QR code data for the part"""
		if not self.part_code:
			return None

		qr_data = {
			"part_code": self.part_code,
			"item_name": self.item_name,
			"zone": self.storage_zone,
			"location": self.current_location,
			"condition": self.condition_grade,
		}

		import json

		return json.dumps(qr_data)

	def get_full_location(self):
		"""Get complete location string"""
		return self.current_location or "Unknown Location"

	def update_zone_capacity(self, remove=False):
		"""Update storage zone capacity"""
		if self.storage_zone:
			zone = frappe.get_doc("Storage Zone", self.storage_zone)
			if remove:
				zone.remove_part_from_zone(self)
			else:
				zone.add_part_to_zone(self)

	def log_movement(self, movement_type, from_location, to_location, reason=None, notes=None):
		"""Log part movement in history"""
		movement_entry = {
			"movement_date": now_datetime(),
			"movement_type": movement_type,
			"from_location": from_location,
			"to_location": to_location,
			"moved_by": frappe.session.user,
			"reason": reason,
			"notes": notes,
		}

		self.append("movement_history", movement_entry)
		self.movement_count = (self.movement_count or 0) + 1
		self.last_moved_date = now_datetime()

	def move_to_location(
		self, new_zone, new_rack=None, new_shelf=None, new_bin=None, reason=None, notes=None
	):
		"""Move part to new location"""
		old_location = self.get_full_location()
		old_zone = self.storage_zone

		# Validate new zone can accommodate the part
		if new_zone != self.storage_zone:
			zone = frappe.get_doc("Storage Zone", new_zone)
			can_accommodate, message = zone.can_accommodate_part(self.part_category, self.weight_kg or 0)
			if not can_accommodate:
				frappe.throw(message)

		# Update location details
		self.storage_zone = new_zone
		if new_rack is not None:
			self.rack_number = new_rack
		if new_shelf is not None:
			self.shelf_level = new_shelf
		if new_bin is not None:
			self.bin_position = new_bin

		# Update current location string
		self.update_current_location()
		new_location = self.get_full_location()

		# Update zone capacities
		if old_zone != new_zone:
			if old_zone:
				old_zone_doc = frappe.get_doc("Storage Zone", old_zone)
				old_zone_doc.remove_part_from_zone(self)

			new_zone_doc = frappe.get_doc("Storage Zone", new_zone)
			new_zone_doc.add_part_to_zone(self)

		# Log the movement
		self.log_movement(
			"Zone Transfer" if old_zone != new_zone else "Position Change",
			old_location,
			new_location,
			reason,
			notes,
		)

		self.save()

	def calculate_current_value(self):
		"""Calculate current value with depreciation"""
		if not self.estimated_value or not self.depreciation_rate:
			return self.estimated_value or 0

		from frappe.utils import date_diff, getdate

		# Calculate months since storage
		months_stored = date_diff(today(), self.date_stored) / 30.44  # Average days per month

		# Apply monthly depreciation
		depreciated_value = self.estimated_value * ((100 - self.depreciation_rate) / 100) ** months_stored

		return max(depreciated_value, 0)

	def get_storage_cost_to_date(self):
		"""Calculate total storage cost since storage date"""
		if not self.storage_cost_per_month:
			return 0

		months_stored = date_diff(today(), self.date_stored) / 30.44
		return self.storage_cost_per_month * months_stored

	def is_due_for_inspection(self):
		"""Check if part is due for inspection"""
		if not self.next_inspection_date:
			return True

		from frappe.utils import getdate

		return getdate(self.next_inspection_date) <= getdate(today())

	def update_inspection_dates(self, inspection_notes=None):
		"""Update inspection dates after inspection"""
		from frappe.utils import add_days

		self.last_inspection_date = today()
		self.next_inspection_date = add_days(today(), 30)

		if inspection_notes:
			if not self.storage_notes:
				self.storage_notes = ""
			self.storage_notes += f"\n[{today()}] Inspection: {inspection_notes}"

		self.save()

	def mark_as_sold(self, sale_price, buyer_info=None):
		"""Mark part as sold and update status"""
		self.status = "Sold"
		if hasattr(self, "final_sale_price"):
			self.final_sale_price = sale_price

		# Log the sale
		self.log_movement("Sale", self.get_full_location(), "Sold", f"Sold for {sale_price} OMR", buyer_info)

		# Update zone capacity
		self.update_zone_capacity(remove=True)

		self.save()

	def mark_as_disposed(self, disposal_reason, disposal_method=None):
		"""Mark part as disposed"""
		self.status = "Disposed"

		# Log the disposal
		self.log_movement("Disposal", self.get_full_location(), "Disposed", disposal_reason, disposal_method)

		# Update zone capacity
		self.update_zone_capacity(remove=True)

		self.save()

	@frappe.whitelist()
	def get_part_summary(self):
		"""Get comprehensive part summary"""
		return {
			"basic_info": {
				"part_code": self.part_code,
				"item_name": self.item_name,
				"item_name_ar": self.item_name_ar,
				"category": self.part_category,
				"condition": self.condition_grade,
				"status": self.status,
			},
			"location_info": {
				"current_location": self.current_location,
				"storage_zone": self.storage_zone,
				"coordinates": self.coordinates,
				"accessible": self.accessible_position,
			},
			"financial_info": {
				"estimated_value": self.estimated_value,
				"current_value": self.calculate_current_value(),
				"storage_cost_to_date": self.get_storage_cost_to_date(),
				"market_demand": self.market_demand,
				"priority_to_sell": self.priority_to_sell,
			},
			"vehicle_info": {
				"make": self.vehicle_make,
				"model": self.vehicle_model,
				"year": self.vehicle_year,
				"original_vehicle": self.original_vehicle,
			},
			"storage_info": {
				"date_stored": self.date_stored,
				"last_moved": self.last_moved_date,
				"movement_count": self.movement_count,
				"due_for_inspection": self.is_due_for_inspection(),
			},
		}


# Utility functions for part storage management
@frappe.whitelist()
def find_optimal_storage_location(part_category, weight_kg=0, requires_special_handling=False):
	"""Find optimal storage location for a part"""
	filters = {"status": "Active"}

	# Get available zones that can accommodate this part
	zones = frappe.get_list(
		"Storage Zone", filters=filters, fields=["name", "zone_code", "zone_name", "utilization_percentage"]
	)

	suitable_zones = []
	for zone_data in zones:
		zone = frappe.get_doc("Storage Zone", zone_data.name)
		can_accommodate, _ = zone.can_accommodate_part(part_category, weight_kg)
		if can_accommodate:
			# Add suitability score based on utilization
			utilization = zone_data.utilization_percentage or 0
			# Prefer zones with 60-80% utilization (not too empty, not too full)
			if 60 <= utilization <= 80:
				score = 100
			elif utilization < 60:
				score = 80 - utilization  # Prefer fuller zones among empty ones
			else:
				score = 100 - utilization  # Prefer emptier zones among full ones

			suitable_zones.append(
				{**zone_data, "suitability_score": score, "available_capacity": zone.get_available_capacity()}
			)

	# Sort by suitability score
	suitable_zones.sort(key=lambda x: x["suitability_score"], reverse=True)

	return suitable_zones[:5]  # Return top 5 recommendations


@frappe.whitelist()
def get_parts_due_for_inspection():
	"""Get list of parts due for inspection"""
	parts = frappe.get_list(
		"Part Storage Location",
		filters={"status": "Stored", "next_inspection_date": ["<=", today()]},
		fields=[
			"name",
			"part_code",
			"item_name",
			"storage_zone",
			"current_location",
			"last_inspection_date",
			"next_inspection_date",
		],
		order_by="next_inspection_date",
	)

	return parts


@frappe.whitelist()
def get_storage_analytics():
	"""Get storage analytics and insights"""
	# Get all stored parts
	parts = frappe.get_all(
		"Part Storage Location",
		filters={"status": "Stored"},
		fields=[
			"part_category",
			"estimated_value",
			"storage_cost_per_month",
			"market_demand",
			"priority_to_sell",
			"date_stored",
			"weight_kg",
		],
	)

	analytics = {
		"overview": {
			"total_parts": len(parts),
			"total_value": sum(p.estimated_value or 0 for p in parts),
			"total_weight": sum(p.weight_kg or 0 for p in parts),
			"monthly_storage_cost": sum(p.storage_cost_per_month or 0 for p in parts),
		},
		"by_category": {},
		"by_demand": {},
		"by_priority": {},
		"aging_analysis": {
			"0_30_days": 0,
			"31_90_days": 0,
			"91_180_days": 0,
			"181_365_days": 0,
			"over_365_days": 0,
		},
	}

	for part in parts:
		# By category
		category = part.part_category or "Unknown"
		if category not in analytics["by_category"]:
			analytics["by_category"][category] = {"count": 0, "value": 0, "weight": 0}
		analytics["by_category"][category]["count"] += 1
		analytics["by_category"][category]["value"] += part.estimated_value or 0
		analytics["by_category"][category]["weight"] += part.weight_kg or 0

		# By market demand
		demand = part.market_demand or "Medium"
		analytics["by_demand"][demand] = analytics["by_demand"].get(demand, 0) + 1

		# By sell priority
		priority = part.priority_to_sell or "Medium"
		analytics["by_priority"][priority] = analytics["by_priority"].get(priority, 0) + 1

		# Aging analysis
		if part.date_stored:
			days_stored = date_diff(today(), part.date_stored)
			if days_stored <= 30:
				analytics["aging_analysis"]["0_30_days"] += 1
			elif days_stored <= 90:
				analytics["aging_analysis"]["31_90_days"] += 1
			elif days_stored <= 180:
				analytics["aging_analysis"]["91_180_days"] += 1
			elif days_stored <= 365:
				analytics["aging_analysis"]["181_365_days"] += 1
			else:
				analytics["aging_analysis"]["over_365_days"] += 1

	return analytics


@frappe.whitelist()
def bulk_move_parts(part_codes, new_zone, reason=None):
	"""Move multiple parts to a new zone"""
	if isinstance(part_codes, str):
		part_codes = json.loads(part_codes)

	results = {"success": [], "failed": []}

	for part_code in part_codes:
		try:
			part = frappe.get_doc("Part Storage Location", part_code)
			part.move_to_location(new_zone, reason=reason)
			results["success"].append(part_code)
		except Exception as e:
			results["failed"].append({"part_code": part_code, "error": str(e)})

	return results
