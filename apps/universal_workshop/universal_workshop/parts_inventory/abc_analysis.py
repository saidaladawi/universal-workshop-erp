# -*- coding: utf-8 -*-
"""
Universal Workshop ERP - ABC Analysis for Inventory Optimization
Advanced ABC analysis system with comprehensive reporting and optimization recommendations
Arabic/English localization support for Omani automotive workshops
"""

import frappe
from frappe import _
import json
from datetime import datetime, timedelta
from frappe.utils import now, get_datetime, cint, flt, add_days, getdate
from typing import Dict, List, Optional, Any


@frappe.whitelist()
def perform_abc_analysis(
    warehouse=None,
    from_date=None,
    to_date=None,
    analysis_type="value",
    threshold_a=80,
    threshold_b=95,
):
    """
    Comprehensive ABC analysis with multiple classification methods

    Args:
        warehouse: Optional warehouse filter
        from_date: Analysis start date (default: 1 year ago)
        to_date: Analysis end date (default: today)
        analysis_type: 'value' (annual value), 'volume' (movement), 'frequency' (transaction count)
        threshold_a: Percentage threshold for Category A (default: 80%)
        threshold_b: Percentage threshold for Category B (default: 95%)
    """
    try:
        # Set default dates
        if not to_date:
            to_date = getdate()
        if not from_date:
            from_date = add_days(to_date, -365)

        # Validate thresholds
        threshold_a = flt(threshold_a, 1)
        threshold_b = flt(threshold_b, 1)

        if threshold_a >= threshold_b or threshold_a <= 0 or threshold_b > 100:
            return {
                "success": False,
                "error": "Invalid thresholds",
                "message": _("Threshold A must be less than Threshold B and within valid range"),
            }

        # Build comprehensive analysis query
        query = """
            SELECT 
                sle.item_code,
                i.item_name,
                i.item_name_ar,
                i.item_group,
                i.brand,
                i.standard_rate,
                i.stock_uom,
                COALESCE(bin.actual_qty, 0) as current_stock,
                COALESCE(bin.valuation_rate, i.standard_rate) as current_rate,
                ABS(SUM(sle.actual_qty)) as total_movement,
                SUM(ABS(sle.actual_qty) * sle.valuation_rate) as annual_value,
                COUNT(sle.name) as transaction_count,
                AVG(sle.valuation_rate) as avg_rate,
                MAX(sle.posting_date) as last_movement_date,
                MIN(sle.posting_date) as first_movement_date,
                DATEDIFF(%s, %s) as analysis_days
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            LEFT JOIN `tabBin` bin ON sle.item_code = bin.item_code {warehouse_join}
            WHERE sle.posting_date BETWEEN %s AND %s
                AND sle.is_cancelled = 0
                AND i.disabled = 0
                {warehouse_condition}
            GROUP BY sle.item_code
            HAVING total_movement > 0
        """.format(
            warehouse_join="AND sle.warehouse = bin.warehouse" if warehouse else "",
            warehouse_condition="AND sle.warehouse = %s" if warehouse else "",
        )

        params = [to_date, from_date, from_date, to_date]
        if warehouse:
            params.append(warehouse)

        items = frappe.db.sql(query, params, as_dict=True)

        if not items:
            return {
                "success": True,
                "items": [],
                "summary": {"A": 0, "B": 0, "C": 0},
                "analysis_config": {
                    "type": analysis_type,
                    "threshold_a": threshold_a,
                    "threshold_b": threshold_b,
                },
                "message": _("No inventory movement data found for the specified period"),
            }

        # Process and classify items
        items = classify_items_abc(items, analysis_type, threshold_a, threshold_b)

        # Generate summary and recommendations
        summary = calculate_abc_summary(items, analysis_type)
        recommendations = generate_optimization_recommendations(items, analysis_type)

        return {
            "success": True,
            "items": items,
            "summary": summary,
            "recommendations": recommendations,
            "analysis_config": {
                "type": analysis_type,
                "threshold_a": threshold_a,
                "threshold_b": threshold_b,
                "warehouse": warehouse,
                "from_date": from_date,
                "to_date": to_date,
                "total_items": len(items),
            },
        }

    except Exception as e:
        frappe.log_error(f"ABC Analysis error: {str(e)}", "ABC Analysis")
        return {"success": False, "error": str(e), "message": _("Failed to perform ABC analysis")}


def classify_items_abc(
    items: List[Dict], analysis_type: str, threshold_a: float, threshold_b: float
) -> List[Dict]:
    """Classify items into ABC categories based on analysis type"""

    # Calculate sorting criteria
    for item in items:
        if analysis_type == "value":
            item.sort_value = item.annual_value
            item.analysis_metric = "Annual Value (OMR)"
        elif analysis_type == "volume":
            item.sort_value = item.total_movement
            item.analysis_metric = "Total Movement (Units)"
        elif analysis_type == "frequency":
            item.sort_value = item.transaction_count
            item.analysis_metric = "Transaction Count"
        else:
            item.sort_value = item.annual_value
            item.analysis_metric = "Annual Value (OMR)"

    # Sort by criteria (descending)
    items.sort(key=lambda x: x.sort_value, reverse=True)

    # Calculate cumulative percentages and assign categories
    total_sort_value = sum(item.sort_value for item in items)
    cumulative_value = 0

    for item in items:
        cumulative_value += item.sort_value
        item.cumulative_percentage = (cumulative_value / total_sort_value) * 100
        item.item_percentage = (item.sort_value / total_sort_value) * 100

        # Assign ABC category with management recommendations
        if item.cumulative_percentage <= threshold_a:
            item.abc_category = "A"
            item.management_strategy = _("High Control - Tight inventory management")
            item.review_frequency = _("Weekly")
            item.count_frequency = _("Monthly")
            item.order_strategy = _("JIT (Just-in-Time)")
            item.safety_stock_days = 7
        elif item.cumulative_percentage <= threshold_b:
            item.abc_category = "B"
            item.management_strategy = _("Moderate Control - Periodic review")
            item.review_frequency = _("Monthly")
            item.count_frequency = _("Quarterly")
            item.order_strategy = _("Periodic Review")
            item.safety_stock_days = 14
        else:
            item.abc_category = "C"
            item.management_strategy = _("Basic Control - Simple reorder system")
            item.review_frequency = _("Quarterly")
            item.count_frequency = _("Semi-Annual")
            item.order_strategy = _("Bulk Orders")
            item.safety_stock_days = 30

        # Calculate advanced metrics
        days_in_period = item.analysis_days or 365
        item.monthly_movement = (item.total_movement / days_in_period) * 30
        item.monthly_value = (item.annual_value / days_in_period) * 30
        item.transaction_frequency = item.transaction_count / days_in_period * 30

        # Inventory turnover calculations
        if item.current_stock and item.current_stock > 0:
            item.annual_turnover = item.total_movement / item.current_stock
            item.days_of_stock = (
                days_in_period / item.annual_turnover if item.annual_turnover > 0 else 999
            )
            item.stock_value = item.current_stock * item.current_rate
        else:
            item.annual_turnover = 0
            item.days_of_stock = 0
            item.stock_value = 0

        # Format numerical values
        item.annual_value = flt(item.annual_value, 2)
        item.monthly_value = flt(item.monthly_value, 2)
        item.avg_rate = flt(item.avg_rate, 2)
        item.current_rate = flt(item.current_rate, 2)
        item.stock_value = flt(item.stock_value, 2)
        item.monthly_movement = flt(item.monthly_movement, 2)
        item.transaction_frequency = flt(item.transaction_frequency, 2)
        item.cumulative_percentage = flt(item.cumulative_percentage, 2)
        item.item_percentage = flt(item.item_percentage, 4)
        item.annual_turnover = flt(item.annual_turnover, 2)
        item.days_of_stock = flt(item.days_of_stock, 1)

    return items


@frappe.whitelist()
def save_abc_classification(items_data, analysis_config):
    """Save ABC classification to Item master for automation"""
    try:
        if isinstance(items_data, str):
            items_data = json.loads(items_data)
        if isinstance(analysis_config, str):
            analysis_config = json.loads(analysis_config)

        updated_count = 0

        for item_data in items_data:
            item_code = item_data.get("item_code")
            abc_category = item_data.get("abc_category")

            if item_code and abc_category:
                # Update Item with ABC classification
                frappe.db.set_value(
                    "Item",
                    item_code,
                    {
                        "custom_abc_category": abc_category,
                        "custom_abc_analysis_date": getdate(),
                        "custom_abc_analysis_type": analysis_config.get("type", "value"),
                        "custom_management_strategy": item_data.get("management_strategy"),
                        "custom_review_frequency": item_data.get("review_frequency"),
                        "custom_safety_stock_days": item_data.get("safety_stock_days", 14),
                        "custom_annual_turnover": item_data.get("annual_turnover", 0),
                    },
                )

                updated_count += 1

        return {
            "success": True,
            "updated_count": updated_count,
            "message": _("ABC classification saved for {0} items").format(updated_count),
        }

    except Exception as e:
        frappe.log_error(f"Save ABC classification error: {str(e)}", "ABC Analysis")
        return {
            "success": False,
            "error": str(e),
            "message": _("Failed to save ABC classification"),
        }


def calculate_abc_summary(items: List[Dict], analysis_type: str) -> Dict:
    """Calculate comprehensive summary statistics"""

    category_stats = {"A": [], "B": [], "C": []}
    for item in items:
        category_stats[item.abc_category].append(item)

    total_value = sum(item.sort_value for item in items)
    total_stock_value = sum(getattr(item, "stock_value", 0) for item in items)

    summary = {
        "total_items": len(items),
        "total_value": flt(total_value, 2),
        "total_stock_value": flt(total_stock_value, 2),
        "analysis_type": analysis_type,
    }

    for category in ["A", "B", "C"]:
        cat_items = category_stats[category]
        cat_count = len(cat_items)
        cat_value = sum(item.sort_value for item in cat_items)

        summary[category] = {
            "count": cat_count,
            "percentage": flt((cat_count / len(items)) * 100, 1) if items else 0,
            "value": flt(cat_value, 2),
            "value_percentage": flt((cat_value / total_value) * 100, 1) if total_value > 0 else 0,
        }

    return summary


def generate_optimization_recommendations(items: List[Dict], analysis_type: str) -> List[Dict]:
    """Generate actionable inventory optimization recommendations"""

    recommendations = []

    # Category A optimization
    category_a = [item for item in items if item.abc_category == "A"]
    if category_a:
        excess_stock_a = [item for item in category_a if getattr(item, "days_of_stock", 0) > 45]
        if excess_stock_a:
            recommendations.append(
                {
                    "type": "reduce_stock",
                    "category": "A",
                    "priority": "high",
                    "title": _("Reduce Excess Category A Stock"),
                    "description": _(
                        "Found {0} high-value items with excess stock (>45 days)"
                    ).format(len(excess_stock_a)),
                    "action": _(
                        "Reduce safety stock levels and implement tighter reorder controls"
                    ),
                    "items_count": len(excess_stock_a),
                }
            )

    # Dead stock identification
    dead_stock = [item for item in items if getattr(item, "days_of_stock", 0) > 365]
    if dead_stock:
        recommendations.append(
            {
                "type": "liquidate",
                "category": "All",
                "priority": "high",
                "title": _("Liquidate Dead Stock"),
                "description": _("Found {0} items with >1 year of stock on hand").format(
                    len(dead_stock)
                ),
                "action": _("Consider liquidation, supplier return, or special promotions"),
                "items_count": len(dead_stock),
            }
        )

    return recommendations
