# Copyright (c) 2024, Said Al-Adowi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PushNotificationSubscription(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields to Document class

    def validate(self):
        """Validate push notification subscription"""
        self.validate_duplicate_subscription()
        self.set_device_info()

    def validate_duplicate_subscription(self):
        """Ensure no duplicate active subscriptions for same endpoint"""
        existing = frappe.db.exists(
            "Push Notification Subscription",
            {
                "endpoint": self.endpoint,
                "is_active": 1,
                "name": ["!=", self.name] if self.name else ["!=", ""],
            },
        )

        if existing:
            # Deactivate the existing subscription
            frappe.db.set_value("Push Notification Subscription", existing, "is_active", 0)
            frappe.msgprint(f"Deactivated existing subscription for this endpoint: {existing}")

    def set_device_info(self):
        """Set device information from user agent if available"""
        if not self.device_info:
            user_agent = frappe.request.headers.get("User-Agent", "") if frappe.request else ""
            self.device_info = user_agent[:500]  # Limit to 500 characters

    def before_save(self):
        """Set technician if user is a technician"""
        if not self.technician and self.user:
            technician = frappe.db.get_value("Technician", {"user": self.user}, "name")
            if technician:
                self.technician = technician

    def on_update(self):
        """Update last notification sent timestamp when activated"""
        if self.is_active and not self.last_notification_sent:
            self.db_set("last_notification_sent", frappe.utils.now())
