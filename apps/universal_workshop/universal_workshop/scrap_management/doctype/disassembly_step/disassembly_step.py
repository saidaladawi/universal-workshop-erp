# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class DisassemblyStep(Document):
	# pylint: disable=no-member
	# Frappe framework dynamically adds DocType fields

	def validate(self):
		"""Validate disassembly step data"""
		self.validate_required_fields()
		self.validate_time_estimates()
		self.validate_safety_requirements()
		self.set_default_values()

	def validate_required_fields(self):
		"""Validate required fields for disassembly step"""
		if not self.step_number:
			frappe.throw(_("Step number is required"))

		if not self.part_name:
			frappe.throw(_("Part name is required"))

		if not self.extraction_method:
			frappe.throw(_("Extraction method is required"))

	def validate_time_estimates(self):
		"""Validate time estimates are positive"""
		if self.estimated_time_minutes and self.estimated_time_minutes < 0:
			frappe.throw(_("Estimated time must be positive"))

		if self.actual_time_minutes and self.actual_time_minutes < 0:
			frappe.throw(_("Actual time must be positive"))

	def validate_safety_requirements(self):
		"""Validate safety level and warnings"""
		valid_safety_levels = ["Standard", "Elevated", "High-Risk", "Hazardous"]
		if self.safety_level and self.safety_level not in valid_safety_levels:
			frappe.throw(
				_("Invalid safety level. Must be one of: {0}").format(", ".join(valid_safety_levels))
			)

		# Require safety warnings for elevated risk levels
		if self.safety_level in ["High-Risk", "Hazardous"] and not self.safety_warnings:
			frappe.throw(_("Safety warnings are required for {0} safety level").format(self.safety_level))

	def set_default_values(self):
		"""Set default values for disassembly step"""
		if not self.safety_level:
			self.safety_level = "Standard"

		if not self.skill_level:
			self.skill_level = "Intermediate"

		if not self.status:
			self.status = "Planned"

	def before_save(self):
		"""Set calculated values before saving"""
		self.calculate_completion_percentage()
		self.update_timestamps()

	def calculate_completion_percentage(self):
		"""Calculate completion percentage based on status"""
		status_percentages = {
			"Planned": 0,
			"In Progress": 50,
			"Completed": 100,
			"Skipped": 0,
			"Failed": 0,
		}

		if self.status in status_percentages:
			self.completion_percentage = status_percentages[self.status]

	def update_timestamps(self):
		"""Update timestamps based on status changes"""
		if self.status == "In Progress" and not self.start_time:
			self.start_time = frappe.utils.now()

		if self.status == "Completed" and not self.end_time:
			self.end_time = frappe.utils.now()
			# Calculate actual time if not manually set
			if self.start_time and not self.actual_time_minutes:
				from frappe.utils import time_diff_in_seconds

				time_diff = time_diff_in_seconds(self.end_time, self.start_time)
				self.actual_time_minutes = round(time_diff / 60, 2)

	def get_status_color(self):
		"""Get color coding for step status"""
		colors = {
			"Planned": "gray",
			"In Progress": "blue",
			"Completed": "green",
			"Skipped": "orange",
			"Failed": "red",
		}
		return colors.get(self.status, "gray")

	def get_safety_color(self):
		"""Get color coding for safety level"""
		colors = {
			"Standard": "green",
			"Elevated": "yellow",
			"High-Risk": "orange",
			"Hazardous": "red",
		}
		return colors.get(self.safety_level, "green")

	def get_arabic_part_name(self):
		"""Get Arabic translation for part name"""
		part_translations = {
			# Engine Components
			"Engine Block": "كتلة المحرك",
			"Transmission": "ناقل الحركة",
			"Radiator": "المبرد",
			"Battery": "البطارية",
			"Alternator": "المولد",
			"Starter Motor": "محرك البدء",
			"Catalytic Converter": "محول حفزي",
			# Body Parts
			"Front Bumper": "الصدام الأمامي",
			"Rear Bumper": "الصدام الخلفي",
			"Hood": "غطاء المحرك",
			"Trunk Lid": "غطاء الصندوق",
			"Front Door": "الباب الأمامي",
			"Rear Door": "الباب الخلفي",
			"Side Mirror": "مرآة جانبية",
			# Interior Components
			"Dashboard": "لوحة القيادة",
			"Steering Wheel": "عجلة القيادة",
			"Seats": "المقاعد",
			"Airbag": "الوسادة الهوائية",
			"Radio": "الراديو",
			# Wheels and Suspension
			"Wheel": "العجلة",
			"Tire": "الإطار",
			"Brake Disc": "قرص الفرامل",
			"Shock Absorber": "ماص الصدمات",
			# Electrical Components
			"Headlight": "المصباح الأمامي",
			"Taillight": "المصباح الخلفي",
			"Wiring Harness": "حزمة الأسلاك",
			"ECU": "وحدة التحكم الإلكترونية",
		}

		return part_translations.get(self.part_name, self.part_name)

	def get_mobile_checklist_data(self):
		"""Get formatted data for mobile checklist"""
		return {
			"step_number": self.step_number,
			"part_name": self.part_name,
			"part_name_ar": self.get_arabic_part_name(),
			"extraction_method": self.extraction_method,
			"estimated_time": self.estimated_time_minutes,
			"safety_level": self.safety_level,
			"safety_color": self.get_safety_color(),
			"required_tools": self.required_tools,
			"safety_warnings": self.safety_warnings,
			"status": self.status,
			"status_color": self.get_status_color(),
			"completion_percentage": self.completion_percentage or 0,
		}
