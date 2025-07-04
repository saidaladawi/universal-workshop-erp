# Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import json
import re
from datetime import datetime, timedelta
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today, now, getdate, get_datetime


class SystemTestCase(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields to Document class

    def validate(self):
        """Validate test case data before saving"""
        self.validate_arabic_fields()
        self.validate_test_configuration()
        self.validate_dependencies()
        self.set_default_values()

    def before_save(self):
        """Set calculated fields before saving"""
        self.calculate_estimated_duration()
        self.update_execution_schedule()

    def on_submit(self):
        """Execute when test case is submitted/approved"""
        self.update_status_to_ready()
        self.create_automation_scripts()

    def validate_arabic_fields(self):
        """Validate Arabic field content and RTL support"""
        arabic_fields = [
            "test_case_title_ar",
            "test_description_ar",
            "test_objective_ar",
            "prerequisites_ar",
            "expected_results_ar",
        ]

        for field in arabic_fields:
            if hasattr(self, field) and getattr(self, field):
                text = getattr(self, field)
                if not self.is_arabic_text(text):
                    frappe.msgprint(_("Field {0} should contain Arabic text").format(_(field)))

    def is_arabic_text(self, text):
        """Check if text contains Arabic characters"""
        if not text:
            return True
        arabic_pattern = re.compile(
            r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+"
        )
        return bool(arabic_pattern.search(text))

    def validate_test_configuration(self):
        """Validate test configuration and requirements"""
        # Validate critical test cases have all required fields
        if self.test_priority == "Critical":
            required_fields = ["test_description", "test_objective", "expected_results"]
            for field in required_fields:
                if not getattr(self, field):
                    frappe.throw(_("Critical test cases must have {0}").format(_(field)))

        # Validate performance benchmarks format
        if self.performance_benchmarks:
            self.validate_performance_format()

    def validate_performance_format(self):
        """Validate performance benchmark format"""
        benchmarks = self.performance_benchmarks
        # Expected format: "Operation < X seconds, Process < Y minutes"
        if not re.search(r"<\s*\d+\s*(second|minute|hour)", benchmarks, re.IGNORECASE):
            frappe.msgprint(
                _("Performance benchmarks should specify time limits (e.g., 'Process < 5 seconds')")
            )

    def validate_dependencies(self):
        """Validate test case dependencies and circular references"""
        if self.dependent_test_cases:
            dependencies = self.parse_dependencies()
            for dep in dependencies:
                if not frappe.db.exists("System Test Case", dep):
                    frappe.throw(_("Dependent test case {0} does not exist").format(dep))

                # Check for circular dependencies
                if self.has_circular_dependency(dep):
                    frappe.throw(_("Circular dependency detected with test case {0}").format(dep))

    def parse_dependencies(self):
        """Parse comma-separated dependencies"""
        if not self.dependent_test_cases:
            return []
        return [dep.strip() for dep in self.dependent_test_cases.split(",") if dep.strip()]

    def has_circular_dependency(self, test_case_name, visited=None):
        """Check for circular dependencies recursively"""
        if visited is None:
            visited = set()

        if test_case_name in visited:
            return True

        visited.add(test_case_name)

        dep_case = frappe.get_doc("System Test Case", test_case_name)
        if dep_case.dependent_test_cases:
            dependencies = dep_case.parse_dependencies()
            for dep in dependencies:
                if self.name in dep or self.has_circular_dependency(dep, visited.copy()):
                    return True

        return False

    def set_default_values(self):
        """Set default values for new test cases"""
        if not self.created_by:
            self.created_by = frappe.session.user
        if not self.created_date:
            self.created_date = today()
        if not self.test_case_version:
            self.test_case_version = "1.0"

    def calculate_estimated_duration(self):
        """Calculate total estimated duration from test steps"""
        if self.test_steps:
            total_duration = 0
            try:
                steps = (
                    json.loads(self.test_steps)
                    if isinstance(self.test_steps, str)
                    else self.test_steps
                )
                for step in steps:
                    if isinstance(step, dict) and "estimated_time" in step:
                        total_duration += int(step.get("estimated_time", 0))
                self.estimated_duration = total_duration
            except (json.JSONDecodeError, ValueError, TypeError):
                frappe.log_error(f"Error calculating duration for test case {self.name}")

    def update_execution_schedule(self):
        """Update next execution due date based on test category"""
        if self.test_category in ["Regression Testing", "Compliance Testing"]:
            # Schedule regular execution for critical test types
            if not self.next_execution_due:
                self.next_execution_due = getdate(today()) + timedelta(days=7)

    def update_status_to_ready(self):
        """Update status to ready for testing when submitted"""
        if self.test_status == "Draft":
            self.test_status = "Ready for Testing"

    def create_automation_scripts(self):
        """Generate automation scripts for eligible test cases"""
        if self.automated_test_available and not self.automation_script_path:
            self.generate_automation_script()

    def generate_automation_script(self):
        """Generate basic automation script template"""
        script_content = self.get_automation_template()

        # Create automation script file
        script_path = (
            f"universal_workshop/testing/automation/{self.name.lower().replace(' ', '_')}.py"
        )
        self.automation_script_path = script_path

        # Save script template for manual completion
        frappe.create_folder(f"apps/universal_workshop/universal_workshop/testing/automation")

    def get_automation_template(self):
        """Generate automation script template"""
        return f'''#!/usr/bin/env python3
# Automation script for: {self.test_case_title}
# Generated on: {now()}

from frappe.tests.utils import FrappeTestCase

class Test{self.name.replace('-', '')}(FrappeTestCase):
    """
    Automated test case for: {self.test_case_title}
    Module: {self.test_module}
    Priority: {self.test_priority}
    """
    
    def setUp(self):
        """Setup test data and environment"""
        self.test_data = self.get_test_data()
        
    def test_{self.name.lower().replace('-', '_')}(self):
        """
        Main test execution
        Expected Result: {self.expected_results[:100] if self.expected_results else 'TBD'}...
        """
        # TODO: Implement test steps
        pass
        
    def get_test_data(self):
        """Prepare test data"""
        return {{
            "test_case": "{self.name}",
            "module": "{self.test_module}",
            "priority": "{self.test_priority}"
        }}
        
    def tearDown(self):
        """Cleanup after test execution"""
        pass

if __name__ == "__main__":
    unittest.main()
'''

    @frappe.whitelist()
    def execute_test_case(self, execution_notes="", test_environment="Development"):
        """Execute this test case and create execution log"""

        # Create test execution log
        execution_log = frappe.new_doc("Test Execution Log")
        execution_log.test_case = self.name
        execution_log.test_case_title = self.test_case_title
        execution_log.execution_date = now()
        execution_log.executed_by = frappe.session.user
        execution_log.test_environment = test_environment
        execution_log.execution_status = "In Progress"
        execution_log.execution_summary = (
            execution_notes or f"Executing test case: {self.test_case_title}"
        )

        # Initialize execution metrics
        execution_log.steps_executed = 0
        execution_log.steps_passed = 0
        execution_log.steps_failed = 0

        try:
            execution_log.insert()
            frappe.db.commit()

            # Update test case execution tracking
            self.execution_count = (self.execution_count or 0) + 1
            self.last_executed = now()
            self.save(ignore_permissions=True)

            return {
                "status": "success",
                "execution_log": execution_log.name,
                "message": _("Test execution started successfully"),
            }

        except Exception as e:
            frappe.log_error(f"Error executing test case {self.name}: {str(e)}")
            return {
                "status": "error",
                "message": _("Failed to start test execution: {0}").format(str(e)),
            }

    @frappe.whitelist()
    def get_execution_history(self, limit=10):
        """Get execution history for this test case"""

        history = frappe.get_list(
            "Test Execution Log",
            filters={"test_case": self.name},
            fields=[
                "name",
                "execution_date",
                "executed_by",
                "execution_status",
                "execution_duration",
                "steps_passed",
                "steps_failed",
            ],
            order_by="execution_date desc",
            limit=limit,
        )

        return history

    @frappe.whitelist()
    def generate_test_report(self):
        """Generate comprehensive test case report"""

        report_data = {
            "test_case": self.as_dict(),
            "execution_history": self.get_execution_history(20),
            "success_rate": self.calculate_success_rate(),
            "performance_analysis": self.analyze_performance(),
            "recommendations": self.get_recommendations(),
        }

        return report_data

    def calculate_success_rate(self):
        """Calculate test case success rate"""
        if not self.execution_count:
            return 0

        total_executions = self.execution_count
        failed_executions = self.total_failures or 0

        return ((total_executions - failed_executions) / total_executions) * 100

    def analyze_performance(self):
        """Analyze test case performance trends"""

        recent_executions = frappe.get_list(
            "Test Execution Log",
            filters={"test_case": self.name, "execution_status": "Passed"},
            fields=["execution_duration"],
            order_by="execution_date desc",
            limit=5,
        )

        if not recent_executions:
            return {"status": "No data", "trend": "unknown"}

        durations = [
            exec_log.execution_duration
            for exec_log in recent_executions
            if exec_log.execution_duration
        ]

        if len(durations) < 2:
            return {
                "status": "Insufficient data",
                "trend": "unknown",
                "avg_duration": durations[0] if durations else 0,
            }

        avg_duration = sum(durations) / len(durations)
        trend = (
            "improving"
            if durations[0] < durations[-1]
            else "degrading" if durations[0] > durations[-1] else "stable"
        )

        return {
            "status": "Analyzed",
            "trend": trend,
            "avg_duration": avg_duration,
            "latest_duration": durations[0],
            "baseline_duration": durations[-1],
        }

    def get_recommendations(self):
        """Get recommendations for test case improvement"""
        recommendations = []

        # Check success rate
        success_rate = self.calculate_success_rate()
        if success_rate < 80:
            recommendations.append(
                _("Test case has low success rate ({0}%). Review test steps and data.").format(
                    success_rate
                )
            )

        # Check execution frequency
        if self.last_executed:
            days_since_execution = (getdate(today()) - getdate(self.last_executed)).days
            if days_since_execution > 30:
                recommendations.append(
                    _("Test case not executed for {0} days. Consider regular execution.").format(
                        days_since_execution
                    )
                )

        # Check automation potential
        if not self.automated_test_available and self.execution_count > 5:
            recommendations.append(
                _("Test case executed {0} times. Consider automation.").format(self.execution_count)
            )

        return recommendations

    @frappe.whitelist()
    def bulk_execute_related_tests(self):
        """Execute all related test cases for comprehensive testing"""

        related_tests = self.get_related_test_cases()
        execution_results = []

        for test_case in related_tests:
            try:
                test_doc = frappe.get_doc("System Test Case", test_case)
                result = test_doc.execute_test_case(f"Bulk execution triggered by {self.name}")
                execution_results.append(
                    {
                        "test_case": test_case,
                        "status": result.get("status"),
                        "execution_log": result.get("execution_log"),
                    }
                )
            except Exception as e:
                execution_results.append(
                    {"test_case": test_case, "status": "error", "error": str(e)}
                )

        return execution_results

    def get_related_test_cases(self):
        """Get test cases related to this one"""

        # Get test cases from same module
        related_tests = frappe.get_list(
            "System Test Case",
            filters={
                "test_module": self.test_module,
                "name": ["!=", self.name],
                "test_status": ["in", ["Ready for Testing", "Passed", "Failed"]],
            },
            fields=["name"],
        )

        return [test.name for test in related_tests]


# Utility functions for test case management


@frappe.whitelist()
def bulk_create_test_cases(test_cases_data):
    """Create multiple test cases from JSON data"""

    if isinstance(test_cases_data, str):
        test_cases_data = json.loads(test_cases_data)

    created_tests = []
    errors = []

    for test_data in test_cases_data.get("test_cases", []):
        try:
            test_case = frappe.new_doc("System Test Case")

            # Map basic fields
            field_mapping = {
                "test_case_title": "test_case_title",
                "test_case_title_ar": "test_case_title_ar",
                "test_module": "test_module",
                "test_category": "test_category",
                "test_priority": "test_priority",
                "test_type": "test_type",
                "test_description": "test_description",
                "test_objective": "test_objective",
                "expected_results": "expected_results",
                "performance_benchmarks": "performance_benchmarks",
                "arabic_localization_checks": "arabic_localization_checks",
            }

            for json_field, doctype_field in field_mapping.items():
                if json_field in test_data:
                    setattr(test_case, doctype_field, test_data[json_field])

            # Handle test steps
            if "test_steps" in test_data:
                test_case.test_steps = json.dumps(test_data["test_steps"], indent=2)

            # Set compliance flags
            test_case.oman_vat_compliance = test_data.get("oman_vat_compliance", False)
            test_case.environmental_compliance = test_data.get("environmental_compliance", False)

            test_case.insert()
            created_tests.append(test_case.name)

        except Exception as e:
            errors.append(
                {"test_title": test_data.get("test_case_title", "Unknown"), "error": str(e)}
            )

    return {
        "created_tests": created_tests,
        "errors": errors,
        "summary": f"Created {len(created_tests)} test cases, {len(errors)} errors",
    }


@frappe.whitelist()
def execute_test_suite(test_module=None, test_category=None, test_priority=None):
    """Execute a suite of test cases based on filters"""

    filters = {"test_status": ["in", ["Ready for Testing", "Passed", "Failed"]]}

    if test_module:
        filters["test_module"] = test_module
    if test_category:
        filters["test_category"] = test_category
    if test_priority:
        filters["test_priority"] = test_priority

    test_cases = frappe.get_list(
        "System Test Case", filters=filters, fields=["name", "test_case_title"]
    )

    execution_results = []

    for test_case in test_cases:
        try:
            test_doc = frappe.get_doc("System Test Case", test_case.name)
            result = test_doc.execute_test_case(f"Suite execution - Module: {test_module or 'All'}")
            execution_results.append(
                {
                    "test_case": test_case.name,
                    "title": test_case.test_case_title,
                    "status": result.get("status"),
                    "execution_log": result.get("execution_log"),
                }
            )
        except Exception as e:
            execution_results.append(
                {
                    "test_case": test_case.name,
                    "title": test_case.test_case_title,
                    "status": "error",
                    "error": str(e),
                }
            )

    return {
        "total_tests": len(test_cases),
        "results": execution_results,
        "summary": f"Executed {len(test_cases)} test cases",
    }


@frappe.whitelist()
def get_testing_dashboard_data():
    """Get dashboard data for testing overview"""

    # Test case statistics
    total_tests = frappe.db.count("System Test Case")
    ready_tests = frappe.db.count("System Test Case", {"test_status": "Ready for Testing"})
    passed_tests = frappe.db.count("System Test Case", {"test_status": "Passed"})
    failed_tests = frappe.db.count("System Test Case", {"test_status": "Failed"})

    # Execution statistics
    total_executions = frappe.db.count("Test Execution Log")
    passed_executions = frappe.db.count("Test Execution Log", {"execution_status": "Passed"})
    failed_executions = frappe.db.count("Test Execution Log", {"execution_status": "Failed"})

    # Module distribution
    module_stats = frappe.db.sql(
        """
        SELECT test_module, COUNT(*) as count
        FROM `tabSystem Test Case`
        GROUP BY test_module
        ORDER BY count DESC
    """,
        as_dict=True,
    )

    # Recent execution trends
    recent_executions = frappe.db.sql(
        """
        SELECT DATE(execution_date) as date, 
               COUNT(*) as total,
               SUM(CASE WHEN execution_status = 'Passed' THEN 1 ELSE 0 END) as passed,
               SUM(CASE WHEN execution_status = 'Failed' THEN 1 ELSE 0 END) as failed
        FROM `tabTest Execution Log`
        WHERE execution_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        GROUP BY DATE(execution_date)
        ORDER BY date DESC
        LIMIT 30
    """,
        as_dict=True,
    )

    return {
        "test_case_stats": {
            "total": total_tests,
            "ready": ready_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
        },
        "execution_stats": {
            "total": total_executions,
            "passed": passed_executions,
            "failed": failed_executions,
            "success_rate": (
                (passed_executions / total_executions * 100) if total_executions > 0 else 0
            ),
        },
        "module_distribution": module_stats,
        "execution_trends": recent_executions,
    }
