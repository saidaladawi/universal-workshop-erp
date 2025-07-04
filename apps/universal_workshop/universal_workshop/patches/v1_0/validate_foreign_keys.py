import frappe
from frappe import _


def execute():
    """Validate foreign key relationships and data consistency"""

    frappe.log_error("Starting Foreign Key Validation", "Foreign Key Validation")

    validation_results = {
        "total_checks": 0,
        "passed_checks": 0,
        "failed_checks": 0,
        "errors": [],
        "warnings": [],
    }

    try:
        # Define Link field relationships to validate
        link_validations = [
            # Service Order validations
            {
                "source_doctype": "Service Order",
                "source_field": "customer",
                "target_doctype": "Customer",
                "description": "Service Order -> Customer",
            },
            {
                "source_doctype": "Service Order",
                "source_field": "vehicle",
                "target_doctype": "Vehicle",
                "description": "Service Order -> Vehicle",
            },
            {
                "source_doctype": "Service Order",
                "source_field": "technician_assigned",
                "target_doctype": "Technician",
                "description": "Service Order -> Technician",
            },
            # Vehicle validations
            {
                "source_doctype": "Vehicle",
                "source_field": "customer",
                "target_doctype": "Customer",
                "description": "Vehicle -> Customer",
            },
            # Parts Request validations
            {
                "source_doctype": "Parts Request",
                "source_field": "service_order",
                "target_doctype": "Service Order",
                "description": "Parts Request -> Service Order",
            },
            {
                "source_doctype": "Parts Request",
                "source_field": "requested_by",
                "target_doctype": "Technician",
                "description": "Parts Request -> Technician",
            },
            # Service History validations
            {
                "source_doctype": "Service History",
                "source_field": "service_order",
                "target_doctype": "Service Order",
                "description": "Service History -> Service Order",
            },
            {
                "source_doctype": "Service History",
                "source_field": "vehicle",
                "target_doctype": "Vehicle",
                "description": "Service History -> Vehicle",
            },
            # Customer Communication validations
            {
                "source_doctype": "Customer Communication",
                "source_field": "customer",
                "target_doctype": "Customer",
                "description": "Customer Communication -> Customer",
            },
            # Technician Assignment validations
            {
                "source_doctype": "Technician Assignment",
                "source_field": "technician",
                "target_doctype": "Technician",
                "description": "Technician Assignment -> Technician",
            },
            {
                "source_doctype": "Technician Assignment",
                "source_field": "service_order",
                "target_doctype": "Service Order",
                "description": "Technician Assignment -> Service Order",
            },
        ]

        # Validate each Link field relationship
        for validation in link_validations:
            validation_results["total_checks"] += 1

            try:
                result = validate_link_field(
                    validation["source_doctype"],
                    validation["source_field"],
                    validation["target_doctype"],
                    validation["description"],
                )

                if result["is_valid"]:
                    validation_results["passed_checks"] += 1
                    frappe.log_error(
                        f"✅ {validation['description']}: {result['message']}",
                        "Foreign Key Validation",
                    )
                else:
                    validation_results["failed_checks"] += 1
                    validation_results["errors"].append(
                        {
                            "validation": validation["description"],
                            "error": result["message"],
                            "invalid_records": result.get("invalid_records", []),
                        }
                    )
                    frappe.log_error(
                        f"❌ {validation['description']}: {result['message']}",
                        "Foreign Key Validation",
                    )

            except Exception as e:
                validation_results["failed_checks"] += 1
                error_msg = f"Error validating {validation['description']}: {str(e)}"
                validation_results["errors"].append(
                    {"validation": validation["description"], "error": error_msg}
                )
                frappe.log_error(error_msg, "Foreign Key Validation")

        # Additional data consistency checks
        consistency_checks = [
            check_orphaned_service_orders(),
            check_vehicle_customer_consistency(),
            check_technician_assignment_consistency(),
            check_service_history_consistency(),
        ]

        for check in consistency_checks:
            validation_results["total_checks"] += 1
            if check["is_valid"]:
                validation_results["passed_checks"] += 1
            else:
                validation_results["failed_checks"] += 1
                validation_results["errors"].append(check)

        # Generate validation report
        generate_validation_report(validation_results)

        # Log summary
        summary = f"""
Foreign Key Validation Summary:
- Total Checks: {validation_results['total_checks']}
- Passed: {validation_results['passed_checks']}
- Failed: {validation_results['failed_checks']}
- Success Rate: {(validation_results['passed_checks'] / validation_results['total_checks'] * 100):.1f}%
        """

        frappe.log_error(summary, "Foreign Key Validation Summary")

        if validation_results["failed_checks"] > 0:
            frappe.log_error(
                "⚠️ Foreign Key Validation completed with errors. Check validation report.",
                "Foreign Key Validation",
            )
        else:
            frappe.log_error(
                "✅ All Foreign Key Validations passed successfully!", "Foreign Key Validation"
            )

    except Exception as e:
        frappe.log_error(
            f"Critical error in foreign key validation: {str(e)}", "Foreign Key Validation Error"
        )
        raise


def validate_link_field(source_doctype, source_field, target_doctype, description):
    """Validate a specific Link field relationship"""

    try:
        # Check if source DocType exists
        if not frappe.db.exists("DocType", source_doctype):
            return {
                "is_valid": False,
                "message": f"Source DocType '{source_doctype}' does not exist",
            }

        # Check if target DocType exists
        if not frappe.db.exists("DocType", target_doctype):
            return {
                "is_valid": False,
                "message": f"Target DocType '{target_doctype}' does not exist",
            }

        # Get all records with non-null link field values
        source_records = frappe.db.sql(
            f"""
            SELECT name, `{source_field}`
            FROM `tab{source_doctype}`
            WHERE `{source_field}` IS NOT NULL 
            AND `{source_field}` != ''
        """,
            as_dict=True,
        )

        if not source_records:
            return {
                "is_valid": True,
                "message": f"No records found with {source_field} values to validate",
            }

        invalid_records = []

        # Check each link field value
        for record in source_records:
            link_value = record[source_field]
            if not frappe.db.exists(target_doctype, link_value):
                invalid_records.append(
                    {"source_record": record["name"], "invalid_link": link_value}
                )

        if invalid_records:
            return {
                "is_valid": False,
                "message": f"Found {len(invalid_records)} invalid link references",
                "invalid_records": invalid_records[:10],  # Limit to first 10 for reporting
            }

        return {"is_valid": True, "message": f"All {len(source_records)} link references are valid"}

    except Exception as e:
        return {"is_valid": False, "message": f"Error during validation: {str(e)}"}


def check_orphaned_service_orders():
    """Check for service orders without valid customers or vehicles"""

    try:
        orphaned_orders = frappe.db.sql(
            """
            SELECT so.name, so.customer, so.vehicle
            FROM `tabService Order` so
            LEFT JOIN `tabCustomer` c ON so.customer = c.name
            LEFT JOIN `tabVehicle` v ON so.vehicle = v.name
            WHERE (so.customer IS NOT NULL AND c.name IS NULL)
            OR (so.vehicle IS NOT NULL AND v.name IS NULL)
        """,
            as_dict=True,
        )

        if orphaned_orders:
            return {
                "is_valid": False,
                "validation": "Orphaned Service Orders",
                "error": f"Found {len(orphaned_orders)} orphaned service orders",
                "invalid_records": orphaned_orders[:10],
            }

        return {
            "is_valid": True,
            "validation": "Orphaned Service Orders",
            "message": "No orphaned service orders found",
        }

    except Exception as e:
        return {
            "is_valid": False,
            "validation": "Orphaned Service Orders",
            "error": f"Error checking orphaned service orders: {str(e)}",
        }


def check_vehicle_customer_consistency():
    """Check vehicle-customer relationship consistency"""

    try:
        inconsistent_vehicles = frappe.db.sql(
            """
            SELECT v.name as vehicle_name, v.customer as vehicle_customer,
                   so.customer as service_customer
            FROM `tabVehicle` v
            JOIN `tabService Order` so ON v.name = so.vehicle
            WHERE v.customer != so.customer
        """,
            as_dict=True,
        )

        if inconsistent_vehicles:
            return {
                "is_valid": False,
                "validation": "Vehicle-Customer Consistency",
                "error": f"Found {len(inconsistent_vehicles)} vehicles with inconsistent customer relationships",
                "invalid_records": inconsistent_vehicles[:10],
            }

        return {
            "is_valid": True,
            "validation": "Vehicle-Customer Consistency",
            "message": "All vehicle-customer relationships are consistent",
        }

    except Exception as e:
        return {
            "is_valid": False,
            "validation": "Vehicle-Customer Consistency",
            "error": f"Error checking vehicle-customer consistency: {str(e)}",
        }


def check_technician_assignment_consistency():
    """Check technician assignment consistency"""

    try:
        invalid_assignments = frappe.db.sql(
            """
            SELECT so.name as service_order, so.technician_assigned
            FROM `tabService Order` so
            LEFT JOIN `tabTechnician` t ON so.technician_assigned = t.name
            WHERE so.technician_assigned IS NOT NULL 
            AND so.technician_assigned != ''
            AND t.name IS NULL
        """,
            as_dict=True,
        )

        if invalid_assignments:
            return {
                "is_valid": False,
                "validation": "Technician Assignment Consistency",
                "error": f"Found {len(invalid_assignments)} service orders with invalid technician assignments",
                "invalid_records": invalid_assignments[:10],
            }

        return {
            "is_valid": True,
            "validation": "Technician Assignment Consistency",
            "message": "All technician assignments are valid",
        }

    except Exception as e:
        return {
            "is_valid": False,
            "validation": "Technician Assignment Consistency",
            "error": f"Error checking technician assignments: {str(e)}",
        }


def check_service_history_consistency():
    """Check service history consistency"""

    try:
        invalid_history = frappe.db.sql(
            """
            SELECT sh.name, sh.service_order, sh.vehicle
            FROM `tabService History` sh
            LEFT JOIN `tabService Order` so ON sh.service_order = so.name
            LEFT JOIN `tabVehicle` v ON sh.vehicle = v.name
            WHERE (sh.service_order IS NOT NULL AND so.name IS NULL)
            OR (sh.vehicle IS NOT NULL AND v.name IS NULL)
        """,
            as_dict=True,
        )

        if invalid_history:
            return {
                "is_valid": False,
                "validation": "Service History Consistency",
                "error": f"Found {len(invalid_history)} service history records with invalid references",
                "invalid_records": invalid_history[:10],
            }

        return {
            "is_valid": True,
            "validation": "Service History Consistency",
            "message": "All service history records are consistent",
        }

    except Exception as e:
        return {
            "is_valid": False,
            "validation": "Service History Consistency",
            "error": f"Error checking service history: {str(e)}",
        }


def generate_validation_report(results):
    """Generate a detailed validation report"""

    try:
        report_content = f"""
# Foreign Key Validation Report
Generated: {frappe.utils.now()}

## Summary
- **Total Checks**: {results['total_checks']}
- **Passed**: {results['passed_checks']}
- **Failed**: {results['failed_checks']}
- **Success Rate**: {(results['passed_checks'] / results['total_checks'] * 100):.1f}%

## Failed Validations
"""

        if results["errors"]:
            for error in results["errors"]:
                report_content += f"""
### {error['validation']}
**Error**: {error['error']}
"""
                if "invalid_records" in error and error["invalid_records"]:
                    report_content += "**Invalid Records**:\n"
                    for record in error["invalid_records"]:
                        report_content += f"- {record}\n"
        else:
            report_content += "No failed validations - all checks passed! ✅\n"

        # Save report to file
        import os

        report_dir = frappe.get_site_path("private", "files", "validation_reports")
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)

        report_file = os.path.join(
            report_dir,
            f'foreign_key_validation_{frappe.utils.now_datetime().strftime("%Y%m%d_%H%M%S")}.md',
        )

        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report_content)

        frappe.log_error(f"Validation report saved to: {report_file}", "Foreign Key Validation")

    except Exception as e:
        frappe.log_error(f"Error generating validation report: {str(e)}", "Foreign Key Validation")
