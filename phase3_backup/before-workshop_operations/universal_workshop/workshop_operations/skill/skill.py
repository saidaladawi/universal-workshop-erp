# Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt
# pylint: disable=no-member
# Frappe framework dynamically adds DocType fields to Document class


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today


class Skill(Document):
	def validate(self):
		"""Validate skill data"""
		self.validate_arabic_name()
		self.validate_skill_category()

	def validate_arabic_name(self):
		"""Ensure Arabic skill name is provided"""
		if not self.skill_name_ar:
			frappe.throw(_("Arabic skill name is required"))

	def validate_skill_category(self):
		"""Validate skill category"""
		valid_categories = [
			"Engine",
			"Transmission",
			"Brakes",
			"Electrical",
			"Air Conditioning",
			"Bodywork",
			"Diagnostics",
			"General Maintenance",
		]

		if self.skill_category and self.skill_category not in valid_categories:
			frappe.msgprint(
				_("Skill category '{0}' is not in the standard list").format(
					self.skill_category
				)
			)

	def before_save(self):
		"""Set default values before saving"""
		if not self.created_by:
			self.created_by = frappe.session.user
		if not self.created_date:
			self.created_date = today()

		# Ensure skill is active by default
		if self.is_active is None:
			self.is_active = 1

	def after_insert(self):
		"""Actions after inserting new skill"""
		frappe.msgprint(
			_("Skill '{0}' created successfully").format(self.skill_name)
		)

	@frappe.whitelist()
	def get_skill_technicians(self):
		"""Get all technicians with this skill"""
		technicians = frappe.get_all(
			"Technician Skills",
			filters={"skill": self.name, "is_active": 1},
			fields=["technician", "proficiency_level", "years_experience"],
		)

		return technicians

	@staticmethod
	@frappe.whitelist()
	def get_skills_by_category(category=None):
		"""Get skills filtered by category"""
		filters = {"is_active": 1}
		if category:
			filters["skill_category"] = category

		skills = frappe.get_all(
			"Skill",
			filters=filters,
			fields=["name", "skill_name", "skill_name_ar", "difficulty_level"],
			order_by="skill_name",
		)

		return skills

	@staticmethod
	@frappe.whitelist()
	def get_skill_requirements_for_service(service_type):
		"""Get required skills for a specific service type"""
		# This would be linked to Service Types in future implementation
		skill_requirements = frappe.get_all(
			"Service Type Skills",  # Future DocType
			filters={"service_type": service_type},
			fields=["skill", "required_level", "is_mandatory"],
		)

		return skill_requirements
