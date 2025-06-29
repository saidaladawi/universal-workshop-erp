# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import re
import uuid
from datetime import datetime, timedelta

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, cint, today, now


class ExtractedParts(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields

    def validate(self):
        """Validate extracted parts data"""
        self.validate_required_fields()
        self.validate_quality_grade()
        self.validate_pricing()
        self.validate_dimensions()
        self.set_default_values()
        self.generate_barcode()

    def before_save(self):
        """Actions before saving"""
        self.calculate_suggested_price()
        self.update_grade_descriptions()
        self.set_storage_date()

    def after_insert(self):
        """Actions after insertion"""
        self.create_inventory_movement()
        self.update_disassembly_plan_status()

    def validate_required_fields(self):
        """Validate required fields for extracted parts"""
        if not self.part_name:
            frappe.throw(_("Part Name (English) is required"))

        if not self.part_name_ar:
            frappe.throw(_("Part Name (Arabic) is required"))

        if not self.scrap_vehicle:
            frappe.throw(_("Source Scrap Vehicle is required"))

        if not self.quality_grade:
            frappe.throw(_("Quality Grade is required"))

        if not self.extraction_date:
            frappe.throw(_("Extraction Date is required"))

    def validate_quality_grade(self):
        """Validate quality grade and certification status"""
        valid_grades = [
            "Grade A - Excellent",
            "Grade B - Good",
            "Grade C - Average",
            "Grade D - Poor/Scrap",
        ]

        if self.quality_grade not in valid_grades:
            frappe.throw(_("Invalid quality grade selected"))

        # Grade A and B require inspection for certification
        if self.quality_grade in ["Grade A - Excellent", "Grade B - Good"]:
            if not self.inspector and self.certification_status == "Certified":
                frappe.throw(_("Inspector is required for Grade A and B parts"))

        # Ensure inspection date is provided for certified parts
        if self.certification_status == "Certified" and not self.inspection_date:
            self.inspection_date = now()

    def validate_pricing(self):
        """Validate pricing information"""
        if self.final_price and self.final_price <= 0:
            frappe.throw(_("Final price must be greater than zero"))

        if self.base_price_new and self.final_price:
            if self.final_price > self.base_price_new:
                frappe.msgprint(_("Warning: Final price is higher than new part price"))

        if self.suggested_price and self.final_price:
            variance = abs(self.final_price - self.suggested_price) / self.suggested_price * 100
            if variance > 50:  # 50% variance threshold
                frappe.msgprint(_("Warning: Final price varies significantly from suggested price"))

    def validate_dimensions(self):
        """Validate physical dimensions"""
        if self.length_mm and self.length_mm <= 0:
            frappe.throw(_("Length must be greater than zero"))
        if self.width_mm and self.width_mm <= 0:
            frappe.throw(_("Width must be greater than zero"))
        if self.height_mm and self.height_mm <= 0:
            frappe.throw(_("Height must be greater than zero"))
        if self.weight_kg and self.weight_kg <= 0:
            frappe.throw(_("Weight must be greater than zero"))

    def set_default_values(self):
        """Set default values for new parts"""
        if not self.created_by:
            self.created_by = frappe.session.user

        if not self.currency:
            self.currency = "OMR"  # Default to Omani Rial

        if not self.part_code:
            self.part_code = self.generate_part_code()

        if not self.availability_status:
            self.availability_status = "Available"

        if not self.workflow_state:
            self.workflow_state = "Extracted"

        if not self.certification_status:
            self.certification_status = "Pending Inspection"

    def generate_part_code(self):
        """Generate unique part code"""
        vehicle_prefix = ""
        if self.scrap_vehicle:
            scrap_vehicle = frappe.get_doc("Scrap Vehicle", self.scrap_vehicle)
            if scrap_vehicle.vin_number:
                vehicle_prefix = scrap_vehicle.vin_number[-4:]  # Last 4 digits of VIN

        # Generate code: PREFIX-YYYYMMDD-HHMMSS-XXXX
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        random_suffix = str(uuid.uuid4())[:4].upper()

        return f"{vehicle_prefix}-{timestamp}-{random_suffix}"

    def generate_barcode(self):
        """Generate barcode for inventory tracking"""
        if not self.barcode and self.part_code:
            # Use part code as barcode base
            self.barcode = f"UW-{self.part_code}"

    def calculate_suggested_price(self):
        """Calculate suggested price based on quality grade and market factors"""
        if not self.base_price_new:
            return

        base_price = flt(self.base_price_new)
        grade_multipliers = {
            "Grade A - Excellent": 0.70,  # 70% of new price
            "Grade B - Good": 0.50,  # 50% of new price
            "Grade C - Average": 0.30,  # 30% of new price
            "Grade D - Poor/Scrap": 0.10,  # 10% of new price (scrap value)
        }

        multiplier = grade_multipliers.get(self.quality_grade, 0.30)

        # Apply market factor if provided
        if self.market_factor:
            multiplier *= flt(self.market_factor)

        # Apply condition adjustments
        condition_adjustments = {
            "Excellent": 1.10,  # +10%
            "Good": 1.00,  # No change
            "Fair": 0.85,  # -15%
            "Poor": 0.70,  # -30%
            "Damaged": 0.50,  # -50%
        }

        if self.physical_condition:
            condition_factor = condition_adjustments.get(self.physical_condition, 1.00)
            multiplier *= condition_factor

        # Apply functional status adjustments
        functional_adjustments = {
            "Fully Functional": 1.00,  # No change
            "Partially Functional": 0.75,  # -25%
            "Non-Functional": 0.40,  # -60%
            "Untested": 0.80,  # -20% (uncertainty discount)
        }

        if self.functional_status:
            functional_factor = functional_adjustments.get(self.functional_status, 0.80)
            multiplier *= functional_factor

        # Apply repair cost deduction
        suggested_price = base_price * multiplier
        if self.estimated_repair_cost:
            suggested_price -= flt(self.estimated_repair_cost)

        # Ensure minimum price (scrap value)
        min_price = base_price * 0.05  # 5% minimum
        suggested_price = max(suggested_price, min_price)

        self.suggested_price = round(suggested_price, 3)  # 3 decimal places for OMR

        # Set final price if not already set
        if not self.final_price:
            self.final_price = self.suggested_price

    def update_grade_descriptions(self):
        """Update grade descriptions based on quality grade"""
        grade_descriptions = {
            "Grade A - Excellent": {
                "en": "Like-new condition, minimal usage signs, 60-80% of new part value",
                "ar": "حالة شبه جديدة، علامات استخدام قليلة، 60-80% من قيمة القطعة الجديدة",
            },
            "Grade B - Good": {
                "en": "Good condition with minor surface wear, no repairs needed, 40-60% of new part value",
                "ar": "حالة جيدة مع تآكل سطحي بسيط، لا تحتاج إصلاحات، 40-60% من قيمة القطعة الجديدة",
            },
            "Grade C - Average": {
                "en": "Average condition, may need minor repairs before use, 20-40% of new part value",
                "ar": "حالة متوسطة، قد تحتاج إصلاحات بسيطة قبل الاستخدام، 20-40% من قيمة القطعة الجديدة",
            },
            "Grade D - Poor/Scrap": {
                "en": "Damaged, only suitable for recycling or partial use, scrap value",
                "ar": "متضررة، مناسبة فقط لإعادة التدوير أو الاستخدام الجزئي، قيمة الخردة",
            },
        }

        if self.quality_grade in grade_descriptions:
            descriptions = grade_descriptions[self.quality_grade]
            if not self.grade_description:
                self.grade_description = descriptions["en"]
            if not self.grade_description_ar:
                self.grade_description_ar = descriptions["ar"]

    def set_storage_date(self):
        """Set storage date when part is moved to warehouse"""
        if self.warehouse and not self.storage_date:
            self.storage_date = today()

    def create_inventory_movement(self):
        """Create inventory movement record for tracking"""
        # Create stock entry for the extracted part
        if self.warehouse:
            try:
                stock_entry = frappe.new_doc("Stock Entry")
                stock_entry.stock_entry_type = "Material Receipt"
                stock_entry.company = frappe.defaults.get_user_default("Company")

                stock_entry.append(
                    "items",
                    {
                        "item_code": self.part_code or self.name,
                        "item_name": self.part_name,
                        "qty": 1,
                        "uom": "Nos",
                        "t_warehouse": self.warehouse,
                        "basic_rate": self.final_price or 0,
                        "amount": self.final_price or 0,
                    },
                )

                stock_entry.insert(ignore_permissions=True)
                frappe.db.commit()

            except Exception as e:
                frappe.log_error(f"Failed to create stock entry for {self.name}: {str(e)}")

    def update_disassembly_plan_status(self):
        """Update disassembly plan with extracted part information"""
        if self.disassembly_plan and self.disassembly_step:
            try:
                disassembly_plan = frappe.get_doc("Disassembly Plan", self.disassembly_plan)

                # Find the corresponding step and update its status
                for step in disassembly_plan.disassembly_steps:
                    if step.name == self.disassembly_step:
                        step.actual_extracted_part = self.name
                        step.actual_extraction_date = self.extraction_date
                        step.actual_condition_grade = self.quality_grade
                        step.step_status = "Completed"
                        break

                disassembly_plan.save(ignore_permissions=True)
                frappe.db.commit()

            except Exception as e:
                frappe.log_error(
                    f"Failed to update disassembly plan {self.disassembly_plan}: {str(e)}"
                )


# WhiteListed API Methods


@frappe.whitelist()
def get_part_pricing_analysis(part_name, quality_grade, base_price_new=None):
    """Get comprehensive pricing analysis for a part"""

    if not base_price_new:
        # Try to fetch base price from Item master if exists
        item_price = frappe.db.get_value("Item Price", {"item_code": part_name}, "price_list_rate")
        if item_price:
            base_price_new = item_price
        else:
            base_price_new = 100  # Default base price for calculation

    base_price = flt(base_price_new)

    grade_analysis = {
        "Grade A - Excellent": {
            "multiplier": 0.70,
            "price_range": {"min": base_price * 0.60, "max": base_price * 0.80},
            "market_position": "Premium used part",
            "target_buyers": "Quality-conscious customers",
        },
        "Grade B - Good": {
            "multiplier": 0.50,
            "price_range": {"min": base_price * 0.40, "max": base_price * 0.60},
            "market_position": "Standard used part",
            "target_buyers": "Regular repair shops",
        },
        "Grade C - Average": {
            "multiplier": 0.30,
            "price_range": {"min": base_price * 0.20, "max": base_price * 0.40},
            "market_position": "Budget option",
            "target_buyers": "Budget-conscious customers",
        },
        "Grade D - Poor/Scrap": {
            "multiplier": 0.10,
            "price_range": {"min": base_price * 0.05, "max": base_price * 0.15},
            "market_position": "Recycling/parts source",
            "target_buyers": "Scrap dealers, DIY enthusiasts",
        },
    }

    analysis = grade_analysis.get(quality_grade, grade_analysis["Grade C - Average"])
    analysis["suggested_price"] = base_price * analysis["multiplier"]
    analysis["base_price_new"] = base_price

    return analysis


@frappe.whitelist()
def generate_quality_inspection_checklist(part_name, quality_grade):
    """Generate quality inspection checklist based on part type and target grade"""

    # Common inspection points for all parts
    base_checklist = [
        {
            "point": "Visual inspection for cracks or damage",
            "point_ar": "فحص بصري للشقوق أو الأضرار",
            "critical": True,
        },
        {
            "point": "Check for corrosion or rust",
            "point_ar": "فحص التآكل أو الصدأ",
            "critical": True,
        },
        {
            "point": "Verify part number and compatibility",
            "point_ar": "التحقق من رقم القطعة والتوافق",
            "critical": True,
        },
        {
            "point": "Test functional operation (if applicable)",
            "point_ar": "اختبار التشغيل الوظيفي (إن أمكن)",
            "critical": True,
        },
    ]

    # Grade-specific additional checks
    grade_specific_checks = {
        "Grade A - Excellent": [
            {
                "point": "Surface finish quality assessment",
                "point_ar": "تقييم جودة التشطيب السطحي",
                "critical": True,
            },
            {
                "point": "Dimensional accuracy verification",
                "point_ar": "التحقق من دقة الأبعاد",
                "critical": True,
            },
        ],
        "Grade B - Good": [
            {
                "point": "Minor wear pattern analysis",
                "point_ar": "تحليل أنماط التآكل البسيط",
                "critical": False,
            }
        ],
        "Grade C - Average": [
            {
                "point": "Repair feasibility assessment",
                "point_ar": "تقييم إمكانية الإصلاح",
                "critical": True,
            }
        ],
        "Grade D - Poor/Scrap": [
            {
                "point": "Salvageable components identification",
                "point_ar": "تحديد المكونات القابلة للإنقاذ",
                "critical": False,
            }
        ],
    }

    checklist = base_checklist.copy()
    if quality_grade in grade_specific_checks:
        checklist.extend(grade_specific_checks[quality_grade])

    return {
        "part_name": part_name,
        "target_grade": quality_grade,
        "checklist": checklist,
        "estimated_time_minutes": len(checklist) * 3,  # 3 minutes per check point
    }


@frappe.whitelist()
def get_market_price_comparison(part_name, quality_grade, region="Oman"):
    """Get market price comparison for similar parts"""

    # This would typically integrate with external APIs or market data
    # For now, providing simulated market data structure

    base_data = {
        "part_name": part_name,
        "quality_grade": quality_grade,
        "region": region,
        "currency": "OMR" if region == "Oman" else "AED",
        "data_sources": ["Local market survey", "Online marketplaces", "Competitor analysis"],
    }

    if region == "Oman":
        price_multipliers = {
            "Grade A - Excellent": 0.75,
            "Grade B - Good": 0.55,
            "Grade C - Average": 0.35,
            "Grade D - Poor/Scrap": 0.12,
        }
    else:  # UAE or other Gulf markets
        price_multipliers = {
            "Grade A - Excellent": 0.72,
            "Grade B - Good": 0.52,
            "Grade C - Average": 0.32,
            "Grade D - Poor/Scrap": 0.10,
        }

    estimated_base_price = 100  # This would come from market research
    market_price = estimated_base_price * price_multipliers.get(quality_grade, 0.35)

    return {
        **base_data,
        "estimated_market_price": market_price,
        "price_range": {"low": market_price * 0.85, "high": market_price * 1.15},
        "demand_level": "Medium",  # This would be calculated from historical data
        "recommendation": (
            "Competitive pricing" if market_price > 20 else "Consider bundling with other parts"
        ),
    }


@frappe.whitelist()
def get_part_photos_summary(extracted_part_name):
    """Get summary of photos for an extracted part"""

    part = frappe.get_doc("Extracted Parts", extracted_part_name)

    summary = {
        "part_name": part.part_name,
        "part_name_ar": part.part_name_ar,
        "primary_photo": part.primary_photo,
        "total_photos": len(part.photo_gallery) if part.photo_gallery else 0,
        "photos_by_type": {},
        "defect_photos": 0,
        "documentation_complete": False,
    }

    required_photo_types = [
        "Front View",
        "Back View",
        "Left Side",
        "Right Side",
        "Overall Condition",
    ]
    found_types = []

    if part.photo_gallery:
        for photo in part.photo_gallery:
            photo_type = photo.photo_type
            if photo_type not in summary["photos_by_type"]:
                summary["photos_by_type"][photo_type] = 0
            summary["photos_by_type"][photo_type] += 1

            if photo.shows_defect:
                summary["defect_photos"] += 1

            if photo_type in required_photo_types:
                found_types.append(photo_type)

    # Check if documentation is complete
    summary["documentation_complete"] = len(found_types) >= 4  # At least 4 of 5 required types
    summary["missing_photo_types"] = [pt for pt in required_photo_types if pt not in found_types]

    return summary


@frappe.whitelist()
def create_barcode_labels(extracted_parts_list):
    """Generate barcode labels for multiple extracted parts"""

    if isinstance(extracted_parts_list, str):
        extracted_parts_list = [extracted_parts_list]

    labels = []

    for part_name in extracted_parts_list:
        try:
            part = frappe.get_doc("Extracted Parts", part_name)

            label_data = {
                "part_name": part.part_name,
                "part_name_ar": part.part_name_ar,
                "part_code": part.part_code,
                "barcode": part.barcode,
                "quality_grade": part.quality_grade,
                "final_price": part.final_price,
                "currency": part.currency,
                "extraction_date": part.extraction_date,
                "shelf_location": part.shelf_location,
                "vehicle_vin": part.vehicle_vin,
            }

            labels.append(label_data)

        except Exception as e:
            frappe.log_error(f"Failed to generate label for {part_name}: {str(e)}")

    return labels


@frappe.whitelist()
def update_part_availability(part_name, new_status, notes=None):
    """Update part availability status with tracking"""

    try:
        part = frappe.get_doc("Extracted Parts", part_name)
        old_status = part.availability_status

        part.availability_status = new_status
        if notes:
            # Add timestamped note to a notes field (would need to add this field)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status_note = f"[{timestamp}] Status changed from {old_status} to {new_status}: {notes}"
            # This would append to a status_notes field

        part.save(ignore_permissions=True)
        frappe.db.commit()

        return {
            "success": True,
            "message": f"Status updated from {old_status} to {new_status}",
            "part_name": part.part_name,
        }

    except Exception as e:
        frappe.log_error(f"Failed to update status for {part_name}: {str(e)}")
        return {"success": False, "message": str(e)}
