import frappe

# التحقق من الحالة الحالية
current_setup_status = frappe.db.get_single_value("System Settings", "setup_complete")
current_home_page = frappe.db.get_default("desktop:home_page")

print("📊 الحالة الحالية:")
print(f"   - Setup Complete: {current_setup_status}")
print(f"   - Home Page: {current_home_page}")

# إعادة تعيين الإعدادات
print("🔧 إعادة تعيين إعدادات النظام...")

frappe.db.set_single_value("System Settings", "setup_complete", 0)
frappe.db.set_default("desktop:home_page", "setup-wizard")
frappe.db.commit()

print("✅ تم إعادة تعيين إعدادات Setup Wizard بنجاح!")

# التحقق من النتيجة
new_setup_status = frappe.db.get_single_value("System Settings", "setup_complete")
new_home_page = frappe.db.get_default("desktop:home_page")

print("📊 الحالة الجديدة:")
print(f"   - Setup Complete: {new_setup_status}")
print(f"   - Home Page: {new_home_page}")
