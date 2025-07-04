# Copyright (c) 2025, Universal Workshop ERP and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class WorkshopPermissionProfile(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields to Document class

    def validate(self):
        """Validate workshop permission profile data before saving"""
        self.validate_arabic_name()
        self.validate_duplicate_roles()
        self.validate_permission_conflicts()

    def validate_arabic_name(self):
        """Ensure Arabic profile name is provided"""
        if not self.profile_name_ar:
            frappe.throw(_("Arabic profile name is required"))

        # Check for duplicate Arabic names
        existing = frappe.db.exists(
            "Workshop Permission Profile",
            {"profile_name_ar": self.profile_name_ar, "name": ["!=", self.name]},
        )
        if existing:
            frappe.throw(_("Arabic profile name '{0}' already exists").format(self.profile_name_ar))

    def validate_duplicate_roles(self):
        """Validate no duplicate roles in the profile"""
        if not self.workshop_roles:
            return

        seen_roles = set()
        for role_row in self.workshop_roles:
            if role_row.role_name in seen_roles:
                frappe.throw(_("Duplicate role found: {0}").format(role_row.role_name))
            seen_roles.add(role_row.role_name)

    def validate_permission_conflicts(self):
        """Validate no conflicting permissions"""
        if not self.document_permissions:
            return

        # Check for conflicting document permissions
        seen_permissions = set()
        for perm in self.document_permissions:
            perm_key = f"{perm.doctype_name}:{perm.permission_type}"
            if perm_key in seen_permissions:
                frappe.throw(
                    _("Duplicate permission found for {0}: {1}").format(
                        perm.doctype_name, perm.permission_type
                    )
                )
            seen_permissions.add(perm_key)

    def before_save(self):
        """Set default values before saving"""
        if not self.created_by:
            self.created_by = frappe.session.user
        if not self.created_date:
            self.created_date = frappe.utils.today()

        self.modified_date = frappe.utils.today()

    def after_insert(self):
        """Apply permissions after profile creation"""
        self.apply_profile_permissions()

    def on_update(self):
        """Update permissions when profile is modified"""
        if not self.is_new():
            self.apply_profile_permissions()

    def apply_profile_permissions(self):
        """Apply the permission profile to associated roles"""
        try:
            from universal_workshop.user_management.permission_manager import (
                WorkshopPermissionManager,
            )

            permission_manager = WorkshopPermissionManager()

            # Apply document permissions
            for role_row in self.workshop_roles:
                for doc_perm in self.document_permissions:
                    permissions = {doc_perm.permission_type.lower(): 1}
                    permission_manager.set_doctype_permissions(
                        doc_perm.doctype_name, role_row.role_name, permissions
                    )

            frappe.db.commit()

        except Exception as e:
            frappe.log_error(f"Error applying permission profile: {e}")


@frappe.whitelist()
def create_default_permission_profiles():
    """Create default permission profiles for workshop operations"""
    default_profiles = [
        {
            "profile_name": "Workshop Management Profile",
            "profile_name_ar": "ملف إدارة الورشة",
            "description": "Full management permissions for workshop operations",
            "description_ar": "صلاحيات إدارية كاملة لعمليات الورشة",
        },
        {
            "profile_name": "Technical Staff Profile",
            "profile_name_ar": "ملف الموظفين التقنيين",
            "description": "Technical staff permissions for service operations",
            "description_ar": "صلاحيات الموظفين التقنيين لعمليات الخدمة",
        },
        {
            "profile_name": "Administrative Profile",
            "profile_name_ar": "الملف الإداري",
            "description": "Administrative permissions for customer and appointment management",
            "description_ar": "صلاحيات إدارية لإدارة العملاء والمواعيد",
        },
    ]

    created_profiles = []
    for profile_data in default_profiles:
        # Check if profile already exists
        if not frappe.db.exists("Workshop Permission Profile", profile_data["profile_name"]):
            profile_doc = frappe.new_doc("Workshop Permission Profile")
            profile_doc.update(profile_data)
            profile_doc.is_active = 1
            profile_doc.insert()
            created_profiles.append(profile_data["profile_name"])

    frappe.db.commit()

    if created_profiles:
        frappe.msgprint(
            _("Created default permission profiles: {0}").format(", ".join(created_profiles))
        )
    else:
        frappe.msgprint(_("All default permission profiles already exist"))

    return created_profiles


@frappe.whitelist()
def get_profile_permissions(profile_name):
    """Get all permissions associated with a profile"""
    try:
        profile = frappe.get_doc("Workshop Permission Profile", profile_name)

        permissions_data = {"roles": [], "document_permissions": [], "field_permissions": []}

        # Get associated roles
        for role_row in profile.workshop_roles:
            role_data = frappe.get_doc("Workshop Role", role_row.role_name)
            permissions_data["roles"].append(
                {
                    "role_name": role_data.role_name,
                    "role_name_ar": role_data.role_name_ar,
                    "role_type": role_data.role_type,
                    "priority_level": role_data.priority_level,
                }
            )

        # Get document permissions
        for doc_perm in profile.document_permissions:
            permissions_data["document_permissions"].append(
                {
                    "doctype_name": doc_perm.doctype_name,
                    "permission_type": doc_perm.permission_type,
                    "permission_level": doc_perm.permission_level,
                }
            )

        # Get field permissions
        for field_perm in profile.field_permissions:
            permissions_data["field_permissions"].append(
                {
                    "doctype_name": field_perm.doctype_name,
                    "field_name": field_perm.field_name,
                    "permission_level": field_perm.permission_level,
                }
            )

        return permissions_data

    except Exception as e:
        frappe.log_error(f"Error getting profile permissions: {e}")
        frappe.throw(_("Failed to get profile permissions"))


@frappe.whitelist()
def assign_profile_to_user(user_id, profile_name):
    """Assign a permission profile to a user"""
    try:
        profile = frappe.get_doc("Workshop Permission Profile", profile_name)

        # Get all roles from the profile
        for role_row in profile.workshop_roles:
            # Check if user already has this role
            if not frappe.db.exists("Has Role", {"parent": user_id, "role": role_row.role_name}):
                # Add role to user
                user_role = frappe.new_doc("Has Role")
                user_role.parent = user_id
                user_role.parenttype = "User"
                user_role.parentfield = "roles"
                user_role.role = role_row.role_name
                user_role.insert()

        frappe.db.commit()
        frappe.msgprint(
            _("Permission profile '{0}' assigned to user successfully").format(profile_name)
        )

        return True

    except Exception as e:
        frappe.log_error(f"Error assigning profile to user: {e}")
        frappe.throw(_("Failed to assign permission profile to user"))
        return False
