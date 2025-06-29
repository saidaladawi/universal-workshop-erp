#!/usr/bin/env python3
"""
Phase 4: Frontend Asset Migration
Copy frontend assets to organized structure
"""

import os
import shutil
import json
import subprocess
from pathlib import Path
from datetime import datetime


class AssetMigrationManager:
    """Manages the migration of frontend assets to organized structure"""
    
    def __init__(self):
        self.app_path = Path("apps/universal_workshop/universal_workshop")
        self.public_path = self.app_path / "public"
        self.assets_path = self.app_path / "assets"
        self.log_file = "phase4_asset_migration.log"
        self.migrated_files = []
        self.errors = []
        self.warnings = []
        
        # Load analysis results
        with open("phase4_frontend_analysis_results.json", "r") as f:
            self.analysis_results = json.load(f)
    
    def log(self, message, level="INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        
        with open(self.log_file, "a") as f:
            f.write(log_entry + "\n")
    
    def create_safety_checkpoint(self):
        """Create safety checkpoint before migration"""
        try:
            # Create git tag
            tag_name = f"phase4-before-migration-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            subprocess.run(["git", "tag", tag_name], check=True)
            
            # Create backup of public directory
            backup_path = f"phase4_backup/public_backup"
            os.makedirs(backup_path, exist_ok=True)
            
            if self.public_path.exists():
                shutil.copytree(self.public_path, f"{backup_path}/public", dirs_exist_ok=True)
            
            self.log(f"✅ Safety checkpoint created: {tag_name}")
            return tag_name
        except Exception as e:
            self.log(f"❌ Failed to create checkpoint: {e}", "ERROR")
            return None
    
    def migrate_javascript_files(self):
        """Migrate JavaScript files to organized structure"""
        self.log("📄 Migrating JavaScript files...")
        
        js_categories = self.analysis_results["javascript"]["categories"]
        success_count = 0
        total_count = 0
        
        for category, files in js_categories.items():
            self.log(f"  📁 Processing {category} category ({len(files)} files)...")
            target_dir = self.assets_path / "js" / category
            target_dir.mkdir(parents=True, exist_ok=True)
            
            for file_info in files:
                total_count += 1
                source_path = self.app_path / file_info["path"]
                target_path = target_dir / file_info["name"]
                
                try:
                    if source_path.exists():
                        shutil.copy2(source_path, target_path)
                        self.migrated_files.append({
                            "type": "js",
                            "source": file_info["path"],
                            "target": str(target_path.relative_to(self.app_path)),
                            "category": category,
                            "size": file_info["size"]
                        })
                        success_count += 1
                        self.log(f"    ✅ {file_info['name']} → {category}/")
                    else:
                        self.log(f"    ⚠️ Source not found: {source_path}", "WARNING")
                        self.warnings.append(f"JS source not found: {file_info['path']}")
                        
                except Exception as e:
                    self.log(f"    ❌ Failed to copy {file_info['name']}: {e}", "ERROR")
                    self.errors.append(f"JS migration failed: {file_info['name']} - {e}")
        
        self.log(f"✅ JavaScript migration: {success_count}/{total_count} files migrated")
        return success_count == total_count
    
    def migrate_css_files(self):
        """Migrate CSS files to organized structure"""
        self.log("🎨 Migrating CSS files...")
        
        css_categories = self.analysis_results["css"]["categories"]
        success_count = 0
        total_count = 0
        
        for category, files in css_categories.items():
            self.log(f"  📁 Processing {category} category ({len(files)} files)...")
            target_dir = self.assets_path / "css" / category
            target_dir.mkdir(parents=True, exist_ok=True)
            
            for file_info in files:
                total_count += 1
                source_path = self.app_path / file_info["path"]
                target_path = target_dir / file_info["name"]
                
                try:
                    if source_path.exists():
                        shutil.copy2(source_path, target_path)
                        self.migrated_files.append({
                            "type": "css",
                            "source": file_info["path"],
                            "target": str(target_path.relative_to(self.app_path)),
                            "category": category,
                            "size": file_info["size"]
                        })
                        success_count += 1
                        self.log(f"    ✅ {file_info['name']} → {category}/")
                    else:
                        self.log(f"    ⚠️ Source not found: {source_path}", "WARNING")
                        self.warnings.append(f"CSS source not found: {file_info['path']}")
                        
                except Exception as e:
                    self.log(f"    ❌ Failed to copy {file_info['name']}: {e}", "ERROR")
                    self.errors.append(f"CSS migration failed: {file_info['name']} - {e}")
        
        self.log(f"✅ CSS migration: {success_count}/{total_count} files migrated")
        return success_count == total_count
    
    def create_index_files(self):
        """Create __init__.py files in asset directories"""
        self.log("📝 Creating index files...")
        
        # Create __init__.py files for Python module recognition
        directories = [
            self.assets_path,
            self.assets_path / "js",
            self.assets_path / "css"
        ]
        
        # Add all category directories
        for category in ["core", "setup", "branding", "workshop", "mobile", "shared", "modules", "analytics", "themes", "localization"]:
            directories.append(self.assets_path / "js" / category)
            directories.append(self.assets_path / "css" / category)
        
        for directory in directories:
            if directory.exists():
                init_file = directory / "__init__.py"
                if not init_file.exists():
                    init_file.write_text(f"# {directory.name.title()} Assets\n")
                    self.log(f"    📝 Created {init_file.relative_to(self.app_path)}")
    
    def validate_migration(self):
        """Validate that all files were migrated correctly"""
        self.log("🔍 Validating migration...")
        
        validation_errors = []
        
        # Check JavaScript files
        js_categories = self.analysis_results["javascript"]["categories"]
        for category, files in js_categories.items():
            target_dir = self.assets_path / "js" / category
            for file_info in files:
                target_path = target_dir / file_info["name"]
                source_path = self.app_path / file_info["path"]
                
                if source_path.exists() and not target_path.exists():
                    validation_errors.append(f"Missing migrated JS file: {target_path}")
                elif target_path.exists():
                    # Check file size
                    if target_path.stat().st_size != file_info["size"]:
                        validation_errors.append(f"JS file size mismatch: {target_path}")
        
        # Check CSS files
        css_categories = self.analysis_results["css"]["categories"]
        for category, files in css_categories.items():
            target_dir = self.assets_path / "css" / category
            for file_info in files:
                target_path = target_dir / file_info["name"]
                source_path = self.app_path / file_info["path"]
                
                if source_path.exists() and not target_path.exists():
                    validation_errors.append(f"Missing migrated CSS file: {target_path}")
                elif target_path.exists():
                    # Check file size
                    if target_path.stat().st_size != file_info["size"]:
                        validation_errors.append(f"CSS file size mismatch: {target_path}")
        
        if validation_errors:
            self.log(f"❌ Validation found {len(validation_errors)} errors:", "ERROR")
            for error in validation_errors:
                self.log(f"  - {error}", "ERROR")
                self.errors.append(error)
            return False
        else:
            self.log("✅ Migration validation passed")
            return True
    
    def create_migration_summary(self):
        """Create detailed migration summary"""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "phase": "Phase 4: Frontend Asset Migration",
            "total_files_migrated": len(self.migrated_files),
            "javascript_files": len([f for f in self.migrated_files if f["type"] == "js"]),
            "css_files": len([f for f in self.migrated_files if f["type"] == "css"]),
            "categories": {},
            "migrated_files": self.migrated_files,
            "errors": self.errors,
            "warnings": self.warnings
        }
        
        # Count by category
        for file_info in self.migrated_files:
            category = file_info["category"]
            if category not in summary["categories"]:
                summary["categories"][category] = {"js": 0, "css": 0}
            summary["categories"][category][file_info["type"]] += 1
        
        return summary
    
    def execute_migration(self):
        """Execute the complete asset migration"""
        self.log("🚀 Starting Phase 4: Frontend Asset Migration")
        self.log("=" * 60)
        
        # Create safety checkpoint
        checkpoint = self.create_safety_checkpoint()
        if not checkpoint:
            self.log("❌ Failed to create safety checkpoint - aborting migration", "ERROR")
            return False
        
        # Migrate files
        js_success = self.migrate_javascript_files()
        css_success = self.migrate_css_files()
        
        # Create index files
        self.create_index_files()
        
        # Validate migration
        validation_success = self.validate_migration()
        
        # Create migration summary
        summary = self.create_migration_summary()
        
        # Create completion checkpoint
        final_tag = f"phase4-migration-complete-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        try:
            subprocess.run(["git", "tag", final_tag], check=True)
            self.log(f"✅ Migration completion checkpoint: {final_tag}")
        except Exception as e:
            self.log(f"⚠️ Failed to create completion tag: {e}", "WARNING")
        
        # Results summary
        self.log("\n" + "=" * 60)
        if js_success and css_success and validation_success and len(self.errors) == 0:
            self.log("🎉 PHASE 4 ASSET MIGRATION COMPLETED SUCCESSFULLY!")
        else:
            self.log("⚠️ PHASE 4 ASSET MIGRATION COMPLETED WITH ISSUES")
        
        self.log(f"📁 Total Files Migrated: {summary['total_files_migrated']}")
        self.log(f"📄 JavaScript Files: {summary['javascript_files']}")
        self.log(f"🎨 CSS Files: {summary['css_files']}")
        self.log(f"🔧 Errors: {len(self.errors)}")
        self.log(f"⚠️ Warnings: {len(self.warnings)}")
        
        # Show category breakdown
        self.log("\n📊 Migration by Category:")
        for category, counts in summary["categories"].items():
            total = counts["js"] + counts["css"]
            self.log(f"  {category}: {total} files (JS: {counts['js']}, CSS: {counts['css']})")
        
        if self.errors:
            self.log("\n❌ Errors encountered:")
            for error in self.errors:
                self.log(f"  - {error}")
        
        if self.warnings:
            self.log("\n⚠️ Warnings:")
            for warning in self.warnings:
                self.log(f"  - {warning}")
        
        # Save migration report
        with open("phase4_asset_migration_report.json", "w") as f:
            json.dump(summary, f, indent=2)
        
        self.log(f"\n📁 Migration report saved to: phase4_asset_migration_report.json")
        
        return js_success and css_success and validation_success and len(self.errors) == 0


def main():
    """Main migration execution"""
    manager = AssetMigrationManager()
    
    try:
        success = manager.execute_migration()
        return success
    except Exception as e:
        print(f"❌ Asset migration failed with exception: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)