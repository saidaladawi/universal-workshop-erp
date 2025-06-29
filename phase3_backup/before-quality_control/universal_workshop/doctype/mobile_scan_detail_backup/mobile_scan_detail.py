# Copyright (c) 2025, Universal Workshop and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class MobileScanDetail(Document):
    def before_save(self):
        """Calculate variance quantity before saving"""
        if self.scanned_qty and self.expected_qty:
            self.variance_qty = self.scanned_qty - self.expected_qty
        
        # Auto-set item name if not provided
        if not self.item_name and self.item_code:
            item = frappe.get_doc("Item", self.item_code)
            self.item_name = item.item_name
    
    def validate(self):
        """Validate scan detail data"""
        # Validate item exists
        if self.item_code and not frappe.db.exists("Item", self.item_code):
            frappe.throw(_("Item {0} does not exist").format(self.item_code))
        
        # Validate warehouse exists
        if self.warehouse and not frappe.db.exists("Warehouse", self.warehouse):
            frappe.throw(_("Warehouse {0} does not exist").format(self.warehouse))
        
        # Validate batch if provided
        if self.batch_no and not frappe.db.exists("Batch", self.batch_no):
            frappe.throw(_("Batch {0} does not exist").format(self.batch_no))
        
        # Validate scanned quantity is positive
        if self.scanned_qty < 0:
            frappe.throw(_("Scanned quantity cannot be negative"))
    
    def get_item_details(self):
        """Get item details for validation"""
        if not self.item_code:
            return {}
        
        item = frappe.get_doc("Item", self.item_code)
        return {
            "item_name": item.item_name,
            "stock_uom": item.stock_uom,
            "is_stock_item": item.is_stock_item,
            "has_batch_no": item.has_batch_no,
            "has_serial_no": item.has_serial_no
        }
    
    def get_current_stock(self):
        """Get current stock for the item in warehouse"""
        if not self.item_code or not self.warehouse:
            return 0
        
        from erpnext.stock.utils import get_stock_balance
        return get_stock_balance(
            item_code=self.item_code,
            warehouse=self.warehouse,
            batch_no=self.batch_no if self.batch_no else None
        )
