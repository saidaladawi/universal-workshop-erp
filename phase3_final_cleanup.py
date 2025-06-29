#!/usr/bin/env python3
"""
Phase 3: Final Cleanup and Comprehensive Testing
Safe removal of original workshop_management DocTypes and final validation
"""

import os
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
import json


class FinalCleanupManager:
    """Manages the final cleanup and comprehensive testing for Phase 3"""
    
    def __init__(self):
        self.app_path = Path("apps/universal_workshop/universal_workshop")
        self.workshop_mgmt_path = self.app_path / "workshop_management"
        self.log_file = "phase3_final_cleanup.log"
        self.errors = []
        self.warnings = []
        self.removed_files = []
        
    def log(self, message, level="INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        
        with open(self.log_file, "a") as f:
            f.write(log_entry + "\n")
    
    def create_final_safety_checkpoint(self):
        """Create final safety checkpoint before removing originals"""
        try:
            # Create git tag for final checkpoint
            tag_name = f"phase3-before-cleanup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            subprocess.run(["git", "tag", tag_name], check=True)
            
            # Create final backup of workshop_management
            backup_path = f"phase3_backup/final_workshop_management_backup"
            os.makedirs(backup_path, exist_ok=True)
            
            if self.workshop_mgmt_path.exists():
                shutil.copytree(self.workshop_mgmt_path, f"{backup_path}/workshop_management", dirs_exist_ok=True)
            
            self.log(f"✅ Final safety checkpoint created: {tag_name}")
            return tag_name
        except Exception as e:
            self.log(f"❌ Failed to create final checkpoint: {e}", "ERROR")
            return None
    
    def verify_new_structure_working(self):
        """Verify that the new structure is fully working before cleanup"""
        self.log("🔍 Verifying new structure is working...")
        
        try:
            # Run database validation
            result = subprocess.run(["python3", "phase3_database_validation.py"], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                self.log(f"❌ Database validation failed: {result.stderr}", "ERROR")
                return False
            
            # Run Phase 2 functionality tests
            result = subprocess.run(["python3", "test_phase2_functionality.py"], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                self.log(f"❌ Phase 2 functionality tests failed: {result.stderr}", "ERROR")
                return False
            
            self.log("✅ New structure verification passed")
            return True
            
        except Exception as e:
            self.log(f"❌ Structure verification failed: {e}", "ERROR")
            return False
    
    def inventory_original_files(self):
        """Create inventory of files to be removed"""
        self.log("📋 Creating inventory of original files...")
        
        files_to_remove = []
        
        if not self.workshop_mgmt_path.exists():
            self.log("⚠️ workshop_management directory not found", "WARNING")
            return files_to_remove
        
        doctype_path = self.workshop_mgmt_path / "doctype"
        if doctype_path.exists():
            for item in doctype_path.iterdir():
                if item.is_dir() and not item.name.startswith('__'):
                    files_to_remove.append(str(item))
                    self.log(f"  📁 {item.name}")
        
        self.log(f"📊 Found {len(files_to_remove)} DocType directories to remove")
        return files_to_remove
    
    def remove_original_doctypes(self, files_to_remove):
        """Safely remove original DocType files"""
        self.log("🗑️ Removing original DocType files...")
        
        removed_count = 0
        
        for file_path in files_to_remove:
            try:
                if os.path.exists(file_path):
                    shutil.rmtree(file_path)
                    self.removed_files.append(file_path)
                    removed_count += 1
                    doctype_name = Path(file_path).name
                    self.log(f"  ✅ Removed {doctype_name}")
                else:
                    self.log(f"  ⚠️ Already removed: {file_path}", "WARNING")
                    
            except Exception as e:
                self.log(f"  ❌ Failed to remove {file_path}: {e}", "ERROR")
                self.errors.append(f"Failed to remove {file_path}: {e}")
        
        self.log(f"✅ Removed {removed_count}/{len(files_to_remove)} DocType directories")
        return removed_count == len(files_to_remove)
    
    def clean_empty_directories(self):
        """Clean up empty directories after removal"""
        self.log("🧹 Cleaning up empty directories...")
        
        try:
            doctype_path = self.workshop_mgmt_path / "doctype"
            
            # Remove doctype directory if empty
            if doctype_path.exists() and not any(doctype_path.iterdir()):
                doctype_path.rmdir()
                self.log("  ✅ Removed empty doctype directory")
            
            # Check if workshop_management directory is mostly empty (only __init__.py and __pycache__)
            if self.workshop_mgmt_path.exists():
                remaining_items = [item for item in self.workshop_mgmt_path.iterdir() 
                                 if not item.name.startswith('__')]
                
                if len(remaining_items) == 0:
                    # Only __init__.py and __pycache__ remain, we can remove the whole directory
                    shutil.rmtree(self.workshop_mgmt_path)
                    self.log("  ✅ Removed empty workshop_management directory")
                else:
                    self.log(f"  ℹ️ workshop_management has {len(remaining_items)} remaining items")
                    for item in remaining_items:
                        self.log(f"    - {item.name}")
            
        except Exception as e:
            self.log(f"❌ Error cleaning directories: {e}", "ERROR")
            self.warnings.append(f"Directory cleanup issue: {e}")
    
    def run_comprehensive_final_tests(self):
        """Run comprehensive tests after cleanup"""
        self.log("🧪 Running comprehensive final tests...")
        
        test_results = {}
        
        # Test 1: Phase 2 functionality
        try:
            result = subprocess.run(["python3", "test_phase2_functionality.py"], 
                                  capture_output=True, text=True)
            test_results["phase2_functionality"] = result.returncode == 0
            if result.returncode == 0:
                self.log("  ✅ Phase 2 functionality tests passed")
            else:
                self.log(f"  ❌ Phase 2 functionality tests failed", "ERROR")
                self.errors.append("Phase 2 functionality tests failed")
        except Exception as e:
            self.log(f"  ❌ Phase 2 test error: {e}", "ERROR")
            test_results["phase2_functionality"] = False
        
        # Test 2: Database validation
        try:
            result = subprocess.run(["python3", "phase3_database_validation.py"], 
                                  capture_output=True, text=True)
            test_results["database_validation"] = result.returncode == 0
            if result.returncode == 0:
                self.log("  ✅ Database validation tests passed")
            else:
                self.log(f"  ❌ Database validation tests failed", "ERROR")
                self.errors.append("Database validation tests failed")
        except Exception as e:
            self.log(f"  ❌ Database validation test error: {e}", "ERROR")
            test_results["database_validation"] = False
        
        # Test 3: Import integrity
        try:
            # Test key imports work
            test_imports = [
                "universal_workshop.workshop_operations.workshop_profile",
                "universal_workshop.workshop_operations.service_order",
                "universal_workshop.system_administration.license_manager",
                "universal_workshop.setup.onboarding.onboarding_progress"
            ]
            
            import_success = True
            for import_path in test_imports:
                module_path = self.app_path / import_path.replace('universal_workshop.', '').replace('.', '/')
                if not (module_path / "__init__.py").exists() and not (module_path.parent / f"{module_path.name}.py").exists():
                    import_success = False
                    self.log(f"    ❌ Import path not found: {import_path}", "ERROR")
                    break
            
            test_results["import_integrity"] = import_success
            if import_success:
                self.log("  ✅ Import integrity tests passed")
            else:
                self.log("  ❌ Import integrity tests failed", "ERROR")
                self.errors.append("Import integrity tests failed")
                
        except Exception as e:
            self.log(f"  ❌ Import integrity test error: {e}", "ERROR")
            test_results["import_integrity"] = False
        
        # Overall test result
        all_passed = all(test_results.values())
        passed_count = sum(test_results.values())
        total_count = len(test_results)
        
        self.log(f"📊 Final tests: {passed_count}/{total_count} passed")
        
        return all_passed, test_results
    
    def update_modules_txt_final(self):
        """Final update to modules.txt to remove workshop_management"""
        self.log("📝 Final update to modules.txt...")
        
        try:
            modules_file = self.app_path / "modules.txt"
            
            if not modules_file.exists():
                self.log("⚠️ modules.txt not found", "WARNING")
                return False
            
            with open(modules_file, 'r') as f:
                modules = f.read().strip().split('\n')
            
            # Remove Workshop Management module if present
            original_count = len(modules)
            modules = [m for m in modules if m != "Workshop Management"]
            
            if len(modules) < original_count:
                with open(modules_file, 'w') as f:
                    f.write('\n'.join(modules) + '\n')
                self.log("✅ Removed Workshop Management from modules.txt")
            else:
                self.log("ℹ️ Workshop Management not found in modules.txt")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error updating modules.txt: {e}", "ERROR")
            self.errors.append(f"modules.txt update failed: {e}")
            return False
    
    def execute_final_cleanup(self):
        """Execute the complete final cleanup process"""
        self.log("🚀 Starting Phase 3: Final Cleanup and Comprehensive Testing")
        self.log("=" * 60)
        
        # Pre-cleanup verification
        if not self.verify_new_structure_working():
            self.log("❌ New structure verification failed - aborting cleanup", "ERROR")
            return False
        
        # Create final safety checkpoint
        checkpoint = self.create_final_safety_checkpoint()
        if not checkpoint:
            self.log("❌ Failed to create safety checkpoint - aborting cleanup", "ERROR")
            return False
        
        # Inventory files to remove
        files_to_remove = self.inventory_original_files()
        
        if not files_to_remove:
            self.log("ℹ️ No original files found to remove")
        else:
            # Remove original files
            if not self.remove_original_doctypes(files_to_remove):
                self.log("⚠️ Some files could not be removed", "WARNING")
            
            # Clean up empty directories
            self.clean_empty_directories()
        
        # Update modules.txt
        self.update_modules_txt_final()
        
        # Run comprehensive final tests
        all_tests_passed, test_results = self.run_comprehensive_final_tests()
        
        # Create final completion checkpoint
        final_tag = f"phase3-completed-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        try:
            subprocess.run(["git", "tag", final_tag], check=True)
            self.log(f"✅ Final completion checkpoint: {final_tag}")
        except Exception as e:
            self.log(f"⚠️ Failed to create completion tag: {e}", "WARNING")
        
        # Summary
        self.log("\n" + "=" * 60)
        if all_tests_passed and len(self.errors) == 0:
            self.log("🎉 PHASE 3 CLEANUP COMPLETED SUCCESSFULLY!")
        else:
            self.log("⚠️ PHASE 3 CLEANUP COMPLETED WITH ISSUES")
        
        self.log(f"📁 Files Removed: {len(self.removed_files)}")
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
        
        # Save final report
        report = {
            "timestamp": datetime.now().isoformat(),
            "phase": "Phase 3: Final Cleanup and Comprehensive Testing",
            "status": "COMPLETED" if all_tests_passed and len(self.errors) == 0 else "COMPLETED_WITH_ISSUES",
            "files_removed": len(self.removed_files),
            "removed_files": self.removed_files,
            "test_results": test_results,
            "errors": self.errors,
            "warnings": self.warnings,
            "checkpoints": [checkpoint, final_tag]
        }
        
        with open("phase3_final_cleanup_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        self.log(f"\n📁 Final cleanup report saved to: phase3_final_cleanup_report.json")
        
        return all_tests_passed and len(self.errors) == 0


def main():
    """Main final cleanup execution"""
    manager = FinalCleanupManager()
    
    try:
        success = manager.execute_final_cleanup()
        return success
    except Exception as e:
        print(f"❌ Final cleanup failed with exception: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)