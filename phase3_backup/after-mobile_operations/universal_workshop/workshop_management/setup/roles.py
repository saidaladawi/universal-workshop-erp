# Copyright (c) 2024, Said Al-Adawi and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def setup_workshop_roles():
	"""Setup role-based permissions for workshop operations"""

	roles = [
		{
			"role_name": "Workshop Manager",
			"desk_access": 1,
			"permissions": ["read", "write", "create", "delete", "submit", "cancel", "import", "export"],
			"description": "Full access to all workshop operations and management functions",
		},
		{
			"role_name": "Workshop Technician",
			"desk_access": 1,
			"permissions": ["read", "write", "create"],
			"description": "Access to technical operations and service records",
		},
		{
			"role_name": "Workshop Receptionist",
			"desk_access": 1,
			"permissions": ["read", "write", "create"],
			"description": "Customer service and appointment management access",
		},
		{
			"role_name": "Workshop Customer",
			"desk_access": 0,
			"permissions": ["read"],
			"description": "Limited portal access for workshop customers",
		},
		{
			"role_name": "Workshop Owner",
			"desk_access": 1,
			"permissions": ["read", "write", "create", "delete", "submit", "cancel", "import", "export"],
			"description": "Workshop owner with full administrative access",
		},
	]

	for role_data in roles:
		create_or_update_role(role_data)


def create_or_update_role(role_data):
	"""Create or update a role"""
	role_name = role_data["role_name"]

	if not frappe.db.exists("Role", role_name):
		role = frappe.new_doc("Role")
		role.role_name = role_name
		role.desk_access = role_data.get("desk_access", 1)
		role.description = role_data.get("description", "")
		role.insert()
		frappe.db.commit()
		print(f"Created role: {role_name}")
	else:
		print(f"Role already exists: {role_name}")


def setup_workshop_permissions():
	"""Setup permissions for workshop DocTypes"""

	permissions_config = {
		"Workshop Profile": {
			"Workshop Manager": ["read", "write", "create", "delete"],
			"Workshop Owner": ["read", "write", "create", "delete"],
			"Workshop Technician": ["read"],
			"Workshop Receptionist": ["read"],
			"System Manager": ["read", "write", "create", "delete"],
		},
		"Workshop Onboarding Form": {
			"Workshop Manager": ["read", "write", "create", "delete"],
			"Workshop Owner": ["read", "write", "create", "delete"],
			"Guest": ["read", "write", "create"],  # For onboarding process
			"System Manager": ["read", "write", "create", "delete"],
		},
		"Onboarding Progress": {
			"Workshop Manager": ["read", "write"],
			"Workshop Owner": ["read", "write"],
			"System Manager": ["read", "write", "create", "delete"],
		},
	}

	for doctype, role_permissions in permissions_config.items():
		setup_doctype_permissions(doctype, role_permissions)


def setup_doctype_permissions(doctype, role_permissions):
	"""Setup permissions for a specific DocType"""

	# Clear existing permissions
	frappe.db.sql(
		"""
        DELETE FROM `tabCustom DocPerm`
        WHERE parent = %s
    """,
		doctype,
	)

	for role, permissions in role_permissions.items():
		if frappe.db.exists("Role", role):
			perm_doc = frappe.new_doc("Custom DocPerm")
			perm_doc.parent = doctype
			perm_doc.parenttype = "DocType"
			perm_doc.parentfield = "permissions"
			perm_doc.role = role

			# Set permission flags
			perm_doc.read = 1 if "read" in permissions else 0
			perm_doc.write = 1 if "write" in permissions else 0
			perm_doc.create = 1 if "create" in permissions else 0
			perm_doc.delete = 1 if "delete" in permissions else 0
			perm_doc.submit = 1 if "submit" in permissions else 0
			perm_doc.cancel = 1 if "cancel" in permissions else 0
			perm_doc.amend = 1 if "amend" in permissions else 0
			perm_doc.report = 1 if "report" in permissions else 0
			perm_doc.export = 1 if "export" in permissions else 0
			perm_doc.import_data = 1 if "import" in permissions else 0
			perm_doc.share = 1 if "share" in permissions else 0
			perm_doc.print = 1 if "print" in permissions else 0
			perm_doc.email = 1 if "email" in permissions else 0

			perm_doc.insert()

	frappe.db.commit()
	print(f"Updated permissions for DocType: {doctype}")


def setup_default_user():
	"""Setup default workshop admin user"""

	admin_email = "admin@universal-workshop.om"

	if not frappe.db.exists("User", admin_email):
		user = frappe.new_doc("User")
		user.email = admin_email
		user.first_name = "Workshop"
		user.last_name = "Administrator"
		user.username = "workshop_admin"
		user.language = "ar"  # Arabic default
		user.time_zone = "Asia/Muscat"
		user.country = "Oman"
		user.send_welcome_email = 0
		user.enabled = 1

		# Add roles
		user.append("roles", {"role": "Workshop Manager"})
		user.append("roles", {"role": "Workshop Owner"})
		user.append("roles", {"role": "System Manager"})

		user.insert()
		frappe.db.commit()
		print(f"Created default user: {admin_email}")
	else:
		print(f"User already exists: {admin_email}")


@frappe.whitelist()
def initialize_workshop_system():
	"""Initialize complete workshop system setup"""
	try:
		setup_workshop_roles()
		setup_workshop_permissions()
		setup_default_user()

		frappe.msgprint(
			{
				"title": _("Workshop System Initialized"),
				"message": _("All roles, permissions, and default user have been set up successfully."),
				"indicator": "green",
			}
		)

		return {"success": True, "message": "Workshop system initialized successfully"}

	except Exception as e:
		frappe.log_error(f"Error initializing workshop system: {e!s}")
		frappe.throw(_("Error initializing workshop system. Please contact administrator."))


def run_setup():
	"""Run the complete setup - for manual execution"""
	initialize_workshop_system()
	print("Workshop system setup completed!")
