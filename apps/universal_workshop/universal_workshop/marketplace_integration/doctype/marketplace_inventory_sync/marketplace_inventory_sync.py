# Copyright (c) 2024, Universal Workshop and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now, add_to_date
import json


class MarketplaceInventorySync(Document):
    def before_insert(self):
        """Set default values before inserting"""
        if not self.sync_date:
            self.sync_date = now()
        
        if not self.sync_status:
            self.sync_status = "Pending"
        
        if not self.retry_count:
            self.retry_count = 0
    
    def validate(self):
        """Validate the document"""
        self.validate_item_and_marketplace()
        self.validate_sync_data()
    
    def validate_item_and_marketplace(self):
        """Validate item exists and marketplace is configured"""
        if not frappe.db.exists("Item", self.item_code):
            frappe.throw(f"Item {self.item_code} does not exist")
        
        if not self.marketplace_sku:
            frappe.throw("Marketplace SKU is required")
    
    def validate_sync_data(self):
        """Validate sync quantities and prices"""
        if self.sync_type in ["Stock Only", "Stock and Price", "Full Sync"]:
            if self.sync_quantity is None:
                frappe.throw("Sync Quantity is required for stock synchronization")
        
        if self.sync_type in ["Price Only", "Stock and Price", "Full Sync"]:
            if self.sync_price is None:
                frappe.throw("Sync Price is required for price synchronization")
    
    def on_update(self):
        """Actions to perform when document is updated"""
        if self.sync_status == "Completed":
            self.set_next_sync_date()
    
    def set_next_sync_date(self):
        """Set next sync date based on sync frequency"""
        if self.auto_sync_enabled:
            # Default to daily sync, this could be configurable
            self.next_sync_date = add_to_date(now(), days=1)
    
    @frappe.whitelist()
    def execute_sync(self):
        """Execute the marketplace synchronization"""
        try:
            self.sync_status = "In Progress"
            self.save()
            
            # Get current item data
            item_doc = frappe.get_doc("Item", self.item_code)
            
            # Update current values
            if hasattr(item_doc, 'stock_qty'):
                self.current_stock = item_doc.stock_qty
            
            if hasattr(item_doc, 'standard_rate'):
                self.current_price = item_doc.standard_rate
            
            # Perform marketplace sync based on type
            sync_result = self.perform_marketplace_sync()
            
            if sync_result.get("success"):
                self.sync_status = "Completed"
                self.last_sync_date = now()
                self.error_message = None
                self.retry_count = 0
            else:
                self.sync_status = "Failed"
                self.error_message = sync_result.get("error", "Unknown error")
                self.retry_count += 1
            
            self.save()
            return sync_result
            
        except Exception as e:
            self.sync_status = "Failed"
            self.error_message = str(e)
            self.retry_count += 1
            self.save()
            frappe.log_error(f"Marketplace sync failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def perform_marketplace_sync(self):
        """Perform the actual marketplace synchronization"""
        try:
            # This is a placeholder for actual marketplace API integration
            # Each marketplace would have its own API implementation
            
            marketplace_config = self.get_marketplace_config()
            if not marketplace_config:
                return {"success": False, "error": "Marketplace configuration not found"}
            
            sync_data = {
                "sku": self.marketplace_sku,
                "sync_type": self.sync_type
            }
            
            if self.sync_type in ["Stock Only", "Stock and Price", "Full Sync"]:
                sync_data["quantity"] = self.sync_quantity
            
            if self.sync_type in ["Price Only", "Stock and Price", "Full Sync"]:
                sync_data["price"] = self.sync_price
            
            # Marketplace-specific sync logic would go here
            if self.marketplace == "Amazon":
                result = self.sync_to_amazon(sync_data)
            elif self.marketplace == "eBay":
                result = self.sync_to_ebay(sync_data)
            elif self.marketplace == "Noon":
                result = self.sync_to_noon(sync_data)
            else:
                result = self.sync_to_generic_marketplace(sync_data)
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_marketplace_config(self):
        """Get marketplace configuration"""
        # This would retrieve marketplace-specific configuration
        # like API keys, endpoints, etc.
        return {
            "api_key": "placeholder",
            "endpoint": f"https://api.{self.marketplace.lower()}.com",
            "enabled": True
        }
    
    def sync_to_amazon(self, sync_data):
        """Amazon marketplace sync implementation"""
        # Placeholder for Amazon MWS/SP-API integration
        return {"success": True, "message": "Amazon sync completed"}
    
    def sync_to_ebay(self, sync_data):
        """eBay marketplace sync implementation"""
        # Placeholder for eBay API integration
        return {"success": True, "message": "eBay sync completed"}
    
    def sync_to_noon(self, sync_data):
        """Noon marketplace sync implementation"""
        # Placeholder for Noon API integration
        return {"success": True, "message": "Noon sync completed"}
    
    def sync_to_generic_marketplace(self, sync_data):
        """Generic marketplace sync implementation"""
        # Placeholder for generic marketplace API integration
        return {"success": True, "message": "Generic marketplace sync completed"}
    
    @frappe.whitelist()
    def retry_sync(self):
        """Retry failed synchronization"""
        if self.retry_count >= 3:
            frappe.throw("Maximum retry attempts reached. Please check the error and try again.")
        
        return self.execute_sync()


@frappe.whitelist()
def bulk_sync_inventory(marketplace=None, item_codes=None):
    """Bulk synchronize inventory for multiple items"""
    filters = {"auto_sync_enabled": 1, "sync_status": ["in", ["Pending", "Failed"]]}
    
    if marketplace:
        filters["marketplace"] = marketplace
    
    if item_codes:
        filters["item_code"] = ["in", item_codes]
    
    sync_records = frappe.get_all("Marketplace Inventory Sync", filters=filters)
    
    results = []
    for record in sync_records:
        sync_doc = frappe.get_doc("Marketplace Inventory Sync", record.name)
        result = sync_doc.execute_sync()
        results.append({"record": record.name, "result": result})
    
    return results


@frappe.whitelist()
def get_sync_statistics():
    """Get synchronization statistics"""
    stats = frappe.db.sql("""
        SELECT 
            marketplace,
            sync_status,
            COUNT(*) as count,
            AVG(CASE WHEN sync_status = 'Failed' THEN retry_count ELSE 0 END) as avg_retries
        FROM `tabMarketplace Inventory Sync`
        GROUP BY marketplace, sync_status
    """, as_dict=True)
    
    return stats


def scheduled_inventory_sync():
    """Scheduled job to sync inventory automatically"""
    # Get all records due for sync
    due_syncs = frappe.get_all("Marketplace Inventory Sync", 
        filters={
            "auto_sync_enabled": 1,
            "next_sync_date": ["<=", now()],
            "sync_status": ["!=", "In Progress"]
        }
    )
    
    for sync_record in due_syncs:
        try:
            sync_doc = frappe.get_doc("Marketplace Inventory Sync", sync_record.name)
            sync_doc.execute_sync()
        except Exception as e:
            frappe.log_error(f"Scheduled sync failed for {sync_record.name}: {str(e)}")
    
    return len(due_syncs)