#!/usr/bin/env python3

import sys
import os

sys.path.append("/home/said/frappe-dev/frappe-bench")
sys.path.append("/home/said/frappe-dev/frappe-bench/apps/frappe")


def analyze_errors():
    """Analyze error patterns from the Error Log"""
    try:
        import frappe
        from datetime import datetime, timedelta

        # Initialize Frappe
        frappe.init(site="universal.local")
        frappe.connect()

        print("🔍 Universal Workshop ERP - Error Analysis Report")
        print("=" * 60)

        # Get total error count
        total_errors = frappe.db.count("Error Log")
        print(f"\n📊 Total errors in system: {total_errors}")

        # Get recent errors (last 7 days)
        seven_days_ago = datetime.now() - timedelta(days=7)
        recent_errors = frappe.db.count("Error Log", {"creation": [">=", seven_days_ago]})
        print(f"📊 Errors in last 7 days: {recent_errors}")

        # Get error breakdown by method
        print(f"\n🔝 Top Error Methods (Last 7 Days):")
        print("-" * 50)

        error_methods = frappe.db.sql(
            """
            SELECT method, COUNT(*) as count 
            FROM `tabError Log` 
            WHERE creation >= %s 
            GROUP BY method 
            ORDER BY count DESC 
            LIMIT 10
        """,
            (seven_days_ago,),
            as_dict=True,
        )

        for i, error in enumerate(error_methods, 1):
            method = error.method if error.method else "Unknown Method"
            print(f"{i:2d}. {error.count:3d} errors - {method[:70]}")

        # Get error distribution by date
        print(f"\n📅 Error Distribution by Date:")
        print("-" * 40)

        date_distribution = frappe.db.sql(
            """
            SELECT DATE(creation) as error_date, COUNT(*) as daily_errors
            FROM `tabError Log`
            WHERE creation >= %s
            GROUP BY DATE(creation)
            ORDER BY error_date DESC
        """,
            (seven_days_ago,),
            as_dict=True,
        )

        for date_error in date_distribution:
            print(f"  {date_error.error_date}: {date_error.daily_errors} errors")

        # Get latest 5 errors with details
        print(f"\n🆕 Latest 5 Errors:")
        print("-" * 30)

        latest_errors = frappe.db.sql(
            """
            SELECT creation, method, LEFT(error, 150) as error_preview
            FROM `tabError Log`
            ORDER BY creation DESC
            LIMIT 5
        """,
            as_dict=True,
        )

        for i, error in enumerate(latest_errors, 1):
            method = error.method if error.method else "Unknown Method"
            error_preview = error.error_preview if error.error_preview else "No error details"
            print(f"\n{i}. {error.creation}")
            print(f"   Method: {method}")
            print(f"   Error: {error_preview}...")

        # Calculate error rate
        if recent_errors > 0:
            error_rate = recent_errors / 7  # errors per day
            print(f"\n⚡ Current Error Rate: {error_rate:.1f} errors/day")

            if error_rate > 10:
                status = "🔴 CRITICAL"
            elif error_rate > 5:
                status = "🟡 WARNING"
            else:
                status = "🟢 NORMAL"

            print(f"📊 System Status: {status}")

        print(f"\n✅ Error analysis completed successfully!")

    except Exception as e:
        print(f"❌ Error analysis failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    analyze_errors()
