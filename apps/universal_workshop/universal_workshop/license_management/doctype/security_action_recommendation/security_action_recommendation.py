"""
Security Action Recommendation DocType
Manages security recommendations and action items for license management
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate, getdate, cint, flt


class SecurityActionRecommendation(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields to Document class
    
    def validate(self):
        """Validate the security action recommendation"""
        self.validate_priority()
        self.validate_due_date()
        self.validate_implementation_status()
    
    def validate_priority(self):
        """Validate priority field"""
        if not self.priority:
            self.priority = "Medium"
        
        valid_priorities = ["Low", "Medium", "High", "Critical"]
        if self.priority not in valid_priorities:
            frappe.throw(_("Priority must be one of: {0}").format(", ".join(valid_priorities)))
    
    def validate_due_date(self):
        """Validate due date"""
        if self.due_date and getdate(self.due_date) < getdate(nowdate()):
            if self.implementation_status != "Completed":
                frappe.msgprint(_("Due date is in the past"), indicator="orange")
    
    def validate_implementation_status(self):
        """Validate implementation status"""
        if not self.implementation_status:
            self.implementation_status = "Pending"
        
        valid_statuses = ["Pending", "In Progress", "Completed", "Cancelled"]
        if self.implementation_status not in valid_statuses:
            frappe.throw(_("Implementation Status must be one of: {0}").format(", ".join(valid_statuses)))
    
    def before_save(self):
        """Actions before saving"""
        if self.implementation_status == "Completed" and not self.get_doc_before_save():
            # Log completion
            frappe.log_error(
                message=f"Security Action Recommendation {self.name} marked as completed",
                title="Security Action Completed"
            )
    
    def on_update(self):
        """Actions after update"""
        if self.has_value_changed("implementation_status"):
            self.update_related_security_audit()
    
    def update_related_security_audit(self):
        """Update related security audit status"""
        try:
            # Check if there are related security audits that need updating
            # This would be implemented based on actual relationship structure
            pass
        except Exception as e:
            frappe.log_error(f"Error updating related security audit: {e}")


# API Methods
@frappe.whitelist()
def get_pending_actions(filters=None):
    """Get list of pending security actions"""
    
    if not filters:
        filters = {}
    
    # Add default filter for non-completed actions
    filters.update({
        "implementation_status": ["!=", "Completed"],
        "docstatus": ["!=", 2]  # Not cancelled
    })
    
    actions = frappe.get_all(
        "Security Action Recommendation",
        filters=filters,
        fields=[
            "name", "action_type", "action_description", "priority",
            "implementation_status", "responsible_party", "due_date",
            "estimated_effort"
        ],
        order_by="priority desc, due_date asc"
    )
    
    return actions


@frappe.whitelist()
def get_security_metrics():
    """Get security action metrics"""
    
    total_actions = frappe.db.count("Security Action Recommendation", {"docstatus": ["!=", 2]})
    
    completed_actions = frappe.db.count(
        "Security Action Recommendation", 
        {"implementation_status": "Completed", "docstatus": ["!=", 2]}
    )
    
    pending_actions = frappe.db.count(
        "Security Action Recommendation",
        {"implementation_status": ["!=", "Completed"], "docstatus": ["!=", 2]}
    )
    
    overdue_actions = frappe.db.sql("""
        SELECT COUNT(*) as count
        FROM `tabSecurity Action Recommendation`
        WHERE due_date < %s 
        AND implementation_status != 'Completed'
        AND docstatus != 2
    """, (nowdate(),))[0][0]
    
    critical_actions = frappe.db.count(
        "Security Action Recommendation",
        {"priority": "Critical", "implementation_status": ["!=", "Completed"], "docstatus": ["!=", 2]}
    )
    
    return {
        "total_actions": total_actions,
        "completed_actions": completed_actions,
        "pending_actions": pending_actions,
        "overdue_actions": overdue_actions,
        "critical_actions": critical_actions,
        "completion_rate": round((completed_actions / total_actions * 100), 2) if total_actions > 0 else 0
    }