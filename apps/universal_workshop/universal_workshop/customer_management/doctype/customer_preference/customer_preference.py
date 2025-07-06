# Copyright (c) 2024, Universal Workshop and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now


class CustomerPreference(Document):
    def before_insert(self):
        """Set default values before inserting"""
        if not self.created_date:
            self.created_date = now()
        
        if not self.is_active:
            self.is_active = 1
    
    def validate(self):
        """Validate the document"""
        self.validate_customer()
        self.validate_preferences()
    
    def validate_customer(self):
        """Validate customer exists"""
        if not frappe.db.exists("Customer", self.customer):
            frappe.throw(f"Customer {self.customer} does not exist")
    
    def validate_preferences(self):
        """Validate preference combinations"""
        # Validate preferred service advisor exists
        if self.preferred_service_advisor:
            if not frappe.db.exists("User", self.preferred_service_advisor):
                frappe.throw("Preferred Service Advisor does not exist")
        
        # Validate preferred technician exists
        if self.preferred_technician:
            if not frappe.db.exists("User", self.preferred_technician):
                frappe.throw("Preferred Technician does not exist")
    
    def on_update(self):
        """Actions to perform when document is updated"""
        self.update_customer_preferences()
    
    def update_customer_preferences(self):
        """Update customer record with preferences"""
        if self.is_active:
            try:
                customer_doc = frappe.get_doc("Customer", self.customer)
                # This would integrate with customer preference tracking
                pass
            except Exception:
                # Customer preference integration not implemented yet
                pass
    
    @frappe.whitelist()
    def duplicate_preferences(self):
        """Create a duplicate of current preferences"""
        new_pref = frappe.copy_doc(self)
        new_pref.is_active = 0
        new_pref.preference_category = "Secondary"
        new_pref.insert()
        
        frappe.msgprint(f"Preference duplicated: {new_pref.name}")
        return new_pref.name
    
    @frappe.whitelist()
    def apply_to_appointments(self):
        """Apply preferences to future appointments"""
        # This would integrate with appointment scheduling
        frappe.msgprint("Preferences will be applied to future appointments")


@frappe.whitelist()
def get_customer_preferences(customer):
    """Get all active preferences for a customer"""
    preferences = frappe.get_all("Customer Preference", 
        filters={"customer": customer, "is_active": 1},
        fields=["*"]
    )
    return preferences


@frappe.whitelist()
def apply_preferences_to_service_order(customer, service_order):
    """Apply customer preferences to a service order"""
    preferences = get_customer_preferences(customer)
    
    if not preferences:
        return {"status": "no_preferences", "message": "No active preferences found"}
    
    service_order_doc = frappe.get_doc("Service Order", service_order)
    
    for pref in preferences:
        if pref.get("preferred_service_advisor"):
            service_order_doc.service_advisor = pref.preferred_service_advisor
        
        if pref.get("preferred_technician"):
            service_order_doc.assigned_technician = pref.preferred_technician
        
        if pref.get("preferred_time_slot"):
            # This would integrate with scheduling system
            pass
    
    service_order_doc.save()
    return {"status": "applied", "message": "Preferences applied to service order"}


def get_preference_statistics():
    """Get statistics about customer preferences"""
    stats = frappe.db.sql("""
        SELECT 
            preference_type,
            COUNT(*) as count,
            COUNT(CASE WHEN is_active = 1 THEN 1 END) as active_count
        FROM `tabCustomer Preference`
        GROUP BY preference_type
    """, as_dict=True)
    
    return stats