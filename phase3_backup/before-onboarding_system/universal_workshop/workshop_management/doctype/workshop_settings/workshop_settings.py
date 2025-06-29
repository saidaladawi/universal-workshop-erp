# Copyright (c) 2025, Said Al-Adowi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import os
import json

class WorkshopSettings(Document):
    """إعدادات الورشة الشاملة"""

    def validate(self):
        """التحقق من صحة البيانات"""
        self.validate_colors()
        self.validate_api_settings()

    def validate_colors(self):
        """التحقق من صحة الألوان"""
        if self.primary_color and not self.primary_color.startswith('#'):
            self.primary_color = f"#{self.primary_color}"

        if self.secondary_color and not self.secondary_color.startswith('#'):
            self.secondary_color = f"#{self.secondary_color}"

    def validate_api_settings(self):
        """إنشاء API Key تلقائياً عند التفعيل"""
        if self.enable_api_access and not self.api_key:
            import secrets
            self.api_key = secrets.token_urlsafe(32)

    def on_update(self):
        """بعد حفظ الإعدادات"""
        self.apply_theme_changes()
        self.update_system_settings()
        self.sync_company_settings()

    def apply_theme_changes(self):
        """تطبيق تغييرات الثيم"""
        if self.primary_color or self.secondary_color:
            self.create_custom_theme()

    def create_custom_theme(self):
        """إنشاء ثيم مُخصص"""

        # CSS مُخصص للثيم
        automotive_css = f"""
        /* Universal Workshop Automotive Theme */
        :root {{
            --uw-primary: {self.primary_color or '#1976d2'};
            --uw-secondary: {self.secondary_color or '#424242'};
            --uw-accent: {self.primary_color or '#1976d2'}22;
            --uw-gradient: linear-gradient(135deg, var(--uw-primary), var(--uw-secondary));
        }}

        /* === HEADER STYLING === */
        .navbar {{
            background: var(--uw-gradient) !important;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}

        .navbar-brand {{
            display: flex;
            align-items: center;
            font-weight: bold;
            color: white !important;
        }}

        .navbar-brand .workshop-logo {{
            max-height: 35px;
            margin-right: 10px;
            border-radius: 4px;
        }}

        /* === SIDEBAR AUTOMOTIVE THEME === */
        .sidebar {{
            background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%) !important;
            border-right: 3px solid var(--uw-primary);
        }}

        .sidebar .sidebar-item {{
            transition: all 0.3s ease;
            border-radius: 8px;
            margin: 2px 8px;
        }}

        .sidebar .sidebar-item:hover {{
            background: var(--uw-accent);
            transform: translateX(5px);
        }}

        .sidebar .sidebar-item.active {{
            background: var(--uw-primary);
            color: white;
        }}

        /* === AUTOMOTIVE ICONS === */
        .automotive-icon {{
            background: var(--uw-gradient);
            color: white;
            border-radius: 50%;
            padding: 12px;
            margin-right: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }}

        /* === CARDS & MODULES === */
        .module-card {{
            background: white;
            border: 1px solid #e3f2fd;
            border-left: 4px solid var(--uw-primary);
            border-radius: 8px;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}

        .module-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: var(--uw-gradient);
        }}

        .module-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.15);
            border-left-color: var(--uw-secondary);
        }}

        /* === BUTTONS === */
        .btn-primary {{
            background: var(--uw-gradient);
            border: none;
            border-radius: 6px;
            transition: all 0.3s ease;
        }}

        .btn-primary:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }}

        /* === AUTOMOTIVE DASHBOARD === */
        .automotive-dashboard {{
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
        }}

        .dashboard-card {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            border-top: 4px solid var(--uw-primary);
        }}

        /* === VEHICLE SPECIFIC === */
        .vehicle-status-indicator {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
        }}

        .vehicle-status-indicator.available {{ background: #4caf50; }}
        .vehicle-status-indicator.maintenance {{ background: #ff9800; }}
        .vehicle-status-indicator.repair {{ background: #f44336; }}

        /* === SERVICE BAY STYLING === */
        .service-bay {{
            background: white;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            transition: all 0.3s ease;
            position: relative;
        }}

        .service-bay.occupied {{
            border-color: var(--uw-primary);
            background: var(--uw-accent);
        }}

        .service-bay.available {{
            border-color: #4caf50;
        }}

        .service-bay:hover {{
            transform: scale(1.05);
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}

        /* === RESPONSIVE DESIGN === */
        @media (max-width: 768px) {{
            .navbar-brand .workshop-logo {{
                max-height: 30px;
            }}

            .module-card {{
                margin: 10px 5px;
            }}

            .automotive-icon {{
                padding: 8px;
                margin-right: 8px;
            }}
        }}

        /* === LOADING ANIMATIONS === */
        .uw-loading {{
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid var(--uw-accent);
            border-radius: 50%;
            border-top-color: var(--uw-primary);
            animation: spin 1s ease-in-out infinite;
        }}

        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}

        /* === PRINT STYLES === */
        @media print {{
            .automotive-dashboard {{
                background: white !important;
            }}

            .module-card {{
                border: 1px solid #ccc !important;
                box-shadow: none !important;
            }}
        }}
        """

        # JavaScript مُخصص للثيم
        automotive_js = f"""
        // Universal Workshop Theme JavaScript
        frappe.ready(function() {{
            // إضافة الشعار للـ navbar
            if ('{self.logo}' && $('.navbar-brand .workshop-logo').length === 0) {{
                $('.navbar-brand').prepend('<img src="{self.logo}" alt="Workshop Logo" class="workshop-logo">');
            }}

            // إضافة أيقونات السيارات للوحدات
            const automotiveIcons = {{
                'Vehicle': 'fa fa-car',
                'Service Order': 'fa fa-wrench',
                'Technician': 'fa fa-user-cog',
                'Customer': 'fa fa-users',
                'Parts': 'fa fa-cogs',
                'Inventory': 'fa fa-boxes'
            }};

            // تطبيق الأيقونات
            Object.keys(automotiveIcons).forEach(function(module) {{
                $(`.sidebar-item:contains("${{module}}")`)
                    .prepend(`<i class="${{automotiveIcons[module]}} automotive-icon"></i>`);
            }});

            // إضافة مؤشرات حالة المركبات
            $('.vehicle-list-item').each(function() {{
                const status = $(this).data('status') || 'available';
                $(this).prepend(`<span class="vehicle-status-indicator ${{status}}"></span>`);
            }});

            // تحديث الثيم عند تغيير الإعدادات
            window.updateWorkshopTheme = function() {{
                $('head').append('<style id="workshop-custom-theme">{automotive_css}</style>');
            }};

            // تطبيق الثيم فوراً
            window.updateWorkshopTheme();
        }});
        """

        # حفظ الثيم المُخصص
        self.save_custom_theme(automotive_css, automotive_js)

    def save_custom_theme(self, css, js):
        """حفظ الثيم المُخصص"""
        try:
            # إنشاء أو تحديث Custom HTML Block
            html_block_name = "Universal Workshop Theme"

            if frappe.db.exists("Custom HTML Block", html_block_name):
                html_block = frappe.get_doc("Custom HTML Block", html_block_name)
            else:
                html_block = frappe.new_doc("Custom HTML Block")
                html_block.name = html_block_name

            html_block.html = f"<style>{css}</style>"
            html_block.script = js
            html_block.save(ignore_permissions=True)

            frappe.db.commit()

        except Exception as e:
            frappe.log_error(f"Theme Save Error: {str(e)}")

    def update_system_settings(self):
        """تحديث إعدادات النظام"""
        if self.time_zone or self.language:
            system_settings = frappe.get_single("System Settings")

            if self.time_zone:
                system_settings.time_zone = self.time_zone

            if self.language:
                system_settings.language = self.language

            if self.date_format:
                system_settings.date_format = self.date_format

            system_settings.save(ignore_permissions=True)

    def sync_company_settings(self):
        """مزامنة إعدادات الشركة"""
        if self.workshop_name and self.default_currency:
            companies = frappe.get_all("Company", limit=1)
            if companies:
                company = frappe.get_doc("Company", companies[0].name)
                company.company_name = self.workshop_name
                company.default_currency = self.default_currency
                company.country = self.country
                company.save(ignore_permissions=True)

    @frappe.whitelist()
    def generate_api_key(self):
        """إنشاء مفتاح API جديد"""
        import secrets
        self.api_key = secrets.token_urlsafe(32)
        self.save(ignore_permissions=True)
        return self.api_key

    @frappe.whitelist()
    def test_theme(self):
        """اختبار الثيم"""
        try:
            self.create_custom_theme()
            return {"status": "success", "message": "Theme applied successfully!"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @frappe.whitelist()
    def reset_theme(self):
        """إعادة تعيين الثيم للافتراضي"""
        self.primary_color = "#1976d2"
        self.secondary_color = "#424242"
        self.theme_style = "Modern"
        self.save(ignore_permissions=True)
        return {"status": "success", "message": "Theme reset to default!"}
