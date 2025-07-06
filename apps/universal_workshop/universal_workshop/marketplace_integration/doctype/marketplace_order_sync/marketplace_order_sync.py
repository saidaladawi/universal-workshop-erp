# Copyright (c) 2024, Universal Workshop and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now, flt
import json


class MarketplaceOrderSync(Document):
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
        self.validate_marketplace_order()
        self.calculate_net_amount()
    
    def validate_marketplace_order(self):
        """Validate marketplace order data"""
        if not self.marketplace_order_id:
            frappe.throw("Marketplace Order ID is required")
        
        # Check for duplicate marketplace order
        existing = frappe.db.exists("Marketplace Order Sync", {
            "marketplace": self.marketplace,
            "marketplace_order_id": self.marketplace_order_id,
            "name": ["!=", self.name]
        })
        
        if existing:
            frappe.throw(f"Order {self.marketplace_order_id} from {self.marketplace} already exists")
    
    def calculate_net_amount(self):
        """Calculate net amount after marketplace fees"""
        if self.total_amount and self.marketplace_fee:
            self.net_amount = flt(self.total_amount) - flt(self.marketplace_fee)
        elif self.total_amount:
            self.net_amount = self.total_amount
    
    def on_update(self):
        """Actions to perform when document is updated"""
        if self.sync_status == "Completed" and not self.sales_order:
            self.create_sales_documents()
    
    @frappe.whitelist()
    def execute_sync(self):
        """Execute the marketplace order synchronization"""
        try:
            self.sync_status = "In Progress"
            self.save()
            
            # Fetch order details from marketplace
            order_data = self.fetch_marketplace_order()
            
            if order_data.get("success"):
                # Update order details
                self.update_order_details(order_data.get("data", {}))
                
                # Create or update ERP documents
                if self.should_create_sales_order():
                    self.create_sales_documents()
                
                self.sync_status = "Completed"
                self.last_sync_date = now()
                self.error_message = None
                self.retry_count = 0
            else:
                self.sync_status = "Failed"
                self.error_message = order_data.get("error", "Failed to fetch order data")
                self.retry_count += 1
            
            self.save()
            return {"success": order_data.get("success"), "message": order_data.get("message")}
            
        except Exception as e:
            self.sync_status = "Failed"
            self.error_message = str(e)
            self.retry_count += 1
            self.save()
            frappe.log_error(f"Marketplace order sync failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def fetch_marketplace_order(self):
        """Fetch order details from marketplace API"""
        try:
            marketplace_config = self.get_marketplace_config()
            if not marketplace_config:
                return {"success": False, "error": "Marketplace configuration not found"}
            
            # Marketplace-specific order fetching
            if self.marketplace == "Amazon":
                result = self.fetch_amazon_order()
            elif self.marketplace == "eBay":
                result = self.fetch_ebay_order()
            elif self.marketplace == "Noon":
                result = self.fetch_noon_order()
            else:
                result = self.fetch_generic_marketplace_order()
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def fetch_amazon_order(self):
        """Fetch order from Amazon API"""
        # Placeholder for Amazon SP-API integration
        return {
            "success": True,
            "data": {
                "order_status": "Shipped",
                "total_amount": 150.00,
                "marketplace_fee": 15.00,
                "customer_name": "John Doe",
                "customer_email": "john@example.com"
            }
        }
    
    def fetch_ebay_order(self):
        """Fetch order from eBay API"""
        # Placeholder for eBay API integration
        return {"success": True, "data": {}}
    
    def fetch_noon_order(self):
        """Fetch order from Noon API"""
        # Placeholder for Noon API integration
        return {"success": True, "data": {}}
    
    def fetch_generic_marketplace_order(self):
        """Fetch order from generic marketplace API"""
        return {"success": True, "data": {}}
    
    def update_order_details(self, order_data):
        """Update order details from marketplace data"""
        if order_data.get("order_status"):
            self.order_status = order_data["order_status"]
        
        if order_data.get("total_amount"):
            self.total_amount = order_data["total_amount"]
        
        if order_data.get("marketplace_fee"):
            self.marketplace_fee = order_data["marketplace_fee"]
        
        if order_data.get("customer_name"):
            self.customer_name = order_data["customer_name"]
        
        if order_data.get("customer_email"):
            self.customer_email = order_data["customer_email"]
        
        if order_data.get("shipping_address"):
            self.shipping_address = order_data["shipping_address"]
        
        if order_data.get("tracking_number"):
            self.tracking_number = order_data["tracking_number"]
        
        self.calculate_net_amount()
    
    def should_create_sales_order(self):
        """Check if sales order should be created"""
        return (
            self.order_status in ["Confirmed", "Shipped", "Delivered"] and
            not self.sales_order and
            self.total_amount > 0
        )
    
    def create_sales_documents(self):
        """Create sales order and related documents"""
        try:
            # Find or create customer
            customer = self.get_or_create_customer()
            
            # Create sales order
            sales_order = self.create_sales_order(customer)
            
            if sales_order:
                self.sales_order = sales_order.name
                
                # Create sales invoice if order is delivered
                if self.order_status in ["Delivered"]:
                    invoice = self.create_sales_invoice(sales_order)
                    if invoice:
                        self.invoice_number = invoice.name
                
                # Create delivery note if order is shipped
                if self.order_status in ["Shipped", "Delivered"]:
                    delivery_note = self.create_delivery_note(sales_order)
                    if delivery_note:
                        self.delivery_note = delivery_note.name
            
        except Exception as e:
            frappe.log_error(f"Failed to create sales documents: {str(e)}")
    
    def get_or_create_customer(self):
        """Get existing customer or create new one"""
        if not self.customer_name:
            return None
        
        # Try to find existing customer by email
        if self.customer_email:
            existing_customer = frappe.db.get_value("Customer", 
                {"email_id": self.customer_email}, "name")
            if existing_customer:
                return existing_customer
        
        # Create new customer
        customer_doc = frappe.new_doc("Customer")
        customer_doc.customer_name = self.customer_name
        customer_doc.customer_type = "Individual"
        customer_doc.customer_group = "Commercial"  # Default group
        customer_doc.territory = "All Territories"  # Default territory
        
        if self.customer_email:
            customer_doc.email_id = self.customer_email
        
        customer_doc.insert(ignore_permissions=True)
        return customer_doc.name
    
    def create_sales_order(self, customer):
        """Create sales order from marketplace order"""
        if not customer:
            return None
        
        sales_order = frappe.new_doc("Sales Order")
        sales_order.customer = customer
        sales_order.order_type = "Sales"
        sales_order.company = frappe.defaults.get_user_default("Company")
        sales_order.transaction_date = self.order_date or self.sync_date
        
        # Add marketplace reference
        sales_order.po_no = f"{self.marketplace}-{self.marketplace_order_id}"
        
        # This would require actual order items data from marketplace
        # For now, create a placeholder item
        sales_order.append("items", {
            "item_code": "MARKETPLACE-ITEM",  # This would be actual item codes
            "qty": 1,
            "rate": self.net_amount or self.total_amount or 0
        })
        
        sales_order.insert(ignore_permissions=True)
        sales_order.submit()
        return sales_order
    
    def create_sales_invoice(self, sales_order):
        """Create sales invoice from sales order"""
        try:
            sales_invoice = frappe.new_doc("Sales Invoice")
            sales_invoice.customer = sales_order.customer
            sales_invoice.company = sales_order.company
            
            # Copy items from sales order
            for item in sales_order.items:
                sales_invoice.append("items", {
                    "item_code": item.item_code,
                    "qty": item.qty,
                    "rate": item.rate,
                    "sales_order": sales_order.name,
                    "so_detail": item.name
                })
            
            sales_invoice.insert(ignore_permissions=True)
            sales_invoice.submit()
            return sales_invoice
            
        except Exception as e:
            frappe.log_error(f"Failed to create sales invoice: {str(e)}")
            return None
    
    def create_delivery_note(self, sales_order):
        """Create delivery note from sales order"""
        try:
            delivery_note = frappe.new_doc("Delivery Note")
            delivery_note.customer = sales_order.customer
            delivery_note.company = sales_order.company
            
            # Copy items from sales order
            for item in sales_order.items:
                delivery_note.append("items", {
                    "item_code": item.item_code,
                    "qty": item.qty,
                    "rate": item.rate,
                    "against_sales_order": sales_order.name,
                    "so_detail": item.name
                })
            
            delivery_note.insert(ignore_permissions=True)
            delivery_note.submit()
            return delivery_note
            
        except Exception as e:
            frappe.log_error(f"Failed to create delivery note: {str(e)}")
            return None
    
    def get_marketplace_config(self):
        """Get marketplace configuration"""
        return {
            "api_key": "placeholder",
            "endpoint": f"https://api.{self.marketplace.lower()}.com",
            "enabled": True
        }
    
    @frappe.whitelist()
    def retry_sync(self):
        """Retry failed synchronization"""
        if self.retry_count >= 3:
            frappe.throw("Maximum retry attempts reached. Please check the error and try again.")
        
        return self.execute_sync()


@frappe.whitelist()
def bulk_sync_orders(marketplace=None, status=None):
    """Bulk synchronize orders from marketplace"""
    filters = {"auto_sync_enabled": 1}
    
    if marketplace:
        filters["marketplace"] = marketplace
    
    if status:
        filters["sync_status"] = status
    else:
        filters["sync_status"] = ["in", ["Pending", "Failed"]]
    
    sync_records = frappe.get_all("Marketplace Order Sync", filters=filters)
    
    results = []
    for record in sync_records:
        sync_doc = frappe.get_doc("Marketplace Order Sync", record.name)
        result = sync_doc.execute_sync()
        results.append({"record": record.name, "result": result})
    
    return results


def scheduled_order_sync():
    """Scheduled job to sync orders automatically"""
    due_syncs = frappe.get_all("Marketplace Order Sync",
        filters={
            "auto_sync_enabled": 1,
            "sync_status": ["in", ["Pending", "Failed"]],
            "retry_count": ["<", 3]
        }
    )
    
    for sync_record in due_syncs:
        try:
            sync_doc = frappe.get_doc("Marketplace Order Sync", sync_record.name)
            sync_doc.execute_sync()
        except Exception as e:
            frappe.log_error(f"Scheduled order sync failed for {sync_record.name}: {str(e)}")
    
    return len(due_syncs)