"""
Receivables Management System for Universal Workshop ERP
Implements aging analysis, automated dunning, and Oman compliance requirements
Supports Arabic language and regional business practices

Enhanced for ERPNext v15 with:
- Background payment reconciliation
- Automated invoice generation
- Bank reconciliation integration
- Deferred revenue support
- Real-time AR reporting
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, cint, getdate, today, add_days, add_months, date_diff, nowdate
from datetime import datetime, timedelta
import json
from typing import Dict, List, Any, Tuple


class OmanReceivablesManager:
    """
    Comprehensive receivables management system for Oman market
    Handles aging analysis, automated dunning, and payment tracking
    """

    def __init__(self):
        self.currency = "OMR"
        self.precision = 3
        self.aging_buckets = [
            {"label": "Current", "label_ar": "حالي", "min_days": 0, "max_days": 0},
            {"label": "1-30 Days", "label_ar": "١-٣٠ يوم", "min_days": 1, "max_days": 30},
            {"label": "31-60 Days", "label_ar": "٣١-٦٠ يوم", "min_days": 31, "max_days": 60},
            {"label": "61-90 Days", "label_ar": "٦١-٩٠ يوم", "min_days": 61, "max_days": 90},
            {"label": "90+ Days", "label_ar": "٩٠+ يوم", "min_days": 91, "max_days": 999999},
        ]

    def generate_aging_analysis(
        self, company: str, as_on_date: str = "", language: str = "en"
    ) -> Dict[str, Any]:
        """
        Generate comprehensive aging analysis report

        Args:
            company: Company name
            as_on_date: Analysis date (defaults to today)
            language: Report language ('en' or 'ar')

        Returns:
            Dict containing aging analysis data
        """

        if not as_on_date:
            as_on_date = today()

        try:
            # Get outstanding invoices
            outstanding_invoices = self._get_outstanding_invoices(company, as_on_date)

            # Categorize by aging buckets
            aging_data = self._categorize_by_aging(outstanding_invoices, as_on_date)

            # Generate customer summaries
            customer_summaries = self._generate_customer_summaries(aging_data, language)

            # Calculate totals
            total_summary = self._calculate_total_summary(aging_data)

            # Generate recommendations
            recommendations = self._generate_aging_recommendations(aging_data, language)

            report = {
                "company": company,
                "as_on_date": as_on_date,
                "generated_on": today(),
                "generated_by": frappe.session.user,
                "language": language,
                "currency": self.currency,
                "precision": self.precision,
                "customer_summaries": customer_summaries,
                "total_summary": total_summary,
                "aging_buckets": self.aging_buckets,
                "recommendations": recommendations,
                "detailed_invoices": aging_data,
                # Statistics
                "total_customers": len(customer_summaries),
                "total_outstanding": total_summary["total_outstanding"],
                "overdue_amount": total_summary["overdue_amount"],
                "overdue_percentage": total_summary["overdue_percentage"],
            }

            return report

        except Exception as e:
            frappe.log_error(f"Aging analysis generation failed: {e}")
            raise frappe.ValidationError(_("Failed to generate aging analysis: {0}").format(str(e)))

    def _get_outstanding_invoices(self, company: str, as_on_date: str) -> List[Dict]:
        """Get all outstanding invoices for the company"""

        query = """
            SELECT 
                si.name as invoice_number,
                si.customer,
                c.customer_name,
                c.customer_name_ar,
                c.customer_group,
                c.territory,
                c.custom_whatsapp_number,
                c.custom_preferred_communication_language,
                c.custom_communication_opt_in,
                c.custom_credit_limit_omr,
                si.posting_date,
                si.due_date,
                si.base_grand_total as invoice_amount,
                si.outstanding_amount,
                si.currency,
                si.payment_terms_template,
                DATEDIFF(%s, si.due_date) as days_overdue,
                CASE 
                    WHEN si.due_date >= %s THEN 0
                    ELSE DATEDIFF(%s, si.due_date)
                END as aging_days,
                si.custom_payment_reminder_count,
                si.custom_last_reminder_date,
                si.custom_payment_follow_up_status,
                si.workflow_state,
                si.creation,
                si.modified
            FROM `tabSales Invoice` si
            LEFT JOIN `tabCustomer` c ON si.customer = c.name
            WHERE si.company = %s
            AND si.docstatus = 1
            AND si.outstanding_amount > 0
            AND si.posting_date <= %s
            ORDER BY si.customer, si.due_date
        """

        return frappe.db.sql(
            query, [as_on_date, as_on_date, as_on_date, company, as_on_date], as_dict=True
        )

    def _categorize_by_aging(self, invoices: List[Dict], as_on_date: str) -> Dict[str, List[Dict]]:
        """Categorize invoices by aging buckets"""

        categorized: Dict[str, List[Dict]] = {bucket["label"]: [] for bucket in self.aging_buckets}

        for invoice in invoices:
            aging_days = invoice.get("aging_days", 0)

            # Find appropriate bucket
            for bucket in self.aging_buckets:
                if bucket["min_days"] <= aging_days <= bucket["max_days"]:
                    categorized[bucket["label"]].append(invoice)
                    break

        return categorized

    def _generate_customer_summaries(self, aging_data: Dict, language: str) -> List[Dict]:
        """Generate customer-wise aging summaries"""

        customer_data = {}

        # Aggregate data by customer
        for bucket_name, invoices in aging_data.items():
            for invoice in invoices:
                customer_id = invoice["customer"]

                if customer_id not in customer_data:
                    customer_data[customer_id] = {
                        "customer_code": customer_id,
                        "customer_name": invoice["customer_name"],
                        "customer_name_ar": invoice.get("customer_name_ar", ""),
                        "customer_group": invoice.get("customer_group", ""),
                        "territory": invoice.get("territory", ""),
                        "whatsapp_number": invoice.get("custom_whatsapp_number", ""),
                        "preferred_language": invoice.get(
                            "custom_preferred_communication_language", "en"
                        ),
                        "communication_opt_in": invoice.get("custom_communication_opt_in", 0),
                        "credit_limit": flt(
                            invoice.get("custom_credit_limit_omr", 0), self.precision
                        ),
                        "total_outstanding": 0,
                        "invoice_count": 0,
                        "aging_breakdown": {bucket["label"]: 0 for bucket in self.aging_buckets},
                        "oldest_invoice_date": None,
                        "last_payment_date": None,
                        "overdue_invoices": 0,
                        "current_invoices": 0,
                    }

                customer_summary = customer_data[customer_id]
                customer_summary["total_outstanding"] += flt(
                    invoice["outstanding_amount"], self.precision
                )
                customer_summary["invoice_count"] += 1
                customer_summary["aging_breakdown"][bucket_name] += flt(
                    invoice["outstanding_amount"], self.precision
                )

                if bucket_name != "Current":
                    customer_summary["overdue_invoices"] += 1
                else:
                    customer_summary["current_invoices"] += 1

                # Track oldest invoice
                if (
                    not customer_summary["oldest_invoice_date"]
                    or invoice["posting_date"] < customer_summary["oldest_invoice_date"]
                ):
                    customer_summary["oldest_invoice_date"] = invoice["posting_date"]

        # Convert to list and add calculations
        summaries = []
        for customer_id, data in customer_data.items():
            # Calculate overdue percentage
            overdue_amount = data["total_outstanding"] - data["aging_breakdown"]["Current"]
            data["overdue_amount"] = flt(overdue_amount, self.precision)
            data["overdue_percentage"] = flt(
                (
                    (overdue_amount / data["total_outstanding"] * 100)
                    if data["total_outstanding"] > 0
                    else 0
                ),
                2,
            )

            # Credit utilization
            data["credit_utilization"] = flt(
                (
                    (data["total_outstanding"] / data["credit_limit"] * 100)
                    if data["credit_limit"] > 0
                    else 0
                ),
                2,
            )

            # Payment behavior score (1-10 scale)
            data["payment_behavior_score"] = self._calculate_payment_score(data)

            # Risk category
            data["risk_category"] = self._assess_customer_risk(data)

            summaries.append(data)

        # Sort by total outstanding (descending)
        summaries.sort(key=lambda x: x["total_outstanding"], reverse=True)

        return summaries

    def _calculate_total_summary(self, aging_data: Dict) -> Dict[str, Any]:
        """Calculate total summary across all customers"""

        summary = {
            "total_outstanding": 0,
            "total_invoices": 0,
            "aging_breakdown": {bucket["label"]: 0 for bucket in self.aging_buckets},
            "aging_breakdown_percentage": {bucket["label"]: 0 for bucket in self.aging_buckets},
        }

        for bucket_name, invoices in aging_data.items():
            bucket_total = sum(flt(inv["outstanding_amount"], self.precision) for inv in invoices)
            summary["aging_breakdown"][bucket_name] = bucket_total
            summary["total_outstanding"] += bucket_total
            summary["total_invoices"] += len(invoices)

        # Calculate percentages
        if summary["total_outstanding"] > 0:
            for bucket_name in summary["aging_breakdown"]:
                percentage = flt(
                    (summary["aging_breakdown"][bucket_name] / summary["total_outstanding"] * 100),
                    2,
                )
                summary["aging_breakdown_percentage"][bucket_name] = percentage

        # Calculate overdue metrics
        overdue_amount = summary["total_outstanding"] - summary["aging_breakdown"]["Current"]
        summary["overdue_amount"] = flt(overdue_amount, self.precision)
        summary["overdue_percentage"] = flt(
            (
                (overdue_amount / summary["total_outstanding"] * 100)
                if summary["total_outstanding"] > 0
                else 0
            ),
            2,
        )

        return summary

    def _calculate_payment_score(self, customer_data: Dict) -> int:
        """Calculate payment behavior score (1-10 scale)"""

        score = 10  # Start with perfect score

        # Deduct points for overdue amounts
        if customer_data["overdue_percentage"] > 50:
            score -= 4
        elif customer_data["overdue_percentage"] > 30:
            score -= 3
        elif customer_data["overdue_percentage"] > 10:
            score -= 2
        elif customer_data["overdue_percentage"] > 0:
            score -= 1

        # Deduct points for high credit utilization
        if customer_data["credit_utilization"] > 90:
            score -= 2
        elif customer_data["credit_utilization"] > 75:
            score -= 1

        # Deduct points for overdue invoice count
        if customer_data["overdue_invoices"] > 5:
            score -= 2
        elif customer_data["overdue_invoices"] > 2:
            score -= 1

        return max(1, score)  # Minimum score is 1

    def _assess_customer_risk(self, customer_data: Dict) -> str:
        """Assess customer risk level"""

        score = customer_data.get("payment_behavior_score", 5)
        overdue_percentage = customer_data.get("overdue_percentage", 0)

        if score >= 8 and overdue_percentage <= 10:
            return "Low Risk"
        elif score >= 6 and overdue_percentage <= 30:
            return "Medium Risk"
        elif score >= 4 and overdue_percentage <= 50:
            return "High Risk"
        else:
            return "Critical Risk"

    def _generate_aging_recommendations(self, aging_data: Dict, language: str) -> List[Dict]:
        """Generate actionable recommendations based on aging analysis"""

        recommendations = []

        # Analyze 30+ days overdue
        overdue_30_plus = []
        for bucket in ["31-60 Days", "61-90 Days", "90+ Days"]:
            overdue_30_plus.extend(aging_data.get(bucket, []))

        if overdue_30_plus:
            overdue_amount = sum(
                flt(inv["outstanding_amount"], self.precision) for inv in overdue_30_plus
            )
            recommendations.append(
                {
                    "priority": "High",
                    "category": "Collections",
                    "recommendation": f"Follow up on {len(overdue_30_plus)} invoices totaling OMR {overdue_amount:,.{self.precision}f} overdue 30+ days",
                    "recommendation_ar": f"متابعة {len(overdue_30_plus)} فاتورة بإجمالي {overdue_amount:,.{self.precision}f} ريال عماني متأخرة أكثر من ٣٠ يوم",
                    "action_required": "Send payment reminders and contact customers",
                    "affected_invoices": len(overdue_30_plus),
                    "amount": overdue_amount,
                }
            )

        # Analyze 90+ days overdue (critical)
        critical_overdue = aging_data.get("90+ Days", [])
        if critical_overdue:
            critical_amount = sum(
                flt(inv["outstanding_amount"], self.precision) for inv in critical_overdue
            )
            recommendations.append(
                {
                    "priority": "Critical",
                    "category": "Debt Collection",
                    "recommendation": f"Consider debt collection for {len(critical_overdue)} invoices totaling OMR {critical_amount:,.{self.precision}f} overdue 90+ days",
                    "recommendation_ar": f"اعتبار تحصيل الديون لـ {len(critical_overdue)} فاتورة بإجمالي {critical_amount:,.{self.precision}f} ريال عماني متأخرة أكثر من ٩٠ يوم",
                    "action_required": "Escalate to debt collection or legal action",
                    "affected_invoices": len(critical_overdue),
                    "amount": critical_amount,
                }
            )

        return recommendations

    def generate_dunning_sequence(
        self, customer: str, overdue_invoices: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generate automated dunning sequence for a customer

        Args:
            customer: Customer ID
            overdue_invoices: List of specific invoice IDs (optional)

        Returns:
            Dict containing dunning sequence data
        """

        try:
            # Get customer information
            customer_info = frappe.get_doc("Customer", customer)

            # Get overdue invoices for customer
            if not overdue_invoices:
                overdue_invoices = self._get_customer_overdue_invoices(customer)

            # Determine dunning level based on oldest overdue
            dunning_level = self._determine_dunning_level(overdue_invoices)

            # Generate appropriate communication
            communication_plan = self._create_communication_plan(
                customer_info, overdue_invoices, dunning_level
            )

            return {
                "customer": customer,
                "customer_name": customer_info.customer_name,
                "customer_name_ar": getattr(customer_info, "customer_name_ar", ""),
                "dunning_level": dunning_level,
                "overdue_invoices": overdue_invoices,
                "communication_plan": communication_plan,
                "generated_on": today(),
                "next_action_date": self._calculate_next_action_date(dunning_level),
            }

        except Exception as e:
            frappe.log_error(f"Dunning sequence generation failed: {e}")
            raise frappe.ValidationError(
                _("Failed to generate dunning sequence: {0}").format(str(e))
            )

    def _get_customer_overdue_invoices(self, customer: str) -> List[Dict]:
        """Get overdue invoices for a specific customer"""

        query = """
            SELECT 
                name as invoice_number,
                posting_date,
                due_date,
                base_grand_total as invoice_amount,
                outstanding_amount,
                DATEDIFF(CURDATE(), due_date) as days_overdue,
                custom_payment_reminder_count,
                custom_last_reminder_date
            FROM `tabSales Invoice`
            WHERE customer = %s
            AND docstatus = 1
            AND outstanding_amount > 0
            AND due_date < CURDATE()
            ORDER BY due_date
        """

        return frappe.db.sql(query, [customer], as_dict=True)

    def _determine_dunning_level(self, overdue_invoices: List[Dict]) -> str:
        """Determine appropriate dunning level based on overdue period"""

        if not overdue_invoices:
            return "No Action"

        max_overdue_days = max(inv.get("days_overdue", 0) for inv in overdue_invoices)

        if max_overdue_days >= 90:
            return "Final Notice"
        elif max_overdue_days >= 60:
            return "Second Reminder"
        elif max_overdue_days >= 30:
            return "First Reminder"
        elif max_overdue_days >= 7:
            return "Gentle Reminder"
        else:
            return "No Action"

    def _create_communication_plan(
        self, customer: Document, overdue_invoices: List[Dict], dunning_level: str
    ) -> Dict[str, Any]:
        """Create communication plan based on customer preferences and dunning level"""

        total_overdue = sum(
            flt(inv["outstanding_amount"], self.precision) for inv in overdue_invoices
        )
        preferred_language = getattr(customer, "custom_preferred_communication_language", "en")

        # Determine communication method based on dunning level
        communication_methods = {
            "Gentle Reminder": ["SMS", "WhatsApp"],
            "First Reminder": ["SMS", "WhatsApp", "Email"],
            "Second Reminder": ["Phone", "Email", "WhatsApp"],
            "Final Notice": ["Phone", "Email", "Registered Mail"],
        }

        # Generate message templates
        templates = self._get_dunning_templates(dunning_level, preferred_language)

        return {
            "dunning_level": dunning_level,
            "preferred_methods": communication_methods.get(dunning_level, ["Email"]),
            "total_overdue_amount": total_overdue,
            "invoice_count": len(overdue_invoices),
            "templates": templates,
            "customer_opt_in": getattr(customer, "custom_communication_opt_in", 0),
            "whatsapp_number": getattr(customer, "custom_whatsapp_number", ""),
            "preferred_language": preferred_language,
        }

    def _get_dunning_templates(self, dunning_level: str, language: str) -> Dict[str, str]:
        """Get dunning message templates"""

        templates = {
            "en": {
                "Gentle Reminder": {
                    "subject": "Payment Reminder - Universal Workshop",
                    "message": "Dear {customer_name},\n\nThis is a gentle reminder that payment for invoice(s) {invoice_numbers} totaling OMR {amount} is now overdue.\n\nWe would appreciate your prompt payment.\n\nThank you for your business.",
                },
                "First Reminder": {
                    "subject": "First Payment Reminder - Action Required",
                    "message": "Dear {customer_name},\n\nWe have not yet received payment for invoice(s) {invoice_numbers} totaling OMR {amount}, which is now {days_overdue} days overdue.\n\nPlease settle this amount immediately to avoid further action.\n\nContact us if you have any questions.",
                },
                "Second Reminder": {
                    "subject": "Second Payment Reminder - Urgent",
                    "message": "Dear {customer_name},\n\nDespite our previous reminder, payment for invoice(s) {invoice_numbers} totaling OMR {amount} remains outstanding for {days_overdue} days.\n\nImmediate payment is required to avoid suspension of services.\n\nPlease contact us urgently to resolve this matter.",
                },
                "Final Notice": {
                    "subject": "Final Notice - Legal Action Pending",
                    "message": "Dear {customer_name},\n\nThis is a final notice regarding overdue payment of OMR {amount} for invoice(s) {invoice_numbers}, now {days_overdue} days overdue.\n\nIf payment is not received within 7 days, we will proceed with debt collection and legal action.\n\nContact us immediately to avoid further consequences.",
                },
            },
            "ar": {
                "Gentle Reminder": {
                    "subject": "تذكير بالدفع - ورشة يونيفرسال",
                    "message": "عزيزي {customer_name}،\n\nهذا تذكير لطيف بأن دفع الفاتورة/الفواتير {invoice_numbers} بإجمالي {amount} ريال عماني أصبح متأخراً.\n\nنقدر دفعكم السريع.\n\nشكراً لتعاملكم معنا.",
                },
                "First Reminder": {
                    "subject": "التذكير الأول بالدفع - مطلوب اتخاذ إجراء",
                    "message": "عزيزي {customer_name}،\n\nلم نتلق بعد دفع الفاتورة/الفواتير {invoice_numbers} بإجمالي {amount} ريال عماني، والتي تأخرت {days_overdue} يوم.\n\nيرجى تسوية هذا المبلغ فوراً لتجنب اتخاذ إجراءات أخرى.\n\nاتصل بنا إذا كان لديك أي استفسارات.",
                },
                "Second Reminder": {
                    "subject": "التذكير الثاني بالدفع - عاجل",
                    "message": "عزيزي {customer_name}،\n\nرغم تذكيرنا السابق، لا يزال دفع الفاتورة/الفواتير {invoice_numbers} بإجمالي {amount} ريال عماني متأخراً لـ {days_overdue} يوم.\n\nالدفع الفوري مطلوب لتجنب تعليق الخدمات.\n\nيرجى الاتصال بنا بشكل عاجل لحل هذه المسألة.",
                },
                "Final Notice": {
                    "subject": "إشعار نهائي - إجراء قانوني معلق",
                    "message": "عزيزي {customer_name}،\n\nهذا إشعار نهائي بخصوص الدفع المتأخر بمبلغ {amount} ريال عماني للفاتورة/الفواتير {invoice_numbers}، المتأخرة الآن {days_overdue} يوم.\n\nإذا لم يتم استلام الدفع خلال ٧ أيام، سنتابع تحصيل الديون والإجراء القانوني.\n\nاتصل بنا فوراً لتجنب عواقب أخرى.",
                },
            },
        }

        return templates.get(language, templates["en"]).get(dunning_level, {})

    def _calculate_next_action_date(self, dunning_level: str) -> str:
        """Calculate next action date based on dunning level"""

        days_map = {
            "Gentle Reminder": 7,
            "First Reminder": 7,
            "Second Reminder": 5,
            "Final Notice": 3,
        }

        days_to_add = days_map.get(dunning_level, 7)
        return add_days(today(), days_to_add)


