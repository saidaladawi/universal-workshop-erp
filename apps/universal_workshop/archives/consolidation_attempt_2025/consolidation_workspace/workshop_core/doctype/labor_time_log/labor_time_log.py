# -*- coding: utf-8 -*-
# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, time_diff, now, get_datetime

class LaborTimeLog(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields to Document class
    
    def validate(self):
        """Validate labor time log before saving"""
        self.validate_technician_availability()
        self.validate_time_entries()
        self.set_technician_details()
        self.calculate_totals()
        
    def before_save(self):
        """Set defaults before saving"""
        if not self.technician_name and self.technician:
            self.set_technician_details()
        
        if not self.hourly_rate and self.technician:
            self.set_default_rates()
            
    def validate_technician_availability(self):
        """Check if technician is available for time tracking"""
        if not self.technician:
            return
            
        # Check for overlapping active time logs
        if self.status == "Active":
            overlapping_logs = frappe.db.exists("Labor Time Log", {
                "technician": self.technician,
                "status": "Active",
                "name": ["!=", self.name or ""],
                "end_time": ["is", "not set"]
            })
            
            if overlapping_logs:
                frappe.throw(_("Technician {0} already has an active time tracking session").format(self.technician))
    
    def validate_time_entries(self):
        """Validate time-related fields"""
        if not self.start_time:
            frappe.throw(_("Start time is required"))
            
        if self.end_time and self.start_time:
            if get_datetime(self.end_time) <= get_datetime(self.start_time):
                frappe.throw(_("End time must be after start time"))
                
        if self.pause_time and self.start_time:
            if get_datetime(self.pause_time) <= get_datetime(self.start_time):
                frappe.throw(_("Pause time must be after start time"))
                
        if self.resume_time and self.pause_time:
            if get_datetime(self.resume_time) <= get_datetime(self.pause_time):
                frappe.throw(_("Resume time must be after pause time"))
    
    def set_technician_details(self):
        """Set technician name fields from linked technician"""
        if self.technician:
            technician_doc = frappe.get_doc("Technician", self.technician)
            self.technician_name = technician_doc.technician_name
            self.technician_name_ar = technician_doc.technician_name_ar
    
    def set_default_rates(self):
        """Set default hourly rates from technician profile"""
        if self.technician:
            technician_doc = frappe.get_doc("Technician", self.technician)
            self.hourly_rate = technician_doc.hourly_rate or 10.0
            
            # Set billing rate (usually higher than cost rate)
            if technician_doc.billing_rate:
                self.billing_rate = technician_doc.billing_rate
            else:
                # Default billing rate is 150% of hourly rate
                self.billing_rate = flt(self.hourly_rate) * 1.5
    
    def calculate_totals(self):
        """Calculate total hours and costs"""
        if self.status == "Completed" and self.start_time and self.end_time:
            # Calculate total elapsed time
            total_elapsed = time_diff(self.end_time, self.start_time)
            self.total_hours = flt(total_elapsed) / 3600  # Convert seconds to hours
            
            # Calculate costs
            self.total_cost = flt(self.total_hours) * flt(self.hourly_rate)
            
            if self.billable and self.billing_rate:
                self.billing_amount = flt(self.total_hours) * flt(self.billing_rate)
        elif self.status == "Active" and self.start_time:
            # For active tracking, show current elapsed time
            current_time = now()
            current_elapsed = time_diff(current_time, self.start_time)
            self.total_hours = flt(current_elapsed) / 3600
            self.total_cost = flt(self.total_hours) * flt(self.hourly_rate)
    
    def on_update(self):
        """After saving the document"""
        # Update service order labor costs if completed
        if self.status == "Completed" and self.service_order:
            self.update_service_order_costs()
    
    def update_service_order_costs(self):
        """Update total labor costs in the linked service order"""
        try:
            # Calculate total labor costs for this service order
            total_costs = frappe.db.sql("""
                SELECT 
                    SUM(total_hours) as total_hours,
                    SUM(total_cost) as total_cost,
                    SUM(billing_amount) as billing_amount
                FROM `tabLabor Time Log`
                WHERE service_order = %s AND status = 'Completed'
            """, [self.service_order], as_dict=True)[0]
            
            if total_costs:
                service_order = frappe.get_doc("Service Order", self.service_order)
                service_order.total_labor_hours = flt(total_costs.total_hours or 0)
                service_order.total_labor_cost = flt(total_costs.total_cost or 0)
                service_order.total_billable_amount = flt(total_costs.billing_amount or 0)
                service_order.save()
                
        except Exception as e:
            frappe.log_error(f"Error updating service order costs: {str(e)}")
    
    def start_tracking(self):
        """Start time tracking"""
        if self.status != "Active":
            self.status = "Active"
            self.start_time = now()
            self.save()
            return True
        return False
    
    def pause_tracking(self, reason=None):
        """Pause active time tracking"""
        if self.status == "Active":
            # Calculate elapsed time so far
            if self.start_time:
                elapsed = time_diff(now(), self.start_time)
                self.total_hours = flt(self.total_hours) + flt(elapsed) / 3600
            
            self.status = "Paused"
            self.pause_time = now()
            self.pause_reason = reason
            self.save()
            return True
        return False
    
    def resume_tracking(self):
        """Resume paused time tracking"""
        if self.status == "Paused":
            self.status = "Active"
            self.resume_time = now()
            self.save()
            return True
        return False
    
    def complete_tracking(self, completion_notes=None):
        """Complete time tracking"""
        if self.status in ["Active", "Paused"]:
            # Calculate final hours if active
            if self.status == "Active" and self.start_time:
                elapsed = time_diff(now(), self.start_time)
                self.total_hours = flt(self.total_hours) + flt(elapsed) / 3600
            
            self.status = "Completed"
            self.end_time = now()
            self.completion_notes = completion_notes
            self.calculate_totals()
            self.save()
            return True
        return False

# Utility functions for time tracking operations
def get_active_sessions(technician_id=None, service_order_id=None):
    """Get active time tracking sessions"""
    filters = {"status": ["in", ["Active", "Paused"]]}
    
    if technician_id:
        filters["technician"] = technician_id
    if service_order_id:
        filters["service_order"] = service_order_id
    
    return frappe.get_list("Labor Time Log",
                          filters=filters,
                          fields=["name", "technician", "technician_name", 
                                "service_order", "activity_type", "status",
                                "start_time", "total_hours", "hourly_rate"])

def get_technician_daily_summary(technician_id, date=None):
    """Get daily summary for a technician"""
    if not date:
        date = frappe.utils.today()
    
    time_logs = frappe.get_list("Labor Time Log",
                               filters={
                                   "technician": technician_id,
                                   "start_time": ["between", [f"{date} 00:00:00", f"{date} 23:59:59"]]
                               },
                               fields=["name", "service_order", "activity_type", 
                                     "status", "total_hours", "total_cost"])
    
    total_hours = sum(flt(log.total_hours or 0) for log in time_logs)
    total_revenue = sum(flt(log.total_cost or 0) for log in time_logs)
    
    return {
        "date": date,
        "technician": technician_id,
        "total_hours": total_hours,
        "total_revenue": total_revenue,
        "total_sessions": len(time_logs),
        "time_logs": time_logs
    } 