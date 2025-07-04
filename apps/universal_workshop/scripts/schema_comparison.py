#!/usr/bin/env python3
"""
Schema Comparison Script for Universal Workshop ERP
Compares DocType definitions with actual database schema
"""

import os
import json
import frappe
from pathlib import Path


def compare_doctype_with_database(doctype_name):
    """Compare DocType definition with actual database table"""
    try:
        # Get DocType definition
        doctype_meta = frappe.get_meta(doctype_name)

        # Get database table structure
        table_name = f"tab{doctype_name}"
        db_columns = frappe.db.sql(f"DESCRIBE `{table_name}`", as_dict=True)

        # Create comparison report
        report = {
            "doctype": doctype_name,
            "table_name": table_name,
            "doctype_fields": len(doctype_meta.fields),
            "database_columns": len(db_columns),
            "missing_in_db": [],
            "missing_in_doctype": [],
            "type_mismatches": [],
            "index_status": [],
        }

        # Get field names from DocType
        doctype_fieldnames = set()
        for field in doctype_meta.fields:
            if field.fieldtype not in ["Section Break", "Column Break", "HTML", "Heading"]:
                doctype_fieldnames.add(field.fieldname)

        # Get column names from database
        db_fieldnames = {col["Field"] for col in db_columns}

        # Find missing fields
        report["missing_in_db"] = list(doctype_fieldnames - db_fieldnames)
        report["missing_in_doctype"] = list(db_fieldnames - doctype_fieldnames)

        # Check for type mismatches (simplified)
        for field in doctype_meta.fields:
            if field.fieldname in db_fieldnames:
                db_col = next((col for col in db_columns if col["Field"] == field.fieldname), None)
                if db_col:
                    # Simple type checking
                    if field.fieldtype == "Data" and "varchar" not in db_col["Type"].lower():
                        report["type_mismatches"].append(
                            {
                                "field": field.fieldname,
                                "doctype_type": field.fieldtype,
                                "db_type": db_col["Type"],
                            }
                        )

        return report

    except Exception as e:
        return {"doctype": doctype_name, "error": str(e)}


def get_universal_workshop_doctypes():
    """Get all Universal Workshop DocTypes"""
    doctypes = []

    # Search for all DocType JSON files
    universal_workshop_path = Path("apps/universal_workshop")

    for json_file in universal_workshop_path.rglob("**/doctype/**/*.json"):
        if json_file.name.startswith("test_") or "test" in json_file.parent.name:
            continue

        try:
            with open(json_file, "r", encoding="utf-8") as f:
                doctype_data = json.load(f)
                if doctype_data.get("doctype") == "DocType":
                    doctypes.append(doctype_data.get("name"))
        except Exception as e:
            print(f"Error reading {json_file}: {e}")

    return sorted(set(doctypes))


def check_database_integrity():
    """Check overall database integrity"""
    print("🔍 Checking Database Integrity...")

    integrity_checks = [
        {
            "name": "Orphaned DocTypes",
            "query": """
                SELECT name FROM tabDocType 
                WHERE app_name = 'universal_workshop' 
                AND name NOT IN (
                    SELECT DISTINCT doctype FROM tabCustom Field 
                    WHERE dt IS NOT NULL
                )
            """,
        },
        {
            "name": "Missing Tables",
            "query": """
                SELECT CONCAT('tab', name) as expected_table
                FROM tabDocType 
                WHERE app_name = 'universal_workshop'
                AND CONCAT('tab', name) NOT IN (
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = DATABASE()
                )
            """,
        },
    ]

    for check in integrity_checks:
        try:
            result = frappe.db.sql(check["query"], as_dict=True)
            print(f"  {check['name']}: {len(result)} issues found")
            if result:
                for item in result[:5]:  # Show first 5
                    print(f"    - {list(item.values())[0]}")
                if len(result) > 5:
                    print(f"    ... and {len(result) - 5} more")
        except Exception as e:
            print(f"  {check['name']}: Error - {e}")


def main():
    """Main function to run schema comparison"""
    print("🚀 Universal Workshop ERP - Schema Comparison")
    print("=" * 50)

    # Initialize Frappe
    frappe.init(site="universal.local")
    frappe.connect()

    # Check database integrity first
    check_database_integrity()
    print()

    # Get all Universal Workshop DocTypes
    print("📋 Getting Universal Workshop DocTypes...")
    doctypes = get_universal_workshop_doctypes()
    print(f"Found {len(doctypes)} DocTypes")
    print()

    # Compare each DocType
    print("🔍 Comparing DocTypes with Database Schema...")

    total_issues = 0
    for doctype in doctypes:
        print(f"  Checking {doctype}...")
        report = compare_doctype_with_database(doctype)

        if "error" in report:
            print(f"    ❌ Error: {report['error']}")
            total_issues += 1
            continue

        issues = (
            len(report["missing_in_db"])
            + len(report["missing_in_doctype"])
            + len(report["type_mismatches"])
        )

        if issues == 0:
            print(f"    ✅ Schema matches ({report['doctype_fields']} fields)")
        else:
            print(f"    ⚠️  {issues} issues found:")
            total_issues += issues

            if report["missing_in_db"]:
                print(
                    f"      - Missing in DB: {', '.join(report['missing_in_db'][:3])}{'...' if len(report['missing_in_db']) > 3 else ''}"
                )

            if report["missing_in_doctype"]:
                print(
                    f"      - Extra in DB: {', '.join(report['missing_in_doctype'][:3])}{'...' if len(report['missing_in_doctype']) > 3 else ''}"
                )

            if report["type_mismatches"]:
                print(f"      - Type mismatches: {len(report['type_mismatches'])}")

    print()
    print(f"📊 Summary: {total_issues} total schema issues found across {len(doctypes)} DocTypes")

    if total_issues == 0:
        print("✅ All schemas are consistent!")
    else:
        print("⚠️  Schema inconsistencies detected - consider running migrations")

    frappe.destroy()


if __name__ == "__main__":
    # Change to bench directory
    os.chdir("/home/said/frappe-dev/frappe-bench")
    main()
