# License Key Pair DocType Controller
# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class LicenseKeyPair(Document):
	"""License Key Pair DocType for storing RSA key pairs"""

	def validate(self):
		"""Validate key pair data"""
		self.validate_algorithm()
		self.validate_key_size()
		self.validate_key_format()

	def validate_algorithm(self):
		"""Ensure algorithm is supported"""
		supported_algorithms = ["RS256", "RS384", "RS512"]
		if self.algorithm not in supported_algorithms:
			frappe.throw(
				f"Algorithm {self.algorithm} is not supported. Use one of: {', '.join(supported_algorithms)}"
			)

	def validate_key_size(self):
		"""Validate key size is appropriate for algorithm"""
		min_key_size = 2048
		if self.key_size < min_key_size:
			frappe.throw(f"Key size must be at least {min_key_size} bits for security")

	def validate_key_format(self):
		"""Validate that keys are in proper PEM format"""
		if self.private_key and not (
			self.private_key.startswith("-----BEGIN PRIVATE KEY-----")
			or self.private_key.startswith("-----BEGIN RSA PRIVATE KEY-----")
		):
			frappe.throw("Private key must be in PEM format")

		if self.public_key and not self.public_key.startswith("-----BEGIN PUBLIC KEY-----"):
			frappe.throw("Public key must be in PEM format")

	def before_insert(self):
		"""Set creation timestamp"""
		if not self.created_at:
			self.created_at = frappe.utils.now()

	def on_update(self):
		"""Handle key pair updates"""
		# Log key pair changes for security audit
		frappe.logger().info(f"License Key Pair '{self.name}' updated")

	def before_save(self):
		"""Security checks before saving"""
		# Ensure only one active key pair of each type
		if self.is_active:
			existing_active = frappe.get_all(
				"License Key Pair",
				filters={"is_active": 1, "algorithm": self.algorithm, "name": ["!=", self.name]},
			)

			if existing_active:
				frappe.throw(
					f"Another active key pair with algorithm {self.algorithm} already exists. Only one active key pair per algorithm is allowed."
				)
