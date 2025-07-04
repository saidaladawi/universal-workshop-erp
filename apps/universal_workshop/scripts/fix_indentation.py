#!/usr/bin/env python3
"""
Universal Workshop - Indentation Fixer
Fixes indentation and spacing issues in Python files
"""

import os
import sys
from pathlib import Path


def fix_indentation(file_path):
	"""Fix indentation issues in a Python file"""
	try:
		with open(file_path, encoding="utf-8") as f:
			lines = f.readlines()

		fixed_lines = []
		for line in lines:
			# Convert tabs to spaces (4 spaces per tab)
			fixed_line = line.expandtabs(4)
			# Remove trailing whitespace
			fixed_line = fixed_line.rstrip() + "\n" if fixed_line.strip() else "\n"
			fixed_lines.append(fixed_line)

		# Remove final newline if it exists to avoid double newlines
		if fixed_lines and fixed_lines[-1] == "\n":
			fixed_lines[-1] = fixed_lines[-1].rstrip()

		with open(file_path, "w", encoding="utf-8") as f:
			f.writelines(fixed_lines)

		print(f"✓ Fixed {file_path}")
		return True

	except Exception as e:
		print(f"✗ Error fixing {file_path}: {e}")
		return False


def main():
	"""Main function"""
	# List of problematic files from the error output
	problematic_files = [
		"universal_workshop/license_management/doctype/license_audit_log/license_audit_log.py",
		"universal_workshop/parts_inventory/demand_forecasting.py",
		"universal_workshop/search_integration/customer_indexer.py",
		"universal_workshop/vehicle_management/api.py",
		"universal_workshop/vehicle_management/doctype/maintenance_alert/maintenance_alert.py",
		"universal_workshop/vehicle_management/doctype/vehicle/test_vin_decoder.py",
		"universal_workshop/workshop_management/doctype/service_order_labor/service_order_labor.py",
		"universal_workshop/workshop_management/doctype/workshop_onboarding_form/workshop_onboarding_form.py",
	]

	print("🔧 Fixing indentation issues...")
	print("=" * 50)

	fixed_count = 0
	for file_path in problematic_files:
		if os.path.exists(file_path):
			if fix_indentation(file_path):
				fixed_count += 1
		else:
			print(f"⚠️ File not found: {file_path}")

	print(f"\n✅ Fixed {fixed_count} files")

	# Also fix all Python files in the project
	print("\n🔄 Fixing all Python files...")
	for root, dirs, files in os.walk("universal_workshop"):
		for file in files:
			if file.endswith(".py"):
				file_path = os.path.join(root, file)
				if file_path not in problematic_files:  # Don't double-fix
					fix_indentation(file_path)


if __name__ == "__main__":
	main()
