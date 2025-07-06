#!/usr/bin/env python3
"""
Complete Consolidation Migration Script - Phase 2
Migrates remaining modules with comprehensive content migration
"""

import os
import shutil
from pathlib import Path

BASE_PATH = "/home/said/frappe-dev/frappe-bench/apps/universal_workshop/universal_workshop"

# Detailed migration mappings for remaining modules
REMAINING_MIGRATIONS = {
    "workshop_core_consolidated": {
        "migrations": [
            {
                "source": "workshop_management",
                "components": ["doctype", "api", "*.py"],
                "target_subdir": "workshop_management_legacy"
            },
            {
                "source": "workshop_operations", 
                "components": ["doctype", "*.py"],
                "target_subdir": "workshop_operations_legacy"
            },
            {
                "source": "sales_service",
                "components": ["doctype", "api", "*.py"],
                "target_subdir": "sales_service_legacy"
            }
        ]
    },
    
    "user_security_consolidated": {
        "migrations": [
            {
                "source": "user_management",
                "components": ["doctype", "*.py", "dashboard"],
                "target_subdir": "user_management_migrated"
            },
            {
                "source": "security",
                "components": ["*.py"],
                "target_subdir": "security_migrated"
            },
            {
                "source": "license_management",
                "components": ["doctype", "api", "utils", "*.py"],
                "target_subdir": "license_management_migrated"
            }
        ]
    },
    
    "analytics_reporting_consolidated": {
        "migrations": [
            {
                "source": "reports_analytics",
                "components": ["doctype", "report", "*.py"],
                "target_subdir": "reports_analytics_migrated"
            },
            {
                "source": "dashboard",
                "components": ["*.py", "*.js", "*.json"],
                "target_subdir": "dashboard_migrated"
            }
        ],
        "merge_with_existing": "analytics_reporting"  # Enhance existing
    },
    
    "mobile_operations_consolidated": {
        "migrations": [
            {
                "source": "mobile_technician.disabled",
                "components": ["doctype", "*.py"],
                "target_subdir": "mobile_technician_migrated"
            },
            {
                "source": "realtime",
                "components": ["*.py"],
                "target_subdir": "realtime_migrated"
            }
        ],
        "merge_with_existing": "mobile_operations"  # Enhance existing
    },
    
    "system_administration_consolidated": {
        "migrations": [
            {
                "source": "training_management",
                "components": ["doctype", "api", "*.py", "h5p"],
                "target_subdir": "training_management_migrated"
            },
            {
                "source": "environmental_compliance",
                "components": ["doctype", "report", "workflow"],
                "target_subdir": "environmental_compliance_migrated"
            },
            {
                "source": "setup",
                "components": ["*.py", "installation", "onboarding"],
                "target_subdir": "setup_migrated"
            }
        ],
        "merge_with_existing": "system_administration"  # Enhance existing
    },
    
    "customer_management_consolidated": {
        "migrations": [
            {
                "source": "customer_portal",
                "components": ["*.py", "doctype"],
                "target_subdir": "portal_integration"
            },
            {
                "source": "customer_satisfaction",
                "components": ["doctype"],
                "target_subdir": "satisfaction_tracking"
            },
            {
                "source": "communication_management",
                "components": ["api", "queue", "*.py"],
                "target_subdir": "communication_integration"
            }
        ]
    },
    
    "financial_operations_consolidated": {
        "migrations": [
            {
                "source": "billing_management",
                "components": ["fixtures", "print_format", "*.py", "cash_flow", "pnl_reporting", "receivables"],
                "target_subdir": "billing_integration"
            },
            {
                "source": "purchasing_management",
                "components": ["*.py", "*.js"],
                "target_subdir": "purchasing_integration"
            }
        ]
    }
}

def migrate_component(source_path, target_path, component):
    """Migrate a specific component (doctype, api, etc.)"""
    if component == "doctype":
        src = os.path.join(source_path, "doctype")
        dst = os.path.join(target_path, "doctype")
        if os.path.exists(src):
            print(f"    - Migrating DocTypes from {os.path.basename(source_path)}")
            shutil.copytree(src, dst, dirs_exist_ok=True)
            return True
            
    elif component == "api":
        src = os.path.join(source_path, "api")
        dst = os.path.join(target_path, "api")
        if os.path.exists(src):
            print(f"    - Migrating API files from {os.path.basename(source_path)}")
            shutil.copytree(src, dst, dirs_exist_ok=True)
            return True
            
    elif component == "report":
        src = os.path.join(source_path, "report")
        dst = os.path.join(target_path, "report")
        if os.path.exists(src):
            print(f"    - Migrating reports from {os.path.basename(source_path)}")
            shutil.copytree(src, dst, dirs_exist_ok=True)
            return True
            
    elif component == "workflow":
        src = os.path.join(source_path, "workflow")
        dst = os.path.join(target_path, "workflow")
        if os.path.exists(src):
            print(f"    - Migrating workflows from {os.path.basename(source_path)}")
            shutil.copytree(src, dst, dirs_exist_ok=True)
            return True
            
    elif component.endswith(".py"):
        # Copy specific Python files
        for file in Path(source_path).glob(component):
            if file.is_file():
                dst_file = os.path.join(target_path, file.name)
                shutil.copy2(file, dst_file)
                print(f"    - Migrated {file.name}")
                
    elif component in ["utils", "dashboard", "fixtures", "print_format", "h5p", "installation", 
                       "onboarding", "queue", "cash_flow", "pnl_reporting", "receivables"]:
        # Copy entire directories
        src = os.path.join(source_path, component)
        dst = os.path.join(target_path, component)
        if os.path.exists(src):
            print(f"    - Migrating {component} from {os.path.basename(source_path)}")
            shutil.copytree(src, dst, dirs_exist_ok=True)
            return True
            
    return False

def merge_with_existing_module(consolidated_path, existing_module):
    """Merge consolidated module enhancements with existing module"""
    existing_path = os.path.join(BASE_PATH, existing_module)
    if os.path.exists(existing_path) and os.path.exists(consolidated_path):
        print(f"  - Merging enhancements into existing {existing_module}")
        # Copy non-conflicting files
        for item in os.listdir(consolidated_path):
            src = os.path.join(consolidated_path, item)
            dst = os.path.join(existing_path, item + "_enhanced")
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)

def main():
    print("=== COMPLETE CONSOLIDATION MIGRATION - PHASE 2 ===\n")
    
    migration_summary = {}
    
    for target_module, config in REMAINING_MIGRATIONS.items():
        print(f"\nMigrating: {target_module}")
        print("-" * 50)
        
        target_path = os.path.join(BASE_PATH, target_module)
        migration_summary[target_module] = {"migrations": [], "errors": []}
        
        if not os.path.exists(target_path):
            print(f"  ⚠️  Target module {target_module} not found!")
            migration_summary[target_module]["errors"].append("Target module not found")
            continue
            
        # Process each migration
        for migration in config.get("migrations", []):
            source_module = migration["source"]
            source_path = os.path.join(BASE_PATH, source_module)
            
            if not os.path.exists(source_path):
                print(f"  ⚠️  Source module {source_module} not found!")
                migration_summary[target_module]["errors"].append(f"Source {source_module} not found")
                continue
                
            # Create target subdirectory
            target_subdir = os.path.join(target_path, migration["target_subdir"])
            os.makedirs(target_subdir, exist_ok=True)
            
            print(f"  From {source_module}:")
            
            # Migrate each component
            for component in migration["components"]:
                migrate_component(source_path, target_subdir, component)
                
            migration_summary[target_module]["migrations"].append(source_module)
            
        # Handle merge with existing module
        if "merge_with_existing" in config:
            merge_with_existing_module(target_path, config["merge_with_existing"])
    
    # Write summary report
    print("\n\n=== MIGRATION SUMMARY ===")
    for module, status in migration_summary.items():
        print(f"\n{module}:")
        print(f"  Migrated from: {', '.join(status['migrations'])}")
        if status['errors']:
            print(f"  Errors: {', '.join(status['errors'])}")
    
    print("\n✅ Phase 2 migration complete!")
    print("📋 Next: Validate all migrations before deleting legacy modules")

if __name__ == "__main__":
    main()