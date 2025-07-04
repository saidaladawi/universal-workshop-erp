# Copyright (c) 2025, Universal Workshop ERP
# For license information, see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from datetime import datetime
import re

class BarcodeScanner(Document):
    def validate(self):
        """Validate barcode scanner data and fetch item details"""
        self.validate_barcode_data()
        self.validate_scan_mode()
        
        if self.auto_fetch_details and self.barcode_data:
            self.fetch_item_details()
            
        self.set_scan_metadata()
    
    def validate_barcode_data(self):
        """Validate barcode data format"""
        if not self.barcode_data:
            frappe.throw(_("بيانات الباركود مطلوبة"))
            
        # Validate barcode length based on type
        if self.barcode_type:
            min_lengths = {
                "Code 128": 1,
                "Code 39": 1,
                "EAN-13": 13,
                "EAN-8": 8,
                "QR Code": 1,
                "DataMatrix": 1,
                "PDF417": 1
            }
            
            min_length = min_lengths.get(self.barcode_type, 1)
            if len(self.barcode_data) < min_length:
                frappe.throw(_("بيانات الباركود قصيرة جداً للنوع المحدد"))
    
    def validate_scan_mode(self):
        """Validate scan mode configuration"""
        valid_modes = ["Manual", "Auto-Scan", "Batch Scan"]
        if self.scan_mode and self.scan_mode not in valid_modes:
            frappe.throw(_("وضع المسح غير صحيح"))
    
    def fetch_item_details(self):
        """Auto-fetch item details from barcode"""
        try:
            # Try to find item by barcode
            item_code = frappe.db.get_value("Item", {"barcode": self.barcode_data}, "name")
            
            if not item_code:
                # Try to find by part number
                item_code = frappe.db.get_value("Item", {"part_number": self.barcode_data}, "name")
            
            if item_code:
                item = frappe.get_doc("Item", item_code)
                self.item_code = item.name
                self.item_name = item.item_name
                self.part_number = item.get("part_number", "")
                self.manufacturer = item.get("manufacturer", "")
                
                # Get current stock
                self.current_stock = self.get_current_stock(item_code)
                self.location = self.get_default_location(item_code)
                
                frappe.msgprint(_("تم العثور على المنتج: {0}").format(item.item_name))
            else:
                frappe.msgprint(_("لم يتم العثور على منتج بهذا الباركود"), indicator="orange")
                
        except Exception as e:
            frappe.log_error(f"Error fetching item details: {e}")
            frappe.msgprint(_("خطأ في جلب تفاصيل المنتج"), indicator="red")
    
    def get_current_stock(self, item_code):
        """Get current stock for item"""
        try:
            stock_qty = frappe.db.sql("""
                SELECT SUM(actual_qty) 
                FROM `tabBin` 
                WHERE item_code = %s
            """, item_code)
            
            return stock_qty[0][0] if stock_qty and stock_qty[0][0] else 0
        except:
            return 0
    
    def get_default_location(self, item_code):
        """Get default location for item"""
        try:
            default_warehouse = frappe.db.get_value("Item", item_code, "default_warehouse")
            return default_warehouse
        except:
            return None
    
    def set_scan_metadata(self):
        """Set scan timestamp and user"""
        if not self.scan_timestamp:
            self.scan_timestamp = datetime.now()
        if not self.scanned_by:
            self.scanned_by = frappe.session.user
    
    def before_save(self):
        """Actions before saving"""
        if self.enable_sound:
            # Trigger sound notification (implemented in JS)
            pass
    
    @frappe.whitelist()
    def process_stock_movement(self):
        """Process stock movement based on scan"""
        if not self.item_code or not self.quantity_to_add:
            frappe.throw(_("يجب تحديد المنتج والكمية"))
        
        try:
            # Create stock entry
            stock_entry = frappe.new_doc("Stock Entry")
            stock_entry.stock_entry_type = "Material Receipt" if self.quantity_to_add > 0 else "Material Issue"
            stock_entry.from_warehouse = self.location if self.quantity_to_add < 0 else None
            stock_entry.to_warehouse = self.destination_location or self.location
            
            stock_entry.append("items", {
                "item_code": self.item_code,
                "qty": abs(self.quantity_to_add),
                "s_warehouse": self.location if self.quantity_to_add < 0 else None,
                "t_warehouse": self.destination_location or self.location
            })
            
            stock_entry.insert()
            stock_entry.submit()
            
            frappe.msgprint(_("تم تحديث المخزون بنجاح"))
            return stock_entry.name
            
        except Exception as e:
            frappe.log_error(f"Error processing stock movement: {e}")
            frappe.throw(_("خطأ في تحديث المخزون"))
    
    @frappe.whitelist()
    def get_barcode_info(self, barcode_data):
        """Get barcode information from external API if needed"""
        # This can be extended to call external barcode lookup services
        return {
            "barcode": barcode_data,
            "type": "Unknown",
            "description": "Barcode information not available"
        } 