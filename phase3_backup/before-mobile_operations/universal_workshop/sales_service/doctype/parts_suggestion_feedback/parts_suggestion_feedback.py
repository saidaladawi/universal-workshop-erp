# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

# pylint: disable=no-member


class PartsSuggestionFeedback(Document):
    """Controller for Parts Suggestion Feedback DocType"""

    def validate(self):
        """Validate feedback data"""
        self.calculate_feedback_score()
        self.set_metadata()

    def before_save(self):
        """Set calculated fields before saving"""
        self.set_ml_training_weight()

    def calculate_feedback_score(self):
        """Calculate numerical feedback score for ML training"""

        base_score = 1.0 if self.was_useful else -1.0

        # Adjust score based on feedback reason
        reason_adjustments = {
            "Relevant to Service": 0.2,
            "Correct Vehicle Match": 0.2,
            "In Stock": 0.1,
            "Good Price": 0.1,
            "Customer Preference": 0.1,
            "Not Relevant": -0.3,
            "Wrong Vehicle": -0.3,
            "Out of Stock": -0.2,
            "Too Expensive": -0.1,
            "Poor Quality": -0.2,
        }

        if self.feedback_reason and self.feedback_reason in reason_adjustments:
            base_score += reason_adjustments[self.feedback_reason]

        # Adjust based on original confidence score
        if self.confidence_score:
            if self.was_useful and self.confidence_score < 0.5:
                # High value feedback for low confidence suggestions that worked
                base_score += 0.3
            elif not self.was_useful and self.confidence_score > 0.8:
                # High negative feedback for high confidence suggestions that didn't work
                base_score -= 0.2

        # Normalize to -1 to +1 range
        self.feedback_score = max(-1.0, min(1.0, base_score))

    def set_metadata(self):
        """Set metadata fields"""
        if not self.user:
            self.user = frappe.session.user

        if not self.feedback_date:
            self.feedback_date = frappe.utils.now()

        # Capture request metadata if available
        if hasattr(frappe.local, "request") and frappe.local.request:
            if not self.ip_address:
                self.ip_address = frappe.utils.get_client_ip()
            if not self.user_agent:
                self.user_agent = frappe.local.request.environ.get("HTTP_USER_AGENT", "")[:500]

    def set_ml_training_weight(self):
        """Set ML training weight based on various factors"""

        weight = 1.0

        # Increase weight for detailed feedback
        if self.feedback_reason and self.feedback_reason != "Other":
            weight += 0.2

        if self.user_notes and len(self.user_notes.strip()) > 10:
            weight += 0.1

        # Adjust weight based on user role
        user_roles = frappe.get_roles(self.user)
        if "Workshop Manager" in user_roles:
            weight += 0.3
        elif "Service Advisor" in user_roles:
            weight += 0.2
        elif "Technician" in user_roles:
            weight += 0.1

        # Reduce weight for very old feedback
        if self.feedback_date:
            days_old = (frappe.utils.today() - frappe.utils.getdate(self.feedback_date)).days
            if days_old > 30:
                weight *= 0.8
            elif days_old > 90:
                weight *= 0.6

        self.ml_training_weight = max(0.1, min(3.0, weight))

    def mark_as_processed(self):
        """Mark feedback as processed for ML training"""
        self.is_processed = 1
        self.processed_date = frappe.utils.now()
        self.save()

    @staticmethod
    def get_feedback_analytics():
        """Get analytics data for feedback optimization"""

        analytics = {}

        # Overall feedback stats
        total_feedback = frappe.db.count("Parts Suggestion Feedback")
        positive_feedback = frappe.db.count("Parts Suggestion Feedback", {"was_useful": 1})

        analytics["total_feedback"] = total_feedback
        analytics["positive_rate"] = (
            (positive_feedback / total_feedback * 100) if total_feedback > 0 else 0
        )

        # Feedback by reason
        reason_stats = frappe.db.sql(
            """
            SELECT feedback_reason, COUNT(*) as count,
                   AVG(CASE WHEN was_useful = 1 THEN 1 ELSE 0 END) * 100 as success_rate
            FROM `tabParts Suggestion Feedback`
            WHERE feedback_reason IS NOT NULL AND feedback_reason != ''
            GROUP BY feedback_reason
            ORDER BY count DESC
        """,
            as_dict=True,
        )

        analytics["feedback_by_reason"] = reason_stats

        # Feedback by service type
        service_stats = frappe.db.sql(
            """
            SELECT service_type, COUNT(*) as count,
                   AVG(feedback_score) as avg_score
            FROM `tabParts Suggestion Feedback`
            WHERE service_type IS NOT NULL
            GROUP BY service_type
            ORDER BY count DESC
            LIMIT 10
        """,
            as_dict=True,
        )

        analytics["feedback_by_service"] = service_stats

        # Confidence score analysis
        confidence_analysis = frappe.db.sql(
            """
            SELECT 
                CASE 
                    WHEN confidence_score >= 0.8 THEN 'High (0.8+)'
                    WHEN confidence_score >= 0.6 THEN 'Medium (0.6-0.8)'
                    WHEN confidence_score >= 0.4 THEN 'Low (0.4-0.6)'
                    ELSE 'Very Low (<0.4)'
                END as confidence_range,
                COUNT(*) as count,
                AVG(CASE WHEN was_useful = 1 THEN 1 ELSE 0 END) * 100 as success_rate,
                AVG(feedback_score) as avg_feedback_score
            FROM `tabParts Suggestion Feedback`
            WHERE confidence_score IS NOT NULL
            GROUP BY confidence_range
            ORDER BY MIN(confidence_score) DESC
        """,
            as_dict=True,
        )

        analytics["confidence_analysis"] = confidence_analysis

        # Recent trends (last 30 days)
        recent_trend = frappe.db.sql(
            """
            SELECT DATE(feedback_date) as date,
                   COUNT(*) as total_feedback,
                   SUM(CASE WHEN was_useful = 1 THEN 1 ELSE 0 END) as positive_feedback
            FROM `tabParts Suggestion Feedback`
            WHERE feedback_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            GROUP BY DATE(feedback_date)
            ORDER BY date DESC
        """,
            as_dict=True,
        )

        analytics["recent_trend"] = recent_trend

        return analytics


# Utility functions for ML training data export


@frappe.whitelist()
def export_training_data(start_date=None, end_date=None, min_confidence=0.3):
    """Export feedback data for ML model training"""

    conditions = ["f.is_processed = 0"]
    values = []

    if start_date:
        conditions.append("DATE(f.feedback_date) >= %s")
        values.append(start_date)

    if end_date:
        conditions.append("DATE(f.feedback_date) <= %s")
        values.append(end_date)

    if min_confidence:
        conditions.append("f.confidence_score >= %s")
        values.append(float(min_confidence))

    query = f"""
        SELECT 
            f.item_code,
            f.service_type,
            f.customer,
            se.vehicle,
            vm.make,
            vm.model,
            vm.year,
            f.confidence_score,
            f.suggestion_reason,
            f.availability_status,
            f.was_useful,
            f.feedback_score,
            f.ml_training_weight,
            f.feedback_reason
        FROM `tabParts Suggestion Feedback` f
        LEFT JOIN `tabService Estimate` se ON f.service_estimate = se.name
        LEFT JOIN `tabVehicle Master` vm ON se.vehicle = vm.name
        WHERE {' AND '.join(conditions)}
        ORDER BY f.feedback_date DESC
    """

    training_data = frappe.db.sql(query, values, as_dict=True)

    # Mark as processed
    if training_data:
        feedback_ids = [
            d["name"]
            for d in frappe.db.sql(
                f"""
            SELECT name FROM `tabParts Suggestion Feedback`
            WHERE {' AND '.join(conditions)}
        """,
                values,
                as_dict=True,
            )
        ]

        for feedback_id in feedback_ids:
            doc = frappe.get_doc("Parts Suggestion Feedback", feedback_id)
            doc.mark_as_processed()

    return training_data


@frappe.whitelist()
def get_feedback_analytics():
    """API endpoint for feedback analytics"""
    return PartsSuggestionFeedback.get_feedback_analytics()


@frappe.whitelist()
def bulk_process_feedback(feedback_ids):
    """Mark multiple feedback records as processed"""

    if isinstance(feedback_ids, str):
        feedback_ids = frappe.parse_json(feedback_ids)

    processed_count = 0

    for feedback_id in feedback_ids:
        try:
            doc = frappe.get_doc("Parts Suggestion Feedback", feedback_id)
            doc.mark_as_processed()
            processed_count += 1
        except Exception as e:
            frappe.log_error(f"Error processing feedback {feedback_id}: {str(e)}")

    return {
        "processed_count": processed_count,
        "total_requested": len(feedback_ids),
        "success": True,
    }


@frappe.whitelist()
def get_suggestion_performance_report(days=30, service_type=None):
    """Get performance report for suggestions"""

    conditions = [f"f.feedback_date >= DATE_SUB(CURDATE(), INTERVAL {int(days)} DAY)"]
    values = []

    if service_type:
        conditions.append("f.service_type = %s")
        values.append(service_type)

    query = f"""
        SELECT 
            f.suggestion_reason,
            COUNT(*) as total_suggestions,
            SUM(CASE WHEN f.was_useful = 1 THEN 1 ELSE 0 END) as successful_suggestions,
            AVG(f.confidence_score) as avg_confidence,
            AVG(f.feedback_score) as avg_feedback_score,
            COUNT(DISTINCT f.item_code) as unique_items,
            COUNT(DISTINCT f.customer) as unique_customers
        FROM `tabParts Suggestion Feedback` f
        WHERE {' AND '.join(conditions)}
        GROUP BY f.suggestion_reason
        ORDER BY total_suggestions DESC
    """

    performance_data = frappe.db.sql(query, values, as_dict=True)

    # Calculate success rates
    for row in performance_data:
        row["success_rate"] = (
            (row["successful_suggestions"] / row["total_suggestions"] * 100)
            if row["total_suggestions"] > 0
            else 0
        )

    return performance_data
