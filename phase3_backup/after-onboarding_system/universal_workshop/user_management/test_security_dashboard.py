"""
Test Security Dashboard Implementation
"""

import unittest
import json
from datetime import datetime, timedelta

import frappe
from frappe.utils import now_datetime, format_datetime

from .security_dashboard import SecurityDashboard, get_security_dashboard_data


class TestSecurityDashboard(unittest.TestCase):
    """Test suite for Security Dashboard functionality"""

    def setUp(self):
        """Set up test environment"""
        self.dashboard = SecurityDashboard()
        self.test_timeframe = 24

    def test_dashboard_initialization(self):
        """Test dashboard initialization"""
        self.assertIsNotNone(self.dashboard)
        self.assertIsNotNone(self.dashboard.permission_engine)

    def test_risk_level_calculation(self):
        """Test risk level calculation logic"""
        # Test low risk
        risk = self.dashboard._calculate_risk_level(0, 0, 0)
        self.assertEqual(risk, 'low')
        
        # Test medium risk
        risk = self.dashboard._calculate_risk_level(3, 2, 0)
        self.assertEqual(risk, 'medium')
        
        # Test high risk
        risk = self.dashboard._calculate_risk_level(5, 3, 2)
        self.assertEqual(risk, 'high')
        
        # Test critical risk
        risk = self.dashboard._calculate_risk_level(10, 8, 5)
        self.assertEqual(risk, 'critical')
        
        print("✅ Risk level calculation test passed")

    def test_trusted_ip_detection(self):
        """Test trusted IP address detection"""
        trusted_ips = [
            '192.168.1.100',
            '10.0.0.1',
            '172.16.0.1',
            '127.0.0.1'
        ]
        
        untrusted_ips = [
            '203.0.113.1',
            '8.8.8.8',
            '1.1.1.1'
        ]
        
        for ip in trusted_ips:
            self.assertTrue(self.dashboard._is_trusted_ip(ip), f"IP {ip} should be trusted")
            
        for ip in untrusted_ips:
            self.assertFalse(self.dashboard._is_trusted_ip(ip), f"IP {ip} should not be trusted")
            
        print("✅ Trusted IP detection test passed")


def run_dashboard_tests():
    """Run basic dashboard tests"""
    try:
        suite = unittest.TestLoader().loadTestsFromTestCase(TestSecurityDashboard)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        return result.wasSuccessful()
    except Exception as e:
        print(f"Test execution error: {e}")
        return False
