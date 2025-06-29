#!/usr/bin/env python3
"""
Phase 3: Workshop Management Reorganization Analysis
Analyze current DocTypes and plan safe migration
"""

import os
import json
from pathlib import Path

def analyze_workshop_management_structure():
    """Analyze current workshop_management DocTypes"""
    
    workshop_path = Path("apps/universal_workshop/universal_workshop/workshop_management/doctype")
    
    # Scan for existing DocTypes
    existing_doctypes = []
    if workshop_path.exists():
        for item in workshop_path.iterdir():
            if item.is_dir() and not item.name.startswith('__'):
                existing_doctypes.append(item.name)
    
    # Classification according to refactoring plan
    classification = {
        "WORKSHOP_OPERATIONS": [
            'workshop_profile', 'workshop_settings', 'workshop_theme',
            'service_order', 'service_bay', 'service_order_labor',
            'service_order_parts', 'service_order_status_history',
            'technician', 'technician_skills', 'skill',
            'service_estimate_parts'  # Added based on analysis
        ],
        "QUALITY_CONTROL": [
            'quality_control_checkpoint', 'quality_control_document', 
            'quality_control_photo'
        ],
        "SYSTEM_ADMINISTRATION": [
            'backup_manager', 'performance_monitor', 'system_health_monitor',
            'error_logger', 'integration_manager', 'license_manager'
        ],
        "MOBILE_OPERATIONS": [
            'mobile_device_management'
        ],
        "ONBOARDING_SYSTEM": [
            'onboarding_progress', 'onboarding_performance_log'
        ]
    }
    
    # Target directory mapping
    target_mapping = {
        "WORKSHOP_OPERATIONS": "workshop_operations",
        "QUALITY_CONTROL": "workshop_operations/quality_control",
        "SYSTEM_ADMINISTRATION": "system_administration",
        "MOBILE_OPERATIONS": "mobile_operations",
        "ONBOARDING_SYSTEM": "setup/onboarding"
    }
    
    # Verify classification coverage
    classified_doctypes = []
    for category, doctypes in classification.items():
        classified_doctypes.extend(doctypes)
    
    missing_from_classification = [dt for dt in existing_doctypes if dt not in classified_doctypes]
    missing_from_filesystem = [dt for dt in classified_doctypes if dt not in existing_doctypes]
    
    analysis = {
        "existing_doctypes": existing_doctypes,
        "total_count": len(existing_doctypes),
        "classification": classification,
        "target_mapping": target_mapping,
        "missing_from_classification": missing_from_classification,
        "missing_from_filesystem": missing_from_filesystem,
        "classification_complete": len(missing_from_classification) == 0,
        "all_doctypes_exist": len(missing_from_filesystem) == 0
    }
    
    return analysis

def create_migration_plan(analysis):
    """Create detailed migration plan"""
    
    migration_steps = []
    
    for category, doctypes in analysis["classification"].items():
        target_dir = analysis["target_mapping"][category]
        
        for doctype in doctypes:
            if doctype in analysis["existing_doctypes"]:
                step = {
                    "doctype": doctype,
                    "category": category,
                    "source": f"workshop_management/doctype/{doctype}",
                    "target": f"{target_dir}/{doctype}",
                    "target_dir": target_dir,
                    "risk_level": "HIGH" if doctype in ["service_order", "workshop_profile", "technician"] else "MEDIUM"
                }
                migration_steps.append(step)
    
    migration_plan = {
        "total_doctypes": len(migration_steps),
        "high_risk_count": len([s for s in migration_steps if s["risk_level"] == "HIGH"]),
        "medium_risk_count": len([s for s in migration_steps if s["risk_level"] == "MEDIUM"]),
        "steps": migration_steps,
        "execution_order": [
            "ONBOARDING_SYSTEM",    # Lowest risk first
            "MOBILE_OPERATIONS",
            "QUALITY_CONTROL", 
            "SYSTEM_ADMINISTRATION",
            "WORKSHOP_OPERATIONS"   # Highest risk last
        ]
    }
    
    return migration_plan

def analyze_import_dependencies():
    """Analyze import dependencies for workshop_management DocTypes"""
    
    dependencies = []
    
    # Search for imports referencing workshop_management.doctype
    import_analysis_file = "import_analysis.txt"
    if os.path.exists(import_analysis_file):
        with open(import_analysis_file, 'r') as f:
            lines = f.readlines()
            
        for line in lines:
            if "workshop_management.doctype" in line:
                dependencies.append(line.strip())
    
    return dependencies

def main():
    """Run Phase 3 analysis"""
    print("🔍 Phase 3: Workshop Management Reorganization Analysis")
    print("=" * 60)
    
    # Analyze current structure
    analysis = analyze_workshop_management_structure()
    
    print(f"📊 Found {analysis['total_count']} DocTypes in workshop_management")
    print(f"✅ Classification complete: {analysis['classification_complete']}")
    print(f"✅ All planned DocTypes exist: {analysis['all_doctypes_exist']}")
    
    if analysis['missing_from_classification']:
        print(f"⚠️ Missing from classification: {analysis['missing_from_classification']}")
    
    if analysis['missing_from_filesystem']:
        print(f"⚠️ Missing from filesystem: {analysis['missing_from_filesystem']}")
    
    # Create migration plan
    migration_plan = create_migration_plan(analysis)
    
    print(f"\n📋 Migration Plan:")
    print(f"   Total DocTypes to migrate: {migration_plan['total_doctypes']}")
    print(f"   High risk DocTypes: {migration_plan['high_risk_count']}")
    print(f"   Medium risk DocTypes: {migration_plan['medium_risk_count']}")
    
    # Analyze dependencies
    dependencies = analyze_import_dependencies()
    print(f"\n🔗 Found {len(dependencies)} import dependencies to update")
    
    # Save detailed analysis
    full_analysis = {
        "timestamp": "2025-06-29T16:10:00",
        "phase": "Phase 3: Workshop Management Reorganization",
        "structure_analysis": analysis,
        "migration_plan": migration_plan,
        "import_dependencies": dependencies
    }
    
    with open("phase3_analysis_results.json", "w") as f:
        json.dump(full_analysis, f, indent=2)
    
    print(f"\n📁 Detailed analysis saved to: phase3_analysis_results.json")
    
    # Print classification summary
    print(f"\n📂 DocType Classification:")
    for category, doctypes in analysis["classification"].items():
        target = analysis["target_mapping"][category]
        existing_count = len([dt for dt in doctypes if dt in analysis["existing_doctypes"]])
        print(f"   {category}: {existing_count} DocTypes → {target}/")
        for doctype in doctypes:
            if doctype in analysis["existing_doctypes"]:
                print(f"     - {doctype}")
    
    return analysis, migration_plan

if __name__ == "__main__":
    analysis, plan = main()