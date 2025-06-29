# universal_workshop/parts_inventory/inventory_alert_engine.py
"""
Comprehensive Inventory Alerts and Notifications System for Universal Workshop ERP
Real-time monitoring with configurable thresholds, Arabic localization, and dashboard integration
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import frappe
from frappe import _
from frappe.utils import flt, getdate, now_datetime, nowdate
from universal_workshop.utils.arabic_utils import ArabicTextUtils, format_arabic_date


class InventoryAlertEngine:
    """Core engine for inventory alerts and notifications with Arabic support"""

    # Alert severity levels with color coding
    ALERT_SEVERITIES = {
        "critical": {
            "threshold": 0.0,  # Out of stock
            "color": "#dc3545",  # Red
            "priority": 1,
            "label_en": "Critical",
            "label_ar": "حرج",
            "auto_escalate": True,
            "escalate_hours": 2,
        },
        "high": {
            "threshold": 0.1,  # Below 10% of reorder level
            "color": "#fd7e14",  # Orange
            "priority": 2,
            "label_en": "High",
            "label_ar": "عالي",
            "auto_escalate": True,
            "escalate_hours": 24,
        },
        "medium": {
            "threshold": 0.5,  # Below 50% of reorder level
            "color": "#ffc107",  # Yellow
            "priority": 3,
            "label_en": "Medium",
            "label_ar": "متوسط",
            "auto_escalate": False,
            "escalate_hours": 48,
        },
        "low": {
            "threshold": 1.0,  # At reorder level
            "color": "#17a2b8",  # Blue
            "priority": 4,
            "label_en": "Low",
            "label_ar": "منخفض",
            "auto_escalate": False,
            "escalate_hours": None,
        },
    }

    # Alert types configuration
    ALERT_TYPES = {
        "stock_low": {
            "name_en": "Low Stock Alert",
            "name_ar": "تنبيه نفاد المخزون",
            "description_en": "Item stock level below minimum threshold",
            "description_ar": "مستوى المخزون أقل من الحد الأدنى",
            "enabled": True,
            "check_interval": 300,  # 5 minutes
        },
        "stock_critical": {
            "name_en": "Critical Stock Alert",
            "name_ar": "تنبيه مخزون حرج",
            "description_en": "Item completely out of stock",
            "description_ar": "نفاد المخزون بالكامل",
            "enabled": True,
            "check_interval": 60,  # 1 minute
        },
        "item_expiring": {
            "name_en": "Item Expiring Soon",
            "name_ar": "انتهاء صلاحية الصنف قريباً",
            "description_en": "Items approaching expiration date",
            "description_ar": "أصناف تقترب من تاريخ انتهاء الصلاحية",
            "enabled": True,
            "check_interval": 3600,  # 1 hour
        },
        "item_expired": {
            "name_en": "Expired Items",
            "name_ar": "أصناف منتهية الصلاحية",
            "description_en": "Items past expiration date",
            "description_ar": "أصناف تجاوزت تاريخ انتهاء الصلاحية",
            "enabled": True,
            "check_interval": 3600,  # 1 hour
        },
        "reorder_point": {
            "name_en": "Reorder Point Reached",
            "name_ar": "وصول نقطة إعادة الطلب",
            "description_en": "Item reached reorder point threshold",
            "description_ar": "وصل الصنف إلى نقطة إعادة الطلب",
            "enabled": True,
            "check_interval": 900,  # 15 minutes
        },
        "slow_moving": {
            "name_en": "Slow Moving Items",
            "name_ar": "أصناف بطيئة الحركة",
            "description_en": "Items with low turnover rate",
            "description_ar": "أصناف ذات معدل دوران منخفض",
            "enabled": True,
            "check_interval": 86400,  # Daily
        },
    }

    @classmethod
    def initialize_alert_system(cls) -> Dict[str, Any]:
        """Initialize the inventory alert system with default configurations"""

        try:
            # Create default alert configuration
            alert_config = {
                "system_enabled": True,
                "default_language": "ar",
                "notification_channels": ["in_app", "email"],
                "alert_types": cls.ALERT_TYPES,
                "severity_levels": cls.ALERT_SEVERITIES,
                "escalation_enabled": True,
                "batch_notifications": True,
                "notification_frequency": "immediate",
                "created_on": now_datetime(),
                "created_by": frappe.session.user,
            }

            # Store configuration in cache
            frappe.cache().set_value("inventory_alert_config", alert_config, expires_in_sec=3600)

            return {
                "status": "success",
                "message": _("Inventory alert system initialized successfully"),
                "config": alert_config,
            }

        except Exception as e:
            frappe.log_error(f"Alert system initialization failed: {str(e)}")
            return {
                "status": "error",
                "message": _("Failed to initialize alert system"),
                "error": str(e),
            }

    @classmethod
    def get_alert_configuration(cls) -> Dict[str, Any]:
        """Get current alert system configuration"""

        config = frappe.cache().get_value("inventory_alert_config")
        if not config:
            config = cls.initialize_alert_system()["config"]

        return config

    @classmethod
    def update_alert_configuration(cls, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update alert system configuration"""

        try:
            current_config = cls.get_alert_configuration()
            current_config.update(updates)
            current_config["updated_on"] = now_datetime()
            current_config["updated_by"] = frappe.session.user

            # Store updated configuration
            frappe.cache().set_value("inventory_alert_config", current_config, expires_in_sec=3600)

            return {
                "status": "success",
                "message": _("Alert configuration updated successfully"),
                "config": current_config,
            }

        except Exception as e:
            frappe.log_error(f"Alert configuration update failed: {str(e)}")
            return {
                "status": "error",
                "message": _("Failed to update alert configuration"),
                "error": str(e),
            }

    @classmethod
    def scan_inventory_alerts(cls, alert_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Comprehensive inventory scan for all alert types"""

        config = cls.get_alert_configuration()
        if not config.get("system_enabled"):
            return {"status": "disabled", "alerts": []}

        if alert_types is None:
            alert_types = list(cls.ALERT_TYPES.keys())

        all_alerts = []
        scan_summary = {
            "total_items_scanned": 0,
            "total_alerts_found": 0,
            "alerts_by_severity": {},
            "alerts_by_type": {},
            "scan_duration": 0,
            "scan_timestamp": now_datetime(),
        }

        scan_start = datetime.now()

        try:
            for alert_type in alert_types:
                if alert_type in cls.ALERT_TYPES and config["alert_types"][alert_type]["enabled"]:
                    alerts = cls._scan_specific_alert_type(alert_type)
                    all_alerts.extend(alerts)

                    # Update summary statistics
                    scan_summary["alerts_by_type"][alert_type] = len(alerts)
                    for alert in alerts:
                        severity = alert["severity"]
                        scan_summary["alerts_by_severity"][severity] = (
                            scan_summary["alerts_by_severity"].get(severity, 0) + 1
                        )

            scan_summary["total_alerts_found"] = len(all_alerts)
            scan_summary["scan_duration"] = (datetime.now() - scan_start).total_seconds()

            # Sort alerts by priority (critical first)
            all_alerts.sort(key=lambda x: cls.ALERT_SEVERITIES[x["severity"]]["priority"])

            # Store alerts in cache for dashboard access
            frappe.cache().set_value(
                "current_inventory_alerts",
                {"alerts": all_alerts, "summary": scan_summary},
                expires_in_sec=300,
            )  # 5 minutes

            return {"status": "success", "alerts": all_alerts, "summary": scan_summary}

        except Exception as e:
            frappe.log_error(f"Inventory alert scan failed: {str(e)}")
            return {
                "status": "error",
                "message": _("Alert scan failed"),
                "error": str(e),
                "summary": scan_summary,
            }

    @classmethod
    def _scan_specific_alert_type(cls, alert_type: str) -> List[Dict[str, Any]]:
        """Scan for specific type of inventory alerts"""

        alerts = []

        if alert_type == "stock_low":
            alerts = cls._scan_low_stock_alerts()
        elif alert_type == "stock_critical":
            alerts = cls._scan_critical_stock_alerts()
        elif alert_type == "item_expiring":
            alerts = cls._scan_expiring_items()
        elif alert_type == "item_expired":
            alerts = cls._scan_expired_items()
        elif alert_type == "reorder_point":
            alerts = cls._scan_reorder_point_alerts()
        elif alert_type == "slow_moving":
            alerts = cls._scan_slow_moving_items()

        return alerts

    @classmethod
    def _scan_low_stock_alerts(cls) -> List[Dict[str, Any]]:
        """Scan for low stock level alerts"""

        alerts = []

        # Get all items with stock below reorder level
        query = """
            SELECT 
                i.item_code,
                i.item_name,
                i.min_stock_level,
                i.reorder_quantity,
                i.preferred_supplier,
                sle.warehouse,
                SUM(sle.actual_qty) as current_stock,
                i.standard_rate,
                i.part_category
            FROM `tabItem` i
            LEFT JOIN `tabStock Ledger Entry` sle ON i.item_code = sle.item_code
            WHERE i.disabled = 0 
            AND i.is_stock_item = 1
            AND i.min_stock_level > 0
            AND sle.is_cancelled = 0
            GROUP BY i.item_code, sle.warehouse
            HAVING SUM(sle.actual_qty) > 0 
            AND SUM(sle.actual_qty) <= i.min_stock_level
            ORDER BY (SUM(sle.actual_qty) / i.min_stock_level) ASC
        """

        results = frappe.db.sql(query, as_dict=True)

        for result in results:
            # Calculate severity based on stock percentage
            stock_percentage = (
                flt(result.current_stock) / flt(result.min_stock_level)
                if result.min_stock_level
                else 1
            )
            severity = cls._determine_stock_severity(stock_percentage)

            alert = {
                "id": f"stock_low_{result.item_code}_{result.warehouse}",
                "type": "stock_low",
                "severity": severity,
                "item_code": result.item_code,
                "item_name": result.item_name,
                "warehouse": result.warehouse,
                "current_stock": flt(result.current_stock),
                "min_stock_level": flt(result.min_stock_level),
                "reorder_quantity": flt(result.reorder_quantity),
                "preferred_supplier": result.preferred_supplier,
                "part_category": result.part_category,
                "estimated_value": flt(result.current_stock) * flt(result.standard_rate),
                "stock_percentage": stock_percentage * 100,
                "created_on": now_datetime(),
                "requires_action": True,
                "action_suggestions": cls._get_reorder_suggestions(result),
                "message_en": f"Low stock alert for {result.item_name} in {result.warehouse}",
                "message_ar": f"تنبيه نفاد مخزون {result.item_name} في {result.warehouse}",
            }

            alerts.append(alert)

        return alerts

    @classmethod
    def _scan_critical_stock_alerts(cls) -> List[Dict[str, Any]]:
        """Scan for critical stock level alerts (out of stock)"""

        alerts = []

        # Get all items that are out of stock
        query = """
            SELECT 
                i.item_code,
                i.item_name,
                i.min_stock_level,
                i.reorder_quantity,
                i.preferred_supplier,
                i.part_category,
                i.standard_rate,
                w.warehouse_name
            FROM `tabItem` i
            CROSS JOIN `tabWarehouse` w
            LEFT JOIN (
                SELECT 
                    item_code, 
                    warehouse, 
                    SUM(actual_qty) as stock_qty
                FROM `tabStock Ledger Entry` 
                WHERE is_cancelled = 0 
                GROUP BY item_code, warehouse
            ) sle ON i.item_code = sle.item_code AND w.name = sle.warehouse
            WHERE i.disabled = 0 
            AND i.is_stock_item = 1
            AND i.min_stock_level > 0
            AND w.is_group = 0
            AND (sle.stock_qty IS NULL OR sle.stock_qty <= 0)
            AND w.company = %s
            ORDER BY i.item_name
        """

        company = frappe.defaults.get_user_default("Company")
        results = frappe.db.sql(query, [company], as_dict=True)

        for result in results:
            alert = {
                "id": f"stock_critical_{result.item_code}_{result.warehouse_name}",
                "type": "stock_critical",
                "severity": "critical",
                "item_code": result.item_code,
                "item_name": result.item_name,
                "warehouse": result.warehouse_name,
                "current_stock": 0.0,
                "min_stock_level": flt(result.min_stock_level),
                "reorder_quantity": flt(result.reorder_quantity),
                "preferred_supplier": result.preferred_supplier,
                "part_category": result.part_category,
                "estimated_value": 0.0,
                "stock_percentage": 0.0,
                "created_on": now_datetime(),
                "requires_action": True,
                "action_suggestions": cls._get_emergency_reorder_suggestions(result),
                "message_en": f"CRITICAL: {result.item_name} is out of stock in {result.warehouse_name}",
                "message_ar": f"حرج: نفد مخزون {result.item_name} في {result.warehouse_name}",
            }

            alerts.append(alert)

        return alerts

    @classmethod
    def _scan_expiring_items(cls) -> List[Dict[str, Any]]:
        """Scan for items expiring within warning period"""

        alerts = []
        warning_days = 30  # Items expiring within 30 days
        warning_date = getdate() + timedelta(days=warning_days)

        # Check batch-wise expiry dates
        query = """
            SELECT 
                sle.item_code,
                i.item_name,
                sle.warehouse,
                sle.batch_no,
                b.expiry_date,
                SUM(sle.actual_qty) as batch_qty,
                i.standard_rate,
                i.part_category,
                DATEDIFF(%s, b.expiry_date) as days_to_expiry
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.item_code
            INNER JOIN `tabBatch` b ON sle.batch_no = b.name
            WHERE sle.is_cancelled = 0
            AND b.expiry_date IS NOT NULL
            AND b.expiry_date BETWEEN %s AND %s
            AND i.disabled = 0
            GROUP BY sle.item_code, sle.warehouse, sle.batch_no
            HAVING SUM(sle.actual_qty) > 0
            ORDER BY b.expiry_date ASC
        """

        results = frappe.db.sql(query, [warning_date, getdate(), warning_date], as_dict=True)

        for result in results:
            days_to_expiry = result.days_to_expiry

            # Determine severity based on days to expiry
            if days_to_expiry <= 7:
                severity = "critical"
            elif days_to_expiry <= 14:
                severity = "high"
            elif days_to_expiry <= 21:
                severity = "medium"
            else:
                severity = "low"

            alert = {
                "id": f"expiring_{result.item_code}_{result.batch_no}",
                "type": "item_expiring",
                "severity": severity,
                "item_code": result.item_code,
                "item_name": result.item_name,
                "warehouse": result.warehouse,
                "batch_no": result.batch_no,
                "expiry_date": result.expiry_date,
                "days_to_expiry": days_to_expiry,
                "batch_quantity": flt(result.batch_qty),
                "estimated_value": flt(result.batch_qty) * flt(result.standard_rate),
                "part_category": result.part_category,
                "created_on": now_datetime(),
                "requires_action": True,
                "action_suggestions": cls._get_expiry_action_suggestions(result, days_to_expiry),
                "message_en": f"{result.item_name} (Batch: {result.batch_no}) expires in {days_to_expiry} days",
                "message_ar": f"{result.item_name} (دفعة: {result.batch_no}) ينتهي خلال {days_to_expiry} أيام",
            }

            alerts.append(alert)

        return alerts

    @classmethod
    def _scan_expired_items(cls) -> List[Dict[str, Any]]:
        """Scan for items that have already expired"""

        alerts = []
        today = getdate()

        # Check expired batches
        query = """
            SELECT 
                sle.item_code,
                i.item_name,
                sle.warehouse,
                sle.batch_no,
                b.expiry_date,
                SUM(sle.actual_qty) as batch_qty,
                i.standard_rate,
                i.part_category,
                DATEDIFF(%s, b.expiry_date) as days_expired
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.item_code
            INNER JOIN `tabBatch` b ON sle.batch_no = b.name
            WHERE sle.is_cancelled = 0
            AND b.expiry_date IS NOT NULL
            AND b.expiry_date < %s
            AND i.disabled = 0
            GROUP BY sle.item_code, sle.warehouse, sle.batch_no
            HAVING SUM(sle.actual_qty) > 0
            ORDER BY b.expiry_date ASC
        """

        results = frappe.db.sql(query, [today, today], as_dict=True)

        for result in results:
            alert = {
                "id": f"expired_{result.item_code}_{result.batch_no}",
                "type": "item_expired",
                "severity": "critical",
                "item_code": result.item_code,
                "item_name": result.item_name,
                "warehouse": result.warehouse,
                "batch_no": result.batch_no,
                "expiry_date": result.expiry_date,
                "days_expired": result.days_expired,
                "batch_quantity": flt(result.batch_qty),
                "estimated_loss": flt(result.batch_qty) * flt(result.standard_rate),
                "part_category": result.part_category,
                "created_on": now_datetime(),
                "requires_action": True,
                "action_suggestions": ["quarantine_item", "dispose_safely", "quality_check"],
                "message_en": f"EXPIRED: {result.item_name} (Batch: {result.batch_no}) expired {result.days_expired} days ago",
                "message_ar": f"منتهي الصلاحية: {result.item_name} (دفعة: {result.batch_no}) انتهت منذ {result.days_expired} أيام",
            }

            alerts.append(alert)

        return alerts

    @classmethod
    def _scan_reorder_point_alerts(cls) -> List[Dict[str, Any]]:
        """Scan for items that have reached reorder point"""

        alerts = []

        # Find items at exactly reorder level
        query = """
            SELECT 
                i.item_code,
                i.item_name,
                i.min_stock_level,
                i.reorder_quantity,
                i.preferred_supplier,
                sle.warehouse,
                SUM(sle.actual_qty) as current_stock,
                i.standard_rate,
                i.part_category
            FROM `tabItem` i
            LEFT JOIN `tabStock Ledger Entry` sle ON i.item_code = sle.item_code
            WHERE i.disabled = 0 
            AND i.is_stock_item = 1
            AND i.min_stock_level > 0
            AND i.reorder_quantity > 0
            AND sle.is_cancelled = 0
            GROUP BY i.item_code, sle.warehouse
            HAVING SUM(sle.actual_qty) <= i.min_stock_level 
            AND SUM(sle.actual_qty) > (i.min_stock_level * 0.8)
            ORDER BY i.item_name
        """

        results = frappe.db.sql(query, as_dict=True)

        for result in results:
            alert = {
                "id": f"reorder_{result.item_code}_{result.warehouse}",
                "type": "reorder_point",
                "severity": "medium",
                "item_code": result.item_code,
                "item_name": result.item_name,
                "warehouse": result.warehouse,
                "current_stock": flt(result.current_stock),
                "min_stock_level": flt(result.min_stock_level),
                "reorder_quantity": flt(result.reorder_quantity),
                "preferred_supplier": result.preferred_supplier,
                "part_category": result.part_category,
                "estimated_cost": flt(result.reorder_quantity) * flt(result.standard_rate),
                "created_on": now_datetime(),
                "requires_action": True,
                "action_suggestions": ["create_purchase_order", "check_supplier_availability"],
                "message_en": f"Reorder point reached for {result.item_name} in {result.warehouse}",
                "message_ar": f"وصلت نقطة إعادة الطلب لـ {result.item_name} في {result.warehouse}",
            }

            alerts.append(alert)

        return alerts

    @classmethod
    def _scan_slow_moving_items(cls) -> List[Dict[str, Any]]:
        """Scan for slow moving inventory items"""

        alerts = []
        days_threshold = 90  # Items not moved in 90 days
        threshold_date = getdate() - timedelta(days=days_threshold)

        # Find items with no movement in specified period
        query = """
            SELECT 
                i.item_code,
                i.item_name,
                i.part_category,
                sle.warehouse,
                SUM(sle.actual_qty) as current_stock,
                i.standard_rate,
                MAX(sle.posting_date) as last_movement_date,
                DATEDIFF(%s, MAX(sle.posting_date)) as days_since_movement
            FROM `tabItem` i
            INNER JOIN `tabStock Ledger Entry` sle ON i.item_code = sle.item_code
            WHERE i.disabled = 0 
            AND i.is_stock_item = 1
            AND sle.is_cancelled = 0
            GROUP BY i.item_code, sle.warehouse
            HAVING SUM(sle.actual_qty) > 0
            AND MAX(sle.posting_date) < %s
            AND SUM(sle.actual_qty) * i.standard_rate > 100
            ORDER BY days_since_movement DESC
        """

        results = frappe.db.sql(query, [getdate(), threshold_date], as_dict=True)

        for result in results:
            alert = {
                "id": f"slow_moving_{result.item_code}_{result.warehouse}",
                "type": "slow_moving",
                "severity": "low",
                "item_code": result.item_code,
                "item_name": result.item_name,
                "warehouse": result.warehouse,
                "current_stock": flt(result.current_stock),
                "last_movement_date": result.last_movement_date,
                "days_since_movement": result.days_since_movement,
                "part_category": result.part_category,
                "tied_up_value": flt(result.current_stock) * flt(result.standard_rate),
                "created_on": now_datetime(),
                "requires_action": False,
                "action_suggestions": ["review_demand", "consider_discount", "transfer_location"],
                "message_en": f"Slow moving: {result.item_name} (no movement for {result.days_since_movement} days)",
                "message_ar": f"بطيء الحركة: {result.item_name} (لا حركة منذ {result.days_since_movement} أيام)",
            }

            alerts.append(alert)

        return alerts

    @classmethod
    def _determine_stock_severity(cls, stock_percentage: float) -> str:
        """Determine alert severity based on stock percentage"""

        if stock_percentage <= 0:
            return "critical"
        elif stock_percentage <= 0.1:
            return "high"
        elif stock_percentage <= 0.5:
            return "medium"
        else:
            return "low"

    @classmethod
    def _get_reorder_suggestions(cls, item_data: Dict[str, Any]) -> List[str]:
        """Get reorder action suggestions for low stock items"""

        suggestions = ["create_purchase_order"]

        if item_data.get("preferred_supplier"):
            suggestions.append("contact_preferred_supplier")
        else:
            suggestions.append("find_supplier")

        suggestions.extend(["check_alternative_parts", "internal_transfer"])

        return suggestions

    @classmethod
    def _get_emergency_reorder_suggestions(cls, item_data: Dict[str, Any]) -> List[str]:
        """Get emergency reorder suggestions for critical stock"""

        return [
            "urgent_purchase_order",
            "emergency_supplier_contact",
            "check_other_locations",
            "customer_notification",
            "alternative_part_search",
        ]

    @classmethod
    def _get_expiry_action_suggestions(
        cls, item_data: Dict[str, Any], days_to_expiry: int
    ) -> List[str]:
        """Get action suggestions for expiring items"""

        if days_to_expiry <= 7:
            return ["urgent_sale", "quality_check", "discount_sale", "internal_use"]
        elif days_to_expiry <= 14:
            return ["promote_sale", "transfer_location", "bundle_offer"]
        else:
            return ["monitor_closely", "fifo_priority", "sales_notification"]


class InventoryNotificationManager:
    """Manages notification delivery for inventory alerts"""

    @staticmethod
    @frappe.whitelist()
    def get_dashboard_alerts(limit: int = 50) -> Dict[str, Any]:
        """Get current alerts for dashboard display"""

        try:
            cached_data = frappe.cache().get_value("current_inventory_alerts")
            if not cached_data:
                # Trigger fresh scan if no cached data
                result = InventoryAlertEngine.scan_inventory_alerts()
                if result["status"] == "success":
                    cached_data = {"alerts": result["alerts"], "summary": result["summary"]}
                else:
                    return {"status": "error", "message": "Failed to scan alerts"}

            # Apply limit and prepare for dashboard
            alerts = cached_data["alerts"][:limit]

            # Group alerts by severity for dashboard widgets
            alerts_by_severity = {}
            for alert in alerts:
                severity = alert["severity"]
                if severity not in alerts_by_severity:
                    alerts_by_severity[severity] = []
                alerts_by_severity[severity].append(alert)

            return {
                "status": "success",
                "alerts": alerts,
                "alerts_by_severity": alerts_by_severity,
                "summary": cached_data["summary"],
                "total_alerts": len(alerts),
                "has_critical": any(alert["severity"] == "critical" for alert in alerts),
            }

        except Exception as e:
            frappe.log_error(f"Dashboard alerts fetch failed: {str(e)}")
            return {
                "status": "error",
                "message": _("Failed to fetch dashboard alerts"),
                "error": str(e),
            }

    @staticmethod
    @frappe.whitelist()
    def create_quick_reorder(alert_id: str, quantity: Optional[float] = None) -> Dict[str, Any]:
        """Create quick reorder from alert notification"""

        try:
            # Get alert details from cache
            cached_data = frappe.cache().get_value("current_inventory_alerts")
            if not cached_data:
                return {"status": "error", "message": "Alert data not found"}

            # Find specific alert
            alert = None
            for cached_alert in cached_data["alerts"]:
                if cached_alert["id"] == alert_id:
                    alert = cached_alert
                    break

            if not alert:
                return {"status": "error", "message": "Alert not found"}

            # Use provided quantity or default reorder quantity
            order_qty = quantity or alert.get("reorder_quantity", alert.get("min_stock_level", 1))

            # Create purchase order or transfer request
            if alert.get("preferred_supplier"):
                result = InventoryNotificationManager._create_purchase_order(alert, order_qty)
            else:
                result = InventoryNotificationManager._create_transfer_request(alert, order_qty)

            return result

        except Exception as e:
            frappe.log_error(f"Quick reorder failed: {str(e)}")
            return {
                "status": "error",
                "message": _("Failed to create quick reorder"),
                "error": str(e),
            }

    @staticmethod
    def _create_purchase_order(alert: Dict[str, Any], quantity: float) -> Dict[str, Any]:
        """Create purchase order for reorder"""

        try:
            # Create purchase order
            purchase_order = frappe.new_doc("Purchase Order")
            purchase_order.supplier = alert["preferred_supplier"]
            purchase_order.transaction_date = nowdate()
            purchase_order.schedule_date = getdate() + timedelta(days=7)  # Default 7 days
            purchase_order.set_warehouse = alert["warehouse"]

            # Add item
            item = purchase_order.append("items", {})
            item.item_code = alert["item_code"]
            item.qty = quantity
            item.schedule_date = purchase_order.schedule_date
            item.warehouse = alert["warehouse"]

            # Get item details for rate
            item_doc = frappe.get_doc("Item", alert["item_code"])
            item.rate = item_doc.standard_rate or 0
            item.amount = flt(quantity) * flt(item.rate)

            purchase_order.insert()

            return {
                "status": "success",
                "message": _("Purchase order created successfully"),
                "document_name": purchase_order.name,
                "document_type": "Purchase Order",
            }

        except Exception as e:
            frappe.log_error(f"Purchase order creation failed: {str(e)}")
            return {
                "status": "error",
                "message": _("Failed to create purchase order"),
                "error": str(e),
            }

    @staticmethod
    def _create_transfer_request(alert: Dict[str, Any], quantity: float) -> Dict[str, Any]:
        """Create internal transfer request for reorder"""

        try:
            # Find warehouse with available stock
            available_warehouses = frappe.db.sql(
                """
                SELECT warehouse, SUM(actual_qty) as available_qty
                FROM `tabStock Ledger Entry`
                WHERE item_code = %s AND is_cancelled = 0
                AND warehouse != %s
                GROUP BY warehouse
                HAVING SUM(actual_qty) >= %s
                ORDER BY SUM(actual_qty) DESC
                LIMIT 1
            """,
                [alert["item_code"], alert["warehouse"], quantity],
                as_dict=True,
            )

            if not available_warehouses:
                return {
                    "status": "error",
                    "message": _("No warehouse with sufficient stock found for transfer"),
                }

            source_warehouse = available_warehouses[0]["warehouse"]

            # Import the StockTransferWorkflow here to avoid circular imports
            from universal_workshop.parts_inventory.warehouse_management import (
                StockTransferWorkflow,
            )

            # Create transfer request
            items = [{"item_code": alert["item_code"], "qty": quantity}]

            transfer_id = StockTransferWorkflow.create_transfer_request(
                source_warehouse=source_warehouse,
                target_warehouse=alert["warehouse"],
                items=items,
                purpose="Stock Replenishment",
                auto_approve=True,
            )

            return {
                "status": "success",
                "message": _("Stock transfer created successfully"),
                "document_name": transfer_id,
                "document_type": "Stock Entry",
            }

        except Exception as e:
            frappe.log_error(f"Transfer request creation failed: {str(e)}")
            return {
                "status": "error",
                "message": _("Failed to create transfer request"),
                "error": str(e),
            }

    @staticmethod
    @frappe.whitelist()
    def send_alert_notifications(alert_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Send notifications for specified alerts"""

        try:
            config = InventoryAlertEngine.get_alert_configuration()

            if not config.get("system_enabled"):
                return {"status": "disabled", "message": "Notification system disabled"}

            # Get alerts to notify
            cached_data = frappe.cache().get_value("current_inventory_alerts")
            if not cached_data:
                return {"status": "error", "message": "No alert data available"}

            alerts_to_notify = cached_data["alerts"]
            if alert_ids:
                alerts_to_notify = [a for a in alerts_to_notify if a["id"] in alert_ids]

            notification_results = {
                "total_alerts": len(alerts_to_notify),
                "notifications_sent": 0,
                "errors": [],
            }

            for alert in alerts_to_notify:
                try:
                    if "email" in config["notification_channels"]:
                        InventoryNotificationManager._send_email_notification(alert, config)

                    if "in_app" in config["notification_channels"]:
                        InventoryNotificationManager._send_in_app_notification(alert, config)

                    notification_results["notifications_sent"] += 1

                except Exception as e:
                    notification_results["errors"].append(
                        {"alert_id": alert["id"], "error": str(e)}
                    )

            return {"status": "success", "results": notification_results}

        except Exception as e:
            frappe.log_error(f"Alert notification sending failed: {str(e)}")
            return {
                "status": "error",
                "message": _("Failed to send notifications"),
                "error": str(e),
            }

    @staticmethod
    def _send_email_notification(alert: Dict[str, Any], config: Dict[str, Any]):
        """Send email notification for alert"""

        language = config.get("default_language", "en")

        # Get recipients based on alert severity
        recipients = InventoryNotificationManager._get_alert_recipients(alert["severity"])

        if not recipients:
            return

        subject = alert[f"message_{language}"]

        # Create detailed email content
        template_context = {
            "alert": alert,
            "language": language,
            "severity_info": InventoryAlertEngine.ALERT_SEVERITIES[alert["severity"]],
            "system_url": frappe.utils.get_url(),
        }

        # Send email
        frappe.sendmail(
            recipients=recipients,
            subject=subject,
            template="inventory_alert_email",
            args=template_context,
            header=[_("Inventory Alert"), "red" if alert["severity"] == "critical" else "orange"],
        )

    @staticmethod
    def _send_in_app_notification(alert: Dict[str, Any], config: Dict[str, Any]):
        """Send in-app notification for alert"""

        language = config.get("default_language", "en")
        recipients = InventoryNotificationManager._get_alert_recipients(alert["severity"])

        for user in recipients:
            # Create notification document
            notification = frappe.new_doc("Notification Log")
            notification.subject = alert[f"message_{language}"]
            notification.for_user = user
            notification.type = "Alert"
            notification.document_type = "Item"
            notification.document_name = alert["item_code"]
            notification.from_user = "Administrator"
            notification.read = 0
            notification.insert()

    @staticmethod
    def _get_alert_recipients(severity: str) -> List[str]:
        """Get notification recipients based on alert severity"""

        # Get users with inventory management roles
        recipients = []

        if severity == "critical":
            # Critical alerts go to managers and supervisors
            roles = ["Inventory Manager", "Workshop Manager", "System Manager"]
        elif severity == "high":
            # High alerts go to inventory staff and managers
            roles = ["Inventory Manager", "Inventory User", "Workshop Manager"]
        else:
            # Medium/Low alerts go to inventory users
            roles = ["Inventory User", "Inventory Manager"]

        for role in roles:
            role_users = frappe.get_all(
                "Has Role", filters={"role": role}, fields=["parent"], pluck="parent"
            )
            recipients.extend(role_users)

        # Remove duplicates and return
        return list(set(recipients))


# WhiteListed API methods for external access
@frappe.whitelist()
def initialize_alert_system():
    """Initialize inventory alert system"""
    return InventoryAlertEngine.initialize_alert_system()


@frappe.whitelist()
def get_dashboard_alerts(limit=50):
    """Get alerts for dashboard display"""
    return InventoryNotificationManager.get_dashboard_alerts(int(limit))


@frappe.whitelist()
def scan_inventory_alerts(alert_types=None):
    """Trigger inventory alert scan"""
    if alert_types and isinstance(alert_types, str):
        alert_types = json.loads(alert_types)
    return InventoryAlertEngine.scan_inventory_alerts(alert_types)


@frappe.whitelist()
def create_quick_reorder(alert_id, quantity=None):
    """Create quick reorder from alert"""
    return InventoryNotificationManager.create_quick_reorder(
        alert_id, float(quantity) if quantity else None
    )


@frappe.whitelist()
def send_alert_notifications(alert_ids=None):
    """Send notifications for alerts"""
    if alert_ids and isinstance(alert_ids, str):
        alert_ids = json.loads(alert_ids)
    return InventoryNotificationManager.send_alert_notifications(alert_ids)


@frappe.whitelist()
def get_alert_configuration():
    """Get current alert configuration"""
    return InventoryAlertEngine.get_alert_configuration()


@frappe.whitelist()
def update_alert_configuration(updates):
    """Update alert configuration"""
    if isinstance(updates, str):
        updates = json.loads(updates)
    return InventoryAlertEngine.update_alert_configuration(updates)
