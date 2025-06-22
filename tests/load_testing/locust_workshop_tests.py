"""
Locust Load Testing for Universal Workshop ERP
==============================================

This module provides comprehensive load testing scenarios for the Universal Workshop ERP system
using Locust, a modern event-driven load testing framework.

Usage:
    locust -f locust_workshop_tests.py --host=http://localhost:8000
    
Then open http://localhost:8089 for the web UI.
"""

import json
import random
import time
from datetime import datetime, timedelta
from locust import HttpUser, TaskSet, task, between
from locust.clients import HttpSession


class WorkshopTestData:
    """Test data generator for workshop scenarios"""
    
    ARABIC_NAMES = [
        "أحمد محمد السعيدي", "فاطمة علي البلوشي", "محمد سالم الشامسي",
        "خديجة يوسف الهنائي", "سعيد أحمد المقبالي", "مريم سالم الريامي"
    ]
    
    ENGLISH_NAMES = [
        "Ahmed Al-Saidi", "Fatima Al-Balushi", "Mohammed Al-Shamsi",
        "Khadija Al-Hinai", "Said Al-Maqbali", "Mariam Al-Riyami"
    ]
    
    VEHICLE_MAKES = ["Toyota", "Nissan", "Honda", "Hyundai", "Ford", "Chevrolet", "BMW", "Mercedes"]
    VEHICLE_MODELS = ["Camry", "Altima", "Civic", "Elantra", "Focus", "Cruze", "X3", "C-Class"]
    SERVICE_TYPES = [
        "Oil Change", "Brake Service", "Tire Rotation", "Engine Diagnostic",
        "AC Repair", "Battery Replacement", "Transmission Service", "General Inspection"
    ]
    
    @classmethod
    def generate_customer_data(cls):
        """Generate realistic customer data"""
        arabic_name = random.choice(cls.ARABIC_NAMES)
        english_name = random.choice(cls.ENGLISH_NAMES)
        
        return {
            "customer_name": english_name,
            "customer_name_arabic": arabic_name,
            "mobile_no": f"+968{random.randint(90000000, 99999999)}",
            "email": f"customer{random.randint(1000, 9999)}@example.com",
            "language": random.choice(["en", "ar"]),
            "customer_type": "Individual",
            "territory": "Oman"
        }
    
    @classmethod
    def generate_vehicle_data(cls, customer):
        """Generate realistic vehicle data"""
        return {
            "customer": customer,
            "make": random.choice(cls.VEHICLE_MAKES),
            "model": random.choice(cls.VEHICLE_MODELS),
            "year": random.randint(2015, 2024),
            "license_plate": f"OM-{random.randint(1000, 9999)}",
            "vin": f"VIN{random.randint(100000000000000, 999999999999999)}",
            "color": random.choice(["White", "Black", "Silver", "Blue", "Red"]),
            "mileage": random.randint(10000, 200000)
        }
    
    @classmethod
    def generate_appointment_data(cls, customer, vehicle):
        """Generate realistic appointment data"""
        appointment_date = datetime.now() + timedelta(days=random.randint(1, 30))
        
        return {
            "customer": customer,
            "vehicle": vehicle,
            "appointment_date": appointment_date.strftime("%Y-%m-%d"),
            "appointment_time": f"{random.randint(8, 17):02d}:00:00",
            "service_type": random.choice(cls.SERVICE_TYPES),
            "priority": random.choice(["Low", "Medium", "High"]),
            "description": f"Customer needs {random.choice(cls.SERVICE_TYPES).lower()}",
            "status": "Scheduled"
        }


class CustomerUserBehavior(TaskSet):
    """Simulate customer user behavior"""
    
    def on_start(self):
        """Initialize customer session"""
        self.customer_data = WorkshopTestData.generate_customer_data()
        self.vehicle_data = None
        self.appointment_data = None
        
        # Simulate login
        self.login()
    
    def login(self):
        """Simulate customer login"""
        response = self.client.post("/api/method/login", {
            "usr": self.customer_data["email"],
            "pwd": "password123"
        })
        
        if response.status_code == 200:
            self.client.cookies.update(response.cookies)
    
    @task(3)
    def register_customer(self):
        """Simulate customer registration"""
        response = self.client.post("/api/resource/Customer", 
                                   json=self.customer_data,
                                   headers={"Content-Type": "application/json"})
        
        if response.status_code in [200, 201]:
            response_data = response.json()
            if "data" in response_data:
                self.customer_data["name"] = response_data["data"]["name"]
    
    @task(2)
    def register_vehicle(self):
        """Simulate vehicle registration"""
        if not self.customer_data.get("name"):
            return
            
        self.vehicle_data = WorkshopTestData.generate_vehicle_data(
            self.customer_data["name"]
        )
        
        response = self.client.post("/api/resource/Vehicle",
                                   json=self.vehicle_data,
                                   headers={"Content-Type": "application/json"})
        
        if response.status_code in [200, 201]:
            response_data = response.json()
            if "data" in response_data:
                self.vehicle_data["name"] = response_data["data"]["name"]
    
    @task(4)
    def book_appointment(self):
        """Simulate appointment booking"""
        if not self.customer_data.get("name") or not self.vehicle_data:
            return
            
        self.appointment_data = WorkshopTestData.generate_appointment_data(
            self.customer_data["name"],
            self.vehicle_data.get("name", "")
        )
        
        response = self.client.post("/api/resource/Appointment",
                                   json=self.appointment_data,
                                   headers={"Content-Type": "application/json"})
    
    @task(2)
    def view_appointments(self):
        """Simulate viewing customer appointments"""
        if not self.customer_data.get("name"):
            return
            
        self.client.get(f"/api/resource/Appointment?filters=[['customer','=','{self.customer_data['name']}']]")
    
    @task(1)
    def view_service_history(self):
        """Simulate viewing service history"""
        if not self.vehicle_data or not self.vehicle_data.get("name"):
            return
            
        self.client.get(f"/api/resource/Service Order?filters=[['vehicle','=','{self.vehicle_data['name']}']]")


class TechnicianUserBehavior(TaskSet):
    """Simulate technician user behavior"""
    
    def on_start(self):
        """Initialize technician session"""
        self.login()
    
    def login(self):
        """Simulate technician login"""
        response = self.client.post("/api/method/login", {
            "usr": "technician@workshop.com",
            "pwd": "password123"
        })
        
        if response.status_code == 200:
            self.client.cookies.update(response.cookies)
    
    @task(3)
    def view_assigned_jobs(self):
        """Simulate viewing assigned service orders"""
        self.client.get("/api/resource/Service Order?filters=[['status','=','In Progress']]")
    
    @task(4)
    def update_job_status(self):
        """Simulate updating job status"""
        # Get a random service order
        response = self.client.get("/api/resource/Service Order?limit=1")
        if response.status_code == 200:
            data = response.json()
            if data.get("data") and len(data["data"]) > 0:
                service_order = data["data"][0]["name"]
                
                # Update status
                update_data = {
                    "status": random.choice(["In Progress", "Completed", "On Hold"]),
                    "technician_notes": f"Status updated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
                
                self.client.put(f"/api/resource/Service Order/{service_order}",
                               json=update_data,
                               headers={"Content-Type": "application/json"})
    
    @task(2)
    def add_parts_usage(self):
        """Simulate adding parts usage to service orders"""
        # This would typically involve creating Stock Entry records
        parts_data = {
            "item_code": f"PART-{random.randint(1000, 9999)}",
            "qty": random.randint(1, 5),
            "rate": random.uniform(10.0, 500.0)
        }
        
        response = self.client.post("/api/resource/Stock Entry",
                                   json=parts_data,
                                   headers={"Content-Type": "application/json"})
    
    @task(1)
    def generate_service_report(self):
        """Simulate generating service reports"""
        report_data = {
            "report_type": "Service Summary",
            "from_date": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
            "to_date": datetime.now().strftime("%Y-%m-%d")
        }
        
        self.client.post("/api/method/workshop.reports.service_summary",
                        json=report_data,
                        headers={"Content-Type": "application/json"})


class AdminUserBehavior(TaskSet):
    """Simulate administrator user behavior"""
    
    def on_start(self):
        """Initialize admin session"""
        self.login()
    
    def login(self):
        """Simulate admin login"""
        response = self.client.post("/api/method/login", {
            "usr": "admin@workshop.com",
            "pwd": "admin123"
        })
        
        if response.status_code == 200:
            self.client.cookies.update(response.cookies)
    
    @task(2)
    def generate_reports(self):
        """Simulate generating various reports"""
        reports = [
            "/api/method/workshop.reports.customer_report",
            "/api/method/workshop.reports.revenue_report",
            "/api/method/workshop.reports.service_performance",
            "/api/method/workshop.reports.inventory_status"
        ]
        
        report_endpoint = random.choice(reports)
        report_data = {
            "from_date": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
            "to_date": datetime.now().strftime("%Y-%m-%d")
        }
        
        self.client.post(report_endpoint,
                        json=report_data,
                        headers={"Content-Type": "application/json"})
    
    @task(3)
    def manage_inventory(self):
        """Simulate inventory management operations"""
        # View low stock items
        self.client.get("/api/resource/Item?filters=[['is_stock_item','=',1]]&fields=['name','item_name','stock_balance']")
        
        # Create purchase order for low stock items
        po_data = {
            "supplier": "Default Supplier",
            "items": [{
                "item_code": f"ITEM-{random.randint(1000, 9999)}",
                "qty": random.randint(10, 100),
                "rate": random.uniform(50.0, 1000.0)
            }]
        }
        
        self.client.post("/api/resource/Purchase Order",
                        json=po_data,
                        headers={"Content-Type": "application/json"})
    
    @task(1)
    def process_invoices(self):
        """Simulate invoice processing"""
        # Get pending invoices
        self.client.get("/api/resource/Sales Invoice?filters=[['status','=','Draft']]")
        
        # Create new invoice
        invoice_data = {
            "customer": f"CUST-{random.randint(1000, 9999)}",
            "items": [{
                "item_code": f"SERVICE-{random.randint(100, 999)}",
                "qty": 1,
                "rate": random.uniform(100.0, 1000.0)
            }],
            "taxes_and_charges": "VAT 5% - OM"
        }
        
        self.client.post("/api/resource/Sales Invoice",
                        json=invoice_data,
                        headers={"Content-Type": "application/json"})


class WorkshopCustomer(HttpUser):
    """Customer user type for load testing"""
    tasks = [CustomerUserBehavior]
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks
    weight = 60  # 60% of users will be customers


class WorkshopTechnician(HttpUser):
    """Technician user type for load testing"""
    tasks = [TechnicianUserBehavior]
    wait_time = between(2, 8)  # Wait 2-8 seconds between tasks
    weight = 30  # 30% of users will be technicians


class WorkshopAdmin(HttpUser):
    """Administrator user type for load testing"""
    tasks = [AdminUserBehavior]
    wait_time = between(5, 15)  # Wait 5-15 seconds between tasks
    weight = 10  # 10% of users will be administrators


# Configuration for different load testing scenarios
class LoadTestConfig:
    """Load testing configuration scenarios"""
    
    LIGHT_LOAD = {
        "users": 10,
        "spawn_rate": 2,
        "run_time": "5m"
    }
    
    MEDIUM_LOAD = {
        "users": 50,
        "spawn_rate": 5,
        "run_time": "15m"
    }
    
    HEAVY_LOAD = {
        "users": 200,
        "spawn_rate": 10,
        "run_time": "30m"
    }
    
    STRESS_TEST = {
        "users": 500,
        "spawn_rate": 20,
        "run_time": "60m"
    }


if __name__ == "__main__":
    print("Universal Workshop ERP Load Testing")
    print("==================================")
    print("Available scenarios:")
    print("- Light Load: 10 users, 5 minutes")
    print("- Medium Load: 50 users, 15 minutes")
    print("- Heavy Load: 200 users, 30 minutes")
    print("- Stress Test: 500 users, 60 minutes")
    print()
    print("Usage:")
    print("locust -f locust_workshop_tests.py --host=http://localhost:8000")
    print("Then open http://localhost:8089 for the web UI")
