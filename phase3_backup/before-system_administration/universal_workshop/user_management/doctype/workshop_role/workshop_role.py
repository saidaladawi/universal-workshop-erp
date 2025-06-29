# Copyright (c) 2025, Universal Workshop ERP and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class WorkshopRole(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields to Document class

    def validate(self):
        """Validate workshop role data before saving"""
        self.validate_arabic_name()
        self.validate_priority_level()
        self.set_arabic_display_name()
        self.validate_role_permissions()

    def validate_arabic_name(self):
        """Ensure Arabic role name is provided"""
        if not self.role_name_ar:
            frappe.throw(_("Arabic role name is required"))

        # Check for duplicate Arabic names
        existing = frappe.db.exists(
            "Workshop Role", {"role_name_ar": self.role_name_ar, "name": ["!=", self.name]}
        )
        if existing:
            frappe.throw(_("Arabic role name '{0}' already exists").format(self.role_name_ar))

    def validate_priority_level(self):
        """Validate priority level is within acceptable range"""
        if self.priority_level and (self.priority_level < 1 or self.priority_level > 10):
            frappe.throw(_("Priority level must be between 1 and 10"))

    def set_arabic_display_name(self):
        """Set the Arabic display name for UI rendering"""
        if self.role_name_ar:
            self.arabic_role_display = self.role_name_ar

    def validate_role_permissions(self):
        """Validate workshop permissions configuration"""
        if not self.workshop_permissions:
            return

        # Check for duplicate permissions
        seen_permissions = set()
        for perm in self.workshop_permissions:
            perm_key = f"{perm.doctype_name}:{perm.permission_type}"
            if perm_key in seen_permissions:
                frappe.throw(_("Duplicate permission found for {0}").format(perm.doctype_name))
            seen_permissions.add(perm_key)

    def before_save(self):
        """Set default values before saving"""
        if not self.is_active:
            self.is_active = 1
        if not self.priority_level:
            self.priority_level = 5

    def after_insert(self):
        """Create corresponding ERPNext role after insert"""
        self.create_erpnext_role()

    def create_erpnext_role(self):
        """Create corresponding role in ERPNext Role master"""
        try:
            # Check if ERPNext role already exists
            if not frappe.db.exists("Role", self.role_name):
                role_doc = frappe.new_doc("Role")
                role_doc.role_name = self.role_name
                role_doc.disabled = 0 if self.is_active else 1
                role_doc.insert()
                frappe.db.commit()

                frappe.msgprint(_("ERPNext role '{0}' created successfully").format(self.role_name))
        except Exception as e:
            frappe.log_error(f"Error creating ERPNext role: {e}")
            frappe.throw(_("Failed to create ERPNext role: {0}").format(str(e)))

    def on_update(self):
        """Update corresponding ERPNext role when workshop role is updated"""
        self.update_erpnext_role()

    def update_erpnext_role(self):
        """Update corresponding ERPNext role"""
        try:
            if frappe.db.exists("Role", self.role_name):
                role_doc = frappe.get_doc("Role", self.role_name)
                role_doc.disabled = 0 if self.is_active else 1
                role_doc.save()
                frappe.db.commit()
        except Exception as e:
            frappe.log_error(f"Error updating ERPNext role: {e}")


@frappe.whitelist()
def get_workshop_roles_for_user(user_id=None):
    """Get workshop roles assigned to a user with Arabic support"""
    if not user_id:
        user_id = frappe.session.user

    # Get user roles from ERPNext
    user_roles = frappe.get_list("Has Role", filters={"parent": user_id}, fields=["role"])

    role_names = [role.role for role in user_roles]

    # Get corresponding workshop roles
    workshop_roles = frappe.get_list(
        "Workshop Role",
        filters={"role_name": ["in", role_names], "is_active": 1},
        fields=["name", "role_name", "role_name_ar", "role_type", "priority_level"],
    )

    return workshop_roles


@frappe.whitelist()
def create_default_workshop_roles():
    """Create default workshop roles for automotive workshop"""
    default_roles = [
        {
            "role_name": "Workshop Manager",
            "role_name_ar": "مدير الورشة",
            "role_description": "Full access to all workshop operations and management functions",
            "role_description_ar": "وصول كامل لجميع عمليات الورشة ووظائف الإدارة",
            "role_type": "Management",
            "priority_level": 10,
        },
        {
            "role_name": "Service Advisor",
            "role_name_ar": "مستشار الخدمة",
            "role_description": "Customer interaction, job creation, and service coordination",
            "role_description_ar": "التفاعل مع العملاء وإنشاء الوظائف وتنسيق الخدمة",
            "role_type": "Operational",
            "priority_level": 8,
        },
        {
            "role_name": "Workshop Technician",
            "role_name_ar": "فني الورشة",
            "role_description": "Vehicle repair and maintenance tasks",
            "role_description_ar": "مهام إصلاح وصيانة المركبات",
            "role_type": "Technical",
            "priority_level": 6,
        },
        {
            "role_name": "Parts Manager",
            "role_name_ar": "مدير قطع الغيار",
            "role_description": "Inventory management and parts procurement",
            "role_description_ar": "إدارة المخزون وشراء قطع الغيار",
            "role_type": "Operational",
            "priority_level": 7,
        },
        {
            "role_name": "Workshop Receptionist",
            "role_name_ar": "موظف استقبال الورشة",
            "role_description": "Customer reception, appointment scheduling, and basic data entry",
            "role_description_ar": "استقبال العملاء وجدولة المواعيد وإدخال البيانات الأساسية",
            "role_type": "Administrative",
            "priority_level": 4,
        },
        {
            "role_name": "Financial Staff",
            "role_name_ar": "الموظف المالي",
            "role_description": "Billing, payments, and financial reporting",
            "role_description_ar": "الفوترة والمدفوعات والتقارير المالية",
            "role_type": "Financial",
            "priority_level": 9,
        },
    ]

    created_roles = []
    for role_data in default_roles:
        # Check if role already exists
        if not frappe.db.exists("Workshop Role", role_data["role_name"]):
            role_doc = frappe.new_doc("Workshop Role")
            role_doc.update(role_data)
            role_doc.is_active = 1
            role_doc.supports_arabic_ui = 1
            role_doc.insert()
            created_roles.append(role_data["role_name"])

    frappe.db.commit()

    if created_roles:
        frappe.msgprint(_("Created default workshop roles: {0}").format(", ".join(created_roles)))
    else:
        frappe.msgprint(_("All default workshop roles already exist"))

    return created_roles


@frappe.whitelist()
def get_role_hierarchy():
    """Get workshop role hierarchy based on priority levels"""
    roles = frappe.get_list(
        "Workshop Role",
        filters={"is_active": 1},
        fields=["name", "role_name", "role_name_ar", "role_type", "priority_level"],
        order_by="priority_level desc",
    )

    # Group by role type
    hierarchy = {}
    for role in roles:
        role_type = role.role_type
        if role_type not in hierarchy:
            hierarchy[role_type] = []
        hierarchy[role_type].append(role)

    return hierarchy
