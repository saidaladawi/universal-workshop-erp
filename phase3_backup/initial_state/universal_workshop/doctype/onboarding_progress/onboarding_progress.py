# Copyright (c) 2025, Said Al-Adawi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class OnboardingProgress(Document):
    def validate(self):
        """Validate onboarding progress data"""
        if self.completed_on and not self.completed_by:
            self.completed_by = frappe.session.user

    def on_submit(self):
        """Actions to perform when onboarding is submitted"""
        # Mark setup as complete in system settings
        frappe.db.set_default("setup_complete", "1")

        # Log the completion
        frappe.log_error(
            f"Onboarding completed for workshop: {self.workshop_profile}",
            "Onboarding Complete"
        )

    def on_cancel(self):
        """Actions to perform when onboarding is cancelled"""
        # Reset setup completion
        frappe.db.set_default("setup_complete", "0")
