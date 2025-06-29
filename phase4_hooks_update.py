#!/usr/bin/env python3
"""
Phase 4: Hooks.py Update for Organized Assets
Update hooks.py to reference new organized asset paths
"""

import os
import re
import json
import subprocess
from pathlib import Path
from datetime import datetime


class HooksUpdateManager:
    """Manages the update of hooks.py for organized assets"""
    
    def __init__(self):
        self.app_path = Path("apps/universal_workshop/universal_workshop")
        self.hooks_file = self.app_path / "hooks.py"
        self.log_file = "phase4_hooks_update.log"
        self.updated_paths = []
        self.errors = []
        self.warnings = []
        
        # Load migration results
        with open("phase4_asset_migration_report.json", "r") as f:
            self.migration_report = json.load(f)
        
        # Create mapping of old paths to new paths
        self.path_mapping = {}
        for file_info in self.migration_report["migrated_files"]:
            old_path = f"/assets/universal_workshop/{file_info['type']}/{Path(file_info['source']).name}"
            new_path = f"/assets/universal_workshop/{file_info['target']}"
            self.path_mapping[old_path] = new_path
    
    def log(self, message, level="INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        
        with open(self.log_file, "a") as f:
            f.write(log_entry + "\n")
    
    def create_safety_checkpoint(self):
        """Create safety checkpoint before updating hooks.py"""
        try:
            # Create git tag
            tag_name = f"phase4-before-hooks-update-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            subprocess.run(["git", "tag", tag_name], check=True)
            
            # Create backup of hooks.py
            backup_path = f"phase4_backup/hooks_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
            os.makedirs("phase4_backup", exist_ok=True)
            
            if self.hooks_file.exists():
                with open(self.hooks_file, 'r') as f:
                    content = f.read()
                with open(backup_path, 'w') as f:
                    f.write(content)
            
            self.log(f"✅ Safety checkpoint created: {tag_name}")
            self.log(f"✅ Hooks.py backup created: {backup_path}")
            return tag_name
        except Exception as e:
            self.log(f"❌ Failed to create checkpoint: {e}", "ERROR")
            return None
    
    def analyze_current_hooks(self):
        """Analyze current hooks.py for asset references"""
        self.log("🔍 Analyzing current hooks.py...")
        
        if not self.hooks_file.exists():
            self.log("❌ hooks.py not found", "ERROR")
            return None
        
        with open(self.hooks_file, 'r') as f:
            content = f.read()
        
        # Extract asset arrays
        analysis = {
            "app_include_js": [],
            "app_include_css": [],
            "web_include_js": [],
            "web_include_css": [],
            "original_content": content
        }
        
        # Find JavaScript assets
        js_pattern = r'app_include_js\s*=\s*\[(.*?)\]'
        js_match = re.search(js_pattern, content, re.DOTALL)
        if js_match:
            js_assets = re.findall(r'[\'"]([^\'"]+)[\'"]', js_match.group(1))
            analysis["app_include_js"] = js_assets
            self.log(f"  📄 Found {len(js_assets)} JS assets")
        
        # Find CSS assets
        css_pattern = r'app_include_css\s*=\s*\[(.*?)\]'
        css_match = re.search(css_pattern, content, re.DOTALL)
        if css_match:
            css_assets = re.findall(r'[\'"]([^\'"]+)[\'"]', css_match.group(1))
            analysis["app_include_css"] = css_assets
            self.log(f"  🎨 Found {len(css_assets)} CSS assets")
        
        return analysis
    
    def create_organized_asset_lists(self):
        """Create organized asset lists based on new structure"""
        self.log("📋 Creating organized asset lists...")
        
        organized_assets = {
            "app_include_js": {
                "core": [],
                "setup": [],
                "branding": [],
                "workshop": [],
                "mobile": [],
                "shared": [],
                "analytics": [],
                "modules": []
            },
            "app_include_css": {
                "core": [],
                "themes": [],
                "localization": [],
                "branding": [],
                "workshop": [],
                "mobile": [],
                "modules": []
            }
        }
        
        # Organize JavaScript files
        for file_info in self.migration_report["migrated_files"]:
            if file_info["type"] == "js":
                category = file_info["category"]
                new_path = f"/assets/universal_workshop/{file_info['target']}"
                if category in organized_assets["app_include_js"]:
                    organized_assets["app_include_js"][category].append(new_path)
                else:
                    # Fallback to modules category
                    organized_assets["app_include_js"]["modules"].append(new_path)
            
            elif file_info["type"] == "css":
                category = file_info["category"]
                new_path = f"/assets/universal_workshop/{file_info['target']}"
                if category in organized_assets["app_include_css"]:
                    organized_assets["app_include_css"][category].append(new_path)
                else:
                    # Fallback to modules category
                    organized_assets["app_include_css"]["modules"].append(new_path)
        
        # Sort within categories for consistency
        for js_category in organized_assets["app_include_js"]:
            organized_assets["app_include_js"][js_category].sort()
        
        for css_category in organized_assets["app_include_css"]:
            organized_assets["app_include_css"][css_category].sort()
        
        return organized_assets
    
    def generate_new_hooks_content(self, current_analysis, organized_assets):
        """Generate new hooks.py content with organized assets"""
        self.log("✍️ Generating new hooks.py content...")
        
        content = current_analysis["original_content"]
        
        # Generate organized JS asset list
        js_lines = ["# JavaScript Assets - Organized by Category"]
        js_lines.append("app_include_js = [")
        
        # Add assets by category with clear organization
        for category, assets in organized_assets["app_include_js"].items():
            if assets:
                js_lines.append(f"\t# {category.title()} Assets")
                for asset in assets:
                    js_lines.append(f"\t\"{asset}\",")
                js_lines.append("")
        
        # Remove trailing empty line and close array
        if js_lines[-1] == "":
            js_lines.pop()
        js_lines.append("]")
        
        # Generate organized CSS asset list
        css_lines = ["", "# CSS Assets - Organized by Category"]
        css_lines.append("app_include_css = [")
        
        for category, assets in organized_assets["app_include_css"].items():
            if assets:
                css_lines.append(f"\t# {category.title()} Assets")
                for asset in assets:
                    css_lines.append(f"\t\"{asset}\",")
                css_lines.append("")
        
        # Remove trailing empty line and close array
        if css_lines[-1] == "":
            css_lines.pop()
        css_lines.append("]")
        
        # Replace existing asset lists
        new_js_content = "\n".join(js_lines)
        new_css_content = "\n".join(css_lines)
        
        # Replace JS assets
        js_pattern = r'app_include_js\s*=\s*\[.*?\]'
        content = re.sub(js_pattern, new_js_content, content, flags=re.DOTALL)
        
        # Replace CSS assets
        css_pattern = r'app_include_css\s*=\s*\[.*?\]'
        content = re.sub(css_pattern, new_css_content, content, flags=re.DOTALL)
        
        return content
    
    def validate_asset_paths(self, organized_assets):
        """Validate that all asset paths exist"""
        self.log("✅ Validating asset paths...")
        
        validation_errors = []
        
        # Check JS assets
        for category, assets in organized_assets["app_include_js"].items():
            for asset_path in assets:
                # Convert web path to file system path
                file_path = self.app_path / asset_path.replace("/assets/universal_workshop/", "")
                if not file_path.exists():
                    validation_errors.append(f"Missing JS file: {file_path}")
        
        # Check CSS assets
        for category, assets in organized_assets["app_include_css"].items():
            for asset_path in assets:
                # Convert web path to file system path
                file_path = self.app_path / asset_path.replace("/assets/universal_workshop/", "")
                if not file_path.exists():
                    validation_errors.append(f"Missing CSS file: {file_path}")
        
        if validation_errors:
            self.log(f"❌ Found {len(validation_errors)} validation errors:", "ERROR")
            for error in validation_errors:
                self.log(f"  - {error}", "ERROR")
                self.errors.append(error)
            return False
        else:
            self.log("✅ All asset paths validated successfully")
            return True
    
    def test_hooks_syntax(self, content):
        """Test hooks.py syntax before saving"""
        self.log("🧪 Testing hooks.py syntax...")
        
        try:
            # Write content to temporary file and test
            temp_file = "temp_hooks_test.py"
            with open(temp_file, 'w') as f:
                f.write(content)
            
            # Try to compile the Python file
            with open(temp_file, 'r') as f:
                compile(f.read(), temp_file, 'exec')
            
            # Clean up
            os.remove(temp_file)
            
            self.log("✅ Hooks.py syntax validation passed")
            return True
            
        except SyntaxError as e:
            self.log(f"❌ Syntax error in hooks.py: {e}", "ERROR")
            self.errors.append(f"Syntax error: {e}")
            return False
        except Exception as e:
            self.log(f"❌ Error testing hooks.py: {e}", "ERROR")
            self.errors.append(f"Testing error: {e}")
            return False
    
    def execute_hooks_update(self):
        """Execute the complete hooks.py update"""
        self.log("🚀 Starting Phase 4: Hooks.py Update")
        self.log("=" * 60)
        
        # Create safety checkpoint
        checkpoint = self.create_safety_checkpoint()
        if not checkpoint:
            self.log("❌ Failed to create safety checkpoint - aborting update", "ERROR")
            return False
        
        # Analyze current hooks
        current_analysis = self.analyze_current_hooks()
        if not current_analysis:
            return False
        
        # Create organized asset lists
        organized_assets = self.create_organized_asset_lists()
        
        # Validate asset paths
        if not self.validate_asset_paths(organized_assets):
            self.log("❌ Asset path validation failed", "ERROR")
            return False
        
        # Generate new content
        new_content = self.generate_new_hooks_content(current_analysis, organized_assets)
        
        # Test syntax
        if not self.test_hooks_syntax(new_content):
            self.log("❌ Syntax validation failed", "ERROR")
            return False
        
        # Save updated hooks.py
        try:
            with open(self.hooks_file, 'w') as f:
                f.write(new_content)
            self.log("✅ hooks.py updated successfully")
        except Exception as e:
            self.log(f"❌ Failed to save hooks.py: {e}", "ERROR")
            self.errors.append(f"Save error: {e}")
            return False
        
        # Create completion checkpoint
        final_tag = f"phase4-hooks-updated-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        try:
            subprocess.run(["git", "tag", final_tag], check=True)
            self.log(f"✅ Hooks update completion checkpoint: {final_tag}")
        except Exception as e:
            self.log(f"⚠️ Failed to create completion tag: {e}", "WARNING")
        
        # Summary
        self.log("\n" + "=" * 60)
        if len(self.errors) == 0:
            self.log("🎉 PHASE 4 HOOKS UPDATE COMPLETED SUCCESSFULLY!")
        else:
            self.log("⚠️ PHASE 4 HOOKS UPDATE COMPLETED WITH ISSUES")
        
        # Calculate statistics
        total_js = sum(len(assets) for assets in organized_assets["app_include_js"].values())
        total_css = sum(len(assets) for assets in organized_assets["app_include_css"].values())
        
        self.log(f"📄 JavaScript Assets Organized: {total_js}")
        self.log(f"🎨 CSS Assets Organized: {total_css}")
        self.log(f"🔧 Errors: {len(self.errors)}")
        self.log(f"⚠️ Warnings: {len(self.warnings)}")
        
        # Show organization summary
        self.log("\n📊 Asset Organization Summary:")
        self.log("JavaScript:")
        for category, assets in organized_assets["app_include_js"].items():
            if assets:
                self.log(f"  {category}: {len(assets)} files")
        
        self.log("CSS:")
        for category, assets in organized_assets["app_include_css"].items():
            if assets:
                self.log(f"  {category}: {len(assets)} files")
        
        if self.errors:
            self.log("\n❌ Errors encountered:")
            for error in self.errors:
                self.log(f"  - {error}")
        
        # Save update report
        report = {
            "timestamp": datetime.now().isoformat(),
            "phase": "Phase 4: Hooks.py Update",
            "status": "COMPLETED" if len(self.errors) == 0 else "COMPLETED_WITH_ERRORS",
            "total_js_assets": total_js,
            "total_css_assets": total_css,
            "organized_assets": organized_assets,
            "errors": self.errors,
            "warnings": self.warnings
        }
        
        with open("phase4_hooks_update_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        self.log(f"\n📁 Hooks update report saved to: phase4_hooks_update_report.json")
        
        return len(self.errors) == 0


def main():
    """Main hooks update execution"""
    manager = HooksUpdateManager()
    
    try:
        success = manager.execute_hooks_update()
        return success
    except Exception as e:
        print(f"❌ Hooks update failed with exception: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)