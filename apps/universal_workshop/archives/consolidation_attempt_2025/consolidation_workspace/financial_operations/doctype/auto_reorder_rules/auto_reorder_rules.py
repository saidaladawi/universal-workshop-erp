import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, cint, getdate, add_days, nowdate
import math
from datetime import datetime, timedelta


class AutoReorderRules(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields to Document class

    def validate(self):
        """Validate auto reorder rules"""
        self.validate_reorder_levels()
        self.validate_forecasting_parameters()
        self.validate_suppliers()
        self.set_title()

    def validate_reorder_levels(self):
        """Validate reorder level configuration"""
        if self.reorder_level <= 0:
            frappe.throw(_("Reorder Level must be greater than zero"))

        if self.reorder_quantity <= 0:
            frappe.throw(_("Reorder Quantity must be greater than zero"))

        if self.maximum_stock and self.maximum_stock <= self.reorder_level:
            frappe.throw(_("Maximum Stock should be greater than Reorder Level"))

        if self.safety_stock and self.safety_stock < 0:
            frappe.throw(_("Safety Stock cannot be negative"))

    def validate_forecasting_parameters(self):
        """Validate demand forecasting parameters"""
        if self.smoothing_alpha < 0 or self.smoothing_alpha > 1:
            frappe.throw(_("Smoothing Alpha must be between 0 and 1"))

        if self.seasonal_factor <= 0:
            frappe.throw(_("Seasonal Factor must be greater than zero"))

        if self.forecast_period_days <= 0:
            frappe.throw(_("Forecast Period must be greater than zero"))

    def validate_suppliers(self):
        """Validate supplier configuration"""
        if not self.preferred_supplier and self.auto_create_purchase_order:
            frappe.throw(
                _("Preferred Supplier is required when Auto Create Purchase Order is enabled")
            )

    def set_title(self):
        """Set document title for easy identification"""
        self.title = f"{self.item_code} - {self.warehouse}"

    def before_save(self):
        """Update calculated fields before saving"""
        self.update_current_stock()
        self.calculate_average_consumption()
        self.update_last_purchase_info()

    def update_current_stock(self):
        """Update current stock level from stock ledger"""
        current_stock = frappe.db.sql(
            """
            SELECT SUM(actual_qty) as stock
            FROM `tabStock Ledger Entry`
            WHERE item_code = %s AND warehouse = %s
            AND is_cancelled = 0
        """,
            [self.item_code, self.warehouse],
        )

        self.current_stock = (
            flt(current_stock[0][0]) if current_stock and current_stock[0][0] else 0.0
        )

    def calculate_average_consumption(self):
        """Calculate average daily consumption based on historical data"""
        # Get consumption data for the last 90 days
        consumption_data = frappe.db.sql(
            """
            SELECT SUM(ABS(actual_qty)) as consumed
            FROM `tabStock Ledger Entry`
            WHERE item_code = %s AND warehouse = %s
            AND actual_qty < 0
            AND posting_date >= %s
            AND is_cancelled = 0
        """,
            [self.item_code, self.warehouse, add_days(nowdate(), -90)],
        )

        total_consumed = (
            flt(consumption_data[0][0]) if consumption_data and consumption_data[0][0] else 0.0
        )
        self.average_consumption = total_consumed / 90 if total_consumed > 0 else 0.0

    def update_last_purchase_info(self):
        """Update last purchase rate and date"""
        last_purchase = frappe.db.sql(
            """
            SELECT rate, posting_date
            FROM `tabPurchase Receipt Item`
            WHERE item_code = %s AND warehouse = %s
            AND docstatus = 1
            ORDER BY posting_date DESC, creation DESC
            LIMIT 1
        """,
            [self.item_code, self.warehouse],
            as_dict=True,
        )

        if last_purchase:
            self.last_purchase_rate = last_purchase[0].rate
            self.last_purchase_date = last_purchase[0].posting_date

    def calculate_demand_forecast(self):
        """Calculate demand forecast using selected method"""
        if self.forecasting_method == "Simple Average":
            return self.simple_average_forecast()
        elif self.forecasting_method == "Moving Average":
            return self.moving_average_forecast()
        elif self.forecasting_method == "Exponential Smoothing":
            return self.exponential_smoothing_forecast()
        elif self.forecasting_method == "Linear Regression":
            return self.linear_regression_forecast()
        else:
            return self.average_consumption * self.forecast_period_days

    def simple_average_forecast(self):
        """Simple average forecast based on historical consumption"""
        return self.average_consumption * self.forecast_period_days * self.seasonal_factor

    def moving_average_forecast(self):
        """Moving average forecast for the last 30 days"""
        consumption_data = frappe.db.sql(
            """
            SELECT ABS(actual_qty) as consumed, posting_date
            FROM `tabStock Ledger Entry`
            WHERE item_code = %s AND warehouse = %s
            AND actual_qty < 0
            AND posting_date >= %s
            AND is_cancelled = 0
            ORDER BY posting_date DESC
            LIMIT 30
        """,
            [self.item_code, self.warehouse, add_days(nowdate(), -30)],
            as_dict=True,
        )

        if not consumption_data:
            return self.simple_average_forecast()

        total_consumption = sum([flt(row.consumed) for row in consumption_data])
        daily_average = total_consumption / min(30, len(consumption_data))

        return daily_average * self.forecast_period_days * self.seasonal_factor

    def exponential_smoothing_forecast(self):
        """Exponential smoothing forecast with configurable alpha"""
        # Get historical data for the last 60 days
        consumption_data = frappe.db.sql(
            """
            SELECT DATE(posting_date) as date, SUM(ABS(actual_qty)) as consumed
            FROM `tabStock Ledger Entry`
            WHERE item_code = %s AND warehouse = %s
            AND actual_qty < 0
            AND posting_date >= %s
            AND is_cancelled = 0
            GROUP BY DATE(posting_date)
            ORDER BY posting_date ASC
        """,
            [self.item_code, self.warehouse, add_days(nowdate(), -60)],
            as_dict=True,
        )

        if not consumption_data:
            return self.simple_average_forecast()

        # Initialize with first value
        forecast = flt(consumption_data[0].consumed)
        alpha = self.smoothing_alpha

        # Apply exponential smoothing
        for row in consumption_data[1:]:
            actual = flt(row.consumed)
            forecast = alpha * actual + (1 - alpha) * forecast

        return forecast * self.forecast_period_days * self.seasonal_factor

    def linear_regression_forecast(self):
        """Linear regression forecast based on trend analysis"""
        # Get historical data for the last 90 days
        consumption_data = frappe.db.sql(
            """
            SELECT DATE(posting_date) as date, SUM(ABS(actual_qty)) as consumed
            FROM `tabStock Ledger Entry`
            WHERE item_code = %s AND warehouse = %s
            AND actual_qty < 0
            AND posting_date >= %s
            AND is_cancelled = 0
            GROUP BY DATE(posting_date)
            ORDER BY posting_date ASC
        """,
            [self.item_code, self.warehouse, add_days(nowdate(), -90)],
            as_dict=True,
        )

        if len(consumption_data) < 7:  # Need at least 7 data points
            return self.exponential_smoothing_forecast()

        # Prepare data for linear regression
        x_values = list(range(len(consumption_data)))
        y_values = [flt(row.consumed) for row in consumption_data]

        # Calculate linear regression coefficients
        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)

        # Calculate slope and intercept
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        intercept = (sum_y - slope * sum_x) / n

        # Forecast for the next period
        next_x = len(x_values)
        forecasted_daily = slope * next_x + intercept

        return max(0, forecasted_daily * self.forecast_period_days * self.seasonal_factor)

    def update_forecast(self):
        """Update demand forecast and next reorder date"""
        self.forecasted_demand = self.calculate_demand_forecast()
        self.last_forecast_date = nowdate()

        # Calculate next reorder date based on consumption rate
        if self.average_consumption > 0:
            days_to_reorder = (self.current_stock - self.reorder_level) / self.average_consumption
            days_to_reorder = max(0, days_to_reorder)  # Cannot be negative
            self.next_reorder_date = add_days(nowdate(), int(days_to_reorder))

        self.save()

    def check_reorder_required(self):
        """Check if reorder is required based on current stock and forecast"""
        if not self.enabled:
            return False

        # Update current stock and forecast
        self.update_current_stock()

        # Check if stock is below reorder level
        if self.current_stock <= self.reorder_level:
            return True

        # Check if projected stock will fall below reorder level
        projected_stock = self.current_stock - (self.average_consumption * self.lead_time_days)
        if projected_stock <= self.reorder_level:
            return True

        return False

    def create_material_request(self):
        """Create material request for reorder"""
        if not self.auto_create_material_request:
            return None

        # Calculate required quantity
        required_qty = self.reorder_quantity

        # Adjust for safety stock
        if self.safety_stock:
            target_stock = self.reorder_level + self.safety_stock
            if self.current_stock < target_stock:
                required_qty = max(required_qty, target_stock - self.current_stock)

        # Create Material Request
        mr = frappe.new_doc("Material Request")
        mr.material_request_type = "Purchase"
        mr.transaction_date = nowdate()
        mr.schedule_date = add_days(nowdate(), self.lead_time_days)
        mr.company = frappe.defaults.get_user_default("Company")

        # Add item
        mr.append(
            "items",
            {
                "item_code": self.item_code,
                "qty": required_qty,
                "schedule_date": add_days(nowdate(), self.lead_time_days),
                "warehouse": self.warehouse,
                "description": f"Auto reorder for {self.item_code}",
            },
        )

        mr.insert()

        if not self.approval_required:
            mr.submit()

        return mr.name

    def create_purchase_order(self):
        """Create purchase order if auto creation is enabled"""
        if not self.auto_create_purchase_order or not self.preferred_supplier:
            return None

        # Calculate required quantity
        required_qty = self.reorder_quantity

        # Create Purchase Order
        po = frappe.new_doc("Purchase Order")
        po.supplier = self.preferred_supplier
        po.transaction_date = nowdate()
        po.schedule_date = add_days(nowdate(), self.lead_time_days)
        po.company = frappe.defaults.get_user_default("Company")

        # Add item
        po.append(
            "items",
            {
                "item_code": self.item_code,
                "qty": required_qty,
                "schedule_date": add_days(nowdate(), self.lead_time_days),
                "warehouse": self.warehouse,
                "rate": self.last_purchase_rate or 0,
                "description": f"Auto reorder for {self.item_code}",
            },
        )

        po.insert()

        if not self.approval_required:
            po.submit()

        return po.name


@frappe.whitelist()
def run_auto_reorder_process():
    """Run automatic reorder process for all enabled rules"""

    # Get all enabled auto reorder rules
    reorder_rules = frappe.get_list("Auto Reorder Rules", filters={"enabled": 1}, fields=["name"])

    results = {
        "processed": 0,
        "reorders_created": 0,
        "material_requests": [],
        "purchase_orders": [],
        "errors": [],
    }

    for rule in reorder_rules:
        try:
            rule_doc = frappe.get_doc("Auto Reorder Rules", rule.name)

            # Update forecast
            rule_doc.update_forecast()

            # Check if reorder is required
            if rule_doc.check_reorder_required():

                # Create material request
                if rule_doc.auto_create_material_request:
                    mr_name = rule_doc.create_material_request()
                    if mr_name:
                        results["material_requests"].append(mr_name)
                        results["reorders_created"] += 1

                # Create purchase order
                if rule_doc.auto_create_purchase_order:
                    po_name = rule_doc.create_purchase_order()
                    if po_name:
                        results["purchase_orders"].append(po_name)
                        results["reorders_created"] += 1

            results["processed"] += 1

        except Exception as e:
            frappe.log_error(f"Error processing auto reorder rule {rule.name}: {str(e)}")
            results["errors"].append(f"Rule {rule.name}: {str(e)}")

    frappe.db.commit()
    return results


@frappe.whitelist()
def update_all_forecasts():
    """Update demand forecasts for all enabled auto reorder rules"""

    rules = frappe.get_list("Auto Reorder Rules", filters={"enabled": 1}, fields=["name"])

    updated_count = 0

    for rule in rules:
        try:
            rule_doc = frappe.get_doc("Auto Reorder Rules", rule.name)
            rule_doc.update_forecast()
            updated_count += 1
        except Exception as e:
            frappe.log_error(f"Error updating forecast for rule {rule.name}: {str(e)}")

    frappe.db.commit()
    return {"updated": updated_count}


@frappe.whitelist()
def get_reorder_analytics(warehouse=None, item_group=None):
    """Get analytics for auto reorder system"""

    filters = {"enabled": 1}
    if warehouse:
        filters["warehouse"] = warehouse

    rules = frappe.db.sql(
        """
        SELECT 
            arr.name,
            arr.item_code,
            arr.item_name,
            arr.warehouse,
            arr.current_stock,
            arr.reorder_level,
            arr.average_consumption,
            arr.forecasted_demand,
            arr.next_reorder_date,
            CASE 
                WHEN arr.current_stock <= arr.reorder_level THEN 'Critical'
                WHEN arr.current_stock <= (arr.reorder_level * 1.2) THEN 'Low'
                ELSE 'Normal'
            END as stock_status
        FROM `tabAuto Reorder Rules` arr
        WHERE arr.enabled = 1
        {warehouse_filter}
        ORDER BY arr.current_stock / arr.reorder_level ASC
    """.format(
            warehouse_filter="AND arr.warehouse = %(warehouse)s" if warehouse else ""
        ),
        {"warehouse": warehouse} if warehouse else {},
        as_dict=True,
    )

    # Get summary statistics
    total_rules = len(rules)
    critical_items = len([r for r in rules if r.stock_status == "Critical"])
    low_items = len([r for r in rules if r.stock_status == "Low"])

    return {
        "rules": rules,
        "summary": {
            "total_rules": total_rules,
            "critical_items": critical_items,
            "low_items": low_items,
            "normal_items": total_rules - critical_items - low_items,
        },
    }
