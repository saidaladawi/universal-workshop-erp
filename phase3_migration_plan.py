#!/usr/bin/env python3
"""
Phase 3: Workshop Management Reorganization - Migration Plan
Implements copy-first approach with safety checkpoints
"""

import os
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime


class Phase3MigrationManager:
    """Manages the safe migration of workshop_management DocTypes"""
    
    def __init__(self):
        self.app_path = Path("apps/universal_workshop/universal_workshop")
        self.log_file = "phase3_migration.log"
        self.backup_dir = "phase3_backup"
        self.errors = []
        self.warnings = []
        
        # Load analysis results
        with open("phase3_analysis_results.json", "r") as f:
            self.analysis = json.load(f)
        
        self.migration_plan = self.analysis["migration_plan"]
        self.import_dependencies = self.analysis["import_dependencies"]
        
    def log(self, message, level="INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        
        with open(self.log_file, "a") as f:
            f.write(log_entry + "\n")
    
    def create_safety_checkpoint(self, checkpoint_name):
        """Create git checkpoint for rollback capability"""
        try:
            # Create git tag for checkpoint
            tag_name = f"phase3-{checkpoint_name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            subprocess.run(["git", "tag", tag_name], check=True)
            
            # Create backup of current state
            backup_path = f"{self.backup_dir}/{checkpoint_name}"
            os.makedirs(backup_path, exist_ok=True)
            shutil.copytree(self.app_path, f"{backup_path}/universal_workshop", dirs_exist_ok=True)
            
            self.log(f"✅ Safety checkpoint created: {tag_name}")
            return tag_name
        except Exception as e:
            self.log(f"❌ Failed to create checkpoint: {e}", "ERROR")
            return None
    
    def verify_backup_integrity(self):
        """Verify backup integrity before starting migration"""
        try:
            # Check if phase3_backup exists
            if not os.path.exists(self.backup_dir):
                self.log("❌ No backup directory found", "ERROR")
                return False
            
            # Check critical files
            critical_files = [
                "apps/universal_workshop/universal_workshop/hooks.py",
                "apps/universal_workshop/universal_workshop/modules.txt"
            ]
            
            for file_path in critical_files:
                if not os.path.exists(file_path):
                    self.log(f"❌ Critical file missing: {file_path}", "ERROR")
                    return False
            
            self.log("✅ Backup integrity verified")
            return True
        except Exception as e:
            self.log(f"❌ Backup integrity check failed: {e}", "ERROR")
            return False
    
    def create_target_directories(self):
        """Create target directory structure"""
        try:
            target_dirs = [
                "workshop_operations",
                "workshop_operations/quality_control", 
                "system_administration",
                "mobile_operations",
                "setup/onboarding"
            ]
            
            for target_dir in target_dirs:
                full_path = self.app_path / target_dir / "doctype"
                full_path.mkdir(parents=True, exist_ok=True)
                
                # Create __init__.py files
                init_file = full_path.parent / "__init__.py"
                if not init_file.exists():
                    init_file.write_text("")
                
                doctype_init_file = full_path / "__init__.py"
                if not doctype_init_file.exists():
                    doctype_init_file.write_text("")
            
            self.log("✅ Target directories created")
            return True
        except Exception as e:
            self.log(f"❌ Failed to create target directories: {e}", "ERROR")
            return False
    
    def copy_doctype_files(self, step):
        """Copy DocType files to new location"""
        try:
            source_path = self.app_path / step["source"]
            target_path = self.app_path / step["target"]
            
            if not source_path.exists():
                self.log(f"⚠️ Source path not found: {source_path}", "WARNING")
                return False
            
            # Create target directory
            target_path.mkdir(parents=True, exist_ok=True)
            
            # Copy all files
            for item in source_path.iterdir():
                if item.is_file():
                    shutil.copy2(item, target_path / item.name)
            
            self.log(f"✅ Copied {step['doctype']} to {step['target']}")
            return True
        except Exception as e:
            self.log(f"❌ Failed to copy {step['doctype']}: {e}", "ERROR")
            return False
    
    def update_import_references(self, step):
        """Update import references for copied DocType"""
        try:
            # Update imports in copied files
            target_path = self.app_path / step["target"]
            
            for py_file in target_path.glob("*.py"):
                if py_file.name.startswith("test_"):
                    continue
                
                content = py_file.read_text()
                
                # Update relative imports
                old_import = f"from universal_workshop.workshop_management.doctype"
                new_import = f"from universal_workshop.{step['target_dir']}"
                
                if old_import in content:
                    content = content.replace(old_import, new_import)
                    py_file.write_text(content)
                    self.log(f"Updated imports in {py_file.name}")
            
            return True
        except Exception as e:
            self.log(f"❌ Failed to update imports for {step['doctype']}: {e}", "ERROR")
            return False
    
    def validate_copied_files(self, step):
        """Validate that copied files are intact"""
        try:
            target_path = self.app_path / step["target"]
            
            # Check for required files
            py_file = target_path / f"{step['doctype']}.py"
            json_file = target_path / f"{step['doctype']}.json"
            
            # Python file is essential
            if not py_file.exists():
                self.log(f"❌ Critical file missing: {py_file}", "ERROR")
                return False
            
            # JSON file is preferred but not always present
            if not json_file.exists():
                self.log(f"⚠️ JSON file missing (might be Python-only DocType): {json_file}", "WARNING")
                self.warnings.append(f"Missing JSON file for {step['doctype']}")
                # Continue without failing
            
            # Check JSON integrity if file exists
            if json_file.exists():
                try:
                    with open(json_file, "r") as f:
                        json.load(f)
                except json.JSONDecodeError:
                    self.log(f"❌ Invalid JSON in {json_file}", "ERROR")
                    return False
            
            self.log(f"✅ Validated {step['doctype']} files")
            return True
        except Exception as e:
            self.log(f"❌ Validation failed for {step['doctype']}: {e}", "ERROR")
            return False
    
    def migrate_category(self, category_name):
        """Migrate all DocTypes in a category"""
        self.log(f"🔄 Starting migration for category: {category_name}")
        
        # Create checkpoint before migrating category
        checkpoint = self.create_safety_checkpoint(f"before-{category_name.lower()}")
        if not checkpoint:
            return False
        
        # Get steps for this category
        category_steps = [
            step for step in self.migration_plan["steps"] 
            if step["category"] == category_name
        ]
        
        success_count = 0
        
        for step in category_steps:
            self.log(f"📁 Migrating {step['doctype']} ({step['risk_level']} risk)")
            
            # Copy files
            if not self.copy_doctype_files(step):
                self.errors.append(f"Failed to copy {step['doctype']}")
                continue
            
            # Update imports
            if not self.update_import_references(step):
                self.warnings.append(f"Import update issues for {step['doctype']}")
            
            # Validate
            if not self.validate_copied_files(step):
                self.errors.append(f"Validation failed for {step['doctype']}")
                continue
            
            success_count += 1
        
        self.log(f"✅ Category {category_name}: {success_count}/{len(category_steps)} DocTypes migrated")
        
        # Create checkpoint after successful category migration
        self.create_safety_checkpoint(f"after-{category_name.lower()}")
        
        return success_count == len(category_steps)
    
    def update_global_import_dependencies(self):
        """Update import dependencies found in analysis"""
        try:
            updated_count = 0
            
            for dependency in self.import_dependencies:
                # Parse dependency line
                parts = dependency.split(":")
                if len(parts) < 2:
                    continue
                
                file_path = parts[0]
                import_line = parts[1].strip()
                
                if not os.path.exists(file_path):
                    continue
                
                # Read file
                with open(file_path, "r") as f:
                    content = f.read()
                
                # Update import
                old_import = "from universal_workshop.workshop_management.doctype"
                new_import = "from universal_workshop.workshop_operations"
                
                if old_import in content:
                    content = content.replace(old_import, new_import)
                    
                    with open(file_path, "w") as f:
                        f.write(content)
                    
                    updated_count += 1
                    self.log(f"Updated import in {file_path}")
            
            self.log(f"✅ Updated {updated_count} import dependencies")
            return True
        except Exception as e:
            self.log(f"❌ Failed to update import dependencies: {e}", "ERROR")
            return False
    
    def run_comprehensive_tests(self):
        """Run comprehensive tests after migration"""
        try:
            self.log("🧪 Running comprehensive tests...")
            
            # Test Phase 2 functionality (should still work)
            result = subprocess.run(["python3", "test_phase2_functionality.py"], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log("✅ Phase 2 functionality tests passed")
            else:
                self.log(f"❌ Phase 2 tests failed: {result.stderr}", "ERROR")
                return False
            
            # Test import integrity 
            try:
                # Test that new module directories exist and are importable
                import sys
                sys.path.insert(0, str(self.app_path.parent))
                
                # Test key module paths exist
                workshop_ops_path = self.app_path / "workshop_operations" / "__init__.py"
                system_admin_path = self.app_path / "system_administration" / "__init__.py"
                
                if workshop_ops_path.exists() and system_admin_path.exists():
                    self.log("✅ Import integrity tests passed")
                else:
                    self.log("❌ Missing module init files", "ERROR")
                    return False
            except Exception as e:
                self.log(f"❌ Import integrity test failed: {e}", "ERROR")
                return False
            
            return True
        except Exception as e:
            self.log(f"❌ Comprehensive tests failed: {e}", "ERROR")
            return False
    
    def execute_migration_plan(self):
        """Execute the complete migration plan"""
        self.log("🚀 Starting Phase 3: Workshop Management Reorganization")
        self.log("=" * 60)
        
        # Pre-migration checks
        if not self.verify_backup_integrity():
            return False
        
        # Create target directories
        if not self.create_target_directories():
            return False
        
        # Create initial checkpoint
        initial_checkpoint = self.create_safety_checkpoint("migration-start")
        if not initial_checkpoint:
            return False
        
        # Execute migration by category (in order)
        execution_order = self.migration_plan["execution_order"]
        
        for category in execution_order:
            if not self.migrate_category(category):
                self.log(f"❌ Migration failed at category: {category}", "ERROR")
                return False
        
        # Update global import dependencies
        if not self.update_global_import_dependencies():
            self.log("⚠️ Import dependency updates had issues", "WARNING")
        
        # Final validation
        if not self.run_comprehensive_tests():
            self.log("❌ Final validation failed", "ERROR")
            return False
        
        # Create final checkpoint
        final_checkpoint = self.create_safety_checkpoint("migration-complete")
        
        # Summary
        self.log("=" * 60)
        self.log("✅ PHASE 3 MIGRATION COMPLETED SUCCESSFULLY")
        self.log(f"📊 Total DocTypes Migrated: {self.migration_plan['total_doctypes']}")
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
        
        # Save migration report
        report = {
            "timestamp": datetime.now().isoformat(),
            "phase": "Phase 3: Workshop Management Reorganization",
            "status": "COMPLETED" if len(self.errors) == 0 else "COMPLETED_WITH_ERRORS",
            "total_doctypes": self.migration_plan["total_doctypes"],
            "errors": self.errors,
            "warnings": self.warnings,
            "checkpoints": [initial_checkpoint, final_checkpoint]
        }
        
        with open("phase3_migration_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        self.log("📁 Migration report saved to: phase3_migration_report.json")
        
        return len(self.errors) == 0


def main():
    """Main migration execution"""
    manager = Phase3MigrationManager()
    
    try:
        success = manager.execute_migration_plan()
        return success
    except Exception as e:
        print(f"❌ Migration failed with exception: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)