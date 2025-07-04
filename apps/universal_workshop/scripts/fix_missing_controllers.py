#!/usr/bin/env python3
"""
Fix Missing DocType Controllers Script
Automatically creates missing Python controller files for Universal Workshop ERP DocTypes
"""

import os
import json
import frappe
from pathlib import Path


def get_missing_controllers():
    """Find all DocType directories that are missing Python controller files"""
    missing_files = []

    # Find all JSON files in doctype directories
    universal_workshop_path = Path("apps/universal_workshop")

    for json_file in universal_workshop_path.rglob("**/doctype/**/*.json"):
        # Skip test files and other non-DocType JSON files
        if json_file.name.startswith("test_") or "test" in json_file.parent.name:
            continue

        # Construct expected Python file path
        py_file = json_file.with_suffix(".py")

        if not py_file.exists():
            missing_files.append(
                {"json_file": json_file, "py_file": py_file, "doctype_name": json_file.stem}
            )

    return missing_files


def create_controller_template(doctype_name, class_name, module_name):
    """Create a basic Python controller template"""
    template = f'''# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class {class_name}(Document):
	# pylint: disable=no-member
	# Frappe framework dynamically adds DocType fields to Document class
	
	def validate(self):
		"""Validate {doctype_name} entry"""
		pass
'''
    return template


def get_class_name(doctype_name):
    """Convert DocType name to Python class name"""
    # Remove spaces and convert to PascalCase
    words = doctype_name.replace("_", " ").split()
    return "".join(word.capitalize() for word in words)


def create_init_file(directory):
    """Create __init__.py file if it doesn't exist"""
    init_file = directory / "__init__.py"
    if not init_file.exists():
        init_file.write_text(f"# {directory.name} DocType\n")


def fix_missing_controllers():
    """Main function to fix all missing controller files"""
    missing_files = get_missing_controllers()

    if not missing_files:
        print("✅ All DocType controllers are present!")
        return True

    print(f"🔧 Found {len(missing_files)} missing controller files:")

    for item in missing_files:
        py_file = item["py_file"]
        doctype_name = item["doctype_name"]

        print(f"  📝 Creating: {py_file}")

        # Ensure directory exists
        py_file.parent.mkdir(parents=True, exist_ok=True)

        # Create __init__.py in DocType directory
        create_init_file(py_file.parent)

        # Get class name
        class_name = get_class_name(doctype_name)

        # Create controller content
        controller_content = create_controller_template(
            doctype_name, class_name, str(py_file.parent.relative_to("apps"))
        )

        # Write the controller file
        py_file.write_text(controller_content)

        print(f"    ✅ Created {class_name} controller")

    print(f"\n🎉 Successfully created {len(missing_files)} missing controller files!")
    return True


def validate_json_files():
    """Validate all DocType JSON files for syntax errors"""
    print("🔍 Validating DocType JSON files...")

    universal_workshop_path = Path("apps/universal_workshop")
    errors = []

    for json_file in universal_workshop_path.rglob("**/doctype/**/*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"❌ {json_file}: {e}")
        except Exception as e:
            errors.append(f"❌ {json_file}: {e}")

    if errors:
        print(f"Found {len(errors)} JSON validation errors:")
        for error in errors:
            print(f"  {error}")
        return False
    else:
        print("✅ All DocType JSON files are valid!")
        return True


if __name__ == "__main__":
    print("🚀 Universal Workshop ERP - Missing Controllers Fix")
    print("=" * 50)

    # Change to bench directory
    os.chdir("/home/said/frappe-dev/frappe-bench")

    # Validate JSON files first
    if not validate_json_files():
        print("❌ Please fix JSON validation errors before proceeding")
        exit(1)

    # Fix missing controllers
    if fix_missing_controllers():
        print("\n🎯 Next steps:")
        print("1. Run: bench --site universal.local migrate")
        print("2. Test DocType creation and functionality")
        print("3. Commit changes to git")
    else:
        print("❌ Failed to fix missing controllers")
        exit(1)
