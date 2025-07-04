# Copyright (c) 2025, Universal Workshop ERP
# For license information, see license.txt

import frappe
from frappe import _


def setup_database_indexes():
    """Setup optimized database indexes for Universal Workshop ERP"""

    try:
        # Workshop Profile indexes
        frappe.db.sql(
            """
            ALTER TABLE `tabWorkshop Profile` 
            ADD INDEX idx_workshop_name_ar (workshop_name_ar),
            ADD INDEX idx_business_license (business_license),
            ADD INDEX idx_vat_number (vat_number)
        """
        )

        # Customer indexes for Arabic search
        frappe.db.sql(
            """
            ALTER TABLE `tabCustomer`
            ADD INDEX idx_customer_name_ar (customer_name_ar),
            ADD INDEX idx_phone_oman (phone),
            ADD FULLTEXT INDEX ft_customer_search (customer_name, customer_name_ar, phone)
        """
        )

        # Customer Vehicle indexes
        frappe.db.sql(
            """
            ALTER TABLE `tabCustomer Vehicle`
            ADD INDEX idx_vehicle_id (vehicle_id),
            ADD INDEX idx_vin_number (vin_number),
            ADD INDEX idx_customer_vehicle (customer, vehicle_id)
        """
        )

        # Parts Inventory indexes
        frappe.db.sql(
            """
            ALTER TABLE `tabItem`
            ADD INDEX idx_item_name_ar (item_name_ar),
            ADD INDEX idx_part_number (part_number),
            ADD FULLTEXT INDEX ft_item_search (item_name, item_name_ar, description)
        """
        )

        # Service Order indexes
        frappe.db.sql(
            """
            ALTER TABLE `tabService Order`
            ADD INDEX idx_service_date (service_date),
            ADD INDEX idx_customer_service (customer, service_date),
            ADD INDEX idx_status_date (status, service_date)
        """
        )

        # Barcode Scanner indexes
        frappe.db.sql(
            """
            ALTER TABLE `tabBarcode Scanner`
            ADD INDEX idx_scan_date (scan_date),
            ADD INDEX idx_barcode_type (barcode_type),
            ADD INDEX idx_warehouse_scan (warehouse, scan_date)
        """
        )

        # ABC Analysis indexes
        frappe.db.sql(
            """
            ALTER TABLE `tabABC Analysis`
            ADD INDEX idx_analysis_date (analysis_date),
            ADD INDEX idx_category (category),
            ADD INDEX idx_item_analysis (item_code, analysis_date)
        """
        )

        # Customer Feedback indexes
        frappe.db.sql(
            """
            ALTER TABLE `tabCustomer Feedback`
            ADD INDEX idx_feedback_date (feedback_date),
            ADD INDEX idx_customer_feedback (customer, feedback_date),
            ADD INDEX idx_rating (rating),
            ADD INDEX idx_status (status)
        """
        )

        frappe.db.commit()
        frappe.msgprint(_("Database indexes created successfully"))

    except Exception as e:
        frappe.logger().error(f"Error creating database indexes: {str(e)}")
        frappe.throw(_("Failed to create database indexes: {0}").format(str(e)))


def optimize_arabic_search():
    """Optimize Arabic text search performance"""

    try:
        # Create Arabic-specific indexes
        frappe.db.sql(
            """
            ALTER TABLE `tabCustomer`
            ADD FULLTEXT INDEX ft_arabic_search (customer_name_ar)
        """
        )

        frappe.db.sql(
            """
            ALTER TABLE `tabWorkshop Profile`
            ADD FULLTEXT INDEX ft_arabic_search (workshop_name_ar)
        """
        )

        frappe.db.sql(
            """
            ALTER TABLE `tabItem`
            ADD FULLTEXT INDEX ft_arabic_search (item_name_ar, description_ar)
        """
        )

        frappe.db.commit()
        frappe.msgprint(_("Arabic search optimization completed"))

    except Exception as e:
        frappe.logger().error(f"Error optimizing Arabic search: {str(e)}")
        frappe.throw(_("Failed to optimize Arabic search: {0}").format(str(e)))


def cleanup_old_data():
    """Clean up old data to maintain performance"""

    try:
        # Clean up old performance logs (older than 90 days)
        frappe.db.sql(
            """
            DELETE FROM `tabPerformance Log`
            WHERE creation < DATE_SUB(NOW(), INTERVAL 90 DAY)
        """
        )

        # Clean up old ML model usage logs (older than 90 days)
        frappe.db.sql(
            """
            DELETE FROM `tabML Model Usage Log`
            WHERE creation < DATE_SUB(NOW(), INTERVAL 90 DAY)
        """
        )

        # Clean up old barcode scan logs (older than 180 days)
        frappe.db.sql(
            """
            DELETE FROM `tabBarcode Scanner`
            WHERE scan_date < DATE_SUB(NOW(), INTERVAL 180 DAY)
        """
        )

        frappe.db.commit()
        frappe.msgprint(_("Old data cleanup completed"))

    except Exception as e:
        frappe.logger().error(f"Error cleaning up old data: {str(e)}")
        frappe.throw(_("Failed to cleanup old data: {0}").format(str(e)))


if __name__ == "__main__":
    setup_database_indexes()
    optimize_arabic_search()
    cleanup_old_data()
