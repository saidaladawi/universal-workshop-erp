# -*- coding: utf-8 -*-
# Copyright (c) 2025, Said Al-Adowi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json
from datetime import datetime


class VINDecodeCache(Document):
    def validate(self):
        """Validate VIN decode cache entry"""
        self.validate_vin_format()
        self.validate_decoded_data()
        
    def validate_vin_format(self):
        """Validate VIN format"""
        if not self.vin or len(self.vin) != 17:
            frappe.throw("VIN must be exactly 17 characters")
            
        # Convert to uppercase
        self.vin = self.vin.upper()
        
        # Validate VIN characters (no I, O, Q)
        import re
        if not re.match(r'^[A-HJ-NPR-Z0-9]{17}$', self.vin):
            frappe.throw("VIN contains invalid characters. VIN cannot contain I, O, or Q")
    
    def validate_decoded_data(self):
        """Validate that decoded_data is valid JSON"""
        if self.decoded_data:
            try:
                json.loads(self.decoded_data)
            except json.JSONDecodeError:
                frappe.throw("Decoded data must be valid JSON")
    
    def before_save(self):
        """Update access tracking"""
        if not self.is_new():
            self.last_accessed = frappe.utils.now()
            self.access_count = (self.access_count or 0) + 1
    
    def get_decoded_data_dict(self):
        """Get decoded data as dictionary"""
        if self.decoded_data:
            return json.loads(self.decoded_data)
        return {}
    
    def set_decoded_data_dict(self, data_dict):
        """Set decoded data from dictionary"""
        self.decoded_data = json.dumps(data_dict, indent=2)
    
    @staticmethod
    def get_cached_vin_data(vin, max_age_days=30):
        """
        Get cached VIN data if available and not expired
        
        Args:
            vin (str): VIN to lookup
            max_age_days (int): Maximum age of cache in days
            
        Returns:
            dict or None: Cached data if available
        """
        try:
            from frappe.utils import date_diff, now_datetime
            
            cache_doc = frappe.get_doc("VIN Decode Cache", vin)
            
            # Check if cache is still valid
            days_old = date_diff(now_datetime(), cache_doc.creation)
            if days_old <= max_age_days:
                # Update access tracking
                cache_doc.last_accessed = frappe.utils.now()
                cache_doc.access_count = (cache_doc.access_count or 0) + 1
                cache_doc.save(ignore_permissions=True)
                
                return cache_doc.get_decoded_data_dict()
            
            return None
            
        except frappe.DoesNotExistError:
            return None
        except Exception as e:
            frappe.log_error(f"VIN Cache Lookup Error: {str(e)}", "VIN Decode Cache")
            return None
    
    @staticmethod
    def cache_vin_data(vin, decoded_data, source="Unknown", confidence="Medium"):
        """
        Cache VIN decoded data
        
        Args:
            vin (str): VIN to cache
            decoded_data (dict): Decoded vehicle data
            source (str): Data source
            confidence (str): Confidence level
        """
        try:
            # Check if cache entry exists
            if frappe.db.exists("VIN Decode Cache", vin):
                # Update existing cache
                cache_doc = frappe.get_doc("VIN Decode Cache", vin)
                cache_doc.set_decoded_data_dict(decoded_data)
                cache_doc.decode_source = source
                cache_doc.confidence_level = confidence
                cache_doc.save(ignore_permissions=True)
            else:
                # Create new cache entry
                cache_doc = frappe.new_doc("VIN Decode Cache")
                cache_doc.vin = vin.upper()
                cache_doc.set_decoded_data_dict(decoded_data)
                cache_doc.decode_source = source
                cache_doc.confidence_level = confidence
                cache_doc.insert(ignore_permissions=True)
                
        except Exception as e:
            # Don't fail if caching fails
            frappe.log_error(f"VIN Cache Save Error: {str(e)}", "VIN Decode Cache")
