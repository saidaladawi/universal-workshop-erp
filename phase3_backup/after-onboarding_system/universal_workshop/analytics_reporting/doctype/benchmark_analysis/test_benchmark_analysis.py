# -*- coding: utf-8 -*-
# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import frappe
import unittest
import json
from datetime import datetime, timedelta

class TestBenchmarkAnalysis(unittest.TestCase):
    """Test suite for Benchmark Analysis DocType"""
    
    def setUp(self):
        """Set up test data"""
        # Create test KPI if it doesn't exist
        if not frappe.db.exists('Analytics KPI', 'TEST_KPI_001'):
            test_kpi = frappe.new_doc('Analytics KPI')
            test_kpi.kpi_code = 'TEST_KPI_001'
            test_kpi.kpi_name = 'Test Revenue KPI'
            test_kpi.kpi_name_ar = 'مؤشر إيرادات تجريبي'
            test_kpi.kpi_category = 'Financial'
            test_kpi.current_value = 100.0
            test_kpi.target_value = 120.0
            test_kpi.is_active = 1
            test_kpi.insert(ignore_permissions=True)
            
    def tearDown(self):
        """Clean up test data"""
        # Delete test documents
        frappe.db.delete('Benchmark Analysis', {'benchmark_name': ['like', 'Test%']})
        frappe.db.delete('Analytics KPI', {'kpi_code': 'TEST_KPI_001'})
        frappe.db.commit()
        
    def test_benchmark_creation(self):
        """Test creating a new benchmark analysis"""
        benchmark = frappe.new_doc('Benchmark Analysis')
        benchmark.benchmark_name = 'Test Financial Benchmark'
        benchmark.benchmark_name_ar = 'مقارنة معيارية مالية تجريبية'
        benchmark.benchmark_type = 'Industry Standard'
        benchmark.business_area = 'Financial Performance'
        benchmark.primary_kpi = 'TEST_KPI_001'
        benchmark.current_value = 100.0
        benchmark.target_value = 120.0
        benchmark.industry_standard = 110.0
        benchmark.insert()
        
        self.assertTrue(benchmark.name)
        self.assertEqual(benchmark.benchmark_name, 'Test Financial Benchmark')
        self.assertEqual(benchmark.primary_kpi, 'TEST_KPI_001')
        
    def test_performance_score_calculation(self):
        """Test performance score calculation"""
        benchmark = self.create_test_benchmark()
        
        # Test with target values
        benchmark.current_value = 100.0
        benchmark.internal_target = 90.0
        benchmark.industry_standard = 110.0
        benchmark.peer_average = 95.0
        benchmark.best_in_class = 130.0
        benchmark.historical_baseline = 85.0
        
        # Calculate performance score
        score = benchmark.calculate_performance_score()
        
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 100.0)
        
    def test_arabic_support(self):
        """Test Arabic language support"""
        benchmark = self.create_test_benchmark()
        benchmark.benchmark_name_ar = 'مقارنة معيارية تجريبية'
        benchmark.rtl_display = 1
        benchmark.arabic_charts = 1
        benchmark.bilingual_reports = 1
        benchmark.arabic_fonts = 'Noto Sans Arabic'
        
        # Test validation with Arabic support
        benchmark.validate()
        
        self.assertTrue(benchmark.benchmark_name_ar)
        self.assertTrue(benchmark.rtl_display)
        self.assertEqual(benchmark.arabic_fonts, 'Noto Sans Arabic')
        
    def create_test_benchmark(self):
        """Helper method to create a test benchmark"""
        benchmark = frappe.new_doc('Benchmark Analysis')
        benchmark.benchmark_name = 'Test Benchmark'
        benchmark.benchmark_type = 'Industry Standard'
        benchmark.business_area = 'Financial Performance'
        benchmark.primary_kpi = 'TEST_KPI_001'
        return benchmark
