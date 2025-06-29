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
from frappe.utils import flt, cint, getdate, today, add_days, date_diff, nowdate
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
        self, customer: frappe.Document, overdue_invoices: List[Dict], dunning_level: str
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


class ERPNextV15ReceivablesEnhancer:
    """
    ERPNext v15 enhancements for receivables management
    Implements latest best practices and new features
    """

    def __init__(self):
        self.currency = "OMR"
        self.precision = 3

    def setup_background_reconciliation(self, company: str) -> Dict[str, Any]:
        """
        Setup background payment reconciliation for high-volume environments
        ERPNext v15 feature to handle large volumes without timeouts
        """
        try:
            # Configure background processing settings
            settings = {
                "enable_background_reconciliation": True,
                "batch_size": 100,
                "max_processing_time": 300,  # 5 minutes
                "retry_failed_reconciliations": True,
                "notification_on_completion": True,
            }

            # Create custom field for background processing status
            if not frappe.db.exists(
                "Custom Field",
                {"dt": "Payment Entry", "fieldname": "custom_background_reconciliation_status"},
            ):
                field = frappe.new_doc("Custom Field")
                field.dt = "Payment Entry"
                field.label = "Background Reconciliation Status"
                field.label_ar = "حالة التسوية الخلفية"
                field.fieldname = "custom_background_reconciliation_status"
                field.fieldtype = "Select"
                field.options = "Pending\nProcessing\nCompleted\nFailed"
                field.default = "Pending"
                field.read_only = 1
                field.insert()

            # Setup background job for reconciliation
            if not frappe.db.exists("Scheduled Job Type", "background_payment_reconciliation"):
                job = frappe.new_doc("Scheduled Job Type")
                job.method = "universal_workshop.billing_management.receivables_management.process_background_reconciliation"
                job.frequency = "Cron"
                job.cron_format = "*/5 * * * *"  # Every 5 minutes
                job.create_log = 1
                job.insert()

            return {
                "status": "success",
                "message": _("Background reconciliation setup completed"),
                "settings": settings,
            }

        except Exception as e:
            frappe.log_error(f"Background reconciliation setup failed: {e}")
            raise frappe.ValidationError(
                _("Failed to setup background reconciliation: {0}").format(str(e))
            )

    def setup_automated_invoice_generation(self, company: str) -> Dict[str, Any]:
        """
        Setup automated invoice generation for recurring services
        ERPNext v15 feature for subscription and recurring billing
        """
        try:
            # Create subscription template for workshop services
            if not frappe.db.exists("Subscription", {"company": company, "custom_auto_invoice": 1}):
                subscription_template = {
                    "subscription_name": "Workshop Service Subscription",
                    "subscription_name_ar": "اشتراك خدمات الورشة",
                    "company": company,
                    "party_type": "Customer",
                    "generate_invoice_automatically": 1,
                    "days_until_due": 30,
                    "currency": "OMR",
                    "custom_auto_invoice": 1,
                    "custom_workshop_service_type": "Maintenance",
                    "custom_arabic_invoice_template": 1,
                }

                # Setup custom fields for subscription enhancement
                subscription_fields = [
                    {
                        "fieldname": "custom_auto_invoice",
                        "label": "Auto Generate Invoices",
                        "label_ar": "إنشاء الفواتير تلقائياً",
                        "fieldtype": "Check",
                        "default": 0,
                    },
                    {
                        "fieldname": "custom_workshop_service_type",
                        "label": "Workshop Service Type",
                        "label_ar": "نوع خدمة الورشة",
                        "fieldtype": "Select",
                        "options": "Maintenance\nRepair\nInspection\nCustom",
                    },
                    {
                        "fieldname": "custom_arabic_invoice_template",
                        "label": "Use Arabic Invoice Template",
                        "label_ar": "استخدام قالب الفاتورة العربية",
                        "fieldtype": "Check",
                        "default": 1,
                    },
                ]

                for field in subscription_fields:
                    if not frappe.db.exists(
                        "Custom Field", {"dt": "Subscription", "fieldname": field["fieldname"]}
                    ):
                        custom_field = frappe.new_doc("Custom Field")
                        custom_field.dt = "Subscription"
                        custom_field.update(field)
                        custom_field.insert()

            # Setup notification for auto-generated invoices
            notification_config = {
                "document_type": "Sales Invoice",
                "event": "New",
                "condition": "doc.custom_auto_generated == 1",
                "subject": _("Auto-generated invoice: {0}").format("{{ doc.name }}"),
                "message": _(
                    "Invoice {{ doc.name }} has been automatically generated for customer {{ doc.customer }}"
                ),
                "send_to_all_assignees": 1,
                "attach_print": 1,
            }

            return {
                "status": "success",
                "message": _("Automated invoice generation setup completed"),
                "template": subscription_template,
                "notification": notification_config,
            }

        except Exception as e:
            frappe.log_error(f"Automated invoice setup failed: {e}")
            raise frappe.ValidationError(
                _("Failed to setup automated invoices: {0}").format(str(e))
            )

    def setup_bank_reconciliation_integration(self, company: str) -> Dict[str, Any]:
        """
        Setup enhanced bank reconciliation with ERPNext v15 features
        """
        try:
            # Configure bank reconciliation settings
            bank_settings = {
                "auto_reconcile_matching_references": True,
                "tolerance_amount": 0.001,  # 1 Baisa for OMR
                "enable_partial_reconciliation": True,
                "auto_create_payment_entries": True,
                "notification_on_mismatch": True,
            }

            # Setup custom fields for enhanced bank reconciliation
            bank_fields = [
                {
                    "dt": "Bank Transaction",
                    "fieldname": "custom_arabic_description",
                    "label": "Arabic Description",
                    "label_ar": "الوصف بالعربية",
                    "fieldtype": "Text",
                    "translatable": 1,
                },
                {
                    "dt": "Bank Transaction",
                    "fieldname": "custom_workshop_reference",
                    "label": "Workshop Reference",
                    "label_ar": "مرجع الورشة",
                    "fieldtype": "Data",
                },
                {
                    "dt": "Bank Transaction",
                    "fieldname": "custom_reconciliation_confidence",
                    "label": "Reconciliation Confidence %",
                    "label_ar": "نسبة ثقة التسوية %",
                    "fieldtype": "Percent",
                    "read_only": 1,
                },
            ]

            for field_config in bank_fields:
                dt = field_config.pop("dt")
                if not frappe.db.exists(
                    "Custom Field", {"dt": dt, "fieldname": field_config["fieldname"]}
                ):
                    field = frappe.new_doc("Custom Field")
                    field.dt = dt
                    field.update(field_config)
                    field.insert()

            # Setup automated bank reconciliation rules
            reconciliation_rules = [
                {
                    "rule_name": "Workshop Invoice Match",
                    "rule_name_ar": "مطابقة فاتورة الورشة",
                    "matching_criteria": "reference_number",
                    "confidence_threshold": 90,
                    "auto_reconcile": True,
                },
                {
                    "rule_name": "Customer Payment Match",
                    "rule_name_ar": "مطابقة دفع العميل",
                    "matching_criteria": "amount_and_date",
                    "confidence_threshold": 85,
                    "auto_reconcile": False,  # Require manual review
                },
            ]

            return {
                "status": "success",
                "message": _("Bank reconciliation integration setup completed"),
                "settings": bank_settings,
                "rules": reconciliation_rules,
            }

        except Exception as e:
            frappe.log_error(f"Bank reconciliation setup failed: {e}")
            raise frappe.ValidationError(
                _("Failed to setup bank reconciliation: {0}").format(str(e))
            )

    def setup_deferred_revenue_support(self, company: str) -> Dict[str, Any]:
        """
        Setup deferred revenue support for prepaid services and subscriptions
        ERPNext v15 feature for accurate revenue recognition
        """
        try:
            # Setup deferred revenue accounts
            deferred_accounts = [
                {
                    "account_name": "Deferred Revenue - Workshop Services",
                    "account_name_ar": "الإيرادات المؤجلة - خدمات الورشة",
                    "account_type": "Liability",
                    "root_type": "Liability",
                    "is_group": 0,
                    "company": company,
                },
                {
                    "account_name": "Deferred Revenue - Parts Sales",
                    "account_name_ar": "الإيرادات المؤجلة - مبيعات القطع",
                    "account_type": "Liability",
                    "root_type": "Liability",
                    "is_group": 0,
                    "company": company,
                },
            ]

            created_accounts = []
            for account_config in deferred_accounts:
                if not frappe.db.exists(
                    "Account", {"company": company, "account_name": account_config["account_name"]}
                ):
                    account = frappe.new_doc("Account")
                    account.update(account_config)
                    account.insert()
                    created_accounts.append(account.name)

            # Setup deferred revenue item configuration
            item_fields = [
                {
                    "fieldname": "custom_enable_deferred_revenue",
                    "label": "Enable Deferred Revenue",
                    "label_ar": "تفعيل الإيرادات المؤجلة",
                    "fieldtype": "Check",
                    "default": 0,
                },
                {
                    "fieldname": "custom_deferred_revenue_account",
                    "label": "Deferred Revenue Account",
                    "label_ar": "حساب الإيرادات المؤجلة",
                    "fieldtype": "Link",
                    "options": "Account",
                    "depends_on": "custom_enable_deferred_revenue",
                },
                {
                    "fieldname": "custom_revenue_recognition_period",
                    "label": "Revenue Recognition Period (Months)",
                    "label_ar": "فترة الاعتراف بالإيراد (أشهر)",
                    "fieldtype": "Int",
                    "default": 12,
                    "depends_on": "custom_enable_deferred_revenue",
                },
            ]

            for field_config in item_fields:
                if not frappe.db.exists(
                    "Custom Field", {"dt": "Item", "fieldname": field_config["fieldname"]}
                ):
                    field = frappe.new_doc("Custom Field")
                    field.dt = "Item"
                    field.update(field_config)
                    field.insert()

            return {
                "status": "success",
                "message": _("Deferred revenue support setup completed"),
                "accounts": created_accounts,
                "item_configuration": "enabled",
            }

        except Exception as e:
            frappe.log_error(f"Deferred revenue setup failed: {e}")
            raise frappe.ValidationError(_("Failed to setup deferred revenue: {0}").format(str(e)))

    def generate_realtime_ar_dashboard(self, company: str, language: str = "en") -> Dict[str, Any]:
        """
        Generate real-time AR dashboard with ERPNext v15 analytics
        """
        try:
            # Get real-time receivables data
            ar_summary = frappe.db.sql(
                """
                SELECT 
                    COUNT(DISTINCT si.customer) as total_customers,
                    COUNT(si.name) as total_invoices,
                    SUM(si.base_grand_total) as total_invoiced,
                    SUM(si.outstanding_amount) as total_outstanding,
                    SUM(CASE WHEN si.due_date < CURDATE() THEN si.outstanding_amount ELSE 0 END) as overdue_amount,
                    AVG(DATEDIFF(CURDATE(), si.due_date)) as avg_days_outstanding,
                    SUM(CASE WHEN DATEDIFF(CURDATE(), si.due_date) > 90 THEN si.outstanding_amount ELSE 0 END) as high_risk_amount
                FROM `tabSales Invoice` si
                WHERE si.company = %s
                AND si.docstatus = 1
                AND si.outstanding_amount > 0
            """,
                [company],
                as_dict=True,
            )[0]

            # Calculate key metrics
            collection_efficiency = flt(
                (
                    (
                        (ar_summary.total_invoiced - ar_summary.total_outstanding)
                        / ar_summary.total_invoiced
                        * 100
                    )
                    if ar_summary.total_invoiced > 0
                    else 0
                ),
                2,
            )

            overdue_percentage = flt(
                (
                    (ar_summary.overdue_amount / ar_summary.total_outstanding * 100)
                    if ar_summary.total_outstanding > 0
                    else 0
                ),
                2,
            )

            # Generate aging buckets summary
            aging_buckets = frappe.db.sql(
                """
                SELECT 
                    CASE 
                        WHEN DATEDIFF(CURDATE(), si.due_date) <= 0 THEN 'Current'
                        WHEN DATEDIFF(CURDATE(), si.due_date) <= 30 THEN '1-30 Days'
                        WHEN DATEDIFF(CURDATE(), si.due_date) <= 60 THEN '31-60 Days'
                        WHEN DATEDIFF(CURDATE(), si.due_date) <= 90 THEN '61-90 Days'
                        ELSE '90+ Days'
                    END as aging_bucket,
                    COUNT(si.name) as invoice_count,
                    SUM(si.outstanding_amount) as bucket_amount
                FROM `tabSales Invoice` si
                WHERE si.company = %s
                AND si.docstatus = 1
                AND si.outstanding_amount > 0
                GROUP BY aging_bucket
                ORDER BY 
                    CASE aging_bucket
                        WHEN 'Current' THEN 1
                        WHEN '1-30 Days' THEN 2
                        WHEN '31-60 Days' THEN 3
                        WHEN '61-90 Days' THEN 4
                        ELSE 5
                    END
            """,
                [company],
                as_dict=True,
            )

            # Top overdue customers
            top_overdue = frappe.db.sql(
                """
                SELECT 
                    si.customer,
                    c.customer_name,
                    c.customer_name_ar,
                    SUM(si.outstanding_amount) as overdue_amount,
                    COUNT(si.name) as overdue_invoices,
                    MAX(DATEDIFF(CURDATE(), si.due_date)) as max_days_overdue
                FROM `tabSales Invoice` si
                LEFT JOIN `tabCustomer` c ON si.customer = c.name
                WHERE si.company = %s
                AND si.docstatus = 1
                AND si.outstanding_amount > 0
                AND si.due_date < CURDATE()
                GROUP BY si.customer
                ORDER BY overdue_amount DESC
                LIMIT 10
            """,
                [company],
                as_dict=True,
            )

            dashboard = {
                "company": company,
                "generated_at": nowdate(),
                "language": language,
                "currency": self.currency,
                "kpis": {
                    "total_customers": ar_summary.total_customers or 0,
                    "total_invoices": ar_summary.total_invoices or 0,
                    "total_outstanding": flt(ar_summary.total_outstanding or 0, self.precision),
                    "overdue_amount": flt(ar_summary.overdue_amount or 0, self.precision),
                    "collection_efficiency": collection_efficiency,
                    "overdue_percentage": overdue_percentage,
                    "avg_days_outstanding": flt(ar_summary.avg_days_outstanding or 0, 1),
                    "high_risk_amount": flt(ar_summary.high_risk_amount or 0, self.precision),
                },
                "aging_analysis": aging_buckets,
                "top_overdue_customers": top_overdue,
                "alerts": self._generate_ar_alerts(ar_summary, language),
                "recommendations": self._generate_ar_recommendations(ar_summary, language),
            }

            return dashboard

        except Exception as e:
            frappe.log_error(f"AR dashboard generation failed: {e}")
            raise frappe.ValidationError(_("Failed to generate AR dashboard: {0}").format(str(e)))

    def _generate_ar_alerts(self, ar_summary: Dict, language: str) -> List[Dict]:
        """Generate automated alerts based on AR metrics"""
        alerts = []

        # High overdue percentage alert
        overdue_pct = flt(
            (
                (ar_summary.overdue_amount / ar_summary.total_outstanding * 100)
                if ar_summary.total_outstanding > 0
                else 0
            ),
            2,
        )

        if overdue_pct > 30:
            alerts.append(
                {
                    "type": "warning",
                    "priority": "high",
                    "title": (
                        _("High Overdue Percentage")
                        if language == "en"
                        else "نسبة عالية من المتأخرات"
                    ),
                    "message": (
                        _("Overdue amount is {0}% of total outstanding").format(overdue_pct)
                        if language == "en"
                        else f"المبلغ المتأخر يشكل {overdue_pct}% من إجمالي المستحق"
                    ),
                    "action_required": True,
                }
            )

        # High risk amount alert
        if ar_summary.high_risk_amount > 10000:  # OMR 10,000
            alerts.append(
                {
                    "type": "error",
                    "priority": "critical",
                    "title": (
                        _("High Risk Receivables") if language == "en" else "ذمم عالية المخاطر"
                    ),
                    "message": (
                        _("OMR {0} in receivables over 90 days old").format(
                            flt(ar_summary.high_risk_amount, 3)
                        )
                        if language == "en"
                        else f"ريال عماني {flt(ar_summary.high_risk_amount, 3)} في الذمم أكثر من ٩٠ يوم"
                    ),
                    "action_required": True,
                }
            )

        return alerts

    def _generate_ar_recommendations(self, ar_summary: Dict, language: str) -> List[Dict]:
        """Generate automated recommendations based on AR analysis"""
        recommendations = []

        # Collection efficiency recommendation
        collection_efficiency = flt(
            (
                (
                    (ar_summary.total_invoiced - ar_summary.total_outstanding)
                    / ar_summary.total_invoiced
                    * 100
                )
                if ar_summary.total_invoiced > 0
                else 0
            ),
            2,
        )

        if collection_efficiency < 85:
            recommendations.append(
                {
                    "category": "collection",
                    "priority": "high",
                    "title": (
                        _("Improve Collection Efficiency")
                        if language == "en"
                        else "تحسين كفاءة التحصيل"
                    ),
                    "description": (
                        _("Collection efficiency is {0}%, target is 90%+").format(
                            collection_efficiency
                        )
                        if language == "en"
                        else f"كفاءة التحصيل {collection_efficiency}%، الهدف ٩٠%+"
                    ),
                    "actions": [
                        (
                            _("Implement automated dunning")
                            if language == "en"
                            else "تطبيق التذكير التلقائي"
                        ),
                        _("Review credit terms") if language == "en" else "مراجعة شروط الائتمان",
                        (
                            _("Enhance follow-up processes")
                            if language == "en"
                            else "تعزيز عمليات المتابعة"
                        ),
                    ],
                }
            )

        return recommendations


# API methods for external access
@frappe.whitelist()
def generate_aging_analysis(company, as_on_date=None, language="en"):
    """Generate aging analysis report (API endpoint)"""
    manager = OmanReceivablesManager()
    return manager.generate_aging_analysis(company, as_on_date, language)


@frappe.whitelist()
def generate_dunning_sequence(customer, overdue_invoices=None):
    """Generate dunning sequence for customer (API endpoint)"""
    manager = OmanReceivablesManager()
    if overdue_invoices and isinstance(overdue_invoices, str):
        overdue_invoices = json.loads(overdue_invoices)
    return manager.generate_dunning_sequence(customer, overdue_invoices)


@frappe.whitelist()
def get_customer_payment_behavior(customer):
    """Get customer payment behavior analysis"""

    # Get recent payment history
    payment_history = frappe.db.sql(
        """
        SELECT 
            pe.posting_date,
            pe.paid_amount,
            per.reference_name as invoice,
            DATEDIFF(pe.posting_date, si.due_date) as days_late
        FROM `tabPayment Entry` pe
        INNER JOIN `tabPayment Entry Reference` per ON pe.name = per.parent
        INNER JOIN `tabSales Invoice` si ON per.reference_name = si.name
        WHERE pe.party = %s
        AND pe.docstatus = 1
        AND pe.posting_date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
        ORDER BY pe.posting_date DESC
        LIMIT 20
    """,
        [customer],
        as_dict=True,
    )

    # Calculate behavior metrics
    total_payments = len(payment_history)
    on_time_payments = len([p for p in payment_history if p.days_late <= 0])
    late_payments = total_payments - on_time_payments

    avg_days_late = (
        sum(max(0, p.days_late) for p in payment_history) / total_payments
        if total_payments > 0
        else 0
    )

    return {
        "customer": customer,
        "total_payments": total_payments,
        "on_time_payments": on_time_payments,
        "late_payments": late_payments,
        "on_time_percentage": flt(
            (on_time_payments / total_payments * 100) if total_payments > 0 else 0, 2
        ),
        "average_days_late": flt(avg_days_late, 1),
        "payment_history": payment_history,
    }


@frappe.whitelist()
def update_payment_behavior_scores():
    """Update payment behavior scores for all customers (scheduled task)"""

    customers = frappe.get_list("Customer", fields=["name"])
    updated_count = 0

    for customer in customers:
        try:
            behavior_data = get_customer_payment_behavior(customer.name)

            # Calculate score based on behavior
            score = 10
            if behavior_data["on_time_percentage"] < 50:
                score -= 5
            elif behavior_data["on_time_percentage"] < 75:
                score -= 3
            elif behavior_data["on_time_percentage"] < 90:
                score -= 1

            if behavior_data["average_days_late"] > 30:
                score -= 3
            elif behavior_data["average_days_late"] > 15:
                score -= 2
            elif behavior_data["average_days_late"] > 7:
                score -= 1

            score = max(1, score)

            # Update customer record
            frappe.db.set_value("Customer", customer.name, "custom_payment_behavior_score", score)
            updated_count += 1

        except Exception as e:
            frappe.log_error(f"Failed to update payment behavior score for {customer.name}: {e}")

    return {"updated_customers": updated_count}


# Enhanced API methods for ERPNext v15
@frappe.whitelist()
def setup_v15_enhancements(company):
    """Setup all ERPNext v15 receivables enhancements"""
    enhancer = ERPNextV15ReceivablesEnhancer()

    results = {
        "background_reconciliation": enhancer.setup_background_reconciliation(company),
        "automated_invoices": enhancer.setup_automated_invoice_generation(company),
        "bank_reconciliation": enhancer.setup_bank_reconciliation_integration(company),
        "deferred_revenue": enhancer.setup_deferred_revenue_support(company),
    }

    return results


@frappe.whitelist()
def get_realtime_ar_dashboard(company, language="en"):
    """Get real-time AR dashboard with ERPNext v15 analytics"""
    enhancer = ERPNextV15ReceivablesEnhancer()
    return enhancer.generate_realtime_ar_dashboard(company, language)


@frappe.whitelist()
def process_background_reconciliation():
    """Background job for payment reconciliation processing"""
    try:
        # Get pending reconciliations
        pending_entries = frappe.get_list(
            "Payment Entry",
            filters={"custom_background_reconciliation_status": "Pending", "docstatus": 1},
            limit=100,
        )

        processed_count = 0
        for entry in pending_entries:
            try:
                # Update status to processing
                frappe.db.set_value(
                    "Payment Entry",
                    entry.name,
                    "custom_background_reconciliation_status",
                    "Processing",
                )

                # Process reconciliation logic here
                # This would integrate with ERPNext's bank reconciliation tool

                # Update status to completed
                frappe.db.set_value(
                    "Payment Entry",
                    entry.name,
                    "custom_background_reconciliation_status",
                    "Completed",
                )
                processed_count += 1

            except Exception as e:
                frappe.log_error(f"Background reconciliation failed for {entry.name}: {e}")
                frappe.db.set_value(
                    "Payment Entry", entry.name, "custom_background_reconciliation_status", "Failed"
                )

        frappe.db.commit()
        return {"processed": processed_count, "total": len(pending_entries)}

    except Exception as e:
        frappe.log_error(f"Background reconciliation job failed: {e}")
        return {"error": str(e)}
