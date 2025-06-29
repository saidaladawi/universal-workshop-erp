# Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document


class TechnicianSkills(Document):
	def validate(self):
		"""Validate technician skills data"""
		self.validate_duplicate_skill()
		self.validate_experience_level()

	def validate_duplicate_skill(self):
		"""Ensure no duplicate skills for same technician"""
		if self.parent:
			existing_skill = frappe.db.exists(
				"Technician Skills",
				{"parent": self.parent, "skill": self.skill, "name": ["!=", self.name]},
			)

			if existing_skill:
				frappe.throw(_("Skill '{0}' already exists for this technician").format(self.skill))

	def validate_experience_level(self):
		"""Validate experience level matches proficiency"""
		if self.years_experience and self.proficiency_level:
			# Basic validation rules
			if self.proficiency_level == "Expert" and self.years_experience < 5:
				frappe.msgprint(_("Expert level usually requires 5+ years of experience"))
			elif self.proficiency_level == "Advanced" and self.years_experience < 3:
				frappe.msgprint(_("Advanced level usually requires 3+ years of experience"))
			elif self.proficiency_level == "Intermediate" and self.years_experience < 1:
				frappe.msgprint(_("Intermediate level usually requires 1+ years of experience"))

	def before_save(self):
		"""Set default values before saving"""
		# Ensure skill is active by default
		if self.is_active is None:
			self.is_active = 1
