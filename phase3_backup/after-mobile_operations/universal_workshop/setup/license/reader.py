# Copyright (c) 2025, Said Al-Adowi and contributors
# For license information, please see license.txt

"""
License File Reader Module
Handles reading and parsing of workshop license files
"""

import os
import json
import frappe
from frappe import _


def get_license_file_data():
    """Read license file data"""
    try:
        # Get bench path
        bench_path = frappe.utils.get_bench_path()
        license_file_path = os.path.join(bench_path, "licenses", "workshop_license.json")
        
        if os.path.exists(license_file_path):
            with open(license_file_path, 'r', encoding='utf-8') as f:
                license_data = json.load(f)
                return license_data
        
        return None
        
    except Exception as e:
        frappe.log_error(f"Error reading license file: {e}")
        return None


def get_license_file_path():
    """Get the full path to the license file"""
    try:
        bench_path = frappe.utils.get_bench_path()
        return os.path.join(bench_path, "licenses", "workshop_license.json")
    except Exception as e:
        frappe.log_error(f"Error getting license file path: {e}")
        return None


def license_file_exists():
    """Check if license file exists"""
    license_path = get_license_file_path()
    return license_path and os.path.exists(license_path)


def read_license_info(field=None):
    """Read specific field from license or all data"""
    license_data = get_license_file_data()
    
    if not license_data:
        return None
        
    if field:
        return license_data.get(field)
    
    return license_data
