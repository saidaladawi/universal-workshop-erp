# Copyright (c) 2025, Universal Workshop ERP and contributors
# For license information, please see license.txt

import frappe
from frappe import _


class WorkshopPermissionManager:
    """Manage workshop-specific permissions and integrate with ERPNext role system"""

    def __init__(self):
        self.workshop_doctypes = [
            "Workshop Role",
            "Workshop Permission Profile",
            "Vehicle",
            "Customer",
            "Service Order",
            "Parts Inventory",
            "Workshop Technician",
            "Service Appointment",
        ]

    def setup_default_permissions(self):
        """Setup default permissions for workshop roles"""
        try:
            # Get all workshop roles
            workshop_roles = frappe.get_list(
                "Workshop Role",
                filters={"is_active": 1},
                fields=["name", "role_name", "role_type", "priority_level"],
            )

            for role in workshop_roles:
                self.setup_role_permissions(role)

            frappe.db.commit()
            return True

        except Exception as e:
            frappe.log_error(f"Error setting up default permissions: {e}")
            return False

    def setup_role_permissions(self, role):
        """Setup permissions for a specific workshop role"""
        role_name = role.get("role_name")
        role_type = role.get("role_type")
        priority_level = role.get("priority_level", 5)

        # Define permission matrix based on role type and priority
        permission_matrix = self.get_permission_matrix(role_type, priority_level)

        for doctype_name, permissions in permission_matrix.items():
            self.set_doctype_permissions(doctype_name, role_name, permissions)

    def get_permission_matrix(self, role_type, priority_level):
        """Get permission matrix based on role type and priority"""
        base_permissions = {
            "read": 1,
            "write": 0,
            "create": 0,
            "delete": 0,
            "submit": 0,
            "cancel": 0,
            "amend": 0,
        }

        # Management roles get full permissions
        if role_type == "Management" and priority_level >= 8:
            management_permissions = base_permissions.copy()
            management_permissions.update(
                {"write": 1, "create": 1, "delete": 1, "submit": 1, "cancel": 1, "amend": 1}
            )

            return {
                "Customer": management_permissions,
                "Vehicle": management_permissions,
                "Service Order": management_permissions,
                "Parts Inventory": management_permissions,
                "Workshop Technician": management_permissions,
                "Service Appointment": management_permissions,
            }

        # Operational roles get limited permissions
        elif role_type == "Operational":
            operational_permissions = base_permissions.copy()
            operational_permissions.update({"write": 1, "create": 1})

            return {
                "Customer": operational_permissions,
                "Vehicle": operational_permissions,
                "Service Order": operational_permissions,
                "Service Appointment": operational_permissions,
                "Parts Inventory": base_permissions,  # Read-only for parts
            }

        # Technical roles get task-specific permissions
        elif role_type == "Technical":
            technical_permissions = base_permissions.copy()
            technical_permissions.update({"write": 1})  # Can update service orders

            return {
                "Service Order": technical_permissions,
                "Vehicle": base_permissions,  # Read-only
                "Customer": base_permissions,  # Read-only
                "Parts Inventory": base_permissions,  # Read-only
            }

        # Financial roles get billing permissions
        elif role_type == "Financial":
            financial_permissions = base_permissions.copy()
            financial_permissions.update({"write": 1, "create": 1, "submit": 1})

            return {
                "Service Order": financial_permissions,  # For billing
                "Customer": base_permissions,  # Read-only
                "Parts Inventory": base_permissions,  # Read-only
            }

        # Administrative roles get basic permissions
        else:
            admin_permissions = base_permissions.copy()
            admin_permissions.update({"write": 1, "create": 1})

            return {
                "Customer": admin_permissions,
                "Service Appointment": admin_permissions,
                "Vehicle": base_permissions,  # Read-only
            }

    def set_doctype_permissions(self, doctype_name, role_name, permissions):
        """Set permissions for a specific DocType and role"""
        try:
            # Check if permission record exists
            existing_perm = frappe.db.exists(
                "Custom DocPerm", {"parent": doctype_name, "role": role_name}
            )

            if existing_perm:
                # Update existing permission
                perm_doc = frappe.get_doc("Custom DocPerm", existing_perm)
            else:
                # Create new permission
                perm_doc = frappe.new_doc("Custom DocPerm")
                perm_doc.parent = doctype_name
                perm_doc.parenttype = "DocType"
                perm_doc.parentfield = "permissions"
                perm_doc.role = role_name

            # Set permissions
            for perm_type, value in permissions.items():
                if hasattr(perm_doc, perm_type):
                    setattr(perm_doc, perm_type, value)

            perm_doc.save()

        except Exception as e:
            frappe.log_error(f"Error setting permissions for {doctype_name}, {role_name}: {e}")

    def validate_user_permission(self, user, doctype_name, doc_name, perm_type="read"):
        """Validate if user has permission for specific document"""
        try:
            # Get user's workshop roles
            user_roles = self.get_user_workshop_roles(user)

            # Check if any role has the required permission
            for role in user_roles:
                if self.role_has_permission(role.get("role_name"), doctype_name, perm_type):
                    return True

            return False

        except Exception as e:
            frappe.log_error(f"Error validating user permission: {e}")
            return False

    def get_user_workshop_roles(self, user):
        """Get workshop roles assigned to a user"""
        user_roles = frappe.get_list("Has Role", filters={"parent": user}, fields=["role"])

        role_names = [role.role for role in user_roles]

        workshop_roles = frappe.get_list(
            "Workshop Role",
            filters={"role_name": ["in", role_names], "is_active": 1},
            fields=["name", "role_name", "role_type", "priority_level"],
        )

        return workshop_roles

    def role_has_permission(self, role_name, doctype_name, perm_type):
        """Check if role has specific permission for DocType"""
        try:
            perm_record = frappe.db.get_value(
                "Custom DocPerm", {"parent": doctype_name, "role": role_name}, perm_type
            )

            return bool(perm_record)

        except Exception:
            return False

    def sync_with_erpnext_permissions(self):
        """Sync workshop permissions with ERPNext permission system"""
        try:
            workshop_roles = frappe.get_list(
                "Workshop Role", filters={"is_active": 1}, fields=["name", "role_name"]
            )

            for role in workshop_roles:
                # Ensure ERPNext role exists
                if not frappe.db.exists("Role", role.role_name):
                    self.create_erpnext_role(role.role_name)

                # Sync permissions
                self.sync_role_permissions(role.role_name)

            frappe.db.commit()
            return True

        except Exception as e:
            frappe.log_error(f"Error syncing with ERPNext permissions: {e}")
            return False

    def create_erpnext_role(self, role_name):
        """Create ERPNext role if it doesn't exist"""
        try:
            role_doc = frappe.new_doc("Role")
            role_doc.role_name = role_name
            role_doc.disabled = 0
            role_doc.insert()

        except Exception as e:
            frappe.log_error(f"Error creating ERPNext role {role_name}: {e}")

    def sync_role_permissions(self, role_name):
        """Sync permissions for a specific role"""
        try:
            # Get workshop role details
            workshop_role = frappe.get_doc("Workshop Role", role_name)

            # Apply default permissions based on role type
            permission_matrix = self.get_permission_matrix(
                workshop_role.role_type, workshop_role.priority_level
            )

            for doctype_name, permissions in permission_matrix.items():
                self.set_doctype_permissions(doctype_name, role_name, permissions)

        except Exception as e:
            frappe.log_error(f"Error syncing permissions for role {role_name}: {e}")


@frappe.whitelist()
def setup_workshop_permissions():
    """API method to setup workshop permissions"""
    manager = WorkshopPermissionManager()
    success = manager.setup_default_permissions()

    if success:
        frappe.msgprint(_("Workshop permissions setup completed successfully"))
    else:
        frappe.throw(_("Failed to setup workshop permissions"))

    return success


@frappe.whitelist()
def validate_user_access(doctype_name, doc_name, perm_type="read"):
    """API method to validate user access"""
    manager = WorkshopPermissionManager()
    user = frappe.session.user

    has_access = manager.validate_user_permission(user, doctype_name, doc_name, perm_type)

    if not has_access:
        frappe.throw(_("You don't have {0} permission for {1}").format(perm_type, doctype_name))

    return has_access


@frappe.whitelist()
def get_user_accessible_documents(doctype_name):
    """Get list of documents user can access"""
    manager = WorkshopPermissionManager()
    user = frappe.session.user

    # Get user's workshop roles
    user_roles = manager.get_user_workshop_roles(user)

    # For now, return all documents if user has any workshop role
    # This can be enhanced with more granular filtering
    if user_roles:
        documents = frappe.get_list(
            doctype_name, fields=["name", "creation", "modified"], limit=100
        )
        return documents

    return []
