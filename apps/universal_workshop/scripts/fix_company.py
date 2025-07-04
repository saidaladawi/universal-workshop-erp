#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import frappe


def fix_company_setup():
    """حل مشكلة Company is mandatory"""

    try:
        # التحقق من وجود شركة
        companies = frappe.get_list("Company", limit=1)
        print(f"عدد الشركات الموجودة: {len(companies)}")

        if not companies:
            print("🔧 إنشاء شركة افتراضية...")

            # إنشاء شركة جديدة
            company = frappe.new_doc("Company")
            company.company_name = "Universal Workshop ERP"
            company.abbr = "UW"
            company.default_currency = "OMR"
            company.country = "Oman"
            company.insert()

            print(f"✅ تم إنشاء الشركة: {company.name}")
            company_name = company.name
        else:
            company_name = companies[0].name
            print(f"✅ الشركة موجودة: {company_name}")

        # تعيين الشركة كافتراضية
        try:
            gd = frappe.get_single("Global Defaults")
            if not gd.default_company:
                gd.default_company = company_name
                gd.save()
                print(f"✅ تم تعيين الشركة الافتراضية: {company_name}")
            else:
                print(f"✅ الشركة الافتراضية موجودة: {gd.default_company}")
        except Exception as e:
            print(f"❌ خطأ في Global Defaults: {e}")

        # التأكد من الحفظ
        frappe.db.commit()
        print("✅ تم حفظ جميع التغييرات")

        return True

    except Exception as e:
        print(f"❌ خطأ عام: {e}")
        return False


if __name__ == "__main__":
    fix_company_setup()
