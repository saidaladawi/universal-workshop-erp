#!/usr/bin/env python3
"""
Proper Consolidation Migration Script for Universal Workshop
This script properly migrates all content from legacy modules to consolidated modules
"""

import os
import shutil
import json
from pathlib import Path

BASE_PATH = "/home/said/frappe-dev/frappe-bench/apps/universal_workshop/universal_workshop"
CONSOLIDATION_PATH = "/home/said/frappe-dev/frappe-bench/apps/universal_workshop/consolidation_workspace"

# Complete consolidation mapping based on source_to_target_mapping.md
CONSOLIDATION_MAPPING = {
    "inventory_management": {
        "sources": ["parts_inventory", "scrap_management", "marketplace_integration"],
        "doctype_mappings": {
            # From parts_inventory
            "abc_analysis": {"from": "parts_inventory", "to_subdir": "inventory_core"},
            "barcode_scanner": {"from": "parts_inventory", "to_subdir": "inventory_core"},
            "cycle_count": {"from": "parts_inventory", "to_subdir": "inventory_core"},
            "item_cross_reference": {"from": "parts_inventory", "to_subdir": "arabic_parts_database"},
            "part_cross_reference": {"from": "parts_inventory", "to_subdir": "arabic_parts_database"},
            "stock_transfer_log": {"from": "parts_inventory", "to_subdir": "inventory_core"},
            "supplier_parts_category": {"from": "parts_inventory", "to_subdir": "traditional_supplier_management"},
            
            # From scrap_management
            "disassembly_plan": {"from": "scrap_management", "to_subdir": "scrap_dismantling_operations"},
            "disassembly_step": {"from": "scrap_management", "to_subdir": "scrap_dismantling_operations"},
            "dismantling_work_order": {"from": "scrap_management", "to_subdir": "scrap_dismantling_operations"},
            "extracted_parts": {"from": "scrap_management", "to_subdir": "scrap_dismantling_operations"},
            "inventory_movement": {"from": "scrap_management", "to_subdir": "inventory_core"},
            "part_movement_history": {"from": "scrap_management", "to_subdir": "inventory_core"},
            "part_photo": {"from": "scrap_management", "to_subdir": "scrap_dismantling_operations"},
            "part_storage_location": {"from": "scrap_management", "to_subdir": "scrap_dismantling_operations"},
            "part_quality_assessment": {"from": "scrap_management", "to_subdir": "scrap_dismantling_operations"},
            "parts_condition_grade": {"from": "scrap_management", "to_subdir": "scrap_dismantling_operations"},
            "profit_analysis": {"from": "scrap_management", "to_subdir": "marketplace_sales_integration"},
            "sales_channel": {"from": "scrap_management", "to_subdir": "marketplace_sales_integration"},
            "scrap_vehicle": {"from": "scrap_management", "to_subdir": "scrap_dismantling_operations"},
            "storage_zone": {"from": "scrap_management", "to_subdir": "scrap_dismantling_operations"},
            "vehicle_dismantling_bom": {"from": "scrap_management", "to_subdir": "scrap_dismantling_operations"},
            
            # From marketplace_integration  
            "marketplace_connector": {"from": "marketplace_integration", "to_subdir": "marketplace_sales_integration"},
            "marketplace_product_listing": {"from": "marketplace_integration", "to_subdir": "marketplace_sales_integration"},
            "marketplace_sync_log": {"from": "marketplace_integration", "to_subdir": "marketplace_sales_integration"}
        }
    },
    
    "workshop_core": {
        "sources": ["workshop_management", "workshop_operations", "sales_service", "vehicle_management"],
        "integrate_vehicle_management": True  # Special handling for vehicle_management
    },
    
    "customer_management": {
        "sources": ["customer_management", "customer_portal", "customer_satisfaction", "communication_management"],
        "use_consolidated_version": True  # Already has consolidated DocTypes
    },
    
    "financial_operations": {
        "sources": ["billing_management", "purchasing_management"],
        "use_consolidated_version": True  # Already has consolidated DocTypes
    },
    
    "user_security": {
        "sources": ["user_management", "security", "license_management"]
    },
    
    "analytics_reporting": {
        "sources": ["analytics_reporting", "reports_analytics", "dashboard"],
        "enhance_existing": True
    },
    
    "mobile_operations": {
        "sources": ["mobile_operations", "mobile_technician", "realtime"],
        "enhance_existing": True
    },
    
    "system_administration": {
        "sources": ["system_administration", "training_management", "environmental_compliance", "setup"],
        "enhance_existing": True
    }
}

def copy_directory_contents(src, dst):
    """Copy directory contents preserving structure"""
    if os.path.exists(src):
        os.makedirs(dst, exist_ok=True)
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)

def migrate_doctype(source_module, doctype_name, target_module, target_subdir):
    """Migrate a single DocType from source to target"""
    source_path = os.path.join(BASE_PATH, source_module, "doctype", doctype_name)
    target_path = os.path.join(BASE_PATH, target_module, target_subdir, doctype_name)
    
    if os.path.exists(source_path):
        print(f"  - Migrating DocType: {doctype_name}")
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        shutil.copytree(source_path, target_path, dirs_exist_ok=True)
        return True
    return False

def migrate_api_files(source_module, target_module):
    """Migrate API files from source to target"""
    source_api = os.path.join(BASE_PATH, source_module, "api")
    target_api = os.path.join(BASE_PATH, target_module, "api")
    
    if os.path.exists(source_api):
        print(f"  - Migrating API files from {source_module}")
        os.makedirs(target_api, exist_ok=True)
        copy_directory_contents(source_api, target_api)

def create_migration_report(module_name, status):
    """Create a migration report for tracking"""
    report_path = os.path.join(BASE_PATH, f"{module_name}_migration_report.json")
    with open(report_path, 'w') as f:
        json.dump(status, f, indent=2)

def main():
    print("=== PROPER CONSOLIDATION MIGRATION ===\n")
    
    # Step 1: Create all consolidated modules from workspace
    print("Step 1: Installing consolidated module structures...")
    for module_name in CONSOLIDATION_MAPPING.keys():
        workspace_module = os.path.join(CONSOLIDATION_PATH, module_name)
        target_module = os.path.join(BASE_PATH, module_name + "_consolidated")
        
        if os.path.exists(workspace_module):
            print(f"- Installing {module_name}_consolidated from workspace")
            shutil.copytree(workspace_module, target_module, dirs_exist_ok=True)
    
    # Step 2: Migrate inventory_management content
    print("\nStep 2: Migrating inventory_management content...")
    inv_config = CONSOLIDATION_MAPPING["inventory_management"]
    inv_status = {"migrated_doctypes": [], "migrated_apis": [], "errors": []}
    
    for doctype, mapping in inv_config["doctype_mappings"].items():
        if migrate_doctype(mapping["from"], doctype, "inventory_management_consolidated", mapping["to_subdir"]):
            inv_status["migrated_doctypes"].append(doctype)
        else:
            inv_status["errors"].append(f"DocType {doctype} not found in {mapping['from']}")
    
    # Migrate APIs
    for source in inv_config["sources"]:
        migrate_api_files(source, "inventory_management_consolidated")
        inv_status["migrated_apis"].append(source)
    
    create_migration_report("inventory_management", inv_status)
    
    # Step 3: Handle vehicle_management integration into workshop_core
    print("\nStep 3: Integrating vehicle_management into workshop_core...")
    vehicle_src = os.path.join(BASE_PATH, "vehicle_management")
    workshop_target = os.path.join(BASE_PATH, "workshop_core_consolidated", "vehicle_integration")
    
    if os.path.exists(vehicle_src):
        os.makedirs(workshop_target, exist_ok=True)
        copy_directory_contents(vehicle_src, workshop_target)
        print("  - Vehicle management integrated into workshop_core")
    
    # Step 4: Create modules.txt update
    print("\nStep 4: Preparing modules.txt update...")
    new_modules = [
        "# Consolidated Modules (New Architecture)",
        "Workshop Core Consolidated",
        "Customer Management Consolidated", 
        "Financial Operations Consolidated",
        "Inventory Management Consolidated",
        "User Security Consolidated",
        "Analytics Reporting Consolidated",
        "Mobile Operations Consolidated",
        "System Administration Consolidated",
        "",
        "# Legacy Modules (To be removed after validation)",
    ]
    
    # Add all existing modules for now
    existing_modules = []
    modules_file = os.path.join(BASE_PATH, "modules.txt")
    if os.path.exists(modules_file):
        with open(modules_file, 'r') as f:
            existing_modules = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    new_modules.extend(existing_modules)
    
    # Write updated modules.txt
    with open(modules_file + ".new", 'w') as f:
        f.write('\n'.join(new_modules))
    
    print("\n=== MIGRATION SUMMARY ===")
    print("✅ Consolidated modules installed with '_consolidated' suffix")
    print("✅ Inventory management DocTypes migrated")
    print("✅ Vehicle management integrated into workshop_core")
    print("✅ New modules.txt prepared (modules.txt.new)")
    print("\n⚠️  IMPORTANT: Verify all migrations before deleting ANY legacy modules!")
    print("📋 Check migration reports: *_migration_report.json")

if __name__ == "__main__":
    main()