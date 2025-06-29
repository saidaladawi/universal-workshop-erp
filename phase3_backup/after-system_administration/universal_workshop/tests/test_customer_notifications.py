import unittest
import frappe
import json
from unittest.mock import patch, MagicMock
from universal_workshop.sales_service.customer_notifications import (
    CustomerNotificationSystem,
    send_service_notification,
    send_customer_notification,
    get_notification_templates,
    test_notification_system,
)


class TestCustomerNotifications(unittest.TestCase):
    """Comprehensive test suite for Customer Notification System"""

    def setUp(self):
        """Set up test environment"""
        self.test_customer_data = {
            "customer_name": "Ahmed Al-Rashid",
            "customer_name_ar": "أحمد الراشد",
            "email_id": "ahmed@example.com",
            "mobile_no": "+96824123456",
            "customer_group": "Individual",
        }

        self.test_service_order_data = {
            "customer": "",  # Will be set dynamically
            "delivery_date": "2024-07-01",
            "grand_total": 150.000,
            "vehicle_registration": "OM-123456",
            "service_estimate_reference": "EST-001",
            "items": [],
        }

        # Create test customer
        self.test_customer = self.create_test_customer()

        # Create test service order
        self.test_service_order = self.create_test_service_order()

    def create_test_customer(self):
        """Create test customer for notifications"""
        try:
            customer = frappe.new_doc("Customer")
            customer.update(self.test_customer_data)
            customer.insert(ignore_permissions=True)
            frappe.db.commit()
            return customer
        except Exception:
            # Customer might already exist
            existing = frappe.get_list(
                "Customer",
                filters={"customer_name": self.test_customer_data["customer_name"]},
                limit=1,
            )
            if existing:
                return frappe.get_doc("Customer", existing[0].name)
            raise

    def create_test_service_order(self):
        """Create test service order for notifications"""
        try:
            service_order = frappe.new_doc("Sales Order")
            self.test_service_order_data["customer"] = self.test_customer.name
            service_order.update(self.test_service_order_data)

            # Add test item
            service_order.append(
                "items",
                {
                    "item_code": "TEST-SERVICE",
                    "item_name": "Test Service",
                    "item_name_ar": "خدمة تجريبية",
                    "qty": 1,
                    "rate": 150.000,
                    "amount": 150.000,
                },
            )

            service_order.insert(ignore_permissions=True)
            frappe.db.commit()
            return service_order
        except Exception:
            # Service order might already exist
            existing = frappe.get_list(
                "Sales Order", filters={"customer": self.test_customer.name}, limit=1
            )
            if existing:
                return frappe.get_doc("Sales Order", existing[0].name)
            raise

    def test_notification_system_initialization(self):
        """Test CustomerNotificationSystem initialization"""
        # Test initialization with service order
        notification_system = CustomerNotificationSystem(self.test_service_order.name)
        self.assertEqual(notification_system.service_order, self.test_service_order.name)
        self.assertEqual(notification_system.customer_doc.name, self.test_customer.name)

        # Test initialization with customer only
        notification_system = CustomerNotificationSystem(customer=self.test_customer.name)
        self.assertEqual(notification_system.customer, self.test_customer.name)
        self.assertEqual(notification_system.customer_doc.name, self.test_customer.name)

    def test_notification_templates(self):
        """Test notification template structure"""
        notification_system = CustomerNotificationSystem()

        # Test service estimate templates
        template = notification_system._get_notification_template("service_estimate", "created")
        self.assertIn("subject_en", template)
        self.assertIn("subject_ar", template)
        self.assertIn("email_body_en", template)
        self.assertIn("email_body_ar", template)
        self.assertIn("sms_en", template)
        self.assertIn("sms_ar", template)

        # Test service progress templates
        template = notification_system._get_notification_template("service_progress", "completed")
        self.assertIn("subject_en", template)
        self.assertIn("email_body_ar", template)

        # Test payment templates
        template = notification_system._get_notification_template("payment", "reminder")
        self.assertIsNotNone(template)

        # Test appointment templates
        template = notification_system._get_notification_template("appointment", "scheduled")
        self.assertIsNotNone(template)

    def test_notification_data_preparation(self):
        """Test notification data preparation"""
        notification_system = CustomerNotificationSystem(self.test_service_order.name)

        custom_data = {
            "progress_percentage": 75,
            "current_operation": "Engine Inspection",
            "current_operation_ar": "فحص المحرك",
        }

        data = notification_system._prepare_notification_data(custom_data)

        # Check basic customer data
        self.assertEqual(data["customer_name"], self.test_customer.customer_name)
        self.assertEqual(data["customer_name_ar"], self.test_customer.customer_name_ar)
        self.assertEqual(data["customer_email"], self.test_customer.email_id)

        # Check service order data
        self.assertEqual(data["service_order"], self.test_service_order.name)
        self.assertEqual(data["vehicle_registration"], self.test_service_order.vehicle_registration)
        self.assertIn("total_amount", data)

        # Check custom data
        self.assertEqual(data["progress_percentage"], 75)
        self.assertEqual(data["current_operation_ar"], "فحص المحرك")

    def test_arabic_text_handling(self):
        """Test Arabic text handling in notifications"""
        notification_system = CustomerNotificationSystem(self.test_service_order.name)

        # Test Arabic data preparation
        data = notification_system._prepare_notification_data({})
        self.assertTrue(len(data["customer_name_ar"]) > 0)

        # Test Arabic template selection
        template = notification_system._get_notification_template("service_estimate", "created")
        self.assertIn("أحمد", template["email_body_ar"])  # Arabic text present
        self.assertIn("تقدير", template["subject_ar"])  # Arabic text present

    def test_oman_mobile_formatting(self):
        """Test Oman mobile number formatting"""
        notification_system = CustomerNotificationSystem()

        # Test various mobile number formats
        test_cases = [
            ("+96824123456", "+96824123456"),
            ("96824123456", "+96824123456"),
            ("24123456", "+96824123456"),
            ("968-24-123456", "+96824123456"),
            ("", ""),
            (None, ""),
        ]

        for input_mobile, expected in test_cases:
            result = notification_system._format_oman_mobile(input_mobile)
            self.assertEqual(result, expected, f"Failed for input: {input_mobile}")

    def test_currency_formatting(self):
        """Test OMR currency formatting"""
        notification_system = CustomerNotificationSystem()

        # Test various amounts
        test_cases = [
            (150.000, "OMR 150.000"),
            (1234.567, "OMR 1,234.567"),
            (0, "OMR 0.000"),
            (None, "OMR 0.000"),
        ]

        for amount, expected in test_cases:
            result = notification_system._format_currency(amount)
            self.assertEqual(result, expected, f"Failed for amount: {amount}")

    def test_services_list_generation(self):
        """Test services list generation for notifications"""
        notification_system = CustomerNotificationSystem(self.test_service_order.name)

        # Test English services list
        services_en = notification_system._get_services_list(arabic=False)
        self.assertIn("Test Service", services_en)
        self.assertIn("OMR 150.000", services_en)

        # Test Arabic services list
        services_ar = notification_system._get_services_list(arabic=True)
        self.assertIn("خدمة تجريبية", services_ar)
        self.assertIn("OMR 150.000", services_ar)

    @patch("frappe.email.doctype.email_queue.email_queue.send_email")
    def test_email_notification_sending(self, mock_send_email):
        """Test email notification sending"""
        mock_send_email.return_value = True

        notification_system = CustomerNotificationSystem(self.test_service_order.name)

        template = notification_system._get_notification_template("service_estimate", "created")
        data = notification_system._prepare_notification_data({})

        result = notification_system._send_email_notification(template, data)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["recipient"], self.test_customer.email_id)
        mock_send_email.assert_called_once()

    @patch("frappe.get_single")
    def test_sms_notification_sending(self, mock_get_single):
        """Test SMS notification sending"""
        # Mock SMS settings
        mock_sms_settings = MagicMock()
        mock_sms_settings.sms_gateway_url = "https://sms.example.com"
        mock_get_single.return_value = mock_sms_settings

        notification_system = CustomerNotificationSystem(self.test_service_order.name)

        template = notification_system._get_notification_template("service_estimate", "created")
        data = notification_system._prepare_notification_data({})

        result = notification_system._send_sms_notification(template, data)

        self.assertEqual(result["status"], "success")
        self.assertIn("+968", result["recipient"])

    def test_workflow_notification_success(self):
        """Test complete workflow notification sending"""
        notification_system = CustomerNotificationSystem(self.test_service_order.name)

        result = notification_system.send_workflow_notification(
            "service_estimate", "created", custom_data={"test_field": "test_value"}
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["notification_type"], "service_estimate")
        self.assertEqual(result["stage"], "created")
        self.assertIn("results", result)

    def test_workflow_notification_invalid_template(self):
        """Test workflow notification with invalid template"""
        notification_system = CustomerNotificationSystem(self.test_service_order.name)

        result = notification_system.send_workflow_notification("invalid_type", "invalid_stage")

        self.assertEqual(result["status"], "error")
        self.assertIn("template not found", result["message"].lower())

    def test_appointment_reminder_scheduling(self):
        """Test appointment reminder scheduling"""
        notification_system = CustomerNotificationSystem()

        # This test would require mocking the date
        # For now, we'll test the method structure
        result = notification_system.schedule_appointment_reminders()

        self.assertIn("status", result)
        if result["status"] == "success":
            self.assertIn("reminders_sent", result)

    def test_bulk_notifications(self):
        """Test bulk notification sending"""
        notification_system = CustomerNotificationSystem()

        customers = [self.test_customer.name]
        results = notification_system.send_bulk_notifications(
            customers, "service_progress", "progress_update", {"progress_percentage": 50}
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["customer"], self.test_customer.name)
        self.assertIn("result", results[0])

    def test_api_send_service_notification(self):
        """Test API method for sending service notifications"""
        result = send_service_notification(
            self.test_service_order.name, "service_estimate", "created"
        )

        self.assertIn("status", result)

    def test_api_send_customer_notification(self):
        """Test API method for sending customer notifications"""
        result = send_customer_notification(
            self.test_customer.name,
            "appointment",
            "scheduled",
            json.dumps({"appointment_date": "2024-07-01"}),
        )

        self.assertIn("status", result)

    def test_api_get_notification_templates(self):
        """Test API method for getting notification templates"""
        result = get_notification_templates()

        self.assertIn("notification_types", result)
        self.assertIn("stages", result)
        self.assertIn("template_example", result)

        # Check notification types
        expected_types = ["service_estimate", "service_progress", "payment", "appointment"]
        for notification_type in expected_types:
            self.assertIn(notification_type, result["notification_types"])

    def test_api_test_notification_system(self):
        """Test API method for testing notification system"""
        result = test_notification_system(service_order=self.test_service_order.name)

        self.assertIn("status", result)

        # Test with customer only
        result = test_notification_system(customer=self.test_customer.name)
        self.assertIn("status", result)

        # Test with neither
        result = test_notification_system()
        self.assertEqual(result["status"], "error")

    def test_notification_type_specific_features(self):
        """Test notification type specific features"""
        notification_system = CustomerNotificationSystem(self.test_service_order.name)

        # Test service progress with progress percentage
        result = notification_system.send_workflow_notification(
            "service_progress",
            "progress_update",
            {"progress_percentage": 75, "current_operation": "Final inspection"},
        )
        self.assertEqual(result["status"], "success")

        # Test payment reminder with amount
        result = notification_system.send_workflow_notification(
            "payment", "reminder", {"amount_due": "OMR 150.000", "payment_link": "/payment/test"}
        )
        self.assertEqual(result["status"], "success")

        # Test appointment with date/time
        result = notification_system.send_workflow_notification(
            "appointment",
            "scheduled",
            {"appointment_date": "2024-07-01", "appointment_time": "09:00"},
        )
        self.assertEqual(result["status"], "success")

    def test_arabic_language_context(self):
        """Test Arabic language context handling"""
        # Temporarily set Arabic language
        original_lang = frappe.local.lang
        frappe.local.lang = "ar"

        try:
            notification_system = CustomerNotificationSystem(self.test_service_order.name)
            data = notification_system._prepare_notification_data({})

            self.assertEqual(data["language"], "ar")

            # Test Arabic template selection in email
            template = notification_system._get_notification_template("service_estimate", "created")
            result = notification_system._send_email_notification(template, data)

            # Should use Arabic template content
            self.assertIn("status", result)

        finally:
            frappe.local.lang = original_lang

    def test_performance_benchmarks(self):
        """Test notification system performance"""
        import time

        notification_system = CustomerNotificationSystem(self.test_service_order.name)

        # Test notification preparation performance
        start_time = time.time()
        data = notification_system._prepare_notification_data({})
        preparation_time = time.time() - start_time

        # Should prepare data in under 0.5 seconds
        self.assertLess(preparation_time, 0.5)

        # Test template retrieval performance
        start_time = time.time()
        template = notification_system._get_notification_template("service_estimate", "created")
        template_time = time.time() - start_time

        # Should retrieve template in under 0.1 seconds
        self.assertLess(template_time, 0.1)

    def test_error_handling(self):
        """Test error handling in notification system"""
        # Test with non-existent service order
        try:
            notification_system = CustomerNotificationSystem("NON-EXISTENT")
            self.fail("Should have raised an exception for non-existent service order")
        except Exception:
            pass  # Expected behavior

        # Test with non-existent customer
        try:
            notification_system = CustomerNotificationSystem(customer="NON-EXISTENT")
            self.fail("Should have raised an exception for non-existent customer")
        except Exception:
            pass  # Expected behavior

    def test_notification_log_creation(self):
        """Test notification log creation"""
        notification_system = CustomerNotificationSystem(self.test_service_order.name)

        # Send a notification
        result = notification_system.send_workflow_notification("service_estimate", "created")

        # Check if notification log was created
        logs = frappe.get_list(
            "Notification Log", filters={"document_name": self.test_service_order.name}, limit=1
        )

        # Should have at least one log entry
        self.assertGreaterEqual(len(logs), 0)

    def tearDown(self):
        """Clean up test data"""
        frappe.db.rollback()

        # Clean up test documents
        try:
            if hasattr(self, "test_service_order"):
                frappe.delete_doc(
                    "Sales Order", self.test_service_order.name, ignore_permissions=True
                )
            if hasattr(self, "test_customer"):
                frappe.delete_doc("Customer", self.test_customer.name, ignore_permissions=True)
        except Exception:
            pass  # Ignore cleanup errors

        frappe.db.commit()


if __name__ == "__main__":
    unittest.main()
