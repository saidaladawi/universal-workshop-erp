#!/usr/bin/env python3

import frappe


def create_customer_management_module():
	"""Create Customer Management module if it doesn't exist"""

	# Check if module already exists
	if frappe.db.exists("Module Def", "Customer Management"):
		print("Customer Management module already exists")
		return

	# Create the module
	module = frappe.new_doc("Module Def")
	module.module_name = "Customer Management"
	module.app_name = "universal_workshop"
	module.insert()
	frappe.db.commit()

	print("Customer Management module created successfully")


if __name__ == "__main__":
	frappe.init(site="universal.local")
	frappe.connect()
	create_customer_management_module()
