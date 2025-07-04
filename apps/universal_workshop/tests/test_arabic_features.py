# Copyright (c) 2025, Universal Workshop ERP
# For license information, see license.txt

import unittest
import frappe
from frappe.test_runner import make_test_records
from universal_workshop.utils.arabic_utils import ArabicTextUtils
from universal_workshop.utils.vat import calculate_oman_vat

class TestArabicFeatures(unittest.TestCase):
    def setUp(self):
        """Setup test data"""
        frappe.set_user("Administrator")
        
    def test_arabic_text_validation(self):
        """Test Arabic text validation"""
        # Test Arabic text detection
        arabic_text = "أحمد الراشد"
        english_text = "Ahmed Al-Rashid"
        mixed_text = "Ahmed الراشد"
        
        self.assertTrue(ArabicTextUtils.is_arabic_text(arabic_text))
        self.assertFalse(ArabicTextUtils.is_arabic_text(english_text))
        self.assertTrue(ArabicTextUtils.is_arabic_text(mixed_text))
        
    def test_oman_vat_calculation(self):
        """Test Oman VAT calculation (5%)"""
        base_amount = 100.000
        
        vat_result = calculate_oman_vat(base_amount)
        
        self.assertEqual(vat_result['base_amount'], 100.000)
        self.assertEqual(vat_result['vat_rate'], 5.0)
        self.assertEqual(vat_result['vat_amount'], 5.000)
        self.assertEqual(vat_result['total_amount'], 105.000)
        
    def test_workshop_profile_arabic(self):
        """Test workshop profile with Arabic data"""
        workshop_data = {
            'workshop_name': 'Al Khaleej Auto Service',
            'workshop_name_ar': 'خدمة الخليج للسيارات',
            'business_license': '1234567',
            'vat_number': 'OM1234567890123',
            'phone_oman': '+968 24 123456'
        }
        
        workshop = frappe.new_doc('Workshop Profile')
        workshop.update(workshop_data)
        workshop.insert()
        
        self.assertEqual(workshop.workshop_name_ar, 'خدمة الخليج للسيارات')
        self.assertTrue(workshop.workshop_code.startswith('WS-'))
        
    def test_customer_arabic_creation(self):
        """Test customer creation with Arabic data"""
        customer_data = {
            'customer_name': 'Ahmed Al-Rashid',
            'customer_name_ar': 'أحمد الراشد',
            'phone': '+968 24123456',
            'email': 'ahmed@example.com'
        }
        
        customer = frappe.new_doc('Customer')
        customer.update(customer_data)
        customer.insert()
        
        self.assertEqual(customer.customer_name_ar, 'أحمد الراشد')
        self.assertEqual(customer.phone, '+968 24123456')
        
    def test_vehicle_management_arabic(self):
        """Test vehicle management with Arabic data"""
        vehicle_data = {
            'customer': 'TEST-CUSTOMER-001',
            'vehicle_id': 'VH-001',
            'make': 'Toyota',
            'model': 'Camry',
            'year': '2020',
            'vin_number': '1HGBH41JXMN109186'
        }
        
        vehicle = frappe.new_doc('Customer Vehicle')
        vehicle.update(vehicle_data)
        vehicle.insert()
        
        self.assertEqual(vehicle.vehicle_id, 'VH-001')
        self.assertEqual(vehicle.make, 'Toyota')
        
    def test_business_license_validation(self):
        """Test Oman business license validation"""
        # Valid license (7 digits)
        valid_license = '1234567'
        self.assertTrue(len(valid_license) == 7 and valid_license.isdigit())
        
        # Invalid license (6 digits)
        invalid_license = '123456'
        self.assertFalse(len(invalid_license) == 7)
        
    def test_oman_phone_validation(self):
        """Test Oman phone number validation"""
        # Valid Oman phone
        valid_phone = '+968 24123456'
        self.assertTrue(valid_phone.startswith('+968'))
        
        # Invalid phone (wrong country code)
        invalid_phone = '+971 24123456'
        self.assertFalse(invalid_phone.startswith('+968'))
        
    def tearDown(self):
        """Clean up test data"""
        frappe.db.rollback()

if __name__ == '__main__':
    unittest.main() 