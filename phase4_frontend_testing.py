#!/usr/bin/env python3
"""
Phase 4: Frontend Functionality Testing
Comprehensive testing of frontend functionality after asset reorganization
"""

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime


class FrontendTestManager:
    """Manages comprehensive frontend testing for Phase 4"""
    
    def __init__(self):
        self.app_path = Path("apps/universal_workshop/universal_workshop")
        self.log_file = "phase4_frontend_testing.log"
        self.test_results = {}
        self.errors = []
        self.warnings = []
        
    def log(self, message, level="INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        
        with open(self.log_file, "a") as f:
            f.write(log_entry + "\n")
    
    def test_asset_accessibility(self):
        """Test that all assets are accessible from their new paths"""
        self.log("🔍 Testing asset accessibility...")
        
        success_count = 0
        total_count = 0
        missing_assets = []
        
        # Test JavaScript assets
        js_path = self.app_path / "assets" / "js"
        if js_path.exists():
            for js_file in js_path.rglob("*.js"):
                total_count += 1
                if js_file.exists() and js_file.stat().st_size > 0:
                    success_count += 1
                else:
                    missing_assets.append(str(js_file.relative_to(self.app_path)))
        
        # Test CSS assets
        css_path = self.app_path / "assets" / "css"
        if css_path.exists():
            for css_file in css_path.rglob("*.css"):
                total_count += 1
                if css_file.exists() and css_file.stat().st_size > 0:
                    success_count += 1
                else:
                    missing_assets.append(str(css_file.relative_to(self.app_path)))
        
        self.test_results["asset_accessibility"] = {
            "total_assets": total_count,
            "accessible_assets": success_count,
            "missing_assets": missing_assets,
            "success_rate": (success_count / total_count) * 100 if total_count > 0 else 0
        }
        
        self.log(f"✅ Asset accessibility: {success_count}/{total_count} ({self.test_results['asset_accessibility']['success_rate']:.1f}%)")
        
        if missing_assets:
            self.log(f"⚠️ Missing assets found:", "WARNING")
            for asset in missing_assets:
                self.log(f"  - {asset}", "WARNING")
                self.warnings.append(f"Missing asset: {asset}")
        
        return len(missing_assets) == 0
    
    def test_hooks_py_syntax(self):
        """Test hooks.py syntax and imports"""
        self.log("🔧 Testing hooks.py syntax...")
        
        hooks_file = self.app_path / "hooks.py"
        
        try:
            # Test Python syntax
            with open(hooks_file, 'r') as f:
                content = f.read()
            
            compile(content, str(hooks_file), 'exec')
            
            # Test that we can import the module
            import sys
            sys.path.insert(0, str(self.app_path.parent))
            
            # Try to access the asset lists
            namespace = {}
            exec(content, namespace)
            
            js_assets = namespace.get('app_include_js', [])
            css_assets = namespace.get('app_include_css', [])
            
            self.test_results["hooks_syntax"] = {
                "syntax_valid": True,
                "js_assets_count": len(js_assets),
                "css_assets_count": len(css_assets),
                "total_assets": len(js_assets) + len(css_assets)
            }
            
            self.log(f"✅ Hooks.py syntax valid - {len(js_assets)} JS + {len(css_assets)} CSS assets")
            return True
            
        except SyntaxError as e:
            self.log(f"❌ Hooks.py syntax error: {e}", "ERROR")
            self.errors.append(f"Hooks syntax error: {e}")
            self.test_results["hooks_syntax"] = {"syntax_valid": False, "error": str(e)}
            return False
        except Exception as e:
            self.log(f"❌ Hooks.py test error: {e}", "ERROR")
            self.errors.append(f"Hooks test error: {e}")
            self.test_results["hooks_syntax"] = {"syntax_valid": False, "error": str(e)}
            return False
    
    def test_asset_build_process(self):
        """Test that assets can be built successfully"""
        self.log("🏗️ Testing asset build process...")
        
        try:
            # Test bench build command
            result = subprocess.run(
                ["bench", "build", "--app", "universal_workshop"],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                self.log("✅ Asset build process successful")
                self.test_results["asset_build"] = {
                    "success": True,
                    "output": result.stdout[-500:] if len(result.stdout) > 500 else result.stdout  # Last 500 chars
                }
                return True
            else:
                self.log(f"❌ Asset build failed: {result.stderr}", "ERROR")
                self.errors.append(f"Build failed: {result.stderr}")
                self.test_results["asset_build"] = {
                    "success": False,
                    "error": result.stderr,
                    "output": result.stdout
                }
                return False
                
        except subprocess.TimeoutExpired:
            self.log("❌ Asset build timed out", "ERROR")
            self.errors.append("Build process timed out")
            self.test_results["asset_build"] = {"success": False, "error": "Timeout"}
            return False
        except Exception as e:
            self.log(f"❌ Asset build error: {e}", "ERROR")
            self.errors.append(f"Build error: {e}")
            self.test_results["asset_build"] = {"success": False, "error": str(e)}
            return False
    
    def test_category_organization(self):
        """Test that assets are properly organized by category"""
        self.log("📂 Testing category organization...")
        
        expected_categories = {
            "js": ["core", "setup", "branding", "workshop", "mobile", "shared", "analytics", "modules"],
            "css": ["core", "themes", "localization", "branding", "workshop", "mobile", "modules"]
        }
        
        organization_results = {"js": {}, "css": {}}
        
        for asset_type, categories in expected_categories.items():
            for category in categories:
                category_path = self.app_path / "assets" / asset_type / category
                if category_path.exists():
                    files = list(category_path.glob(f"*.{asset_type}"))
                    organization_results[asset_type][category] = {
                        "exists": True,
                        "file_count": len(files),
                        "files": [f.name for f in files]
                    }
                else:
                    organization_results[asset_type][category] = {
                        "exists": False,
                        "file_count": 0,
                        "files": []
                    }
        
        # Calculate success metrics
        js_categories_with_files = sum(1 for cat in organization_results["js"].values() if cat["file_count"] > 0)
        css_categories_with_files = sum(1 for cat in organization_results["css"].values() if cat["file_count"] > 0)
        
        total_js_files = sum(cat["file_count"] for cat in organization_results["js"].values())
        total_css_files = sum(cat["file_count"] for cat in organization_results["css"].values())
        
        self.test_results["category_organization"] = {
            "js_categories_used": js_categories_with_files,
            "css_categories_used": css_categories_with_files,
            "total_js_files": total_js_files,
            "total_css_files": total_css_files,
            "organization_details": organization_results
        }
        
        self.log(f"✅ Category organization: JS({js_categories_with_files} categories, {total_js_files} files) CSS({css_categories_with_files} categories, {total_css_files} files)")
        
        return total_js_files > 0 and total_css_files > 0
    
    def test_previous_functionality(self):
        """Test that previous system functionality still works"""
        self.log("🔄 Testing previous functionality...")
        
        functionality_tests = []
        
        # Test Phase 2 functionality
        try:
            result = subprocess.run(["python3", "test_phase2_functionality.py"], 
                                  capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                functionality_tests.append({"test": "Phase 2 Functionality", "status": "PASSED"})
                self.log("  ✅ Phase 2 functionality tests passed")
            else:
                functionality_tests.append({"test": "Phase 2 Functionality", "status": "FAILED", "error": result.stderr})
                self.log(f"  ❌ Phase 2 functionality tests failed", "ERROR")
                self.errors.append("Phase 2 functionality tests failed")
        except Exception as e:
            functionality_tests.append({"test": "Phase 2 Functionality", "status": "ERROR", "error": str(e)})
            self.log(f"  ❌ Phase 2 test error: {e}", "ERROR")
        
        # Test database validation
        try:
            result = subprocess.run(["python3", "phase3_database_validation.py"], 
                                  capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                functionality_tests.append({"test": "Database Validation", "status": "PASSED"})
                self.log("  ✅ Database validation tests passed")
            else:
                functionality_tests.append({"test": "Database Validation", "status": "FAILED", "error": result.stderr})
                self.log(f"  ❌ Database validation tests failed", "ERROR")
                self.errors.append("Database validation tests failed")
        except Exception as e:
            functionality_tests.append({"test": "Database Validation", "status": "ERROR", "error": str(e)})
            self.log(f"  ❌ Database validation test error: {e}", "ERROR")
        
        self.test_results["previous_functionality"] = {
            "tests": functionality_tests,
            "passed_tests": len([t for t in functionality_tests if t["status"] == "PASSED"]),
            "total_tests": len(functionality_tests)
        }
        
        passed_count = self.test_results["previous_functionality"]["passed_tests"]
        total_count = self.test_results["previous_functionality"]["total_tests"]
        
        self.log(f"✅ Previous functionality: {passed_count}/{total_count} tests passed")
        
        return passed_count == total_count
    
    def test_asset_loading_paths(self):
        """Test asset loading paths in hooks.py"""
        self.log("🔗 Testing asset loading paths...")
        
        hooks_file = self.app_path / "hooks.py"
        path_errors = []
        
        try:
            with open(hooks_file, 'r') as f:
                content = f.read()
            
            # Execute hooks.py to get asset lists
            namespace = {}
            exec(content, namespace)
            
            js_assets = namespace.get('app_include_js', [])
            css_assets = namespace.get('app_include_css', [])
            
            # Test each asset path
            for asset_path in js_assets + css_assets:
                # Convert web path to file system path
                if asset_path.startswith("/assets/universal_workshop/"):
                    file_path = self.app_path / asset_path.replace("/assets/universal_workshop/", "")
                    if not file_path.exists():
                        path_errors.append(f"Asset not found: {asset_path}")
            
            self.test_results["asset_loading_paths"] = {
                "total_assets_tested": len(js_assets) + len(css_assets),
                "path_errors": path_errors,
                "success_rate": ((len(js_assets) + len(css_assets) - len(path_errors)) / (len(js_assets) + len(css_assets))) * 100 if (len(js_assets) + len(css_assets)) > 0 else 0
            }
            
            if path_errors:
                self.log(f"❌ Found {len(path_errors)} asset path errors:", "ERROR")
                for error in path_errors:
                    self.log(f"  - {error}", "ERROR")
                    self.errors.append(error)
                return False
            else:
                self.log(f"✅ All {len(js_assets) + len(css_assets)} asset paths validated")
                return True
                
        except Exception as e:
            self.log(f"❌ Asset path testing error: {e}", "ERROR")
            self.errors.append(f"Asset path testing error: {e}")
            return False
    
    def execute_frontend_testing(self):
        """Execute comprehensive frontend testing"""
        self.log("🚀 Starting Phase 4: Frontend Functionality Testing")
        self.log("=" * 60)
        
        # Run all tests
        tests = [
            ("Asset Accessibility", self.test_asset_accessibility),
            ("Hooks.py Syntax", self.test_hooks_py_syntax),
            ("Category Organization", self.test_category_organization),
            ("Asset Loading Paths", self.test_asset_loading_paths),
            ("Asset Build Process", self.test_asset_build_process),
            ("Previous Functionality", self.test_previous_functionality)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_function in tests:
            self.log(f"\n🧪 Running {test_name}...")
            if test_function():
                passed_tests += 1
                self.log(f"✅ {test_name} PASSED")
            else:
                self.log(f"❌ {test_name} FAILED")
        
        # Overall results
        success_rate = (passed_tests / total_tests) * 100
        
        self.log("\n" + "=" * 60)
        if passed_tests == total_tests:
            self.log("🎉 PHASE 4 FRONTEND TESTING COMPLETED SUCCESSFULLY!")
        else:
            self.log("⚠️ PHASE 4 FRONTEND TESTING COMPLETED WITH ISSUES")
        
        self.log(f"📊 Test Results: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
        self.log(f"🔧 Errors: {len(self.errors)}")
        self.log(f"⚠️ Warnings: {len(self.warnings)}")
        
        # Show detailed results
        self.log("\n📋 Detailed Test Results:")
        for test_name, test_function in tests:
            test_key = test_name.lower().replace(" ", "_").replace(".", "")
            if test_key in self.test_results:
                result = self.test_results[test_key]
                if isinstance(result, dict) and "success_rate" in result:
                    self.log(f"  {test_name}: {result['success_rate']:.1f}% success rate")
                elif isinstance(result, dict) and "syntax_valid" in result:
                    self.log(f"  {test_name}: {'VALID' if result['syntax_valid'] else 'INVALID'}")
                else:
                    self.log(f"  {test_name}: Completed")
        
        if self.errors:
            self.log("\n❌ Errors encountered:")
            for error in self.errors:
                self.log(f"  - {error}")
        
        if self.warnings:
            self.log("\n⚠️ Warnings:")
            for warning in self.warnings:
                self.log(f"  - {warning}")
        
        # Save test report
        report = {
            "timestamp": datetime.now().isoformat(),
            "phase": "Phase 4: Frontend Functionality Testing",
            "status": "PASSED" if passed_tests == total_tests else "FAILED",
            "tests_passed": passed_tests,
            "tests_total": total_tests,
            "success_rate": success_rate,
            "test_results": self.test_results,
            "errors": self.errors,
            "warnings": self.warnings
        }
        
        with open("phase4_frontend_testing_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        self.log(f"\n📁 Frontend testing report saved to: phase4_frontend_testing_report.json")
        
        if passed_tests == total_tests:
            self.log("✅ PHASE 4 FRONTEND ASSET REORGANIZATION COMPLETED SUCCESSFULLY!")
        else:
            self.log("❌ PHASE 4 FRONTEND ASSET REORGANIZATION COMPLETED WITH ISSUES")
        
        return passed_tests == total_tests


def main():
    """Main frontend testing execution"""
    manager = FrontendTestManager()
    
    try:
        success = manager.execute_frontend_testing()
        return success
    except Exception as e:
        print(f"❌ Frontend testing failed with exception: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)