#!/usr/bin/env python3

import frappe


def test_install_doctypes():
    """Test and install new DocTypes"""
    frappe.init(site="universal.local")
    frappe.connect()

    try:
        # Test if DocTypes can be loaded
        print("Testing DocType imports...")

        # Install DocTypes in correct order (child tables first)
        doctypes = [
            ("purchasing_management", "doctype", "supplier_comparison_item"),
            ("purchasing_management", "doctype", "supplier_comparison_quotation"),
            ("purchasing_management", "doctype", "supplier_comparison"),
        ]

        for module, folder, doctype in doctypes:
            try:
                frappe.reload_doc(module, folder, doctype)
                print(f"✅ Successfully installed {doctype}")
            except Exception as e:
                print(f"❌ Failed to install {doctype}: {e}")

        # Test if DocTypes are accessible
        print("\nTesting DocType accessibility...")
        try:
            sc = frappe.new_doc("Supplier Comparison")
            print("✅ Supplier Comparison DocType is accessible")
        except Exception as e:
            print(f"❌ Supplier Comparison not accessible: {e}")

        # Commit changes
        frappe.db.commit()
        print("✅ All changes committed")

    except Exception as e:
        print(f"❌ Overall error: {e}")
    finally:
        frappe.destroy()


if __name__ == "__main__":
    test_install_doctypes()
