# -*- coding: utf-8 -*-
"""
VIN Decoder Integration for Universal Workshop ERP
Supports multiple VIN decoder APIs with fallback options
"""

import frappe
from frappe import _
import requests
import json
from typing import Dict, Optional
import re


class VINDecoderManager:
    """
    Comprehensive VIN decoder with multiple API providers and offline fallback
    """
    
    def __init__(self):
        self.primary_api = "nhtsa"  # US NHTSA free API
        self.secondary_api = "vindecoder"  # Backup commercial API
        self.cache_expiry_days = 30
        
    def decode_vin(self, vin: str, use_cache: bool = True) -> Dict:
        """
        Decode VIN using multiple APIs with intelligent fallback
        
        Args:
            vin (str): 17-character VIN
            use_cache (bool): Whether to use cached results
            
        Returns:
            Dict: Decoded vehicle information
        """
        try:
            # Validate VIN format
            if not self.validate_vin_format(vin):
                return {
                    "success": False,
                    "error": _("Invalid VIN format. VIN must be 17 characters.")
                }
            
            # Check cache first
            if use_cache:
                cached_result = self.get_cached_vin_data(vin)
                if cached_result:
                    return cached_result
            
            # Try primary API
            result = self.decode_with_nhtsa_api(vin)
            if result.get("success"):
                self.cache_vin_data(vin, result)
                return result
            
            # Fallback to secondary API
            result = self.decode_with_vindecoder_api(vin)
            if result.get("success"):
                self.cache_vin_data(vin, result)
                return result
            
            # Fallback to basic VIN parsing
            result = self.basic_vin_decode(vin)
            if result.get("success"):
                self.cache_vin_data(vin, result)
                return result
            
            return {
                "success": False,
                "error": _("Unable to decode VIN using any available method")
            }
            
        except Exception as e:
            frappe.log_error(f"VIN Decoder Error: {str(e)}", "VIN Decoder")
            return {
                "success": False,
                "error": _("VIN decoding failed: {0}").format(str(e))
            }
    
    def validate_vin_format(self, vin: str) -> bool:
        """Validate VIN format (17 characters, alphanumeric except I, O, Q)"""
        if not vin or len(vin) != 17:
            return False
        
        # VIN should not contain I, O, Q
        invalid_chars = set('IOQ')
        if any(char in invalid_chars for char in vin.upper()):
            return False
        
        # Should be alphanumeric
        if not re.match(r'^[A-HJ-NPR-Z0-9]{17}$', vin.upper()):
            return False
            
        return True
    
    def decode_with_nhtsa_api(self, vin: str) -> Dict:
        """Decode VIN using NHTSA free API"""
        try:
            url = f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/{vin}?format=json"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("Results"):
                # Parse NHTSA response
                decoded_data = self.parse_nhtsa_response(data["Results"])
                decoded_data["success"] = True
                decoded_data["source"] = "NHTSA"
                return decoded_data
            
            return {"success": False, "error": "No data from NHTSA API"}
            
        except Exception as e:
            frappe.log_error(f"NHTSA API Error: {str(e)}", "VIN Decoder NHTSA")
            return {"success": False, "error": str(e)}
    
    def decode_with_vindecoder_api(self, vin: str) -> Dict:
        """Decode VIN using VinDecoder.eu API (backup)"""
        try:
            # This would require API key in production
            # Using free endpoint for demo
            url = f"https://api.vindecoder.eu/3.2/{vin}/decode"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("success"):
                decoded_data = self.parse_vindecoder_response(data)
                decoded_data["success"] = True
                decoded_data["source"] = "VinDecoder.eu"
                return decoded_data
            
            return {"success": False, "error": "No data from VinDecoder API"}
            
        except Exception as e:
            frappe.log_error(f"VinDecoder API Error: {str(e)}", "VIN Decoder VinDecoder")
            return {"success": False, "error": str(e)}
    
    def basic_vin_decode(self, vin: str) -> Dict:
        """Basic VIN decoding using VIN position rules"""
        try:
            vin = vin.upper()
            
            # Basic VIN decoding rules
            year_codes = {
                'A': 1980, 'B': 1981, 'C': 1982, 'D': 1983, 'E': 1984,
                'F': 1985, 'G': 1986, 'H': 1987, 'J': 1988, 'K': 1989,
                'L': 1990, 'M': 1991, 'N': 1992, 'P': 1993, 'R': 1994,
                'S': 1995, 'T': 1996, 'V': 1997, 'W': 1998, 'X': 1999,
                'Y': 2000, '1': 2001, '2': 2002, '3': 2003, '4': 2004,
                '5': 2005, '6': 2006, '7': 2007, '8': 2008, '9': 2009,
                'A': 2010, 'B': 2011, 'C': 2012, 'D': 2013, 'E': 2014,
                'F': 2015, 'G': 2016, 'H': 2017, 'J': 2018, 'K': 2019,
                'L': 2020, 'M': 2021, 'N': 2022, 'P': 2023, 'R': 2024
            }
            
            # Extract basic information
            wmi = vin[:3]  # World Manufacturer Identifier
            vds = vin[3:9]  # Vehicle Descriptor Section
            vis = vin[9:]  # Vehicle Identifier Section
            
            model_year_char = vin[9]
            model_year = year_codes.get(model_year_char)
            
            # Basic manufacturer detection
            manufacturer = self.get_manufacturer_from_wmi(wmi)
            
            return {
                "success": True,
                "source": "Basic VIN Decode",
                "make": manufacturer,
                "model": "Unknown",
                "year": model_year,
                "body_style": "Unknown",
                "engine": "Unknown",
                "transmission": "Unknown",
                "drivetrain": "Unknown",
                "fuel_type": "Unknown",
                "wmi": wmi,
                "vds": vds,
                "vis": vis,
                "decoded_at": frappe.utils.now(),
                "confidence": "Low"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def parse_nhtsa_response(self, results: list) -> Dict:
        """Parse NHTSA API response into standardized format"""
        parsed_data = {
            "make": "Unknown",
            "model": "Unknown", 
            "year": None,
            "body_style": "Unknown",
            "engine": "Unknown",
            "transmission": "Unknown",
            "drivetrain": "Unknown",
            "fuel_type": "Unknown",
            "decoded_at": frappe.utils.now(),
            "confidence": "High"
        }
        
        # Map NHTSA fields to our format
        field_mapping = {
            "Make": "make",
            "Model": "model",
            "Model Year": "year",
            "Body Class": "body_style",
            "Engine Configuration": "engine",
            "Transmission Style": "transmission",
            "Drive Type": "drivetrain",
            "Fuel Type - Primary": "fuel_type"
        }
        
        for result in results:
            variable = result.get("Variable", "")
            value = result.get("Value", "")
            
            if variable in field_mapping and value and value != "Not Applicable":
                field_name = field_mapping[variable]
                if field_name == "year":
                    parsed_data[field_name] = int(value) if value.isdigit() else None
                else:
                    parsed_data[field_name] = value
        
        return parsed_data
    
    def parse_vindecoder_response(self, data: dict) -> Dict:
        """Parse VinDecoder API response into standardized format"""
        decode_data = data.get("decode", {})
        
        return {
            "make": decode_data.get("make", "Unknown"),
            "model": decode_data.get("model", "Unknown"),
            "year": decode_data.get("year"),
            "body_style": decode_data.get("body", "Unknown"),
            "engine": decode_data.get("engine", "Unknown"),
            "transmission": decode_data.get("transmission", "Unknown"),
            "drivetrain": decode_data.get("drive", "Unknown"),
            "fuel_type": decode_data.get("fuel", "Unknown"),
            "decoded_at": frappe.utils.now(),
            "confidence": "High"
        }
    
    def get_manufacturer_from_wmi(self, wmi: str) -> str:
        """Get manufacturer from World Manufacturer Identifier"""
        # Common WMI mappings
        wmi_manufacturers = {
            "1FT": "Ford", "1GC": "General Motors", "1GM": "General Motors",
            "2T1": "Toyota", "3VW": "Volkswagen", "4F2": "Mazda",
            "5NP": "Hyundai", "6F6": "Ford Australia", "7AT": "Toyota Australia",
            "8AG": "Chrysler", "9BD": "Fiat", "JHM": "Honda",
            "JN1": "Nissan", "KMH": "Hyundai", "SAL": "Land Rover",
            "WBA": "BMW", "WDB": "Mercedes-Benz", "WVW": "Volkswagen"
        }
        
        return wmi_manufacturers.get(wmi, "Unknown")
    
    def get_cached_vin_data(self, vin: str) -> Optional[Dict]:
        """Get cached VIN data if available and not expired"""
        try:
            cache_doc = frappe.db.get_value(
                "VIN Decode Cache",
                {"vin": vin},
                ["name", "decoded_data", "creation"],
                as_dict=True
            )
            
            if cache_doc:
                # Check if cache is still valid
                from frappe.utils import date_diff, now_datetime
                
                days_old = date_diff(now_datetime(), cache_doc.creation)
                if days_old <= self.cache_expiry_days:
                    return json.loads(cache_doc.decoded_data)
            
            return None
            
        except Exception:
            return None
    
    def cache_vin_data(self, vin: str, decoded_data: Dict):
        """Cache VIN decoded data for future use"""
        try:
            # Check if cache entry exists
            existing = frappe.db.exists("VIN Decode Cache", {"vin": vin})
            
            if existing:
                # Update existing cache
                cache_doc = frappe.get_doc("VIN Decode Cache", existing)
                cache_doc.decoded_data = json.dumps(decoded_data)
                cache_doc.save()
            else:
                # Create new cache entry
                cache_doc = frappe.new_doc("VIN Decode Cache")
                cache_doc.vin = vin
                cache_doc.decoded_data = json.dumps(decoded_data)
                cache_doc.insert()
                
        except Exception as e:
            # Don't fail if caching fails
            frappe.log_error(f"VIN Cache Error: {str(e)}", "VIN Decoder Cache")


# Frappe API Endpoints

@frappe.whitelist()
def decode_vehicle_vin(vin: str, use_cache: bool = True):
    """
    API endpoint to decode VIN
    
    Args:
        vin (str): Vehicle VIN to decode
        use_cache (bool): Whether to use cached results
        
    Returns:
        dict: Decoded vehicle information
    """
    decoder = VINDecoderManager()
    return decoder.decode_vin(vin, use_cache)


@frappe.whitelist() 
def update_vehicle_from_vin(vehicle_doc_name: str, vin: str):
    """
    Update Vehicle document with VIN decoded data
    
    Args:
        vehicle_doc_name (str): Name of Vehicle document
        vin (str): VIN to decode
        
    Returns:
        dict: Update result
    """
    try:
        # Decode VIN
        decoder = VINDecoderManager()
        decoded_data = decoder.decode_vin(vin)
        
        if not decoded_data.get("success"):
            return decoded_data
        
        # Get Vehicle document
        vehicle_doc = frappe.get_doc("Vehicle", vehicle_doc_name)
        
        # Update vehicle fields from decoded data
        vehicle_doc.vin = vin
        if decoded_data.get("make"):
            vehicle_doc.make = decoded_data["make"]
        if decoded_data.get("model"):
            vehicle_doc.model = decoded_data["model"]
        if decoded_data.get("year"):
            vehicle_doc.year = decoded_data["year"]
        if decoded_data.get("body_style"):
            vehicle_doc.body_style = decoded_data["body_style"]
        if decoded_data.get("engine"):
            vehicle_doc.engine_type = decoded_data["engine"]
        if decoded_data.get("fuel_type"):
            vehicle_doc.fuel_type = decoded_data["fuel_type"]
        
        # Add custom fields for VIN decode metadata
        vehicle_doc.vin_decoded_at = decoded_data.get("decoded_at")
        vehicle_doc.vin_decode_source = decoded_data.get("source")
        vehicle_doc.vin_decode_confidence = decoded_data.get("confidence")
        
        # Save vehicle
        vehicle_doc.save()
        
        return {
            "success": True,
            "message": _("Vehicle updated successfully with VIN data"),
            "decoded_data": decoded_data
        }
        
    except Exception as e:
        frappe.log_error(f"Vehicle VIN Update Error: {str(e)}", "VIN Decoder")
        return {
            "success": False,
            "error": _("Failed to update vehicle: {0}").format(str(e))
        }


@frappe.whitelist()
def get_compatible_parts(vin: str, part_category: str = None):
    """
    Get compatible parts for a vehicle based on VIN
    
    Args:
        vin (str): Vehicle VIN
        part_category (str): Optional part category filter
        
    Returns:
        dict: Compatible parts list
    """
    try:
        # First decode VIN to get vehicle specifications
        decoder = VINDecoderManager()
        decoded_data = decoder.decode_vin(vin)
        
        if not decoded_data.get("success"):
            return decoded_data
        
        # Build compatibility filters
        filters = {}
        if decoded_data.get("make"):
            filters["make"] = decoded_data["make"]
        if decoded_data.get("model"):
            filters["model"] = decoded_data["model"]
        if decoded_data.get("year"):
            filters["year"] = decoded_data["year"]
        if part_category:
            filters["part_category"] = part_category
        
        # Get compatible parts
        compatible_parts = frappe.get_list(
            "Parts Compatibility",
            filters=filters,
            fields=[
                "part_number", "part_name", "part_category",
                "brand", "price", "stock_quantity", "compatibility_notes"
            ]
        )
        
        return {
            "success": True,
            "vehicle_info": decoded_data,
            "compatible_parts": compatible_parts,
            "total_parts": len(compatible_parts)
        }
        
    except Exception as e:
        frappe.log_error(f"Parts Compatibility Error: {str(e)}", "VIN Decoder")
        return {
            "success": False,
            "error": _("Failed to get compatible parts: {0}").format(str(e))
        }
