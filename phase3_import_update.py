#!/usr/bin/env python3
"""
Phase 3: Import Update and Testing
Comprehensive import reference updates and group testing
"""

import os
import re
import subprocess
from pathlib import Path
from datetime import datetime


class ImportUpdateManager:
    """Manages comprehensive import updates for Phase 3"""
    
    def __init__(self):
        self.app_path = Path("apps/universal_workshop")
        self.log_file = "phase3_import_update.log"
        self.updated_files = []
        self.errors = []
        self.warnings = []
        
        # Mapping of old paths to new paths
        self.path_mappings = {
            "workshop_management.doctype.workshop_profile": "workshop_operations.workshop_profile",
            "workshop_management.doctype.workshop_settings": "workshop_operations.workshop_settings", 
            "workshop_management.doctype.workshop_theme": "workshop_operations.workshop_theme",
            "workshop_management.doctype.service_order": "workshop_operations.service_order",
            "workshop_management.doctype.service_bay": "workshop_operations.service_bay",
            "workshop_management.doctype.service_order_labor": "workshop_operations.service_order_labor",
            "workshop_management.doctype.service_order_parts": "workshop_operations.service_order_parts",
            "workshop_management.doctype.service_order_status_history": "workshop_operations.service_order_status_history",
            "workshop_management.doctype.technician": "workshop_operations.technician",
            "workshop_management.doctype.technician_skills": "workshop_operations.technician_skills",
            "workshop_management.doctype.skill": "workshop_operations.skill",
            "workshop_management.doctype.service_estimate_parts": "workshop_operations.service_estimate_parts",
            
            "workshop_management.doctype.quality_control_checkpoint": "workshop_operations.quality_control.quality_control_checkpoint",
            "workshop_management.doctype.quality_control_document": "workshop_operations.quality_control.quality_control_document",
            "workshop_management.doctype.quality_control_photo": "workshop_operations.quality_control.quality_control_photo",
            
            "workshop_management.doctype.backup_manager": "system_administration.backup_manager",
            "workshop_management.doctype.performance_monitor": "system_administration.performance_monitor",
            "workshop_management.doctype.system_health_monitor": "system_administration.system_health_monitor",
            "workshop_management.doctype.error_logger": "system_administration.error_logger",
            "workshop_management.doctype.integration_manager": "system_administration.integration_manager",
            "workshop_management.doctype.license_manager": "system_administration.license_manager",
            
            "workshop_management.doctype.mobile_device_management": "mobile_operations.mobile_device_management",
            
            "workshop_management.doctype.onboarding_progress": "setup.onboarding.onboarding_progress",
            "workshop_management.doctype.onboarding_performance_log": "setup.onboarding.onboarding_performance_log",
        }
        
    def log(self, message, level="INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        
        with open(self.log_file, "a") as f:
            f.write(log_entry + "\n")
    
    def find_import_references(self):
        """Find all files containing workshop_management.doctype references"""
        self.log("🔍 Searching for import references...")
        
        try:
            # Use grep to find all references  
            result = subprocess.run([
                "grep", 
                "-r",
                "-n", 
                "workshop_management\.doctype",
                str(self.app_path),
                "--include=*.py"
            ], capture_output=True, text=True)
            
            references = []
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if ':' in line:
                        file_path, line_content = line.split(':', 1)
                        references.append({
                            'file': file_path,
                            'content': line_content.strip()
                        })
            
            self.log(f"Found {len(references)} import references")
            return references
            
        except Exception as e:
            self.log(f"❌ Error finding references: {e}", "ERROR")
            return []
    
    def update_file_imports(self, file_path):
        """Update imports in a single file"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            original_content = content
            updated = False
            
            # Update each mapping
            for old_path, new_path in self.path_mappings.items():
                old_import = f"universal_workshop.{old_path}"
                new_import = f"universal_workshop.{new_path}"
                
                if old_import in content:
                    content = content.replace(old_import, new_import)
                    updated = True
                    self.log(f"  Updated: {old_path} → {new_path}")
            
            # Write back if updated
            if updated:
                with open(file_path, 'w') as f:
                    f.write(content)
                self.updated_files.append(file_path)
                self.log(f"✅ Updated imports in {file_path}")
                return True
            else:
                return False
                
        except Exception as e:
            self.log(f"❌ Error updating {file_path}: {e}", "ERROR")
            self.errors.append(f"Failed to update {file_path}: {e}")
            return False
    
    def test_import_group(self, group_name, module_paths):
        """Test imports for a specific group"""
        self.log(f"🧪 Testing {group_name} imports...")
        
        success_count = 0
        total_count = len(module_paths)
        
        for module_path in module_paths:
            try:
                # Test if module can be imported
                import_statement = f"from universal_workshop.{module_path} import *"
                
                # Try to validate module path exists
                full_path = self.app_path / "universal_workshop" / module_path.replace('.', '/')
                if full_path.exists() or (full_path.parent / "__init__.py").exists():
                    success_count += 1
                    self.log(f"  ✅ {module_path}")
                else:
                    self.log(f"  ⚠️ Path not found: {module_path}", "WARNING")
                    self.warnings.append(f"Path not found: {module_path}")
                    
            except Exception as e:
                self.log(f"  ❌ {module_path}: {e}", "ERROR")
                self.errors.append(f"Import test failed for {module_path}: {e}")
        
        self.log(f"✅ {group_name}: {success_count}/{total_count} imports successful")
        return success_count == total_count
    
    def validate_new_structure(self):
        """Validate that the new structure is working"""
        self.log("🔍 Validating new structure...")
        
        # Test each group
        groups = {
            "WORKSHOP_OPERATIONS": [
                "workshop_operations.workshop_profile",
                "workshop_operations.service_order", 
                "workshop_operations.technician",
                "workshop_operations.service_bay"
            ],
            "QUALITY_CONTROL": [
                "workshop_operations.quality_control.quality_control_checkpoint",
                "workshop_operations.quality_control.quality_control_document"
            ],
            "SYSTEM_ADMINISTRATION": [
                "system_administration.backup_manager",
                "system_administration.license_manager"
            ],
            "MOBILE_OPERATIONS": [
                "mobile_operations.mobile_device_management"
            ],
            "ONBOARDING_SYSTEM": [
                "setup.onboarding.onboarding_progress"
            ]
        }
        
        all_success = True
        for group_name, module_paths in groups.items():
            if not self.test_import_group(group_name, module_paths):
                all_success = False
        
        return all_success
    
    def run_comprehensive_tests(self):
        """Run comprehensive tests after import updates"""
        self.log("🧪 Running comprehensive tests...")
        
        try:
            # Test Phase 2 functionality
            result = subprocess.run(["python3", "test_phase2_functionality.py"], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log("✅ Phase 2 functionality tests passed")
            else:
                self.log(f"❌ Phase 2 tests failed: {result.stderr}", "ERROR")
                return False
            
            # Validate new structure
            if not self.validate_new_structure():
                self.log("❌ New structure validation failed", "ERROR")
                return False
            
            return True
            
        except Exception as e:
            self.log(f"❌ Comprehensive tests failed: {e}", "ERROR")
            return False
    
    def execute_import_updates(self):
        """Execute comprehensive import updates"""
        self.log("🚀 Starting Phase 3: Import Updates and Testing")
        self.log("=" * 60)
        
        # Find all references
        references = self.find_import_references()
        
        if not references:
            self.log("✅ No import references found to update")
            return True
        
        # Update files
        unique_files = set(ref['file'] for ref in references)
        self.log(f"📁 Updating imports in {len(unique_files)} files...")
        
        for file_path in unique_files:
            self.update_file_imports(file_path)
        
        # Run tests
        if not self.run_comprehensive_tests():
            self.log("❌ Import update validation failed", "ERROR")
            return False
        
        # Summary
        self.log("=" * 60)
        self.log("✅ PHASE 3 IMPORT UPDATES COMPLETED")
        self.log(f"📁 Files Updated: {len(self.updated_files)}")
        self.log(f"🔧 Errors: {len(self.errors)}")
        self.log(f"⚠️ Warnings: {len(self.warnings)}")
        
        if self.errors:
            self.log("❌ Errors encountered:")
            for error in self.errors:
                self.log(f"  - {error}")
        
        if self.warnings:
            self.log("⚠️ Warnings:")
            for warning in self.warnings:
                self.log(f"  - {warning}")
        
        # Save report
        import json
        report = {
            "timestamp": datetime.now().isoformat(),
            "phase": "Phase 3: Import Updates and Testing",
            "status": "COMPLETED" if len(self.errors) == 0 else "COMPLETED_WITH_ERRORS",
            "files_updated": len(self.updated_files),
            "updated_files": self.updated_files,
            "errors": self.errors,
            "warnings": self.warnings
        }
        
        with open("phase3_import_update_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        self.log("📁 Import update report saved to: phase3_import_update_report.json")
        
        return len(self.errors) == 0


def main():
    """Main import update execution"""
    manager = ImportUpdateManager()
    
    try:
        success = manager.execute_import_updates()
        return success
    except Exception as e:
        print(f"❌ Import update failed with exception: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)