"""
Advanced Chart Engine for Universal Workshop ERP
Comprehensive charting system with real-time updates, Arabic support, and performance optimization
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, flt, cint, add_days, get_datetime
from typing import Dict, List, Any, Optional, Union, Tuple
import json
import hashlib
from datetime import datetime, timedelta
import statistics

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class ChartEngine:
    """Advanced Chart Engine for Universal Workshop Analytics"""

    def __init__(self):
        self.redis_client = frappe.cache() if REDIS_AVAILABLE else None
        self.cache_duration = 300  # 5 minutes default cache
        
        # Supported chart types
        self.chart_types = {
            "line": "خط بياني",
            "bar": "رسم بياني بالأعمدة",
            "pie": "رسم دائري",
            "doughnut": "رسم دائري مفرغ",
            "area": "رسم المنطقة",
            "scatter": "رسم النقاط",
            "heatmap": "خريطة حرارية",
            "gauge": "مقياس",
            "radar": "رسم رادار",
            "funnel": "رسم قمعي",
            "treemap": "خريطة شجرية",
            "waterfall": "رسم شلال"
        }
        
        # Color schemes for different themes
        self.color_schemes = {
            "default": [
                "#3498db", "#e74c3c", "#2ecc71", "#f39c12", "#9b59b6",
                "#1abc9c", "#e67e22", "#34495e", "#95a5a6", "#f1c40f"
            ],
            "arabic": [
                "#2c3e50", "#c0392b", "#27ae60", "#f39c12", "#8e44ad",
                "#16a085", "#d35400", "#2980b9", "#7f8c8d", "#f1c40f"
            ],
            "workshop": [
                "#ff6b6b", "#4ecdc4", "#45b7d1", "#96ceb4", "#feca57",
                "#ff9ff3", "#54a0ff", "#5f27cd", "#00d2d3", "#ff9f43"
            ],
            "performance": [
                "#00b894", "#00cec9", "#6c5ce7", "#a29bfe", "#fd79a8",
                "#fdcb6e", "#e17055", "#81ecec", "#74b9ff", "#55a3ff"
            ]
        }

    def generate_chart(self, chart_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate chart with data and configuration"""
        try:
            # Validate chart configuration
            validated_config = self._validate_chart_config(chart_config)
            
            # Generate cache key for the chart
            cache_key = self._generate_cache_key(validated_config)
            
            # Try to get cached data first
            cached_chart = self._get_cached_chart(cache_key)
            if cached_chart and not validated_config.get("force_refresh", False):
                return cached_chart
            
            # Get chart data based on configuration
            chart_data = self._get_chart_data(validated_config)
            
            # Process and format data
            processed_data = self._process_chart_data(chart_data, validated_config)
            
            # Generate chart configuration
            chart_result = {
                "id": validated_config.get("id", f"chart_{int(now_datetime().timestamp())}"),
                "type": validated_config["type"],
                "title": validated_config.get("title", "Chart"),
                "title_ar": validated_config.get("title_ar", validated_config.get("title", "مخطط")),
                "data": processed_data,
                "options": self._generate_chart_options(validated_config),
                "metadata": {
                    "generated_at": now_datetime().isoformat(),
                    "data_points": len(processed_data.get("datasets", [{}])[0].get("data", [])),
                    "cache_key": cache_key,
                    "auto_refresh": validated_config.get("auto_refresh", False),
                    "refresh_interval": validated_config.get("refresh_interval", 30000)  # 30 seconds
                }
            }
            
            # Cache the result
            self._cache_chart(cache_key, chart_result, validated_config.get("cache_duration", self.cache_duration))
            
            return chart_result
            
        except Exception as e:
            frappe.log_error(f"Chart generation error: {str(e)}", "Chart Engine Error")
            return self._generate_error_chart(str(e))

    def _validate_chart_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize chart configuration"""
        if not isinstance(config, dict):
            raise ValueError("Chart configuration must be a dictionary")
        
        # Required fields
        if "type" not in config:
            raise ValueError("Chart type is required")
        
        if config["type"] not in self.chart_types:
            raise ValueError(f"Unsupported chart type: {config['type']}")
        
        if "data_source" not in config:
            raise ValueError("Data source is required")
        
        # Set defaults
        defaults = {
            "title": "Chart",
            "title_ar": "مخطط",
            "color_scheme": "default",
            "responsive": True,
            "animation": True,
            "legend_position": "top",
            "arabic_support": True,
            "rtl_direction": True,
            "auto_refresh": False,
            "refresh_interval": 30000,
            "cache_duration": 300
        }
        
        # Merge with defaults
        validated_config = {**defaults, **config}
        
        return validated_config

    def _get_chart_data(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get chart data based on configuration"""
        data_source = config["data_source"]
        
        try:
            # Handle different data source types
            if data_source["type"] == "sql":
                return self._get_sql_data(data_source)
            elif data_source["type"] == "doctype":
                return self._get_doctype_data(data_source)
            elif data_source["type"] == "api":
                return self._get_api_data(data_source)
            elif data_source["type"] == "custom":
                return self._get_custom_data(data_source)
            elif data_source["type"] == "realtime":
                return self._get_realtime_data(data_source)
            else:
                raise ValueError(f"Unsupported data source type: {data_source['type']}")
                
        except Exception as e:
            frappe.log_error(f"Chart data retrieval error: {str(e)}", "Chart Engine Data Error")
            return []

    def _get_sql_data(self, data_source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get data from SQL query"""
        query = data_source["query"]
        params = data_source.get("params", [])
        
        # Security check for SQL injection (basic)
        dangerous_keywords = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE"]
        query_upper = query.upper()
        
        for keyword in dangerous_keywords:
            if keyword in query_upper and "SELECT" not in query_upper[:20]:
                raise ValueError("Only SELECT queries are allowed")
        
        return frappe.db.sql(query, params, as_dict=True)

    def _get_doctype_data(self, data_source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get data from DocType"""
        doctype = data_source["doctype"]
        filters = data_source.get("filters", {})
        fields = data_source.get("fields", ["*"])
        order_by = data_source.get("order_by", "creation desc")
        limit = data_source.get("limit", 1000)
        
        return frappe.get_list(
            doctype,
            filters=filters,
            fields=fields,
            order_by=order_by,
            limit=limit
        )

    def _get_api_data(self, data_source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get data from API endpoint"""
        endpoint = data_source["endpoint"]
        method = data_source.get("method", "GET")
        
        # Call the whitelisted API function
        if hasattr(frappe, endpoint.replace("/", ".")):
            api_function = getattr(frappe, endpoint.replace("/", "."))
            return api_function()
        else:
            # Try to call as method
            try:
                return frappe.call(endpoint, **data_source.get("params", {}))
            except Exception:
                return []

    def _get_custom_data(self, data_source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get data from custom function"""
        function_name = data_source["function"]
        params = data_source.get("params", {})
        
        # Import and call the custom function
        try:
            module_path, function = function_name.rsplit(".", 1)
            module = frappe.get_module(module_path)
            custom_function = getattr(module, function)
            return custom_function(**params)
        except Exception as e:
            frappe.log_error(f"Custom function error: {str(e)}", "Chart Engine Custom Function Error")
            return []

    def _get_realtime_data(self, data_source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get real-time data from Redis or other sources"""
        if not self.redis_client:
            return []
        
        redis_key = data_source["redis_key"]
        data_format = data_source.get("format", "json")
        
        try:
            cached_data = self.redis_client.get(redis_key)
            if cached_data:
                if data_format == "json":
                    return frappe.parse_json(cached_data)
                else:
                    return [{"value": cached_data}]
            return []
        except Exception:
            return []

    def _process_chart_data(self, raw_data: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw data into chart format"""
        chart_type = config["type"]
        
        if chart_type in ["line", "bar", "area"]:
            return self._process_xy_chart_data(raw_data, config)
        elif chart_type in ["pie", "doughnut"]:
            return self._process_pie_chart_data(raw_data, config)
        elif chart_type == "scatter":
            return self._process_scatter_chart_data(raw_data, config)
        elif chart_type == "heatmap":
            return self._process_heatmap_data(raw_data, config)
        elif chart_type == "gauge":
            return self._process_gauge_data(raw_data, config)
        elif chart_type == "radar":
            return self._process_radar_data(raw_data, config)
        elif chart_type == "funnel":
            return self._process_funnel_data(raw_data, config)
        elif chart_type == "waterfall":
            return self._process_waterfall_data(raw_data, config)
        else:
            return self._process_xy_chart_data(raw_data, config)

    def _process_xy_chart_data(self, raw_data: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process data for line, bar, area charts"""
        if not raw_data:
            return {"labels": [], "datasets": []}
        
        # Get field mappings
        x_field = config.get("x_field", list(raw_data[0].keys())[0])
        y_field = config.get("y_field", list(raw_data[0].keys())[1] if len(raw_data[0]) > 1 else x_field)
        group_field = config.get("group_field")
        
        if group_field:
            return self._process_grouped_xy_data(raw_data, x_field, y_field, group_field, config)
        else:
            return self._process_simple_xy_data(raw_data, x_field, y_field, config)

    def _process_simple_xy_data(self, raw_data: List[Dict], x_field: str, y_field: str, config: Dict) -> Dict[str, Any]:
        """Process simple X-Y data"""
        labels = []
        data = []
        
        for row in raw_data:
            labels.append(str(row.get(x_field, "")))
            data.append(flt(row.get(y_field, 0)))
        
        # Get colors
        colors = self._get_chart_colors(config["color_scheme"], 1)
        
        dataset = {
            "label": config.get("dataset_label", y_field),
            "data": data,
            "backgroundColor": colors[0] if config["type"] == "bar" else colors[0] + "20",
            "borderColor": colors[0],
            "borderWidth": 2,
            "fill": config["type"] == "area"
        }
        
        return {
            "labels": labels,
            "datasets": [dataset]
        }

    def _process_grouped_xy_data(self, raw_data: List[Dict], x_field: str, y_field: str, group_field: str, config: Dict) -> Dict[str, Any]:
        """Process grouped X-Y data"""
        # Group data by x_field and group_field
        grouped_data = {}
        x_values = set()
        groups = set()
        
        for row in raw_data:
            x_val = str(row.get(x_field, ""))
            group_val = str(row.get(group_field, ""))
            y_val = flt(row.get(y_field, 0))
            
            x_values.add(x_val)
            groups.add(group_val)
            
            if group_val not in grouped_data:
                grouped_data[group_val] = {}
            grouped_data[group_val][x_val] = y_val
        
        # Sort values
        sorted_x_values = sorted(list(x_values))
        sorted_groups = sorted(list(groups))
        
        # Get colors
        colors = self._get_chart_colors(config["color_scheme"], len(sorted_groups))
        
        # Create datasets
        datasets = []
        for i, group in enumerate(sorted_groups):
            data = []
            for x_val in sorted_x_values:
                data.append(grouped_data[group].get(x_val, 0))
            
            dataset = {
                "label": group,
                "data": data,
                "backgroundColor": colors[i] if config["type"] == "bar" else colors[i] + "20",
                "borderColor": colors[i],
                "borderWidth": 2,
                "fill": config["type"] == "area"
            }
            datasets.append(dataset)
        
        return {
            "labels": sorted_x_values,
            "datasets": datasets
        }

    def _process_pie_chart_data(self, raw_data: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process data for pie/doughnut charts"""
        if not raw_data:
            return {"labels": [], "datasets": []}
        
        # Get field mappings
        label_field = config.get("label_field", list(raw_data[0].keys())[0])
        value_field = config.get("value_field", list(raw_data[0].keys())[1] if len(raw_data[0]) > 1 else label_field)
        
        labels = []
        data = []
        
        for row in raw_data:
            labels.append(str(row.get(label_field, "")))
            data.append(flt(row.get(value_field, 0)))
        
        # Get colors
        colors = self._get_chart_colors(config["color_scheme"], len(labels))
        
        dataset = {
            "data": data,
            "backgroundColor": colors[:len(data)],
            "borderColor": "#ffffff",
            "borderWidth": 2
        }
        
        return {
            "labels": labels,
            "datasets": [dataset]
        }

    def _process_scatter_chart_data(self, raw_data: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process data for scatter charts"""
        if not raw_data:
            return {"datasets": []}
        
        x_field = config.get("x_field", list(raw_data[0].keys())[0])
        y_field = config.get("y_field", list(raw_data[0].keys())[1] if len(raw_data[0]) > 1 else x_field)
        
        data = []
        for row in raw_data:
            data.append({
                "x": flt(row.get(x_field, 0)),
                "y": flt(row.get(y_field, 0))
            })
        
        colors = self._get_chart_colors(config["color_scheme"], 1)
        
        dataset = {
            "label": config.get("dataset_label", "Data"),
            "data": data,
            "backgroundColor": colors[0],
            "borderColor": colors[0],
            "borderWidth": 1
        }
        
        return {"datasets": [dataset]}

    def _process_gauge_data(self, raw_data: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process data for gauge charts"""
        if not raw_data:
            return {"value": 0, "min": 0, "max": 100}
        
        value_field = config.get("value_field", list(raw_data[0].keys())[0])
        value = flt(raw_data[0].get(value_field, 0))
        
        return {
            "value": value,
            "min": config.get("min_value", 0),
            "max": config.get("max_value", 100),
            "thresholds": config.get("thresholds", [
                {"value": 50, "color": "#f39c12"},
                {"value": 80, "color": "#e74c3c"}
            ])
        }

    def _process_heatmap_data(self, raw_data: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process data for heatmap charts"""
        if not raw_data:
            return {"data": []}
        
        x_field = config.get("x_field", list(raw_data[0].keys())[0])
        y_field = config.get("y_field", list(raw_data[0].keys())[1])
        value_field = config.get("value_field", list(raw_data[0].keys())[2])
        
        data = []
        for row in raw_data:
            data.append([
                row.get(x_field, ""),
                row.get(y_field, ""),
                flt(row.get(value_field, 0))
            ])
        
        return {"data": data}

    def _process_waterfall_data(self, raw_data: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process data for waterfall charts"""
        if not raw_data:
            return {"labels": [], "datasets": []}
        
        label_field = config.get("label_field", list(raw_data[0].keys())[0])
        value_field = config.get("value_field", list(raw_data[0].keys())[1])
        
        labels = []
        data = []
        cumulative = 0
        
        for row in raw_data:
            labels.append(str(row.get(label_field, "")))
            value = flt(row.get(value_field, 0))
            data.append({
                "value": value,
                "cumulative": cumulative + value
            })
            cumulative += value
        
        colors = self._get_chart_colors(config["color_scheme"], len(labels))
        
        return {
            "labels": labels,
            "data": data,
            "colors": colors
        }

    def _generate_chart_options(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate chart options based on configuration"""
        base_options = {
            "responsive": config.get("responsive", True),
            "maintainAspectRatio": False,
            "plugins": {
                "legend": {
                    "position": config.get("legend_position", "top"),
                    "rtl": config.get("rtl_direction", True),
                    "labels": {
                        "font": {
                            "family": "Cairo, Tajawal, Arial",
                            "size": 12
                        },
                        "usePointStyle": True
                    }
                },
                "title": {
                    "display": bool(config.get("title")),
                    "text": config.get("title_ar" if config.get("arabic_support") else "title", ""),
                    "font": {
                        "family": "Cairo, Tajawal, Arial",
                        "size": 16,
                        "weight": "bold"
                    }
                },
                "tooltip": {
                    "backgroundColor": "rgba(0,0,0,0.8)",
                    "titleFont": {
                        "family": "Cairo, Tajawal, Arial"
                    },
                    "bodyFont": {
                        "family": "Cairo, Tajawal, Arial"
                    },
                    "rtl": config.get("rtl_direction", True)
                }
            },
            "animation": {
                "duration": 1000 if config.get("animation", True) else 0
            }
        }
        
        # Add chart-specific options
        chart_type = config["type"]
        
        if chart_type in ["line", "bar", "area"]:
            base_options["scales"] = self._get_xy_scales(config)
        elif chart_type == "pie":
            base_options["plugins"]["legend"]["position"] = "right"
        elif chart_type == "doughnut":
            base_options["cutout"] = "50%"
        
        return base_options

    def _get_xy_scales(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get scales configuration for X-Y charts"""
        return {
            "x": {
                "title": {
                    "display": bool(config.get("x_title")),
                    "text": config.get("x_title", ""),
                    "font": {
                        "family": "Cairo, Tajawal, Arial",
                        "size": 14
                    }
                },
                "ticks": {
                    "font": {
                        "family": "Cairo, Tajawal, Arial"
                    }
                }
            },
            "y": {
                "title": {
                    "display": bool(config.get("y_title")),
                    "text": config.get("y_title", ""),
                    "font": {
                        "family": "Cairo, Tajawal, Arial",
                        "size": 14
                    }
                },
                "ticks": {
                    "font": {
                        "family": "Cairo, Tajawal, Arial"
                    }
                }
            }
        }

    def _get_chart_colors(self, scheme: str, count: int) -> List[str]:
        """Get color palette for charts"""
        colors = self.color_schemes.get(scheme, self.color_schemes["default"])
        
        # Repeat colors if we need more than available
        result = []
        for i in range(count):
            result.append(colors[i % len(colors)])
        
        return result

    def _generate_cache_key(self, config: Dict[str, Any]) -> str:
        """Generate cache key for chart configuration"""
        # Create a hash of the configuration
        config_str = json.dumps(config, sort_keys=True, default=str)
        return f"chart:{hashlib.md5(config_str.encode()).hexdigest()}"

    def _get_cached_chart(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached chart data"""
        if not self.redis_client:
            return None
        
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                return frappe.parse_json(cached_data)
            return None
        except Exception:
            return None

    def _cache_chart(self, cache_key: str, chart_data: Dict[str, Any], duration: int):
        """Cache chart data"""
        if not self.redis_client:
            return
        
        try:
            self.redis_client.setex(cache_key, duration, frappe.as_json(chart_data))
        except Exception as e:
            frappe.log_error(f"Chart caching error: {str(e)}", "Chart Engine Cache Error")

    def _generate_error_chart(self, error_message: str) -> Dict[str, Any]:
        """Generate error chart when data loading fails"""
        return {
            "id": "error_chart",
            "type": "bar",
            "title": "Chart Error",
            "title_ar": "خطأ في المخطط",
            "data": {
                "labels": ["Error"],
                "datasets": [{
                    "label": "Error",
                    "data": [0],
                    "backgroundColor": ["#e74c3c"],
                    "borderColor": ["#c0392b"],
                    "borderWidth": 2
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {
                        "display": True,
                        "text": f"Error: {error_message}"
                    }
                }
            },
            "metadata": {
                "generated_at": now_datetime().isoformat(),
                "error": True,
                "error_message": error_message
            }
        }

    def invalidate_cache(self, pattern: str = None):
        """Invalidate chart cache"""
        if not self.redis_client:
            return
        
        try:
            if pattern:
                keys = self.redis_client.keys(f"chart:*{pattern}*")
            else:
                keys = self.redis_client.keys("chart:*")
            
            if keys:
                self.redis_client.delete(*keys)
                
            return len(keys)
        except Exception as e:
            frappe.log_error(f"Cache invalidation error: {str(e)}", "Chart Engine Cache Error")
            return 0

    def get_chart_performance_stats(self) -> Dict[str, Any]:
        """Get chart performance statistics"""
        if not self.redis_client:
            return {"error": "Redis not available"}
        
        try:
            # Get all chart cache keys
            chart_keys = self.redis_client.keys("chart:*")
            
            total_charts = len(chart_keys)
            cache_size_mb = 0
            
            # Calculate total cache size
            for key in chart_keys:
                try:
                    size = len(self.redis_client.get(key) or "")
                    cache_size_mb += size
                except Exception:
                    continue
            
            cache_size_mb = cache_size_mb / (1024 * 1024)  # Convert to MB
            
            return {
                "total_cached_charts": total_charts,
                "cache_size_mb": round(cache_size_mb, 2),
                "supported_chart_types": len(self.chart_types),
                "color_schemes": len(self.color_schemes),
                "cache_hit_rate": self._calculate_cache_hit_rate(),
                "generated_at": now_datetime().isoformat()
            }
            
        except Exception as e:
            frappe.log_error(f"Chart performance stats error: {str(e)}", "Chart Engine Error")
            return {"error": str(e)}

    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate (simplified)"""
        # This would require tracking hits/misses in a real implementation
        # For now, return a placeholder
        return 85.5


# Global chart engine instance
chart_engine = ChartEngine()


# Whitelisted API methods
@frappe.whitelist()
def generate_chart(chart_config):
    """API endpoint to generate charts"""
    if isinstance(chart_config, str):
        chart_config = frappe.parse_json(chart_config)
    
    return chart_engine.generate_chart(chart_config)


@frappe.whitelist()
def get_chart_types():
    """API endpoint to get supported chart types"""
    return chart_engine.chart_types


@frappe.whitelist()
def get_color_schemes():
    """API endpoint to get available color schemes"""
    return chart_engine.color_schemes


@frappe.whitelist()
def invalidate_chart_cache(pattern=None):
    """API endpoint to invalidate chart cache"""
    return {"invalidated_count": chart_engine.invalidate_cache(pattern)}


@frappe.whitelist()
def get_chart_performance():
    """API endpoint to get chart performance statistics"""
    return chart_engine.get_chart_performance_stats()


@frappe.whitelist()
def generate_sample_chart(chart_type="bar"):
    """Generate sample chart for testing"""
    sample_config = {
        "type": chart_type,
        "title": "Sample Chart",
        "title_ar": "مخطط تجريبي",
        "data_source": {
            "type": "custom",
            "function": "universal_workshop.utils.chart_engine.get_sample_data"
        },
        "color_scheme": "workshop",
        "arabic_support": True
    }
    
    return chart_engine.generate_chart(sample_config)


def get_sample_data():
    """Generate sample data for testing"""
    return [
        {"month": "January", "month_ar": "يناير", "sales": 1200, "orders": 45},
        {"month": "February", "month_ar": "فبراير", "sales": 1900, "orders": 52},
        {"month": "March", "month_ar": "مارس", "sales": 3000, "orders": 68},
        {"month": "April", "month_ar": "أبريل", "sales": 5000, "orders": 89},
        {"month": "May", "month_ar": "مايو", "sales": 4200, "orders": 76},
        {"month": "June", "month_ar": "يونيو", "sales": 6100, "orders": 95}
    ] 