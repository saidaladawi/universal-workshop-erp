#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Universal Workshop ERP - User Training System
Comprehensive bilingual training system for billing operations
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, getdate, add_days
import json
import os
from datetime import datetime, timedelta


class UniversalWorkshopTrainingManager(Document):
    """Main training manager for Universal Workshop billing system"""

    def __init__(self):
        self.training_modules = self.get_training_modules()
        self.user_roles = self.get_user_roles()

    def get_training_modules(self):
        """Define comprehensive training modules for billing system"""
        return {
            "basic_billing": {
                "title": _("Basic Billing Operations"),
                "title_ar": "العمليات الأساسية للفوترة",
                "description": _("Introduction to invoice creation and basic billing workflows"),
                "description_ar": "مقدمة لإنشاء الفواتير وسير العمل الأساسي للفوترة",
                "duration_hours": 2,
                "difficulty": "beginner",
                "required_for": ["workshop_staff", "billing_clerk"],
                "modules": [
                    "invoice_creation_basics",
                    "customer_billing_info",
                    "arabic_invoice_handling",
                    "basic_vat_application",
                ],
            },
            "advanced_vat_compliance": {
                "title": _("Oman VAT Compliance"),
                "title_ar": "الامتثال لضريبة القيمة المضافة العمانية",
                "description": _(
                    "Complete training on Oman VAT requirements and e-invoice compliance"
                ),
                "description_ar": "التدريب الشامل على متطلبات ضريبة القيمة المضافة العمانية والامتثال للفاتورة الإلكترونية",
                "duration_hours": 4,
                "difficulty": "advanced",
                "required_for": ["billing_manager", "accountant"],
                "modules": [
                    "oman_vat_regulations",
                    "e_invoice_compliance",
                    "qr_code_generation",
                    "ota_reporting_requirements",
                ],
            },
            "multi_currency_payments": {
                "title": _("Multi-Currency and Payment Processing"),
                "title_ar": "العملات المتعددة ومعالجة المدفوعات",
                "description": _(
                    "Training on multi-currency operations and payment gateway integration"
                ),
                "description_ar": "التدريب على عمليات العملات المتعددة وتكامل بوابة الدفع",
                "duration_hours": 3,
                "difficulty": "intermediate",
                "required_for": ["billing_manager", "cashier"],
                "modules": [
                    "currency_conversion",
                    "payment_gateway_operations",
                    "baisa_precision_handling",
                    "payment_reconciliation",
                ],
            },
            "receivables_management": {
                "title": _("Receivables and Financial Reporting"),
                "title_ar": "إدارة المستحقات والتقارير المالية",
                "description": _(
                    "Comprehensive training on receivables management and financial reporting"
                ),
                "description_ar": "التدريب الشامل على إدارة المستحقات والتقارير المالية",
                "duration_hours": 3,
                "difficulty": "intermediate",
                "required_for": ["billing_manager", "accountant"],
                "modules": [
                    "aging_analysis",
                    "dunning_processes",
                    "financial_reporting",
                    "compliance_reporting",
                ],
            },
            "system_administration": {
                "title": _("Billing System Administration"),
                "title_ar": "إدارة نظام الفوترة",
                "description": _("Advanced system configuration and troubleshooting"),
                "description_ar": "التكوين المتقدم للنظام واستكشاف الأخطاء وإصلاحها",
                "duration_hours": 4,
                "difficulty": "expert",
                "required_for": ["system_admin", "workshop_manager"],
                "modules": [
                    "system_configuration",
                    "user_permissions",
                    "troubleshooting",
                    "backup_recovery",
                ],
            },
        }

    def get_user_roles(self):
        """Define user roles and their training requirements"""
        return {
            "workshop_staff": {
                "title": _("Workshop Staff"),
                "title_ar": "موظفو الورشة",
                "required_modules": ["basic_billing"],
                "optional_modules": ["multi_currency_payments"],
                "competency_level": "basic",
            },
            "billing_clerk": {
                "title": _("Billing Clerk"),
                "title_ar": "موظف الفوترة",
                "required_modules": ["basic_billing", "multi_currency_payments"],
                "optional_modules": ["advanced_vat_compliance"],
                "competency_level": "intermediate",
            },
            "billing_manager": {
                "title": _("Billing Manager"),
                "title_ar": "مدير الفوترة",
                "required_modules": [
                    "advanced_vat_compliance",
                    "multi_currency_payments",
                    "receivables_management",
                ],
                "optional_modules": ["system_administration"],
                "competency_level": "advanced",
            },
            "accountant": {
                "title": _("Accountant"),
                "title_ar": "المحاسب",
                "required_modules": ["advanced_vat_compliance", "receivables_management"],
                "optional_modules": ["multi_currency_payments"],
                "competency_level": "advanced",
            },
            "cashier": {
                "title": _("Cashier"),
                "title_ar": "أمين الصندوق",
                "required_modules": ["basic_billing", "multi_currency_payments"],
                "optional_modules": [],
                "competency_level": "intermediate",
            },
            "workshop_manager": {
                "title": _("Workshop Manager"),
                "title_ar": "مدير الورشة",
                "required_modules": [
                    "basic_billing",
                    "receivables_management",
                    "system_administration",
                ],
                "optional_modules": ["advanced_vat_compliance", "multi_currency_payments"],
                "competency_level": "expert",
            },
            "system_admin": {
                "title": _("System Administrator"),
                "title_ar": "مدير النظام",
                "required_modules": ["system_administration", "advanced_vat_compliance"],
                "optional_modules": [],
                "competency_level": "expert",
            },
        }

    @frappe.whitelist()
    def create_training_program(self, user_role, language="en"):
        """Create a comprehensive training program for a specific role"""

        if user_role not in self.user_roles:
            frappe.throw(_("Invalid user role: {0}").format(user_role))

        role_config = self.user_roles[user_role]
        training_plan = {
            "role": user_role,
            "role_title": role_config["title_ar"] if language == "ar" else role_config["title"],
            "competency_level": role_config["competency_level"],
            "required_modules": [],
            "optional_modules": [],
            "total_duration_hours": 0,
            "estimated_completion_days": 0,
        }

        # Add required modules
        for module_id in role_config["required_modules"]:
            if module_id in self.training_modules:
                module = self.training_modules[module_id]
                training_plan["required_modules"].append(
                    {
                        "id": module_id,
                        "title": module["title_ar"] if language == "ar" else module["title"],
                        "description": (
                            module["description_ar"] if language == "ar" else module["description"]
                        ),
                        "duration_hours": module["duration_hours"],
                        "difficulty": module["difficulty"],
                        "modules": module["modules"],
                    }
                )
                training_plan["total_duration_hours"] += module["duration_hours"]

        # Add optional modules
        for module_id in role_config["optional_modules"]:
            if module_id in self.training_modules:
                module = self.training_modules[module_id]
                training_plan["optional_modules"].append(
                    {
                        "id": module_id,
                        "title": module["title_ar"] if language == "ar" else module["title"],
                        "description": (
                            module["description_ar"] if language == "ar" else module["description"]
                        ),
                        "duration_hours": module["duration_hours"],
                        "difficulty": module["difficulty"],
                        "modules": module["modules"],
                    }
                )

        # Calculate completion timeline
        training_plan["estimated_completion_days"] = max(
            7, training_plan["total_duration_hours"] * 2
        )

        return training_plan

    @frappe.whitelist()
    def enroll_user_in_training(self, user_id, training_program_id, language="en"):
        """Enroll a user in a specific training program"""

        # Create Training Record
        training_record = frappe.new_doc("Training Record")
        training_record.employee = user_id
        training_record.training_program = training_program_id
        training_record.status = "Enrolled"
        training_record.enrollment_date = now_datetime()
        training_record.language_preference = language

        # Set expected completion date
        training_program = self.create_training_program(training_program_id, language)
        training_record.expected_completion_date = add_days(
            getdate(), training_program["estimated_completion_days"]
        )

        training_record.insert()
        frappe.db.commit()

        return {
            "training_record_id": training_record.name,
            "message": _("User successfully enrolled in training program"),
            "expected_completion": training_record.expected_completion_date,
        }

    @frappe.whitelist()
    def track_training_progress(self, training_record_id, module_id, completion_status, score=0):
        """Track user progress through training modules"""

        training_record = frappe.get_doc("Training Record", training_record_id)

        # Update module completion
        progress_data = json.loads(training_record.progress_data or "{}")
        progress_data[module_id] = {
            "completion_status": completion_status,
            "score": score,
            "completion_date": now_datetime().isoformat(),
            "attempts": progress_data.get(module_id, {}).get("attempts", 0) + 1,
        }

        training_record.progress_data = json.dumps(progress_data)

        # Calculate overall completion percentage
        completed_modules = sum(
            1 for module in progress_data.values() if module["completion_status"] == "completed"
        )
        total_modules = len(
            self.training_modules.get(training_record.training_program, {}).get("modules", [])
        )

        if total_modules > 0:
            training_record.completion_percentage = (completed_modules / total_modules) * 100

            # Update status based on completion
            if training_record.completion_percentage == 100:
                training_record.status = "Completed"
                training_record.completion_date = now_datetime()

                # Issue certificate if passed
                if self.calculate_overall_score(progress_data) >= 80:
                    self.issue_training_certificate(training_record_id)

        training_record.save()
        frappe.db.commit()

        return {
            "completion_percentage": training_record.completion_percentage,
            "status": training_record.status,
            "overall_score": self.calculate_overall_score(progress_data),
        }

    def calculate_overall_score(self, progress_data):
        """Calculate overall training score"""
        if not progress_data:
            return 0

        total_score = sum(module.get("score", 0) for module in progress_data.values())
        total_modules = len(progress_data)

        return total_score / total_modules if total_modules > 0 else 0

    @frappe.whitelist()
    def issue_training_certificate(self, training_record_id):
        """Issue digital training certificate"""

        training_record = frappe.get_doc("Training Record", training_record_id)

        certificate_data = {
            "certificate_id": f"UW-CERT-{training_record.name}",
            "employee_id": training_record.employee,
            "training_program": training_record.training_program,
            "completion_date": training_record.completion_date,
            "overall_score": self.calculate_overall_score(
                json.loads(training_record.progress_data or "{}")
            ),
            "language": training_record.language_preference,
            "issued_by": frappe.session.user,
            "issue_date": now_datetime(),
        }

        # Save certificate data
        training_record.certificate_data = json.dumps(certificate_data)
        training_record.certificate_issued = 1
        training_record.save()

        return certificate_data

    @frappe.whitelist()
    def get_training_analytics(self, date_from=None, date_to=None):
        """Get comprehensive training analytics"""

        conditions = ""
        if date_from:
            conditions += f" AND enrollment_date >= '{date_from}'"
        if date_to:
            conditions += f" AND enrollment_date <= '{date_to}'"

        # Get training statistics
        training_stats = frappe.db.sql(
            f"""
            SELECT 
                training_program,
                status,
                language_preference,
                COUNT(*) as count,
                AVG(completion_percentage) as avg_completion,
                COUNT(CASE WHEN certificate_issued = 1 THEN 1 END) as certificates_issued
            FROM `tabTraining Record`
            WHERE 1=1 {conditions}
            GROUP BY training_program, status, language_preference
        """,
            as_dict=True,
        )

        # Calculate overall metrics
        total_enrollments = sum(stat["count"] for stat in training_stats)
        completed_trainings = sum(
            stat["count"] for stat in training_stats if stat["status"] == "Completed"
        )
        completion_rate = (
            (completed_trainings / total_enrollments * 100) if total_enrollments > 0 else 0
        )

        return {
            "total_enrollments": total_enrollments,
            "completed_trainings": completed_trainings,
            "completion_rate": round(completion_rate, 2),
            "certificates_issued": sum(stat["certificates_issued"] for stat in training_stats),
            "detailed_stats": training_stats,
            "language_breakdown": self.get_language_breakdown(training_stats),
            "role_performance": self.get_role_performance(training_stats),
        }

    def get_language_breakdown(self, training_stats):
        """Get training statistics by language"""
        arabic_stats = [stat for stat in training_stats if stat["language_preference"] == "ar"]
        english_stats = [stat for stat in training_stats if stat["language_preference"] == "en"]

        return {
            "arabic": {
                "total": sum(stat["count"] for stat in arabic_stats),
                "completed": sum(
                    stat["count"] for stat in arabic_stats if stat["status"] == "Completed"
                ),
            },
            "english": {
                "total": sum(stat["count"] for stat in english_stats),
                "completed": sum(
                    stat["count"] for stat in english_stats if stat["status"] == "Completed"
                ),
            },
        }

    def get_role_performance(self, training_stats):
        """Get performance statistics by role"""
        role_performance = {}

        for role_id, role_config in self.user_roles.items():
            role_stats = [stat for stat in training_stats if stat["training_program"] == role_id]
            total = sum(stat["count"] for stat in role_stats)
            completed = sum(stat["count"] for stat in role_stats if stat["status"] == "Completed")

            role_performance[role_id] = {
                "role_title": role_config["title"],
                "total_enrollments": total,
                "completed": completed,
                "completion_rate": (completed / total * 100) if total > 0 else 0,
                "avg_completion_percentage": (
                    sum(stat["avg_completion"] * stat["count"] for stat in role_stats) / total
                    if total > 0
                    else 0
                ),
            }

        return role_performance

    @frappe.whitelist()
    def generate_training_report(
        self, report_type="summary", language="en", date_from=None, date_to=None
    ):
        """Generate comprehensive training reports"""

        analytics = self.get_training_analytics(date_from, date_to)

        if report_type == "summary":
            return self.generate_summary_report(analytics, language)
        elif report_type == "detailed":
            return self.generate_detailed_report(analytics, language)
        elif report_type == "compliance":
            return self.generate_compliance_report(analytics, language)
        else:
            frappe.throw(_("Invalid report type: {0}").format(report_type))

    def generate_summary_report(self, analytics, language):
        """Generate summary training report"""

        title = "تقرير ملخص التدريب" if language == "ar" else "Training Summary Report"

        report = {
            "title": title,
            "generated_date": now_datetime().isoformat(),
            "language": language,
            "summary": {
                "total_enrollments": analytics["total_enrollments"],
                "completed_trainings": analytics["completed_trainings"],
                "completion_rate": f"{analytics['completion_rate']}%",
                "certificates_issued": analytics["certificates_issued"],
            },
            "language_breakdown": analytics["language_breakdown"],
            "top_performing_roles": sorted(
                analytics["role_performance"].items(),
                key=lambda x: x[1]["completion_rate"],
                reverse=True,
            )[:5],
        }

        return report

    def generate_detailed_report(self, analytics, language):
        """Generate detailed training report"""

        title = "التقرير التفصيلي للتدريب" if language == "ar" else "Detailed Training Report"

        return {
            "title": title,
            "generated_date": now_datetime().isoformat(),
            "language": language,
            "summary": analytics,
            "role_performance": analytics["role_performance"],
            "recommendations": self.generate_training_recommendations(analytics, language),
        }

    def generate_compliance_report(self, analytics, language):
        """Generate compliance training report"""

        title = "تقرير التدريب على الامتثال" if language == "ar" else "Compliance Training Report"

        # Focus on VAT compliance training
        vat_compliance_stats = analytics["role_performance"].get("advanced_vat_compliance", {})

        return {
            "title": title,
            "generated_date": now_datetime().isoformat(),
            "language": language,
            "vat_compliance": vat_compliance_stats,
            "compliance_rate": vat_compliance_stats.get("completion_rate", 0),
            "certified_users": analytics["certificates_issued"],
            "compliance_status": (
                "Compliant"
                if vat_compliance_stats.get("completion_rate", 0) >= 90
                else "Needs Improvement"
            ),
        }

    def generate_training_recommendations(self, analytics, language):
        """Generate training improvement recommendations"""

        recommendations = []

        # Check completion rates
        if analytics["completion_rate"] < 80:
            recommendations.append(
                {
                    "priority": "high",
                    "recommendation": (
                        "زيادة معدل إتمام التدريب"
                        if language == "ar"
                        else "Improve training completion rate"
                    ),
                    "details": (
                        "معدل الإتمام الحالي أقل من 80%"
                        if language == "ar"
                        else "Current completion rate is below 80%"
                    ),
                }
            )

        # Check language preference balance
        lang_breakdown = analytics["language_breakdown"]
        if lang_breakdown["arabic"]["total"] < lang_breakdown["english"]["total"] * 0.3:
            recommendations.append(
                {
                    "priority": "medium",
                    "recommendation": (
                        "تحسين التدريب باللغة العربية"
                        if language == "ar"
                        else "Improve Arabic language training adoption"
                    ),
                    "details": (
                        "انخفاض في التسجيل للتدريب باللغة العربية"
                        if language == "ar"
                        else "Low Arabic language training enrollment"
                    ),
                }
            )

        return recommendations
