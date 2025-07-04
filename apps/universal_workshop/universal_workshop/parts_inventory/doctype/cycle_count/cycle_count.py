import frappe
from frappe import _
from frappe.model.document import Document
from datetime import datetime, timedelta

class CycleCount(Document):
    # pylint: disable=no-member
    
    def validate(self):
        """Validate cycle count settings"""
        self.validate_count_settings()
        self.validate_location_settings()
        self.validate_assignment()
        self.set_default_values()
    
    def validate_count_settings(self):
        """Validate count configuration"""
        if self.tolerance_percentage and self.tolerance_percentage < 0:
            frappe.throw(_("Tolerance percentage cannot be negative"))
        
        if self.tolerance_percentage and self.tolerance_percentage > 100:
            frappe.throw(_("Tolerance percentage cannot exceed 100%"))
    
    def validate_location_settings(self):
        """Validate location settings"""
        if not self.warehouse:
            frappe.throw(_("Warehouse is required"))
        
        # Validate that at least one filter is applied
        if not any([self.item_group, self.item_category, self.specific_items]):
            frappe.throw(_("At least one item filter must be specified"))
    
    def validate_assignment(self):
        """Validate assignment settings"""
        if not self.assigned_to:
            frappe.throw(_("Assigned user is required"))
    
    def set_default_values(self):
        """Set default values before saving"""
        if not self.cycle_count_status:
            self.cycle_count_status = "Draft"
        
        if not self.created_by:
            self.created_by = frappe.session.user
        
        if not self.creation_date:
            self.creation_date = frappe.utils.now()
    
    def before_save(self):
        """Actions before saving"""
        self.calculate_progress()
    
    def calculate_progress(self):
        """Calculate count progress"""
        if self.total_items and self.counted_items:
            self.pending_items = self.total_items - self.counted_items
            self.completion_percentage = (self.counted_items / self.total_items) * 100
        else:
            self.pending_items = 0
            self.completion_percentage = 0
    
    @frappe.whitelist()
    def start_count(self):
        """Start the cycle count process"""
        if self.cycle_count_status != "Draft":
            frappe.throw(_("Cycle count can only be started from Draft status"))
        
        # Generate item list based on filters
        items = self.generate_item_list()
        
        if not items:
            frappe.throw(_("No items found matching the specified criteria"))
        
        self.total_items = len(items)
        self.counted_items = 0
        self.pending_items = self.total_items
        self.completion_percentage = 0
        self.cycle_count_status = "In Progress"
        self.start_time = frappe.utils.now()
        
        self.save()
        
        return {
            "status": "success",
            "message": f"Cycle count started with {self.total_items} items",
            "total_items": self.total_items
        }
    
    def generate_item_list(self):
        """Generate list of items to count based on filters"""
        filters = {"disabled": 0}
        
        if self.warehouse:
            filters["warehouse"] = self.warehouse
        
        if self.item_group:
            filters["item_group"] = self.item_group
        
        if self.item_category:
            filters["item_category"] = self.item_category
        
        # Get items from stock
        items = frappe.get_list(
            "Stock Ledger Entry",
            filters=filters,
            fields=["item_code", "warehouse", "qty_after_transaction"],
            group_by="item_code, warehouse"
        )
        
        return items
    
    @frappe.whitelist()
    def complete_count(self):
        """Complete the cycle count process"""
        if self.cycle_count_status != "In Progress":
            frappe.throw(_("Cycle count must be in progress to complete"))
        
        if self.completion_percentage < 100:
            frappe.throw(_("Cannot complete count until all items are counted"))
        
        self.cycle_count_status = "Completed"
        self.end_time = frappe.utils.now()
        
        # Calculate duration
        if self.start_time and self.end_time:
            start_dt = frappe.utils.get_datetime(self.start_time)
            end_dt = frappe.utils.get_datetime(self.end_time)
            self.duration = str(end_dt - start_dt)
        
        # Calculate variances
        self.calculate_variances()
        
        self.save()
        
        return {
            "status": "success",
            "message": "Cycle count completed successfully",
            "duration": self.duration,
            "variance_count": self.items_with_variance
        }
    
    def calculate_variances(self):
        """Calculate count variances"""
        # This would typically query the actual count results
        # For now, using placeholder logic
        self.items_with_variance = 0
        self.total_variance_value = 0.0
        self.variance_percentage = 0.0
        
        # Placeholder calculation
        if self.total_items > 0:
            self.items_with_variance = int(self.total_items * 0.05)  # 5% variance rate
            self.total_variance_value = 500.0  # Placeholder value
            self.variance_percentage = (self.items_with_variance / self.total_items) * 100
    
    @frappe.whitelist()
    def get_count_progress(self):
        """Get current count progress"""
        return {
            "total_items": self.total_items or 0,
            "counted_items": self.counted_items or 0,
            "pending_items": self.pending_items or 0,
            "completion_percentage": self.completion_percentage or 0,
            "status": self.cycle_count_status
        }
    
    @frappe.whitelist()
    def approve_count(self):
        """Approve the cycle count"""
        if self.cycle_count_status != "Completed":
            frappe.throw(_("Cycle count must be completed before approval"))
        
        if self.requires_approval:
            self.approved_by = frappe.session.user
            self.approval_date = frappe.utils.now()
        
        self.cycle_count_status = "Approved"
        self.save()
        
        return {
            "status": "success",
            "message": "Cycle count approved successfully"
        }
    
    @frappe.whitelist()
    def generate_count_report(self):
        """Generate cycle count report"""
        if self.cycle_count_status not in ["Completed", "Approved"]:
            frappe.throw(_("Cycle count must be completed to generate report"))
        
        # Placeholder report data
        report_data = {
            "cycle_count_name": self.cycle_count_name,
            "count_date": self.cycle_count_date,
            "assigned_to": self.assigned_to,
            "warehouse": self.warehouse,
            "total_items": self.total_items,
            "counted_items": self.counted_items,
            "items_with_variance": self.items_with_variance,
            "variance_percentage": self.variance_percentage,
            "total_variance_value": self.total_variance_value,
            "duration": self.duration,
            "status": self.cycle_count_status
        }
        
        return report_data 