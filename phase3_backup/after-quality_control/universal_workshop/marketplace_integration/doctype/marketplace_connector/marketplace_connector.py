# -*- coding: utf-8 -*-
# Copyright (c) 2024, Universal Workshop and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
import requests
import json
from datetime import datetime, timedelta
import hashlib
import re
from typing import Dict, List, Optional, Any

class MarketplaceConnector(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields to Document class
    
    def validate(self):
        """Validate marketplace connector configuration"""
        self.validate_connector_name()
        self.validate_api_configuration()
        self.validate_sync_settings()
        self.validate_regional_compliance()
        self.set_default_values()
    
    def before_save(self):
        """Operations before saving the connector"""
        self.encrypt_sensitive_fields()
        self.update_metadata()
        self.validate_token_expiry()
    
    def after_insert(self):
        """Post-insertion operations"""
        self.log_activity("Marketplace Connector Created")
        self.initialize_default_mappings()
    
    def validate_connector_name(self):
        """Validate connector name requirements"""
        if not self.connector_name:
            frappe.throw(_("Connector name is required"))
        
        # Check for duplicate connector names
        existing = frappe.db.exists("Marketplace Connector", {
            "connector_name": self.connector_name,
            "name": ("!=", self.name or "")
        })
        if existing:
            frappe.throw(_("Connector name '{0}' already exists").format(self.connector_name))
        
        # Set Arabic name if not provided
        if not self.connector_name_ar and self.marketplace_platform:
            platform_ar_names = {
                "Dubizzle Motors": "دوبيزل موتورز",
                "OpenSooq": "أوبن سوق",
                "YallaMotor": "يالا موتور",
                "Autoline": "أوتولاين",
                "Motory": "موتوري"
            }
            if self.marketplace_platform in platform_ar_names:
                self.connector_name_ar = f"{platform_ar_names[self.marketplace_platform]} - {self.connector_name}"
    
    def validate_api_configuration(self):
        """Validate API connection settings"""
        if not self.api_endpoint:
            frappe.throw(_("API endpoint is required"))
        
        if not self.auth_method:
            frappe.throw(_("Authentication method is required"))
        
        # Validate authentication credentials based on method
        if self.auth_method == "API Key" and not self.api_key:
            frappe.throw(_("API Key is required for API Key authentication"))
        
        if self.auth_method == "OAuth 2.0":
            if not self.oauth_client_id or not self.oauth_client_secret:
                frappe.throw(_("OAuth Client ID and Secret are required"))
        
        if self.auth_method == "Bearer Token" and not self.access_token:
            frappe.throw(_("Access Token is required for Bearer Token authentication"))
        
        # Validate URL format
        if self.api_endpoint and not self.is_valid_url(self.api_endpoint):
            frappe.throw(_("Invalid API endpoint URL format"))
        
        if self.marketplace_url and not self.is_valid_url(self.marketplace_url):
            frappe.throw(_("Invalid marketplace URL format"))
    
    def validate_sync_settings(self):
        """Validate synchronization configuration"""
        if self.auto_sync_enabled and not self.sync_frequency:
            frappe.throw(_("Sync frequency is required when auto sync is enabled"))
        
        # Ensure at least one sync type is enabled
        if self.auto_sync_enabled:
            if not any([self.sync_products, self.sync_inventory, self.sync_orders, self.sync_pricing]):
                frappe.throw(_("At least one sync type must be enabled"))
        
        # Validate retry settings
        if self.retry_attempts and (self.retry_attempts < 1 or self.retry_attempts > 10):
            frappe.throw(_("Retry attempts must be between 1 and 10"))
        
        if self.retry_interval and (self.retry_interval < 1 or self.retry_interval > 60):
            frappe.throw(_("Retry interval must be between 1 and 60 minutes"))
    
    def validate_regional_compliance(self):
        """Validate regional compliance settings"""
        if self.platform_region == "Oman" and not self.vat_handling:
            frappe.throw(_("VAT handling configuration is required for Oman region"))
        
        # Validate email format for error notifications
        if self.error_notification_email and not self.is_valid_email(self.error_notification_email):
            frappe.throw(_("Invalid email format for error notifications"))
    
    def set_default_values(self):
        """Set default values for required fields"""
        if not self.created_by:
            self.created_by = frappe.session.user
        if not self.created_date:
            self.created_date = frappe.utils.today()
        if not self.status:
            self.status = "Draft"
        if not self.default_currency:
            self.default_currency = frappe.get_cached_value("Company", frappe.defaults.get_defaults().company, "default_currency") or "OMR"
        if not self.max_log_retention_days:
            self.max_log_retention_days = 30
        if not self.retry_attempts:
            self.retry_attempts = 3
        if not self.retry_interval:
            self.retry_interval = 5
    
    def encrypt_sensitive_fields(self):
        """Encrypt sensitive authentication data"""
        # Note: In production, use proper encryption
        # This is a placeholder for actual encryption implementation
        pass
    
    def update_metadata(self):
        """Update modification metadata"""
        self.modified_by = frappe.session.user
        self.modified_date = frappe.utils.today()
    
    def validate_token_expiry(self):
        """Check if OAuth token is expiring soon"""
        if self.auth_method == "OAuth 2.0" and self.token_expires_at:
            expiry_time = frappe.utils.get_datetime(self.token_expires_at)
            current_time = frappe.utils.now_datetime()
            time_until_expiry = expiry_time - current_time
            
            # Alert if token expires within 24 hours
            if time_until_expiry.total_seconds() < 86400:  # 24 hours
                self.log_activity("Token Expiring Soon", f"OAuth token expires at {self.token_expires_at}")
    
    def initialize_default_mappings(self):
        """Initialize default field mappings for the marketplace"""
        default_mappings = self.get_default_mappings()
        
        if not self.category_mapping:
            self.category_mapping = json.dumps(default_mappings.get("categories", {}))
        
        if not self.condition_grade_mapping:
            self.condition_grade_mapping = json.dumps(default_mappings.get("condition_grades", {}))
        
        if not self.attribute_mapping:
            self.attribute_mapping = json.dumps(default_mappings.get("attributes", {}))
        
        # Save the updated mappings
        self.save()
    
    def get_default_mappings(self) -> Dict[str, Any]:
        """Get default field mappings based on marketplace platform"""
        mappings = {
            "categories": {
                "Engine Parts": "engine-components",
                "Body Parts": "body-panels",
                "Electrical": "electrical-components",
                "Interior": "interior-accessories",
                "Exterior": "exterior-accessories"
            },
            "condition_grades": {
                "A": "like-new",
                "B": "excellent", 
                "C": "good",
                "D": "fair",
                "E": "poor",
                "F": "scrap-only"
            },
            "attributes": {
                "brand": "brand",
                "model": "model",
                "year": "year",
                "color": "color",
                "material": "material"
            }
        }
        
        # Platform-specific mappings
        if self.marketplace_platform == "Dubizzle Motors":
            mappings["categories"].update({
                "Transmission": "transmission-parts",
                "Suspension": "suspension-components"
            })
        
        return mappings
    
    @frappe.whitelist()
    def test_connection(self) -> Dict[str, Any]:
        """Test the API connection to the marketplace"""
        try:
            headers = self.get_auth_headers()
            test_endpoint = f"{self.api_endpoint.rstrip('/')}/health"
            
            response = requests.get(test_endpoint, headers=headers, timeout=30)
            
            if response.status_code == 200:
                self.status = "Connected"
                self.log_activity("Connection Test", "Connection successful")
                return {
                    "status": "success",
                    "message": _("Connection successful"),
                    "response_code": response.status_code
                }
            else:
                self.status = "Error"
                error_msg = f"HTTP {response.status_code}: {response.text}"
                self.log_activity("Connection Test Failed", error_msg)
                return {
                    "status": "error",
                    "message": error_msg,
                    "response_code": response.status_code
                }
        
        except Exception as e:
            self.status = "Error"
            error_msg = str(e)
            self.log_activity("Connection Test Error", error_msg)
            return {
                "status": "error",
                "message": error_msg
            }
        finally:
            self.save()
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers based on auth method"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"Universal Workshop ERP v2.0 ({self.connector_name})"
        }
        
        if self.auth_method == "API Key":
            headers["X-API-Key"] = self.get_password("api_key")
        
        elif self.auth_method == "Bearer Token":
            headers["Authorization"] = f"Bearer {self.get_password('access_token')}"
        
        elif self.auth_method == "Basic Auth":
            import base64
            credentials = f"{self.get_password('api_key')}:{self.get_password('api_secret')}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            headers["Authorization"] = f"Basic {encoded_credentials}"
        
        elif self.auth_method == "OAuth 2.0":
            if self.access_token:
                headers["Authorization"] = f"Bearer {self.get_password('access_token')}"
        
        return headers
    
    @frappe.whitelist()
    def refresh_oauth_token(self) -> Dict[str, Any]:
        """Refresh OAuth 2.0 access token"""
        if self.auth_method != "OAuth 2.0":
            return {"status": "error", "message": _("Not an OAuth 2.0 connector")}
        
        if not self.refresh_token:
            return {"status": "error", "message": _("No refresh token available")}
        
        try:
            token_endpoint = f"{self.api_endpoint.rstrip('/')}/oauth/token"
            data = {
                "grant_type": "refresh_token",
                "refresh_token": self.get_password("refresh_token"),
                "client_id": self.oauth_client_id,
                "client_secret": self.get_password("oauth_client_secret")
            }
            
            response = requests.post(token_endpoint, data=data, timeout=30)
            
            if response.status_code == 200:
                token_data = response.json()
                
                self.access_token = token_data.get("access_token")
                if "refresh_token" in token_data:
                    self.refresh_token = token_data.get("refresh_token")
                
                if "expires_in" in token_data:
                    expires_in = int(token_data["expires_in"])
                    self.token_expires_at = (datetime.now() + timedelta(seconds=expires_in)).isoformat()
                
                self.last_token_refresh = frappe.utils.now()
                self.save()
                
                self.log_activity("Token Refresh", "OAuth token refreshed successfully")
                return {"status": "success", "message": _("Token refreshed successfully")}
            
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                self.log_activity("Token Refresh Failed", error_msg)
                return {"status": "error", "message": error_msg}
        
        except Exception as e:
            error_msg = str(e)
            self.log_activity("Token Refresh Error", error_msg)
            return {"status": "error", "message": error_msg}
    
    @frappe.whitelist()
    def sync_to_marketplace(self, sync_type: str = "all") -> Dict[str, Any]:
        """Sync data to marketplace"""
        if not self.is_active:
            return {"status": "error", "message": _("Connector is not active")}
        
        if self.status != "Connected":
            return {"status": "error", "message": _("Connector is not connected")}
        
        sync_results = {}
        
        try:
            if sync_type in ["all", "products"] and self.sync_products:
                sync_results["products"] = self.sync_products_to_marketplace()
            
            if sync_type in ["all", "inventory"] and self.sync_inventory:
                sync_results["inventory"] = self.sync_inventory_to_marketplace()
            
            if sync_type in ["all", "pricing"] and self.sync_pricing:
                sync_results["pricing"] = self.sync_pricing_to_marketplace()
            
            if sync_type in ["all", "orders"] and self.sync_orders:
                sync_results["orders"] = self.sync_orders_from_marketplace()
            
            # Update sync statistics
            self.update_sync_statistics(sync_results)
            
            return {
                "status": "success",
                "message": _("Sync completed successfully"),
                "results": sync_results
            }
        
        except Exception as e:
            error_msg = str(e)
            self.log_activity("Sync Error", error_msg)
            return {"status": "error", "message": error_msg}
    
    def sync_products_to_marketplace(self) -> Dict[str, Any]:
        """Sync products from ERPNext to marketplace"""
        # Get extracted parts that are ready for listing
        extracted_parts = frappe.get_list("Scrap Vehicle Extracted Part",
            filters={
                "status": "Available for Sale",
                "marketplace_listed": 0
            },
            fields=["name", "part_name", "part_code", "final_grade", "storage_location",
                   "final_sale_price", "marketplace_title", "marketplace_description"]
        )
        
        successful_syncs = 0
        failed_syncs = 0
        
        for part in extracted_parts:
            try:
                listing_data = self.prepare_product_listing_data(part)
                result = self.post_product_to_marketplace(listing_data)
                
                if result.get("status") == "success":
                    # Update part as listed
                    frappe.db.set_value("Scrap Vehicle Extracted Part", part.name, {
                        "marketplace_listed": 1,
                        "marketplace_listing_id": result.get("listing_id"),
                        "marketplace_listing_date": frappe.utils.now()
                    })
                    successful_syncs += 1
                else:
                    failed_syncs += 1
                    self.log_activity("Product Sync Failed", f"Part {part.part_code}: {result.get('message')}")
            
            except Exception as e:
                failed_syncs += 1
                self.log_activity("Product Sync Error", f"Part {part.part_code}: {str(e)}")
        
        return {
            "total_processed": len(extracted_parts),
            "successful": successful_syncs,
            "failed": failed_syncs
        }
    
    def prepare_product_listing_data(self, part: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare product data for marketplace listing"""
        # Get part details
        part_doc = frappe.get_doc("Scrap Vehicle Extracted Part", part.name)
        
        # Get images
        images = []
        for i in range(1, 11):  # Up to 10 images
            image_field = f"image_{i}"
            if hasattr(part_doc, image_field) and getattr(part_doc, image_field):
                images.append(getattr(part_doc, image_field))
        
        # Map condition grade
        condition_mapping = json.loads(self.condition_grade_mapping or "{}")
        marketplace_condition = condition_mapping.get(part_doc.final_grade, "used")
        
        listing_data = {
            "title": part_doc.marketplace_title or part_doc.part_name,
            "description": part_doc.marketplace_description or part_doc.part_description,
            "price": float(part_doc.final_sale_price or 0),
            "currency": self.default_currency,
            "condition": marketplace_condition,
            "category": self.map_category(part_doc.part_category),
            "brand": part_doc.original_manufacturer,
            "part_number": part_doc.part_code,
            "compatibility": self.get_part_compatibility(part_doc),
            "images": images,
            "location": part_doc.storage_location,
            "seller_notes": part_doc.assessment_notes
        }
        
        # Add Arabic content if supported
        if "ar" in (self.supported_languages or ""):
            listing_data.update({
                "title_ar": part_doc.part_name_ar,
                "description_ar": part_doc.part_description_ar
            })
        
        return listing_data
    
    def post_product_to_marketplace(self, listing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Post product listing to marketplace API"""
        try:
            headers = self.get_auth_headers()
            endpoint = f"{self.api_endpoint.rstrip('/')}/listings"
            
            response = requests.post(endpoint, json=listing_data, headers=headers, timeout=60)
            
            if response.status_code in [200, 201]:
                result = response.json()
                return {
                    "status": "success",
                    "listing_id": result.get("id") or result.get("listing_id"),
                    "url": result.get("url"),
                    "message": _("Product listed successfully")
                }
            else:
                return {
                    "status": "error",
                    "message": f"HTTP {response.status_code}: {response.text}"
                }
        
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def sync_inventory_to_marketplace(self) -> Dict[str, Any]:
        """Sync inventory levels to marketplace"""
        # Implementation for inventory sync
        return {"message": "Inventory sync not yet implemented"}
    
    def sync_pricing_to_marketplace(self) -> Dict[str, Any]:
        """Sync pricing updates to marketplace"""
        # Implementation for pricing sync
        return {"message": "Pricing sync not yet implemented"}
    
    def sync_orders_from_marketplace(self) -> Dict[str, Any]:
        """Sync orders from marketplace to ERPNext"""
        # Implementation for order sync
        return {"message": "Order sync not yet implemented"}
    
    def update_sync_statistics(self, sync_results: Dict[str, Any]):
        """Update synchronization statistics"""
        # Update counters and success rates
        total_synced = sum([r.get("successful", 0) for r in sync_results.values() if isinstance(r, dict)])
        self.total_products_synced = (self.total_products_synced or 0) + total_synced
        self.last_successful_sync = frappe.utils.now()
        
        # Calculate success rate
        total_attempted = sum([r.get("total_processed", 0) for r in sync_results.values() if isinstance(r, dict)])
        if total_attempted > 0:
            success_rate = (total_synced / total_attempted) * 100
            # Weighted average with previous success rate
            current_rate = self.sync_success_rate or 0
            self.sync_success_rate = (current_rate * 0.7) + (success_rate * 0.3)
        
        self.save()
    
    def map_category(self, erpnext_category: str) -> str:
        """Map ERPNext category to marketplace category"""
        category_mapping = json.loads(self.category_mapping or "{}")
        return category_mapping.get(erpnext_category, "automotive-parts")
    
    def get_part_compatibility(self, part_doc) -> List[Dict[str, str]]:
        """Get vehicle compatibility information"""
        # Get vehicle information from the scrap vehicle
        if part_doc.scrap_vehicle:
            vehicle_doc = frappe.get_doc("Scrap Vehicle", part_doc.scrap_vehicle)
            return [{
                "make": vehicle_doc.vehicle_make,
                "model": vehicle_doc.vehicle_model,
                "year": str(vehicle_doc.vehicle_year),
                "engine": vehicle_doc.engine_type
            }]
        return []
    
    def log_activity(self, activity_type: str, details: str = ""):
        """Log connector activity"""
        frappe.get_doc({
            "doctype": "Marketplace Sync Log",
            "connector": self.name,
            "activity_type": activity_type,
            "details": details,
            "timestamp": frappe.utils.now()
        }).insert(ignore_permissions=True)
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Validate URL format"""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return url_pattern.match(url) is not None
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validate email format"""
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        return email_pattern.match(email) is not None 