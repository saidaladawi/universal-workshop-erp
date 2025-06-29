# pylint: disable=no-member
import frappe
from frappe import _
from frappe.model.document import Document


class VehicleInspectionItem(Document):
    """Child DocType for individual inspection items in vehicle inspection checklist"""

    def validate(self):
        """Validate inspection item data"""
        self.validate_inspection_item()
        self.set_arabic_translations()
        self.calculate_priority_score()

    def validate_inspection_item(self):
        """Validate inspection item details"""
        if not self.item_name:
            frappe.throw(_("Inspection item name is required"))

        # Validate inspection result
        valid_results = ["Pass", "Fail", "Needs Attention", "Not Applicable", "Not Checked"]
        if self.inspection_result and self.inspection_result not in valid_results:
            frappe.throw(
                _("Invalid inspection result. Must be one of: {0}").format(", ".join(valid_results))
            )

        # Set default result if not provided
        if not self.inspection_result:
            self.inspection_result = "Not Checked"

        # Validate severity if result is Fail or Needs Attention
        if self.inspection_result in ["Fail", "Needs Attention"] and not self.severity:
            self.severity = "Medium"

    def set_arabic_translations(self):
        """Set Arabic translations for inspection items and results"""
        # Arabic translations for common inspection items
        item_translations = {
            # Engine Components
            "Engine Oil Level": "مستوى زيت المحرك",
            "Engine Oil Condition": "حالة زيت المحرك",
            "Coolant Level": "مستوى سائل التبريد",
            "Belt Condition": "حالة السيور",
            "Battery Condition": "حالة البطارية",
            "Air Filter": "فلتر الهواء",
            "Spark Plugs": "شموع الاحتراق",
            # Braking System
            "Brake Pads Front": "تيل الفرامل الأمامية",
            "Brake Pads Rear": "تيل الفرامل الخلفية",
            "Brake Fluid Level": "مستوى سائل الفرامل",
            "Brake Disc Condition": "حالة أقراص الفرامل",
            "Handbrake Operation": "عمل فرامل اليد",
            # Tires and Wheels
            "Tire Tread Depth Front Left": "عمق مداس الإطار الأمامي الأيسر",
            "Tire Tread Depth Front Right": "عمق مداس الإطار الأمامي الأيمن",
            "Tire Tread Depth Rear Left": "عمق مداس الإطار الخلفي الأيسر",
            "Tire Tread Depth Rear Right": "عمق مداس الإطار الخلفي الأيمن",
            "Tire Pressure": "ضغط الإطارات",
            "Wheel Alignment": "ضبط العجلات",
            "Wheel Balancing": "توازن العجلات",
            # Lighting System
            "Headlights": "المصابيح الأمامية",
            "Taillights": "المصابيح الخلفية",
            "Indicators": "أضواء الاتجاه",
            "Hazard Lights": "أضواء الطوارئ",
            "Interior Lights": "الإضاءة الداخلية",
            # Suspension and Steering
            "Shock Absorbers": "مساعدات الصدمات",
            "Steering Wheel Play": "لعبة عجلة القيادة",
            "Power Steering Fluid": "سائل المقود المعزز",
            "Suspension Noise": "أصوات التعليق",
            # Electrical System
            "Alternator": "المولد",
            "Starter Motor": "محرك البداية",
            "Fuses": "الفيوزات",
            "Wiring Condition": "حالة الأسلاك",
            # Body and Interior
            "Seat Belts": "أحزمة الأمان",
            "Horn": "الزمور",
            "Windscreen": "الزجاج الأمامي",
            "Mirrors": "المرايا",
            "Door Locks": "أقفال الأبواب",
            "Window Operation": "عمل النوافذ",
            # Exhaust System
            "Exhaust Pipe": "أنبوب العادم",
            "Muffler": "كاتم الصوت",
            "Catalytic Converter": "المحول الحفاز",
            "Emissions": "الانبعاثات",
        }

        # Set Arabic item name if available
        if self.item_name and not self.item_name_ar:
            self.item_name_ar = item_translations.get(self.item_name, self.item_name)

        # Arabic translations for inspection results
        result_translations = {
            "Pass": "مقبول",
            "Fail": "راسب",
            "Needs Attention": "يحتاج انتباه",
            "Not Applicable": "غير قابل للتطبيق",
            "Not Checked": "غير محقق",
        }

        if self.inspection_result:
            self.inspection_result_ar = result_translations.get(
                self.inspection_result, self.inspection_result
            )

        # Arabic translations for severity levels
        severity_translations = {
            "Critical": "حرج",
            "High": "عالي",
            "Medium": "متوسط",
            "Low": "منخفض",
        }

        if self.severity:
            self.severity_ar = severity_translations.get(self.severity, self.severity)

    def calculate_priority_score(self):
        """Calculate priority score based on result and severity"""
        priority_scores = {"Critical": 10, "High": 7, "Medium": 5, "Low": 2}

        result_multipliers = {
            "Fail": 1.0,
            "Needs Attention": 0.7,
            "Pass": 0.0,
            "Not Applicable": 0.0,
            "Not Checked": 0.1,
        }

        severity_score = priority_scores.get(self.severity or "Low", 2)
        result_multiplier = result_multipliers.get(self.inspection_result or "Not Checked", 0.1)

        self.priority_score = int(severity_score * result_multiplier)

    def before_save(self):
        """Actions before saving the inspection item"""
        # Set checked date and user if result is not 'Not Checked'
        if self.inspection_result and self.inspection_result != "Not Checked":
            if not self.checked_date:
                self.checked_date = frappe.utils.now()
            if not self.checked_by:
                self.checked_by = frappe.session.user

        # Auto-generate remarks for critical items
        self.set_auto_remarks()

    def set_auto_remarks(self):
        """Set automatic remarks based on inspection result and severity"""
        if self.inspection_result == "Fail" and self.severity == "Critical":
            if not self.remarks:
                self.remarks = _("CRITICAL: Immediate attention required before vehicle operation")
        elif self.inspection_result == "Fail" and self.severity == "High":
            if not self.remarks:
                self.remarks = _("HIGH PRIORITY: Should be addressed within 1 week")
        elif self.inspection_result == "Needs Attention" and not self.remarks:
            self.remarks = _("Monitor and schedule maintenance as needed")


@frappe.whitelist()
def get_inspection_checklist_template(inspection_type="General"):
    """Get standard inspection checklist template based on inspection type"""

    templates = {
        "General": [
            {"item_name": "Engine Oil Level", "category": "Engine", "severity": "Medium"},
            {"item_name": "Brake Pads Front", "category": "Brakes", "severity": "High"},
            {"item_name": "Brake Pads Rear", "category": "Brakes", "severity": "High"},
            {"item_name": "Tire Tread Depth Front Left", "category": "Tires", "severity": "High"},
            {"item_name": "Tire Tread Depth Front Right", "category": "Tires", "severity": "High"},
            {"item_name": "Tire Tread Depth Rear Left", "category": "Tires", "severity": "High"},
            {"item_name": "Tire Tread Depth Rear Right", "category": "Tires", "severity": "High"},
            {"item_name": "Headlights", "category": "Lights", "severity": "Medium"},
            {"item_name": "Taillights", "category": "Lights", "severity": "Medium"},
            {"item_name": "Seat Belts", "category": "Safety", "severity": "Critical"},
        ],
        "Pre-Purchase": [
            {"item_name": "Engine Oil Condition", "category": "Engine", "severity": "High"},
            {"item_name": "Coolant Level", "category": "Engine", "severity": "Medium"},
            {"item_name": "Belt Condition", "category": "Engine", "severity": "Medium"},
            {"item_name": "Battery Condition", "category": "Electrical", "severity": "Medium"},
            {"item_name": "Brake Disc Condition", "category": "Brakes", "severity": "High"},
            {"item_name": "Shock Absorbers", "category": "Suspension", "severity": "Medium"},
            {"item_name": "Exhaust Pipe", "category": "Exhaust", "severity": "Medium"},
            {"item_name": "Body Rust", "category": "Body", "severity": "Low"},
            {"item_name": "Interior Condition", "category": "Interior", "severity": "Low"},
        ],
        "Annual": [
            {"item_name": "Emissions", "category": "Exhaust", "severity": "Critical"},
            {"item_name": "Handbrake Operation", "category": "Brakes", "severity": "High"},
            {"item_name": "Steering Wheel Play", "category": "Steering", "severity": "High"},
            {"item_name": "Horn", "category": "Safety", "severity": "Medium"},
            {"item_name": "Windscreen", "category": "Safety", "severity": "High"},
            {"item_name": "Mirrors", "category": "Safety", "severity": "Medium"},
        ],
    }

    return templates.get(inspection_type, templates["General"])


@frappe.whitelist()
def bulk_update_inspection_results(inspection_id, items_data):
    """Bulk update inspection results for multiple items"""
    try:
        import json

        if isinstance(items_data, str):
            items_data = json.loads(items_data)

        updated_count = 0
        for item_data in items_data:
            if "name" in item_data:
                item_doc = frappe.get_doc("Vehicle Inspection Item", item_data["name"])

                # Update fields
                for field in ["inspection_result", "severity", "remarks", "measured_value"]:
                    if field in item_data:
                        setattr(item_doc, field, item_data[field])

                item_doc.save(ignore_permissions=True)
                updated_count += 1

        return {
            "status": "success",
            "message": _("Updated {0} inspection items").format(updated_count),
            "updated_count": updated_count,
        }

    except Exception as e:
        frappe.throw(_("Error updating inspection items: {0}").format(str(e)))
