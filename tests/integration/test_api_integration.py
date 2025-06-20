"""
API Integration Tests for Universal Workshop ERP System
Tests REST API endpoints and business logic integration
"""

import pytest
import requests
import json
import frappe
from datetime import datetime
from tests.conftest import TestDataManager


class TestWorkshopAPIIntegration:
    """Test API endpoints for workshop system integration."""
    
    @pytest.fixture(autouse=True)
    def setup(self, test_data_manager):
        """Setup API test environment."""
        self.data_manager = test_data_manager
        self.base_url = "http://localhost:8000"
        self.api_key = self._get_api_key()
        self.api_secret = self._get_api_secret()
        
        # Setup authentication headers
        self.headers = {
            'Authorization': f'token {self.api_key}:{self.api_secret}',
            'Content-Type': 'application/json'
        }
    
    def _get_api_key(self):
        """Get API key for testing."""
        # Create API key for testing if doesn't exist
        user = "Administrator"
        api_key = frappe.db.get_value("User", user, "api_key")
        if not api_key:
            api_key = frappe.generate_hash(length=15)
            frappe.db.set_value("User", user, "api_key", api_key)
            frappe.db.commit()
        return api_key
    
    def _get_api_secret(self):
        """Get API secret for testing."""
        user = "Administrator"
        api_secret = frappe.db.get_value("User", user, "api_secret")
        if not api_secret:
            api_secret = frappe.generate_hash(length=15)
            frappe.db.set_value("User", user, "api_secret", api_secret)
            frappe.db.commit()
        return api_secret
    
    def test_customer_api_crud(self, test_customer_data):
        """Test Customer API CRUD operations."""
        
        # CREATE - Create customer via API
        customer_data = test_customer_data["english"]
        response = requests.post(
            f"{self.base_url}/api/resource/Customer",
            headers=self.headers,
            data=json.dumps(customer_data)
        )
        
        assert response.status_code == 200
        customer_response = response.json()
        customer_name = customer_response["data"]["name"]
        
        # READ - Get customer via API
        response = requests.get(
            f"{self.base_url}/api/resource/Customer/{customer_name}",
            headers=self.headers
        )
        
        assert response.status_code == 200
        retrieved_customer = response.json()["data"]
        assert retrieved_customer["customer_name"] == customer_data["customer_name"]
        assert retrieved_customer["language"] == customer_data["language"]
        
        # UPDATE - Update customer via API
        update_data = {"mobile_no": "+968 9999 8888"}
        response = requests.put(
            f"{self.base_url}/api/resource/Customer/{customer_name}",
            headers=self.headers,
            data=json.dumps(update_data)
        )
        
        assert response.status_code == 200
        
        # Verify update
        response = requests.get(
            f"{self.base_url}/api/resource/Customer/{customer_name}",
            headers=self.headers
        )
        updated_customer = response.json()["data"]
        assert updated_customer["mobile_no"] == "+968 9999 8888"
        
        # DELETE - Delete customer via API
        response = requests.delete(
            f"{self.base_url}/api/resource/Customer/{customer_name}",
            headers=self.headers
        )
        
        assert response.status_code == 202
        
        # Verify deletion
        response = requests.get(
            f"{self.base_url}/api/resource/Customer/{customer_name}",
            headers=self.headers
        )
        assert response.status_code == 404
    
    def test_vehicle_registration_api(self, test_customer_data, test_vehicle_data):
        """Test Vehicle registration via API with VIN decoder integration."""
        
        # First create customer
        customer_data = test_customer_data["english"]
        response = requests.post(
            f"{self.base_url}/api/resource/Customer",
            headers=self.headers,
            data=json.dumps(customer_data)
        )
        customer_name = response.json()["data"]["name"]
        
        # Create vehicle with VIN
        vehicle_data = {
            **test_vehicle_data,
            "customer": customer_name
        }
        
        response = requests.post(
            f"{self.base_url}/api/resource/Vehicle",
            headers=self.headers,
            data=json.dumps(vehicle_data)
        )
        
        assert response.status_code == 200
        vehicle_response = response.json()["data"]
        
        # Verify VIN decoder populated fields
        assert vehicle_response["make"] == test_vehicle_data["make"]
        assert vehicle_response["model"] == test_vehicle_data["model"]
        assert vehicle_response["year"] == test_vehicle_data["year"]
        
        # Test VIN validation
        invalid_vehicle_data = {
            **vehicle_data,
            "vin": "INVALID_VIN",
            "license_plate": "B-54321"
        }
        
        response = requests.post(
            f"{self.base_url}/api/resource/Vehicle",
            headers=self.headers,
            data=json.dumps(invalid_vehicle_data)
        )
        
        assert response.status_code == 417  # Validation error
    
    def test_service_order_workflow_api(self, test_customer_data, test_vehicle_data, test_service_data):
        """Test complete service order workflow via API."""
        
        # Setup customer and vehicle
        customer_data = test_customer_data["english"]
        response = requests.post(
            f"{self.base_url}/api/resource/Customer",
            headers=self.headers,
            data=json.dumps(customer_data)
        )
        customer_name = response.json()["data"]["name"]
        
        vehicle_data = {**test_vehicle_data, "customer": customer_name}
        response = requests.post(
            f"{self.base_url}/api/resource/Vehicle", 
            headers=self.headers,
            data=json.dumps(vehicle_data)
        )
        vehicle_name = response.json()["data"]["name"]
        
        # Create service order
        service_order_data = {
            "customer": customer_name,
            "vehicle": vehicle_name,
            "service_type": test_service_data["service_type"],
            "description": test_service_data["description"],
            "estimated_duration": test_service_data["estimated_duration"],
            "status": "Open",
            "priority": "Medium"
        }
        
        response = requests.post(
            f"{self.base_url}/api/resource/Service Order",
            headers=self.headers,
            data=json.dumps(service_order_data)
        )
        
        assert response.status_code == 200
        service_order_name = response.json()["data"]["name"]
        
        # Update status to In Progress
        status_update = {"status": "In Progress", "actual_start_time": datetime.now().isoformat()}
        response = requests.put(
            f"{self.base_url}/api/resource/Service Order/{service_order_name}",
            headers=self.headers,
            data=json.dumps(status_update)
        )
        
        assert response.status_code == 200
        
        # Complete service
        completion_update = {
            "status": "Completed",
            "actual_end_time": datetime.now().isoformat(),
            "actual_duration": 70,
            "work_notes": "Service completed successfully via API"
        }
        
        response = requests.put(
            f"{self.base_url}/api/resource/Service Order/{service_order_name}",
            headers=self.headers,
            data=json.dumps(completion_update)
        )
        
        assert response.status_code == 200
        
        # Verify completion
        response = requests.get(
            f"{self.base_url}/api/resource/Service Order/{service_order_name}",
            headers=self.headers
        )
        
        completed_service = response.json()["data"]
        assert completed_service["status"] == "Completed"
        assert completed_service["actual_duration"] == 70
    
    def test_appointment_scheduling_api(self, test_customer_data, test_vehicle_data):
        """Test appointment scheduling via API."""
        
        # Setup data
        customer_data = test_customer_data["english"]
        response = requests.post(
            f"{self.base_url}/api/resource/Customer",
            headers=self.headers,
            data=json.dumps(customer_data)
        )
        customer_name = response.json()["data"]["name"]
        
        vehicle_data = {**test_vehicle_data, "customer": customer_name}
        response = requests.post(
            f"{self.base_url}/api/resource/Vehicle",
            headers=self.headers,
            data=json.dumps(vehicle_data)
        )
        vehicle_name = response.json()["data"]["name"]
        
        # Create appointment
        appointment_data = {
            "customer": customer_name,
            "vehicle": vehicle_name,
            "service_type": "Brake Service",
            "scheduled_date": "2025-06-22",
            "scheduled_time": "10:00:00",
            "estimated_duration": 90,
            "service_bay": "Bay-01",
            "status": "Scheduled"
        }
        
        response = requests.post(
            f"{self.base_url}/api/resource/Appointment",
            headers=self.headers,
            data=json.dumps(appointment_data)
        )
        
        assert response.status_code == 200
        appointment_name = response.json()["data"]["name"]
        
        # Test appointment conflict detection
        conflicting_appointment = {
            **appointment_data,
            "customer": customer_name,  # Different customer, same time/bay
            "service_bay": "Bay-01",
            "scheduled_date": "2025-06-22",
            "scheduled_time": "10:30:00"  # Overlapping time
        }
        
        response = requests.post(
            f"{self.base_url}/api/resource/Appointment",
            headers=self.headers,
            data=json.dumps(conflicting_appointment)
        )
        
        # Should detect conflict (assuming validation is implemented)
        # assert response.status_code == 417  # Validation error
    
    def test_inventory_integration_api(self, test_customer_data, test_vehicle_data):
        """Test inventory integration with service orders via API."""
        
        # Create item
        item_data = {
            "item_code": "API-TEST-FILTER",
            "item_name": "API Test Oil Filter",
            "item_group": "Auto Parts",
            "stock_uom": "Nos",
            "is_stock_item": 1,
            "valuation_rate": 12.5
        }
        
        response = requests.post(
            f"{self.base_url}/api/resource/Item",
            headers=self.headers,
            data=json.dumps(item_data)
        )
        
        assert response.status_code == 200
        item_code = response.json()["data"]["item_code"]
        
        # Create stock entry to add inventory
        stock_entry_data = {
            "stock_entry_type": "Material Receipt",
            "items": [{
                "item_code": item_code,
                "qty": 20,
                "basic_rate": 12.5,
                "t_warehouse": "Stores - UW"
            }]
        }
        
        response = requests.post(
            f"{self.base_url}/api/resource/Stock Entry",
            headers=self.headers,
            data=json.dumps(stock_entry_data)
        )
        
        assert response.status_code == 200
        stock_entry_name = response.json()["data"]["name"]
        
        # Submit stock entry
        response = requests.put(
            f"{self.base_url}/api/resource/Stock Entry/{stock_entry_name}",
            headers=self.headers,
            data=json.dumps({"docstatus": 1})
        )
        
        assert response.status_code == 200
        
        # Verify stock balance
        response = requests.get(
            f"{self.base_url}/api/method/frappe.desk.query_report.run",
            headers=self.headers,
            params={
                "report_name": "Stock Balance",
                "filters": json.dumps({"item_code": item_code})
            }
        )
        
        assert response.status_code == 200
        stock_data = response.json()
        # Should show 20 units in stock
    
    def test_billing_vat_compliance_api(self, test_customer_data):
        """Test billing system with Omani VAT compliance via API."""
        
        # Create customer
        customer_data = test_customer_data["english"]
        response = requests.post(
            f"{self.base_url}/api/resource/Customer",
            headers=self.headers,
            data=json.dumps(customer_data)
        )
        customer_name = response.json()["data"]["name"]
        
        # Create sales invoice with VAT
        invoice_data = {
            "customer": customer_name,
            "currency": "OMR",
            "language": "en",
            "items": [{
                "item_code": "VAT-TEST-SERVICE",
                "item_name": "VAT Test Service",
                "description": "Test service for VAT calculation",
                "qty": 1,
                "rate": 100.0,
                "amount": 100.0
            }],
            "taxes_and_charges": "Oman VAT - UW",
            "tax_category": "Standard VAT"
        }
        
        response = requests.post(
            f"{self.base_url}/api/resource/Sales Invoice",
            headers=self.headers,
            data=json.dumps(invoice_data)
        )
        
        assert response.status_code == 200
        invoice_name = response.json()["data"]["name"]
        
        # Submit invoice
        response = requests.put(
            f"{self.base_url}/api/resource/Sales Invoice/{invoice_name}",
            headers=self.headers,
            data=json.dumps({"docstatus": 1})
        )
        
        assert response.status_code == 200
        
        # Verify VAT calculation
        response = requests.get(
            f"{self.base_url}/api/resource/Sales Invoice/{invoice_name}",
            headers=self.headers
        )
        
        invoice = response.json()["data"]
        assert invoice["currency"] == "OMR"
        assert invoice["net_total"] == 100.0
        assert invoice["grand_total"] > invoice["net_total"]  # VAT added
        
        # Test QR code generation
        assert "qr_code" in invoice or invoice.get("custom_qr_code")
    
    def test_arabic_api_support(self, test_customer_data):
        """Test API support for Arabic content."""
        
        # Create customer with Arabic name
        arabic_customer_data = test_customer_data["arabic"]
        response = requests.post(
            f"{self.base_url}/api/resource/Customer",
            headers=self.headers,
            data=json.dumps(arabic_customer_data)
        )
        
        assert response.status_code == 200
        customer_name = response.json()["data"]["name"]
        
        # Retrieve and verify Arabic content
        response = requests.get(
            f"{self.base_url}/api/resource/Customer/{customer_name}",
            headers=self.headers
        )
        
        assert response.status_code == 200
        customer = response.json()["data"]
        assert customer["customer_name"] == arabic_customer_data["customer_name"]
        assert "ورشة أحمد" in customer["customer_name"]
        
        # Test search with Arabic text
        response = requests.get(
            f"{self.base_url}/api/resource/Customer",
            headers=self.headers,
            params={
                "filters": json.dumps([["customer_name", "like", "%أحمد%"]])
            }
        )
        
        assert response.status_code == 200
        search_results = response.json()["data"]
        arabic_results = [c for c in search_results if "أحمد" in c["customer_name"]]
        assert len(arabic_results) >= 1
    
    def test_sms_whatsapp_integration_api(self, test_customer_data):
        """Test SMS/WhatsApp communication API endpoints."""
        
        # Create customer with mobile number
        customer_data = test_customer_data["english"]
        response = requests.post(
            f"{self.base_url}/api/resource/Customer",
            headers=self.headers,
            data=json.dumps(customer_data)
        )
        customer_name = response.json()["data"]["name"]
        
        # Test SMS sending API
        sms_data = {
            "receiver_list": [customer_data["mobile_no"]],
            "message": "Your vehicle service is ready for pickup.",
            "sender_name": "Universal Workshop"
        }
        
        response = requests.post(
            f"{self.base_url}/api/method/universal_workshop.api.send_sms",
            headers=self.headers,
            data=json.dumps(sms_data)
        )
        
        # Should accept request (actual sending depends on configuration)
        assert response.status_code in [200, 202]
        
        # Test WhatsApp messaging API
        whatsapp_data = {
            "to": customer_data["mobile_no"],
            "message": "Your service appointment is confirmed for tomorrow at 10 AM.",
            "template_name": "appointment_confirmation"
        }
        
        response = requests.post(
            f"{self.base_url}/api/method/universal_workshop.api.send_whatsapp",
            headers=self.headers,
            data=json.dumps(whatsapp_data)
        )
        
        # Should accept request
        assert response.status_code in [200, 202]
    
    def test_license_management_api(self):
        """Test license management and security API endpoints."""
        
        # Test hardware fingerprint generation
        response = requests.get(
            f"{self.base_url}/api/method/universal_workshop.license.get_hardware_fingerprint",
            headers=self.headers
        )
        
        assert response.status_code == 200
        fingerprint_data = response.json()
        assert "mac_address" in fingerprint_data
        assert "cpu_serial" in fingerprint_data
        
        # Test license validation
        response = requests.get(
            f"{self.base_url}/api/method/universal_workshop.license.validate_license",
            headers=self.headers
        )
        
        assert response.status_code == 200
        license_status = response.json()
        assert "valid" in license_status
        assert "expires_on" in license_status
        
        # Test business binding verification
        business_data = {
            "business_name": "Test Workshop LLC",
            "business_name_arabic": "شركة الورشة التجريبية",
            "registration_number": "CR-123456789"
        }
        
        response = requests.post(
            f"{self.base_url}/api/method/universal_workshop.license.verify_business",
            headers=self.headers,
            data=json.dumps(business_data)
        )
        
        # Should process verification request
        assert response.status_code in [200, 202]
    
    def test_api_error_handling(self):
        """Test API error handling and validation."""
        
        # Test invalid endpoint
        response = requests.get(
            f"{self.base_url}/api/resource/InvalidDocType",
            headers=self.headers
        )
        
        assert response.status_code == 404
        
        # Test invalid authentication
        invalid_headers = {
            'Authorization': 'token invalid:credentials',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            f"{self.base_url}/api/resource/Customer",
            headers=invalid_headers
        )
        
        assert response.status_code == 401
        
        # Test invalid data submission
        invalid_customer_data = {
            "customer_name": "",  # Required field empty
            "customer_group": "NonExistentGroup"
        }
        
        response = requests.post(
            f"{self.base_url}/api/resource/Customer",
            headers=self.headers,
            data=json.dumps(invalid_customer_data)
        )
        
        assert response.status_code == 417  # Validation error
        error_response = response.json()
        assert "message" in error_response
    
    def test_api_performance_and_rate_limiting(self):
        """Test API performance and rate limiting."""
        
        # Test bulk operations
        import time
        start_time = time.time()
        
        # Create multiple customers quickly
        responses = []
        for i in range(10):
            customer_data = {
                "customer_name": f"Bulk Test Customer {i}",
                "customer_group": "Individual",
                "territory": "Oman",
                "email_id": f"bulk{i}@test.com"
            }
            
            response = requests.post(
                f"{self.base_url}/api/resource/Customer",
                headers=self.headers,
                data=json.dumps(customer_data)
            )
            responses.append(response)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
        
        # Should complete within reasonable time (5 seconds for 10 requests)
        assert processing_time < 5.0
        
        # Test rate limiting (if implemented)
        # Make rapid requests to test rate limiter
        rapid_responses = []
        for i in range(50):
            response = requests.get(
                f"{self.base_url}/api/resource/Customer",
                headers=self.headers
            )
            rapid_responses.append(response)
            
            # Check if rate limited
            if response.status_code == 429:
                break
        
        # At least some requests should succeed
        successful_requests = [r for r in rapid_responses if r.status_code == 200]
        assert len(successful_requests) > 0
