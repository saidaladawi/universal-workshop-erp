# Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class CustomerFeedback(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields

    def validate(self):
        """Validate customer feedback data"""
        self.validate_ratings()
        self.set_customer_details()

    def before_save(self):
        """Set default values before saving"""
        if not self.created_by:
            self.created_by = frappe.session.user
        if not self.created_date:
            self.created_date = frappe.utils.now()

    def validate_ratings(self):
        """Validate rating values are within acceptable range"""
        rating_fields = [
            "satisfaction_rating",
            "service_quality_rating",
            "staff_behavior_rating",
            "timeliness_rating",
            "value_for_money_rating",
        ]

        for field in rating_fields:
            rating = getattr(self, field, None)
            if rating and (rating < 1 or rating > 5):
                frappe.throw(_("Rating must be between 1 and 5 stars"))

    def set_customer_details(self):
        """Set customer name from customer link"""
        if self.customer:
            customer_data = frappe.db.get_value(
                "Customer", self.customer, ["customer_name", "customer_name_ar"], as_dict=True
            )
            if customer_data:
                self.customer_name = customer_data.customer_name
                self.customer_name_ar = customer_data.get("customer_name_ar", "")


@frappe.whitelist()
def get_customer_feedback_summary(customer=None, from_date=None, to_date=None):
    """Get customer feedback summary with statistics"""

    filters = {}
    if customer:
        filters["customer"] = customer
    if from_date:
        filters["feedback_date"] = [">=", from_date]
    if to_date:
        if "feedback_date" in filters:
            filters["feedback_date"] = ["between", [from_date, to_date]]
        else:
            filters["feedback_date"] = ["<=", to_date]

    # Get feedback records
    feedback_list = frappe.get_list(
        "Customer Feedback",
        filters=filters,
        fields=[
            "satisfaction_rating",
            "service_quality_rating",
            "staff_behavior_rating",
            "timeliness_rating",
            "value_for_money_rating",
            "overall_experience",
            "would_recommend",
            "return_customer",
        ],
    )

    if not feedback_list:
        return {
            "total_feedback": 0,
            "average_satisfaction": 0,
            "recommendation_rate": 0,
            "return_rate": 0,
        }

    # Calculate statistics
    total_feedback = len(feedback_list)
    satisfaction_sum = sum([f.satisfaction_rating or 0 for f in feedback_list])
    recommendation_count = sum([1 for f in feedback_list if f.would_recommend])
    return_count = sum([1 for f in feedback_list if f.return_customer])

    return {
        "total_feedback": total_feedback,
        "average_satisfaction": round(satisfaction_sum / total_feedback, 2),
        "recommendation_rate": round((recommendation_count / total_feedback) * 100, 1),
        "return_rate": round((return_count / total_feedback) * 100, 1),
    }


@frappe.whitelist()
def create_feedback_from_service_order(service_order):
    """Create feedback record from completed service order"""

    # Get service order details
    so_data = frappe.db.get_value(
        "Service Order", service_order, ["customer", "customer_name"], as_dict=True
    )

    if not so_data:
        frappe.throw(_("Service Order not found"))

    # Check if feedback already exists
    existing_feedback = frappe.db.exists("Customer Feedback", {"service_order": service_order})

    if existing_feedback:
        frappe.throw(_("Feedback already exists for this service order"))

    # Create new feedback record
    feedback = frappe.new_doc("Customer Feedback")
    feedback.customer = so_data.customer
    feedback.service_order = service_order
    feedback.feedback_date = frappe.utils.today()
    feedback.feedback_source = "Service Completion"

    return feedback
