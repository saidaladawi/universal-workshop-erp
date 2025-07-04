#!/usr/bin/env python3
"""
Test script for Training Module implementation
Tests DocType creation, validation, and API functionality
"""

import sys
import os
import json
from pathlib import Path

# Add the bench directory to Python path
bench_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(bench_path))

try:
    import frappe
    from frappe.test_runner import make_test_records

    def init_frappe():
        """Initialize Frappe environment"""
        frappe.init(site="universal.local")
        frappe.connect()

    def test_training_module_creation():
        """Test basic training module creation"""
        print("Testing Training Module creation...")

        try:
            # Test data for training module
            test_data = {
                "doctype": "Training Module",
                "title": "Engine Diagnostics Basics",
                "title_ar": "أساسيات تشخيص المحرك",
                "description": "Learn basic engine diagnostic procedures",
                "description_ar": "تعلم إجراءات تشخيص المحرك الأساسية",
                "content_type": "Video Tutorial",
                "video_url": "https://www.youtube.com/watch?v=test123",
                "estimated_duration": 30,
                "difficulty_level": "Beginner",
                "target_roles": "Workshop Technician\nMaintenance Staff",
                "has_quiz": 1,
                "passing_score": 70,
                "max_attempts": 3,
                "quiz_questions": json.dumps(
                    [
                        {
                            "question": "What is the first step in engine diagnosis?",
                            "options": ["Visual inspection", "Start engine", "Check fluids"],
                            "correct": 0,
                        }
                    ]
                ),
            }

            # Create training module
            doc = frappe.new_doc("Training Module")
            doc.update(test_data)
            doc.insert()

            print(f"✅ Training Module created successfully: {doc.name}")
            print(f"   Module Code: {doc.module_code}")
            print(f"   Title (EN): {doc.title}")
            print(f"   Title (AR): {doc.title_ar}")

            return doc

        except Exception as e:
            print(f"❌ Error creating Training Module: {str(e)}")
            return None

    def test_arabic_validation():
        """Test Arabic text validation"""
        print("\nTesting Arabic validation...")

        try:
            from universal_workshop.training_management.doctype.training_module.training_module import (
                TrainingModule,
            )

            module = TrainingModule()

            # Test Arabic text detection
            arabic_text = "تشخيص المحرك"
            english_text = "Engine Diagnostics"
            mixed_text = "Engine تشخيص"

            assert module.contains_arabic_text(arabic_text) == True
            assert module.contains_arabic_text(english_text) == False
            assert module.contains_arabic_text(mixed_text) == True

            print("✅ Arabic text validation working correctly")

        except Exception as e:
            print(f"❌ Error in Arabic validation: {str(e)}")

    def test_video_url_validation():
        """Test video URL validation"""
        print("\nTesting video URL validation...")

        try:
            from universal_workshop.training_management.doctype.training_module.training_module import (
                TrainingModule,
            )

            module = TrainingModule()

            # Test valid URLs
            valid_urls = [
                "https://www.youtube.com/watch?v=test123",
                "https://vimeo.com/123456",
                "https://example.com/video.mp4",
            ]

            # Test invalid URLs
            invalid_urls = [
                "not_a_url",
                "https://example.com/document.pdf",
                "ftp://example.com/video.mp4",
            ]

            for url in valid_urls:
                assert module.is_valid_video_url(url) == True

            for url in invalid_urls:
                assert module.is_valid_video_url(url) == False

            print("✅ Video URL validation working correctly")

        except Exception as e:
            print(f"❌ Error in video URL validation: {str(e)}")

    def test_module_code_generation():
        """Test automatic module code generation"""
        print("\nTesting module code generation...")

        try:
            from universal_workshop.training_management.doctype.training_module.training_module import (
                TrainingModule,
            )

            module = TrainingModule()
            code = module.generate_module_code()

            # Verify format TM-00001
            import re

            assert re.match(r"^TM-\d{5}$", code)

            print(f"✅ Module code generation working: {code}")

        except Exception as e:
            print(f"❌ Error in module code generation: {str(e)}")

    def test_h5p_integration():
        """Test H5P integration components"""
        print("\nTesting H5P integration...")

        try:
            from universal_workshop.training_management.h5p.h5p_manager import H5PManager

            manager = H5PManager()

            # Test content validation
            test_path = "/tmp/test.h5p"
            result = manager.validate_h5p_file(test_path)

            print("✅ H5P Manager initialized successfully")
            print(f"   Validation result for non-existent file: {result}")

        except Exception as e:
            print(f"❌ Error in H5P integration: {str(e)}")

    def run_all_tests():
        """Run all training module tests"""
        print("=" * 50)
        print("TRAINING MODULE IMPLEMENTATION TEST")
        print("=" * 50)

        init_frappe()

        # Run tests
        test_training_module_creation()
        test_arabic_validation()
        test_video_url_validation()
        test_module_code_generation()
        test_h5p_integration()

        print("\n" + "=" * 50)
        print("TEST SUMMARY COMPLETE")
        print("=" * 50)

        frappe.destroy()

    if __name__ == "__main__":
        run_all_tests()

except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this from the bench directory")
    sys.exit(1)
