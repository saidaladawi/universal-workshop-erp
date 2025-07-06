# Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now, add_to_date, format_datetime, get_datetime
import json
from datetime import datetime, timedelta


class CommunicationHistory(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields

    def validate(self):
        """Validate communication history data"""
        self.validate_customer_details()
        self.validate_phone_number()
        self.validate_message_content()
        self.validate_template_variables()
        self.validate_delivery_dates()

    def before_save(self):
        """Set default values before saving"""
        self.set_customer_details()
        self.set_compliance_defaults()
        self.calculate_retention_date()
        self.set_triggered_by()

    def after_insert(self):
        """Actions after communication record is created"""
        self.update_customer_communication_stats()

    def validate_customer_details(self):
        """Validate customer information"""
        if not self.customer:
            frappe.throw(_("Customer is required"))

        if not self.phone_number and not self.email:
            frappe.throw(_("Either phone number or email is required"))

    def validate_phone_number(self):
        """Validate Oman phone number format if provided"""
        if self.phone_number:
            import re

            oman_pattern = r"^\+968\s?\d{8}$"
            if not re.match(oman_pattern, self.phone_number):
                frappe.throw(_("Invalid Oman phone number format. Use: +968 XXXXXXXX"))

    def validate_message_content(self):
        """Validate message content requirements"""
        if not self.message_content and not self.template_used:
            frappe.throw(_("Either message content or template is required"))

        # Validate Arabic content if provided
        if self.message_content_ar:
            # Check for Arabic characters

            if not re.search(r"[\u0600-\u06FF]", self.message_content_ar):
                frappe.msgprint(
                    _("Warning: Arabic content field doesn't contain Arabic characters")
                )

    def validate_template_variables(self):
        """Validate template variables JSON format"""
        if self.template_variables:
            try:
                json.loads(self.template_variables)
            except json.JSONDecodeError:
                frappe.throw(_("Template variables must be valid JSON"))

    def validate_delivery_dates(self):
        """Validate delivery date sequence"""
        dates = []
        if self.sent_datetime:
            dates.append(("sent", self.sent_datetime))
        if self.delivered_datetime:
            dates.append(("delivered", self.delivered_datetime))
        if self.read_datetime:
            dates.append(("read", self.read_datetime))

        # Check chronological order
        dates.sort(key=lambda x: get_datetime(x[1]))
        expected_order = ["sent", "delivered", "read"]

        for i, (event_type, _) in enumerate(dates):
            if i < len(expected_order) and event_type != expected_order[i]:
                frappe.throw(
                    _("Delivery dates must be in chronological order: sent → delivered → read")
                )

    def set_customer_details(self):
        """Set customer details from linked customer"""
        if self.customer and not self.customer_name:
            customer_doc = frappe.get_doc("Customer", self.customer)
            self.customer_name = customer_doc.customer_name

            # Get contact details if not provided
            if not self.email and customer_doc.email_id:
                self.email = customer_doc.email_id

    def set_compliance_defaults(self):
        """Set compliance flags based on consent"""
        # Check consent status
        if self.customer and self.phone_number:
            consent_status = self.check_customer_consent()
            self.consent_given = consent_status.get("has_consent", False)
            self.consent_record = consent_status.get("consent_record")

        # Always compliant if properly documented
        self.gdpr_compliant = 1

    def calculate_retention_date(self):
        """Calculate data retention date based on compliance requirements"""
        if not self.data_retention_date:
            # Default retention: 7 years for transactional, 3 years for marketing
            retention_years = 7 if self.communication_type == "Transactional" else 3
            self.data_retention_date = add_to_date(now(), years=retention_years)

    def set_triggered_by(self):
        """Set who triggered this communication"""
        if not self.triggered_by_user:
            self.triggered_by_user = frappe.session.user

    def check_customer_consent(self):
        """Check if customer has valid consent for this communication"""
        try:
            from universal_workshop.communication_management.doctype.communication_consent.communication_consent import (
                get_customer_consent_status,
            )

            consent_status = get_customer_consent_status(
                customer=self.customer, phone_number=self.phone_number
            )

            # Get the actual consent record
            consent_record = frappe.get_list(
                "Communication Consent",
                filters={
                    "customer": self.customer,
                    "phone_number": self.phone_number,
                    "consent_status": "Given",
                },
                limit=1,
            )

            return {
                "has_consent": consent_status.get(self.communication_channel, False),
                "consent_record": consent_record[0].name if consent_record else None,
                "full_status": consent_status,
            }

        except Exception as e:
            frappe.log_error(f"Error checking consent: {str(e)}")
            return {"has_consent": False, "consent_record": None}

    def update_customer_communication_stats(self):
        """Update customer communication statistics"""
        try:
            # Update last communication date on customer record
            customer_doc = frappe.get_doc("Customer", self.customer)

            # Add custom field if it doesn't exist
            if not hasattr(customer_doc, "last_communication_date"):
                self.add_custom_field_to_customer()

            customer_doc.db_set("last_communication_date", now())

        except Exception as e:
            frappe.log_error(f"Error updating customer stats: {str(e)}")

    def add_custom_field_to_customer(self):
        """Add custom fields to Customer DocType for communication tracking"""
        custom_fields = [
            {
                "fieldname": "last_communication_date",
                "label": "Last Communication Date",
                "fieldtype": "Datetime",
                "insert_after": "mobile_no",
                "read_only": 1,
            },
            {
                "fieldname": "communication_preferences",
                "label": "Communication Preferences",
                "fieldtype": "Small Text",
                "insert_after": "last_communication_date",
            },
        ]

        for field in custom_fields:
            if not frappe.db.exists(
                "Custom Field", {"dt": "Customer", "fieldname": field["fieldname"]}
            ):
                custom_field = frappe.new_doc("Custom Field")
                custom_field.dt = "Customer"
                custom_field.update(field)
                custom_field.insert(ignore_permissions=True)

    def update_delivery_status(self, status, external_id=None, error_msg=None):
        """Update delivery status from external provider webhook"""
        status_mapping = {
            "sent": "Sent",
            "delivered": "Delivered",
            "read": "Read",
            "failed": "Failed",
            "undelivered": "Undelivered",
        }

        self.delivery_status = status_mapping.get(status, status)
        self.communication_status = status_mapping.get(status, status)

        if external_id:
            self.external_message_id = external_id

        if error_msg:
            self.error_message = error_msg

        # Update timestamps
        if status == "sent" and not self.sent_datetime:
            self.sent_datetime = now()
        elif status == "delivered" and not self.delivered_datetime:
            self.delivered_datetime = now()
        elif status == "read" and not self.read_datetime:
            self.read_datetime = now()

        if status == "failed":
            self.delivery_attempts = (self.delivery_attempts or 0) + 1

        self.save(ignore_permissions=True)

    def get_delivery_timeline(self):
        """Get delivery timeline for this communication"""
        timeline = []

        if self.sent_datetime:
            timeline.append(
                {"event": "Sent", "datetime": self.sent_datetime, "status": "completed"}
            )

        if self.delivered_datetime:
            timeline.append(
                {"event": "Delivered", "datetime": self.delivered_datetime, "status": "completed"}
            )

        if self.read_datetime:
            timeline.append(
                {"event": "Read", "datetime": self.read_datetime, "status": "completed"}
            )

        if self.delivery_status == "Failed":
            timeline.append(
                {
                    "event": "Failed",
                    "datetime": self.modified,
                    "status": "failed",
                    "error": self.error_message,
                }
            )

        return timeline

    def calculate_delivery_metrics(self):
        """Calculate delivery time metrics"""
        metrics = {}

        if self.sent_datetime and self.delivered_datetime:
            sent_time = get_datetime(self.sent_datetime)
            delivered_time = get_datetime(self.delivered_datetime)
            metrics["delivery_time_seconds"] = (delivered_time - sent_time).total_seconds()

        if self.delivered_datetime and self.read_datetime:
            delivered_time = get_datetime(self.delivered_datetime)
            read_time = get_datetime(self.read_datetime)
            metrics["read_time_seconds"] = (read_time - delivered_time).total_seconds()

        if self.sent_datetime and self.read_datetime:
            sent_time = get_datetime(self.sent_datetime)
            read_time = get_datetime(self.read_datetime)
            metrics["total_time_seconds"] = (read_time - sent_time).total_seconds()

        return metrics


# WhiteListed Methods
@frappe.whitelist()
def create_communication_record(
    customer,
    phone_number,
    communication_type,
    communication_channel,
    message_content,
    template_used=None,
    template_variables=None,
    external_message_id=None,
    queue_id=None,
):
    """Create new communication history record"""
    try:
        comm = frappe.new_doc("Communication History")
        comm.update(
            {
                "customer": customer,
                "phone_number": phone_number,
                "communication_type": communication_type,
                "communication_channel": communication_channel,
                "message_content": message_content,
                "template_used": template_used,
                "template_variables": template_variables,
                "external_message_id": external_message_id,
                "queue_id": queue_id,
                "communication_status": "Queued",
                "delivery_status": "Pending",
            }
        )

        comm.insert(ignore_permissions=True)

        return {
            "success": True,
            "communication_id": comm.name,
            "message": _("Communication record created successfully"),
        }

    except Exception as e:
        frappe.log_error(f"Error creating communication record: {str(e)}")
        return {"success": False, "message": _("Failed to create communication record")}


@frappe.whitelist()
def update_delivery_status_webhook(external_id, status, error_message=None):
    """Update delivery status from external provider webhook"""
    try:
        # Find communication record by external ID
        comm_records = frappe.get_list(
            "Communication History", filters={"external_message_id": external_id}, limit=1
        )

        if not comm_records:
            return {"success": False, "message": "Communication record not found"}

        comm = frappe.get_doc("Communication History", comm_records[0].name)
        comm.update_delivery_status(status, external_id, error_message)

        return {"success": True, "message": f"Status updated to {status}"}

    except Exception as e:
        frappe.log_error(f"Error updating delivery status: {str(e)}")
        return {"success": False, "message": "Failed to update delivery status"}


@frappe.whitelist()
def get_customer_communication_history(customer, limit=50, communication_type=None):
    """Get communication history for a customer"""
    try:
        filters = {"customer": customer}
        if communication_type:
            filters["communication_type"] = communication_type

        communications = frappe.get_list(
            "Communication History",
            filters=filters,
            fields=["*"],
            order_by="creation desc",
            limit=limit,
        )

        # Add delivery metrics for each communication
        for comm in communications:
            doc = frappe.get_doc("Communication History", comm.name)
            comm["delivery_timeline"] = doc.get_delivery_timeline()
            comm["delivery_metrics"] = doc.calculate_delivery_metrics()

        return {"success": True, "communications": communications}

    except Exception as e:
        frappe.log_error(f"Error getting communication history: {str(e)}")
        return {"success": False, "message": "Failed to get communication history"}


@frappe.whitelist()
def get_communication_analytics(
    date_from=None, date_to=None, communication_type=None, communication_channel=None
):
    """Get communication analytics and statistics"""
    try:
        # Build filters
        filters = []
        if date_from:
            filters.append(["creation", ">=", date_from])
        if date_to:
            filters.append(["creation", "<=", date_to])
        if communication_type:
            filters.append(["communication_type", "=", communication_type])
        if communication_channel:
            filters.append(["communication_channel", "=", communication_channel])

        # Get total communications
        total_communications = frappe.db.count("Communication History", filters)

        # Get delivery status breakdown
        status_breakdown = frappe.db.sql(
            """
            SELECT delivery_status, COUNT(*) as count
            FROM `tabCommunication History`
            WHERE {where_clause}
            GROUP BY delivery_status
        """.format(
                where_clause=(
                    " AND ".join([f"`{f[0]}` {f[1]} '{f[2]}'" for f in filters])
                    if filters
                    else "1=1"
                )
            ),
            as_dict=True,
        )

        # Get channel breakdown
        channel_breakdown = frappe.db.sql(
            """
            SELECT communication_channel, COUNT(*) as count,
                   AVG(CASE WHEN sent_datetime IS NOT NULL AND delivered_datetime IS NOT NULL 
                       THEN TIMESTAMPDIFF(SECOND, sent_datetime, delivered_datetime) END) as avg_delivery_time
            FROM `tabCommunication History`
            WHERE {where_clause}
            GROUP BY communication_channel
        """.format(
                where_clause=(
                    " AND ".join([f"`{f[0]}` {f[1]} '{f[2]}'" for f in filters])
                    if filters
                    else "1=1"
                )
            ),
            as_dict=True,
        )

        # Calculate success rate
        successful = len(
            [s for s in status_breakdown if s.delivery_status in ["Delivered", "Read"]]
        )
        success_rate = (
            (
                sum(
                    [
                        s.count
                        for s in status_breakdown
                        if s.delivery_status in ["Delivered", "Read"]
                    ]
                )
                / total_communications
                * 100
            )
            if total_communications > 0
            else 0
        )

        # Get top customers by communication volume
        top_customers = frappe.db.sql(
            """
            SELECT customer, customer_name, COUNT(*) as communication_count
            FROM `tabCommunication History`
            WHERE {where_clause}
            GROUP BY customer, customer_name
            ORDER BY communication_count DESC
            LIMIT 10
        """.format(
                where_clause=(
                    " AND ".join([f"`{f[0]}` {f[1]} '{f[2]}'" for f in filters])
                    if filters
                    else "1=1"
                )
            ),
            as_dict=True,
        )

        # Calculate costs
        total_cost = (
            frappe.db.sql(
                """
            SELECT SUM(external_cost) as total_cost
            FROM `tabCommunication History`
            WHERE {where_clause} AND external_cost IS NOT NULL
        """.format(
                    where_clause=(
                        " AND ".join([f"`{f[0]}` {f[1]} '{f[2]}'" for f in filters])
                        if filters
                        else "1=1"
                    )
                ),
                as_dict=True,
            )[0].total_cost
            or 0
        )

        return {
            "success": True,
            "analytics": {
                "total_communications": total_communications,
                "success_rate": round(success_rate, 2),
                "total_cost_omr": round(total_cost, 3),
                "status_breakdown": status_breakdown,
                "channel_breakdown": channel_breakdown,
                "top_customers": top_customers,
            },
        }

    except Exception as e:
        frappe.log_error(f"Error getting communication analytics: {str(e)}")
        return {"success": False, "message": "Failed to get communication analytics"}


@frappe.whitelist()
def handle_opt_out_request(external_id, method="SMS STOP"):
    """Handle customer opt-out request from communication"""
    try:
        # Find communication record
        comm_records = frappe.get_list(
            "Communication History",
            filters={"external_message_id": external_id},
            fields=["customer", "phone_number", "communication_channel"],
            limit=1,
        )

        if not comm_records:
            return {"success": False, "message": "Communication record not found"}

        comm_data = comm_records[0]

        # Update communication record
        comm = frappe.get_doc("Communication History", comm_records[0].name)
        comm.opt_out_requested = 1
        comm.save(ignore_permissions=True)

        # Find and update consent records
        consent_records = frappe.get_list(
            "Communication Consent",
            filters={
                "customer": comm_data.customer,
                "phone_number": comm_data.phone_number,
                "consent_channel": comm_data.communication_channel,
                "consent_status": "Given",
            },
        )

        for consent_record in consent_records:
            consent_doc = frappe.get_doc("Communication Consent", consent_record.name)
            consent_doc.withdraw_consent(method, "Customer requested opt-out via communication")

        return {
            "success": True,
            "message": f"Opt-out processed for {len(consent_records)} consent records",
        }

    except Exception as e:
        frappe.log_error(f"Error handling opt-out request: {str(e)}")
        return {"success": False, "message": "Failed to process opt-out request"}


@frappe.whitelist()
def cleanup_old_records():
    """Clean up old communication records based on retention policy"""
    try:
        deleted_count = 0

        # Get records past their retention date
        old_records = frappe.get_list(
            "Communication History", filters={"data_retention_date": ["<", now()]}, fields=["name"]
        )

        for record in old_records:
            frappe.delete_doc("Communication History", record.name, ignore_permissions=True)
            deleted_count += 1

        return {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"Cleaned up {deleted_count} old communication records",
        }

    except Exception as e:
        frappe.log_error(f"Error cleaning up old records: {str(e)}")
        return {"success": False, "message": "Failed to clean up old records"}
