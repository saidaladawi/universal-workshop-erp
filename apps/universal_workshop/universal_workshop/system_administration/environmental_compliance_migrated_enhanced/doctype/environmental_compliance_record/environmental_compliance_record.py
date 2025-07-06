# -*- coding: utf-8 -*-
# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from datetime import datetime, timedelta
import re
import json
from typing import Dict, List, Optional


class EnvironmentalComplianceRecord(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields to Document class
    
    def validate(self):
        """Validate environmental compliance record before saving"""
        self.validate_compliance_type()
        self.validate_regulatory_requirements()
        self.validate_waste_information()
        self.validate_dates()
        self.validate_financial_amounts()
        self.calculate_total_compliance_cost()
        self.validate_oman_specific_requirements()
        
    def before_save(self):
        """Set default values and generate tracking information"""
        self.set_audit_trail()
        self.generate_tracking_number()
        self.generate_barcode()
        self.update_monitoring_schedule()
        self.validate_compliance_checklist()
        
    def on_submit(self):
        """Actions when compliance record is submitted"""
        self.create_follow_up_tasks()
        self.send_notifications()
        self.update_reference_documents()
        
    def validate_compliance_type(self):
        """Validate compliance type and set required fields"""
        if not self.compliance_type:
            frappe.throw(_("Compliance Type is required"))
            
        # Set required fields based on compliance type
        if self.compliance_type == "Vehicle Processing":
            if not self.reference_document:
                frappe.throw(_("Reference Document is required for Vehicle Processing compliance"))
                
        elif self.compliance_type == "Waste Disposal":
            if not self.waste_type:
                frappe.throw(_("Waste Type is required for Waste Disposal compliance"))
            if not self.disposal_method:
                frappe.throw(_("Disposal Method is required for Waste Disposal compliance"))
                
        elif self.compliance_type == "Hazardous Material":
            if not self.waste_type or self.waste_type != "Hazardous Waste":
                frappe.throw(_("Waste Type must be 'Hazardous Waste' for Hazardous Material compliance"))
            if not self.disposal_contractor:
                frappe.throw(_("Disposal Contractor is required for Hazardous Material compliance"))
                
    def validate_regulatory_requirements(self):
        """Validate regulatory authority and license information"""
        # Validate Oman regulatory authority
        if self.regulatory_authority and "Oman" not in self.regulatory_authority:
            frappe.msgprint(_("Warning: Regulatory Authority should be from Oman for local compliance"))
            
        # Validate license number format (if provided)
        if self.license_number:
            if not re.match(r'^[A-Z0-9\-]{5,20}$', self.license_number):
                frappe.throw(_("License Number format is invalid. Use alphanumeric characters and hyphens only."))
                
        # Validate permit number format (if provided)
        if self.permit_number:
            if not re.match(r'^[A-Z0-9\-]{5,20}$', self.permit_number):
                frappe.throw(_("Permit Number format is invalid. Use alphanumeric characters and hyphens only."))
                
    def validate_waste_information(self):
        """Validate waste type, quantity, and disposal information"""
        if self.waste_type and self.waste_quantity:
            # Validate waste quantity is positive
            if self.waste_quantity <= 0:
                frappe.throw(_("Waste Quantity must be greater than zero"))
                
            # Check for reasonable waste quantities
            if self.waste_quantity > 10000:  # 10 tons
                frappe.msgprint(_("Warning: Large waste quantity detected. Please verify the amount."))
                
        # Validate disposal contractor for hazardous waste
        if self.waste_type == "Hazardous Waste" and not self.disposal_contractor:
            frappe.throw(_("Disposal Contractor is required for Hazardous Waste"))
            
    def validate_dates(self):
        """Validate date fields and logical relationships"""
        today = datetime.now().date()
        
        # Validate compliance date
        if self.compliance_date:
            compliance_date = datetime.strptime(str(self.compliance_date), '%Y-%m-%d').date()
            if compliance_date > today + timedelta(days=365):
                frappe.throw(_("Compliance Date cannot be more than one year in the future"))
                
        # Validate due date
        if self.due_date:
            due_date = datetime.strptime(str(self.due_date), '%Y-%m-%d').date()
            if self.compliance_date and due_date < compliance_date:
                frappe.throw(_("Due Date cannot be before Compliance Date"))
                
    def validate_financial_amounts(self):
        """Validate financial amounts and currency"""
        financial_fields = ['compliance_cost', 'fine_amount', 'disposal_cost', 'certification_cost']
        
        for field in financial_fields:
            amount = getattr(self, field, 0)
            if amount and amount < 0:
                frappe.throw(_("{0} cannot be negative").format(self.meta.get_label(field)))
                
    def calculate_total_compliance_cost(self):
        """Calculate total compliance cost from individual components"""
        total = 0
        cost_components = [
            self.compliance_cost or 0,
            self.fine_amount or 0,
            self.disposal_cost or 0,
            self.certification_cost or 0
        ]
        
        total = sum(cost_components)
        self.total_compliance_cost = total
        
    def validate_oman_specific_requirements(self):
        """Validate Oman-specific regulatory requirements"""
        # Check industrial area compliance for vehicle processing
        if self.compliance_type == "Vehicle Processing":
            if not self.location_compliance:
                frappe.msgprint(_("Warning: Vehicle processing must be conducted in designated industrial areas as per Oman regulations"))
                
        # Validate GPS coordinates format (if provided)
        if self.gps_coordinates:
            # Simple validation for GPS coordinates format
            gps_pattern = r'^-?\d+\.?\d*,-?\d+\.?\d*$'
            if not re.match(gps_pattern, self.gps_coordinates):
                frappe.throw(_("GPS Coordinates format is invalid. Use format: latitude,longitude"))
                
    def set_audit_trail(self):
        """Set audit trail information"""
        current_user = frappe.session.user
        current_time = datetime.now()
        
        if self.is_new():
            self.created_by_user = current_user
            self.creation_timestamp = current_time
        
        self.last_modified_by = current_user
        self.last_modification_timestamp = current_time
        
    def generate_tracking_number(self):
        """Generate unique tracking number for compliance record"""
        if not self.tracking_number:
            # Format: ECR-YYYY-MM-NNNN
            current_date = datetime.now()
            year_month = current_date.strftime("%Y-%m")
            
            # Get the last tracking number for current month
            last_record = frappe.db.sql("""
                SELECT tracking_number FROM `tabEnvironmental Compliance Record`
                WHERE tracking_number LIKE 'ECR-{}-%%'
                ORDER BY creation DESC LIMIT 1
            """.format(year_month))
            
            if last_record:
                last_number = int(last_record[0][0].split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
                
            self.tracking_number = f"ECR-{year_month}-{new_number:04d}"
            
    def generate_barcode(self):
        """Generate barcode for tracking"""
        if self.tracking_number:
            self.barcode = self.tracking_number
            
    def update_monitoring_schedule(self):
        """Update monitoring schedule based on frequency"""
        if self.monitoring_frequency and self.compliance_date:
            compliance_date = datetime.strptime(str(self.compliance_date), '%Y-%m-%d').date()
            
            if self.monitoring_frequency == "Daily":
                self.next_monitoring_due = compliance_date + timedelta(days=1)
            elif self.monitoring_frequency == "Weekly":
                self.next_monitoring_due = compliance_date + timedelta(weeks=1)
            elif self.monitoring_frequency == "Monthly":
                self.next_monitoring_due = compliance_date + timedelta(days=30)
            elif self.monitoring_frequency == "Quarterly":
                self.next_monitoring_due = compliance_date + timedelta(days=90)
            elif self.monitoring_frequency == "Annually":
                self.next_monitoring_due = compliance_date + timedelta(days=365)
                
    def validate_compliance_checklist(self):
        """Validate compliance checklist requirements"""
        critical_checks = [
            'location_compliance',
            'license_valid',
            'documentation_complete'
        ]
        
        failed_checks = []
        for check in critical_checks:
            if not getattr(self, check, False):
                field_label = self.meta.get_label(check)
                failed_checks.append(field_label)
                
        if failed_checks and self.status == "Compliant":
            frappe.throw(_("Cannot mark as Compliant. Failed critical checks: {0}").format(", ".join(failed_checks)))
            
    def create_follow_up_tasks(self):
        """Create follow-up tasks based on compliance requirements"""
        if self.follow_up_required:
            # Create a ToDo for follow-up
            todo = frappe.new_doc("ToDo")
            todo.description = _("Follow-up required for Environmental Compliance Record: {0}").format(self.name)
            todo.reference_type = "Environmental Compliance Record"
            todo.reference_name = self.name
            todo.assigned_by = frappe.session.user
            todo.owner = self.created_by_user or frappe.session.user
            todo.priority = "Medium"
            if self.due_date:
                todo.date = self.due_date
            todo.insert(ignore_permissions=True)
            
    def send_notifications(self):
        """Send notifications to relevant users"""
        # Notify Environmental Officer
        environmental_officers = frappe.get_list("User", 
                                                filters={"role_profile_name": "Environmental Officer"},
                                                fields=["name", "email"])
        
        for officer in environmental_officers:
            frappe.sendmail(
                recipients=[officer.email],
                subject=_("Environmental Compliance Record Submitted: {0}").format(self.name),
                message=_("A new environmental compliance record has been submitted for review.<br><br>"
                         "Compliance Type: {0}<br>"
                         "Status: {1}<br>"
                         "Due Date: {2}<br><br>"
                         "Please review and take necessary action.").format(
                    self.compliance_type, self.status, self.due_date or "Not Set"
                )
            )
            
    def update_reference_documents(self):
        """Update reference documents with compliance information"""
        if self.reference_document and self.reference_doctype:
            try:
                ref_doc = frappe.get_doc(self.reference_doctype, self.reference_document)
                
                # Add compliance record reference
                if hasattr(ref_doc, 'environmental_compliance_records'):
                    # Check if this record is already linked
                    existing = False
                    for record in ref_doc.environmental_compliance_records:
                        if record.compliance_record == self.name:
                            existing = True
                            break
                    
                    if not existing:
                        ref_doc.append('environmental_compliance_records', {
                            'compliance_record': self.name,
                            'compliance_type': self.compliance_type,
                            'status': self.status,
                            'compliance_date': self.compliance_date
                        })
                        ref_doc.save(ignore_permissions=True)
                        
            except Exception as e:
                frappe.log_error(f"Failed to update reference document: {str(e)}")
                
    @frappe.whitelist()
    def get_compliance_summary(self):
        """Get compliance summary for dashboard"""
        return {
            'total_cost': self.total_compliance_cost or 0,
            'status': self.status,
            'compliance_percentage': self.calculate_compliance_percentage(),
            'next_due_date': self.next_monitoring_due or self.due_date,
            'critical_issues': self.get_critical_issues()
        }
        
    def calculate_compliance_percentage(self):
        """Calculate compliance percentage based on checklist"""
        checklist_fields = [
            'location_compliance',
            'license_valid',
            'documentation_complete',
            'waste_properly_segregated',
            'hazardous_materials_handled',
            'spill_containment_in_place',
            'pollution_prevention_active',
            'staff_trained'
        ]
        
        total_checks = len(checklist_fields)
        passed_checks = sum(1 for field in checklist_fields if getattr(self, field, False))
        
        return (passed_checks / total_checks) * 100 if total_checks > 0 else 0
        
    def get_critical_issues(self):
        """Get list of critical compliance issues"""
        issues = []
        
        if not self.location_compliance:
            issues.append(_("Location not compliant with industrial area requirements"))
            
        if not self.license_valid:
            issues.append(_("License not valid or expired"))
            
        if not self.documentation_complete:
            issues.append(_("Documentation incomplete"))
            
        if self.waste_type == "Hazardous Waste" and not self.hazardous_materials_handled:
            issues.append(_("Hazardous materials not properly handled"))
            
        return issues


# Utility functions for environmental compliance

@frappe.whitelist()
def get_compliance_dashboard_data():
    """Get dashboard data for environmental compliance"""
    
    # Get compliance statistics
    total_records = frappe.db.count("Environmental Compliance Record")
    compliant_records = frappe.db.count("Environmental Compliance Record", {"status": "Compliant"})
    overdue_records = frappe.db.count("Environmental Compliance Record", {"status": "Overdue"})
    
    # Get upcoming due dates
    upcoming_due = frappe.db.sql("""
        SELECT name, compliance_type, due_date, status
        FROM `tabEnvironmental Compliance Record`
        WHERE due_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
        AND status NOT IN ('Compliant', 'Closed')
        ORDER BY due_date
        LIMIT 10
    """, as_dict=True)
    
    # Get compliance by type
    compliance_by_type = frappe.db.sql("""
        SELECT compliance_type, COUNT(*) as count
        FROM `tabEnvironmental Compliance Record`
        GROUP BY compliance_type
        ORDER BY count DESC
    """, as_dict=True)
    
    return {
        'total_records': total_records,
        'compliant_records': compliant_records,
        'overdue_records': overdue_records,
        'compliance_rate': (compliant_records / total_records * 100) if total_records > 0 else 0,
        'upcoming_due': upcoming_due,
        'compliance_by_type': compliance_by_type
    }


@frappe.whitelist()
def create_compliance_record_from_scrap_vehicle(scrap_vehicle_id):
    """Create environmental compliance record from scrap vehicle"""
    
    scrap_vehicle = frappe.get_doc("Scrap Vehicle", scrap_vehicle_id)
    
    # Create compliance record
    compliance_record = frappe.new_doc("Environmental Compliance Record")
    compliance_record.compliance_type = "Vehicle Processing"
    compliance_record.reference_doctype = "Scrap Vehicle"
    compliance_record.reference_document = scrap_vehicle_id
    compliance_record.compliance_date = frappe.utils.today()
    compliance_record.due_date = frappe.utils.add_days(frappe.utils.today(), 30)
    compliance_record.status = "Draft"
    compliance_record.priority = "Medium"
    
    # Set default regulatory information
    compliance_record.regulatory_authority = "Ministry of Environment and Climate Affairs - Oman"
    compliance_record.monitoring_frequency = "Monthly"
    
    compliance_record.insert()
    
    return compliance_record.name


@frappe.whitelist()
def validate_environmental_compliance(doctype, docname):
    """Validate environmental compliance for any document"""
    
    # Check if there are any open compliance records
    open_compliance = frappe.db.exists("Environmental Compliance Record", {
        "reference_doctype": doctype,
        "reference_document": docname,
        "status": ["not in", ["Compliant", "Closed"]]
    })
    
    if open_compliance:
        frappe.throw(_("Cannot proceed. There are open environmental compliance records that must be resolved first."))
        
    return True
