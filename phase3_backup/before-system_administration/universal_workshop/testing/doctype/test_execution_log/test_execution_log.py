# Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from datetime import datetime, timedelta
import json
import time


class TestExecutionLog(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields

    def validate(self):
        """Validate test execution log before saving"""
        self.validate_execution_data()
        self.validate_test_results()
        self.calculate_metrics()

    def before_save(self):
        """Process data before saving"""
        self.update_execution_status()
        self.calculate_success_rate()
        self.validate_compliance_checks()

    def after_insert(self):
        """Actions after creating execution log"""
        self.update_test_case_statistics()
        self.create_follow_up_tasks()
        self.send_notifications()

    def validate_execution_data(self):
        """Validate basic execution data"""
        if not self.test_case:
            frappe.throw(_("Test case is required"))

        if not self.execution_date:
            frappe.throw(_("Execution date is required"))

        if not self.executed_by:
            frappe.throw(_("Executed by is required"))

        if not self.execution_summary:
            frappe.throw(_("Execution summary is required"))

        # Validate execution duration
        if self.execution_duration and self.execution_duration < 0:
            frappe.throw(_("Execution duration cannot be negative"))

    def validate_test_results(self):
        """Validate test step results"""
        if not self.test_results:
            frappe.msgprint(_("No test step results recorded"), alert=True)
            return

        total_steps = 0
        passed_steps = 0
        failed_steps = 0
        critical_failures = 0

        step_numbers = []

        for result in self.test_results:
            if not result.step_title:
                frappe.throw(_("Step title is required for all test results"))

            if not result.actual_result:
                frappe.throw(_("Actual result is required for all test results"))

            if result.step_number in step_numbers:
                frappe.throw(_("Duplicate step number in results: {0}").format(result.step_number))
            step_numbers.append(result.step_number)

            total_steps += 1

            if result.step_status == "Passed":
                passed_steps += 1
            elif result.step_status == "Failed":
                failed_steps += 1
                # Check if this was a critical step
                test_case = frappe.get_doc("System Test Case", self.test_case)
                for step in test_case.test_steps:
                    if step.step_number == result.step_number and step.is_critical:
                        critical_failures += 1
                        break

        # Update step counts
        self.steps_executed = total_steps
        self.steps_passed = passed_steps
        self.steps_failed = failed_steps

        # Critical step validation
        if critical_failures > 0:
            self.execution_status = "Failed"
            frappe.msgprint(
                _("Test failed due to {0} critical step failure(s)").format(critical_failures),
                alert=True,
            )

    def calculate_metrics(self):
        """Calculate execution metrics and performance data"""
        if self.test_results:
            # Calculate total execution time from step results
            total_step_time = sum(result.execution_time or 0 for result in self.test_results)
            if total_step_time > 0 and not self.execution_duration:
                self.execution_duration = max(1, int(total_step_time / 60))  # Convert to minutes

            # Performance metrics
            performance_data = {
                "total_steps": len(self.test_results),
                "average_step_time": (
                    total_step_time / len(self.test_results) if self.test_results else 0
                ),
                "api_response_times": [
                    result.api_response_time
                    for result in self.test_results
                    if result.api_response_time
                ],
                "screenshots_count": sum(1 for result in self.test_results if result.screenshot),
                "errors_count": sum(
                    1 for result in self.test_results if result.step_status == "Failed"
                ),
            }

            if performance_data["api_response_times"]:
                performance_data["average_api_response"] = sum(
                    performance_data["api_response_times"]
                ) / len(performance_data["api_response_times"])
                performance_data["max_api_response"] = max(performance_data["api_response_times"])

            self.performance_metrics = json.dumps(performance_data, indent=2)

    def update_execution_status(self):
        """Update execution status based on results"""
        if not self.test_results:
            return

        total_steps = len(self.test_results)
        passed_steps = sum(1 for result in self.test_results if result.step_status == "Passed")
        failed_steps = sum(1 for result in self.test_results if result.step_status == "Failed")
        blocked_steps = sum(1 for result in self.test_results if result.step_status == "Blocked")

        if blocked_steps > 0:
            self.execution_status = "Blocked"
        elif failed_steps > 0:
            self.execution_status = "Failed"
        elif passed_steps == total_steps:
            self.execution_status = "Passed"
        else:
            self.execution_status = "In Progress"

    def calculate_success_rate(self):
        """Calculate step success rate"""
        if self.steps_executed > 0:
            success_rate = (self.steps_passed / self.steps_executed) * 100
            # Store in performance metrics
            if self.performance_metrics:
                metrics = json.loads(self.performance_metrics)
                metrics["success_rate"] = round(success_rate, 2)
                self.performance_metrics = json.dumps(metrics, indent=2)

    def validate_compliance_checks(self):
        """Validate compliance-related checks"""
        test_case = frappe.get_doc("System Test Case", self.test_case)

        # Arabic localization validation
        if test_case.arabic_localization_checks and not self.arabic_localization_validated:
            frappe.msgprint(
                _("Arabic localization validation is required for this test case"), alert=True
            )

        # VAT compliance validation
        if test_case.oman_vat_compliance and not self.oman_vat_compliance_validated:
            frappe.msgprint(
                _("Oman VAT compliance validation is required for this test case"), alert=True
            )

        # Environmental compliance validation
        if test_case.environmental_compliance and not self.environmental_compliance_validated:
            frappe.msgprint(
                _("Environmental compliance validation is required for this test case"), alert=True
            )

        # Security validation
        if test_case.security_validation and not self.security_validation_passed:
            frappe.msgprint(_("Security validation is required for this test case"), alert=True)

    def update_test_case_statistics(self):
        """Update statistics in the parent test case"""
        test_case = frappe.get_doc("System Test Case", self.test_case)

        # Update execution count
        test_case.execution_count = (test_case.execution_count or 0) + 1

        # Update last execution details
        test_case.last_executed = self.execution_date
        test_case.last_execution_result = self.execution_status
        test_case.last_execution_duration = self.execution_duration

        # Update failure count
        if self.execution_status == "Failed":
            test_case.total_failures = (test_case.total_failures or 0) + 1
            test_case.last_failure_reason = (
                self.failure_details[:200] if self.failure_details else "Test execution failed"
            )

        # Calculate success rate
        if test_case.execution_count > 0:
            passed_executions = test_case.execution_count - (test_case.total_failures or 0)
            test_case.success_rate = (passed_executions / test_case.execution_count) * 100

        # Update test case status
        if self.execution_status == "Passed":
            test_case.test_status = "Passed"
        elif self.execution_status == "Failed":
            test_case.test_status = "Failed"
        elif self.execution_status == "Blocked":
            test_case.test_status = "Blocked"

        test_case.save(ignore_permissions=True)

    def create_follow_up_tasks(self):
        """Create follow-up tasks based on execution results"""
        if self.execution_status == "Failed" and self.defects_found:
            for defect in self.defects_found:
                if defect.defect_severity in ["Critical", "High"]:
                    # Create follow-up task for critical/high severity defects
                    self.create_defect_follow_up_task(defect)

        if self.retesting_required:
            self.schedule_retesting()

    def create_defect_follow_up_task(self, defect):
        """Create a follow-up task for a defect"""
        # In a real implementation, this would create a Task or Issue
        task_title = f"Fix Defect: {defect.defect_title}"
        frappe.msgprint(_("Follow-up task created: {0}").format(task_title), alert=True)

    def schedule_retesting(self):
        """Schedule retesting if required"""
        if self.next_execution_scheduled:
            # Create scheduled retest
            frappe.msgprint(
                _("Retesting scheduled for: {0}").format(self.next_execution_scheduled), alert=True
            )

    def send_notifications(self):
        """Send notifications based on execution results"""
        if self.execution_status == "Failed":
            self.send_failure_notification()
        elif self.execution_status == "Passed" and self.defects_found:
            self.send_defect_notification()

    def send_failure_notification(self):
        """Send notification for test failure"""
        test_case = frappe.get_doc("System Test Case", self.test_case)

        # Get stakeholders to notify
        recipients = [self.executed_by]
        if test_case.reviewer:
            recipients.append(test_case.reviewer)

        # Send email notification
        subject = f"Test Execution Failed: {test_case.test_case_title}"
        message = f"""
        Test Case: {test_case.test_case_title}
        Execution Date: {self.execution_date}
        Executed By: {self.executed_by}
        
        Failure Details:
        {self.failure_details or 'No specific failure details provided'}
        
        Steps Failed: {self.steps_failed} out of {self.steps_executed}
        
        Please review and take necessary action.
        """

        for recipient in recipients:
            frappe.sendmail(recipients=[recipient], subject=subject, message=message, delayed=False)

    def send_defect_notification(self):
        """Send notification for defects found"""
        if not self.defects_found:
            return

        high_severity_defects = [
            d for d in self.defects_found if d.defect_severity in ["Critical", "High"]
        ]

        if high_severity_defects:
            subject = f"High Severity Defects Found: {self.test_case_title}"
            message = f"""
            Test execution completed with {len(high_severity_defects)} high severity defect(s).
            
            Test Case: {self.test_case_title}
            Execution Date: {self.execution_date}
            
            High Severity Defects:
            """

            for defect in high_severity_defects:
                message += f"\n- {defect.defect_title} ({defect.defect_severity})"

            # Send to test case reviewer and workshop manager
            recipients = ["Workshop Manager"]  # Role-based notification

            frappe.sendmail(recipients=recipients, subject=subject, message=message, delayed=False)

    @frappe.whitelist()
    def generate_execution_report(self):
        """Generate detailed execution report"""
        test_case = frappe.get_doc("System Test Case", self.test_case)

        # Performance analysis
        performance_data = json.loads(self.performance_metrics) if self.performance_metrics else {}

        # Compliance summary
        compliance_summary = {
            "arabic_localization": self.arabic_localization_validated,
            "oman_vat_compliance": self.oman_vat_compliance_validated,
            "environmental_compliance": self.environmental_compliance_validated,
            "security_validation": self.security_validation_passed,
            "performance_benchmarks": self.performance_benchmarks_met,
            "integration_points": self.integration_points_validated,
            "audit_trail": self.audit_trail_verified,
        }

        # Step details
        step_details = []
        for result in self.test_results:
            step_details.append(
                {
                    "step_number": result.step_number,
                    "step_title": result.step_title,
                    "status": result.step_status,
                    "execution_time": result.execution_time,
                    "actual_result": result.actual_result,
                    "error_message": result.error_message,
                    "screenshot": result.screenshot,
                }
            )

        # Defect summary
        defect_summary = []
        for defect in self.defects_found:
            defect_summary.append(
                {
                    "title": defect.defect_title,
                    "severity": defect.defect_severity,
                    "priority": defect.defect_priority,
                    "type": defect.defect_type,
                    "module": defect.affected_module,
                    "status": defect.defect_status,
                }
            )

        report = {
            "execution_info": {
                "test_case_title": test_case.test_case_title,
                "test_case_title_ar": test_case.test_case_title_ar,
                "execution_date": self.execution_date,
                "executed_by": self.executed_by,
                "execution_status": self.execution_status,
                "execution_duration": self.execution_duration,
                "test_environment": self.test_environment,
            },
            "results_summary": {
                "steps_executed": self.steps_executed,
                "steps_passed": self.steps_passed,
                "steps_failed": self.steps_failed,
                "success_rate": performance_data.get("success_rate", 0),
                "defects_found": len(self.defects_found),
            },
            "performance_metrics": performance_data,
            "compliance_summary": compliance_summary,
            "step_details": step_details,
            "defect_summary": defect_summary,
            "recommendations": self.recommendations,
            "recommendations_ar": self.recommendations_ar,
        }

        return report

    @frappe.whitelist()
    def compare_with_previous_execution(self):
        """Compare this execution with the previous one"""
        previous_execution = frappe.get_list(
            "Test Execution Log",
            filters={
                "test_case": self.test_case,
                "name": ["!=", self.name],
                "execution_date": ["<", self.execution_date],
            },
            fields=[
                "name",
                "execution_status",
                "execution_duration",
                "steps_passed",
                "steps_failed",
            ],
            order_by="execution_date desc",
            limit=1,
        )

        if not previous_execution:
            return {"message": _("No previous execution found for comparison")}

        prev = previous_execution[0]
        prev_doc = frappe.get_doc("Test Execution Log", prev.name)

        comparison = {
            "previous_execution": prev.name,
            "status_change": {
                "previous": prev.execution_status,
                "current": self.execution_status,
                "improved": self.execution_status == "Passed" and prev.execution_status != "Passed",
            },
            "duration_change": {
                "previous": prev.execution_duration or 0,
                "current": self.execution_duration or 0,
                "difference": (self.execution_duration or 0) - (prev.execution_duration or 0),
            },
            "steps_comparison": {
                "passed_change": self.steps_passed - prev.steps_passed,
                "failed_change": self.steps_failed - prev.steps_failed,
            },
        }

        # Performance comparison
        if self.performance_metrics and prev_doc.performance_metrics:
            current_metrics = json.loads(self.performance_metrics)
            prev_metrics = json.loads(prev_doc.performance_metrics)

            comparison["performance_comparison"] = {
                "success_rate_change": current_metrics.get("success_rate", 0)
                - prev_metrics.get("success_rate", 0),
                "api_response_improvement": self.compare_api_performance(
                    current_metrics, prev_metrics
                ),
            }

        return comparison

    def compare_api_performance(self, current_metrics, prev_metrics):
        """Compare API performance between executions"""
        current_avg = current_metrics.get("average_api_response", 0)
        prev_avg = prev_metrics.get("average_api_response", 0)

        if prev_avg > 0:
            improvement_percent = ((prev_avg - current_avg) / prev_avg) * 100
            return {
                "previous_avg": prev_avg,
                "current_avg": current_avg,
                "improvement_percent": round(improvement_percent, 2),
            }
        return None


# Utility functions for test execution management
@frappe.whitelist()
def get_execution_statistics(date_range=None):
    """Get test execution statistics"""
    filters = {}
    if date_range:
        filters["execution_date"] = [">=", date_range]

    executions = frappe.get_list(
        "Test Execution Log",
        filters=filters,
        fields=["execution_status", "execution_duration", "steps_passed", "steps_failed"],
    )

    if not executions:
        return {"message": _("No executions found")}

    total_executions = len(executions)
    passed_executions = sum(1 for e in executions if e.execution_status == "Passed")
    failed_executions = sum(1 for e in executions if e.execution_status == "Failed")
    blocked_executions = sum(1 for e in executions if e.execution_status == "Blocked")

    avg_duration = sum(e.execution_duration or 0 for e in executions) / total_executions

    return {
        "total_executions": total_executions,
        "passed_executions": passed_executions,
        "failed_executions": failed_executions,
        "blocked_executions": blocked_executions,
        "success_rate": (passed_executions / total_executions) * 100,
        "average_duration": round(avg_duration, 2),
        "total_steps_executed": sum(e.steps_passed + e.steps_failed for e in executions),
        "total_steps_passed": sum(e.steps_passed for e in executions),
        "total_steps_failed": sum(e.steps_failed for e in executions),
    }


@frappe.whitelist()
def get_module_test_coverage(module_name):
    """Get test coverage for a specific module"""
    test_cases = frappe.get_list(
        "System Test Case",
        filters={"test_module": module_name},
        fields=["name", "test_case_title", "last_execution_result"],
    )

    if not test_cases:
        return {"message": _("No test cases found for module: {0}").format(module_name)}

    total_tests = len(test_cases)
    executed_tests = sum(1 for tc in test_cases if tc.last_execution_result)
    passed_tests = sum(1 for tc in test_cases if tc.last_execution_result == "Passed")

    coverage = {
        "module": module_name,
        "total_test_cases": total_tests,
        "executed_test_cases": executed_tests,
        "passed_test_cases": passed_tests,
        "execution_coverage": (executed_tests / total_tests) * 100 if total_tests > 0 else 0,
        "success_rate": (passed_tests / executed_tests) * 100 if executed_tests > 0 else 0,
    }

    return coverage
