import frappe
from frappe import _
from frappe.utils import nowdate, get_datetime, add_days, cint, flt
from frappe.model.document import Document
from typing import Dict, List, Optional
import json


class QualityControlWorkflow:
    """Comprehensive quality control workflow system for Universal Workshop ERP"""

    def __init__(self, service_order: str = None):
        self.service_order = service_order
        self.service_order_doc = None

        if service_order:
            self.service_order_doc = frappe.get_doc("Sales Order", service_order)

    def create_inspection_checklist(
        self,
        checklist_type: str = "comprehensive",
        vehicle_type: str = "passenger",
        custom_items: List[Dict] = None,
    ) -> Dict:
        """Create inspection checklist for service order"""
        try:
            # Get checklist template
            checklist_items = self._get_checklist_template(checklist_type, vehicle_type)

            # Add custom items if provided
            if custom_items:
                checklist_items.extend(custom_items)

            # Create inspection checklist document
            checklist_doc = frappe.new_doc("Quality Inspection Checklist")
            checklist_doc.service_order = self.service_order
            checklist_doc.checklist_type = checklist_type
            checklist_doc.vehicle_type = vehicle_type
            checklist_doc.inspection_date = nowdate()
            checklist_doc.status = "draft"

            # Add customer and vehicle details
            if self.service_order_doc:
                checklist_doc.customer = self.service_order_doc.customer
                checklist_doc.vehicle_registration = getattr(
                    self.service_order_doc, "vehicle_registration", ""
                )

            # Add checklist items
            for item in checklist_items:
                checklist_doc.append(
                    "inspection_items",
                    {
                        "item_code": item.get("code"),
                        "item_name": item.get("name"),
                        "item_name_ar": item.get("name_ar"),
                        "category": item.get("category"),
                        "inspection_type": item.get("type", "visual"),
                        "acceptance_criteria": item.get("criteria"),
                        "acceptance_criteria_ar": item.get("criteria_ar"),
                        "is_mandatory": item.get("mandatory", True),
                        "sort_order": item.get("order", 0),
                    },
                )

            checklist_doc.insert()

            return {
                "status": "success",
                "message": _("Inspection checklist created successfully"),
                "message_ar": "تم إنشاء قائمة فحص الجودة بنجاح",
                "checklist_id": checklist_doc.name,
                "total_items": len(checklist_items),
            }

        except Exception as e:
            frappe.log_error(f"Quality control checklist creation error: {str(e)}")
            return {
                "status": "error",
                "message": _("Failed to create inspection checklist: {0}").format(str(e)),
                "message_ar": "فشل في إنشاء قائمة فحص الجودة: {0}".format(str(e)),
            }

    def _get_checklist_template(self, checklist_type: str, vehicle_type: str) -> List[Dict]:
        """Get inspection checklist template based on type and vehicle"""

        # Base checklist items for all vehicles
        base_items = [
            {
                "code": "EXT_001",
                "name": "Exterior Body Condition",
                "name_ar": "حالة الهيكل الخارجي",
                "category": "Exterior",
                "type": "visual",
                "criteria": "No dents, scratches, or rust visible",
                "criteria_ar": "لا توجد خدوش أو صدأ مرئي",
                "mandatory": True,
                "order": 1,
            },
            {
                "code": "LGT_001",
                "name": "Headlights Functionality",
                "name_ar": "وظائف المصابيح الأمامية",
                "category": "Lighting",
                "type": "functional",
                "criteria": "All headlights working properly",
                "criteria_ar": "جميع المصابيح الأمامية تعمل بشكل صحيح",
                "mandatory": True,
                "order": 2,
            },
            {
                "code": "LGT_002",
                "name": "Tail Lights Functionality",
                "name_ar": "وظائف المصابيح الخلفية",
                "category": "Lighting",
                "type": "functional",
                "criteria": "All tail lights working properly",
                "criteria_ar": "جميع المصابيح الخلفية تعمل بشكل صحيح",
                "mandatory": True,
                "order": 3,
            },
            {
                "code": "BRK_001",
                "name": "Brake System Check",
                "name_ar": "فحص نظام الفرامل",
                "category": "Safety",
                "type": "functional",
                "criteria": "Brake pedal firm, no noise, adequate stopping power",
                "criteria_ar": "دواسة الفرامل ثابتة، لا ضوضاء، قوة توقف كافية",
                "mandatory": True,
                "order": 4,
            },
            {
                "code": "TIR_001",
                "name": "Tire Condition and Pressure",
                "name_ar": "حالة الإطارات والضغط",
                "category": "Safety",
                "type": "measurement",
                "criteria": "Proper tread depth (>1.6mm), correct pressure",
                "criteria_ar": "عمق المداس مناسب (>1.6مم)، ضغط صحيح",
                "mandatory": True,
                "order": 5,
            },
            {
                "code": "FLD_001",
                "name": "Engine Oil Level",
                "name_ar": "مستوى زيت المحرك",
                "category": "Engine",
                "type": "measurement",
                "criteria": "Oil level between MIN and MAX marks",
                "criteria_ar": "مستوى الزيت بين علامتي الحد الأدنى والأقصى",
                "mandatory": True,
                "order": 6,
            },
            {
                "code": "FLD_002",
                "name": "Coolant Level",
                "name_ar": "مستوى سائل التبريد",
                "category": "Engine",
                "type": "measurement",
                "criteria": "Coolant level adequate, no leaks",
                "criteria_ar": "مستوى سائل التبريد كافي، لا توجد تسريبات",
                "mandatory": True,
                "order": 7,
            },
            {
                "code": "BAT_001",
                "name": "Battery Condition",
                "name_ar": "حالة البطارية",
                "category": "Electrical",
                "type": "functional",
                "criteria": "Clean terminals, proper voltage (12.6V+)",
                "criteria_ar": "أطراف نظيفة، جهد مناسب (12.6 فولت+)",
                "mandatory": True,
                "order": 8,
            },
            {
                "code": "INT_001",
                "name": "Interior Cleanliness",
                "name_ar": "نظافة الداخل",
                "category": "Interior",
                "type": "visual",
                "criteria": "Interior clean and undamaged",
                "criteria_ar": "الداخل نظيف وغير تالف",
                "mandatory": False,
                "order": 9,
            },
            {
                "code": "DOC_001",
                "name": "Required Documents",
                "name_ar": "الوثائق المطلوبة",
                "category": "Documentation",
                "type": "visual",
                "criteria": "Registration, insurance valid",
                "criteria_ar": "التسجيل والتأمين ساريان",
                "mandatory": True,
                "order": 10,
            },
        ]

        # Additional items based on checklist type
        if checklist_type == "comprehensive":
            additional_items = [
                {
                    "code": "ENG_001",
                    "name": "Engine Performance",
                    "name_ar": "أداء المحرك",
                    "category": "Engine",
                    "type": "functional",
                    "criteria": "Smooth idle, no unusual noises",
                    "criteria_ar": "تشغيل سلس، لا أصوات غريبة",
                    "mandatory": True,
                    "order": 11,
                },
                {
                    "code": "TRN_001",
                    "name": "Transmission Operation",
                    "name_ar": "تشغيل ناقل الحركة",
                    "category": "Drivetrain",
                    "type": "functional",
                    "criteria": "Smooth shifting, no slipping",
                    "criteria_ar": "تغيير سلس للسرعات، لا انزلاق",
                    "mandatory": True,
                    "order": 12,
                },
                {
                    "code": "SUS_001",
                    "name": "Suspension System",
                    "name_ar": "نظام التعليق",
                    "category": "Chassis",
                    "type": "functional",
                    "criteria": "No excessive bounce, even ride",
                    "criteria_ar": "لا ارتداد مفرط، قيادة مستوية",
                    "mandatory": True,
                    "order": 13,
                },
                {
                    "code": "STR_001",
                    "name": "Steering System",
                    "name_ar": "نظام التوجيه",
                    "category": "Chassis",
                    "type": "functional",
                    "criteria": "Responsive steering, no play",
                    "criteria_ar": "توجيه متجاوب، لا حركة زائدة",
                    "mandatory": True,
                    "order": 14,
                },
                {
                    "code": "AC_001",
                    "name": "Air Conditioning",
                    "name_ar": "تكييف الهواء",
                    "category": "Comfort",
                    "type": "functional",
                    "criteria": "Cool air output, no unusual noises",
                    "criteria_ar": "هواء بارد، لا أصوات غريبة",
                    "mandatory": False,
                    "order": 15,
                },
            ]
            base_items.extend(additional_items)

        # Additional items for commercial vehicles
        if vehicle_type == "commercial":
            commercial_items = [
                {
                    "code": "LD_001",
                    "name": "Load Capacity Check",
                    "name_ar": "فحص سعة التحميل",
                    "category": "Commercial",
                    "type": "measurement",
                    "criteria": "Within legal load limits",
                    "criteria_ar": "ضمن حدود التحميل القانونية",
                    "mandatory": True,
                    "order": 16,
                },
                {
                    "code": "SF_001",
                    "name": "Safety Equipment",
                    "name_ar": "معدات السلامة",
                    "category": "Commercial",
                    "type": "visual",
                    "criteria": "Fire extinguisher, first aid kit present",
                    "criteria_ar": "طفاية حريق، حقيبة إسعافات أولية متوفرة",
                    "mandatory": True,
                    "order": 17,
                },
            ]
            base_items.extend(commercial_items)

        return base_items

    def update_inspection_item(
        self,
        checklist_id: str,
        item_code: str,
        status: str,
        notes: str = "",
        measurements: Dict = None,
        photos: List[str] = None,
    ) -> Dict:
        """Update inspection item status and details"""
        try:
            checklist_doc = frappe.get_doc("Quality Inspection Checklist", checklist_id)

            # Find the inspection item
            item_found = False
            for item in checklist_doc.inspection_items:
                if item.item_code == item_code:
                    item.status = status
                    item.inspector_notes = notes
                    item.inspector_notes_ar = self._translate_to_arabic(notes)
                    item.inspection_date = get_datetime()
                    item.inspector = frappe.session.user

                    # Add measurements
                    if measurements:
                        item.measurements = json.dumps(measurements)

                    # Add photo references
                    if photos:
                        item.photo_references = json.dumps(photos)

                    item_found = True
                    break

            if not item_found:
                return {
                    "status": "error",
                    "message": _("Inspection item not found: {0}").format(item_code),
                }

            # Update overall checklist status
            self._update_checklist_status(checklist_doc)

            checklist_doc.save()

            # Send real-time update
            self._publish_inspection_update(checklist_id, item_code, status)

            return {
                "status": "success",
                "message": _("Inspection item updated successfully"),
                "message_ar": "تم تحديث عنصر الفحص بنجاح",
                "item_code": item_code,
                "item_status": status,
                "overall_progress": self._calculate_inspection_progress(checklist_doc),
            }

        except Exception as e:
            frappe.log_error(f"Inspection item update error: {str(e)}")
            return {
                "status": "error",
                "message": _("Failed to update inspection item: {0}").format(str(e)),
            }

    def _update_checklist_status(self, checklist_doc):
        """Update overall checklist status based on item completion"""
        total_items = len(checklist_doc.inspection_items)
        completed_items = sum(
            1 for item in checklist_doc.inspection_items if item.status in ["pass", "fail"]
        )
        failed_items = sum(1 for item in checklist_doc.inspection_items if item.status == "fail")

        if completed_items == 0:
            checklist_doc.status = "draft"
        elif completed_items < total_items:
            checklist_doc.status = "in_progress"
        elif failed_items > 0:
            checklist_doc.status = "failed"
        else:
            checklist_doc.status = "passed"

        checklist_doc.completion_percentage = (
            (completed_items / total_items) * 100 if total_items > 0 else 0
        )
        checklist_doc.last_updated = get_datetime()

    def _calculate_inspection_progress(self, checklist_doc) -> Dict:
        """Calculate inspection progress metrics"""
        total_items = len(checklist_doc.inspection_items)
        completed_items = sum(
            1 for item in checklist_doc.inspection_items if item.status in ["pass", "fail"]
        )
        passed_items = sum(1 for item in checklist_doc.inspection_items if item.status == "pass")
        failed_items = sum(1 for item in checklist_doc.inspection_items if item.status == "fail")

        return {
            "total_items": total_items,
            "completed_items": completed_items,
            "passed_items": passed_items,
            "failed_items": failed_items,
            "completion_percentage": (
                (completed_items / total_items) * 100 if total_items > 0 else 0
            ),
            "pass_rate": (passed_items / completed_items) * 100 if completed_items > 0 else 0,
        }

    def approve_inspection(self, checklist_id: str, approval_notes: str = "") -> Dict:
        """Approve completed inspection checklist"""
        try:
            checklist_doc = frappe.get_doc("Quality Inspection Checklist", checklist_id)

            # Validate all mandatory items are completed
            incomplete_mandatory = []
            for item in checklist_doc.inspection_items:
                if item.is_mandatory and item.status not in ["pass", "fail"]:
                    incomplete_mandatory.append(item.item_name)

            if incomplete_mandatory:
                return {
                    "status": "error",
                    "message": _("Mandatory items not completed: {0}").format(
                        ", ".join(incomplete_mandatory)
                    ),
                    "message_ar": "عناصر إجبارية لم تكتمل: {0}".format(
                        ", ".join(incomplete_mandatory)
                    ),
                }

            # Check if any mandatory items failed
            failed_mandatory = []
            for item in checklist_doc.inspection_items:
                if item.is_mandatory and item.status == "fail":
                    failed_mandatory.append(item.item_name)

            if failed_mandatory:
                checklist_doc.status = "rejected"
                checklist_doc.rejection_reason = (
                    f"Failed mandatory items: {', '.join(failed_mandatory)}"
                )
                checklist_doc.rejection_reason_ar = (
                    f"عناصر إجبارية فاشلة: {', '.join(failed_mandatory)}"
                )
            else:
                checklist_doc.status = "approved"

            checklist_doc.approved_by = frappe.session.user
            checklist_doc.approval_date = get_datetime()
            checklist_doc.approval_notes = approval_notes
            checklist_doc.approval_notes_ar = self._translate_to_arabic(approval_notes)

            checklist_doc.save()

            # Update service order status
            if checklist_doc.status == "approved" and self.service_order:
                self._update_service_order_qc_status(True)
            elif checklist_doc.status == "rejected" and self.service_order:
                self._update_service_order_qc_status(False)

            # Send notifications
            self._send_inspection_notifications(checklist_doc)

            return {
                "status": "success",
                "message": _("Inspection {0} successfully").format(checklist_doc.status),
                "message_ar": "تم {0} الفحص بنجاح".format(
                    "الموافقة على" if checklist_doc.status == "approved" else "رفض"
                ),
                "checklist_status": checklist_doc.status,
                "approval_date": checklist_doc.approval_date,
            }

        except Exception as e:
            frappe.log_error(f"Inspection approval error: {str(e)}")
            return {
                "status": "error",
                "message": _("Failed to approve inspection: {0}").format(str(e)),
            }

    def _update_service_order_qc_status(self, passed: bool):
        """Update service order QC status"""
        if not self.service_order_doc:
            return

        self.service_order_doc.db_set("qc_status", "Passed" if passed else "Failed")
        self.service_order_doc.db_set("qc_completion_date", get_datetime())

        # Add to timeline
        self.service_order_doc.add_comment(
            "Info", _("Quality Control {0}").format("Passed" if passed else "Failed")
        )

    def _send_inspection_notifications(self, checklist_doc):
        """Send notifications for inspection completion"""
        try:
            # Import here to avoid circular imports
            from universal_workshop.sales_service.customer_notifications import (
                CustomerNotificationSystem,
            )

            if self.service_order:
                notification_system = CustomerNotificationSystem(self.service_order)

                if checklist_doc.status == "approved":
                    notification_system.send_workflow_notification(
                        "service_progress",
                        "completed",
                        {"qc_status": "passed", "completion_date": checklist_doc.approval_date},
                    )
                elif checklist_doc.status == "rejected":
                    notification_system.send_workflow_notification(
                        "service_progress",
                        "on_hold",
                        {
                            "hold_reason": "Quality control failed",
                            "hold_reason_ar": "فشل في مراقبة الجودة",
                        },
                    )
        except Exception as e:
            frappe.log_error(f"Inspection notification error: {str(e)}")

    def _publish_inspection_update(self, checklist_id: str, item_code: str, status: str):
        """Publish real-time inspection update"""
        try:
            frappe.publish_realtime(
                "inspection_update",
                {
                    "checklist_id": checklist_id,
                    "item_code": item_code,
                    "status": status,
                    "service_order": self.service_order,
                    "timestamp": get_datetime(),
                },
                user=frappe.session.user,
            )
        except Exception as e:
            frappe.log_error(f"Realtime inspection update error: {str(e)}")

    def get_inspection_dashboard(self, checklist_id: str = None) -> Dict:
        """Get inspection dashboard data"""
        try:
            if checklist_id:
                checklist_doc = frappe.get_doc("Quality Inspection Checklist", checklist_id)
                checklists = [checklist_doc]
            elif self.service_order:
                checklists = frappe.get_list(
                    "Quality Inspection Checklist",
                    filters={"service_order": self.service_order},
                    fields=["*"],
                )
            else:
                return {"status": "error", "message": "No checklist or service order specified"}

            dashboard_data = []

            for checklist in checklists:
                if isinstance(checklist, dict):
                    checklist_doc = frappe.get_doc(
                        "Quality Inspection Checklist", checklist["name"]
                    )
                else:
                    checklist_doc = checklist

                progress = self._calculate_inspection_progress(checklist_doc)

                # Get inspection items by category
                items_by_category = {}
                for item in checklist_doc.inspection_items:
                    category = item.category
                    if category not in items_by_category:
                        items_by_category[category] = []

                    items_by_category[category].append(
                        {
                            "code": item.item_code,
                            "name": item.item_name,
                            "name_ar": item.item_name_ar,
                            "status": item.status or "pending",
                            "mandatory": item.is_mandatory,
                            "inspector": item.inspector,
                            "inspection_date": item.inspection_date,
                            "notes": item.inspector_notes or "",
                            "measurements": (
                                json.loads(item.measurements) if item.measurements else {}
                            ),
                        }
                    )

                dashboard_data.append(
                    {
                        "checklist_id": checklist_doc.name,
                        "checklist_type": checklist_doc.checklist_type,
                        "vehicle_type": checklist_doc.vehicle_type,
                        "status": checklist_doc.status,
                        "progress": progress,
                        "items_by_category": items_by_category,
                        "approved_by": checklist_doc.approved_by,
                        "approval_date": checklist_doc.approval_date,
                        "creation_date": checklist_doc.creation,
                    }
                )

            return {
                "status": "success",
                "data": dashboard_data,
                "service_order": self.service_order,
                "total_checklists": len(dashboard_data),
            }

        except Exception as e:
            frappe.log_error(f"Inspection dashboard error: {str(e)}")
            return {
                "status": "error",
                "message": _("Failed to load inspection dashboard: {0}").format(str(e)),
            }

    def generate_inspection_report(self, checklist_id: str) -> Dict:
        """Generate comprehensive inspection report"""
        try:
            checklist_doc = frappe.get_doc("Quality Inspection Checklist", checklist_id)
            progress = self._calculate_inspection_progress(checklist_doc)

            # Group items by category and status
            report_data = {
                "checklist_info": {
                    "id": checklist_doc.name,
                    "service_order": checklist_doc.service_order,
                    "customer": checklist_doc.customer,
                    "vehicle_registration": checklist_doc.vehicle_registration,
                    "checklist_type": checklist_doc.checklist_type,
                    "vehicle_type": checklist_doc.vehicle_type,
                    "creation_date": checklist_doc.creation,
                    "completion_date": checklist_doc.approval_date,
                    "status": checklist_doc.status,
                },
                "summary": progress,
                "categories": {},
                "failed_items": [],
                "recommendations": [],
            }

            # Process inspection items
            for item in checklist_doc.inspection_items:
                category = item.category
                if category not in report_data["categories"]:
                    report_data["categories"][category] = {
                        "total": 0,
                        "passed": 0,
                        "failed": 0,
                        "pending": 0,
                        "items": [],
                    }

                report_data["categories"][category]["total"] += 1

                if item.status == "pass":
                    report_data["categories"][category]["passed"] += 1
                elif item.status == "fail":
                    report_data["categories"][category]["failed"] += 1
                    report_data["failed_items"].append(
                        {
                            "code": item.item_code,
                            "name": item.item_name,
                            "name_ar": item.item_name_ar,
                            "category": item.category,
                            "notes": item.inspector_notes,
                        }
                    )
                else:
                    report_data["categories"][category]["pending"] += 1

                report_data["categories"][category]["items"].append(
                    {
                        "code": item.item_code,
                        "name": item.item_name,
                        "name_ar": item.item_name_ar,
                        "status": item.status or "pending",
                        "mandatory": item.is_mandatory,
                        "criteria": item.acceptance_criteria,
                        "notes": item.inspector_notes,
                        "inspector": item.inspector,
                        "date": item.inspection_date,
                    }
                )

            # Generate recommendations
            if report_data["failed_items"]:
                report_data["recommendations"] = self._generate_recommendations(
                    report_data["failed_items"]
                )

            return {"status": "success", "report": report_data, "generated_date": get_datetime()}

        except Exception as e:
            frappe.log_error(f"Inspection report generation error: {str(e)}")
            return {
                "status": "error",
                "message": _("Failed to generate inspection report: {0}").format(str(e)),
            }

    def _generate_recommendations(self, failed_items: List[Dict]) -> List[Dict]:
        """Generate recommendations based on failed inspection items"""
        recommendations = []

        # Predefined recommendations based on common failures
        recommendation_map = {
            "BRK_001": {
                "action": "Replace brake pads and check brake fluid",
                "action_ar": "استبدال فحمات الفرامل وفحص سائل الفرامل",
                "priority": "High",
                "estimated_cost": "OMR 75.000",
            },
            "TIR_001": {
                "action": "Replace tires and check wheel alignment",
                "action_ar": "استبدال الإطارات وفحص توازن العجلات",
                "priority": "High",
                "estimated_cost": "OMR 200.000",
            },
            "LGT_001": {
                "action": "Replace headlight bulbs",
                "action_ar": "استبدال لمبات المصابيح الأمامية",
                "priority": "Medium",
                "estimated_cost": "OMR 25.000",
            },
            "FLD_001": {
                "action": "Change engine oil and filter",
                "action_ar": "تغيير زيت المحرك والفلتر",
                "priority": "High",
                "estimated_cost": "OMR 35.000",
            },
        }

        for item in failed_items:
            item_code = item["code"]
            if item_code in recommendation_map:
                recommendation = recommendation_map[item_code].copy()
                recommendation["item_code"] = item_code
                recommendation["item_name"] = item["name"]
                recommendation["category"] = item["category"]
                recommendations.append(recommendation)

        return recommendations

    def _translate_to_arabic(self, text: str) -> str:
        """Simple Arabic translation for common terms"""
        if not text:
            return ""

        translation_map = {
            "pass": "نجح",
            "fail": "فشل",
            "pending": "معلق",
            "approved": "موافق عليه",
            "rejected": "مرفوض",
            "Good condition": "حالة جيدة",
            "Needs attention": "يحتاج انتباه",
            "Replace immediately": "استبدل فوراً",
            "Check required": "فحص مطلوب",
            "Normal wear": "تآكل طبيعي",
            "Excellent": "ممتاز",
            "Satisfactory": "مرضي",
            "Poor": "ضعيف",
        }

        return translation_map.get(text, text)


# WhiteListed API Methods
@frappe.whitelist()
def create_inspection_checklist(
    service_order, checklist_type="comprehensive", vehicle_type="passenger"
):
    """Create new inspection checklist for service order"""
    try:
        qc_workflow = QualityControlWorkflow(service_order)
        return qc_workflow.create_inspection_checklist(checklist_type, vehicle_type)
    except Exception as e:
        frappe.log_error(f"API create inspection checklist error: {str(e)}")
        return {
            "status": "error",
            "message": _("Failed to create inspection checklist: {0}").format(str(e)),
        }


@frappe.whitelist()
def update_inspection_item(
    checklist_id, item_code, status, notes="", measurements=None, photos=None
):
    """Update inspection item status and details"""
    try:
        # Parse JSON parameters
        if measurements and isinstance(measurements, str):
            measurements = json.loads(measurements)
        if photos and isinstance(photos, str):
            photos = json.loads(photos)

        qc_workflow = QualityControlWorkflow()
        return qc_workflow.update_inspection_item(
            checklist_id, item_code, status, notes, measurements, photos
        )
    except Exception as e:
        frappe.log_error(f"API update inspection item error: {str(e)}")
        return {
            "status": "error",
            "message": _("Failed to update inspection item: {0}").format(str(e)),
        }


@frappe.whitelist()
def approve_inspection(checklist_id, approval_notes=""):
    """Approve completed inspection checklist"""
    try:
        qc_workflow = QualityControlWorkflow()
        return qc_workflow.approve_inspection(checklist_id, approval_notes)
    except Exception as e:
        frappe.log_error(f"API approve inspection error: {str(e)}")
        return {"status": "error", "message": _("Failed to approve inspection: {0}").format(str(e))}


@frappe.whitelist()
def get_inspection_dashboard(service_order=None, checklist_id=None):
    """Get inspection dashboard data"""
    try:
        qc_workflow = QualityControlWorkflow(service_order)
        return qc_workflow.get_inspection_dashboard(checklist_id)
    except Exception as e:
        frappe.log_error(f"API inspection dashboard error: {str(e)}")
        return {
            "status": "error",
            "message": _("Failed to load inspection dashboard: {0}").format(str(e)),
        }


@frappe.whitelist()
def generate_inspection_report(checklist_id):
    """Generate comprehensive inspection report"""
    try:
        qc_workflow = QualityControlWorkflow()
        return qc_workflow.generate_inspection_report(checklist_id)
    except Exception as e:
        frappe.log_error(f"API inspection report error: {str(e)}")
        return {
            "status": "error",
            "message": _("Failed to generate inspection report: {0}").format(str(e)),
        }


@frappe.whitelist()
def get_checklist_templates():
    """Get available checklist templates"""
    try:
        qc_workflow = QualityControlWorkflow()

        templates = {
            "checklist_types": [
                {"value": "basic", "label": "Basic Inspection", "label_ar": "فحص أساسي"},
                {
                    "value": "comprehensive",
                    "label": "Comprehensive Inspection",
                    "label_ar": "فحص شامل",
                },
                {
                    "value": "safety_only",
                    "label": "Safety Check Only",
                    "label_ar": "فحص السلامة فقط",
                },
            ],
            "vehicle_types": [
                {"value": "passenger", "label": "Passenger Car", "label_ar": "سيارة ركاب"},
                {"value": "commercial", "label": "Commercial Vehicle", "label_ar": "مركبة تجارية"},
                {"value": "motorcycle", "label": "Motorcycle", "label_ar": "دراجة نارية"},
            ],
            "sample_items": qc_workflow._get_checklist_template("comprehensive", "passenger")[:5],
        }

        return {"status": "success", "templates": templates}
    except Exception as e:
        return {
            "status": "error",
            "message": _("Failed to get checklist templates: {0}").format(str(e)),
        }
