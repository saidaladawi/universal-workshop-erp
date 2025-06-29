# Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, get_datetime
from frappe.core.doctype.communication.email import make


@frappe.whitelist()
def send_rfq_to_suppliers(comparison_name, suppliers, message, message_ar=None):
    """Send Request for Quotation to multiple suppliers"""

    if not comparison_name or not suppliers:
        frappe.throw(_("Comparison name and suppliers are required"))

    # Get comparison document
    comparison = frappe.get_doc("Supplier Comparison", comparison_name)

    # Convert suppliers to list if string
    if isinstance(suppliers, str):
        suppliers = suppliers.split(",")

    sent_count = 0
    failed_suppliers = []

    for supplier_id in suppliers:
        supplier_id = supplier_id.strip()

        try:
            # Get supplier details
            supplier = frappe.get_doc("Supplier", supplier_id)

            if not supplier.email_id:
                failed_suppliers.append(f"{supplier.supplier_name} (No email)")
                continue

            # Create email content
            subject = f"Request for Quotation - {comparison.title}"
            if frappe.boot.lang == "ar" and comparison.title_ar:
                subject = f"طلب عرض أسعار - {comparison.title_ar}"

            email_content = create_rfq_email_content(comparison, supplier, message, message_ar)

            # Send email
            make_email(
                {
                    "recipients": [supplier.email_id],
                    "subject": subject,
                    "content": email_content,
                    "send_email": True,
                    "doctype": "Supplier Comparison",
                    "name": comparison_name,
                }
            )

            # Create communication record
            comm = frappe.get_doc(
                {
                    "doctype": "Communication",
                    "communication_type": "Communication",
                    "communication_medium": "Email",
                    "sent_or_received": "Sent",
                    "subject": subject,
                    "content": email_content,
                    "status": "Linked",
                    "reference_doctype": "Supplier Comparison",
                    "reference_name": comparison_name,
                    "timeline_label": "Email",
                }
            )
            comm.insert()

            sent_count += 1

        except Exception as e:
            frappe.log_error(f"Failed to send RFQ to {supplier_id}: {str(e)}")
            failed_suppliers.append(f"{supplier_id} (Error: {str(e)})")

    # Return results
    result = {
        "sent_count": sent_count,
        "failed_suppliers": failed_suppliers,
        "success": sent_count > 0,
    }

    if failed_suppliers:
        frappe.msgprint(
            _("RFQ sent to {0} suppliers. Failed: {1}").format(
                sent_count, ", ".join(failed_suppliers)
            )
        )

    return result


def create_rfq_email_content(comparison, supplier, message, message_ar=None):
    """Create RFQ email content with Arabic support"""

    # Determine language
    is_arabic = frappe.boot.lang == "ar"

    # Email header
    if is_arabic and message_ar:
        content = f"""
        <div dir="rtl" style="font-family: 'Tahoma', Arial, sans-serif;">
            <h3>طلب عرض أسعار</h3>
            <p>السيد/السيدة {supplier.supplier_name} المحترم/ة،</p>
            <p>{message_ar}</p>
        """
    else:
        content = f"""
        <div style="font-family: Arial, sans-serif;">
            <h3>Request for Quotation</h3>
            <p>Dear {supplier.supplier_name},</p>
            <p>{message}</p>
        """

    # Items table
    if is_arabic:
        content += """
            <h4>العناصر المطلوبة:</h4>
            <table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 100%;">
                <thead style="background-color: #f8f9fa;">
                    <tr>
                        <th>كود العنصر</th>
                        <th>اسم العنصر</th>
                        <th>الوصف</th>
                        <th>الكمية</th>
                        <th>الوحدة</th>
                    </tr>
                </thead>
                <tbody>
        """
    else:
        content += """
            <h4>Required Items:</h4>
            <table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 100%;">
                <thead style="background-color: #f8f9fa;">
                    <tr>
                        <th>Item Code</th>
                        <th>Item Name</th>
                        <th>Description</th>
                        <th>Quantity</th>
                        <th>UOM</th>
                    </tr>
                </thead>
                <tbody>
        """

    # Add items
    for item in comparison.comparison_items:
        content += f"""
            <tr>
                <td>{item.item_code}</td>
                <td>{item.item_name or ''}</td>
                <td>{item.description or ''}</td>
                <td>{item.qty}</td>
                <td>{item.uom or ''}</td>
            </tr>
        """

    content += "</tbody></table>"

    # Email footer
    if is_arabic:
        content += f"""
            <br>
            <p><strong>المطلوب بحلول:</strong> {comparison.required_by or 'غير محدد'}</p>
            <p><strong>أولوية:</strong> {comparison.priority or 'عادية'}</p>
            <br>
            <p>يرجى إرسال عرض الأسعار في أقرب وقت ممكن.</p>
            <p>شكراً لكم،<br>
            فريق إدارة المشتريات</p>
        </div>
        """
    else:
        content += f"""
            <br>
            <p><strong>Required By:</strong> {comparison.required_by or 'Not specified'}</p>
            <p><strong>Priority:</strong> {comparison.priority or 'Normal'}</p>
            <br>
            <p>Please send your quotation at your earliest convenience.</p>
            <p>Thank you,<br>
            Purchasing Management Team</p>
        </div>
        """

    return content


@frappe.whitelist()
def get_supplier_performance_data(supplier, date_range=None):
    """Get supplier performance data for analytics"""

    if not supplier:
        return {}

    # Default date range (last 12 months)
    if not date_range:
        from datetime import datetime, timedelta

        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=365)
    else:
        start_date, end_date = date_range

    # Get purchase orders
    pos = frappe.get_all(
        "Purchase Order",
        filters={
            "supplier": supplier,
            "transaction_date": ["between", [start_date, end_date]],
            "docstatus": 1,
        },
        fields=["name", "transaction_date", "grand_total", "status"],
    )

    # Get purchase receipts
    prs = frappe.get_all(
        "Purchase Receipt",
        filters={
            "supplier": supplier,
            "posting_date": ["between", [start_date, end_date]],
            "docstatus": 1,
        },
        fields=["name", "posting_date", "grand_total"],
    )

    # Calculate metrics
    total_orders = len(pos)
    total_value = sum([po.grand_total for po in pos])
    completed_orders = len([po for po in pos if po.status == "Completed"])
    on_time_delivery_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0

    # Get quality inspection data
    qi_data = frappe.get_all(
        "Quality Inspection",
        filters={
            "reference_type": "Purchase Receipt",
            "inspection_date": ["between", [start_date, end_date]],
        },
        fields=["status"],
    )

    quality_score = 0
    if qi_data:
        passed_inspections = len([qi for qi in qi_data if qi.status == "Accepted"])
        quality_score = passed_inspections / len(qi_data) * 100

    return {
        "total_orders": total_orders,
        "total_value": total_value,
        "on_time_delivery_rate": on_time_delivery_rate,
        "quality_score": quality_score,
        "completed_orders": completed_orders,
        "total_receipts": len(prs),
    }


@frappe.whitelist()
def create_supplier_scorecard(supplier, performance_period=None):
    """Create or update supplier scorecard"""

    # Get performance data
    performance_data = get_supplier_performance_data(supplier, performance_period)

    # Calculate overall score
    delivery_weight = 0.4
    quality_weight = 0.3
    price_weight = 0.3

    delivery_score = performance_data.get("on_time_delivery_rate", 0)
    quality_score = performance_data.get("quality_score", 0)

    # Simple price score (can be enhanced)
    price_score = 75  # Default score, can be calculated based on price competitiveness

    overall_score = (
        delivery_score * delivery_weight
        + quality_score * quality_weight
        + price_score * price_weight
    )

    # Create scorecard data
    scorecard = {
        "supplier": supplier,
        "performance_period": performance_period or "Last 12 Months",
        "delivery_score": delivery_score,
        "quality_score": quality_score,
        "price_score": price_score,
        "overall_score": overall_score,
        "total_orders": performance_data.get("total_orders", 0),
        "total_value": performance_data.get("total_value", 0),
        "grade": get_supplier_grade(overall_score),
    }

    return scorecard


def get_supplier_grade(score):
    """Get supplier grade based on score"""
    if score >= 90:
        return "A+"
    elif score >= 80:
        return "A"
    elif score >= 70:
        return "B"
    elif score >= 60:
        return "C"
    else:
        return "D"


@frappe.whitelist()
def get_procurement_dashboard_data():
    """Get data for procurement dashboard"""

    # Current month stats
    from datetime import datetime, timedelta

    today = datetime.now().date()
    month_start = today.replace(day=1)

    # Purchase orders this month
    po_data = frappe.db.sql(
        """
        SELECT COUNT(*) as count, SUM(grand_total) as total
        FROM `tabPurchase Order`
        WHERE transaction_date >= %s AND docstatus = 1
    """,
        [month_start],
        as_dict=True,
    )[0]

    # Material requests pending
    pending_mr = frappe.db.count("Material Request", {"status": "Pending"})

    # Overdue purchase orders
    overdue_po = frappe.db.sql(
        """
        SELECT COUNT(*) as count
        FROM `tabPurchase Order`
        WHERE schedule_date < %s AND status != 'Completed' AND docstatus = 1
    """,
        [today],
        as_dict=True,
    )[0].count

    # Top suppliers by value
    top_suppliers = frappe.db.sql(
        """
        SELECT supplier, SUM(grand_total) as total_value, COUNT(*) as order_count
        FROM `tabPurchase Order`
        WHERE transaction_date >= %s AND docstatus = 1
        GROUP BY supplier
        ORDER BY total_value DESC
        LIMIT 5
    """,
        [month_start],
        as_dict=True,
    )

    return {
        "purchase_orders": {"count": po_data.count or 0, "value": po_data.total or 0},
        "pending_requests": pending_mr,
        "overdue_orders": overdue_po,
        "top_suppliers": top_suppliers,
    }


# Mobile-specific API methods


@frappe.whitelist()
def find_item_by_barcode(barcode):
    """Find item by barcode for mobile scanning"""
    try:
        # First try to find by item code
        item = frappe.get_doc("Item", barcode)
        return {
            "item_code": item.name,
            "item_name": item.item_name,
            "stock_uom": item.stock_uom,
            "default_warehouse": item.default_warehouse,
        }
    except frappe.DoesNotExistError:
        # Try to find by barcode in Item Barcode table
        barcode_item = frappe.db.get_value("Item Barcode", {"barcode": barcode}, "parent")
        if barcode_item:
            item = frappe.get_doc("Item", barcode_item)
            return {
                "item_code": item.name,
                "item_name": item.item_name,
                "stock_uom": item.stock_uom,
                "default_warehouse": item.default_warehouse,
            }

        return None


@frappe.whitelist()
def create_mobile_document(doctype, data):
    """Create document from mobile interface"""
    try:
        # Create new document
        doc = frappe.new_doc(doctype)

        # Set basic fields
        for key, value in data.items():
            if key != "items" and hasattr(doc, key):
                setattr(doc, key, value)

        # Handle items for Purchase Receipt
        if doctype == "Purchase Receipt" and "items" in data:
            for item_data in data["items"]:
                item_row = doc.append("items", {})
                item_row.item_code = item_data.get("item_code")
                item_row.qty = item_data.get("received_qty", 1)
                item_row.received_qty = item_data.get("received_qty", 1)
                item_row.uom = item_data.get("uom")
                item_row.warehouse = item_data.get("warehouse")

        # Set naming series if available
        if hasattr(doc, "naming_series"):
            if doctype == "Purchase Receipt":
                doc.naming_series = "MAT-PRE-.YYYY.-"
            elif doctype == "Quality Inspection":
                doc.naming_series = "MAT-QA-.YYYY.-"

        # Set company
        if hasattr(doc, "company") and not doc.company:
            doc.company = frappe.defaults.get_user_default("Company")

        # Insert document
        doc.insert()

        return {"success": True, "name": doc.name, "doctype": doctype}

    except Exception as e:
        frappe.log_error(f"Mobile document creation failed: {str(e)}")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_reference_items(doctype, name):
    """Get items from reference document for Quality Inspection"""
    try:
        doc = frappe.get_doc(doctype, name)
        items = []

        # Get items from the document
        if hasattr(doc, "items"):
            for item in doc.items:
                items.append(
                    {
                        "item_code": item.item_code,
                        "item_name": getattr(item, "item_name", ""),
                        "qty": getattr(item, "qty", 1),
                    }
                )

        return items

    except Exception as e:
        frappe.log_error(f"Failed to get reference items: {str(e)}")
        return []


@frappe.whitelist()
def get_pending_receipts():
    """Get pending Purchase Receipts for mobile interface"""
    try:
        receipts = frappe.get_all(
            "Purchase Receipt",
            filters={"docstatus": 0},
            fields=["name", "supplier", "posting_date", "status"],
            order_by="creation desc",
            limit=20,
        )

        return receipts

    except Exception as e:
        frappe.log_error(f"Failed to get pending receipts: {str(e)}")
        return []


@frappe.whitelist()
def get_mobile_dashboard_data():
    """Get dashboard data optimized for mobile interface"""
    try:
        from datetime import datetime, timedelta

        today = datetime.now().date()
        week_ago = today - timedelta(days=7)

        # Recent receipts
        recent_receipts = frappe.get_all(
            "Purchase Receipt",
            filters={"posting_date": [">=", week_ago], "docstatus": 1},
            fields=["name", "supplier", "posting_date"],
            limit=5,
        )

        # Pending quality inspections
        pending_qi = frappe.get_all(
            "Quality Inspection",
            filters={"docstatus": 0},
            fields=["name", "item_code", "inspection_date"],
            limit=5,
        )

        # Items needing inspection
        items_needing_inspection = frappe.db.sql(
            """
            SELECT pr.name, pr.supplier, pri.item_code, pri.received_qty
            FROM `tabPurchase Receipt` pr
            JOIN `tabPurchase Receipt Item` pri ON pr.name = pri.parent
            LEFT JOIN `tabQuality Inspection` qi ON pr.name = qi.reference_name
            WHERE pr.docstatus = 1 
                AND qi.name IS NULL 
                AND pr.posting_date >= %s
            LIMIT 10
        """,
            [week_ago],
            as_dict=True,
        )

        return {
            "recent_receipts": recent_receipts,
            "pending_inspections": pending_qi,
            "items_needing_inspection": items_needing_inspection,
            "summary": {
                "recent_receipts_count": len(recent_receipts),
                "pending_inspections_count": len(pending_qi),
                "items_needing_inspection_count": len(items_needing_inspection),
            },
        }

    except Exception as e:
        frappe.log_error(f"Failed to get mobile dashboard data: {str(e)}")
        return {
            "recent_receipts": [],
            "pending_inspections": [],
            "items_needing_inspection": [],
            "summary": {
                "recent_receipts_count": 0,
                "pending_inspections_count": 0,
                "items_needing_inspection_count": 0,
            },
        }


# Quality Inspection Integration Functions


@frappe.whitelist()
def create_quality_inspection(
    purchase_receipt, item_code, supplier, quality_inspection_template=None
):
    """Create quality inspection from purchase receipt"""

    # Get purchase receipt details
    pr = frappe.get_doc("Purchase Receipt", purchase_receipt)
    pr_item = None

    for item in pr.items:
        if item.item_code == item_code:
            pr_item = item
            break

    if not pr_item:
        frappe.throw(
            _("Item {0} not found in Purchase Receipt {1}").format(item_code, purchase_receipt)
        )

    # Create quality inspection
    qi = frappe.new_doc("Quality Inspection")
    qi.purchase_receipt = purchase_receipt
    qi.purchase_receipt_item = pr_item.name
    qi.item_code = item_code
    qi.supplier = supplier
    qi.batch_no = pr_item.batch_no if hasattr(pr_item, "batch_no") else None
    qi.sample_size = pr_item.qty
    qi.inspection_date = frappe.utils.today()
    qi.inspection_time = frappe.utils.now_datetime().strftime("%H:%M:%S")
    qi.inspected_by = frappe.session.user

    # Set quality inspection template if provided
    if quality_inspection_template:
        qi.quality_inspection_template = quality_inspection_template

        # Load template criteria (simplified for now)
        qi.append(
            "inspection_criteria",
            {
                "parameter_name": "General Quality",
                "parameter_name_ar": "الجودة العامة",
                "inspection_type": "Manual",
                "min_value": 70,
                "max_value": 100,
                "target_value": 95,
            },
        )

    qi.insert()
    return qi.name


@frappe.whitelist()
def submit_quality_inspection(quality_inspection_name, inspection_results):
    """Submit quality inspection with results"""
    import json

    qi = frappe.get_doc("Quality Inspection", quality_inspection_name)

    if isinstance(inspection_results, str):
        inspection_results = json.loads(inspection_results)

    # Update inspection criteria with results
    for result in inspection_results:
        for criteria in qi.inspection_criteria:
            if criteria.parameter_name == result.get("parameter_name"):
                criteria.actual_value = result.get("actual_value")
                criteria.result = result.get("result")
                criteria.remarks = result.get("remarks", "")
                criteria.remarks_ar = result.get("remarks_ar", "")
                break

    # Calculate quality metrics
    total_criteria = len(qi.inspection_criteria)
    passed_criteria = sum(1 for c in qi.inspection_criteria if c.result == "Pass")

    qi.pass_percentage = (passed_criteria / total_criteria) * 100 if total_criteria > 0 else 0
    qi.quality_score = qi.pass_percentage  # Simplified calculation
    qi.defects_found = sum(1 for c in qi.inspection_criteria if c.result == "Fail")

    # Determine overall result
    if qi.pass_percentage >= 95:
        qi.overall_result = "Pass"
        qi.inspection_status = "Completed"
        qi.corrective_action_required = 0
    elif qi.pass_percentage >= 70:
        qi.overall_result = "Partial Pass"
        qi.inspection_status = "Completed"
        qi.corrective_action_required = 1
    else:
        qi.overall_result = "Fail"
        qi.inspection_status = "Rejected"
        qi.corrective_action_required = 1

    qi.save()
    qi.submit()

    # Update supplier scorecard
    update_supplier_scorecard_from_inspection(qi.name)

    return qi.name


@frappe.whitelist()
def update_supplier_scorecard_from_inspection(quality_inspection_name):
    """Update supplier scorecard when quality inspection is completed"""
    qi = frappe.get_doc("Quality Inspection", quality_inspection_name)

    if not qi.supplier:
        return

    # Get or create scorecard for current year
    year = frappe.utils.getdate().year
    scorecard_name = f"{qi.supplier}-{year}"

    if frappe.db.exists("Supplier Scorecard", scorecard_name):
        scorecard = frappe.get_doc("Supplier Scorecard", scorecard_name)
    else:
        # Create new scorecard
        scorecard = frappe.new_doc("Supplier Scorecard")
        scorecard.supplier = qi.supplier
        scorecard.year = year
        scorecard.evaluation_period = "Quarterly"
        scorecard.performance_rating = "Satisfactory"
        scorecard.risk_level = "Medium"
        scorecard.insert()

    # Update quality metrics
    scorecard.total_inspections += 1
    scorecard.total_quality_score += qi.quality_score

    if qi.overall_result == "Pass":
        scorecard.passed_inspections += 1
    else:
        scorecard.failed_inspections += 1

    # Recalculate averages
    scorecard.average_quality_score = scorecard.total_quality_score / scorecard.total_inspections
    scorecard.pass_rate = (scorecard.passed_inspections / scorecard.total_inspections) * 100

    # Update performance rating based on pass rate
    if scorecard.pass_rate >= 95 and scorecard.average_quality_score >= 90:
        scorecard.performance_rating = "Excellent"
        scorecard.risk_level = "Low"
    elif scorecard.pass_rate >= 85 and scorecard.average_quality_score >= 80:
        scorecard.performance_rating = "Good"
        scorecard.risk_level = "Low"
    elif scorecard.pass_rate >= 70 and scorecard.average_quality_score >= 70:
        scorecard.performance_rating = "Satisfactory"
        scorecard.risk_level = "Medium"
    else:
        scorecard.performance_rating = "Needs Improvement"
        scorecard.risk_level = "High"

    # Calculate overall score
    scorecard.calculate_overall_score()
    scorecard.save()

    return scorecard.name


@frappe.whitelist()
def get_quality_inspection_analytics(supplier=None, date_from=None, date_to=None):
    """Get quality inspection analytics with filtering"""

    filters = {}
    if supplier:
        filters["supplier"] = supplier
    if date_from:
        filters["inspection_date"] = [">=", date_from]
    if date_to:
        if "inspection_date" in filters:
            filters["inspection_date"] = ["between", [date_from, date_to]]
        else:
            filters["inspection_date"] = ["<=", date_to]

    # Get quality inspections
    inspections = frappe.get_list(
        "Quality Inspection",
        filters=filters,
        fields=[
            "name",
            "supplier",
            "item_code",
            "inspection_date",
            "overall_result",
            "quality_score",
            "pass_percentage",
            "defects_found",
            "corrective_action_required",
        ],
    )

    # Calculate summary statistics
    total_inspections = len(inspections)
    passed_inspections = sum(1 for i in inspections if i.overall_result == "Pass")
    avg_quality_score = (
        sum(i.quality_score or 0 for i in inspections) / total_inspections
        if total_inspections > 0
        else 0
    )

    # Result distribution
    result_distribution = {}
    for inspection in inspections:
        result = inspection.overall_result
        result_distribution[result] = result_distribution.get(result, 0) + 1

    # Top defect items
    defect_items = {}
    for inspection in inspections:
        if inspection.defects_found and inspection.defects_found > 0:
            item = inspection.item_code
            defect_items[item] = defect_items.get(item, 0) + inspection.defects_found

    return {
        "summary": {
            "total_inspections": total_inspections,
            "passed_inspections": passed_inspections,
            "pass_rate": (
                (passed_inspections / total_inspections) * 100 if total_inspections > 0 else 0
            ),
            "average_quality_score": round(avg_quality_score, 2),
            "result_distribution": result_distribution,
        },
        "defect_analysis": {
            "top_defect_items": sorted(defect_items.items(), key=lambda x: x[1], reverse=True)[:10]
        },
        "inspections": inspections,
    }
