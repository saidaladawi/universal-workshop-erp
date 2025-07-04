#!/usr/bin/env python3
"""
Universal Workshop - Technician.py Error Fixer
Fixes specific issues in technician.py related to Frappe framework patterns
Author: Eng. Saeed Al-Adawi
"""

import re
from pathlib import Path


def fix_technician_file():
    """Fix specific issues in technician.py"""
    technician_file = Path("universal_workshop/workshop_management/doctype/technician/technician.py")
    
    if not technician_file.exists():
        print(f"❌ File not found: {technician_file}")
        return
    
    print(f"🔧 Fixing technician.py...")
    
    try:
        content = technician_file.read_text(encoding="utf-8")
        original_content = content
        
        # 1. Remove unused imports
        content = re.sub(r'from frappe\.utils import cint, flt, getdate, now_datetime', 
                        'from frappe.utils import flt, now_datetime', content)
        
        # 2. Fix SQL query tuple access issues
        # Replace [0][0] with safer access pattern
        content = re.sub(
            r'frappe\.db\.sql\(\s*"""([^"]+)""",\s*\[([^\]]+)\],?\s*\)\[0\]\[0\]',
            r'frappe.db.sql("""\1""", [\2], as_list=True)[0][0] if frappe.db.sql("""\1""", [\2], as_list=True) else 0',
            content
        )
        
        # 3. Fix the workload calculation query
        old_workload_query = '''current_workload = (
			frappe.db.sql(
				"""
            SELECT COALESCE(SUM(estimated_hours - completed_hours), 0)
            FROM `tabService Order`
            WHERE assigned_technician = %s
            AND status IN ('Assigned', 'In Progress')
        """,
				[self.name],
			)[0][0]
			or 0
		)'''
        
        new_workload_query = '''current_workload_result = frappe.db.sql(
			"""
			SELECT COALESCE(SUM(estimated_hours - completed_hours), 0)
			FROM `tabService Order`
			WHERE assigned_technician = %s
			AND status IN ('Assigned', 'In Progress')
			""",
			[self.name],
			as_list=True
		)
		current_workload = current_workload_result[0][0] if current_workload_result else 0'''
        
        content = content.replace(old_workload_query, new_workload_query)
        
        # 4. Fix average time calculation
        old_avg_query = '''avg_time = (
				frappe.db.sql(
					"""
                SELECT AVG(completed_hours)
                FROM `tabService Order`
                WHERE assigned_technician = %s
                AND status = 'Completed'
                AND completed_hours > 0
            """,
					[self.name],
				)[0][0]
				or 0
			)'''
        
        new_avg_query = '''avg_time_result = frappe.db.sql(
				"""
				SELECT AVG(completed_hours)
				FROM `tabService Order`
				WHERE assigned_technician = %s
				AND status = 'Completed'
				AND completed_hours > 0
				""",
				[self.name],
				as_list=True
			)
			avg_time = avg_time_result[0][0] if avg_time_result else 0'''
        
        content = content.replace(old_avg_query, new_avg_query)
        
        # 5. Fix last assignment query
        old_last_query = '''last_assignment = frappe.db.sql(
			"""
            SELECT MAX(creation)
            FROM `tabService Order`
            WHERE assigned_technician = %s
        """,
			[self.name],
		)[0][0]'''
        
        new_last_query = '''last_assignment_result = frappe.db.sql(
			"""
			SELECT MAX(creation)
			FROM `tabService Order`
			WHERE assigned_technician = %s
			""",
			[self.name],
			as_list=True
		)
		last_assignment = last_assignment_result[0][0] if last_assignment_result else None'''
        
        content = content.replace(old_last_query, new_last_query)
        
        # 6. Add type hints comment to suppress pylint warnings
        type_hints_comment = '''# Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt
# pylint: disable=no-member
# Frappe framework dynamically adds DocType fields to Document class

'''
        
        # Replace the existing copyright header
        content = re.sub(
            r'^# Copyright.*?# For license information.*?\n\n',
            type_hints_comment,
            content,
            flags=re.MULTILINE | re.DOTALL
        )
        
        # 7. Fix long lines by splitting them
        # Split the workload ratio calculation
        content = re.sub(
            r'workload_ratio = self\.current_workload_hours / \(self\.capacity_hours_per_day \* 5\)  # 5 working days',
            '''# Calculate workload ratio (5 working days)
		daily_capacity = self.capacity_hours_per_day * 5
		workload_ratio = self.current_workload_hours / daily_capacity''',
            content
        )
        
        # 8. Fix performance multiplier calculation
        content = re.sub(
            r'performance_multiplier = \(\s*\(self\.performance_rating or 3\) \+ \(self\.efficiency_rating or 3\) \+ \(self\.quality_rating or 3\)\s*\) / 15',
            '''# Calculate performance multiplier from ratings
		total_ratings = (
			(self.performance_rating or 3) + 
			(self.efficiency_rating or 3) + 
			(self.quality_rating or 3)
		)
		performance_multiplier = total_ratings / 15''',
            content
        )
        
        # Write the fixed content
        if content != original_content:
            technician_file.write_text(content, encoding="utf-8")
            print("✅ Fixed technician.py successfully!")
            print("   - Removed unused imports")
            print("   - Fixed SQL query tuple access")
            print("   - Added pylint suppressions")
            print("   - Split long lines")
            print("   - Improved error handling")
        else:
            print("ℹ️  No changes needed in technician.py")
            
    except Exception as e:
        print(f"❌ Error fixing technician.py: {e}")


if __name__ == "__main__":
    fix_technician_file() 