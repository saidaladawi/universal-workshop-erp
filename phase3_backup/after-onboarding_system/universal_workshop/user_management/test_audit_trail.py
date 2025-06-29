"""
Test Suite for Audit Trail Extension
Universal Workshop ERP - User Management
"""

import unittest
import json
from datetime import datetime

import frappe
from frappe.utils import now_datetime

from universal_workshop.user_management.audit_trail_extension import (
    AuditTrailExtension, AuditEventData, EventType, SeverityLevel, get_audit_trail
)


class TestAuditTrailExtension(unittest.TestCase):
    """Test suite for audit trail extension"""
    
    def setUp(self):
        """Setup test environment"""
        self.audit_trail = get_audit_trail()
        self.test_user = "Administrator"
        
        # Clean up any existing test records
        frappe.db.sql("""
            DELETE FROM `tabSecurity Audit Log` 
            WHERE description LIKE '%TEST%'
        """)
        frappe.db.commit()
    
    def test_audit_event_data_creation(self):
        """Test AuditEventData creation"""
        event_data = AuditEventData(
            event_type=EventType.LOGIN_SUCCESS,
            severity=SeverityLevel.INFO,
            user_email=self.test_user,
            description="TEST: Login event",
            details={"ip": "127.0.0.1", "browser": "test"}
        )
        
        self.assertEqual(event_data.event_type, EventType.LOGIN_SUCCESS)
        self.assertEqual(event_data.severity, SeverityLevel.INFO)
        self.assertEqual(event_data.user_email, self.test_user)
        self.assertIsNotNone(event_data.timestamp)
        self.assertIsInstance(event_data.details, dict)
    
    def test_log_event_success(self):
        """Test successful event logging"""
        event_data = AuditEventData(
            event_type=EventType.MFA_ENABLED,
            severity=SeverityLevel.MEDIUM,
            user_email=self.test_user,
            description="TEST: MFA enabled for user",
            details={"method": "TOTP", "test": True}
        )
        
        event_id = self.audit_trail.log_event(event_data)
        
        self.assertIsNotNone(event_id)
        self.assertIsInstance(event_id, str)
        self.assertEqual(len(event_id), 16)  # Event ID length
        
        # Verify event was saved to database
        saved_event = frappe.db.get_value("Security Audit Log", 
                                         {"event_id": event_id}, 
                                         ["event_type", "severity", "user_email", "description"])
        
        self.assertIsNotNone(saved_event)
        self.assertEqual(saved_event[0], "mfa_enabled")
        self.assertEqual(saved_event[1], "medium")
        self.assertEqual(saved_event[2], self.test_user)
        self.assertIn("TEST:", saved_event[3])
    
    def test_multiple_event_logging(self):
        """Test logging multiple events"""
        events_to_log = [
            (EventType.LOGIN_SUCCESS, SeverityLevel.INFO, "TEST: First login"),
            (EventType.SESSION_CREATED, SeverityLevel.INFO, "TEST: Session created"),
            (EventType.ROLE_ASSIGNED, SeverityLevel.MEDIUM, "TEST: Role assigned"),
            (EventType.SUSPICIOUS_ACTIVITY, SeverityLevel.HIGH, "TEST: Suspicious activity")
        ]
        
        logged_event_ids = []
        
        for event_type, severity, description in events_to_log:
            event_data = AuditEventData(
                event_type=event_type,
                severity=severity,
                user_email=self.test_user,
                description=description
            )
            
            event_id = self.audit_trail.log_event(event_data)
            self.assertIsNotNone(event_id)
            logged_event_ids.append(event_id)
        
        # Verify all events were saved
        count = frappe.db.count("Security Audit Log", {"description": ["like", "%TEST:%"]})
        self.assertEqual(count, len(events_to_log))
        
        # Verify event IDs are unique
        self.assertEqual(len(logged_event_ids), len(set(logged_event_ids)))
    
    def test_api_log_audit_event(self):
        """Test the whitelisted API method"""
        from universal_workshop.user_management.audit_trail_extension import log_audit_event
        
        # Test successful API call
        result = log_audit_event(
            event_type="login_success",
            severity="info", 
            description="TEST: API login event",
            details='{"api_test": true}'
        )
        
        self.assertTrue(result["success"])
        self.assertIn("event_id", result)
        self.assertIsNotNone(result["event_id"])
        
        # Verify the event was saved
        saved_event = frappe.db.get_value("Security Audit Log",
                                         {"event_id": result["event_id"]},
                                         ["description", "details"])
        
        self.assertIsNotNone(saved_event)
        self.assertIn("TEST:", saved_event[0])
        
        # Parse and verify details
        details = json.loads(saved_event[1])
        self.assertTrue(details["api_test"])
    
    def test_api_invalid_parameters(self):
        """Test API with invalid parameters"""
        from universal_workshop.user_management.audit_trail_extension import log_audit_event
        
        # Test invalid event type
        result = log_audit_event(
            event_type="invalid_event_type",
            severity="info",
            description="TEST: Invalid event"
        )
        
        self.assertFalse(result["success"])
        self.assertIn("error", result)
    
    def test_get_audit_summary(self):
        """Test audit summary generation"""
        from universal_workshop.user_management.audit_trail_extension import get_audit_summary
        
        # Log some test events first
        test_events = [
            (EventType.LOGIN_SUCCESS, SeverityLevel.INFO),
            (EventType.LOGIN_FAILED, SeverityLevel.MEDIUM),
            (EventType.MFA_ENABLED, SeverityLevel.MEDIUM),
            (EventType.SUSPICIOUS_ACTIVITY, SeverityLevel.HIGH)
        ]
        
        for event_type, severity in test_events:
            event_data = AuditEventData(
                event_type=event_type,
                severity=severity,
                user_email=self.test_user,
                description=f"TEST: Summary test - {event_type.value}"
            )
            self.audit_trail.log_event(event_data)
        
        # Get audit summary
        summary = get_audit_summary()
        
        self.assertIsInstance(summary, dict)
        self.assertIn("event_counts", summary)
        self.assertIn("total_events", summary)
        self.assertGreater(summary["total_events"], 0)
        
        # Check event counts structure
        event_counts = summary["event_counts"]
        self.assertIsInstance(event_counts, list)
        
        for event_count in event_counts:
            self.assertIn("event_type", event_count)
            self.assertIn("severity", event_count)
            self.assertIn("count", event_count)
    
    def test_event_id_generation(self):
        """Test event ID generation uniqueness"""
        event_ids = set()
        
        for i in range(10):
            event_data = AuditEventData(
                event_type=EventType.LOGIN_SUCCESS,
                severity=SeverityLevel.INFO,
                user_email=f"test_user_{i}@test.com",
                description=f"TEST: Event {i}"
            )
            
            event_id = self.audit_trail._generate_event_id(event_data)
            self.assertNotIn(event_id, event_ids)
            event_ids.add(event_id)
            
            # Verify event ID format
            self.assertEqual(len(event_id), 16)
            self.assertTrue(event_id.isupper())
            self.assertTrue(all(c in '0123456789ABCDEF' for c in event_id))
    
    def test_enum_values(self):
        """Test enum value consistency"""
        # Test EventType enum values
        expected_event_types = [
            "login_success", "login_failed", "logout", "mfa_enabled", 
            "mfa_disabled", "session_created", "session_revoked",
            "role_assigned", "permission_granted", "suspicious_activity"
        ]
        
        actual_event_types = [event.value for event in EventType]
        
        for expected in expected_event_types:
            self.assertIn(expected, actual_event_types)
        
        # Test SeverityLevel enum values  
        expected_severities = ["info", "medium", "high", "critical"]
        actual_severities = [severity.value for severity in SeverityLevel]
        
        for expected in expected_severities:
            self.assertIn(expected, actual_severities)
    
    def tearDown(self):
        """Clean up after tests"""
        # Clean up test records
        frappe.db.sql("""
            DELETE FROM `tabSecurity Audit Log` 
            WHERE description LIKE '%TEST%'
        """)
        frappe.db.commit()


def run_audit_trail_tests():
    """Run all audit trail tests"""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAuditTrailExtension)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    run_audit_trail_tests()
