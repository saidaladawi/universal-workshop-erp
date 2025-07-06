#!/usr/bin/env python3
"""
DocType Migration Script for Universal Workshop Consolidation
Executes the actual migration of DocTypes from legacy modules to consolidated modules
"""

import os
import shutil
from pathlib import Path

BASE_PATH = "/home/said/frappe-dev/frappe-bench/apps/universal_workshop/universal_workshop"

# Migration mappings based on consolidation plans
MIGRATIONS = {
    # Inventory Management Consolidation
    "inventory_management": {
        "from_parts_inventory": [
            # DocTypes to copy from parts_inventory
        ],
        "from_scrap_management": [
            "disassembly_plan",
            "disassembly_step", 
            "dismantling_work_order",
            "extracted_parts",
            "inventory_movement",
            "part_movement_history",
            "part_photo",
            "part_quality_assessment",
            "part_storage_location",
            "parts_condition_grade",
            "parts_grade_applicable_category",
            "parts_grade_history",
            "profit_analysis",
            "sales_channel",
            "scrap_vehicle",
            "scrap_vehicle_assessment_item",
            "scrap_vehicle_document",
            "scrap_vehicle_extracted_part",
            "scrap_vehicle_part_assessment",
            "scrap_vehicle_photo",
            "storage_location",
            "storage_zone",
            "storage_zone_allowed_category",
            "vehicle_dismantling_bom",
            "vehicle_dismantling_extractable_part",
            "vehicle_dismantling_operation"
        ],
        "from_marketplace_integration": [
            # DocTypes to copy from marketplace_integration  
        ]
    }
}

def migrate_doctype(source_module, doctype_name, target_module, target_subdir="doctype"):
    """Migrate a single DocType from source to target module"""
    source_path = Path(BASE_PATH) / source_module / "doctype" / doctype_name
    target_path = Path(BASE_PATH) / target_module / target_subdir / doctype_name
    
    if source_path.exists():
        print(f"Migrating {doctype_name} from {source_module} to {target_module}/{target_subdir}")
        
        # Create target directory if it doesn't exist
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy the entire DocType folder
        shutil.copytree(source_path, target_path, dirs_exist_ok=True)
        return True
    else:
        print(f"WARNING: DocType {doctype_name} not found in {source_module}")
        return False

def main():
    """Execute all DocType migrations"""
    print("Starting DocType migrations...")
    
    # Migrate inventory_management DocTypes
    print("\n=== Migrating Inventory Management DocTypes ===")
    
    # Create subdirectories for organization
    inv_subdirs = [
        "inventory_core",
        "scrap_dismantling_operations", 
        "marketplace_sales_integration",
        "arabic_parts_database",
        "traditional_supplier_management"
    ]
    
    for subdir in inv_subdirs:
        Path(BASE_PATH, "inventory_management", subdir).mkdir(parents=True, exist_ok=True)
    
    # Migrate scrap_management DocTypes
    scrap_to_inventory_mapping = {
        "disassembly_plan": "scrap_dismantling_operations",
        "disassembly_step": "scrap_dismantling_operations",
        "dismantling_work_order": "scrap_dismantling_operations",
        "extracted_parts": "scrap_dismantling_operations",
        "inventory_movement": "inventory_core",
        "part_movement_history": "inventory_core",
        "part_photo": "scrap_dismantling_operations",
        "part_quality_assessment": "scrap_dismantling_operations",
        "part_storage_location": "scrap_dismantling_operations",
        "parts_condition_grade": "scrap_dismantling_operations",
        "profit_analysis": "marketplace_sales_integration",
        "sales_channel": "marketplace_sales_integration",
        "scrap_vehicle": "scrap_dismantling_operations",
        "storage_zone": "scrap_dismantling_operations",
        "vehicle_dismantling_bom": "scrap_dismantling_operations"
    }
    
    for doctype, target_subdir in scrap_to_inventory_mapping.items():
        migrate_doctype("scrap_management", doctype, "inventory_management", target_subdir)
    
    print("\nMigration complete!")

if __name__ == "__main__":
    main()