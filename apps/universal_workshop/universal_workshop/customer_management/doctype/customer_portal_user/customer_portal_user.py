import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, random_string
import hashlib


class CustomerPortalUser(Document):
    def validate(self):
        self.validate_user_customer_link()
        self.validate_email_unique()
        self.update_customer_name()
        
    def before_save(self):
        if self.is_new():
            self.generate_api_credentials()
        
    def on_update(self):
        self.update_last_activity()
        
    def validate_user_customer_link(self):
        if self.user and self.customer:
            existing = frappe.db.get_value(
                "Customer Portal User", 
                {"user": self.user, "name": ("!=", self.name)}, 
                "name"
            )
            if existing:
                frappe.throw(_("User {0} is already linked to another Customer Portal User").format(self.user))
                
    def validate_email_unique(self):
        if self.email:
            existing = frappe.db.get_value(
                "Customer Portal User", 
                {"email": self.email, "name": ("!=", self.name)}, 
                "name"
            )
            if existing:
                frappe.throw(_("Email {0} is already registered").format(self.email))
                
    def update_customer_name(self):
        if self.customer:
            self.customer_name = frappe.db.get_value("Customer", self.customer, "customer_name")
            
    def generate_api_credentials(self):
        if not self.api_key:
            self.api_key = random_string(32)
        if not self.api_secret:
            self.api_secret = hashlib.sha256(random_string(64).encode()).hexdigest()
            
    def update_last_activity(self):
        if not self.flags.skip_activity_update:
            self.db_set("last_activity", now_datetime(), update_modified=False)
            
    def log_activity(self, activity_type, details=None):
        activity_log = self.get("activity_log") or []
        activity_log.append({
            "activity_type": activity_type,
            "timestamp": now_datetime(),
            "details": details or "",
            "ip_address": frappe.local.request_ip if hasattr(frappe.local, 'request_ip') else None
        })
        self.db_set("activity_log", activity_log)
        
    def increment_login_attempts(self):
        current_attempts = self.get("login_attempts") or 0
        self.db_set("login_attempts", current_attempts + 1)
        
        if current_attempts + 1 >= 5:
            self.db_set("account_locked", 1)
            self.log_activity("Account Locked", "Too many failed login attempts")
            
    def reset_login_attempts(self):
        self.db_set("login_attempts", 0)
        if self.account_locked:
            self.db_set("account_locked", 0)
            
    def update_last_login(self):
        self.db_set("last_login", now_datetime())
        self.reset_login_attempts()
        self.log_activity("Successful Login")
        
    @frappe.whitelist()
    def enable_two_factor(self):
        self.db_set("two_factor_enabled", 1)
        self.log_activity("Two Factor Authentication Enabled")
        
    @frappe.whitelist()
    def disable_two_factor(self):
        self.db_set("two_factor_enabled", 0)
        self.log_activity("Two Factor Authentication Disabled")
        
    @frappe.whitelist()
    def regenerate_api_credentials(self):
        self.api_key = random_string(32)
        self.api_secret = hashlib.sha256(random_string(64).encode()).hexdigest()
        self.save()
        self.log_activity("API Credentials Regenerated")
        return {"api_key": self.api_key, "api_secret": self.api_secret}
        
    def get_permissions(self):
        return {
            "can_view_invoices": self.can_view_invoices,
            "can_book_appointments": self.can_book_appointments,
            "can_view_service_history": self.can_view_service_history,
            "can_track_vehicles": self.can_track_vehicles,
            "can_download_reports": self.can_download_reports,
            "can_update_profile": self.can_update_profile
        }
        
    def get_notification_settings(self):
        return {
            "sms_notifications": self.sms_notifications,
            "email_notifications": self.email_notifications,
            "whatsapp_notifications": self.whatsapp_notifications,
            "service_reminders": self.service_reminders,
            "payment_notifications": self.payment_notifications,
            "marketing_communications": self.marketing_communications
        }


@frappe.whitelist()
def get_customer_portal_user(user=None):
    if not user:
        user = frappe.session.user
        
    portal_user = frappe.get_value("Customer Portal User", {"user": user}, "*")
    if portal_user:
        return frappe.get_doc("Customer Portal User", portal_user.name)
    return None


@frappe.whitelist()
def check_portal_access(user=None):
    if not user:
        user = frappe.session.user
        
    portal_user = get_customer_portal_user(user)
    if not portal_user:
        return False
        
    if portal_user.status != "Active" or not portal_user.portal_enabled:
        return False
        
    if portal_user.account_locked:
        return False
        
    return True


@frappe.whitelist()
def authenticate_portal_user(email, password):
    from frappe.auth import check_password
    
    portal_user = frappe.get_value("Customer Portal User", {"email": email}, "*")
    if not portal_user:
        return {"success": False, "message": "Invalid credentials"}
        
    portal_user_doc = frappe.get_doc("Customer Portal User", portal_user.name)
    
    if portal_user_doc.account_locked:
        return {"success": False, "message": "Account is locked"}
        
    if portal_user_doc.status != "Active":
        return {"success": False, "message": "Account is not active"}
        
    try:
        check_password(portal_user_doc.user, password)
        portal_user_doc.update_last_login()
        return {"success": True, "user": portal_user_doc.user}
    except Exception:
        portal_user_doc.increment_login_attempts()
        return {"success": False, "message": "Invalid credentials"}