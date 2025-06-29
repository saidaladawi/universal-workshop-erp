#!/usr/bin/env python3
"""
Phase 4: Frontend Asset Analysis
Comprehensive analysis of JavaScript and CSS files for reorganization
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime


class FrontendAssetAnalyzer:
    """Analyzes current frontend assets for reorganization"""
    
    def __init__(self):
        self.app_path = Path("apps/universal_workshop/universal_workshop")
        self.public_path = self.app_path / "public"
        self.log_file = "phase4_frontend_analysis.log"
        self.analysis_results = {}
        
    def log(self, message, level="INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        
        with open(self.log_file, "a") as f:
            f.write(log_entry + "\n")
    
    def analyze_javascript_files(self):
        """Analyze all JavaScript files"""
        self.log("🔍 Analyzing JavaScript files...")
        
        js_files = []
        js_path = self.public_path / "js"
        
        if js_path.exists():
            for js_file in js_path.rglob("*.js"):
                try:
                    # Read file content to understand its purpose
                    with open(js_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    file_info = {
                        "name": js_file.name,
                        "path": str(js_file.relative_to(self.app_path)),
                        "size": js_file.stat().st_size,
                        "lines": len(content.split('\n')),
                        "category": self.categorize_js_file(js_file.name, content),
                        "dependencies": self.extract_js_dependencies(content),
                        "functions": self.extract_js_functions(content)
                    }
                    
                    js_files.append(file_info)
                    self.log(f"  📄 {js_file.name} ({file_info['size']} bytes, {file_info['lines']} lines) → {file_info['category']}")
                    
                except Exception as e:
                    self.log(f"  ❌ Error analyzing {js_file}: {e}", "ERROR")
        
        self.analysis_results["javascript"] = {
            "total_files": len(js_files),
            "files": js_files,
            "categories": self.group_by_category(js_files)
        }
        
        return js_files
    
    def analyze_css_files(self):
        """Analyze all CSS files"""
        self.log("🎨 Analyzing CSS files...")
        
        css_files = []
        css_path = self.public_path / "css"
        
        if css_path.exists():
            for css_file in css_path.rglob("*.css"):
                try:
                    with open(css_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    file_info = {
                        "name": css_file.name,
                        "path": str(css_file.relative_to(self.app_path)),
                        "size": css_file.stat().st_size,
                        "lines": len(content.split('\n')),
                        "category": self.categorize_css_file(css_file.name, content),
                        "imports": self.extract_css_imports(content),
                        "media_queries": self.count_media_queries(content)
                    }
                    
                    css_files.append(file_info)
                    self.log(f"  🎨 {css_file.name} ({file_info['size']} bytes, {file_info['lines']} lines) → {file_info['category']}")
                    
                except Exception as e:
                    self.log(f"  ❌ Error analyzing {css_file}: {e}", "ERROR")
        
        self.analysis_results["css"] = {
            "total_files": len(css_files),
            "files": css_files,
            "categories": self.group_by_category(css_files)
        }
        
        return css_files
    
    def categorize_js_file(self, filename, content):
        """Categorize JavaScript file based on name and content"""
        filename_lower = filename.lower()
        content_lower = content.lower()
        
        # Core system files
        if any(keyword in filename_lower for keyword in ['boot', 'session', 'auth', 'core', 'setup_check']):
            return "core"
        
        # Setup and onboarding
        if any(keyword in filename_lower for keyword in ['onboarding', 'wizard', 'setup', 'install']):
            return "setup"
        
        # Branding and theming
        if any(keyword in filename_lower for keyword in ['branding', 'theme', 'dark_mode', 'rtl', 'logo']):
            return "branding"
        
        # Workshop operations
        if any(keyword in filename_lower for keyword in ['workshop', 'service', 'technician', 'quality']):
            return "workshop"
        
        # Mobile and PWA
        if any(keyword in filename_lower for keyword in ['mobile', 'pwa', 'app', 'device']):
            return "mobile"
        
        # Utilities and shared
        if any(keyword in filename_lower for keyword in ['utils', 'helper', 'common', 'shared', 'arabic']):
            return "shared"
        
        # Analytics and monitoring
        if any(keyword in filename_lower for keyword in ['analytics', 'monitor', 'track', 'report']):
            return "analytics"
        
        return "modules"
    
    def categorize_css_file(self, filename, content):
        """Categorize CSS file based on name and content"""
        filename_lower = filename.lower()
        
        # Core system styles
        if any(keyword in filename_lower for keyword in ['core', 'base', 'reset', 'normalize']):
            return "core"
        
        # Theme files
        if any(keyword in filename_lower for keyword in ['theme', 'dark', 'light']):
            return "themes"
        
        # RTL and Arabic
        if any(keyword in filename_lower for keyword in ['rtl', 'arabic', 'ar']):
            return "localization"
        
        # Mobile styles
        if any(keyword in filename_lower for keyword in ['mobile', 'responsive', 'pwa']):
            return "mobile"
        
        # Workshop specific
        if any(keyword in filename_lower for keyword in ['workshop', 'service', 'technician']):
            return "workshop"
        
        # Branding
        if any(keyword in filename_lower for keyword in ['branding', 'logo', 'brand']):
            return "branding"
        
        return "modules"
    
    def extract_js_dependencies(self, content):
        """Extract JavaScript dependencies from content"""
        dependencies = []
        
        # Look for imports, requires, and frappe calls
        import_patterns = [
            r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]',
            r'require\([\'"]([^\'"]+)[\'"]\)',
            r'frappe\.require\([\'"]([^\'"]+)[\'"]\)',
            r'include_js\([\'"]([^\'"]+)[\'"]\)'
        ]
        
        for pattern in import_patterns:
            matches = re.findall(pattern, content)
            dependencies.extend(matches)
        
        return list(set(dependencies))  # Remove duplicates
    
    def extract_js_functions(self, content):
        """Extract main function names from JavaScript"""
        functions = []
        
        # Look for function declarations
        function_patterns = [
            r'function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\(',
            r'([a-zA-Z_$][a-zA-Z0-9_$]*)\s*:\s*function\s*\(',
            r'const\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*\(',
            r'let\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*\('
        ]
        
        for pattern in function_patterns:
            matches = re.findall(pattern, content)
            functions.extend(matches)
        
        return list(set(functions))[:10]  # Return first 10 unique functions
    
    def extract_css_imports(self, content):
        """Extract CSS import statements"""
        imports = []
        import_pattern = r'@import\s+[\'"]([^\'"]+)[\'"]'
        matches = re.findall(import_pattern, content)
        return matches
    
    def count_media_queries(self, content):
        """Count media queries in CSS"""
        media_pattern = r'@media\s*\([^{]+\)'
        return len(re.findall(media_pattern, content))
    
    def group_by_category(self, files):
        """Group files by category"""
        categories = {}
        for file_info in files:
            category = file_info["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append(file_info)
        return categories
    
    def analyze_hooks_py(self):
        """Analyze current hooks.py for asset references"""
        self.log("🔧 Analyzing hooks.py for asset references...")
        
        hooks_file = self.app_path / "hooks.py"
        hooks_analysis = {
            "app_include_js": [],
            "app_include_css": [],
            "web_include_js": [],
            "web_include_css": [],
            "other_assets": []
        }
        
        if hooks_file.exists():
            with open(hooks_file, 'r') as f:
                content = f.read()
            
            # Extract asset lists
            js_pattern = r'app_include_js\s*=\s*\[(.*?)\]'
            css_pattern = r'app_include_css\s*=\s*\[(.*?)\]'
            
            js_match = re.search(js_pattern, content, re.DOTALL)
            if js_match:
                js_assets = re.findall(r'[\'"]([^\'"]+)[\'"]', js_match.group(1))
                hooks_analysis["app_include_js"] = js_assets
                self.log(f"  📄 Found {len(js_assets)} JS assets in hooks.py")
            
            css_match = re.search(css_pattern, content, re.DOTALL)
            if css_match:
                css_assets = re.findall(r'[\'"]([^\'"]+)[\'"]', css_match.group(1))
                hooks_analysis["app_include_css"] = css_assets
                self.log(f"  🎨 Found {len(css_assets)} CSS assets in hooks.py")
        
        self.analysis_results["hooks_analysis"] = hooks_analysis
        return hooks_analysis
    
    def create_reorganization_plan(self):
        """Create detailed reorganization plan"""
        self.log("📋 Creating reorganization plan...")
        
        plan = {
            "target_structure": {
                "assets/js/core/": "Core system JavaScript files",
                "assets/js/setup/": "Setup and onboarding scripts", 
                "assets/js/branding/": "Branding and theme scripts",
                "assets/js/workshop/": "Workshop-specific scripts",
                "assets/js/mobile/": "Mobile and PWA scripts",
                "assets/js/shared/": "Shared utilities and helpers",
                "assets/js/modules/": "Module-specific scripts",
                "assets/js/analytics/": "Analytics and monitoring scripts",
                
                "assets/css/core/": "Core system stylesheets",
                "assets/css/themes/": "Theme and color scheme files",
                "assets/css/localization/": "RTL and Arabic styles",
                "assets/css/mobile/": "Mobile and responsive styles",
                "assets/css/workshop/": "Workshop-specific styles",
                "assets/css/branding/": "Branding and logo styles",
                "assets/css/modules/": "Module-specific styles"
            },
            "migration_steps": [],
            "hooks_updates": [],
            "validation_tests": []
        }
        
        # Create migration steps for JavaScript files
        if "javascript" in self.analysis_results:
            js_categories = self.analysis_results["javascript"]["categories"]
            for category, files in js_categories.items():
                target_dir = f"assets/js/{category}/"
                for file_info in files:
                    step = {
                        "type": "js",
                        "source": file_info["path"],
                        "target": f"{target_dir}{file_info['name']}",
                        "category": category,
                        "size": file_info["size"]
                    }
                    plan["migration_steps"].append(step)
        
        # Create migration steps for CSS files
        if "css" in self.analysis_results:
            css_categories = self.analysis_results["css"]["categories"]
            for category, files in css_categories.items():
                target_dir = f"assets/css/{category}/"
                for file_info in files:
                    step = {
                        "type": "css",
                        "source": file_info["path"],
                        "target": f"{target_dir}{file_info['name']}",
                        "category": category,
                        "size": file_info["size"]
                    }
                    plan["migration_steps"].append(step)
        
        self.analysis_results["reorganization_plan"] = plan
        return plan
    
    def execute_analysis(self):
        """Execute comprehensive frontend analysis"""
        self.log("🚀 Starting Phase 4: Frontend Asset Analysis")
        self.log("=" * 60)
        
        # Analyze current assets
        js_files = self.analyze_javascript_files()
        css_files = self.analyze_css_files()
        hooks_analysis = self.analyze_hooks_py()
        
        # Create reorganization plan
        plan = self.create_reorganization_plan()
        
        # Summary
        self.log("\n" + "=" * 60)
        self.log("📊 FRONTEND ASSET ANALYSIS COMPLETE")
        self.log(f"📄 JavaScript Files: {len(js_files)}")
        self.log(f"🎨 CSS Files: {len(css_files)}")
        self.log(f"📋 Migration Steps: {len(plan['migration_steps'])}")
        
        # Show categories
        if "javascript" in self.analysis_results:
            self.log("\n📄 JavaScript Categories:")
            for category, files in self.analysis_results["javascript"]["categories"].items():
                self.log(f"  {category}: {len(files)} files")
        
        if "css" in self.analysis_results:
            self.log("\n🎨 CSS Categories:")
            for category, files in self.analysis_results["css"]["categories"].items():
                self.log(f"  {category}: {len(files)} files")
        
        # Save detailed analysis
        with open("phase4_frontend_analysis_results.json", "w") as f:
            json.dump(self.analysis_results, f, indent=2)
        
        self.log(f"\n📁 Detailed analysis saved to: phase4_frontend_analysis_results.json")
        
        return self.analysis_results


def main():
    """Main analysis execution"""
    analyzer = FrontendAssetAnalyzer()
    
    try:
        results = analyzer.execute_analysis()
        return True
    except Exception as e:
        print(f"❌ Frontend analysis failed with exception: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)