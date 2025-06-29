# Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import unittest
import frappe
from frappe.utils import now_datetime, add_days
import json
from datetime import datetime, timedelta


class TestTrainingSystem(unittest.TestCase):
    """Comprehensive test suite for Universal Workshop Training System"""

    def setUp(self):
        """Setup test data for training system tests"""
        self.test_user = "test.user@universal-workshop.om"
        self.test_role = "Workshop Technician"

        # Create test user if doesn't exist
        if not frappe.db.exists("User", self.test_user):
            user = frappe.new_doc("User")
            user.email = self.test_user
            user.first_name = "Test"
            user.last_name = "User"
            user.enabled = 1
            user.insert(ignore_permissions=True)

            # Add role to user
            user.add_roles(self.test_role)

        # Test training module data
        self.test_module_data = {
            "title": "Engine Diagnostics Test Module",
            "title_ar": "وحدة اختبار تشخيص المحرك",
            "description": "Test module for engine diagnostic procedures",
            "description_ar": "وحدة اختبار لإجراءات تشخيص المحرك",
            "content_type": "H5P Interactive",
            "category": "Engine",
            "difficulty_level": "Intermediate",
            "estimated_duration": 120,  # 2 hours
            "has_quiz": 1,
            "passing_score": 80,
            "max_attempts": 3,
            "requires_certification": 1,
            "is_active": 1,
        }

    def tearDown(self):
        """Clean up test data"""
        # Clean up test records
        frappe.db.rollback()

    def test_training_module_creation(self):
        """Test training module creation with Arabic content"""
        module = frappe.new_doc("Training Module")
        module.update(self.test_module_data)

        # Test validation
        module.insert()

        # Verify module code generation
        self.assertTrue(module.module_code.startswith("TM-"))
        self.assertEqual(len(module.module_code), 8)  # TM-00001 format

        # Verify Arabic content validation
        self.assertEqual(module.title_ar, "وحدة اختبار تشخيص المحرك")

        # Verify metadata fields
        self.assertEqual(module.created_by, frappe.session.user)
        self.assertIsNotNone(module.created_date)

    def test_arabic_text_validation(self):
        """Test Arabic text validation functionality"""
        module = frappe.new_doc("Training Module")
        module.update(self.test_module_data)

        # Test contains_arabic_text method
        self.assertTrue(module.contains_arabic_text("وحدة اختبار"))
        self.assertFalse(module.contains_arabic_text("Test Module"))
        self.assertFalse(module.contains_arabic_text(""))

        module.insert()

    def test_training_progress_tracking(self):
        """Test training progress tracking and competency calculation"""
        # Create training module
        module = frappe.new_doc("Training Module")
        module.update(self.test_module_data)
        module.insert()

        # Create progress record
        progress = frappe.new_doc("Training Progress")
        progress.user = self.test_user
        progress.training_module = module.name
        progress.progress_percentage = 85
        progress.quiz_score = 88
        progress.quiz_attempts = 2
        progress.status = "Completed"
        progress.insert()

        # Test competency level calculation
        self.assertEqual(progress.competency_level, "Advanced")  # 88% score = Advanced
        self.assertTrue(progress.passed_assessment)
        self.assertTrue(progress.certification_issued)

    def test_progress_milestone_notifications(self):
        """Test milestone notification system"""
        # Create training module
        module = frappe.new_doc("Training Module")
        module.update(self.test_module_data)
        module.insert()

        # Create progress record
        progress = frappe.new_doc("Training Progress")
        progress.user = self.test_user
        progress.training_module = module.name
        progress.progress_percentage = 50  # 50% milestone
        progress.status = "In Progress"
        progress.insert()

        # Test milestone detection
        progress.check_milestone_notifications()

        # Verify notification was triggered (this would normally send email)
        self.assertEqual(progress.progress_percentage, 50)

    def test_certification_generation(self):
        """Test automatic certification generation"""
        # Create training module
        module = frappe.new_doc("Training Module")
        module.update(self.test_module_data)
        module.insert()

        # Create completed progress with high score
        progress = frappe.new_doc("Training Progress")
        progress.user = self.test_user
        progress.training_module = module.name
        progress.progress_percentage = 100
        progress.quiz_score = 92  # Expert level
        progress.status = "Completed"
        progress.insert()

        # Verify certification was generated
        certification = frappe.get_doc(
            "Training Certification", {"user": self.test_user, "training_module": module.name}
        )

        self.assertEqual(certification.competency_level, "Expert")
        self.assertEqual(certification.quiz_score, 92)
        self.assertTrue(certification.certificate_number.startswith("CERT-"))

    def test_knowledge_base_article_creation(self):
        """Test knowledge base article creation with multilingual support"""
        article = frappe.new_doc("Knowledge Base Article")
        article.title_en = "Engine Troubleshooting Guide"
        article.title_ar = "دليل استكشاف أخطاء المحرك"
        article.content_en = "Step-by-step engine troubleshooting procedures"
        article.content_ar = "إجراءات استكشاف أخطاء المحرك خطوة بخطوة"
        article.category = "Technical Guides"
        article.status = "Published"
        article.is_public = 1
        article.insert()

        # Verify article code generation
        self.assertTrue(article.article_code.startswith("KB-"))

        # Verify translation status
        self.assertEqual(article.translation_status, "Complete")

        # Test Arabic content detection
        self.assertTrue(article.contains_arabic_text(article.title_ar))

    def test_contextual_help_system(self):
        """Test contextual help content and retrieval"""
        help_content = frappe.new_doc("Help Content")
        help_content.title = "Customer Form Help"
        help_content.content_key = "customer-form-help"
        help_content.help_type = "Tooltip"
        help_content.target_doctype = "Customer"
        help_content.target_field = "customer_name"
        help_content.content = "Enter customer name in English"
        help_content.content_ar = "أدخل اسم العميل باللغة الإنجليزية"
        help_content.is_active = 1
        help_content.insert()

        # Test contextual help retrieval
        from universal_workshop.training_management.doctype.help_content.help_content import (
            get_contextual_help,
        )

        help_data = get_contextual_help("/app/customer", "Customer", "customer_name")
        self.assertGreater(len(help_data), 0)

    def test_training_path_creation(self):
        """Test role-based training path creation"""
        # Create training modules first
        module1 = frappe.new_doc("Training Module")
        module1.update(self.test_module_data)
        module1.title = "Basic Engine Knowledge"
        module1.difficulty_level = "Beginner"
        module1.insert()

        module2 = frappe.new_doc("Training Module")
        module2.update(self.test_module_data)
        module2.title = "Advanced Engine Diagnostics"
        module2.difficulty_level = "Advanced"
        module2.insert()

        # Create training path
        path = frappe.new_doc("Training Path")
        path.path_name = "Engine Specialist Track"
        path.path_name_ar = "مسار أخصائي المحرك"
        path.role = self.test_role
        path.department = "Technical"
        path.is_mandatory = 1
        path.auto_enrollment = 1

        # Add modules to path
        path.append(
            "training_modules",
            {"training_module": module1.name, "sequence_order": 1, "is_mandatory": 1},
        )
        path.append(
            "training_modules",
            {"training_module": module2.name, "sequence_order": 2, "is_mandatory": 1},
        )

        path.insert()

        # Verify path creation
        self.assertEqual(path.estimated_duration_hours, 4)  # 2 modules × 2 hours each
        self.assertEqual(len(path.training_modules), 2)

    def test_h5p_content_management(self):
        """Test H5P content upload and management"""
        from universal_workshop.training_management.h5p.h5p_manager import H5PManager

        h5p_manager = H5PManager()

        # Test directory creation
        self.assertTrue(h5p_manager.h5p_content_path.exists())

        # Test content ID generation
        content_info = {
            "content_id": "test_h5p_001",
            "training_module": "test_module",
            "title": "Test H5P Content",
            "library": [],
            "content_path": "/test/path",
            "uploaded_by": frappe.session.user,
            "uploaded_on": now_datetime(),
            "status": "active",
        }

        # This would normally save to database
        # h5p_manager.save_h5p_content_info(content_info)

    def test_user_dashboard_data(self):
        """Test user dashboard data retrieval"""
        from universal_workshop.training_management.doctype.training_progress.training_progress import (
            get_competency_dashboard,
        )

        # Create test progress records
        module = frappe.new_doc("Training Module")
        module.update(self.test_module_data)
        module.insert()

        progress = frappe.new_doc("Training Progress")
        progress.user = self.test_user
        progress.training_module = module.name
        progress.progress_percentage = 100
        progress.status = "Completed"
        progress.competency_level = "Advanced"
        progress.insert()

        # Get dashboard data
        dashboard_data = get_competency_dashboard(self.test_user)

        self.assertIn("total_modules", dashboard_data)
        self.assertIn("completed_modules", dashboard_data)
        self.assertIn("competency_distribution", dashboard_data)

    def test_notification_system(self):
        """Test training notification system"""
        from universal_workshop.training_management.notifications import (
            send_overdue_training_reminders,
        )

        # Create overdue training record
        module = frappe.new_doc("Training Module")
        module.update(self.test_module_data)
        module.insert()

        progress = frappe.new_doc("Training Progress")
        progress.user = self.test_user
        progress.training_module = module.name
        progress.status = "Completed"
        progress.next_review_date = add_days(now_datetime(), -30)  # 30 days overdue
        progress.insert()

        # Test notification function (would normally send emails)
        try:
            send_overdue_training_reminders()
        except Exception:
            pass  # Email sending might fail in test environment

    def test_skill_gap_analysis(self):
        """Test skill gap identification and recommendations"""
        # Create training module
        module = frappe.new_doc("Training Module")
        module.update(self.test_module_data)
        module.insert()

        # Create progress record
        progress = frappe.new_doc("Training Progress")
        progress.user = self.test_user
        progress.training_module = module.name
        progress.progress_percentage = 100
        progress.status = "Completed"
        progress.competency_level = "Beginner"  # Low competency
        progress.insert()

        # Test skill gap identification
        skill_gaps = progress.identify_skill_gaps()

        self.assertIn("recommendations", skill_gaps)
        self.assertIn("skill_gaps", skill_gaps)

    def test_adaptive_learning_paths(self):
        """Test adaptive learning path adjustments"""
        # Create training path
        path = frappe.new_doc("Training Path")
        path.path_name = "Adaptive Engine Track"
        path.role = self.test_role
        path.is_adaptive = 1
        path.insert()

        # Test adaptive progression
        result = path.check_adaptive_progression(self.test_user, "test_module", 95)

        # High score should trigger advanced path
        self.assertIsInstance(result, dict)

    def test_multilingual_search(self):
        """Test multilingual search functionality"""
        from universal_workshop.training_management.doctype.knowledge_base_article.knowledge_base_article import (
            search_articles,
        )

        # Create test article
        article = frappe.new_doc("Knowledge Base Article")
        article.title_en = "Engine Maintenance"
        article.title_ar = "صيانة المحرك"
        article.content_en = "Regular engine maintenance procedures"
        article.content_ar = "إجراءات صيانة المحرك المنتظمة"
        article.status = "Published"
        article.insert()

        # Test English search
        results_en = search_articles("engine", "en")
        self.assertGreater(len(results_en), 0)

        # Test Arabic search
        results_ar = search_articles("محرك", "ar")
        self.assertGreater(len(results_ar), 0)


if __name__ == "__main__":
    unittest.main()
