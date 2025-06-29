# universal_workshop/parts_inventory/demand_forecasting.py
"""
Advanced Demand Forecasting Algorithm with Seasonal Adjustments
Intelligent demand prediction system for automotive workshop inventory optimization
"""

import json
import math
import statistics
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

import frappe
from frappe import _
from frappe.utils import add_days, add_months, date_diff, flt, getdate, now_datetime, nowdate
from universal_workshop.utils.arabic_utils import ArabicTextUtils


class DemandForecastingEngine:
    """Advanced demand forecasting with multiple algorithms and seasonal adjustments"""

    def __init__(self):
        self.seasonal_patterns = {}
        self.forecast_cache = {}

    def generate_demand_forecast(
        self,
        item_code: str,
        forecast_periods: int = 12,
        forecast_method: str = "auto",
        warehouse: str | None = None,
        include_seasonality: bool = True,
        confidence_level: float = 0.95,
    ) -> dict[str, Any]:
        """Generate comprehensive demand forecast for an item"""

        try:
            # Get historical demand data
            historical_data = self._get_historical_demand_data(item_code, warehouse)

            if not historical_data or len(historical_data) < 6:
                return {
                    "success": False,
                    "error": "Insufficient historical data (minimum 6 months required)",
                    "required_periods": 6,
                }

            # Prepare data for forecasting
            demand_series = self._prepare_demand_series(historical_data)

            # Detect seasonality if enabled
            seasonal_analysis = None
            if include_seasonality:
                seasonal_analysis = self._detect_seasonality(demand_series)

            # Select optimal forecasting method
            if forecast_method == "auto":
                forecast_method = self._select_optimal_method(demand_series, seasonal_analysis)

            # Generate forecast
            forecast_result = self._generate_forecast(
                demand_series, forecast_periods, forecast_method, seasonal_analysis
            )

            # Calculate confidence intervals
            confidence_intervals = self._calculate_confidence_intervals(
                demand_series, forecast_result["forecasts"], confidence_level
            )

            # Generate insights and recommendations
            insights = self._generate_forecast_insights(historical_data, forecast_result, seasonal_analysis)

            return {
                "success": True,
                "item_code": item_code,
                "warehouse": warehouse,
                "forecast_method": forecast_method,
                "forecast_periods": forecast_periods,
                "historical_stats": self._calculate_historical_stats(demand_series),
                "seasonal_analysis": seasonal_analysis,
                "forecasts": forecast_result["forecasts"],
                "confidence_intervals": confidence_intervals,
                "accuracy_metrics": forecast_result.get("accuracy_metrics", {}),
                "insights": insights,
                "generated_at": now_datetime(),
            }

        except Exception as e:
            frappe.log_error(f"Demand forecasting failed for {item_code}: {e!s}")
            return {"success": False, "error": str(e)}

    def _get_historical_demand_data(self, item_code: str, warehouse: str, months: int = 24) -> list[dict]:
        """Get historical demand data from stock transactions"""

        from_date = add_months(nowdate(), -months)

        # Get consumption data from stock ledger entries (negative quantities = consumption)
        demand_data = frappe.db.sql(
            """
            SELECT
                DATE_FORMAT(posting_date, '%%Y-%%m') as period,
                SUM(ABS(actual_qty)) as total_demand,
                COUNT(*) as transaction_count,
                AVG(ABS(actual_qty)) as avg_transaction_size
            FROM `tabStock Ledger Entry`
            WHERE item_code = %(item_code)s
            AND posting_date >= %(from_date)s
            AND actual_qty < 0
            {warehouse_condition}
            GROUP BY DATE_FORMAT(posting_date, '%%Y-%%m')
            ORDER BY posting_date
        """.format(warehouse_condition="AND warehouse = %(warehouse)s" if warehouse else ""),
            {"item_code": item_code, "from_date": from_date, "warehouse": warehouse},
            as_dict=True,
        )

        # Fill in missing months with zero demand
        filled_data = self._fill_missing_periods(demand_data, from_date)

        return filled_data

    def _fill_missing_periods(self, data: list[dict], from_date: str) -> list[dict]:
        """Fill missing periods with zero demand to ensure continuous time series"""

        if not data:
            return []

        # Create period map from existing data
        existing_periods = {item["period"]: item for item in data}

        # Generate all periods from start date to now
        current_date = getdate(from_date)
        end_date = getdate(nowdate())
        filled_data = []

        while current_date <= end_date:
            period = current_date.strftime("%Y-%m")

            if period in existing_periods:
                filled_data.append(existing_periods[period])
            else:
                filled_data.append(
                    {"period": period, "total_demand": 0, "transaction_count": 0, "avg_transaction_size": 0}
                )

            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)

        return filled_data

    def _prepare_demand_series(self, historical_data: list[dict]) -> list[float]:
        """Convert historical data to time series for analysis"""
        return [float(item["total_demand"]) for item in historical_data]

    def _detect_seasonality(self, demand_series: list[float]) -> dict[str, Any]:
        """Detect seasonal patterns in demand data"""

        if len(demand_series) < 12:
            return {"has_seasonality": False, "reason": "Insufficient data for seasonal analysis"}

        # Simple seasonal decomposition
        n = len(demand_series)
        seasonal_indices = {}

        # Calculate seasonal indices for each month
        for month in range(12):
            month_values = []
            for i in range(month, n, 12):
                if i < n:
                    month_values.append(demand_series[i])

            if month_values:
                # Calculate average for this month across all years
                month_avg = statistics.mean(month_values)
                overall_avg = statistics.mean(demand_series)

                # Seasonal index = month average / overall average
                seasonal_index = month_avg / overall_avg if overall_avg > 0 else 1.0
                seasonal_indices[month + 1] = seasonal_index

        # Detect if there's significant seasonality
        seasonal_values = list(seasonal_indices.values())
        seasonal_variation = max(seasonal_values) - min(seasonal_values)
        has_seasonality = seasonal_variation > 0.2  # 20% variation threshold

        # Identify peak and low seasons
        peak_month = max(seasonal_indices, key=seasonal_indices.get)
        low_month = min(seasonal_indices, key=seasonal_indices.get)

        return {
            "has_seasonality": has_seasonality,
            "seasonal_variation": round(seasonal_variation, 3),
            "seasonal_indices": seasonal_indices,
            "peak_month": peak_month,
            "low_month": low_month,
            "peak_index": round(seasonal_indices[peak_month], 2),
            "low_index": round(seasonal_indices[low_month], 2),
        }

    def _select_optimal_method(self, demand_series: list[float], seasonal_analysis: dict) -> str:
        """Automatically select the best forecasting method based on data characteristics"""

        n = len(demand_series)

        # Calculate basic statistics
        mean_demand = statistics.mean(demand_series)
        std_demand = statistics.stdev(demand_series) if n > 1 else 0
        cv = std_demand / mean_demand if mean_demand > 0 else 0  # Coefficient of variation

        # Detect trend
        trend_slope = self._calculate_trend_slope(demand_series)
        has_trend = abs(trend_slope) > 0.1  # Significant trend threshold

        # Method selection logic
        if seasonal_analysis.get("has_seasonality", False) and has_trend:
            return "seasonal_trend"  # Holt-Winters equivalent
        elif seasonal_analysis.get("has_seasonality", False):
            return "seasonal"
        elif has_trend:
            return "exponential_smoothing"
        elif cv < 0.3:  # Low variability
            return "simple_moving_average"
        else:  # High variability
            return "weighted_moving_average"

    def _calculate_trend_slope(self, demand_series: list[float]) -> float:
        """Calculate trend slope using linear regression"""

        n = len(demand_series)
        if n < 2:
            return 0

        x = list(range(n))
        y = demand_series

        # Linear regression slope calculation
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(y)

        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        return numerator / denominator if denominator != 0 else 0

    def _generate_forecast(
        self, demand_series: list[float], periods: int, method: str, seasonal_analysis: dict
    ) -> dict[str, Any]:
        """Generate forecast using the specified method"""

        if method == "simple_moving_average":
            return self._simple_moving_average_forecast(demand_series, periods)
        elif method == "weighted_moving_average":
            return self._weighted_moving_average_forecast(demand_series, periods)
        elif method == "exponential_smoothing":
            return self._exponential_smoothing_forecast(demand_series, periods)
        elif method == "seasonal":
            return self._seasonal_forecast(demand_series, periods, seasonal_analysis)
        elif method == "seasonal_trend":
            return self._seasonal_trend_forecast(demand_series, periods, seasonal_analysis)
        else:
            # Default to simple moving average
            return self._simple_moving_average_forecast(demand_series, periods)

    def _simple_moving_average_forecast(
        self, demand_series: list[float], periods: int, window: int = 6
    ) -> dict[str, Any]:
        """Simple Moving Average forecast"""

        if len(demand_series) < window:
            window = max(1, len(demand_series))

        # Calculate moving average from last 'window' periods
        recent_data = demand_series[-window:]
        forecast_value = statistics.mean(recent_data)

        # Forecast same value for all future periods
        forecasts = [round(forecast_value, 2) for _ in range(periods)]

        # Calculate accuracy on historical data
        accuracy_metrics = self._calculate_accuracy_metrics(demand_series, "sma", window)

        return {
            "forecasts": forecasts,
            "method_params": {"window": window},
            "accuracy_metrics": accuracy_metrics,
        }

    def _weighted_moving_average_forecast(
        self, demand_series: list[float], periods: int, window: int = 6
    ) -> dict[str, Any]:
        """Weighted Moving Average forecast with higher weights for recent periods"""

        if len(demand_series) < window:
            window = max(1, len(demand_series))

        recent_data = demand_series[-window:]

        # Create weights (higher for recent periods)
        weights = [(i + 1) for i in range(window)]
        total_weight = sum(weights)

        # Calculate weighted average
        weighted_sum = sum(recent_data[i] * weights[i] for i in range(len(recent_data)))
        forecast_value = weighted_sum / total_weight

        forecasts = [round(forecast_value, 2) for _ in range(periods)]

        accuracy_metrics = self._calculate_accuracy_metrics(demand_series, "wma", window)

        return {
            "forecasts": forecasts,
            "method_params": {"window": window, "weights": weights},
            "accuracy_metrics": accuracy_metrics,
        }

    def _exponential_smoothing_forecast(
        self, demand_series: list[float], periods: int, alpha: float = 0.3
    ) -> dict[str, Any]:
        """Exponential Smoothing forecast"""

        if not demand_series:
            return {"forecasts": [0] * periods, "method_params": {"alpha": alpha}, "accuracy_metrics": {}}

        # Initialize with first value
        smoothed_value = demand_series[0]

        # Apply exponential smoothing to historical data
        for value in demand_series[1:]:
            smoothed_value = alpha * value + (1 - alpha) * smoothed_value

        # Forecast same smoothed value for all future periods
        forecasts = [round(smoothed_value, 2) for _ in range(periods)]

        accuracy_metrics = self._calculate_accuracy_metrics(demand_series, "exp", alpha)

        return {
            "forecasts": forecasts,
            "method_params": {"alpha": alpha},
            "accuracy_metrics": accuracy_metrics,
        }

    def _seasonal_forecast(
        self, demand_series: list[float], periods: int, seasonal_analysis: dict
    ) -> dict[str, Any]:
        """Seasonal forecast using seasonal indices"""

        seasonal_indices = seasonal_analysis.get("seasonal_indices", {})

        # Calculate base level (trend-adjusted average)
        base_level = (
            statistics.mean(demand_series[-12:])
            if len(demand_series) >= 12
            else statistics.mean(demand_series)
        )

        forecasts = []
        for period in range(periods):
            # Determine which month this forecast period represents
            current_month = ((len(demand_series) + period) % 12) + 1
            seasonal_index = seasonal_indices.get(current_month, 1.0)

            # Apply seasonal adjustment
            forecast_value = base_level * seasonal_index
            forecasts.append(round(forecast_value, 2))

        accuracy_metrics = self._calculate_accuracy_metrics(demand_series, "seasonal", seasonal_analysis)

        return {
            "forecasts": forecasts,
            "method_params": {"base_level": base_level, "seasonal_indices": seasonal_indices},
            "accuracy_metrics": accuracy_metrics,
        }

    def _seasonal_trend_forecast(
        self, demand_series: list[float], periods: int, seasonal_analysis: dict
    ) -> dict[str, Any]:
        """Seasonal forecast with trend adjustment (simplified Holt-Winters)"""

        seasonal_indices = seasonal_analysis.get("seasonal_indices", {})

        # Calculate trend
        trend_slope = self._calculate_trend_slope(demand_series)

        # Calculate base level from recent data
        base_level = (
            statistics.mean(demand_series[-6:]) if len(demand_series) >= 6 else statistics.mean(demand_series)
        )

        forecasts = []
        for period in range(periods):
            # Project trend forward
            trend_component = base_level + (trend_slope * (period + 1))

            # Apply seasonal adjustment
            current_month = ((len(demand_series) + period) % 12) + 1
            seasonal_index = seasonal_indices.get(current_month, 1.0)

            forecast_value = trend_component * seasonal_index
            forecasts.append(round(max(0, forecast_value), 2))  # Ensure non-negative

        accuracy_metrics = self._calculate_accuracy_metrics(
            demand_series, "seasonal_trend", seasonal_analysis
        )

        return {
            "forecasts": forecasts,
            "method_params": {
                "base_level": base_level,
                "trend_slope": trend_slope,
                "seasonal_indices": seasonal_indices,
            },
            "accuracy_metrics": accuracy_metrics,
        }

    def _calculate_accuracy_metrics(
        self, demand_series: list[float], method: str, params: Any
    ) -> dict[str, float]:
        """Calculate forecast accuracy metrics using backtesting"""

        if len(demand_series) < 6:
            return {"note": "Insufficient data for accuracy calculation"}

        # Use last 6 periods for testing
        test_periods = 6
        train_data = demand_series[:-test_periods]
        actual_test = demand_series[-test_periods:]

        # Generate forecasts for test period
        if method == "sma":
            window = params
            if len(train_data) >= window:
                forecast_value = statistics.mean(train_data[-window:])
                forecasts = [forecast_value] * test_periods
        elif method == "exp":
            alpha = params
            smoothed = train_data[0]
            for value in train_data[1:]:
                smoothed = alpha * value + (1 - alpha) * smoothed
            forecasts = [smoothed] * test_periods
        else:
            # For other methods, use simple average as fallback
            forecasts = [statistics.mean(train_data)] * test_periods

        # Calculate error metrics
        errors = [actual_test[i] - forecasts[i] for i in range(len(actual_test))]
        mae = statistics.mean([abs(e) for e in errors])  # Mean Absolute Error

        # Calculate MAPE (Mean Absolute Percentage Error)
        mape_errors = []
        for i in range(len(actual_test)):
            if actual_test[i] != 0:
                mape_errors.append(abs(errors[i] / actual_test[i]) * 100)

        mape = statistics.mean(mape_errors) if mape_errors else 0

        return {
            "mae": round(mae, 2),
            "mape": round(mape, 2),
            "rmse": round(math.sqrt(statistics.mean([e**2 for e in errors])), 2),
        }

    def _calculate_confidence_intervals(
        self, demand_series: list[float], forecasts: list[float], confidence_level: float
    ) -> dict[str, list[float]]:
        """Calculate confidence intervals for forecasts"""

        if len(demand_series) < 3:
            return {"lower": forecasts, "upper": forecasts}

        # Calculate standard error from historical residuals
        mean_demand = statistics.mean(demand_series)
        residuals = [x - mean_demand for x in demand_series]
        std_error = statistics.stdev(residuals) if len(residuals) > 1 else 0

        # Z-score for confidence level
        z_scores = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
        z_score = z_scores.get(confidence_level, 1.96)

        # Calculate intervals
        margin_of_error = z_score * std_error

        lower_bounds = [max(0, f - margin_of_error) for f in forecasts]
        upper_bounds = [f + margin_of_error for f in forecasts]

        return {
            "lower": [round(x, 2) for x in lower_bounds],
            "upper": [round(x, 2) for x in upper_bounds],
            "confidence_level": confidence_level,
        }

    def _calculate_historical_stats(self, demand_series: list[float]) -> dict[str, float]:
        """Calculate summary statistics for historical demand"""

        if not demand_series:
            return {}

        return {
            "total_periods": len(demand_series),
            "mean": round(statistics.mean(demand_series), 2),
            "median": round(statistics.median(demand_series), 2),
            "std_dev": round(statistics.stdev(demand_series), 2) if len(demand_series) > 1 else 0,
            "min": round(min(demand_series), 2),
            "max": round(max(demand_series), 2),
            "total_demand": round(sum(demand_series), 2),
        }

    def _generate_forecast_insights(
        self, historical_data: list[dict], forecast_result: dict, seasonal_analysis: dict
    ) -> dict[str, Any]:
        """Generate actionable insights from forecast analysis"""

        insights = {"recommendations": [], "risk_factors": [], "opportunities": []}

        forecasts = forecast_result["forecasts"]

        # Trend analysis
        if len(forecasts) > 1:
            forecast_trend = (forecasts[-1] - forecasts[0]) / len(forecasts)

            if forecast_trend > 0.1:
                insights["recommendations"].append(
                    _("Increasing demand trend detected - consider increasing stock levels")
                )
            elif forecast_trend < -0.1:
                insights["recommendations"].append(
                    _("Decreasing demand trend - optimize inventory to avoid excess stock")
                )

        # Seasonality insights
        if seasonal_analysis and seasonal_analysis.get("has_seasonality"):
            peak_month = seasonal_analysis.get("peak_month")
            low_month = seasonal_analysis.get("low_month")

            month_names = {
                1: _("January"),
                2: _("February"),
                3: _("March"),
                4: _("April"),
                5: _("May"),
                6: _("June"),
                7: _("July"),
                8: _("August"),
                9: _("September"),
                10: _("October"),
                11: _("November"),
                12: _("December"),
            }

            if peak_month and low_month:
                insights["recommendations"].append(
                    _(
                        "Peak demand in {peak_month}, low demand in {low_month} - plan inventory accordingly"
                    ).format(
                        peak_month=month_names.get(peak_month, peak_month),
                        low_month=month_names.get(low_month, low_month),
                    )
                )

        # Volatility assessment
        forecast_cv = (
            statistics.stdev(forecasts) / statistics.mean(forecasts) if statistics.mean(forecasts) > 0 else 0
        )

        if forecast_cv > 0.5:
            insights["risk_factors"].append(_("High demand volatility - maintain higher safety stock"))

        # Zero demand periods
        zero_periods = len([f for f in forecasts if f == 0])
        if zero_periods > len(forecasts) * 0.3:
            insights["risk_factors"].append(_("Frequent zero demand periods - consider obsolescence risk"))

        # Accuracy assessment
        accuracy_metrics = forecast_result.get("accuracy_metrics", {})
        mape = accuracy_metrics.get("mape", 0)

        if mape < 20:
            insights["opportunities"].append(_("High forecast accuracy - suitable for automated reordering"))
        elif mape > 50:
            insights["risk_factors"].append(_("Low forecast accuracy - manual review recommended"))

        return insights


# Forecast optimization and integration
class ForecastOptimizer:
    """Optimize inventory decisions based on demand forecasts"""

    @staticmethod
    def optimize_reorder_points_with_forecast(item_code: str, warehouse: str | None = None) -> dict[str, Any]:
        """Optimize reorder points using demand forecasts"""

        try:
            # Generate demand forecast
            forecasting_engine = DemandForecastingEngine()
            forecast_result = forecasting_engine.generate_demand_forecast(
                item_code, forecast_periods=6, include_seasonality=True
            )

            if not forecast_result["success"]:
                return forecast_result

            # Calculate dynamic reorder point
            forecasts = forecast_result["forecasts"]
            avg_forecast_demand = statistics.mean(forecasts)

            # Get current reorder point calculation
            from universal_workshop.parts_inventory.reorder_management import ReorderPointCalculator

            current_reorder = ReorderPointCalculator.calculate_reorder_point(item_code, warehouse)

            if not current_reorder["success"]:
                return current_reorder

            # Optimize based on forecast
            lead_time = current_reorder["lead_time_stats"]["average_lead_time"]
            safety_factor = 1.5

            # Dynamic safety stock based on forecast uncertainty
            forecast_std = statistics.stdev(forecasts) if len(forecasts) > 1 else 0
            dynamic_safety_stock = forecast_std * safety_factor

            # New reorder point = forecast demand * lead time + dynamic safety stock
            optimized_reorder_point = (avg_forecast_demand * lead_time) + dynamic_safety_stock

            return {
                "success": True,
                "item_code": item_code,
                "current_reorder_point": current_reorder["reorder_point"],
                "optimized_reorder_point": round(optimized_reorder_point, 2),
                "forecast_based_demand": round(avg_forecast_demand, 2),
                "dynamic_safety_stock": round(dynamic_safety_stock, 2),
                "improvement": round(optimized_reorder_point - current_reorder["reorder_point"], 2),
                "forecast_confidence": forecast_result.get("accuracy_metrics", {}),
                "recommendation": "Apply optimized reorder point"
                if abs(optimized_reorder_point - current_reorder["reorder_point"]) > 1
                else "Current reorder point is adequate",
            }

        except Exception as e:
            frappe.log_error(f"Reorder point optimization failed for {item_code}: {e!s}")
            return {"success": False, "error": str(e)}


# API Methods for frontend integration
@frappe.whitelist()
def generate_item_demand_forecast(
    item_code, forecast_periods=12, forecast_method="auto", warehouse=None, include_seasonality=True
):
    """API method to generate demand forecast for a specific item"""
    try:
        forecasting_engine = DemandForecastingEngine()
        result = forecasting_engine.generate_demand_forecast(
            item_code, int(forecast_periods), forecast_method, warehouse, bool(include_seasonality)
        )
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def optimize_reorder_with_forecast(item_code, warehouse=None):
    """API method to optimize reorder points using demand forecasts"""
    try:
        result = ForecastOptimizer.optimize_reorder_points_with_forecast(item_code, warehouse)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_forecast_dashboard_data(warehouse=None, top_items=20):
    """Get forecast dashboard data for multiple items"""
    try:
        # Get top items by consumption
        items_query = """
            SELECT
                sle.item_code,
                i.item_name,
                SUM(ABS(sle.actual_qty)) as total_consumption
            FROM `tabStock Ledger Entry` sle
            JOIN `tabItem` i ON sle.item_code = i.item_code
            WHERE sle.posting_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
            AND sle.actual_qty < 0
            {warehouse_condition}
            AND i.is_stock_item = 1
            AND i.disabled = 0
            GROUP BY sle.item_code, i.item_name
            ORDER BY total_consumption DESC
            LIMIT %(limit)s
        """.format(warehouse_condition="AND sle.warehouse = %(warehouse)s" if warehouse else "")

        top_items_data = frappe.db.sql(
            items_query, {"warehouse": warehouse, "limit": top_items}, as_dict=True
        )

        # Generate forecasts for top items
        forecasting_engine = DemandForecastingEngine()
        dashboard_data = []

        for item in top_items_data:
            forecast_result = forecasting_engine.generate_demand_forecast(
                item["item_code"], forecast_periods=6, warehouse=warehouse
            )

            if forecast_result["success"]:
                dashboard_data.append(
                    {
                        "item_code": item["item_code"],
                        "item_name": item["item_name"],
                        "total_consumption": item["total_consumption"],
                        "forecast_summary": {
                            "next_period_forecast": forecast_result["forecasts"][0],
                            "forecast_method": forecast_result["forecast_method"],
                            "has_seasonality": forecast_result["seasonal_analysis"].get(
                                "has_seasonality", False
                            )
                            if forecast_result["seasonal_analysis"]
                            else False,
                        },
                    }
                )

        return {"success": True, "dashboard_data": dashboard_data}

    except Exception as e:
        frappe.log_error(f"Forecast dashboard data failed: {e!s}")
        return {"success": False, "error": str(e)}
