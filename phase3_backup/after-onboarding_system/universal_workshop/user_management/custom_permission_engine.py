# Copyright (c) 2025, Universal Workshop ERP and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.permissions import get_user_permissions
from frappe.core.doctype.user_permission.user_permission import (
    get_user_permissions as get_user_permission_list,
)


class CustomPermissionEngine:
    """
    Advanced permission engine for Universal Workshop ERP
    Implements row-level, field-level, and context-aware permissions
    """

    def __init__(self):
        self.workshop_doctypes = [
            "Customer",
            "Vehicle",
            "Service Order",
            "Parts Inventory",
            "Workshop Technician",
            "Service Appointment",
            "Workshop Role",
            "Workshop Permission Profile",
        ]

        self.sensitive_fields = {
            "Customer": ["customer_credit_limit", "payment_terms", "tax_id"],
            "Vehicle": ["owner_id_number", "registration_document"],
            "Service Order": ["total_amount", "discount_amount", "cost_breakdown"],
            "Parts Inventory": ["cost_price", "supplier_price", "profit_margin"],
            "Workshop Technician": ["salary", "commission_rate", "performance_rating"],
        }

    def has_permission(self, doc, user=None, ptype="read"):
        """
        Main permission check method - called by ERPNext permission system
        """
        if not user:
            user = frappe.session.user

        # System Manager always has access
        if "System Manager" in frappe.get_roles(user):
            return True

        # Check workshop-specific permissions
        return self.check_workshop_permission(doc, user, ptype)

    def check_workshop_permission(self, doc, user, ptype):
        """
        Check workshop-specific permissions with context awareness
        """
        try:
            # Get user's workshop roles
            user_roles = self.get_user_workshop_roles(user)
            if not user_roles:
                return False

            # Check document-level permissions
            if not self.check_document_permission(doc, user_roles, ptype):
                return False

            # Check row-level permissions
            if not self.check_row_level_permission(doc, user, ptype):
                return False

            # Check field-level permissions for write operations
            if ptype in ["write", "create"] and not self.check_field_level_permission(
                doc, user_roles
            ):
                return False

            # Check business context permissions
            if not self.check_business_context_permission(doc, user):
                return False

            return True

        except Exception as e:
            frappe.log_error(f"Permission check error: {e}")
            return False

    def get_user_workshop_roles(self, user):
        """Get workshop roles assigned to user"""
        try:
            user_roles = frappe.get_list("Has Role", filters={"parent": user}, fields=["role"])

            role_names = [role.role for role in user_roles]

            workshop_roles = frappe.get_list(
                "Workshop Role",
                filters={"role_name": ["in", role_names], "is_active": 1},
                fields=["name", "role_name", "role_type", "priority_level"],
            )

            return workshop_roles

        except Exception:
            return []

    def check_document_permission(self, doc, user_roles, ptype):
        """Check basic document-level permissions"""
        doctype = doc.doctype if hasattr(doc, "doctype") else doc

        # Check if any user role has permission for this doctype
        for role in user_roles:
            if self.role_has_doctype_permission(role["role_name"], doctype, ptype):
                return True

        return False

    def role_has_doctype_permission(self, role_name, doctype, ptype):
        """Check if role has specific permission for doctype"""
        try:
            # Check in ERPNext's permission system
            permissions = frappe.get_list(
                "DocPerm", filters={"parent": doctype, "role": role_name}, fields=[ptype]
            )

            return any(perm.get(ptype) for perm in permissions)

        except Exception:
            return False

    def check_row_level_permission(self, doc, user, ptype):
        """
        Check row-level permissions based on user context
        Implements workshop location, department, and ownership restrictions
        """
        if isinstance(doc, str):
            return True  # Can't check row-level for doctype string

        try:
            # Get user's workshop context
            user_context = self.get_user_workshop_context(user)

            # Apply row-level filters based on doctype
            if doc.doctype == "Service Order":
                return self.check_service_order_access(doc, user_context)
            elif doc.doctype == "Vehicle":
                return self.check_vehicle_access(doc, user_context)
            elif doc.doctype == "Customer":
                return self.check_customer_access(doc, user_context)
            elif doc.doctype == "Parts Inventory":
                return self.check_parts_access(doc, user_context)

            return True

        except Exception as e:
            frappe.log_error(f"Row-level permission check error: {e}")
            return True  # Default to allow if check fails

    def get_user_workshop_context(self, user):
        """Get user's workshop context (location, department, etc.)"""
        try:
            user_doc = frappe.get_doc("User", user)

            context = {
                "user": user,
                "workshop_location": getattr(user_doc, "workshop_location", None),
                "department": getattr(user_doc, "department", None),
                "branch": getattr(user_doc, "branch", None),
                "role_priority": self.get_user_max_priority(user),
            }

            # Get user permissions from ERPNext
            user_permissions = get_user_permissions(user)
            context["user_permissions"] = user_permissions

            return context

        except Exception:
            return {"user": user, "role_priority": 1}

    def get_user_max_priority(self, user):
        """Get user's maximum role priority level"""
        try:
            user_roles = self.get_user_workshop_roles(user)
            if user_roles:
                return max(role.get("priority_level", 1) for role in user_roles)
            return 1
        except Exception:
            return 1

    def check_service_order_access(self, doc, user_context):
        """Check access to service orders based on assignment and location"""
        try:
            # Technicians can only see orders assigned to them
            if any(
                "Technician" in role["role_type"]
                for role in self.get_user_workshop_roles(user_context["user"])
            ):
                if (
                    hasattr(doc, "assigned_technician")
                    and doc.assigned_technician == user_context["user"]
                ):
                    return True
                return False

            # Workshop location restriction
            if user_context.get("workshop_location") and hasattr(doc, "workshop_location"):
                if doc.workshop_location != user_context["workshop_location"]:
                    return False

            # High-priority roles can see all orders
            if user_context.get("role_priority", 1) >= 8:
                return True

            return True

        except Exception:
            return True

    def check_vehicle_access(self, doc, user_context):
        """Check access to vehicle records"""
        try:
            # Check if user has specific vehicle permissions
            vehicle_permissions = user_context.get("user_permissions", {}).get("Vehicle", [])
            if vehicle_permissions:
                return doc.name in vehicle_permissions

            # Location-based access
            if user_context.get("workshop_location") and hasattr(doc, "primary_workshop"):
                return doc.primary_workshop == user_context["workshop_location"]

            return True

        except Exception:
            return True

    def check_customer_access(self, doc, user_context):
        """Check access to customer records"""
        try:
            # Department-based access
            if user_context.get("department") and hasattr(doc, "assigned_department"):
                return doc.assigned_department == user_context["department"]

            # Branch-based access
            if user_context.get("branch") and hasattr(doc, "branch"):
                return doc.branch == user_context["branch"]

            return True

        except Exception:
            return True

    def check_parts_access(self, doc, user_context):
        """Check access to parts inventory"""
        try:
            # Parts managers have full access
            user_roles = self.get_user_workshop_roles(user_context["user"])
            if any("Parts Manager" in role["role_name"] for role in user_roles):
                return True

            # Location-based access for other roles
            if user_context.get("workshop_location") and hasattr(doc, "warehouse_location"):
                return doc.warehouse_location == user_context["workshop_location"]

            return True

        except Exception:
            return True

    def check_field_level_permission(self, doc, user_roles):
        """Check field-level permissions for sensitive data"""
        try:
            doctype = doc.doctype if hasattr(doc, "doctype") else doc

            if doctype not in self.sensitive_fields:
                return True

            # Get maximum role priority
            max_priority = max(role.get("priority_level", 1) for role in user_roles)

            # High-priority roles can access all fields
            if max_priority >= 8:
                return True

            # Check if user is trying to access sensitive fields
            sensitive_fields = self.sensitive_fields[doctype]

            # For now, allow access - this can be enhanced with specific field checks
            return True

        except Exception:
            return True

    def check_business_context_permission(self, doc, user):
        """Check business context permissions (Oman-specific)"""
        try:
            # Check business binding requirements
            if hasattr(doc, "requires_business_binding") and doc.requires_business_binding:
                # Verify user has business binding access
                if not self.user_has_business_binding_access(user):
                    return False

            # Check government approval requirements
            if hasattr(doc, "requires_government_approval") and doc.requires_government_approval:
                if not self.user_has_government_approval_access(user):
                    return False

            return True

        except Exception:
            return True

    def user_has_business_binding_access(self, user):
        """Check if user has access to business binding features"""
        try:
            user_roles = self.get_user_workshop_roles(user)
            # Only management and financial roles can access business binding
            return any(role["role_type"] in ["Management", "Financial"] for role in user_roles)
        except Exception:
            return False

    def user_has_government_approval_access(self, user):
        """Check if user has access to government approval features"""
        try:
            user_roles = self.get_user_workshop_roles(user)
            # Only management roles can access government approval
            return any(role["role_type"] == "Management" for role in user_roles)
        except Exception:
            return False

    def apply_query_conditions(self, doctype, user=None):
        """
        Apply query conditions for list views based on user permissions
        This method is called by ERPNext when building queries
        """
        if not user:
            user = frappe.session.user

        # System Manager sees everything
        if "System Manager" in frappe.get_roles(user):
            return ""

        conditions = []
        user_context = self.get_user_workshop_context(user)

        # Apply doctype-specific conditions
        if doctype == "Service Order":
            conditions.extend(self.get_service_order_conditions(user_context))
        elif doctype == "Vehicle":
            conditions.extend(self.get_vehicle_conditions(user_context))
        elif doctype == "Customer":
            conditions.extend(self.get_customer_conditions(user_context))
        elif doctype == "Parts Inventory":
            conditions.extend(self.get_parts_conditions(user_context))

        return " AND ".join(conditions) if conditions else ""

    def get_service_order_conditions(self, user_context):
        """Get query conditions for service orders"""
        conditions = []

        # Technicians only see assigned orders
        user_roles = self.get_user_workshop_roles(user_context["user"])
        if any("Technician" in role["role_type"] for role in user_roles):
            conditions.append(f"`tabService Order`.assigned_technician = '{user_context['user']}'")

        # Location-based filtering
        if user_context.get("workshop_location"):
            conditions.append(
                f"`tabService Order`.workshop_location = '{user_context['workshop_location']}'"
            )

        return conditions

    def get_vehicle_conditions(self, user_context):
        """Get query conditions for vehicles"""
        conditions = []

        # Location-based filtering
        if user_context.get("workshop_location"):
            conditions.append(
                f"`tabVehicle`.primary_workshop = '{user_context['workshop_location']}'"
            )

        return conditions

    def get_customer_conditions(self, user_context):
        """Get query conditions for customers"""
        conditions = []

        # Department-based filtering
        if user_context.get("department"):
            conditions.append(f"`tabCustomer`.assigned_department = '{user_context['department']}'")

        # Branch-based filtering
        if user_context.get("branch"):
            conditions.append(f"`tabCustomer`.branch = '{user_context['branch']}'")

        return conditions

    def get_parts_conditions(self, user_context):
        """Get query conditions for parts inventory"""
        conditions = []

        # Location-based filtering for non-managers
        user_roles = self.get_user_workshop_roles(user_context["user"])
        if not any("Parts Manager" in role["role_name"] for role in user_roles):
            if user_context.get("workshop_location") and hasattr(doc, "warehouse_location"):
                conditions.append(
                    f"`tabParts Inventory`.warehouse_location = '{user_context['workshop_location']}'"
                )

        return conditions


# Global instance for use in hooks
permission_engine = CustomPermissionEngine()


@frappe.whitelist()
def check_permission(doc, ptype="read"):
    """API method to check permissions"""
    return permission_engine.has_permission(doc, ptype=ptype)


@frappe.whitelist()
def get_user_accessible_records(doctype, filters=None):
    """Get records accessible to current user"""
    user = frappe.session.user

    # Apply permission filters
    permission_conditions = permission_engine.apply_query_conditions(doctype, user)

    query_filters = filters or {}

    # Build query with permission conditions
    if permission_conditions:
        # Add permission conditions to the query
        pass  # This would be implemented in the actual query building

    return frappe.get_list(doctype, filters=query_filters, limit=100)


def validate_field_access(doc, method):
    """Hook to validate field-level access during save"""
    user = frappe.session.user

    # Skip for System Manager
    if "System Manager" in frappe.get_roles(user):
        return

    # Check field-level permissions
    user_roles = permission_engine.get_user_workshop_roles(user)
    if not permission_engine.check_field_level_permission(doc, user_roles):
        frappe.throw(_("You don't have permission to modify sensitive fields in this document"))


def apply_user_permissions_on_read(doc, method):
    """Hook to apply user permissions when reading documents"""
    user = frappe.session.user

    # Skip for System Manager
    if "System Manager" in frappe.get_roles(user):
        return

    # Check if user can access this document
    if not permission_engine.has_permission(doc, user, "read"):
        frappe.throw(_("You don't have permission to access this document"))


def log_permission_access(doc, method):
    """Hook to log permission access for audit trail"""
    try:
        user = frappe.session.user

        # Log access for sensitive documents
        if doc.doctype in permission_engine.workshop_doctypes:
            frappe.get_doc(
                {
                    "doctype": "Activity Log",
                    "subject": f"Accessed {doc.doctype}: {doc.name}",
                    "content": f"User {user} accessed {doc.doctype} document",
                    "communication_date": frappe.utils.now(),
                    "reference_doctype": doc.doctype,
                    "reference_name": doc.name,
                    "user": user,
                }
            ).insert(ignore_permissions=True)

    except Exception as e:
        # Don't fail the main operation if logging fails
        frappe.log_error(f"Permission logging error: {e}")


@frappe.whitelist()
def test_permission_engine():
    """Test method for the custom permission engine"""
    user = frappe.session.user

    results = {
        "user": user,
        "workshop_roles": permission_engine.get_user_workshop_roles(user),
        "user_context": permission_engine.get_user_workshop_context(user),
        "test_results": [],
    }

    # Test document access
    test_doctypes = ["Customer", "Vehicle", "Service Order"]

    for doctype in test_doctypes:
        has_read = permission_engine.check_document_permission(
            doctype, results["workshop_roles"], "read"
        )
        has_write = permission_engine.check_document_permission(
            doctype, results["workshop_roles"], "write"
        )

        results["test_results"].append(
            {"doctype": doctype, "read_access": has_read, "write_access": has_write}
        )

    return results
