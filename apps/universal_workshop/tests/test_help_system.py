#!/usr/bin/env python3

import frappe
import json

def test_help_system():
    """Test the contextual help system functionality"""

    # Initialize site
    frappe.init(site='universal.local')
    frappe.connect()

    print("Testing Contextual Help System...")
    print("=" * 50)

    # Test 1: Check if Help Content DocType exists
    try:
        help_content_meta = frappe.get_meta("Help Content")
        print("✓ Help Content DocType exists")
        print(f"  Fields: {len(help_content_meta.fields)} fields defined")
    except Exception as e:
        print(f"✗ Help Content DocType not found: {e}")
        return False

    # Test 2: Create sample help content
    try:
        from universal_workshop.training_management.help_content_samples import create_sample_help_content
        create_sample_help_content()
        print("✓ Sample help content creation completed")
    except Exception as e:
        print(f"✗ Error creating sample content: {e}")

    # Test 3: Check help content records
    try:
        help_records = frappe.get_all("Help Content",
                                    fields=["name", "title", "content_key", "help_type"],
                                    limit=5)
        print(f"✓ Found {len(help_records)} help content records")
        for record in help_records:
            print(f"  - {record.title} ({record.content_key})")
    except Exception as e:
        print(f"✗ Error fetching help records: {e}")

    # Test 4: Test API endpoints
    try:
        # Test context detection
        context_result = frappe.call("universal_workshop.training_management.api.contextual_help.get_contextual_help",
                                   route="/app/training-module")
        print("✓ Context detection API working")
        print(f"  Found {len(context_result.get('content', []))} contextual help items")

        # Test search functionality
        search_result = frappe.call("universal_workshop.training_management.api.contextual_help.search_help_content",
                                  query="training")
        print("✓ Help search API working")
        print(f"  Found {len(search_result.get('results', []))} search results")

    except Exception as e:
        print(f"✗ API testing failed: {e}")

    # Test 5: Check JavaScript file exists
    import os
    js_file = "/home/said/frappe-dev/frappe-bench/apps/universal_workshop/universal_workshop/public/js/contextual_help.js"
    if os.path.exists(js_file):
        print("✓ Contextual help JavaScript file exists")
        with open(js_file, 'r') as f:
            content = f.read()
            print(f"  File size: {len(content)} characters")
    else:
        print("✗ Contextual help JavaScript file missing")

    print("\nContextual Help System Test Complete!")
    frappe.destroy()
    return True

if __name__ == "__main__":
    test_help_system()
