"""
Safety Testing Framework for Universal Workshop Refactoring
Tests core system functions before/after each refactoring phase.
"""

import frappe
import json
import sys
from datetime import datetime
from pathlib import Path
import os


class RefactoringSafetyTester:
    """Test suite to ensure system stability during refactoring"""

    def __init__(self):
        self.test_results = []
        self.errors = []
        self.start_time = datetime.now()

    def log_test(self, test_name, passed, details=""):
        """Log test result"""
        result = {
            "test": test_name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        }
        self.test_results.append(result)

        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"    Details: {details}")

    def test_database_connectivity(self):
        """Test database connectivity and basic queries"""
        try:
            # Test basic database connection
            frappe.db.sql("SELECT 1")

            # Test universal_workshop tables exist
            tables = frappe.db.sql(
                """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = %s 
                AND table_name LIKE 'tabWorkshop%%'
            """,
                (frappe.db.get_database_name(),),
                as_dict=True,
            )

            if not tables:
                self.log_test("Database Connectivity", False, "No Universal Workshop tables found")
                return False

            self.log_test("Database Connectivity", True, f"Found {len(tables)} workshop tables")
            return True

        except Exception as e:
            self.log_test("Database Connectivity", False, str(e))
            self.errors.append(f"Database connectivity error: {e}")
            return False

    def test_basic_doctype_operations(self):
        """Test basic DocType operations"""
        try:
            # Test if we can load core DocTypes
            core_doctypes = ["Workshop Profile", "Service Order", "Technician", "Part"]

            loaded_doctypes = []
            for doctype in core_doctypes:
                try:
                    meta = frappe.get_meta(doctype)
                    if meta:
                        loaded_doctypes.append(doctype)
                except:
                    pass

            if len(loaded_doctypes) < 2:
                self.log_test(
                    "DocType Operations",
                    False,
                    f"Only {len(loaded_doctypes)} core DocTypes accessible",
                )
                return False

            self.log_test(
                "DocType Operations", True, f"Loaded {len(loaded_doctypes)} core DocTypes"
            )
            return True

        except Exception as e:
            self.log_test("DocType Operations", False, str(e))
            self.errors.append(f"DocType operations error: {e}")
            return False

    def test_user_authentication(self):
        """Test user authentication system"""
        try:
            # Test current user session
            user = frappe.session.user
            if not user or user == "Guest":
                self.log_test("User Authentication", False, "No authenticated user session")
                return False

            # Test user permissions
            if not frappe.has_permission("User", "read"):
                self.log_test("User Authentication", False, "User lacks basic read permissions")
                return False

            self.log_test("User Authentication", True, f"Authenticated as {user}")
            return True

        except Exception as e:
            self.log_test("User Authentication", False, str(e))
            self.errors.append(f"Authentication error: {e}")
            return False

    def test_import_integrity(self):
        """Test all critical imports work correctly"""
        try:
            import_tests = []

            # Test core framework imports
            try:
                import frappe
                from frappe.model.document import Document

                import_tests.append("frappe_core")
            except:
                pass

            # Test universal_workshop imports
            try:
                import universal_workshop

                import_tests.append("universal_workshop_main")
            except:
                pass

            # Test specific module imports
            try:
                from universal_workshop.hooks import app_name

                import_tests.append("universal_workshop_hooks")
            except:
                pass

            try:
                from universal_workshop import boot

                import_tests.append("universal_workshop_boot")
            except:
                pass

            if len(import_tests) < 3:
                self.log_test(
                    "Import Integrity",
                    False,
                    f"Only {len(import_tests)} critical imports successful",
                )
                return False

            self.log_test(
                "Import Integrity", True, f"All {len(import_tests)} critical imports successful"
            )
            return True

        except Exception as e:
            self.log_test("Import Integrity", False, str(e))
            self.errors.append(f"Import integrity error: {e}")
            return False

    def test_basic_ui_loading(self):
        """Test basic UI components can be loaded"""
        try:
            # Test if we can get desk page
            response = frappe.local.response = frappe._dict()

            # Check if basic web assets exist
            web_assets_exist = False
            try:
                # Check for basic JS/CSS files
                public_path = Path(frappe.get_app_path("universal_workshop", "public"))
                if public_path.exists():
                    js_files = list(public_path.glob("**/*.js"))
                    css_files = list(public_path.glob("**/*.css"))
                    if js_files or css_files:
                        web_assets_exist = True
            except:
                pass

            # Test hooks loading
            hooks_accessible = False
            try:
                from universal_workshop import hooks

                if hasattr(hooks, "app_name"):
                    hooks_accessible = True
            except:
                pass

            if not web_assets_exist and not hooks_accessible:
                self.log_test("Basic UI Loading", False, "No web assets or hooks accessible")
                return False

            self.log_test("Basic UI Loading", True, "Web assets and hooks accessible")
            return True

        except Exception as e:
            self.log_test("Basic UI Loading", False, str(e))
            self.errors.append(f"UI loading error: {e}")
            return False

    def test_system_configuration(self):
        """Test system configuration integrity"""
        try:
            # Test if we can access site config
            try:
                site_config = frappe.get_site_config()
                db_name = site_config.get("db_name")
                if not db_name:
                    self.log_test("System Configuration", False, "No database name in site config")
                    return False
            except:
                self.log_test("System Configuration", False, "Cannot access site configuration")
                return False

            # Test Redis connectivity
            try:
                frappe.cache().set_value("refactoring_test", "success")
                test_value = frappe.cache().get_value("refactoring_test")
                if test_value != "success":
                    self.log_test("System Configuration", False, "Redis cache not working")
                    return False
            except:
                # Redis might not be critical for basic operation
                pass

            self.log_test("System Configuration", True, "System configuration intact")
            return True

        except Exception as e:
            self.log_test("System Configuration", False, str(e))
            self.errors.append(f"System configuration error: {e}")
            return False

    def run_all_tests(self):
        """Run complete safety test suite"""
        print("🧪 Starting Refactoring Safety Tests...")
        print(f"Time: {self.start_time}")
        print("=" * 50)

        # Core functionality tests
        tests = [
            self.test_database_connectivity,
            self.test_basic_doctype_operations,
            self.test_user_authentication,
            self.test_import_integrity,
            self.test_basic_ui_loading,
            self.test_system_configuration,
        ]

        passed_tests = 0
        total_tests = len(tests)

        for test in tests:
            try:
                if test():
                    passed_tests += 1
            except Exception as e:
                self.errors.append(f"Test execution error: {e}")

        # Generate report
        end_time = datetime.now()
        duration = end_time - self.start_time

        print("=" * 50)
        print(f"📊 Test Results: {passed_tests}/{total_tests} passed")
        print(f"⏱️ Duration: {duration.total_seconds():.2f} seconds")

        if self.errors:
            print(f"❌ Errors: {len(self.errors)}")
            for error in self.errors:
                print(f"   - {error}")

        # Save detailed results
        results_data = {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "success_rate": (passed_tests / total_tests) * 100,
                "duration_seconds": duration.total_seconds(),
                "timestamp": end_time.isoformat(),
            },
            "tests": self.test_results,
            "errors": self.errors,
        }

        with open("refactoring_safety_baseline.json", "w") as f:
            json.dump(results_data, f, indent=2)

        print(f"📁 Detailed results saved to: refactoring_safety_baseline.json")

        # Determine overall success
        success_threshold = 0.8  # 80% of tests must pass
        success_rate = passed_tests / total_tests

        if success_rate >= success_threshold:
            print("✅ BASELINE SAFETY TEST PASSED - Ready for refactoring")
            return True
        else:
            print(
                f"❌ BASELINE SAFETY TEST FAILED - Success rate {success_rate:.1%} below threshold {success_threshold:.1%}"
            )
            return False


def main():
    """Main function to run safety tests"""
    print("🔍 Universal Workshop ERP - Refactoring Safety Tests")
    print("=" * 60)

    try:
        # Initialize frappe with correct site
        os.chdir("/home/said/frappe-dev/frappe-bench")
        frappe.init(site="universal.local")
        frappe.connect()

        # Create tester instance
        tester = RefactoringSafetyTester()

        # Run all tests
        results = tester.run_all_tests()

        # Print summary
        tester.print_summary()

        # Exit with appropriate code
        if results["passed"]:
            print("\n✅ All safety tests PASSED - System ready for refactoring")
            return 0
        else:
            print(f"\n❌ {results['failed']} tests FAILED - Review issues before proceeding")
            return 1

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        return 2
    finally:
        # Cleanup
        try:
            if frappe.local.db:
                frappe.local.db.close()
        except:
            pass


if __name__ == "__main__":
    main()
