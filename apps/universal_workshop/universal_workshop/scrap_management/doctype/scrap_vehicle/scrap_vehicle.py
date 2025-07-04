# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import os
import re
import uuid
from datetime import datetime, timedelta

import barcode
from barcode.writer import ImageWriter

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, now, today


class ScrapVehicle(Document):
	# pylint: disable=no-member
	# Frappe framework dynamically adds DocType fields to Document class

	def autoname(self):
		"""Auto-generate scrap vehicle ID"""
		year = getdate().year
		last_id = frappe.db.sql(
			"""
            SELECT MAX(CAST(SUBSTRING(name, 4, 4) AS UNSIGNED)) as max_id
            FROM `tabScrap Vehicle`
            WHERE name LIKE %s
        """,
			[f"SV-{year}-%"],
			as_dict=True,
		)

		next_id = 1
		if last_id and last_id[0].max_id:
			next_id = last_id[0].max_id + 1

		self.name = f"SV-{year}-{next_id:04d}"

	def validate(self):
		"""Validate scrap vehicle data"""
		self.validate_vin_number()
		self.validate_arabic_names()
		self.validate_assessment_data()
		self.validate_oman_compliance()
		self.calculate_financial_metrics()
		self.set_default_values()

	def validate_vin_number(self):
		"""Validate VIN number format"""
		if self.vin_number:
			# Clean VIN number
			self.vin_number = self.vin_number.upper().strip()

			# Basic VIN validation (17 characters, alphanumeric excluding I, O, Q)
			vin_pattern = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")
			if not vin_pattern.match(self.vin_number):
				frappe.throw(
					_("Invalid VIN number format. Must be 17 characters, alphanumeric excluding I, O, Q")
				)

			# Check for duplicate VIN
			existing = frappe.db.exists(
				"Scrap Vehicle", {"vin_number": self.vin_number, "name": ["!=", self.name]}
			)
			if existing:
				frappe.throw(
					_("VIN number {0} already exists in Scrap Vehicle {1}").format(self.vin_number, existing)
				)

	def validate_arabic_names(self):
		"""Validate Arabic name fields"""
		if self.owner_name and not self.owner_name_ar:
			frappe.msgprint(_("Arabic owner name is recommended for better documentation"))

		# Validate Arabic character encoding
		if self.owner_name_ar:
			try:
				self.owner_name_ar.encode("utf-8")
			except UnicodeEncodeError:
				frappe.throw(_("Arabic owner name contains invalid characters"))

	def validate_assessment_data(self):
		"""Validate assessment information"""
		if self.assessment_completed and not self.assessment_date:
			frappe.throw(_("Assessment date is required when assessment is marked complete"))

		if self.assessment_date and getdate(self.assessment_date) > getdate():
			frappe.throw(_("Assessment date cannot be in the future"))

		if self.approved_for_scrapping and not self.assessment_completed:
			frappe.throw(_("Vehicle must be assessed before approval for scrapping"))

		# Update status based on assessment completion
		if self.assessment_completed and self.status == "Draft":
			self.status = "Assessed"

	def validate_oman_compliance(self):
		"""Validate Oman-specific compliance requirements"""
		# Validate Oman phone format if provided
		if self.owner_phone:
			oman_phone_pattern = re.compile(r"^\+968\s?\d{8}$")
			if not oman_phone_pattern.match(self.owner_phone):
				frappe.throw(_("Invalid Oman phone number format. Use +968 XXXXXXXX"))

		# Environmental compliance checks
		if self.status in ["In Dismantling", "Dismantled"] and not self.fluids_drained:
			frappe.msgprint(
				_("Warning: Fluids should be drained before dismantling for environmental compliance")
			)

		if self.hazmat_removal_required and not self.hazmat_removal_date:
			frappe.msgprint(_("Hazmat removal date should be set when hazmat removal is required"))

	def calculate_financial_metrics(self):
		"""Calculate financial metrics automatically"""
		# Calculate total cost
		total_cost = 0
		if self.acquisition_cost:
			total_cost += flt(self.acquisition_cost)
		if self.assessment_cost:
			total_cost += flt(self.assessment_cost)
		if self.dismantling_cost:
			total_cost += flt(self.dismantling_cost)
		if self.storage_cost:
			total_cost += flt(self.storage_cost)

		self.total_cost = flt(total_cost, 3)

		# Calculate total revenue
		total_revenue = 0
		if self.parts_sales_revenue:
			total_revenue += flt(self.parts_sales_revenue)
		if self.scrap_metal_revenue:
			total_revenue += flt(self.scrap_metal_revenue)
		if self.other_revenue:
			total_revenue += flt(self.other_revenue)

		self.total_revenue = flt(total_revenue, 3)

		# Calculate profit metrics
		self.gross_profit = flt(self.total_revenue - self.total_cost, 3)

		if self.total_revenue > 0:
			self.profit_margin = flt((self.gross_profit / self.total_revenue) * 100, 2)
		else:
			self.profit_margin = 0

		if self.total_cost > 0:
			self.roi_percentage = flt((self.gross_profit / self.total_cost) * 100, 2)
		else:
			self.roi_percentage = 0

	def set_default_values(self):
		"""Set default values for new records"""
		if not self.created_by:
			self.created_by = frappe.session.user
		if not self.created_date:
			self.created_date = now()

		# Set assessment location default
		if not self.assessment_location:
			default_workshop = frappe.db.get_single_value("Workshop Settings", "default_workshop")
			if default_workshop:
				self.assessment_location = default_workshop

		# Generate storage barcode if needed
		if self.storage_location and not self.storage_barcode:
			self.storage_barcode = self.generate_storage_barcode()

	def before_save(self):
		"""Actions before saving the document"""
		self.update_parts_extracted_count()
		self.update_parts_sales_revenue()

	def update_parts_extracted_count(self):
		"""Update count of extracted parts"""
		if hasattr(self, "extracted_parts") and self.extracted_parts:
			self.parts_extracted_count = len(self.extracted_parts)
		else:
			self.parts_extracted_count = 0

	def update_parts_sales_revenue(self):
		"""Update parts sales revenue from extracted parts"""
		if hasattr(self, "extracted_parts") and self.extracted_parts:
			total_sales = 0
			for part in self.extracted_parts:
				if part.sale_price:
					total_sales += flt(part.sale_price)
			self.parts_sales_revenue = flt(total_sales, 3)

	def after_insert(self):
		"""Actions after document creation"""
		self.create_initial_assessment_checklist()
		self.log_activity("Scrap Vehicle Created")

	def create_initial_assessment_checklist(self):
		"""Create initial assessment checklist items"""
		checklist_items = [
			{
				"assessment_category": "Body",
				"item_name": "Front Bumper",
				"item_name_ar": "المصد الأمامي",
			},
			{
				"assessment_category": "Body",
				"item_name": "Rear Bumper",
				"item_name_ar": "المصد الخلفي",
			},
			{"assessment_category": "Body", "item_name": "Hood", "item_name_ar": "غطاء المحرك"},
			{"assessment_category": "Body", "item_name": "Doors", "item_name_ar": "الأبواب"},
			{
				"assessment_category": "Engine",
				"item_name": "Engine Block",
				"item_name_ar": "كتلة المحرك",
			},
			{
				"assessment_category": "Engine",
				"item_name": "Transmission",
				"item_name_ar": "ناقل الحركة",
			},
			{
				"assessment_category": "Electrical",
				"item_name": "Battery",
				"item_name_ar": "البطارية",
			},
			{
				"assessment_category": "Electrical",
				"item_name": "Alternator",
				"item_name_ar": "المولد",
			},
			{"assessment_category": "Interior", "item_name": "Seats", "item_name_ar": "المقاعد"},
			{
				"assessment_category": "Interior",
				"item_name": "Dashboard",
				"item_name_ar": "لوحة القيادة",
			},
			{
				"assessment_category": "Tires",
				"item_name": "Front Tires",
				"item_name_ar": "الإطارات الأمامية",
			},
			{
				"assessment_category": "Tires",
				"item_name": "Rear Tires",
				"item_name_ar": "الإطارات الخلفية",
			},
		]

		for item in checklist_items:
			self.append("assessment_checklist", item)
		self.save()

	def generate_storage_barcode(self):
		"""Generate unique barcode for storage tracking"""
		# Generate unique identifier
		unique_id = f"SV-{self.name}-{uuid.uuid4().hex[:8]}"

		# Generate barcode image (optional - for printing)
		try:
			code128 = barcode.get_barcode_class("code128")
			barcode_instance = code128(unique_id, writer=ImageWriter())

			# Save barcode image
			barcode_path = f"/tmp/barcode_{unique_id}.png"
			barcode_instance.save(barcode_path)

		except Exception as e:
			frappe.log_error(f"Barcode generation failed: {e}")

		return unique_id

	def log_activity(self, activity):
		"""Log activity to document timeline"""
		frappe.get_doc(
			{
				"doctype": "Activity Log",
				"subject": activity,
				"content": f"{activity} for Scrap Vehicle {self.name}",
				"reference_doctype": "Scrap Vehicle",
				"reference_name": self.name,
				"user": frappe.session.user,
			}
		).insert(ignore_permissions=True)

	@frappe.whitelist()
	def start_dismantling(self):
		"""Start dismantling process"""
		if self.status != "Approved for Scrapping":
			frappe.throw(_("Vehicle must be approved for scrapping before dismantling can start"))

		if not self.assigned_technician:
			frappe.throw(_("Technician must be assigned before starting dismantling"))

		# Update dismantling status
		self.dismantling_status = "In Progress"
		self.dismantling_start_date = today()
		self.status = "In Dismantling"

		# Environmental compliance checks
		if not self.fluids_drained:
			frappe.msgprint(_("Warning: Ensure all fluids are drained before dismantling"))
		if not self.battery_removed:
			frappe.msgprint(_("Warning: Ensure battery is safely removed"))
		if not self.airbags_deactivated:
			frappe.msgprint(_("Warning: Ensure airbags are deactivated for safety"))

		self.save()
		self.log_activity("Dismantling Started")

		frappe.msgprint(_("Dismantling process started successfully"))

	@frappe.whitelist()
	def complete_dismantling(self):
		"""Complete dismantling process"""
		if self.dismantling_status != "In Progress":
			frappe.throw(_("Dismantling is not currently in progress"))

		# Update dismantling status
		self.dismantling_status = "Completed"
		self.dismantling_end_date = today()
		self.status = "Dismantled"

		# Update parts to storage status
		for part in self.extracted_parts:
			if part.part_status == "Extracted":
				part.part_status = "Stored"

		self.save()
		self.log_activity("Dismantling Completed")

		# Create inventory entries for extracted parts
		self.create_inventory_entries()

		frappe.msgprint(_("Dismantling completed successfully. Parts moved to storage."))

	def create_inventory_entries(self):
		"""Create inventory entries for extracted parts"""
		for part in self.extracted_parts:
			if part.item_code and part.storage_location:
				try:
					# Create stock entry for the extracted part
					stock_entry = frappe.new_doc("Stock Entry")
					stock_entry.stock_entry_type = "Material Receipt"
					stock_entry.company = frappe.defaults.get_user_default("Company")

					stock_entry.append(
						"items",
						{
							"item_code": part.item_code,
							"qty": 1,
							"t_warehouse": part.storage_location,
							"cost_center": frappe.defaults.get_user_default("Cost Center"),
							"basic_rate": part.final_graded_value or 0,
							"serial_no": part.part_barcode,
						},
					)

					stock_entry.insert()
					stock_entry.submit()

					# Update part with stock entry reference
					part.notes = f"Stock Entry: {stock_entry.name}"

				except Exception as e:
					frappe.log_error(f"Failed to create inventory entry for part {part.part_name}: {e}")

	@frappe.whitelist()
	def generate_assessment_report(self):
		"""Generate comprehensive assessment report"""
		# Collect assessment data
		report_data = {
			"vehicle_info": {
				"vin": self.vin_number,
				"make": self.make,
				"model": self.model,
				"year": self.year,
				"owner": self.owner_name,
				"owner_ar": self.owner_name_ar,
			},
			"assessment": {
				"date": self.assessment_date,
				"assessor": self.assessor,
				"condition": self.overall_condition,
				"damage_severity": self.damage_severity,
				"estimated_value": self.estimated_scrap_value,
			},
			"checklist": [],
		}

		# Add checklist items
		for item in self.assessment_checklist:
			report_data["checklist"].append(
				{
					"category": item.assessment_category,
					"item": item.item_name,
					"item_ar": item.item_name_ar,
					"condition": item.condition_rating,
					"damage": item.damage_level,
					"value": item.estimated_value,
				}
			)

		return report_data

	@frappe.whitelist()
	def calculate_roi_projection(self, parts_markup_percent=20):
		"""Calculate ROI projection based on parts assessment"""
		markup = flt(parts_markup_percent) / 100

		# Calculate potential revenue from parts
		total_parts_value = 0
		high_value_parts = 0

		for checklist in [
			self.exterior_checklist,
			self.engine_checklist,
			self.interior_checklist,
			self.electrical_checklist,
			self.wheels_tires_checklist,
		]:
			if checklist:
				for part in checklist:
					if part.estimated_value:
						part_value = flt(part.estimated_value) * (1 + markup)
						total_parts_value += part_value

						if part_value > 50:  # High-value parts above 50 OMR
							high_value_parts += 1

		# Add scrap metal value (estimated)
		scrap_metal_value = flt(self.estimated_scrap_value) * 0.3  # Conservative estimate
		projected_revenue = total_parts_value + scrap_metal_value

		# Calculate projected ROI
		total_costs = self.total_cost or 0
		projected_profit = projected_revenue - total_costs
		projected_roi = (projected_profit / total_costs * 100) if total_costs > 0 else 0

		return {
			"projected_parts_revenue": flt(total_parts_value, 3),
			"projected_scrap_revenue": flt(scrap_metal_value, 3),
			"total_projected_revenue": flt(projected_revenue, 3),
			"projected_profit": flt(projected_profit, 3),
			"projected_roi_percent": flt(projected_roi, 2),
			"high_value_parts_count": high_value_parts,
			"markup_applied": f"{parts_markup_percent}%",
		}


# Utility functions
@frappe.whitelist()
def get_scrap_vehicle_dashboard_data():
	"""Get dashboard data for scrap vehicle management"""

	# Status summary
	status_summary = frappe.db.sql(
		"""
        SELECT status, COUNT(*) as count
        FROM `tabScrap Vehicle`
        GROUP BY status
    """,
		as_dict=True,
	)

	# Financial summary
	financial_summary = frappe.db.sql(
		"""
        SELECT 
            SUM(total_cost) as total_costs,
            SUM(total_revenue) as total_revenue,
            SUM(gross_profit) as total_profit,
            AVG(roi_percentage) as avg_roi
        FROM `tabScrap Vehicle`
        WHERE total_cost > 0
    """,
		as_dict=True,
	)

	# Monthly processing
	monthly_processing = frappe.db.sql(
		"""
        SELECT 
            DATE_FORMAT(assessment_date, '%Y-%m') as month,
            COUNT(*) as vehicles_processed,
            SUM(estimated_scrap_value) as total_value
        FROM `tabScrap Vehicle`
        WHERE assessment_date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
        GROUP BY month
        ORDER BY month
    """,
		as_dict=True,
	)

	return {
		"status_summary": status_summary,
		"financial_summary": financial_summary[0] if financial_summary else {},
		"monthly_processing": monthly_processing,
	}


@frappe.whitelist()
def bulk_update_vehicle_status(vehicle_names, new_status):
	"""Bulk update status for multiple vehicles"""
	vehicle_list = frappe.parse_json(vehicle_names)

	for vehicle_name in vehicle_list:
		doc = frappe.get_doc("Scrap Vehicle", vehicle_name)
		doc.status = new_status
		doc.save()

	frappe.msgprint(_("Updated {0} vehicles to status: {1}").format(len(vehicle_list), new_status))


@frappe.whitelist()
def generate_vehicle_barcode(vehicle_name):
	"""Generate barcode for a specific vehicle"""
	doc = frappe.get_doc("Scrap Vehicle", vehicle_name)
	if not doc.storage_barcode:
		doc.storage_barcode = doc.generate_storage_barcode()
		doc.save()

	return doc.storage_barcode
