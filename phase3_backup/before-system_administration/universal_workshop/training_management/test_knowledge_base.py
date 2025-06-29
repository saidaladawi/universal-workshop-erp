# Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import unittest
import frappe
from frappe.utils import now_datetime
import json


class TestKnowledgeBase(unittest.TestCase):
    """Test suite for Knowledge Base and Documentation System"""

    def setUp(self):
        """Setup test data for knowledge base tests"""
        self.test_category_data = {
            "category_name_en": "Engine Maintenance",
            "category_name_ar": "صيانة المحرك",
            "description_en": "Engine maintenance procedures and guides",
            "description_ar": "إجراءات وأدلة صيانة المحرك",
            "is_active": 1,
            "sort_order": 1,
        }

        self.test_article_data = {
            "title_en": "Oil Change Procedure",
            "title_ar": "إجراء تغيير الزيت",
            "content_en": "Step-by-step oil change procedure for automotive engines",
            "content_ar": "إجراء تغيير الزيت خطوة بخطوة لمحركات السيارات",
            "excerpt_en": "Learn how to change engine oil properly",
            "excerpt_ar": "تعلم كيفية تغيير زيت المحرك بشكل صحيح",
            "status": "Published",
            "is_public": 1,
            "review_frequency": "Annually",
        }

    def tearDown(self):
        """Clean up test data"""
        frappe.db.rollback()

    def test_knowledge_base_category_creation(self):
        """Test knowledge base category creation with Arabic support"""
        category = frappe.new_doc("Knowledge Base Category")
        category.update(self.test_category_data)
        category.insert()

        # Verify category code generation
        self.assertTrue(category.category_code.startswith("CAT-"))

        # Verify Arabic content
        self.assertEqual(category.category_name_ar, "صيانة المحرك")

        # Test Arabic text detection
        self.assertTrue(category.contains_arabic_text(category.category_name_ar))

    def test_hierarchical_category_structure(self):
        """Test hierarchical category relationships"""
        # Create parent category
        parent_category = frappe.new_doc("Knowledge Base Category")
        parent_category.update(self.test_category_data)
        parent_category.insert()

        # Create child category
        child_category = frappe.new_doc("Knowledge Base Category")
        child_category.update(self.test_category_data)
        child_category.category_name_en = "Oil Change Procedures"
        child_category.category_name_ar = "إجراءات تغيير الزيت"
        child_category.parent_category = parent_category.name
        child_category.insert()

        # Verify hierarchy
        self.assertEqual(child_category.parent_category, parent_category.name)

        # Test circular dependency prevention
        parent_category.parent_category = child_category.name
        with self.assertRaises(frappe.ValidationError):
            parent_category.save()

    def test_knowledge_base_article_creation(self):
        """Test knowledge base article creation with multilingual content"""
        # Create category first
        category = frappe.new_doc("Knowledge Base Category")
        category.update(self.test_category_data)
        category.insert()

        # Create article
        article = frappe.new_doc("Knowledge Base Article")
        article.update(self.test_article_data)
        article.category = category.name
        article.insert()

        # Verify article code generation
        self.assertTrue(article.article_code.startswith("KB-"))

        # Verify translation status
        self.assertEqual(article.translation_status, "Complete")

        # Verify automatic excerpt generation
        if not article.excerpt_en and article.content_en:
            self.assertIsNotNone(article.excerpt_en)

    def test_article_workflow_status(self):
        """Test article workflow and status transitions"""
        category = frappe.new_doc("Knowledge Base Category")
        category.update(self.test_category_data)
        category.insert()

        article = frappe.new_doc("Knowledge Base Article")
        article.update(self.test_article_data)
        article.category = category.name
        article.status = "Draft"
        article.insert()

        # Test status transitions
        article.status = "In Review (EN)"
        article.save()
        self.assertEqual(article.status, "In Review (EN)")

        # Test publish functionality
        article.publish_article()
        article.reload()
        self.assertEqual(article.status, "Published")
        self.assertIsNotNone(article.published_date)

    def test_article_search_functionality(self):
        """Test multilingual article search"""
        from universal_workshop.training_management.doctype.knowledge_base_article.knowledge_base_article import (
            search_articles,
        )

        # Create category and article
        category = frappe.new_doc("Knowledge Base Category")
        category.update(self.test_category_data)
        category.insert()

        article = frappe.new_doc("Knowledge Base Article")
        article.update(self.test_article_data)
        article.category = category.name
        article.insert()

        # Test English search
        results_en = search_articles("oil change", "en")
        self.assertGreater(len(results_en), 0)

        # Test Arabic search
        results_ar = search_articles("تغيير الزيت", "ar")
        self.assertGreater(len(results_ar), 0)

        # Test category filtering
        results_category = search_articles("oil", "en", category=category.name)
        self.assertGreater(len(results_category), 0)

    def test_article_feedback_system(self):
        """Test article feedback and rating system"""
        category = frappe.new_doc("Knowledge Base Category")
        category.update(self.test_category_data)
        category.insert()

        article = frappe.new_doc("Knowledge Base Article")
        article.update(self.test_article_data)
        article.category = category.name
        article.insert()

        # Test feedback submission
        feedback_result = article.add_feedback(4, "Very helpful article")
        self.assertEqual(feedback_result["status"], "success")

        # Test rating update
        article.reload()
        self.assertGreater(article.helpfulness_rating, 0)

    def test_documentation_template_system(self):
        """Test documentation template creation and usage"""
        template = frappe.new_doc("Documentation Template")
        template.template_name = "Standard Procedure Template"
        template.template_name_ar = "قالب الإجراء المعياري"
        template.description = "Template for standard maintenance procedures"
        template.description_ar = "قالب لإجراءات الصيانة المعيارية"
        template.category = "Maintenance"
        template.is_active = 1

        # Add template sections
        template.append(
            "sections",
            {
                "section_title": "Overview",
                "section_title_ar": "نظرة عامة",
                "content_placeholder": "Provide procedure overview here",
                "content_placeholder_ar": "قدم نظرة عامة على الإجراء هنا",
                "is_required": 1,
                "sort_order": 1,
            },
        )

        template.append(
            "sections",
            {
                "section_title": "Tools Required",
                "section_title_ar": "الأدوات المطلوبة",
                "content_placeholder": "List required tools and equipment",
                "content_placeholder_ar": "اذكر الأدوات والمعدات المطلوبة",
                "is_required": 1,
                "sort_order": 2,
            },
        )

        template.insert()

        # Verify template creation
        self.assertEqual(template.template_name_ar, "قالب الإجراء المعياري")
        self.assertEqual(len(template.sections), 2)

    def test_article_view_tracking(self):
        """Test article view count tracking"""
        category = frappe.new_doc("Knowledge Base Category")
        category.update(self.test_category_data)
        category.insert()

        article = frappe.new_doc("Knowledge Base Article")
        article.update(self.test_article_data)
        article.category = category.name
        article.insert()

        # Test view increment
        initial_views = article.view_count or 0
        article.increment_view_count()
        article.reload()

        self.assertEqual(article.view_count, initial_views + 1)

    def test_article_review_scheduling(self):
        """Test article review date calculation"""
        category = frappe.new_doc("Knowledge Base Category")
        category.update(self.test_category_data)
        category.insert()

        article = frappe.new_doc("Knowledge Base Article")
        article.update(self.test_article_data)
        article.category = category.name
        article.review_frequency = "Quarterly"
        article.insert()

        # Test review date calculation
        next_review = article.calculate_next_review_date()
        self.assertIsNotNone(next_review)

    def test_multilingual_content_validation(self):
        """Test multilingual content validation"""
        category = frappe.new_doc("Knowledge Base Category")
        category.update(self.test_category_data)
        category.insert()

        # Test complete translation
        article1 = frappe.new_doc("Knowledge Base Article")
        article1.title_en = "Test Article"
        article1.title_ar = "مقال اختبار"
        article1.content_en = "Test content"
        article1.content_ar = "محتوى اختبار"
        article1.category = category.name
        article1.insert()

        self.assertEqual(article1.translation_status, "Complete")

        # Test partial translation
        article2 = frappe.new_doc("Knowledge Base Article")
        article2.title_en = "Test Article 2"
        article2.content_en = "Test content"
        article2.category = category.name
        article2.insert()

        self.assertEqual(article2.translation_status, "Partial")

    def test_featured_articles(self):
        """Test featured articles functionality"""
        from universal_workshop.training_management.doctype.knowledge_base_article.knowledge_base_article import (
            get_featured_articles,
        )

        # Create category and featured article
        category = frappe.new_doc("Knowledge Base Category")
        category.update(self.test_category_data)
        category.insert()

        article = frappe.new_doc("Knowledge Base Article")
        article.update(self.test_article_data)
        article.category = category.name
        article.is_featured = 1
        article.insert()

        # Test featured articles retrieval
        featured_en = get_featured_articles("en")
        self.assertGreater(len(featured_en), 0)

        featured_ar = get_featured_articles("ar")
        self.assertGreater(len(featured_ar), 0)

    def test_article_content_retrieval(self):
        """Test article content retrieval by language"""
        category = frappe.new_doc("Knowledge Base Category")
        category.update(self.test_category_data)
        category.insert()

        article = frappe.new_doc("Knowledge Base Article")
        article.update(self.test_article_data)
        article.category = category.name
        article.insert()

        # Test English content retrieval
        content_en = article.get_article_content("en")
        self.assertEqual(content_en["title"], article.title_en)
        self.assertEqual(content_en["content"], article.content_en)

        # Test Arabic content retrieval
        content_ar = article.get_article_content("ar")
        self.assertEqual(content_ar["title"], article.title_ar)
        self.assertEqual(content_ar["content"], article.content_ar)

    def test_category_tree_navigation(self):
        """Test category tree navigation functionality"""
        from universal_workshop.training_management.doctype.knowledge_base_category.knowledge_base_category import (
            get_category_tree,
        )

        # Create parent category
        parent = frappe.new_doc("Knowledge Base Category")
        parent.update(self.test_category_data)
        parent.insert()

        # Create child categories
        child1 = frappe.new_doc("Knowledge Base Category")
        child1.category_name_en = "Oil Changes"
        child1.category_name_ar = "تغيير الزيت"
        child1.parent_category = parent.name
        child1.insert()

        child2 = frappe.new_doc("Knowledge Base Category")
        child2.category_name_en = "Filter Replacement"
        child2.category_name_ar = "استبدال المرشح"
        child2.parent_category = parent.name
        child2.insert()

        # Test tree retrieval
        tree = get_category_tree()
        self.assertIsInstance(tree, list)
        self.assertGreater(len(tree), 0)

    def test_arabic_excerpt_generation(self):
        """Test automatic excerpt generation for Arabic content"""
        category = frappe.new_doc("Knowledge Base Category")
        category.update(self.test_category_data)
        category.insert()

        article = frappe.new_doc("Knowledge Base Article")
        article.title_en = "Arabic Content Test"
        article.title_ar = "اختبار المحتوى العربي"
        article.content_ar = "هذا محتوى عربي طويل جداً يجب أن يتم اقتطاع منه مقطع تلقائياً. " * 10
        article.category = category.name
        article.insert()

        # Verify Arabic excerpt was generated
        self.assertIsNotNone(article.excerpt_ar)
        self.assertLess(len(article.excerpt_ar), len(article.content_ar))


if __name__ == "__main__":
    unittest.main()
