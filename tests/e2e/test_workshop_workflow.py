"""
End-to-End Integration Tests for Universal Workshop ERP System
Tests complete workflow from customer registration through service completion and billing
Supports both Arabic and English workflows with Omani VAT compliance
"""

import pytest
import frappe
import json
from datetime import datetime, timedelta
from tests.conftest import TestDataManager


class TestWorkshopE2EWorkflow:
    """Complete end-to-end workflow tests for automotive workshop operations."""
    
    @pytest.fixture(autouse=True)
    def setup(self, test_data_manager):
        """Setup test environment for each test."""
        self.data_manager = test_data_manager
        frappe.set_user("Administrator")
    
    def test_complete_workshop_workflow_english(self, test_customer_data, test_vehicle_data, test_service_data):
        """Test complete workflow in English: Customer → Vehicle → Service → Billing."""
        
        # Step 1: Create Customer
        customer = self.data_manager.create_doc("Customer", {
            "doctype": "Customer",
            **test_customer_data["english"]
        })
        
        assert customer.name
        assert customer.customer_name == test_customer_data["english"]["customer_name"]
        assert customer.language == "en"
        
        # Step 2: Register Vehicle
        vehicle = self.data_manager.create_doc("Vehicle", {
            "doctype": "Vehicle", 
            "customer": customer.name,
            **test_vehicle_data
        })
        
        assert vehicle.name
        assert vehicle.customer == customer.name
        assert vehicle.vin == test_vehicle_data["vin"]
        
        # Step 3: Create Service Order
        service_order = self.data_manager.create_doc("Service Order", {
            "doctype": "Service Order",
            "customer": customer.name,
            "vehicle": vehicle.name,
            "service_type": test_service_data["service_type"],
            "estimated_duration": test_service_data["estimated_duration"],
            "description": test_service_data["description"],
            "status": "Open",
            "priority": "Medium"
        })
        
        assert service_order.name
        assert service_order.customer == customer.name
        assert service_order.vehicle == vehicle.name
        assert service_order.status == "Open"
        
        # Step 4: Assign Technician and Start Work
        # Create a test technician first
        technician = self.data_manager.create_doc("Employee", {
            "doctype": "Employee",
            "employee_name": "Ahmed Al-Kindi",
            "first_name": "Ahmed", 
            "last_name": "Al-Kindi",
            "designation": "Senior Technician",
            "department": "Workshop",
            "status": "Active"
        })
        
        # Assign technician to service order
        service_order.assigned_technician = technician.name
        service_order.status = "In Progress"
        service_order.actual_start_time = datetime.now()
        service_order.save()
        
        assert service_order.assigned_technician == technician.name
        assert service_order.status == "In Progress"
        
        # Step 5: Complete Service
        service_order.status = "Completed"
        service_order.actual_end_time = datetime.now()
        service_order.actual_duration = 65  # minutes
        service_order.work_notes = "Oil change completed successfully. Used 5L synthetic oil."
        service_order.save()
        
        assert service_order.status == "Completed"
        assert service_order.work_notes
        
        # Step 6: Create Invoice with VAT (Oman compliance)
        sales_invoice = self.data_manager.create_doc("Sales Invoice", {
            "doctype": "Sales Invoice",
            "customer": customer.name,
            "service_order": service_order.name,
            "currency": "OMR",
            "language": "en",
            "items": [{
                "item_code": "OIL-CHANGE-SVC",
                "item_name": "Oil Change Service",
                "description": test_service_data["description"],
                "qty": 1,
                "rate": test_service_data["labor_cost"],
                "amount": test_service_data["labor_cost"]
            }],
            "taxes_and_charges": "Oman VAT - UW",
            "tax_category": "Standard VAT"
        })
        
        # Submit invoice
        sales_invoice.submit()
        
        assert sales_invoice.name
        assert sales_invoice.customer == customer.name
        assert sales_invoice.currency == "OMR"
        assert sales_invoice.docstatus == 1  # Submitted
        assert sales_invoice.grand_total > sales_invoice.net_total  # VAT applied
        
        # Step 7: Verify complete workflow integration
        # Check customer service history
        service_records = frappe.get_list("Service Order", 
            filters={"customer": customer.name}, 
            fields=["name", "status", "service_type"])
        
        assert len(service_records) == 1
        assert service_records[0]["status"] == "Completed"
        
        # Check vehicle service history  
        vehicle_services = frappe.get_list("Service Order",
            filters={"vehicle": vehicle.name},
            fields=["name", "service_type", "actual_duration"])
            
        assert len(vehicle_services) == 1
        assert vehicle_services[0]["actual_duration"] == 65
        
        # Check billing completion
        customer_invoices = frappe.get_list("Sales Invoice",
            filters={"customer": customer.name, "docstatus": 1},
            fields=["name", "grand_total", "outstanding_amount"])
            
        assert len(customer_invoices) == 1
        assert customer_invoices[0]["grand_total"] > 0
    
    def test_complete_workshop_workflow_arabic(self, test_customer_data, test_vehicle_data, test_service_data):
        """Test complete workflow in Arabic with RTL support."""
        
        # Step 1: Create Arabic Customer
        customer = self.data_manager.create_doc("Customer", {
            "doctype": "Customer",
            **test_customer_data["arabic"]
        })
        
        assert customer.name
        assert customer.customer_name == test_customer_data["arabic"]["customer_name"]
        assert customer.language == "ar"
        
        # Step 2: Register Vehicle (same as English but linked to Arabic customer)
        vehicle = self.data_manager.create_doc("Vehicle", {
            "doctype": "Vehicle",
            "customer": customer.name,
            **test_vehicle_data
        })
        
        assert vehicle.customer == customer.name
        
        # Step 3: Create Service Order with Arabic description
        service_order = self.data_manager.create_doc("Service Order", {
            "doctype": "Service Order", 
            "customer": customer.name,
            "vehicle": vehicle.name,
            "service_type": test_service_data["service_type"],
            "description": test_service_data["description_arabic"],
            "estimated_duration": test_service_data["estimated_duration"],
            "status": "Open",
            "priority": "Medium"
        })
        
        assert service_order.description == test_service_data["description_arabic"]
        
        # Step 4: Create Arabic Invoice
        sales_invoice = self.data_manager.create_doc("Sales Invoice", {
            "doctype": "Sales Invoice",
            "customer": customer.name,
            "service_order": service_order.name,
            "currency": "OMR", 
            "language": "ar",
            "items": [{
                "item_code": "OIL-CHANGE-SVC",
                "item_name": "خدمة تغيير الزيت",
                "description": test_service_data["description_arabic"],
                "qty": 1,
                "rate": test_service_data["labor_cost"],
                "amount": test_service_data["labor_cost"]
            }],
            "taxes_and_charges": "Oman VAT - UW"
        })
        
        sales_invoice.submit()
        
        assert sales_invoice.language == "ar"
        assert sales_invoice.items[0].item_name == "خدمة تغيير الزيت"
        assert sales_invoice.docstatus == 1
    
    def test_multi_service_workflow(self, test_customer_data, test_vehicle_data):
        """Test handling multiple concurrent services for same customer."""
        
        customer = self.data_manager.create_doc("Customer", {
            "doctype": "Customer",
            **test_customer_data["english"]
        })
        
        vehicle = self.data_manager.create_doc("Vehicle", {
            "doctype": "Vehicle",
            "customer": customer.name,
            **test_vehicle_data
        })
        
        # Create multiple service orders
        services = [
            {"service_type": "Oil Change", "description": "Engine oil change", "priority": "Medium"},
            {"service_type": "Brake Service", "description": "Brake pad replacement", "priority": "High"},
            {"service_type": "Tire Rotation", "description": "Rotate all four tires", "priority": "Low"}
        ]
        
        service_orders = []
        for service_data in services:
            service_order = self.data_manager.create_doc("Service Order", {
                "doctype": "Service Order",
                "customer": customer.name,
                "vehicle": vehicle.name,
                **service_data,
                "status": "Open"
            })
            service_orders.append(service_order)
        
        assert len(service_orders) == 3
        
        # Verify priority ordering works
        high_priority = [so for so in service_orders if so.priority == "High"]
        assert len(high_priority) == 1
        assert high_priority[0].service_type == "Brake Service"
    
    def test_inventory_integration_workflow(self, test_customer_data, test_vehicle_data):
        """Test service workflow with parts inventory integration."""
        
        customer = self.data_manager.create_doc("Customer", {
            "doctype": "Customer", 
            **test_customer_data["english"]
        })
        
        vehicle = self.data_manager.create_doc("Vehicle", {
            "doctype": "Vehicle",
            "customer": customer.name,
            **test_vehicle_data
        })
        
        # Create inventory item
        oil_filter = self.data_manager.create_doc("Item", {
            "doctype": "Item",
            "item_code": "OIL-FILTER-TOY-CAM",
            "item_name": "Toyota Camry Oil Filter",
            "item_group": "Auto Parts",
            "stock_uom": "Nos",
            "is_stock_item": 1,
            "valuation_rate": 8.5  # OMR
        })
        
        # Create stock entry
        stock_entry = self.data_manager.create_doc("Stock Entry", {
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Receipt",
            "items": [{
                "item_code": oil_filter.item_code,
                "qty": 10,
                "basic_rate": 8.5,
                "t_warehouse": "Stores - UW"
            }]
        })
        stock_entry.submit()
        
        # Create service order that uses parts
        service_order = self.data_manager.create_doc("Service Order", {
            "doctype": "Service Order",
            "customer": customer.name,
            "vehicle": vehicle.name,
            "service_type": "Oil Change",
            "description": "Full oil change with filter",
            "status": "In Progress",
            "parts_required": [{
                "item_code": oil_filter.item_code,
                "qty": 1,
                "rate": 8.5
            }]
        })
        
        # Complete service and issue parts
        parts_issue = self.data_manager.create_doc("Stock Entry", {
            "doctype": "Stock Entry", 
            "stock_entry_type": "Material Issue",
            "service_order": service_order.name,
            "items": [{
                "item_code": oil_filter.item_code,
                "qty": 1,
                "s_warehouse": "Stores - UW"
            }]
        })
        parts_issue.submit()
        
        service_order.status = "Completed"
        service_order.save()
        
        # Verify inventory was properly consumed
        stock_balance = frappe.get_value("Bin", 
            {"item_code": oil_filter.item_code, "warehouse": "Stores - UW"}, 
            "actual_qty")
        
        assert stock_balance == 9  # 10 - 1 used
    
    def test_appointment_scheduling_workflow(self, test_customer_data, test_vehicle_data):
        """Test appointment scheduling and service bay management."""
        
        customer = self.data_manager.create_doc("Customer", {
            "doctype": "Customer",
            **test_customer_data["english"] 
        })
        
        vehicle = self.data_manager.create_doc("Vehicle", {
            "doctype": "Vehicle",
            "customer": customer.name,
            **test_vehicle_data
        })
        
        # Create appointment
        appointment = self.data_manager.create_doc("Appointment", {
            "doctype": "Appointment",
            "customer": customer.name,
            "vehicle": vehicle.name,
            "service_type": "Oil Change",
            "scheduled_date": datetime.now().date(),
            "scheduled_time": "09:00:00",
            "estimated_duration": 60,
            "service_bay": "Bay-01",
            "status": "Scheduled"
        })
        
        assert appointment.name
        assert appointment.status == "Scheduled"
        
        # Convert appointment to service order
        service_order = self.data_manager.create_doc("Service Order", {
            "doctype": "Service Order",
            "appointment": appointment.name,
            "customer": customer.name, 
            "vehicle": vehicle.name,
            "service_type": appointment.service_type,
            "scheduled_date": appointment.scheduled_date,
            "service_bay": appointment.service_bay,
            "status": "Scheduled"
        })
        
        # Update appointment status
        appointment.status = "Confirmed"
        appointment.service_order = service_order.name
        appointment.save()
        
        assert appointment.service_order == service_order.name
        assert service_order.appointment == appointment.name
    
    def test_error_handling_and_rollback(self, test_customer_data, test_vehicle_data):
        """Test error handling and transaction rollback scenarios."""
        
        customer = self.data_manager.create_doc("Customer", {
            "doctype": "Customer",
            **test_customer_data["english"]
        })
        
        # Test invalid vehicle data
        with pytest.raises(Exception):
            invalid_vehicle = frappe.get_doc({
                "doctype": "Vehicle",
                "customer": customer.name,
                "vin": "",  # Invalid empty VIN
                "license_plate": test_vehicle_data["license_plate"]
            })
            invalid_vehicle.insert()
        
        # Test duplicate customer email
        with pytest.raises(Exception):
            duplicate_customer = frappe.get_doc({
                "doctype": "Customer",
                "customer_name": "Different Name",
                "email_id": test_customer_data["english"]["email_id"]  # Same email
            })
            duplicate_customer.insert()
        
        # Verify original customer still exists
        assert frappe.db.exists("Customer", customer.name)
    
    def test_arabic_unicode_handling(self, test_customer_data):
        """Test proper Unicode handling for Arabic text throughout the system."""
        
        # Create customer with Arabic data
        customer = self.data_manager.create_doc("Customer", {
            "doctype": "Customer",
            **test_customer_data["arabic"]
        })
        
        # Verify Arabic text is properly stored and retrieved
        retrieved_customer = frappe.get_doc("Customer", customer.name)
        assert retrieved_customer.customer_name == test_customer_data["arabic"]["customer_name"]
        
        # Test search functionality with Arabic text
        search_results = frappe.get_list("Customer", 
            filters={"customer_name": ["like", "%أحمد%"]},
            fields=["name", "customer_name"])
        
        assert len(search_results) >= 1
        arabic_customers = [c for c in search_results if "أحمد" in c.customer_name]
        assert len(arabic_customers) >= 1
        
        # Test Arabic text in service descriptions
        service_order = self.data_manager.create_doc("Service Order", {
            "doctype": "Service Order", 
            "customer": customer.name,
            "service_type": "Oil Change",
            "description": "تغيير زيت المحرك والفلتر مع فحص شامل للسيارة",
            "status": "Open"
        })
        
        assert "تغيير زيت" in service_order.description
        
    def test_performance_with_large_dataset(self, test_customer_data, test_vehicle_data):
        """Test system performance with larger dataset simulation."""
        
        # Create multiple customers and vehicles to simulate load
        customers = []
        for i in range(5):
            customer_data = test_customer_data["english"].copy()
            customer_data["customer_name"] = f"Test Customer {i}"
            customer_data["email_id"] = f"customer{i}@test.com"
            
            customer = self.data_manager.create_doc("Customer", {
                "doctype": "Customer",
                **customer_data
            })
            customers.append(customer)
        
        # Create vehicles for each customer
        vehicles = []
        for i, customer in enumerate(customers):
            vehicle_data = test_vehicle_data.copy()
            vehicle_data["vin"] = f"1HGBH41JXMN10918{i}"
            vehicle_data["license_plate"] = f"A-1234{i}"
            
            vehicle = self.data_manager.create_doc("Vehicle", {
                "doctype": "Vehicle",
                "customer": customer.name,
                **vehicle_data
            })
            vehicles.append(vehicle)
        
        # Create service orders for load testing
        service_orders = []
        for vehicle in vehicles:
            service_order = self.data_manager.create_doc("Service Order", {
                "doctype": "Service Order",
                "customer": vehicle.customer,
                "vehicle": vehicle.name,
                "service_type": "Oil Change",
                "status": "Open"
            })
            service_orders.append(service_order)
        
        assert len(service_orders) == 5
        
        # Test bulk operations performance
        start_time = datetime.now()
        
        # Simulate concurrent status updates
        for so in service_orders:
            so.status = "In Progress"
            so.save()
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # Assert reasonable performance (should complete within 5 seconds)
        assert processing_time < 5.0, f"Bulk updates took too long: {processing_time} seconds"
