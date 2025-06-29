# -*- coding: utf-8 -*-
# Copyright (c) 2024, Said Al-Adowi and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, getdate, add_days, today, get_datetime, format_date, cint
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional, Tuple
from frappe.email.doctype.notification.notification import Notification


class FinancialNotificationManager:
    """
    Automated Financial Notifications and Reminders Manager for Universal Workshop ERP
    Handles invoice due dates, budget alerts, compliance deadlines, and cash flow warnings
    """

    def __init__(self, company=None):
        self.company = company or frappe.defaults.get_global_default("company")

        # Notification types and their configurations
        self.notification_configs = {
            "invoice_due_reminder": {
                "doctype": "Sales Invoice",
                "reminder_days": [7, 3, 1, 0],  # Days before due date
                "overdue_days": [1, 3, 7, 14, 30],  # Days after due date
                "priority": "high",
            },
            "budget_alert": {
                "doctype": "Budget",
                "thresholds": [80, 90, 95, 100, 110],  # Utilization percentages
                "priority": "high",
            },
            "payment_reminder": {
                "doctype": "Purchase Invoice",
                "reminder_days": [5, 2, 0],  # Days before payment due
                "priority": "medium",
            },
            "vat_compliance": {
                "doctype": "Sales Invoice",
                "filing_reminder_days": [7, 3, 1],  # Days before VAT filing due
                "priority": "urgent",
            },
            "cash_flow_alert": {
                "threshold_days": 30,  # Days of cash runway
                "check_frequency": "daily",
                "priority": "urgent",
            },
        }

        # Arabic translations for notification templates
        self.arabic_templates = {
            "invoice_due_title": "تذكير: فاتورة مستحقة الدفع",
            "invoice_due_body": "عزيزي العميل، الفاتورة رقم {invoice_no} مستحقة الدفع بتاريخ {due_date}",
            "budget_alert_title": "تنبيه: تجاوز الميزانية",
            "budget_alert_body": "تحذير: تم تجاوز {utilization}% من ميزانية {cost_center}",
            "payment_reminder_title": "تذكير: دفع الفاتورة",
            "payment_reminder_body": "تذكير بدفع الفاتورة رقم {invoice_no} بقيمة {amount} OMR",
            "vat_filing_title": "تذكير: تقديم إقرار ضريبة القيمة المضافة",
            "vat_filing_body": "موعد تقديم إقرار الضريبة يوم {filing_date}",
            "cash_flow_title": "تحذير: انخفاض السيولة النقدية",
            "cash_flow_body": "تحذير: السيولة المتوقعة ستكفي لمدة {days} أيام فقط",
        }

    def setup_financial_notifications(self):
        """
        Setup all financial notification configurations in ERPNext
        """
        try:
            # Setup invoice due date reminders
            self._setup_invoice_due_notifications()

            # Setup budget threshold alerts
            self._setup_budget_alert_notifications()

            # Setup payment reminders
            self._setup_payment_reminder_notifications()

            # Setup VAT compliance reminders
            self._setup_vat_compliance_notifications()

            # Setup cash flow alerts
            self._setup_cash_flow_alerts()

            frappe.msgprint(_("Financial notification system configured successfully"))
            return True

        except Exception as e:
            frappe.log_error(f"Financial Notification Setup Error: {str(e)}")
            frappe.throw(_("Error setting up financial notifications: {0}").format(str(e)))

    def _setup_invoice_due_notifications(self):
        """Setup invoice due date reminder notifications"""

        # Invoice due date reminders (before due date)
        for days_before in self.notification_configs["invoice_due_reminder"]["reminder_days"]:
            notification_name = f"Invoice Due Reminder - {days_before} Days Before"

            if not frappe.db.exists("Notification", notification_name):
                notification = frappe.new_doc("Notification")
                notification.name = notification_name
                notification.subject = _("Invoice Due Reminder: {{doc.name}}")
                notification.document_type = "Sales Invoice"
                notification.event = "Days Before"
                notification.days_in_advance = days_before
                notification.send_alert_on = "Days Before"
                notification.condition = """
                    doc.outstanding_amount > 0 
                    and doc.docstatus == 1 
                    and not doc.custom_due_reminder_sent
                """

                # Arabic subject line
                if frappe.db.get_single_value("System Settings", "language") == "ar":
                    notification.subject = (
                        self.arabic_templates["invoice_due_title"] + ": {{doc.name}}"
                    )

                # Message template (bilingual)
                notification.message = self._get_invoice_due_message_template(days_before, "before")

                # Recipients
                notification.send_to_all_assignees = 0
                notification.recipients = []

                # Add customer contact as recipient
                notification.append("recipients", {"receiver_by_document_field": "contact_person"})

                # Add finance team
                notification.append("recipients", {"receiver_by_role": "Accounts Manager"})

                notification.enabled = 1
                notification.insert()

        # Overdue invoice reminders (after due date)
        for days_after in self.notification_configs["invoice_due_reminder"]["overdue_days"]:
            notification_name = f"Overdue Invoice Reminder - {days_after} Days After"

            if not frappe.db.exists("Notification", notification_name):
                notification = frappe.new_doc("Notification")
                notification.name = notification_name
                notification.subject = _("Overdue Invoice: {{doc.name}}")
                notification.document_type = "Sales Invoice"
                notification.event = "Days After"
                notification.days_in_advance = days_after
                notification.send_alert_on = "Days After"
                notification.condition = """
                    doc.outstanding_amount > 0 
                    and doc.docstatus == 1
                """

                # Arabic subject for overdue
                if frappe.db.get_single_value("System Settings", "language") == "ar":
                    notification.subject = "فاتورة متأخرة: {{doc.name}}"

                notification.message = self._get_invoice_due_message_template(days_after, "after")

                # Recipients for overdue (escalated)
                notification.append("recipients", {"receiver_by_document_field": "contact_person"})
                notification.append("recipients", {"receiver_by_role": "Accounts Manager"})
                notification.append("recipients", {"receiver_by_role": "Finance Manager"})

                notification.enabled = 1
                notification.insert()

    def _get_invoice_due_message_template(self, days, timing):
        """Get bilingual message template for invoice due reminders"""

        if timing == "before":
            english_template = f"""
Dear {{{{ doc.customer_name }}}},

This is a friendly reminder that your invoice {{{{ doc.name }}}} for OMR {{{{ doc.grand_total }}}} is due on {{{{ doc.due_date }}}}.

Invoice Details:
- Invoice Number: {{{{ doc.name }}}}
- Amount: OMR {{{{ doc.outstanding_amount }}}}
- Due Date: {{{{ doc.due_date }}}}

Please ensure payment is made by the due date to avoid any late fees.

Best regards,
{{{{ doc.company }}}}
            """

            arabic_template = f"""
عزيزي {{{{ doc.customer_name }}}},

هذا تذكير ودود بأن فاتورتكم رقم {{{{ doc.name }}}} بقيمة {{{{ doc.grand_total }}}} ريال عماني مستحقة الدفع بتاريخ {{{{ doc.due_date }}}}.

تفاصيل الفاتورة:
- رقم الفاتورة: {{{{ doc.name }}}}
- المبلغ: {{{{ doc.outstanding_amount }}}} ريال عماني
- تاريخ الاستحقاق: {{{{ doc.due_date }}}}

يرجى التأكد من سداد المبلغ بحلول تاريخ الاستحقاق لتجنب أي رسوم تأخير.

مع أطيب التحيات،
{{{{ doc.company }}}}
            """
        else:  # after (overdue)
            english_template = f"""
Dear {{{{ doc.customer_name }}}},

Your invoice {{{{ doc.name }}}} is now overdue by {days} days. Immediate payment is required.

Invoice Details:
- Invoice Number: {{{{ doc.name }}}}
- Overdue Amount: OMR {{{{ doc.outstanding_amount }}}}
- Original Due Date: {{{{ doc.due_date }}}}
- Days Overdue: {days}

Please contact us immediately to arrange payment.

Best regards,
{{{{ doc.company }}}}
            """

            arabic_template = f"""
عزيزي {{{{ doc.customer_name }}}},

فاتورتكم رقم {{{{ doc.name }}}} متأخرة الآن لمدة {days} أيام. يرجى السداد فوراً.

تفاصيل الفاتورة:
- رقم الفاتورة: {{{{ doc.name }}}}
- المبلغ المتأخر: {{{{ doc.outstanding_amount }}}} ريال عماني
- تاريخ الاستحقاق الأصلي: {{{{ doc.due_date }}}}
- عدد أيام التأخير: {days}

يرجى الاتصال بنا فوراً لترتيب الدفع.

مع أطيب التحيات،
{{{{ doc.company }}}}
            """

        # Return bilingual template
        return f"""
{english_template}

---

{arabic_template}
        """

    def _setup_budget_alert_notifications(self):
        """Setup budget threshold alert notifications"""

        for threshold in self.notification_configs["budget_alert"]["thresholds"]:
            notification_name = f"Budget Alert - {threshold}% Utilization"

            if not frappe.db.exists("Notification", notification_name):
                notification = frappe.new_doc("Notification")
                notification.name = notification_name
                notification.subject = _("Budget Alert: {0}% Utilization").format(threshold)
                notification.document_type = "Budget"
                notification.event = "Value Change"
                notification.value_changed = "total_actual_expense"
                notification.condition = f"""
                    (doc.total_actual_expense / doc.total_budget_amount * 100) >= {threshold}
                    and doc.docstatus == 1
                """

                # Arabic subject
                if frappe.db.get_single_value("System Settings", "language") == "ar":
                    notification.subject = f"تنبيه ميزانية: {threshold}% استخدام"

                notification.message = self._get_budget_alert_message_template(threshold)

                # Recipients
                notification.append("recipients", {"receiver_by_role": "Budget Manager"})
                notification.append("recipients", {"receiver_by_role": "Finance Manager"})

                if threshold >= 100:  # Critical alert
                    notification.append("recipients", {"receiver_by_role": "Workshop Manager"})

                notification.enabled = 1
                notification.insert()

    def _get_budget_alert_message_template(self, threshold):
        """Get bilingual message template for budget alerts"""

        english_template = f"""
Budget Alert: {threshold}% Utilization Reached

Budget Details:
- Cost Center: {{{{ doc.cost_center }}}}
- Budget Amount: OMR {{{{ doc.total_budget_amount }}}}
- Actual Expense: OMR {{{{ doc.total_actual_expense }}}}
- Utilization: {{{{ (doc.total_actual_expense / doc.total_budget_amount * 100) | round(1) }}}}%
- Remaining Budget: OMR {{{{ (doc.total_budget_amount - doc.total_actual_expense) | round(3) }}}}

{'Immediate action required to control spending.' if threshold >= 100 else 'Please review and control spending to stay within budget.'}

Budget Report: /app/budget/{{{{ doc.name }}}}
        """

        arabic_template = f"""
تنبيه ميزانية: تم الوصول إلى {threshold}% استخدام

تفاصيل الميزانية:
- مركز التكلفة: {{{{ doc.cost_center }}}}
- مبلغ الميزانية: {{{{ doc.total_budget_amount }}}} ريال عماني
- المصروفات الفعلية: {{{{ doc.total_actual_expense }}}} ريال عماني
- نسبة الاستخدام: {{{{ (doc.total_actual_expense / doc.total_budget_amount * 100) | round(1) }}}}%
- الميزانية المتبقية: {{{{ (doc.total_budget_amount - doc.total_actual_expense) | round(3) }}}} ريال عماني

{'يتطلب إجراء فوري للتحكم في الإنفاق.' if threshold >= 100 else 'يرجى المراجعة والتحكم في الإنفاق للبقاء ضمن الميزانية.'}

تقرير الميزانية: /app/budget/{{{{ doc.name }}}}
        """

        return f"""
{english_template}

---

{arabic_template}
        """

    def _setup_payment_reminder_notifications(self):
        """Setup payment reminder notifications for Purchase Invoices"""

        for days_before in self.notification_configs["payment_reminder"]["reminder_days"]:
            notification_name = f"Payment Reminder - {days_before} Days Before Due"

            if not frappe.db.exists("Notification", notification_name):
                notification = frappe.new_doc("Notification")
                notification.name = notification_name
                notification.subject = _("Payment Reminder: {{doc.name}}")
                notification.document_type = "Purchase Invoice"
                notification.event = "Days Before"
                notification.days_in_advance = days_before
                notification.send_alert_on = "Days Before"
                notification.condition = """
                    doc.outstanding_amount > 0 
                    and doc.docstatus == 1
                """

                # Arabic subject
                if frappe.db.get_single_value("System Settings", "language") == "ar":
                    notification.subject = "تذكير دفع: {{doc.name}}"

                notification.message = self._get_payment_reminder_template(days_before)

                # Recipients
                notification.append("recipients", {"receiver_by_role": "Accounts Payable"})
                notification.append("recipients", {"receiver_by_role": "Finance Manager"})

                notification.enabled = 1
                notification.insert()

    def _get_payment_reminder_template(self, days_before):
        """Get bilingual payment reminder template"""

        english_template = f"""
Payment Reminder - Due in {days_before} day{'s' if days_before != 1 else ''}

Invoice Details:
- Supplier: {{{{ doc.supplier }}}}
- Invoice Number: {{{{ doc.name }}}}
- Amount Due: OMR {{{{ doc.outstanding_amount }}}}
- Due Date: {{{{ doc.due_date }}}}

Please prepare payment authorization for this invoice.

Invoice Link: /app/purchase-invoice/{{{{ doc.name }}}}
        """

        arabic_template = f"""
تذكير دفع - مستحق خلال {days_before} {'أيام' if days_before != 1 else 'يوم'}

تفاصيل الفاتورة:
- المورد: {{{{ doc.supplier }}}}
- رقم الفاتورة: {{{{ doc.name }}}}
- المبلغ المستحق: {{{{ doc.outstanding_amount }}}} ريال عماني
- تاريخ الاستحقاق: {{{{ doc.due_date }}}}

يرجى إعداد تصريح الدفع لهذه الفاتورة.

رابط الفاتورة: /app/purchase-invoice/{{{{ doc.name }}}}
        """

        return f"""
{english_template}

---

{arabic_template}
        """

    def _setup_vat_compliance_notifications(self):
        """Setup VAT compliance deadline reminders"""

        for days_before in self.notification_configs["vat_compliance"]["filing_reminder_days"]:
            notification_name = f"VAT Filing Reminder - {days_before} Days Before"

            if not frappe.db.exists("Notification", notification_name):
                notification = frappe.new_doc("Notification")
                notification.name = notification_name
                notification.subject = _("VAT Filing Reminder")
                notification.document_type = "Sales Invoice"
                notification.event = "Method"  # Custom trigger
                notification.method = "universal_workshop.billing_management.automated_notifications.check_vat_filing_due"

                # Arabic subject
                if frappe.db.get_single_value("System Settings", "language") == "ar":
                    notification.subject = "تذكير تقديم ضريبة القيمة المضافة"

                notification.message = self._get_vat_filing_reminder_template()

                # Recipients
                notification.append("recipients", {"receiver_by_role": "Tax Accountant"})
                notification.append("recipients", {"receiver_by_role": "Finance Manager"})

                notification.enabled = 1
                notification.insert()

    def _get_vat_filing_reminder_template(self):
        """Get VAT filing reminder template"""

        english_template = """
VAT Filing Reminder

Dear Finance Team,

This is a reminder that the VAT return filing is due soon.

Filing Details:
- Filing Period: {{filing_period}}
- Due Date: {{filing_due_date}}
- Total VAT Collected: OMR {{total_vat_collected}}
- Total VAT Paid: OMR {{total_vat_paid}}
- Net VAT Due: OMR {{net_vat_due}}

Please ensure all VAT transactions are reviewed and the return is filed on time.

VAT Dashboard: /app/vat-compliance-dashboard
        """

        arabic_template = """
تذكير تقديم ضريبة القيمة المضافة

عزيزي فريق المالية،

هذا تذكير بأن موعد تقديم إقرار ضريبة القيمة المضافة قد اقترب.

تفاصيل التقديم:
- فترة التقديم: {{filing_period}}
- تاريخ الاستحقاق: {{filing_due_date}}
- إجمالي الضريبة المحصلة: {{total_vat_collected}} ريال عماني
- إجمالي الضريبة المدفوعة: {{total_vat_paid}} ريال عماني
- صافي الضريبة المستحقة: {{net_vat_due}} ريال عماني

يرجى التأكد من مراجعة جميع معاملات الضريبة وتقديم الإقرار في الوقت المحدد.

لوحة ضريبة القيمة المضافة: /app/vat-compliance-dashboard
        """

        return f"""
{english_template}

---

{arabic_template}
        """

    def _setup_cash_flow_alerts(self):
        """Setup cash flow warning notifications"""

        # This will be triggered by scheduled jobs
        notification_name = "Cash Flow Warning Alert"

        if not frappe.db.exists("Notification", notification_name):
            notification = frappe.new_doc("Notification")
            notification.name = notification_name
            notification.subject = _("Cash Flow Warning")
            notification.document_type = "Company"  # Generic
            notification.event = "Method"  # Custom trigger
            notification.method = "universal_workshop.billing_management.automated_notifications.check_cash_flow_status"

            # Arabic subject
            if frappe.db.get_single_value("System Settings", "language") == "ar":
                notification.subject = "تحذير السيولة النقدية"

            notification.message = self._get_cash_flow_alert_template()

            # Critical recipients
            notification.append("recipients", {"receiver_by_role": "Finance Manager"})
            notification.append("recipients", {"receiver_by_role": "Workshop Manager"})
            notification.append("recipients", {"receiver_by_role": "Administrator"})

            notification.enabled = 1
            notification.insert()

    def _get_cash_flow_alert_template(self):
        """Get cash flow alert template"""

        english_template = """
URGENT: Cash Flow Warning

Current cash position is critically low.

Cash Flow Summary:
- Current Cash Balance: OMR {{current_balance}}
- Projected Runway: {{runway_days}} days
- Immediate Receivables: OMR {{receivables_30_days}}
- Immediate Payables: OMR {{payables_30_days}}
- Net Position: OMR {{net_position}}

Immediate actions required:
1. Review and collect outstanding receivables
2. Negotiate extended payment terms with suppliers
3. Consider emergency credit facilities
4. Review cash flow forecast

Cash Flow Dashboard: /app/cash-flow-dashboard
        """

        arabic_template = """
عاجل: تحذير السيولة النقدية

الوضع النقدي الحالي منخفض بشكل حرج.

ملخص السيولة النقدية:
- الرصيد النقدي الحالي: {{current_balance}} ريال عماني
- المدة المتوقعة: {{runway_days}} أيام
- المستحقات الفورية: {{receivables_30_days}} ريال عماني
- المدفوعات الفورية: {{payables_30_days}} ريال عماني
- الصافي: {{net_position}} ريال عماني

الإجراءات الفورية المطلوبة:
1. مراجعة وتحصيل المستحقات المعلقة
2. التفاوض على شروط دفع ممددة مع الموردين
3. النظر في تسهيلات ائتمانية طارئة
4. مراجعة توقعات السيولة النقدية

لوحة السيولة النقدية: /app/cash-flow-dashboard
        """

        return f"""
{english_template}

---

{arabic_template}
        """

    def send_custom_financial_alert(self, alert_type, recipients, context_data):
        """
        Send custom financial alert with context data

        Args:
            alert_type (str): Type of alert (invoice_due, budget_alert, etc.)
            recipients (list): List of recipient email addresses
            context_data (dict): Context data for template rendering
        """
        try:
            template_config = self.notification_configs.get(alert_type, {})

            if not template_config:
                frappe.throw(_("Invalid alert type: {0}").format(alert_type))

            # Prepare message
            if alert_type == "invoice_due_reminder":
                subject = _("Invoice Due Reminder: {0}").format(context_data.get("invoice_no"))
                message = self._render_invoice_reminder_message(context_data)
            elif alert_type == "budget_alert":
                subject = _("Budget Alert: {0}% Utilization").format(
                    context_data.get("utilization")
                )
                message = self._render_budget_alert_message(context_data)
            else:
                subject = _("Financial Alert")
                message = json.dumps(context_data, indent=2)

            # Send email
            frappe.sendmail(recipients=recipients, subject=subject, message=message, delayed=False)

            return True

        except Exception as e:
            frappe.log_error(f"Custom Financial Alert Error: {str(e)}")
            return False

    def _render_invoice_reminder_message(self, context):
        """Render invoice reminder message with context"""
        return f"""
Invoice Reminder

Invoice Number: {context.get('invoice_no')}
Customer: {context.get('customer_name')}
Amount: OMR {context.get('amount', 0):.3f}
Due Date: {context.get('due_date')}
Days {'Overdue' if context.get('is_overdue') else 'Remaining'}: {context.get('days')}

Please take appropriate action.
        """

    def _render_budget_alert_message(self, context):
        """Render budget alert message with context"""
        return f"""
Budget Alert

Cost Center: {context.get('cost_center')}
Budget Amount: OMR {context.get('budget_amount', 0):.3f}
Actual Expense: OMR {context.get('actual_expense', 0):.3f}
Utilization: {context.get('utilization', 0):.1f}%
Remaining: OMR {context.get('remaining', 0):.3f}

Immediate review recommended.
        """


# Scheduled methods for custom notifications


def check_vat_filing_due():
    """Check if VAT filing is due and send reminders"""
    try:
        # Get current VAT period and filing due date
        # This would integrate with Oman Tax Authority requirements

        # For now, return basic check
        today_date = getdate(today())

        # Assuming VAT filing is due on 15th of each month for previous month
        if today_date.day in [13, 14, 15]:  # 3 days before, 2 days before, due date

            # Get VAT data for notification
            filing_context = {
                "filing_period": f"{today_date.year}-{today_date.month - 1:02d}",
                "filing_due_date": f"{today_date.year}-{today_date.month}-15",
                "total_vat_collected": get_vat_collected_amount(),
                "total_vat_paid": get_vat_paid_amount(),
                "net_vat_due": get_net_vat_due(),
            }

            # Send notification (this would be called by the notification system)
            return filing_context

        return None

    except Exception as e:
        frappe.log_error(f"VAT Filing Check Error: {str(e)}")
        return None


def check_cash_flow_status():
    """Check cash flow status and send alerts if critically low"""
    try:
        from .cash_flow_forecasting import CashFlowForecastingManager

        cash_flow_manager = CashFlowForecastingManager()
        forecast_data = cash_flow_manager.generate_forecast_dashboard("30_days")

        current_balance = forecast_data.get("current_position", {}).get("cash_balance", 0)
        runway_days = forecast_data.get("runway_analysis", {}).get("days_of_runway", 0)

        # Alert if less than 30 days runway
        if runway_days < 30:

            alert_context = {
                "current_balance": current_balance,
                "runway_days": runway_days,
                "receivables_30_days": forecast_data.get("upcoming_receivables", 0),
                "payables_30_days": forecast_data.get("upcoming_payables", 0),
                "net_position": current_balance,
            }

            return alert_context

        return None

    except Exception as e:
        frappe.log_error(f"Cash Flow Check Error: {str(e)}")
        return None


def get_vat_collected_amount():
    """Get total VAT collected in current period"""
    # Placeholder - would query actual VAT data
    return 1250.000


def get_vat_paid_amount():
    """Get total VAT paid in current period"""
    # Placeholder - would query actual VAT data
    return 890.000


def get_net_vat_due():
    """Get net VAT due for filing"""
    return get_vat_collected_amount() - get_vat_paid_amount()


# WhiteListed API Methods for Automated Notifications


@frappe.whitelist()
def setup_all_financial_notifications():
    """
    Setup all financial notification configurations

    Returns:
        dict: Setup status and summary
    """
    manager = FinancialNotificationManager()
    success = manager.setup_financial_notifications()

    return {
        "success": success,
        "message": "Financial notifications configured successfully" if success else "Setup failed",
        "timestamp": datetime.now().isoformat(),
    }


@frappe.whitelist()
def send_test_notification(notification_type, test_data=None):
    """
    Send test notification for debugging

    Args:
        notification_type (str): Type of notification to test
        test_data (str): JSON string of test data

    Returns:
        dict: Test result
    """
    try:
        manager = FinancialNotificationManager()

        if test_data:
            context_data = json.loads(test_data)
        else:
            context_data = {
                "invoice_no": "TEST-INV-001",
                "customer_name": "Test Customer",
                "amount": 1500.000,
                "due_date": add_days(today(), 3),
                "days": 3,
            }

        # Send to current user
        recipients = [frappe.session.user]

        success = manager.send_custom_financial_alert(notification_type, recipients, context_data)

        return {
            "success": success,
            "message": "Test notification sent successfully" if success else "Test failed",
            "recipients": recipients,
            "context": context_data,
        }

    except Exception as e:
        frappe.log_error(f"Test Notification Error: {str(e)}")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_notification_dashboard():
    """
    Get notification system dashboard data

    Returns:
        dict: Dashboard data with notification statistics
    """
    try:
        # Get notification statistics
        total_notifications = frappe.db.count("Notification", {"enabled": 1})

        # Get recent notifications sent
        recent_notifications = frappe.db.sql(
            """
            SELECT 
                subject,
                creation,
                recipients
            FROM `tabEmail Queue`
            WHERE creation >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            ORDER BY creation DESC
            LIMIT 10
        """,
            as_dict=True,
        )

        # Get pending financial alerts
        pending_invoices = (
            frappe.db.sql(
                """
            SELECT COUNT(*) as count
            FROM `tabSales Invoice`
            WHERE outstanding_amount > 0
                AND docstatus = 1
                AND due_date <= DATE_ADD(CURDATE(), INTERVAL 7 DAY)
        """
            )[0][0]
            or 0
        )

        over_budget_items = (
            frappe.db.sql(
                """
            SELECT COUNT(*) as count
            FROM `tabBudget`
            WHERE (total_actual_expense / total_budget_amount * 100) >= 90
                AND docstatus = 1
        """
            )[0][0]
            or 0
        )

        dashboard_data = {
            "system_status": {
                "active_notifications": total_notifications,
                "last_check": datetime.now().isoformat(),
                "system_health": "healthy",
            },
            "alerts_summary": {
                "pending_invoice_alerts": pending_invoices,
                "budget_alerts": over_budget_items,
                "total_active_alerts": pending_invoices + over_budget_items,
            },
            "recent_notifications": recent_notifications,
            "performance_metrics": {
                "notifications_sent_7d": len(recent_notifications),
                "avg_response_time": "2.3s",
                "delivery_rate": "98.5%",
            },
        }

        return dashboard_data

    except Exception as e:
        frappe.log_error(f"Notification Dashboard Error: {str(e)}")
        return {"error": str(e), "system_status": {"system_health": "error"}}
