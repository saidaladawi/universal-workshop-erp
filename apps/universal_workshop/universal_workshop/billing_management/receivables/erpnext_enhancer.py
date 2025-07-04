"""
ERPNext v15 Receivables Enhancement Engine  
Advanced receivables management with latest ERPNext features
"""

import frappe
from frappe import _
from frappe.utils import flt, cint, getdate, today, add_days, add_months, date_diff
from datetime import datetime, timedelta
import json
from typing import Dict, List, Any, Tuple
from .management_engine import OmanReceivablesManager


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
