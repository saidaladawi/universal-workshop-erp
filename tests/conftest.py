import pytest
import frappe
import os
import json
from pathlib import Path

# Test Configuration for Universal Workshop ERP System
# Supporting Arabic/English dual language testing

TEST_USER = "test@workshop.local"
TEST_ADMIN = "Administrator"
TEST_PASSWORD = "test123"

# Test site configuration
TEST_SITE = "universal.local"

def pytest_configure(config):
    """Setup test environment configuration."""
    try:
        # Initialize Frappe if not already done
        if not hasattr(frappe, 'db') or not frappe.db:
            import os
            os.environ['FRAPPE_SITE'] = TEST_SITE
            frappe.init(site=TEST_SITE)
            frappe.connect()
        
        # Set test user if database is available
        if frappe.db and not frappe.db.exists("User", TEST_USER):
            user = frappe.get_doc({
                "doctype": "User",
                "email": TEST_USER,
                "first_name": "Test",
                "last_name": "User",
                "new_password": TEST_PASSWORD,
                "language": "en",
                "roles": [
                    {"role": "Workshop Manager"},
                    {"role": "System Manager"}
                ]
            })
            user.insert(ignore_permissions=True)
            frappe.db.commit()
    except Exception as e:
        print(f"Warning: Could not fully initialize Frappe environment: {str(e)}")

def pytest_unconfigure(config):
    """Cleanup after tests."""
    try:
        if hasattr(frappe, 'destroy') and callable(frappe.destroy):
            frappe.destroy()
    except Exception as e:
        print(f"Warning: Could not cleanup Frappe environment: {str(e)}")

@pytest.fixture(scope="session")
def test_site():
    """Fixture to ensure test site is available."""
    return TEST_SITE

@pytest.fixture(scope="session")
def test_user():
    """Fixture to provide test user credentials."""
    return {"email": TEST_USER, "password": TEST_PASSWORD}

@pytest.fixture(scope="session")
def admin_user():
    """Fixture to provide admin user credentials."""
    return {"email": TEST_ADMIN, "password": "admin"}

@pytest.fixture(scope="function")
def clean_db():
    """Fixture to provide clean database state for each test."""
    # Backup current state
    frappe.db.begin()
    yield
    # Rollback changes
    frappe.db.rollback()

@pytest.fixture(scope="function")
def test_customer_data():
    """Fixture providing test customer data for both Arabic and English."""
    return {
        "english": {
            "customer_name": "Ahmed Al-Rashid Motors",
            "customer_group": "Commercial", 
            "territory": "Oman",
            "customer_type": "Company",
            "language": "en",
            "mobile_no": "+968 9123 4567",
            "email_id": "ahmed@alrashidmotors.om"
        },
        "arabic": {
            "customer_name": "ورشة أحمد الراشد للسيارات",
            "customer_name_arabic": "ورشة أحمد الراشد للسيارات", 
            "customer_group": "Commercial",
            "territory": "Oman",
            "customer_type": "Company",
            "language": "ar",
            "mobile_no": "+968 9123 4567",
            "email_id": "ahmed@alrashidmotors.om"
        }
    }

@pytest.fixture(scope="function")
def test_vehicle_data():
    """Fixture providing test vehicle data."""
    return {
        "vin": "1HGBH41JXMN109186",
        "license_plate": "A-12345", 
        "make": "Toyota",
        "model": "Camry",
        "year": 2023,
        "color": "White",
        "fuel_type": "Petrol",
        "engine_number": "ENG123456"
    }

@pytest.fixture(scope="function") 
def test_service_data():
    """Fixture providing test service data."""
    return {
        "service_type": "Oil Change",
        "service_category": "Maintenance",
        "estimated_duration": 60,  # minutes
        "labor_cost": 25.0,  # OMR
        "description": "Engine oil and filter change",
        "description_arabic": "تغيير زيت المحرك والفلتر"
    }

class TestDataManager:
    """Utility class for managing test data lifecycle."""
    
    def __init__(self):
        self.created_docs = []
    
    def create_doc(self, doctype, data, commit=True):
        """Create a document and track it for cleanup."""
        doc = frappe.get_doc(data)
        doc.doctype = doctype
        doc.insert(ignore_permissions=True)
        if commit:
            frappe.db.commit()
        
        self.created_docs.append((doctype, doc.name))
        return doc
    
    def cleanup(self):
        """Clean up all created test documents."""
        for doctype, name in reversed(self.created_docs):
            try:
                if frappe.db.exists(doctype, name):
                    frappe.delete_doc(doctype, name, force=True)
            except Exception as e:
                print(f"Warning: Could not delete {doctype} {name}: {str(e)}")
        
        frappe.db.commit()
        self.created_docs = []

@pytest.fixture(scope="function")
def test_data_manager():
    """Fixture providing test data manager for document lifecycle."""
    manager = TestDataManager()
    yield manager
    manager.cleanup()
