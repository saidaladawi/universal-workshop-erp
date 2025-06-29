# Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class StockTransferLog(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields to Document class
    
    def before_insert(self):
        """Set default values before saving"""
        if not self.user:
            self.user = frappe.session.user
        if not self.timestamp:
            self.timestamp = frappe.utils.now()
        
        # Set system information for audit trail
        if hasattr(frappe.local, 'request'):
            request = frappe.local.request
            if request:
                self.ip_address = frappe.utils.get_request_site_address(request)
                self.user_agent = request.headers.get('User-Agent', '')[:140]  # Limit length
        
        if hasattr(frappe.local, 'session_obj'):
            self.session_id = frappe.local.session_obj.sid[:20]  # Limit length
    
    def validate(self):
        """Validate the log entry"""
        # Ensure transfer_id exists
        if self.transfer_id and not frappe.db.exists("Stock Entry", self.transfer_id):
            frappe.throw(frappe._("Stock Entry {0} does not exist").format(self.transfer_id))
        
        # Validate status values
        valid_statuses = ["Draft", "Source Approved", "Target Approved", "In Transit", "Completed", "Cancelled"]
        if self.status and self.status not in valid_statuses:
            frappe.throw(frappe._("Invalid status: {0}").format(self.status))

@frappe.whitelist()
def create_transfer_log(transfer_id, status, remarks=None, reference_doctype=None, reference_name=None):
    """
    Create a new transfer log entry
    
    Args:
        transfer_id (str): Stock Entry ID
        status (str): Transfer status
        remarks (str): Log remarks
        reference_doctype (str): Related DocType
        reference_name (str): Related document name
    
    Returns:
        str: Created log entry name
    """
    try:
        log_entry = frappe.new_doc("Stock Transfer Log")
        log_entry.transfer_id = transfer_id
        log_entry.status = status
        log_entry.remarks = remarks or ""
        log_entry.reference_doctype = reference_doctype
        log_entry.reference_name = reference_name
        log_entry.insert(ignore_permissions=True)
        frappe.db.commit()
        
        return log_entry.name
        
    except Exception as e:
        frappe.log_error(f"Failed to create transfer log: {str(e)}")
        return None

@frappe.whitelist()
def get_transfer_logs(transfer_id, limit=50):
    """
    Get transfer logs for a specific transfer
    
    Args:
        transfer_id (str): Stock Entry ID
        limit (int): Number of logs to return
    
    Returns:
        list: Transfer logs
    """
    try:
        logs = frappe.get_list(
            "Stock Transfer Log",
            filters={"transfer_id": transfer_id},
            fields=[
                "name", "status", "user", "timestamp", "remarks",
                "reference_doctype", "reference_name", "ip_address"
            ],
            order_by="timestamp desc",
            limit=limit
        )
        
        # Add user details
        for log in logs:
            if log.user:
                user_details = frappe.get_cached_value("User", log.user, ["full_name", "email"], as_dict=True)
                if user_details:
                    log.user_full_name = user_details.get("full_name") or log.user
                    log.user_email = user_details.get("email")
        
        return logs
        
    except Exception as e:
        frappe.log_error(f"Failed to get transfer logs: {str(e)}")
        return []

@frappe.whitelist()
def get_transfer_activity_summary(date_range=30):
    """
    Get transfer activity summary
    
    Args:
        date_range (int): Number of days to analyze
    
    Returns:
        dict: Activity summary
    """
    try:
        from_date = frappe.utils.add_days(frappe.utils.nowdate(), -date_range)
        
        # Get activity counts by status
        activity_data = frappe.db.sql("""
            SELECT 
                status,
                COUNT(*) as count,
                DATE(timestamp) as log_date
            FROM `tabStock Transfer Log`
            WHERE timestamp >= %s
            GROUP BY status, DATE(timestamp)
            ORDER BY log_date DESC, status
        """, [from_date], as_dict=True)
        
        # Get user activity
        user_activity = frappe.db.sql("""
            SELECT 
                user,
                COUNT(*) as total_actions,
                COUNT(DISTINCT transfer_id) as unique_transfers
            FROM `tabStock Transfer Log`
            WHERE timestamp >= %s
            GROUP BY user
            ORDER BY total_actions DESC
            LIMIT 10
        """, [from_date], as_dict=True)
        
        # Add user details
        for activity in user_activity:
            if activity.user:
                user_details = frappe.get_cached_value("User", activity.user, ["full_name"], as_dict=True)
                if user_details:
                    activity.user_full_name = user_details.get("full_name") or activity.user
        
        return {
            "activity_data": activity_data,
            "user_activity": user_activity,
            "date_range": date_range
        }
        
    except Exception as e:
        frappe.log_error(f"Failed to get activity summary: {str(e)}")
        return {"error": str(e)} 