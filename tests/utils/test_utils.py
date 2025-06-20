"""
Test utilities for Universal Workshop ERP System
Provides helper functions for test setup, data creation, and validation
"""

import frappe
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
import random
import string


class WorkshopTestUtils:
    """Utility class for workshop testing operations."""
    
    @staticmethod
    def load_test_fixtures():
        """Load test data from fixtures file."""
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "workshop_test_data.json"
        with open(fixtures_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @staticmethod
    def create_test_customer(language="en", customer_type="Individual"):
        """Create a test customer with random data."""
        if language == "ar":
            names = ["أحمد الراشد", "محمد الكندي", "فاطمة الزهراء", "سارة الهنائي"]
            domains = ["workshop.om", "garage.om", "auto.om"]
        else:
            names = ["Ahmed Al-Rashid", "Mohammed Al-Kindi", "Fatima Al-Zahra", "Sarah Al-Hinai"]
            domains = ["workshop.om", "motors.om", "auto.om"]
        
        name = random.choice(names)
        domain = random.choice(domains)
        random_id = ''.join(random.choices(string.digits, k=4))
        
        customer_data = {
            "doctype": "Customer",
            "customer_name": name + (f" Motors" if customer_type == "Company" else ""),
            "customer_group": "Commercial" if customer_type == "Company" else "Individual",
            "territory": "Oman",
            "customer_type": customer_type,
            "language": language,
            "mobile_no": f"+968 9{random_id[:3]} {random_id[3:]}",
            "email_id": f"test{random_id}@{domain}"
        }
        
        customer = frappe.get_doc(customer_data)
        customer.insert(ignore_permissions=True)
        frappe.db.commit()
        return customer
    
    @staticmethod
    def create_test_vehicle(customer_name, make="Toyota", model="Camry"):
        """Create a test vehicle for a customer."""
        random_id = ''.join(random.choices(string.digits, k=4))
        
        vehicle_data = {
            "doctype": "Vehicle",
            "customer": customer_name,
            "vin": f"1HGBH41JXMN10{random_id}",
            "license_plate": f"T-{random_id}",
            "make": make,
            "model": model,
            "year": random.choice([2020, 2021, 2022, 2023]),
            "color": random.choice(["White", "Black", "Silver", "Blue", "Red"]),
            "fuel_type": "Petrol",
            "engine_number": f"ENG{random_id}",
            "chassis_number": f"CHS{random_id}"
        }
        
        vehicle = frappe.get_doc(vehicle_data)
        vehicle.insert(ignore_permissions=True)
        frappe.db.commit()
        return vehicle
    
    @staticmethod
    def create_test_service_order(customer_name, vehicle_name, service_type="Oil Change"):
        """Create a test service order."""
        service_data = {
            "doctype": "Service Order",
            "customer": customer_name,
            "vehicle": vehicle_name,
            "service_type": service_type,
            "description": f"{service_type} service for vehicle",
            "estimated_duration": 60,
            "status": "Open",
            "priority": "Medium",
            "scheduled_date": datetime.now().date()
        }
        
        service_order = frappe.get_doc(service_data)
        service_order.insert(ignore_permissions=True)
        frappe.db.commit()
        return service_order
    
    @staticmethod
    def create_test_invoice(customer_name, service_order_name=None):
        """Create a test sales invoice."""
        invoice_data = {
            "doctype": "Sales Invoice",
            "customer": customer_name,
            "currency": "OMR",
            "language": "en",
            "items": [{
                "item_code": "SVC-TEST-001",
                "item_name": "Test Service",
                "description": "Test service description",
                "qty": 1,
                "rate": 50.0,
                "amount": 50.0
            }],
            "taxes_and_charges": "Oman VAT - UW"
        }
        
        if service_order_name:
            invoice_data["service_order"] = service_order_name
        
        invoice = frappe.get_doc(invoice_data)
        invoice.insert(ignore_permissions=True)
        frappe.db.commit()
        return invoice
    
    @staticmethod
    def create_test_appointment(customer_name, vehicle_name, scheduled_date=None):
        """Create a test appointment."""
        if not scheduled_date:
            scheduled_date = datetime.now().date() + timedelta(days=1)
        
        appointment_data = {
            "doctype": "Appointment",
            "customer": customer_name,
            "vehicle": vehicle_name,
            "service_type": "Oil Change",
            "scheduled_date": scheduled_date,
            "scheduled_time": "10:00:00",
            "estimated_duration": 60,
            "service_bay": "Bay-01",
            "status": "Scheduled"
        }
        
        appointment = frappe.get_doc(appointment_data)
        appointment.insert(ignore_permissions=True)
        frappe.db.commit()
        return appointment
    
    @staticmethod
    def setup_test_environment():
        """Setup basic test environment with required master data."""
        # Create test company if not exists
        if not frappe.db.exists("Company", "Universal Workshop"):
            company = frappe.get_doc({
                "doctype": "Company",
                "company_name": "Universal Workshop",
                "abbr": "UW",
                "default_currency": "OMR",
                "country": "Oman"
            })
            company.insert(ignore_permissions=True)
        
        # Create test customer groups
        for group in ["Individual", "Commercial"]:
            if not frappe.db.exists("Customer Group", group):
                customer_group = frappe.get_doc({
                    "doctype": "Customer Group",
                    "customer_group_name": group,
                    "is_group": 0
                })
                customer_group.insert(ignore_permissions=True)
        
        # Create test territory
        if not frappe.db.exists("Territory", "Oman"):
            territory = frappe.get_doc({
                "doctype": "Territory",
                "territory_name": "Oman",
                "is_group": 0
            })
            territory.insert(ignore_permissions=True)
        
        # Create test warehouses
        warehouses = ["Main Store - UW", "Parts Counter - UW", "Used Parts - UW"]
        for warehouse in warehouses:
            if not frappe.db.exists("Warehouse", warehouse):
                warehouse_doc = frappe.get_doc({
                    "doctype": "Warehouse",
                    "warehouse_name": warehouse,
                    "company": "Universal Workshop"
                })
                warehouse_doc.insert(ignore_permissions=True)
        
        # Create VAT tax template
        if not frappe.db.exists("Sales Taxes and Charges Template", "Oman VAT - UW"):
            tax_template = frappe.get_doc({
                "doctype": "Sales Taxes and Charges Template",
                "title": "Oman VAT - UW",
                "company": "Universal Workshop",
                "taxes": [{
                    "charge_type": "On Net Total",
                    "account_head": "VAT 5% - UW",
                    "description": "VAT @ 5%",
                    "rate": 5.0
                }]
            })
            tax_template.insert(ignore_permissions=True)
        
        frappe.db.commit()
    
    @staticmethod
    def cleanup_test_data(doc_names_by_doctype):
        """Clean up test data by doctype and names."""
        for doctype, names in doc_names_by_doctype.items():
            for name in names:
                try:
                    if frappe.db.exists(doctype, name):
                        frappe.delete_doc(doctype, name, force=True)
                except Exception as e:
                    print(f"Warning: Could not delete {doctype} {name}: {str(e)}")
        frappe.db.commit()
    
    @staticmethod
    def simulate_workflow_completion(service_order_name):
        """Simulate complete service order workflow."""
        service_order = frappe.get_doc("Service Order", service_order_name)
        
        # Start service
        service_order.status = "In Progress"
        service_order.actual_start_time = datetime.now()
        service_order.save()
        
        # Complete service  
        service_order.status = "Completed"
        service_order.actual_end_time = datetime.now()
        service_order.actual_duration = service_order.estimated_duration + random.randint(-10, 20)
        service_order.work_notes = "Service completed successfully during testing"
        service_order.save()
        
        frappe.db.commit()
        return service_order
    
    @staticmethod
    def validate_arabic_text_storage(text):
        """Validate that Arabic text is properly stored and retrieved."""
        # Check if text contains Arabic characters
        arabic_chars = any('\u0600' <= char <= '\u06FF' for char in text)
        if arabic_chars:
            # Verify proper encoding
            try:
                encoded = text.encode('utf-8')
                decoded = encoded.decode('utf-8')
                return decoded == text
            except UnicodeError:
                return False
        return True
    
    @staticmethod
    def generate_test_data_bulk(count=10):
        """Generate bulk test data for performance testing."""
        customers = []
        vehicles = []
        service_orders = []
        
        for i in range(count):
            # Create customer
            customer = WorkshopTestUtils.create_test_customer(
                language=random.choice(["en", "ar"]),
                customer_type=random.choice(["Individual", "Company"])
            )
            customers.append(customer)
            
            # Create 1-3 vehicles per customer
            vehicle_count = random.randint(1, 3)
            customer_vehicles = []
            
            for j in range(vehicle_count):
                make = random.choice(["Toyota", "Honda", "Nissan", "BMW", "Mercedes"])
                models = {
                    "Toyota": ["Camry", "Corolla", "Hilux"],
                    "Honda": ["Civic", "Accord", "CR-V"],
                    "Nissan": ["Altima", "Sentra", "Patrol"],
                    "BMW": ["3 Series", "X5", "5 Series"],
                    "Mercedes": ["C-Class", "E-Class", "GLC"]
                }
                model = random.choice(models[make])
                
                vehicle = WorkshopTestUtils.create_test_vehicle(
                    customer.name, make, model
                )
                vehicles.append(vehicle)
                customer_vehicles.append(vehicle)
            
            # Create 1-2 service orders per customer
            for vehicle in customer_vehicles[:2]:  # Max 2 service orders
                service_type = random.choice([
                    "Oil Change", "Brake Service", "Tire Rotation", "Engine Diagnostic"
                ])
                
                service_order = WorkshopTestUtils.create_test_service_order(
                    customer.name, vehicle.name, service_type
                )
                service_orders.append(service_order)
        
        return {
            "customers": customers,
            "vehicles": vehicles, 
            "service_orders": service_orders
        }
    
    @staticmethod
    def run_performance_test(operation_func, iterations=100):
        """Run performance test for a given operation."""
        import time
        
        start_time = time.time()
        results = []
        
        for i in range(iterations):
            iteration_start = time.time()
            result = operation_func()
            iteration_end = time.time()
            
            results.append({
                "iteration": i + 1,
                "duration": iteration_end - iteration_start,
                "result": result
            })
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        durations = [r["duration"] for r in results]
        avg_duration = sum(durations) / len(durations)
        min_duration = min(durations)
        max_duration = max(durations)
        
        return {
            "total_duration": total_duration,
            "average_duration": avg_duration,
            "min_duration": min_duration,
            "max_duration": max_duration,
            "iterations": iterations,
            "results": results
        }
    
    @staticmethod
    def validate_vat_calculation(invoice_name):
        """Validate VAT calculation on invoice."""
        invoice = frappe.get_doc("Sales Invoice", invoice_name)
        
        # Check if VAT is properly calculated
        net_total = invoice.net_total
        tax_amount = sum([tax.tax_amount for tax in invoice.taxes])
        expected_vat = net_total * 0.05  # 5% VAT
        
        # Allow for small rounding differences
        vat_difference = abs(tax_amount - expected_vat)
        return vat_difference < 0.01
    
    @staticmethod
    def create_sample_reports_data():
        """Create sample data for testing reports and analytics."""
        # Create data for last 30 days
        base_date = datetime.now().date()
        
        for i in range(30):
            test_date = base_date - timedelta(days=i)
            
            # Create 2-5 service orders per day
            daily_orders = random.randint(2, 5)
            
            for j in range(daily_orders):
                customer = WorkshopTestUtils.create_test_customer()
                vehicle = WorkshopTestUtils.create_test_vehicle(customer.name)
                
                service_order = frappe.get_doc({
                    "doctype": "Service Order",
                    "customer": customer.name,
                    "vehicle": vehicle.name,
                    "service_type": random.choice([
                        "Oil Change", "Brake Service", "Tire Rotation"
                    ]),
                    "status": "Completed",
                    "scheduled_date": test_date,
                    "actual_start_time": datetime.combine(test_date, datetime.min.time()),
                    "actual_end_time": datetime.combine(test_date, datetime.min.time()) + timedelta(hours=1),
                    "actual_duration": random.randint(30, 120)
                })
                service_order.insert(ignore_permissions=True)
        
        frappe.db.commit()


class MockDataGenerator:
    """Generate realistic mock data for testing."""
    
    @staticmethod
    def generate_oman_mobile_number():
        """Generate realistic Omani mobile number."""
        prefixes = ["9123", "9234", "9345", "9456", "9567"]
        prefix = random.choice(prefixes)
        suffix = ''.join(random.choices(string.digits, k=4))
        return f"+968 {prefix} {suffix}"
    
    @staticmethod
    def generate_arabic_name():
        """Generate realistic Arabic name."""
        first_names = ["أحمد", "محمد", "علي", "حسن", "عمر", "فاطمة", "عائشة", "خديجة", "مريم", "سارة"]
        last_names = ["الراشد", "الكندي", "الهنائي", "البلوشي", "الشامسي", "المعمري", "الزدجالي", "الحبسي"]
        
        first = random.choice(first_names)
        last = random.choice(last_names)
        return f"{first} {last}"
    
    @staticmethod
    def generate_english_name():
        """Generate realistic English name."""
        first_names = ["Ahmed", "Mohammed", "Ali", "Hassan", "Omar", "Fatima", "Aisha", "Khadija", "Mariam", "Sarah"]
        last_names = ["Al-Rashid", "Al-Kindi", "Al-Hinai", "Al-Balushi", "Al-Shamsi", "Al-Mamari", "Al-Zadjali", "Al-Habsi"]
        
        first = random.choice(first_names)
        last = random.choice(last_names)
        return f"{first} {last}"
    
    @staticmethod
    def generate_license_plate():
        """Generate realistic Omani license plate."""
        letters = random.choice(["A", "B", "C", "D", "E", "F", "G", "H"])
        numbers = ''.join(random.choices(string.digits, k=5))
        return f"{letters}-{numbers}"
    
    @staticmethod
    def generate_vin():
        """Generate realistic VIN number."""
        wmi_codes = ["1HG", "JM1", "WBA", "WDD", "KNA"]  # Honda, Mazda, BMW, Mercedes, Kia
        wmi = random.choice(wmi_codes)
        rest = ''.join(random.choices(string.ascii_uppercase + string.digits, k=14))
        return wmi + rest
