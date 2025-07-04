# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import json
import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, now


class VehicleDismantlingBOM(Document):
	# pylint: disable=no-member
	# Frappe framework dynamically adds DocType fields

	def validate(self):
		"""Validate BOM data before saving"""
		self.validate_required_fields()
		self.validate_vehicle_data()
		self.validate_operations()
		self.validate_extractable_parts()
		self.calculate_totals()
		self.set_default_values()

	def validate_required_fields(self):
		"""Validate required fields"""
		if not self.bom_name:
			frappe.throw(_("BOM Name is required"))

		if not self.vehicle_make:
			frappe.throw(_("Vehicle Make is required"))

		if not self.vehicle_model:
			frappe.throw(_("Vehicle Model is required"))

		if not self.year_from or not self.year_to:
			frappe.throw(_("Year range is required"))

		if cint(self.year_from) > cint(self.year_to):
			frappe.throw(_("Year From cannot be greater than Year To"))

	def validate_vehicle_data(self):
		"""Validate vehicle-related data"""
		# Validate year range
		current_year = frappe.utils.getdate().year
		if cint(self.year_from) < 1900 or cint(self.year_to) > current_year + 2:
			frappe.throw(_("Invalid year range. Must be between 1900 and {0}").format(current_year + 2))

		# Validate Arabic names if provided
		if self.vehicle_make_ar and not self.is_arabic_text(self.vehicle_make_ar):
			frappe.throw(_("Vehicle Make (Arabic) must contain Arabic characters"))

		if self.vehicle_model_ar and not self.is_arabic_text(self.vehicle_model_ar):
			frappe.throw(_("Vehicle Model (Arabic) must contain Arabic characters"))

	def validate_operations(self):
		"""Validate dismantling operations"""
		if not self.dismantling_operations:
			frappe.msgprint(_("Warning: No dismantling operations defined"), alert=True)
			return

		sequences = []
		total_time = 0

		for operation in self.dismantling_operations:
			# Check for duplicate sequences
			if operation.operation_sequence in sequences:
				frappe.throw(_("Duplicate operation sequence: {0}").format(operation.operation_sequence))
			sequences.append(operation.operation_sequence)

			# Validate time estimates
			if operation.estimated_time <= 0:
				frappe.throw(
					_("Operation '{0}' must have positive estimated time").format(operation.operation_name)
				)

			total_time += flt(operation.estimated_time)

			# Validate Arabic fields
			if operation.operation_name_ar and not self.is_arabic_text(operation.operation_name_ar):
				frappe.throw(
					_("Operation '{0}' Arabic name must contain Arabic characters").format(
						operation.operation_name
					)
				)

		# Update total estimated time
		self.total_estimated_time = total_time

	def validate_extractable_parts(self):
		"""Validate extractable parts data"""
		if not self.extractable_parts:
			frappe.msgprint(_("Warning: No extractable parts defined"), alert=True)
			return

		sequences = []
		total_value = 0
		total_cost = 0

		for part in self.extractable_parts:
			# Check for duplicate sequences
			if part.part_sequence in sequences:
				frappe.throw(_("Duplicate part sequence: {0}").format(part.part_sequence))
			sequences.append(part.part_sequence)

			# Validate financial data
			if part.estimated_value < 0:
				frappe.throw(_("Part '{0}' estimated value cannot be negative").format(part.part_name))

			if part.minimum_selling_price > part.maximum_selling_price and part.maximum_selling_price > 0:
				frappe.throw(_("Part '{0}' minimum price cannot exceed maximum price").format(part.part_name))

			# Validate extraction time
			if part.estimated_extraction_time <= 0:
				frappe.throw(_("Part '{0}' must have positive extraction time").format(part.part_name))

			# Accumulate totals
			total_value += flt(part.estimated_value)
			total_cost += flt(part.estimated_refurbishment_cost)

			# Validate Arabic fields
			if part.part_name_ar and not self.is_arabic_text(part.part_name_ar):
				frappe.throw(
					_("Part '{0}' Arabic name must contain Arabic characters").format(part.part_name)
				)

		# Update financial totals
		self.total_estimated_value = total_value
		self.total_refurbishment_cost = total_cost
		self.estimated_profit = total_value - total_cost

		# Calculate profit margin
		if total_value > 0:
			self.profit_margin_percent = (self.estimated_profit / total_value) * 100
		else:
			self.profit_margin_percent = 0

	def calculate_totals(self):
		"""Calculate various totals and metrics"""
		# Calculate operation totals
		total_operations = len(self.dismantling_operations) if self.dismantling_operations else 0
		hazmat_operations = 0

		if self.dismantling_operations:
			for operation in self.dismantling_operations:
				if operation.generates_hazmat:
					hazmat_operations += 1

		self.total_operations = total_operations
		self.hazmat_operations_count = hazmat_operations

		# Calculate parts totals
		total_parts = len(self.extractable_parts) if self.extractable_parts else 0
		high_value_parts = 0
		high_priority_parts = 0

		if self.extractable_parts:
			for part in self.extractable_parts:
				if flt(part.estimated_value) > 100:  # High value threshold: 100 OMR
					high_value_parts += 1
				if part.extraction_priority == "High":
					high_priority_parts += 1

		self.total_extractable_parts = total_parts
		self.high_value_parts_count = high_value_parts
		self.high_priority_parts_count = high_priority_parts

		# Calculate total extraction time
		total_extraction_time = 0
		if self.extractable_parts:
			for part in self.extractable_parts:
				total_extraction_time += flt(part.estimated_extraction_time)

		self.total_extraction_time = total_extraction_time

	def set_default_values(self):
		"""Set default values for metadata fields"""
		if not self.created_by:
			self.created_by = frappe.session.user

		if not self.created_date:
			self.created_date = frappe.utils.today()

		# Auto-generate BOM code if not provided
		if not self.bom_code:
			self.bom_code = self.generate_bom_code()

	def generate_bom_code(self):
		"""Generate unique BOM code: BOM-MAKE-MODEL-YYYY"""
		make_code = self.vehicle_make[:3].upper() if self.vehicle_make else "VEH"
		model_code = self.vehicle_model[:3].upper() if self.vehicle_model else "MOD"
		year_code = str(self.year_from) if self.year_from else "0000"

		# Get next sequence number for this combination
		existing_boms = frappe.db.sql(
			"""
            SELECT bom_code FROM `tabVehicle Dismantling BOM`
            WHERE bom_code LIKE %s
            ORDER BY creation DESC LIMIT 1
        """,
			[f"BOM-{make_code}-{model_code}-{year_code}-%"],
		)

		if existing_boms:
			last_code = existing_boms[0][0]
			try:
				last_seq = int(last_code.split("-")[-1])
				new_seq = last_seq + 1
			except (ValueError, IndexError):
				new_seq = 1
		else:
			new_seq = 1

		return f"BOM-{make_code}-{model_code}-{year_code}-{new_seq:03d}"

	def is_arabic_text(self, text):
		"""Check if text contains Arabic characters"""
		if not text:
			return False
		arabic_pattern = re.compile(r"[\u0600-\u06FF\u0750-\u077F]+")
		return bool(arabic_pattern.search(text))

	def before_save(self):
		"""Actions before saving"""
		self.validate_bom_conflicts()
		self.update_modification_info()

	def validate_bom_conflicts(self):
		"""Check for conflicting BOMs for same vehicle specification"""
		if self.is_new():
			return

		filters = {
			"vehicle_make": self.vehicle_make,
			"vehicle_model": self.vehicle_model,
			"engine_type": self.engine_type,
			"name": ["!=", self.name],
			"is_active": 1,
		}

		# Check for overlapping year ranges
		existing_boms = frappe.get_list(
			"Vehicle Dismantling BOM",
			filters=filters,
			fields=["name", "year_from", "year_to", "bom_name"],
		)

		for bom in existing_boms:
			# Check if year ranges overlap
			if cint(self.year_from) <= cint(bom.year_to) and cint(self.year_to) >= cint(bom.year_from):
				frappe.throw(
					_("Conflicting BOM exists: {0} for years {1}-{2}").format(
						bom.bom_name, bom.year_from, bom.year_to
					)
				)

	def update_modification_info(self):
		"""Update modification tracking"""
		self.modified_by = frappe.session.user
		self.modified_date = frappe.utils.today()

	@frappe.whitelist()
	def create_work_order_template(self):
		"""Create a Work Order template from this BOM"""
		try:
			# Create Work Order document
			work_order = frappe.new_doc("Work Order")
			work_order.production_item = f"DISMANTLED-{self.vehicle_make}-{self.vehicle_model}"
			work_order.qty = 1
			work_order.company = frappe.defaults.get_user_default("Company")
			work_order.bom_no = self.name

			# Add operations from BOM
			if self.dismantling_operations:
				for operation in self.dismantling_operations:
					wo_operation = work_order.append("operations", {})
					wo_operation.operation = operation.operation_name
					wo_operation.workstation = operation.workstation
					wo_operation.time_in_mins = operation.estimated_time
					wo_operation.description = operation.operation_description

			work_order.insert()
			frappe.msgprint(_("Work Order template created: {0}").format(work_order.name))
			return work_order.name

		except Exception as e:
			frappe.log_error(f"Error creating work order template: {e!s}")
			frappe.throw(_("Failed to create Work Order template: {0}").format(str(e)))

	@frappe.whitelist()
	def get_roi_projection(self, acquisition_cost=0):
		"""Calculate ROI projection based on BOM estimates"""
		acquisition_cost = flt(acquisition_cost)

		# Calculate total costs
		total_extraction_cost = 0
		labor_rate_per_minute = (
			frappe.db.get_single_value("Workshop Settings", "labor_rate_per_minute") or 0.5
		)

		# Calculate labor costs
		if self.dismantling_operations:
			for operation in self.dismantling_operations:
				total_extraction_cost += flt(operation.estimated_time) * labor_rate_per_minute

		# Add refurbishment costs
		total_refurbishment = flt(self.total_refurbishment_cost)

		# Calculate disposal costs for hazmat
		disposal_cost_per_operation = (
			frappe.db.get_single_value("Workshop Settings", "hazmat_disposal_cost") or 10
		)
		total_disposal_cost = self.hazmat_operations_count * disposal_cost_per_operation

		# Total costs
		total_costs = acquisition_cost + total_extraction_cost + total_refurbishment + total_disposal_cost

		# Revenue projection
		total_revenue = flt(self.total_estimated_value)

		# Calculate ROI
		net_profit = total_revenue - total_costs
		roi_percentage = (net_profit / total_costs * 100) if total_costs > 0 else 0

		return {
			"acquisition_cost": acquisition_cost,
			"extraction_cost": total_extraction_cost,
			"refurbishment_cost": total_refurbishment,
			"disposal_cost": total_disposal_cost,
			"total_costs": total_costs,
			"estimated_revenue": total_revenue,
			"net_profit": net_profit,
			"roi_percentage": roi_percentage,
			"break_even_acquisition_cost": total_revenue
			- total_extraction_cost
			- total_refurbishment
			- total_disposal_cost,
		}

	@frappe.whitelist()
	def get_parts_by_priority(self):
		"""Get extractable parts grouped by priority"""
		if not self.extractable_parts:
			return {"high": [], "medium": [], "low": []}

		priority_groups = {"high": [], "medium": [], "low": []}

		for part in self.extractable_parts:
			priority = part.extraction_priority.lower() if part.extraction_priority else "medium"
			if priority in priority_groups:
				priority_groups[priority].append(
					{
						"part_name": part.part_name,
						"part_name_ar": part.part_name_ar,
						"estimated_value": part.estimated_value,
						"extraction_time": part.estimated_extraction_time,
						"category": part.part_category,
					}
				)

		return priority_groups

	@frappe.whitelist()
	def generate_barcode_labels(self):
		"""Generate barcode labels for all extractable parts"""
		if not self.extractable_parts:
			frappe.throw(_("No extractable parts defined"))

		labels = []
		for idx, part in enumerate(self.extractable_parts, 1):
			barcode = f"{self.bom_code}-P{idx:03d}"
			part.barcode_label = barcode

			labels.append(
				{
					"barcode": barcode,
					"part_name": part.part_name,
					"part_name_ar": part.part_name_ar,
					"category": part.part_category,
					"estimated_value": part.estimated_value,
				}
			)

		self.save()
		frappe.msgprint(_("Barcode labels generated for {0} parts").format(len(labels)))
		return labels
