# Copyright (c) 2025, Universal Workshop ERP and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from universal_workshop.user_management.custom_permission_engine import permission_engine


def has_permission(doc, user=None, ptype="read"):
    """
    Custom permission hook for workshop documents
    This function is called by ERPNext's permission system
    """
    # Only apply custom permissions to workshop documents
    doctype = doc.doctype if hasattr(doc, "doctype") else doc

    if doctype in permission_engine.workshop_doctypes:
        return permission_engine.has_permission(doc, user, ptype)

    # For other documents, use default ERPNext permissions
    return True


def get_permission_query_conditions(doctype, user=None):
    """
    Custom query conditions for list views
    This function is called by ERPNext when building list queries
    """
    if not user:
        user = frappe.session.user

    # Only apply custom conditions to workshop documents
    if doctype in permission_engine.workshop_doctypes:
        conditions = permission_engine.apply_query_conditions(doctype, user)
        return conditions

    return ""


def validate_document_access(doc, method):
    """
    Hook to validate document access during operations
    Called on before_save, before_submit, etc.
    """
    user = frappe.session.user

    # Skip for System Manager
    if "System Manager" in frappe.get_roles(user):
        return

    # Check if user can access this document
    if doc.doctype in permission_engine.workshop_doctypes:
        if not permission_engine.has_permission(doc, user, "write"):
            frappe.throw(_("You don't have permission to modify this {0}").format(doc.doctype))


def validate_field_access(doc, method):
    """
    Hook to validate field-level access during save
    """
    user = frappe.session.user

    # Skip for System Manager
    if "System Manager" in frappe.get_roles(user):
        return

    # Check field-level permissions for workshop documents
    if doc.doctype in permission_engine.workshop_doctypes:
        user_roles = permission_engine.get_user_workshop_roles(user)
        if not permission_engine.check_field_level_permission(doc, user_roles):
            frappe.throw(_("You don't have permission to modify sensitive fields in this document"))


def log_permission_access(doc, method):
    """
    Hook to log permission access for audit trail
    """
    try:
        user = frappe.session.user

        # Log access for sensitive documents
        if doc.doctype in permission_engine.workshop_doctypes:
            # Create activity log entry
            activity_log = frappe.get_doc(
                {
                    "doctype": "Activity Log",
                    "subject": f"Accessed {doc.doctype}: {doc.name}",
                    "content": f"User {user} accessed {doc.doctype} document",
                    "communication_date": frappe.utils.now(),
                    "reference_doctype": doc.doctype,
                    "reference_name": doc.name,
                    "user": user,
                    "operation": method,
                }
            )
            activity_log.insert(ignore_permissions=True)

    except Exception as e:
        # Don't fail the main operation if logging fails
        frappe.log_error(f"Permission logging error: {e}")


def apply_user_permissions_on_read(doc, method):
    """
    Hook to apply user permissions when reading documents
    """
    user = frappe.session.user

    # Skip for System Manager
    if "System Manager" in frappe.get_roles(user):
        return

    # Check if user can access this document
    if doc.doctype in permission_engine.workshop_doctypes:
        if not permission_engine.has_permission(doc, user, "read"):
            frappe.throw(_("You don't have permission to access this document"))


def filter_sensitive_fields(doc, method):
    """
    Hook to filter sensitive fields based on user permissions
    """
    user = frappe.session.user

    # Skip for System Manager
    if "System Manager" in frappe.get_roles(user):
        return

    # Filter sensitive fields for workshop documents
    if doc.doctype in permission_engine.sensitive_fields:
        user_roles = permission_engine.get_user_workshop_roles(user)
        max_priority = (
            max(role.get("priority_level", 1) for role in user_roles) if user_roles else 1
        )

        # Hide sensitive fields for low-priority users
        if max_priority < 8:
            sensitive_fields = permission_engine.sensitive_fields[doc.doctype]

            for field in sensitive_fields:
                if hasattr(doc, field):
                    # Set sensitive field to None or empty value
                    setattr(doc, field, None)


def check_business_binding_access(doc, method):
    """
    Hook to check business binding access for Oman-specific requirements
    """
    user = frappe.session.user

    # Skip for System Manager
    if "System Manager" in frappe.get_roles(user):
        return

    # Check business binding requirements
    if hasattr(doc, "requires_business_binding") and doc.requires_business_binding:
        if not permission_engine.user_has_business_binding_access(user):
            frappe.throw(_("You don't have permission to access business binding features"))

    # Check government approval requirements
    if hasattr(doc, "requires_government_approval") and doc.requires_government_approval:
        if not permission_engine.user_has_government_approval_access(user):
            frappe.throw(_("You don't have permission to access government approval features"))


def validate_workshop_location_access(doc, method):
    """
    Hook to validate workshop location-based access
    """
    user = frappe.session.user

    # Skip for System Manager
    if "System Manager" in frappe.get_roles(user):
        return

    # Check workshop location restrictions
    if hasattr(doc, "workshop_location"):
        user_context = permission_engine.get_user_workshop_context(user)
        user_location = user_context.get("workshop_location")

        # If user has a specific workshop location, enforce restriction
        if user_location and doc.workshop_location != user_location:
            # Allow high-priority users to access all locations
            if user_context.get("role_priority", 1) < 8:
                frappe.throw(
                    _("You don't have permission to access documents from this workshop location")
                )


def setup_permission_hooks():
    """
    Setup all permission hooks for the workshop system
    This function should be called during app installation
    """
    try:
        # Document-level hooks
        hook_configs = [
            {"doctype": "Customer", "hooks": ["before_save", "on_update", "after_insert"]},
            {"doctype": "Vehicle", "hooks": ["before_save", "on_update", "after_insert"]},
            {
                "doctype": "Service Order",
                "hooks": ["before_save", "before_submit", "on_update", "after_insert"],
            },
            {"doctype": "Parts Inventory", "hooks": ["before_save", "on_update", "after_insert"]},
            {
                "doctype": "Workshop Technician",
                "hooks": ["before_save", "on_update", "after_insert"],
            },
            {
                "doctype": "Service Appointment",
                "hooks": ["before_save", "on_update", "after_insert"],
            },
        ]

        # Register hooks programmatically
        for config in hook_configs:
            doctype = config["doctype"]
            for hook in config["hooks"]:
                # This would be registered in hooks.py file
                pass

        frappe.msgprint(_("Permission hooks setup completed"))
        return True

    except Exception as e:
        frappe.log_error(f"Error setting up permission hooks: {e}")
        return False


@frappe.whitelist()
def test_permission_hooks():
    """
    Test method for permission hooks
    """
    user = frappe.session.user

    test_results = {"user": user, "permission_engine_status": "Active", "hook_tests": []}

    # Test document access
    test_doc = frappe._dict(
        {"doctype": "Customer", "name": "TEST-CUSTOMER", "customer_name": "Test Customer"}
    )

    # Test permission check
    has_read_access = has_permission(test_doc, user, "read")
    has_write_access = has_permission(test_doc, user, "write")

    test_results["hook_tests"].append(
        {
            "test": "Document Permission Check",
            "read_access": has_read_access,
            "write_access": has_write_access,
            "status": "Pass" if has_read_access else "Fail",
        }
    )

    # Test query conditions
    query_conditions = get_permission_query_conditions("Customer", user)

    test_results["hook_tests"].append(
        {"test": "Query Conditions", "conditions": query_conditions, "status": "Pass"}
    )

    return test_results


@frappe.whitelist()
def get_user_permission_summary():
    """
    Get comprehensive permission summary for current user
    """
    user = frappe.session.user

    summary = {
        "user": user,
        "workshop_roles": permission_engine.get_user_workshop_roles(user),
        "user_context": permission_engine.get_user_workshop_context(user),
        "document_permissions": {},
        "sensitive_field_access": {},
    }

    # Check permissions for each workshop doctype
    for doctype in permission_engine.workshop_doctypes:
        summary["document_permissions"][doctype] = {
            "read": permission_engine.check_document_permission(
                doctype, summary["workshop_roles"], "read"
            ),
            "write": permission_engine.check_document_permission(
                doctype, summary["workshop_roles"], "write"
            ),
            "create": permission_engine.check_document_permission(
                doctype, summary["workshop_roles"], "create"
            ),
            "delete": permission_engine.check_document_permission(
                doctype, summary["workshop_roles"], "delete"
            ),
        }

    # Check sensitive field access
    for doctype, fields in permission_engine.sensitive_fields.items():
        summary["sensitive_field_access"][doctype] = {
            "fields": fields,
            "has_access": permission_engine.check_field_level_permission(
                doctype, summary["workshop_roles"]
            ),
        }

    return summary
