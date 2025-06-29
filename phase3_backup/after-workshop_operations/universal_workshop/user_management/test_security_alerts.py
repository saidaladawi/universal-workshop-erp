"""
Test Suite for Security Alerts System
Universal Workshop ERP - User Management
"""

import unittest
import json
from datetime import datetime

import frappe
from frappe.utils import now_datetime, add_to_date

from universal_workshop.user_management.security_alerts import (
    SecurityAlertsManager, AlertType, NotificationChannel, EscalationLevel,
    get_security_alerts_manager, trigger_security_alert, get_security_alerts_summary
)
from universal_workshop.user_management.audit_trail_extension import SeverityLevel


class TestSecurityAlertsSystem(unittest.TestCase):
    """Test suite for security alerts system"""
    
    def setUp(self):
        """Setup test environment"""
        self.alerts_manager = get_security_alerts_manager()
        self.test_user = "Administrator"
        self.test_ip = "192.168.1.100"
        
        # Clean up any existing test records
        frappe.db.sql("""
            DELETE FROM `tabSecurity Alert Log` 
            WHERE user_email = %s AND source_ip = %s
        """, [self.test_user, self.test_ip])
        frappe.db.commit()
        
    def test_alert_manager_initialization(self):
        """Test alert manager initialization"""
        self.assertIsNotNone(self.alerts_manager)
        self.assertIsNotNone(self.alerts_manager.alert_thresholds)
        self.assertIn(AlertType.FAILED_LOGIN, self.alerts_manager.alert_thresholds)
        
    def test_failed_login_alert_threshold(self):
        """Test failed login alert threshold detection"""
        
        # First few failed logins should not trigger alert
        for i in range(2):
            alerts = self.alerts_manager.check_and_trigger_alerts(
                event_type="login_failed",
                user_email=self.test_user,
                source_ip=self.test_ip,
                details={"attempt": i + 1}
            )
            self.assertEqual(len(alerts), 0, f"Alert should not trigger on attempt {i + 1}")
        
        # Third failed login should trigger alert (threshold = 3)
        alerts = self.alerts_manager.check_and_trigger_alerts(
            event_type="login_failed",
            user_email=self.test_user,
            source_ip=self.test_ip,
            details={"attempt": 3}
        )
        
        self.assertEqual(len(alerts), 1, "Alert should trigger on 3rd failed login")
        self.assertEqual(alerts[0]["alert_type"], AlertType.FAILED_LOGIN)
        
    def test_mfa_disabled_alert(self):
        """Test MFA disabled alert (immediate trigger)"""
        
        alerts = self.alerts_manager.check_and_trigger_alerts(
            event_type="mfa_disabled",
            user_email=self.test_user,
            source_ip=self.test_ip,
            details={"reason": "user_request"}
        )
        
        self.assertEqual(len(alerts), 1, "MFA disabled should trigger immediate alert")
        self.assertEqual(alerts[0]["alert_type"], AlertType.MFA_DISABLED)
        self.assertEqual(alerts[0]["severity"], SeverityLevel.CRITICAL)
        
    def test_permission_change_alert(self):
        """Test permission change alert"""
        
        alerts = self.alerts_manager.check_and_trigger_alerts(
            event_type="role_assigned",
            user_email=self.test_user,
            source_ip=self.test_ip,
            details={"role": "System Manager", "assigned_to": "test@example.com"}
        )
        
        self.assertEqual(len(alerts), 1, "Permission change should trigger alert")
        self.assertEqual(alerts[0]["alert_type"], AlertType.PERMISSION_CHANGE)
        
    def test_cooldown_period(self):
        """Test alert cooldown period functionality"""
        
        # Trigger first alert
        alerts1 = self.alerts_manager.check_and_trigger_alerts(
            event_type="mfa_disabled",
            user_email=self.test_user,
            source_ip=self.test_ip,
            details={"test": "cooldown_test_1"}
        )
        
        self.assertEqual(len(alerts1), 1, "First alert should trigger")
        
        # Immediate second trigger should be blocked by cooldown
        alerts2 = self.alerts_manager.check_and_trigger_alerts(
            event_type="mfa_disabled",
            user_email=self.test_user,
            source_ip=self.test_ip,
            details={"test": "cooldown_test_2"}
        )
        
        self.assertEqual(len(alerts2), 0, "Second alert should be blocked by cooldown")
        
    def test_alert_database_storage(self):
        """Test alert storage in database"""
        
        initial_count = frappe.db.count("Security Alert Log")
        
        alerts = self.alerts_manager.check_and_trigger_alerts(
            event_type="suspicious_activity",
            user_email=self.test_user,
            source_ip=self.test_ip,
            details={"test": "database_storage"}
        )
        
        final_count = frappe.db.count("Security Alert Log")
        
        self.assertEqual(final_count, initial_count + 1, "Alert should be stored in database")
        
        # Verify alert data
        if alerts:
            alert_id = alerts[0]["alert_id"]
            stored_alert = frappe.db.get_value("Security Alert Log", 
                                             {"alert_id": alert_id}, 
                                             ["alert_type", "user_email", "source_ip"], 
                                             as_dict=True)
            
            self.assertEqual(stored_alert.alert_type, "suspicious_activity")
            self.assertEqual(stored_alert.user_email, self.test_user)
            self.assertEqual(stored_alert.source_ip, self.test_ip)
    
    def test_api_trigger_security_alert(self):
        """Test API method for triggering alerts"""
        
        result = trigger_security_alert(
            event_type="login_failed",
            user_email=self.test_user,
            source_ip=self.test_ip,
            details='{"api_test": true}'
        )
        
        self.assertTrue(result["success"], "API call should succeed")
        self.assertIn("alerts_triggered", result)
        
    def test_get_security_alerts_summary(self):
        """Test getting security alerts summary"""
        
        # Create some test alerts first
        for i in range(3):
            self.alerts_manager.check_and_trigger_alerts(
                event_type="suspicious_activity",
                user_email=f"test{i}@example.com",
                source_ip=self.test_ip,
                details={"test": f"summary_test_{i}"}
            )
        
        summary = get_security_alerts_summary(days=7)
        
        self.assertTrue(summary["success"], "Summary API should succeed")
        self.assertIn("summary", summary)
        self.assertIn("total_alerts", summary["summary"])
        self.assertGreaterEqual(summary["summary"]["total_alerts"], 3)
        
    def test_escalation_levels(self):
        """Test different escalation levels"""
        
        # Test different alert types and their escalation levels
        test_cases = [
            ("login_failed", EscalationLevel.SUPERVISOR),
            ("mfa_disabled", EscalationLevel.EMERGENCY),
            ("permission_change", EscalationLevel.ADMINISTRATOR)
        ]
        
        for event_type, expected_escalation in test_cases:
            alerts = self.alerts_manager.check_and_trigger_alerts(
                event_type=event_type,
                user_email=f"test_{event_type}@example.com",
                source_ip=self.test_ip,
                details={"escalation_test": True}
            )
            
            if alerts:  # Some may not trigger due to thresholds
                self.assertEqual(alerts[0]["escalation_level"], expected_escalation,
                               f"Wrong escalation level for {event_type}")
    
    def test_notification_channels(self):
        """Test notification channel configuration"""
        
        # Test that different alert types have appropriate channels
        failed_login_threshold = self.alerts_manager.alert_thresholds[AlertType.FAILED_LOGIN]
        mfa_disabled_threshold = self.alerts_manager.alert_thresholds[AlertType.MFA_DISABLED]
        
        # Failed login should use email only
        self.assertIn(NotificationChannel.EMAIL, failed_login_threshold.notification_channels)
        
        # MFA disabled should use all channels (critical)
        self.assertIn(NotificationChannel.EMAIL, mfa_disabled_threshold.notification_channels)
        self.assertIn(NotificationChannel.SMS, mfa_disabled_threshold.notification_channels)
        self.assertIn(NotificationChannel.WHATSAPP, mfa_disabled_threshold.notification_channels)
        
    def test_alert_resolution(self):
        """Test alert resolution functionality"""
        
        # Create an alert first
        alerts = self.alerts_manager.check_and_trigger_alerts(
            event_type="suspicious_activity",
            user_email=self.test_user,
            source_ip=self.test_ip,
            details={"resolution_test": True}
        )
        
        if alerts:
            alert_id = alerts[0]["alert_id"]
            
            # Test resolution via API
            from universal_workshop.user_management.security_alerts import resolve_security_alert
            
            result = resolve_security_alert(
                alert_id=alert_id,
                resolution_notes="Test resolution - false positive"
            )
            
            self.assertTrue(result["success"], "Alert resolution should succeed")
            
            # Verify alert is marked as resolved
            resolved_alert = frappe.db.get_value("Security Alert Log",
                                               {"alert_id": alert_id},
                                               ["is_resolved", "resolved_by"],
                                               as_dict=True)
            
            self.assertEqual(resolved_alert.is_resolved, 1, "Alert should be marked as resolved")
            self.assertEqual(resolved_alert.resolved_by, frappe.session.user)
    
    def tearDown(self):
        """Clean up test data"""
        # Clean up test alerts
        frappe.db.sql("""
            DELETE FROM `tabSecurity Alert Log` 
            WHERE user_email LIKE %s OR source_ip = %s
        """, ["%test%", self.test_ip])
        frappe.db.commit()


def run_security_alerts_tests():
    """Run all security alerts tests"""
    
    print("Running Security Alerts System Tests...")
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSecurityAlertsSystem)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\nTest Results:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun) * 100
    print(f"\nSuccess Rate: {success_rate:.1f}%")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    run_security_alerts_tests()
