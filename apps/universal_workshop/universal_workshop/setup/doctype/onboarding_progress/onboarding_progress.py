# Copyright (c) 2025, Universal Workshop and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json

class OnboardingProgress(Document):
    def validate(self):
        """Validate onboarding progress data"""
        # Ensure completed_steps is valid JSON
        if self.completed_steps:
            try:
                json.loads(self.completed_steps)
            except json.JSONDecodeError:
                frappe.throw("Completed steps must be valid JSON array")
        
        # Ensure form_data is valid JSON
        if self.form_data:
            try:
                json.loads(self.form_data)
            except json.JSONDecodeError:
                frappe.throw("Form data must be valid JSON object")
        
        # Set timestamps
        if not self.started_at:
            self.started_at = frappe.utils.now()
        
        if self.status == "Completed" and not self.completed_at:
            self.completed_at = frappe.utils.now()
        
        if self.status == "Cancelled" and not self.cancelled_at:
            self.cancelled_at = frappe.utils.now()
    
    def get_progress_percentage(self):
        """Calculate progress percentage based on completed steps"""
        if not self.completed_steps:
            return 0
        
        try:
            completed = json.loads(self.completed_steps)
            total_steps = 3  # license_verification, admin_account, workshop_config
            return min((len(completed) / total_steps) * 100, 100)
        except:
            return 0
    
    def get_form_data(self):
        """Get form data as Python object"""
        if not self.form_data:
            return {}
        
        try:
            return json.loads(self.form_data)
        except:
            return {}
    
    def get_completed_steps(self):
        """Get completed steps as Python list"""
        if not self.completed_steps:
            return []
        
        try:
            return json.loads(self.completed_steps)
        except:
            return []
    
    def add_completed_step(self, step_name):
        """Add a step to completed steps"""
        completed = self.get_completed_steps()
        if step_name not in completed:
            completed.append(step_name)
            self.completed_steps = json.dumps(completed)
    
    def update_form_data(self, step_name, step_data):
        """Update form data for a specific step"""
        form_data = self.get_form_data()
        form_data[step_name] = step_data
        self.form_data = json.dumps(form_data)
    
    def on_update(self):
        """Trigger actions when progress is updated"""
        if self.status == "Completed":
            self.notify_completion()
    
    def notify_completion(self):
        """Send notification when onboarding is completed"""
        try:
            # Send email notification to admin
            if self.user and frappe.db.exists("User", self.user):
                user_doc = frappe.get_doc("User", self.user)
                
                subject = "Workshop Onboarding Completed"
                message = f"""
                <h3>Congratulations! Workshop onboarding completed successfully.</h3>
                <p>User: {user_doc.full_name} ({user_doc.email})</p>
                <p>Completion Time: {self.completed_at}</p>
                <p>Your workshop is now ready to use.</p>
                """
                
                frappe.sendmail(
                    recipients=[user_doc.email],
                    subject=subject,
                    message=message,
                    delayed=False
                )
        except Exception as e:
            frappe.log_error(f"Failed to send completion notification: {str(e)}")

@frappe.whitelist()
def get_onboarding_stats():
    """Get onboarding completion statistics"""
    try:
        stats = frappe.db.sql("""
            SELECT 
                status,
                COUNT(*) as count,
                AVG(TIMESTAMPDIFF(MINUTE, started_at, COALESCE(completed_at, cancelled_at, NOW()))) as avg_duration_minutes
            FROM `tabOnboarding Progress`
            GROUP BY status
        """, as_dict=True)
        
        total = frappe.db.count("Onboarding Progress")
        
        result = {
            "total_onboardings": total,
            "by_status": {stat.status: stat for stat in stats},
            "completion_rate": 0
        }
        
        # Calculate completion rate
        completed = next((stat.count for stat in stats if stat.status == "Completed"), 0)
        if total > 0:
            result["completion_rate"] = (completed / total) * 100
        
        return result
        
    except Exception as e:
        frappe.log_error(f"Get onboarding stats failed: {str(e)}")
        return {"error": str(e)}

@frappe.whitelist()
def cleanup_old_progress(days=30):
    """Cleanup old cancelled/expired onboarding progress records"""
    try:
        from frappe.utils import add_days, nowdate
        
        cutoff_date = add_days(nowdate(), -days)
        
        # Delete old cancelled records
        cancelled_records = frappe.db.sql("""
            SELECT name FROM `tabOnboarding Progress`
            WHERE status = 'Cancelled' 
            AND DATE(cancelled_at) <= %s
        """, (cutoff_date,), as_dict=True)
        
        # Delete old incomplete records
        incomplete_records = frappe.db.sql("""
            SELECT name FROM `tabOnboarding Progress`
            WHERE status = 'In Progress' 
            AND DATE(started_at) <= %s
        """, (cutoff_date,), as_dict=True)
        
        deleted_count = 0
        for record in cancelled_records + incomplete_records:
            frappe.delete_doc("Onboarding Progress", record.name, ignore_permissions=True)
            deleted_count += 1
        
        frappe.db.commit()
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"Cleaned up {deleted_count} old onboarding records"
        }
        
    except Exception as e:
        frappe.log_error(f"Cleanup old progress failed: {str(e)}")
        return {"success": False, "error": str(e)}