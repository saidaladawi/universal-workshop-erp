# Copyright (c) 2024, Universal Workshop and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now, add_days


class CustomerFeedback(Document):
    def before_insert(self):
        """Set default values before inserting"""
        if not self.feedback_date:
            self.feedback_date = now()
        
        if not self.status:
            self.status = "Open"
    
    def validate(self):
        """Validate the document"""
        self.validate_customer_and_vehicle()
        self.set_follow_up_date()
    
    def validate_customer_and_vehicle(self):
        """Validate customer and vehicle relationship"""
        if self.customer and self.vehicle:
            # Check if the vehicle belongs to the customer
            vehicle_doc = frappe.get_doc("Vehicle", self.vehicle)
            if vehicle_doc.customer != self.customer:
                frappe.throw("Selected vehicle does not belong to the customer")
    
    def set_follow_up_date(self):
        """Set follow-up date based on feedback type and response requirement"""
        if self.response_required and not self.follow_up_date:
            if self.feedback_type == "Complaint":
                self.follow_up_date = add_days(self.feedback_date, 1)
            elif self.feedback_type == "Suggestion":
                self.follow_up_date = add_days(self.feedback_date, 3)
            else:
                self.follow_up_date = add_days(self.feedback_date, 7)
    
    def on_update(self):
        """Actions to perform when document is updated"""
        self.check_response_completion()
        self.update_customer_satisfaction()
    
    def check_response_completion(self):
        """Check if response is completed and update status"""
        if self.response_details and self.responded_by and not self.response_date:
            self.response_date = now()
        
        if self.response_details and self.status == "Open":
            self.status = "Resolved"
    
    def update_customer_satisfaction(self):
        """Update customer satisfaction metrics"""
        if self.rating and self.customer:
            # Update customer's overall satisfaction rating
            try:
                customer_doc = frappe.get_doc("Customer", self.customer)
                # This would integrate with customer satisfaction tracking
                pass
            except Exception:
                # Customer satisfaction tracking not implemented yet
                pass
    
    @frappe.whitelist()
    def mark_as_resolved(self):
        """Mark feedback as resolved"""
        self.status = "Resolved"
        self.save()
        frappe.msgprint("Feedback marked as resolved")
    
    @frappe.whitelist()
    def create_follow_up(self):
        """Create follow-up feedback entry"""
        follow_up = frappe.copy_doc(self)
        follow_up.subject = f"Follow-up: {self.subject}"
        follow_up.feedback_type = "General Inquiry"
        follow_up.status = "Open"
        follow_up.feedback_date = now()
        follow_up.insert()
        
        frappe.msgprint(f"Follow-up feedback created: {follow_up.name}")
        return follow_up.name


def get_pending_feedback_count():
    """Get count of pending feedback items"""
    return frappe.db.count("Customer Feedback", {"status": ["in", ["Open", "In Progress"]]})


@frappe.whitelist()
def get_customer_feedback_summary(customer):
    """Get customer feedback summary"""
    feedback_data = frappe.db.sql("""
        SELECT 
            feedback_type,
            AVG(rating) as avg_rating,
            COUNT(*) as count
        FROM `tabCustomer Feedback`
        WHERE customer = %s
        GROUP BY feedback_type
    """, customer, as_dict=True)
    
    return feedback_data