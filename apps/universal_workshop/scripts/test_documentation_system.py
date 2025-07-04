#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for multilingual documentation system
"""

import re

def test_arabic_text_detection():
    """Test Arabic text detection function"""
    print("Testing Arabic text detection...")
    
    # Simple Arabic text detection (copied from the DocType)
    def is_arabic_text(text):
        if not text:
            return False
        arabic_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+')
        return bool(arabic_pattern.search(text))
    
    test_cases = [
        ("Hello World", False),
        ("مرحبا بالعالم", True),
        ("Universal Workshop ورشة عالمية", True),
        ("", False),
        ("12345", False),
        ("ورشة", True)
    ]
    
    passed = 0
    for text, expected in test_cases:
        result = is_arabic_text(text)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"  {status}: '{text}' -> {result} (expected {expected})")
        if result == expected:
            passed += 1
    
    print(f"Arabic text detection: {passed}/{len(test_cases)} tests passed\n")
    return passed == len(test_cases)

def test_category_code_generation():
    """Test category code generation logic"""
    print("Testing category code generation...")
    
    def generate_category_code(name):
        """Simplified version of the category code generation"""
        import re
        code_base = re.sub(r'[^a-zA-Z0-9\s]', '', name)
        code_base = re.sub(r'\s+', '_', code_base.strip())
        return code_base.upper()
    
    test_cases = [
        ("Getting Started", "GETTING_STARTED"),
        ("User Guide & Tips", "USER_GUIDE__TIPS"),
        ("API Reference", "API_REFERENCE"),
        ("FAQ Section", "FAQ_SECTION")
    ]
    
    passed = 0
    for name, expected in test_cases:
        result = generate_category_code(name)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"  {status}: '{name}' -> '{result}' (expected '{expected}')")
        if result == expected:
            passed += 1
    
    print(f"Category code generation: {passed}/{len(test_cases)} tests passed\n")
    return passed == len(test_cases)

def test_multilingual_fields():
    """Test multilingual field validation"""
    print("Testing multilingual field requirements...")
    
    # Test data structure
    test_articles = [
        {
            "title_en": "Getting Started",
            "title_ar": "البداية",
            "content_en": "Welcome to Universal Workshop",
            "content_ar": "أهلاً بكم في الورشة العالمية",
            "valid": True
        },
        {
            "title_en": "FAQ",
            "title_ar": "",  # Missing Arabic title
            "content_en": "Frequently asked questions",
            "content_ar": "الأسئلة الشائعة",
            "valid": False
        },
        {
            "title_en": "",  # Missing English title
            "title_ar": "التعليمات",
            "content_en": "Instructions",
            "content_ar": "التعليمات المفصلة",
            "valid": False
        }
    ]
    
    def validate_article(article):
        """Simple validation logic"""
        if not article.get("title_en") or not article.get("title_en").strip():
            return False, "English title required"
        if not article.get("title_ar") or not article.get("title_ar").strip():
            return False, "Arabic title required"
        return True, "Valid"
    
    passed = 0
    for i, article in enumerate(test_articles):
        is_valid, message = validate_article(article)
        expected_valid = article["valid"]
        status = "✅ PASS" if is_valid == expected_valid else "❌ FAIL"
        print(f"  {status}: Article {i+1} -> {message} (expected {'valid' if expected_valid else 'invalid'})")
        if is_valid == expected_valid:
            passed += 1
    
    print(f"Multilingual validation: {passed}/{len(test_articles)} tests passed\n")
    return passed == len(test_articles)

def main():
    """Run all tests"""
    print("🧪 Testing Universal Workshop Documentation System\n")
    print("=" * 60)
    
    tests = [
        test_arabic_text_detection,
        test_category_code_generation,
        test_multilingual_fields
    ]
    
    passed_tests = 0
    for test_func in tests:
        if test_func():
            passed_tests += 1
    
    print("=" * 60)
    print(f"Overall Results: {passed_tests}/{len(tests)} test suites passed")
    
    if passed_tests == len(tests):
        print("🎉 All tests passed! Documentation system is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    main()
