# Copyright (c) 2024, Said Al-Adawi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class OnboardingPerformanceLog(Document):
	def validate(self):
		"""Validate performance log data"""
		if self.total_duration and self.total_duration < 0:
			frappe.throw("Total duration cannot be negative")

	def before_save(self):
		"""Process data before saving"""
		# Ensure completion date is set
		if not self.completion_date:
			self.completion_date = frappe.utils.now()

	def get_performance_grade(self):
		"""Calculate performance grade based on duration"""
		if not self.total_duration:
			return "N/A"

		if self.total_duration < 300:  # Less than 5 minutes
			return "A"
		elif self.total_duration < 600:  # Less than 10 minutes
			return "B"
		elif self.total_duration < 1200:  # Less than 20 minutes
			return "C"
		elif self.total_duration < 1800:  # Less than 30 minutes (requirement)
			return "D"
		else:
			return "F"  # Failed performance requirement
