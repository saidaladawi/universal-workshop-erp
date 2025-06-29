import frappe


def get_boot_session_info():
    """تحديد معلومات جلسة المستخدم وحالة الإعداد"""
    if frappe.session.user == "Guest":
        return {}

    try:
        # التحقق من حالة إعداد الورشة
        workshop_profiles = frappe.get_all("Workshop Profile", limit=1)
        setup_complete = bool(workshop_profiles)

        # إضافة معلومات الإعداد لجلسة المستخدم
        return {
            "universal_workshop": {
                "setup_complete": setup_complete,
                "onboarding_url": "/workshop-onboarding",
                "needs_setup": not setup_complete
            }
        }
    except Exception as e:
        frappe.log_error(f"Error in boot session: {str(e)}")
        return {}
