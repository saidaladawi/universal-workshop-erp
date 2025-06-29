#!/usr/bin/env python3
"""
Phase 4: Old Asset Cleanup
Safe removal of duplicate assets from public/ directory after reorganization
"""

import os
import shutil
import json
import subprocess
from pathlib import Path
from datetime import datetime


class OldAssetCleanupManager:
    """Manages safe cleanup of old duplicate assets"""
    
    def __init__(self):
        self.app_path = Path("apps/universal_workshop/universal_workshop")
        self.public_path = self.app_path / "public"
        self.assets_path = self.app_path / "assets"
        self.log_file = "phase4_cleanup.log"
        self.removed_files = []
        self.preserved_files = []
        self.errors = []
        self.warnings = []
        
    def log(self, message, level="INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        
        with open(self.log_file, "a") as f:
            f.write(log_entry + "\n")
    
    def create_safety_checkpoint(self):
        """Create safety checkpoint before cleanup"""
        try:
            # Create git tag
            tag_name = f"phase4-before-cleanup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            subprocess.run(["git", "tag", tag_name], check=True)
            
            # Create backup of public directory
            backup_path = f"phase4_backup/public_final_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.makedirs(backup_path, exist_ok=True)
            
            if self.public_path.exists():
                shutil.copytree(self.public_path, f"{backup_path}/public", dirs_exist_ok=True)
            
            self.log(f"✅ Safety checkpoint created: {tag_name}")
            self.log(f"✅ Public directory backup: {backup_path}")
            return tag_name
        except Exception as e:
            self.log(f"❌ Failed to create checkpoint: {e}", "ERROR")
            return None
    
    def analyze_files_to_clean(self):
        """Analyze which files need to be cleaned vs preserved"""
        self.log("🔍 Analyzing files for cleanup...")
        
        cleanup_analysis = {
            "js_files": [],
            "css_files": [],
            "preserve_files": [],
            "unknown_files": []
        }
        
        # Check JavaScript files
        js_path = self.public_path / "js"
        if js_path.exists():
            for js_file in js_path.rglob("*.js"):
                file_name = js_file.name
                
                # Check if this file exists in new organized structure
                found_in_assets = False
                for asset_file in self.assets_path.rglob(file_name):
                    if asset_file.name == file_name:
                        found_in_assets = True
                        break
                
                if found_in_assets:
                    cleanup_analysis["js_files"].append({
                        "path": str(js_file.relative_to(self.app_path)),
                        "name": file_name,
                        "size": js_file.stat().st_size
                    })
                else:
                    cleanup_analysis["unknown_files"].append({
                        "path": str(js_file.relative_to(self.app_path)),
                        "name": file_name,
                        "type": "js"
                    })
        
        # Check CSS files
        css_path = self.public_path / "css"
        if css_path.exists():
            for css_file in css_path.rglob("*.css"):
                file_name = css_file.name
                
                # Check if this file exists in new organized structure
                found_in_assets = False
                for asset_file in self.assets_path.rglob(file_name):
                    if asset_file.name == file_name:
                        found_in_assets = True
                        break
                
                if found_in_assets:
                    cleanup_analysis["css_files"].append({
                        "path": str(css_file.relative_to(self.app_path)),
                        "name": file_name,
                        "size": css_file.stat().st_size
                    })
                else:
                    cleanup_analysis["unknown_files"].append({
                        "path": str(css_file.relative_to(self.app_path)),
                        "name": file_name,
                        "type": "css"
                    })
        
        # Check for other important files to preserve
        preserve_patterns = ["manifest.json", ".gitkeep", "*.md", "*.txt"]
        for pattern in preserve_patterns:
            for file_path in self.public_path.rglob(pattern):
                if file_path.is_file():
                    cleanup_analysis["preserve_files"].append({
                        "path": str(file_path.relative_to(self.app_path)),
                        "name": file_path.name,
                        "reason": f"Matches preserve pattern: {pattern}"
                    })
        
        self.log(f"📊 Analysis Results:")
        self.log(f"  📄 JS files to clean: {len(cleanup_analysis['js_files'])}")
        self.log(f"  🎨 CSS files to clean: {len(cleanup_analysis['css_files'])}")
        self.log(f"  📁 Files to preserve: {len(cleanup_analysis['preserve_files'])}")
        self.log(f"  ❓ Unknown files: {len(cleanup_analysis['unknown_files'])}")
        
        if cleanup_analysis["unknown_files"]:
            self.log("⚠️ Unknown files found (will be preserved):", "WARNING")
            for file_info in cleanup_analysis["unknown_files"]:
                self.log(f"    - {file_info['path']}", "WARNING")
        
        return cleanup_analysis
    
    def verify_assets_working(self):
        """Verify that new organized assets are working before cleanup"""
        self.log("✅ Verifying new assets are working...")
        
        try:
            # Run build process to ensure assets work
            result = subprocess.run(
                ["bench", "build", "--app", "universal_workshop"],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                self.log("✅ Build process successful - assets working correctly")
                return True
            else:
                self.log(f"❌ Build process failed: {result.stderr}", "ERROR")
                self.errors.append(f"Build verification failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.log(f"❌ Asset verification failed: {e}", "ERROR")
            self.errors.append(f"Asset verification error: {e}")
            return False
    
    def safe_remove_duplicates(self, cleanup_analysis):
        """Safely remove duplicate files"""
        self.log("🗑️ Removing duplicate asset files...")
        
        removed_count = 0
        total_to_remove = len(cleanup_analysis["js_files"]) + len(cleanup_analysis["css_files"])
        
        # Remove JS files
        for file_info in cleanup_analysis["js_files"]:
            try:
                file_path = self.app_path / file_info["path"]
                if file_path.exists():
                    file_path.unlink()
                    self.removed_files.append(file_info)
                    removed_count += 1
                    self.log(f"  ✅ Removed {file_info['name']} ({file_info['size']} bytes)")
                else:
                    self.log(f"  ⚠️ File not found: {file_info['path']}", "WARNING")
            except Exception as e:
                self.log(f"  ❌ Failed to remove {file_info['path']}: {e}", "ERROR")
                self.errors.append(f"Failed to remove {file_info['path']}: {e}")
        
        # Remove CSS files
        for file_info in cleanup_analysis["css_files"]:
            try:
                file_path = self.app_path / file_info["path"]
                if file_path.exists():
                    file_path.unlink()
                    self.removed_files.append(file_info)
                    removed_count += 1
                    self.log(f"  ✅ Removed {file_info['name']} ({file_info['size']} bytes)")
                else:
                    self.log(f"  ⚠️ File not found: {file_info['path']}", "WARNING")
            except Exception as e:
                self.log(f"  ❌ Failed to remove {file_info['path']}: {e}", "ERROR")
                self.errors.append(f"Failed to remove {file_info['path']}: {e}")
        
        self.log(f"✅ Removed {removed_count}/{total_to_remove} duplicate files")
        return removed_count == total_to_remove
    
    def clean_empty_directories(self):
        """Clean up empty directories after file removal"""
        self.log("🧹 Cleaning empty directories...")
        
        directories_removed = []
        
        # Check js and css directories
        for dir_name in ["js", "css"]:
            dir_path = self.public_path / dir_name
            if dir_path.exists():
                try:
                    # Check if directory is empty (or only contains subdirectories that are empty)
                    if not any(dir_path.rglob("*")):
                        shutil.rmtree(dir_path)
                        directories_removed.append(dir_name)
                        self.log(f"  ✅ Removed empty {dir_name}/ directory")
                    else:
                        remaining_files = list(dir_path.rglob("*"))
                        self.log(f"  📁 {dir_name}/ directory kept ({len(remaining_files)} items remaining)")
                except Exception as e:
                    self.log(f"  ❌ Error removing {dir_name}/ directory: {e}", "ERROR")
                    self.warnings.append(f"Directory cleanup issue: {dir_name} - {e}")
        
        return directories_removed
    
    def verify_cleanup_success(self):
        """Verify cleanup was successful and system still works"""
        self.log("🔍 Verifying cleanup success...")
        
        verification_results = {}
        
        # Test that build still works
        try:
            result = subprocess.run(
                ["bench", "build", "--app", "universal_workshop"],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            verification_results["build_test"] = result.returncode == 0
            if result.returncode == 0:
                self.log("  ✅ Post-cleanup build successful")
            else:
                self.log(f"  ❌ Post-cleanup build failed: {result.stderr}", "ERROR")
                self.errors.append("Post-cleanup build failed")
        except Exception as e:
            verification_results["build_test"] = False
            self.log(f"  ❌ Build verification error: {e}", "ERROR")
        
        # Test that previous functionality still works
        try:
            result = subprocess.run(["python3", "test_phase2_functionality.py"], 
                                  capture_output=True, text=True, timeout=60)
            
            verification_results["functionality_test"] = result.returncode == 0
            if result.returncode == 0:
                self.log("  ✅ Functionality tests passed")
            else:
                self.log("  ❌ Functionality tests failed", "ERROR")
                self.errors.append("Post-cleanup functionality test failed")
        except Exception as e:
            verification_results["functionality_test"] = False
            self.log(f"  ❌ Functionality test error: {e}", "ERROR")
        
        # Check that no assets are missing
        missing_assets = 0
        for asset_file in self.assets_path.rglob("*"):
            if asset_file.is_file() and asset_file.suffix in [".js", ".css"]:
                if not asset_file.exists() or asset_file.stat().st_size == 0:
                    missing_assets += 1
        
        verification_results["assets_intact"] = missing_assets == 0
        if missing_assets == 0:
            self.log("  ✅ All organized assets intact")
        else:
            self.log(f"  ❌ {missing_assets} assets missing or empty", "ERROR")
        
        return all(verification_results.values())
    
    def execute_cleanup(self):
        """Execute the complete cleanup process"""
        self.log("🚀 Starting Phase 4: Old Asset Cleanup")
        self.log("=" * 60)
        
        # Create safety checkpoint
        checkpoint = self.create_safety_checkpoint()
        if not checkpoint:
            self.log("❌ Failed to create safety checkpoint - aborting cleanup", "ERROR")
            return False
        
        # Analyze files to clean
        cleanup_analysis = self.analyze_files_to_clean()
        
        # Verify new assets are working
        if not self.verify_assets_working():
            self.log("❌ New assets verification failed - aborting cleanup", "ERROR")
            return False
        
        # Ask for confirmation (in real scenario)
        total_to_remove = len(cleanup_analysis["js_files"]) + len(cleanup_analysis["css_files"])
        self.log(f"📋 Ready to remove {total_to_remove} duplicate files")
        
        # Remove duplicate files
        removal_success = self.safe_remove_duplicates(cleanup_analysis)
        
        # Clean empty directories
        removed_dirs = self.clean_empty_directories()
        
        # Verify cleanup success
        verification_success = self.verify_cleanup_success()
        
        # Create completion checkpoint
        final_tag = f"phase4-cleanup-complete-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        try:
            subprocess.run(["git", "tag", final_tag], check=True)
            self.log(f"✅ Cleanup completion checkpoint: {final_tag}")
        except Exception as e:
            self.log(f"⚠️ Failed to create completion tag: {e}", "WARNING")
        
        # Results summary
        self.log("\n" + "=" * 60)
        if removal_success and verification_success and len(self.errors) == 0:
            self.log("🎉 PHASE 4 CLEANUP COMPLETED SUCCESSFULLY!")
        else:
            self.log("⚠️ PHASE 4 CLEANUP COMPLETED WITH ISSUES")
        
        self.log(f"🗑️ Files Removed: {len(self.removed_files)}")
        self.log(f"📁 Directories Removed: {len(removed_dirs)}")
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
        
        # Save cleanup report
        report = {
            "timestamp": datetime.now().isoformat(),
            "phase": "Phase 4: Old Asset Cleanup",
            "status": "COMPLETED" if removal_success and verification_success and len(self.errors) == 0 else "COMPLETED_WITH_ISSUES",
            "files_removed": len(self.removed_files),
            "directories_removed": len(removed_dirs),
            "removed_files": self.removed_files,
            "cleanup_analysis": cleanup_analysis,
            "errors": self.errors,
            "warnings": self.warnings
        }
        
        with open("phase4_cleanup_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        self.log(f"\n📁 Cleanup report saved to: phase4_cleanup_report.json")
        
        return removal_success and verification_success and len(self.errors) == 0


def main():
    """Main cleanup execution"""
    manager = OldAssetCleanupManager()
    
    try:
        success = manager.execute_cleanup()
        return success
    except Exception as e:
        print(f"❌ Cleanup failed with exception: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)