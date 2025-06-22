#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import frappe


def setup_default_company():
    """إعداد شركة افتراضية لحل مشكلة Company is mandatory"""

    # التحقق من وجود شركة
    companies = frappe.get_list("Company")

    if not companies:
        print("إنشاء شركة افتراضية...")

        # إنشاء شركة جديدة
        company = frappe.new_doc("Company")
        company.company_name = "Universal Workshop ERP"
        company.abbr = "UW"
        company.default_currency = "OMR"
        company.country = "Oman"
        company.insert()

        print(f"✅ تم إنشاء الشركة: {company.name}")

        # تعيين الشركة كافتراضية
        try:
            global_defaults = frappe.get_doc("Global Defaults")
            global_defaults.default_company = company.name
            global_defaults.save()
            print(f"✅ تم تعيين الشركة الافتراضية: {company.name}")
        except Exception as e:
            print(f"❌ خطأ في تعيين الشركة الافتراضية: {e}")

        frappe.db.commit()
        print("✅ تم حفظ التغييرات")

    else:
        company_name = companies[0].name
        print(f"✅ الشركة موجودة بالفعل: {company_name}")

        # التأكد من أنها مُعيّنة كافتراضية
        try:
            global_defaults = frappe.get_doc("Global Defaults")
            if not global_defaults.default_company:
                global_defaults.default_company = company_name
                global_defaults.save()
                frappe.db.commit()
                print(f"✅ تم تعيين الشركة الافتراضية: {company_name}")
        except Exception as e:
            print(f"❌ خطأ في تعيين الشركة الافتراضية: {e}")


if __name__ == "__main__":
    setup_default_company()
