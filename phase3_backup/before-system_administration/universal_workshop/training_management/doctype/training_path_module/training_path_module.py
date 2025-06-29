# Copyright (c) 2024, Universal Workshop and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class TrainingPathModule(Document):
	"""Child table for Training Path modules with sequencing and completion tracking"""

	def validate(self):
		"""Validate training path module data"""
		self.validate_sequence_order()
		self.validate_training_module()

	def validate_sequence_order(self):
		"""Ensure sequence order is positive and unique within the path"""
		if self.sequence_order <= 0:
			frappe.throw("Sequence order must be a positive number")

	def validate_training_module(self):
		"""Validate that the training module exists and is active"""
		if self.training_module:
			module_doc = frappe.get_doc("Training Module", self.training_module)
			if not module_doc.is_active:
				frappe.throw(f"Training Module {self.training_module} is not active")
