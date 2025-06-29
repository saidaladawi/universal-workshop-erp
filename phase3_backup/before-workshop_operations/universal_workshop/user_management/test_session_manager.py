"""
Unit Tests for Session Management System
Universal Workshop ERP - User Management

Tests for session timeout policies, concurrent session limits, session revocation,
device tracking, and integration with security features.
"""

import unittest
import json
import datetime
from unittest.mock import patch, MagicMock

import frappe
from frappe.utils import now_datetime, add_to_date
from universal_workshop.user_management.session_manager import SessionManager, SessionPolicy


class TestSessionManager(unittest.TestCase):
    """Test suite for SessionManager class"""

    def setUp(self):
        """Setup test environment"""
        self.session_manager = SessionManager()
        self.test_user = "test@universal-workshop.om"
        self.test_session_id = "test_session_123"
        
        # Ensure test user exists
        if not frappe.db.exists("User", self.test_user):
            user_doc = frappe.new_doc("User")
            user_doc.email = self.test_user
            user_doc.first_name = "Test"
            user_doc.last_name = "User"
            user_doc.insert(ignore_permissions=True)
            
        # Clean up any existing test sessions
        frappe.db.sql("""
            DELETE FROM `tabWorkshop User Session` 
            WHERE user_email = %s
        """, [self.test_user])
        
        frappe.db.commit()

    def tearDown(self):
        """Clean up test data"""
        try:
            # Clean up test sessions
            frappe.db.sql("""
                DELETE FROM `tabWorkshop User Session` 
                WHERE user_email = %s OR session_id LIKE 'test_%'
            """, [self.test_user])
            
            # Clean up test user (optional)
            if frappe.db.exists("User", self.test_user):
                frappe.delete_doc("User", self.test_user, ignore_permissions=True)
                
            frappe.db.commit()
        except Exception as e:
            frappe.log_error(f"Test cleanup error: {e}")

    def test_session_policy_creation(self):
        """Test SessionPolicy dataclass functionality"""
        # Test default policy
        default_policy = SessionPolicy()
        self.assertEqual(default_policy.idle_timeout_minutes, 30)
        self.assertEqual(default_policy.absolute_timeout_hours, 8)
        self.assertEqual(default_policy.max_concurrent_sessions, 3)
        
        # Test custom policy
        custom_policy = SessionPolicy(
            idle_timeout_minutes=15,
            max_concurrent_sessions=2,
            force_single_session=True
        )
        self.assertEqual(custom_policy.idle_timeout_minutes, 15)
        self.assertTrue(custom_policy.force_single_session)
        
        # Test serialization
        policy_dict = custom_policy.to_dict()
        self.assertIsInstance(policy_dict, dict)
        self.assertEqual(policy_dict['idle_timeout_minutes'], 15)
        
        # Test deserialization
        restored_policy = SessionPolicy.from_dict(policy_dict)
        self.assertEqual(restored_policy.idle_timeout_minutes, 15)
        self.assertTrue(restored_policy.force_single_session)

    def test_get_session_policy_by_role(self):
        """Test session policy determination by user roles"""
        # Mock user roles for testing
        with patch('frappe.get_roles') as mock_get_roles:
            # Test System Manager policy (high security)
            mock_get_roles.return_value = ["System Manager", "User"]
            policy = self.session_manager.get_session_policy(self.test_user)
            self.assertEqual(policy.idle_timeout_minutes, 15)
            self.assertEqual(policy.max_concurrent_sessions, 2)
            self.assertTrue(policy.force_single_session)
            
            # Test regular workshop user policy
            mock_get_roles.return_value = ["Technician", "User"]
            policy = self.session_manager.get_session_policy(self.test_user)
            self.assertEqual(policy.idle_timeout_minutes, 30)
            self.assertEqual(policy.max_concurrent_sessions, 3)
            self.assertFalse(policy.force_single_session)
            
            # Test default policy for unknown roles
            mock_get_roles.return_value = ["Guest"]
            policy = self.session_manager.get_session_policy(self.test_user)
            self.assertEqual(policy.idle_timeout_minutes, 30)  # Default

    @patch('frappe.local.request')
    def test_create_session_record(self, mock_request):
        """Test session record creation"""
        # Mock request information
        mock_request.environ = {
            'REMOTE_ADDR': '192.168.1.100',
            'HTTP_USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        request_info = {
            'ip_address': '192.168.1.100',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'device_info': {'browser': 'Chrome', 'os': 'Windows'}
        }
        
        # Create session record
        result = self.session_manager.create_session_record(
            self.test_user, 
            self.test_session_id, 
            request_info
        )
        
        self.assertTrue(result['success'])
        self.assertIn('session_id', result)
        
        # Verify session was created in database
        session_exists = frappe.db.exists("Workshop User Session", {
            "session_id": self.test_session_id,
            "user_email": self.test_user
        })
        self.assertTrue(session_exists)

    def test_concurrent_session_limit(self):
        """Test concurrent session limit enforcement"""
        # Create a policy with low concurrent session limit
        policy = SessionPolicy(max_concurrent_sessions=2)
        
        # Create first session
        result1 = self.session_manager.create_session_record(
            self.test_user, "session_1", {}
        )
        self.assertTrue(result1['success'])
        
        # Create second session
        result2 = self.session_manager.create_session_record(
            self.test_user, "session_2", {}
        )
        self.assertTrue(result2['success'])
        
        # Try to create third session (should fail or revoke oldest)
        with patch.object(self.session_manager, 'get_session_policy', return_value=policy):
            result3 = self.session_manager.create_session_record(
                self.test_user, "session_3", {}
            )
            
            # Should succeed (oldest session revoked)
            self.assertTrue(result3['success'])
            
        # Verify only 2 active sessions remain
        active_sessions = frappe.db.count("Workshop User Session", {
            "user_email": self.test_user,
            "is_active": 1
        })
        self.assertLessEqual(active_sessions, 2)

    def test_session_revocation(self):
        """Test manual session revocation"""
        # Create a session
        self.session_manager.create_session_record(
            self.test_user, self.test_session_id, {}
        )
        
        # Revoke the session
        result = self.session_manager.revoke_session(
            self.test_session_id, "Test revocation"
        )
        
        self.assertTrue(result['success'])
        
        # Verify session is revoked
        session_doc = frappe.get_doc("Workshop User Session", {
            "session_id": self.test_session_id
        })
        self.assertFalse(session_doc.is_active)
        self.assertEqual(session_doc.revocation_reason, "Test revocation")

    def test_session_expiry_cleanup(self):
        """Test cleanup of expired sessions"""
        # Create expired session
        expired_time = add_to_date(now_datetime(), hours=-2)  # 2 hours ago
        
        session_doc = frappe.new_doc("Workshop User Session")
        session_doc.user_email = self.test_user
        session_doc.session_id = "expired_session_123"
        session_doc.login_time = expired_time
        session_doc.last_activity = expired_time
        session_doc.expiry_time = expired_time
        session_doc.is_active = 1
        session_doc.insert(ignore_permissions=True)
        
        # Run cleanup
        result = self.session_manager.cleanup_expired_sessions()
        
        self.assertTrue(result['success'])
        self.assertGreater(result['cleaned_count'], 0)
        
        # Verify expired session is deactivated
        session_doc.reload()
        self.assertFalse(session_doc.is_active)

    def test_device_info_extraction(self):
        """Test device information extraction from user agent"""
        user_agents = [
            {
                'agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'expected_browser': 'Chrome',
                'expected_os': 'Windows'
            },
            {
                'agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'expected_browser': 'Chrome',
                'expected_os': 'macOS'
            },
            {
                'agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'expected_browser': 'Chrome',
                'expected_os': 'Linux'
            }
        ]
        
        for test_case in user_agents:
            request_info = {'user_agent': test_case['agent']}
            device_info = self.session_manager._extract_device_info(request_info)
            
            self.assertEqual(device_info['browser'], test_case['expected_browser'])
            self.assertEqual(device_info['os'], test_case['expected_os'])

    def test_session_validation(self):
        """Test session validation logic"""
        # Create valid session
        self.session_manager.create_session_record(
            self.test_user, self.test_session_id, {}
        )
        
        # Validate active session
        result = self.session_manager.validate_session(self.test_session_id)
        self.assertTrue(result['valid'])
        self.assertEqual(result['user_email'], self.test_user)
        
        # Test non-existent session
        result = self.session_manager.validate_session("non_existent_session")
        self.assertFalse(result['valid'])
        self.assertIn('error', result)

    def test_user_sessions_retrieval(self):
        """Test retrieval of user sessions"""
        # Create multiple sessions for user
        sessions = ["session_1", "session_2", "session_3"]
        for session_id in sessions:
            self.session_manager.create_session_record(
                self.test_user, session_id, {'ip_address': f'192.168.1.{sessions.index(session_id) + 1}'}
            )
        
        # Revoke one session
        self.session_manager.revoke_session("session_2", "Test revocation")
        
        # Get active sessions only
        active_sessions = self.session_manager.get_user_sessions(self.test_user, include_inactive=False)
        self.assertEqual(len(active_sessions), 2)  # 2 active sessions
        
        # Get all sessions
        all_sessions = self.session_manager.get_user_sessions(self.test_user, include_inactive=True)
        self.assertEqual(len(all_sessions), 3)  # All sessions including revoked

    def test_session_statistics(self):
        """Test session statistics generation"""
        # Create test sessions
        for i in range(3):
            self.session_manager.create_session_record(
                f"user{i}@test.com", f"session_{i}", {}
            )
        
        # Get statistics
        stats = self.session_manager.get_session_statistics()
        
        self.assertIsInstance(stats, dict)
        self.assertIn('total_active_sessions', stats)
        self.assertIn('total_users_online', stats)
        self.assertGreaterEqual(stats['total_active_sessions'], 0)

    @patch('frappe.db.get_value')
    def test_custom_user_session_policy(self, mock_get_value):
        """Test custom session policy for specific user"""
        # Mock custom session policy
        custom_policy_json = json.dumps({
            'idle_timeout_minutes': 45,
            'max_concurrent_sessions': 5,
            'force_single_session': False
        })
        
        mock_get_value.return_value = custom_policy_json
        
        # Get policy should return custom settings
        policy = self.session_manager.get_session_policy(self.test_user)
        self.assertEqual(policy.idle_timeout_minutes, 45)
        self.assertEqual(policy.max_concurrent_sessions, 5)

    def test_bulk_session_revocation(self):
        """Test bulk revocation of user sessions"""
        # Create multiple sessions
        sessions = ["bulk_session_1", "bulk_session_2", "bulk_session_3"]
        for session_id in sessions:
            self.session_manager.create_session_record(
                self.test_user, session_id, {}
            )
        
        # Revoke all sessions
        result = self.session_manager.revoke_user_sessions(
            self.test_user, "Bulk revocation test"
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['revoked_count'], 3)
        
        # Verify all sessions are revoked
        active_count = frappe.db.count("Workshop User Session", {
            "user_email": self.test_user,
            "is_active": 1
        })
        self.assertEqual(active_count, 0)


class TestSessionManagerAPI(unittest.TestCase):
    """Test suite for Session Manager API methods"""

    def setUp(self):
        """Setup test environment for API tests"""
        self.test_user = "api_test@universal-workshop.om"
        
        # Clean up any existing data
        frappe.db.sql("""
            DELETE FROM `tabWorkshop User Session` 
            WHERE user_email = %s
        """, [self.test_user])
        
        frappe.db.commit()

    def tearDown(self):
        """Clean up test data"""
        frappe.db.sql("""
            DELETE FROM `tabWorkshop User Session` 
            WHERE user_email = %s
        """, [self.test_user])
        frappe.db.commit()

    @patch('frappe.session.user', 'test@example.com')
    def test_get_session_status_api(self):
        """Test get_session_status API method"""
        from universal_workshop.user_management.session_manager import get_session_status
        
        # Should return current session status
        result = get_session_status()
        self.assertIsInstance(result, dict)
        self.assertIn('policy', result)

    def test_cleanup_expired_sessions_api(self):
        """Test cleanup_expired_sessions API method"""
        from universal_workshop.user_management.session_manager import cleanup_expired_sessions
        
        result = cleanup_expired_sessions()
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
        self.assertIn('cleaned_count', result)

    def test_get_session_statistics_api(self):
        """Test get_session_statistics API method"""
        from universal_workshop.user_management.session_manager import get_session_statistics
        
        result = get_session_statistics()
        self.assertIsInstance(result, dict)
        self.assertIn('total_active_sessions', result)
        self.assertIn('total_users_online', result)


class TestSessionIntegration(unittest.TestCase):
    """Integration tests for session management with other systems"""

    def test_session_security_dashboard_integration(self):
        """Test integration with security dashboard"""
        # This would test that session events are properly logged
        # and visible in the security dashboard
        pass

    def test_session_audit_trail_integration(self):
        """Test integration with audit trail system"""
        # This would test that session events are properly logged
        # in the audit trail for compliance purposes
        pass

    def test_session_mfa_integration(self):
        """Test integration with MFA system"""
        # This would test that MFA status affects session policies
        # and that session revocation triggers MFA re-verification
        pass


if __name__ == '__main__':
    # Run tests
    frappe.init(site="universal.local")
    frappe.connect()
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_suite.addTest(unittest.makeSuite(TestSessionManager))
    test_suite.addTest(unittest.makeSuite(TestSessionManagerAPI))
    test_suite.addTest(unittest.makeSuite(TestSessionIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print results
    if result.wasSuccessful():
        print("All session management tests passed!")
    else:
        print(f"Tests failed: {len(result.failures)} failures, {len(result.errors)} errors")
        for failure in result.failures:
            print(f"FAILURE: {failure[0]}")
            print(failure[1])
        for error in result.errors:
            print(f"ERROR: {error[0]}")
            print(error[1]) 