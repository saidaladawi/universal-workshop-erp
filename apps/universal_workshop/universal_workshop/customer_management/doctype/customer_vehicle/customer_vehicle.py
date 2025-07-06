# Copyright (c) 2024, Universal Workshop and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now, getdate


class CustomerVehicle(Document):
    def before_insert(self):
        """Set default values before inserting"""
        if not self.registration_date:
            self.registration_date = getdate()
        
        if not self.created_date:
            self.created_date = getdate()
        
        if not self.is_active:
            self.is_active = 1
    
    def validate(self):
        """Validate the document"""
        self.validate_customer_and_vehicle()
        self.validate_primary_vehicle()
        self.validate_insurance_details()
    
    def validate_customer_and_vehicle(self):
        """Validate customer and vehicle exist"""
        if not frappe.db.exists("Customer", self.customer):
            frappe.throw(f"Customer {self.customer} does not exist")
        
        if not frappe.db.exists("Vehicle", self.vehicle):
            frappe.throw(f"Vehicle {self.vehicle} does not exist")
    
    def validate_primary_vehicle(self):
        """Ensure only one primary vehicle per customer"""
        if self.primary_vehicle:
            existing_primary = frappe.db.exists("Customer Vehicle", {
                "customer": self.customer,
                "primary_vehicle": 1,
                "name": ["!=", self.name],
                "is_active": 1
            })
            
            if existing_primary:
                frappe.throw("Customer already has a primary vehicle. Please uncheck the existing primary vehicle first.")
    
    def validate_insurance_details(self):
        """Validate insurance information"""
        if self.insurance_expiry and self.insurance_expiry < getdate():
            frappe.msgprint("Warning: Insurance has expired", alert=True)
        
        if self.insurance_policy_number and not self.insurance_provider:
            frappe.throw("Insurance Provider is required when Policy Number is specified")
    
    def on_update(self):
        """Actions to perform when document is updated"""
        self.update_vehicle_customer()
        self.update_last_service_date()
    
    def update_vehicle_customer(self):
        """Update vehicle's customer field if needed"""
        try:
            vehicle_doc = frappe.get_doc("Vehicle", self.vehicle)
            if vehicle_doc.customer != self.customer and self.relationship_type == "Owner":
                vehicle_doc.customer = self.customer
                vehicle_doc.save()
        except Exception:
            # Vehicle customer update not critical
            pass
    
    def update_last_service_date(self):
        """Update last service date from service orders"""
        if not self.last_service_date:
            last_service = frappe.db.get_value("Service Order", 
                {"customer": self.customer, "vehicle": self.vehicle, "status": "Completed"},
                "service_date",
                order_by="service_date desc"
            )
            if last_service:
                self.last_service_date = last_service
    
    @frappe.whitelist()
    def get_service_history(self):
        """Get service history for this customer-vehicle combination"""
        service_orders = frappe.get_all("Service Order",
            filters={
                "customer": self.customer,
                "vehicle": self.vehicle
            },
            fields=["name", "service_date", "status", "total_amount", "service_type"],
            order_by="service_date desc"
        )
        return service_orders
    
    @frappe.whitelist()
    def check_insurance_expiry(self):
        """Check insurance expiry and return warning if needed"""
        if not self.insurance_expiry:
            return {"status": "no_expiry", "message": "No insurance expiry date set"}
        
        from frappe.utils import date_diff
        days_to_expiry = date_diff(self.insurance_expiry, getdate())
        
        if days_to_expiry < 0:
            return {"status": "expired", "message": f"Insurance expired {abs(days_to_expiry)} days ago"}
        elif days_to_expiry <= 30:
            return {"status": "expiring", "message": f"Insurance expires in {days_to_expiry} days"}
        else:
            return {"status": "valid", "message": f"Insurance valid for {days_to_expiry} days"}
    
    @frappe.whitelist()
    def set_as_primary(self):
        """Set this vehicle as primary for the customer"""
        # Unset existing primary vehicle
        frappe.db.set_value("Customer Vehicle", 
            {"customer": self.customer, "primary_vehicle": 1, "name": ["!=", self.name]}, 
            "primary_vehicle", 0
        )
        
        # Set this as primary
        self.primary_vehicle = 1
        self.save()
        frappe.msgprint("Vehicle set as primary")


@frappe.whitelist()
def get_customer_vehicles(customer):
    """Get all active vehicles for a customer"""
    vehicles = frappe.get_all("Customer Vehicle",
        filters={"customer": customer, "is_active": 1},
        fields=["*"],
        order_by="primary_vehicle desc, created_date desc"
    )
    return vehicles


@frappe.whitelist()
def get_vehicle_customers(vehicle):
    """Get all customers associated with a vehicle"""
    customers = frappe.get_all("Customer Vehicle",
        filters={"vehicle": vehicle, "is_active": 1},
        fields=["customer", "relationship_type", "primary_vehicle"],
        order_by="primary_vehicle desc"
    )
    return customers


def check_insurance_expiry_reminders():
    """Daily job to check for insurance expiry reminders"""
    from frappe.utils import add_days
    
    expiring_soon = frappe.get_all("Customer Vehicle",
        filters={
            "insurance_expiry": ["between", [getdate(), add_days(getdate(), 30)]],
            "is_active": 1
        },
        fields=["name", "customer", "vehicle", "insurance_expiry", "insurance_provider"]
    )
    
    for record in expiring_soon:
        # This would integrate with notification system
        print(f"Insurance expiring for {record.customer} - {record.vehicle}")
    
    return len(expiring_soon)