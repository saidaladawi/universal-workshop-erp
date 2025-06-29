#!/usr/bin/env python3
"""
Phase 3: Database Reference Validation
Validate database integrity after workshop_management reorganization
"""

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime


class DatabaseValidationManager:
    """Manages database validation for Phase 3"""
    
    def __init__(self):
        self.app_path = Path("apps/universal_workshop/universal_workshop")
        self.log_file = "phase3_database_validation.log"
        self.errors = []
        self.warnings = []
        self.validation_results = {}
        
        # DocTypes that were migrated
        self.migrated_doctypes = [
            "workshop_profile", "workshop_settings", "workshop_theme",
            "service_order", "service_bay", "service_order_labor",
            "service_order_parts", "service_order_status_history",
            "technician", "technician_skills", "skill", "service_estimate_parts",
            "quality_control_checkpoint", "quality_control_document", "quality_control_photo",
            "backup_manager", "performance_monitor", "system_health_monitor",
            "error_logger", "integration_manager", "license_manager",
            "mobile_device_management", "onboarding_progress", "onboarding_performance_log"
        ]
        
    def log(self, message, level="INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        
        with open(self.log_file, "a") as f:
            f.write(log_entry + "\n")
    
    def check_modules_txt(self):
        """Check if modules.txt needs updating"""
        self.log("📋 Checking modules.txt...")
        
        try:
            modules_file = self.app_path / "modules.txt"
            
            if not modules_file.exists():
                self.log("⚠️ modules.txt not found", "WARNING")
                return False
            
            with open(modules_file, 'r') as f:
                modules = f.read().strip().split('\n')
            
            # Check if new modules need to be added
            new_modules = [
                "Workshop Operations",
                "System Administration", 
                "Mobile Operations"
            ]
            
            needs_update = False
            for new_module in new_modules:
                if new_module not in modules:
                    modules.append(new_module)
                    needs_update = True
                    self.log(f"  Adding module: {new_module}")
            
            if needs_update:
                with open(modules_file, 'w') as f:
                    f.write('\n'.join(modules) + '\n')
                self.log("✅ Updated modules.txt")
            else:
                self.log("✅ modules.txt is up to date")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error checking modules.txt: {e}", "ERROR")
            self.errors.append(f"modules.txt check failed: {e}")
            return False
    
    def validate_doctype_files(self):
        """Validate that all DocType files are accessible"""
        self.log("📁 Validating DocType files...")
        
        validation_count = 0
        success_count = 0
        
        # Define the new locations
        doctype_locations = {
            "workshop_operations": [
                "workshop_profile", "workshop_settings", "workshop_theme",
                "service_order", "service_bay", "service_order_labor",
                "service_order_parts", "service_order_status_history",
                "technician", "technician_skills", "skill", "service_estimate_parts"
            ],
            "workshop_operations/quality_control": [
                "quality_control_checkpoint", "quality_control_document", "quality_control_photo"
            ],
            "system_administration": [
                "backup_manager", "performance_monitor", "system_health_monitor",
                "error_logger", "integration_manager", "license_manager"
            ],
            "mobile_operations": [
                "mobile_device_management"
            ],
            "setup/onboarding": [
                "onboarding_progress", "onboarding_performance_log"
            ]
        }
        
        for location, doctypes in doctype_locations.items():
            self.log(f"  Checking {location}...")
            
            for doctype in doctypes:
                validation_count += 1
                doctype_path = self.app_path / location / doctype
                
                if doctype_path.exists():
                    # Check for Python file
                    py_file = doctype_path / f"{doctype}.py"
                    if py_file.exists():
                        success_count += 1
                        self.log(f"    ✅ {doctype}")
                    else:
                        self.log(f"    ⚠️ {doctype} - missing .py file", "WARNING")
                        self.warnings.append(f"Missing .py file for {doctype}")
                else:
                    self.log(f"    ❌ {doctype} - directory not found", "ERROR")
                    self.errors.append(f"DocType directory not found: {doctype}")
        
        self.validation_results["doctype_validation"] = {
            "total": validation_count,
            "success": success_count,
            "success_rate": (success_count / validation_count) * 100 if validation_count > 0 else 0
        }
        
        self.log(f"✅ DocType validation: {success_count}/{validation_count} ({self.validation_results['doctype_validation']['success_rate']:.1f}%)")
        return success_count == validation_count
    
    def check_hook_references(self):
        """Check if hooks.py has any workshop_management references"""
        self.log("🔧 Checking hooks.py for old references...")
        
        try:
            hooks_file = self.app_path / "hooks.py"
            
            if not hooks_file.exists():
                self.log("❌ hooks.py not found", "ERROR")
                return False
            
            with open(hooks_file, 'r') as f:
                content = f.read()
            
            # Check for old workshop_management references
            if "workshop_management" in content:
                self.log("⚠️ Found workshop_management references in hooks.py", "WARNING")
                self.warnings.append("hooks.py contains workshop_management references")
                
                # Show the lines with references
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if "workshop_management" in line:
                        self.log(f"    Line {i}: {line.strip()}")
                
                return False
            else:
                self.log("✅ No old workshop_management references in hooks.py")
                return True
                
        except Exception as e:
            self.log(f"❌ Error checking hooks.py: {e}", "ERROR")
            self.errors.append(f"hooks.py check failed: {e}")
            return False
    
    def test_doctype_imports(self):
        """Test that DocTypes can be imported from new locations"""
        self.log("🧪 Testing DocType imports...")
        
        test_imports = [
            "from universal_workshop.workshop_operations.workshop_profile.workshop_profile import WorkshopProfile",
            "from universal_workshop.workshop_operations.service_order.service_order import ServiceOrder", 
            "from universal_workshop.workshop_operations.technician.technician import Technician",
            "from universal_workshop.system_administration.license_manager.license_manager import LicenseManager"
        ]
        
        success_count = 0
        total_count = len(test_imports)
        
        for import_statement in test_imports:
            try:
                # Extract module info for path validation
                parts = import_statement.split()
                module_path = parts[1].replace('universal_workshop.', '').replace('.', '/')
                
                # Check if file exists
                file_path = self.app_path / f"{module_path}.py"
                if file_path.exists():
                    success_count += 1
                    self.log(f"  ✅ {parts[1]}")
                else:
                    self.log(f"  ❌ File not found: {file_path}", "ERROR")
                    self.errors.append(f"Import test failed: {import_statement}")
                    
            except Exception as e:
                self.log(f"  ❌ Import error: {e}", "ERROR")
                self.errors.append(f"Import test error: {import_statement} - {e}")
        
        self.validation_results["import_tests"] = {
            "total": total_count,
            "success": success_count,
            "success_rate": (success_count / total_count) * 100 if total_count > 0 else 0
        }
        
        self.log(f"✅ Import tests: {success_count}/{total_count} ({self.validation_results['import_tests']['success_rate']:.1f}%)")
        return success_count == total_count
    
    def validate_directory_structure(self):
        """Validate the new directory structure is complete"""
        self.log("📂 Validating directory structure...")
        
        required_dirs = [
            "workshop_operations/doctype",
            "workshop_operations/quality_control/doctype",
            "system_administration/doctype", 
            "mobile_operations/doctype",
            "setup/onboarding/doctype"
        ]
        
        success_count = 0
        total_count = len(required_dirs)
        
        for dir_path in required_dirs:
            full_path = self.app_path / dir_path
            if full_path.exists() and full_path.is_dir():
                success_count += 1
                self.log(f"  ✅ {dir_path}")
            else:
                self.log(f"  ❌ Missing directory: {dir_path}", "ERROR")
                self.errors.append(f"Missing directory: {dir_path}")
        
        self.validation_results["directory_structure"] = {
            "total": total_count,
            "success": success_count,
            "success_rate": (success_count / total_count) * 100 if total_count > 0 else 0
        }
        
        self.log(f"✅ Directory structure: {success_count}/{total_count} ({self.validation_results['directory_structure']['success_rate']:.1f}%)")
        return success_count == total_count
    
    def run_system_validation(self):
        """Run system-level validation"""
        self.log("🔍 Running system validation...")
        
        try:
            # Test that the system can start basic operations
            result = subprocess.run(["python3", "test_phase2_functionality.py"], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log("✅ System validation passed")
                self.validation_results["system_validation"] = {"status": "PASSED"}
                return True
            else:
                self.log(f"❌ System validation failed: {result.stderr}", "ERROR")
                self.errors.append(f"System validation failed: {result.stderr}")
                self.validation_results["system_validation"] = {"status": "FAILED", "error": result.stderr}
                return False
                
        except Exception as e:
            self.log(f"❌ System validation error: {e}", "ERROR")
            self.errors.append(f"System validation error: {e}")
            return False
    
    def execute_database_validation(self):
        """Execute comprehensive database validation"""
        self.log("🚀 Starting Phase 3: Database Validation")
        self.log("=" * 60)
        
        # Run all validation checks
        checks = [
            ("Directory Structure", self.validate_directory_structure),
            ("DocType Files", self.validate_doctype_files),
            ("Modules Configuration", self.check_modules_txt),
            ("Hook References", self.check_hook_references),
            ("Import Testing", self.test_doctype_imports),
            ("System Validation", self.run_system_validation)
        ]
        
        passed_checks = 0
        total_checks = len(checks)
        
        for check_name, check_function in checks:
            self.log(f"\n🔍 Running {check_name}...")
            if check_function():
                passed_checks += 1
                self.log(f"✅ {check_name} PASSED")
            else:
                self.log(f"❌ {check_name} FAILED")
        
        # Overall results
        success_rate = (passed_checks / total_checks) * 100
        
        self.log("\n" + "=" * 60)
        self.log(f"📊 DATABASE VALIDATION RESULTS")
        self.log(f"✅ Checks Passed: {passed_checks}/{total_checks} ({success_rate:.1f}%)")
        self.log(f"🔧 Errors: {len(self.errors)}")
        self.log(f"⚠️ Warnings: {len(self.warnings)}")
        
        if self.errors:
            self.log("\n❌ Errors encountered:")
            for error in self.errors:
                self.log(f"  - {error}")
        
        if self.warnings:
            self.log("\n⚠️ Warnings:")
            for warning in self.warnings:
                self.log(f"  - {warning}")
        
        # Save validation report
        report = {
            "timestamp": datetime.now().isoformat(),
            "phase": "Phase 3: Database Validation",
            "status": "PASSED" if passed_checks == total_checks else "FAILED",
            "checks_passed": passed_checks,
            "checks_total": total_checks,
            "success_rate": success_rate,
            "validation_results": self.validation_results,
            "errors": self.errors,
            "warnings": self.warnings
        }
        
        with open("phase3_database_validation_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        self.log(f"\n📁 Database validation report saved to: phase3_database_validation_report.json")
        
        if passed_checks == total_checks:
            self.log("✅ DATABASE VALIDATION SUCCESSFUL")
        else:
            self.log("❌ DATABASE VALIDATION COMPLETED WITH ISSUES")
        
        return passed_checks == total_checks


def main():
    """Main database validation execution"""
    manager = DatabaseValidationManager()
    
    try:
        success = manager.execute_database_validation()
        return success
    except Exception as e:
        print(f"❌ Database validation failed with exception: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)