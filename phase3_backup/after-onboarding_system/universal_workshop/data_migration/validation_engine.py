# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import re
import json
import difflib
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Set
from abc import ABC, abstractmethod

import frappe
from frappe import _
from frappe.utils import getdate, get_datetime, flt, cint, validate_email_address


class ValidationRule(ABC):
    """Abstract base class for validation rules"""

    def __init__(self, config: Dict):
        self.config = config
        self.field_name = config.get("field")
        self.error_message = config.get("error_message", "Validation failed")

    @abstractmethod
    def validate(self, value: Any, record: Dict) -> Tuple[bool, Optional[str]]:
        """
        Validate a value
        Returns: (is_valid, error_message)
        """
        pass


class RequiredFieldRule(ValidationRule):
    """Validate required fields"""

    def validate(self, value: Any, record: Dict) -> Tuple[bool, Optional[str]]:
        if value is None or value == "" or (isinstance(value, str) and not value.strip()):
            return False, _("Field {0} is required").format(self.field_name)
        return True, None


class EmailValidationRule(ValidationRule):
    """Validate email format"""

    def validate(self, value: Any, record: Dict) -> Tuple[bool, Optional[str]]:
        if not value:
            return True, None  # Allow empty if not required

        try:
            validate_email_address(str(value))
            return True, None
        except Exception:
            return False, _("Invalid email format: {0}").format(value)


class PhoneValidationRule(ValidationRule):
    """Validate phone number format for Oman"""

    def __init__(self, config: Dict):
        super().__init__(config)
        self.country_code = config.get("country_code", "+968")
        self.digit_count = config.get("digit_count", 8)

    def validate(self, value: Any, record: Dict) -> Tuple[bool, Optional[str]]:
        if not value:
            return True, None

        phone = str(value).strip()

        # Check format: +968 XXXXXXXX or 968XXXXXXXX
        if phone.startswith(self.country_code):
            digits = phone[len(self.country_code) :].replace(" ", "").replace("-", "")
        elif phone.startswith("968"):
            digits = phone[3:]
        else:
            return False, _("Phone number must start with {0}").format(self.country_code)

        if not digits.isdigit() or len(digits) != self.digit_count:
            return False, _("Phone number must have {0} digits after country code").format(
                self.digit_count
            )

        return True, None


class BusinessLicenseRule(ValidationRule):
    """Validate Oman business license format"""

    def validate(self, value: Any, record: Dict) -> Tuple[bool, Optional[str]]:
        if not value:
            return True, None

        license_number = str(value).strip()

        # Oman business license: 7 digits
        if not re.match(r"^\d{7}$", license_number):
            return False, _("Business license must be 7 digits")

        return True, None


class DateRangeRule(ValidationRule):
    """Validate date is within specified range"""

    def __init__(self, config: Dict):
        super().__init__(config)
        self.min_date = config.get("min_date")
        self.max_date = config.get("max_date")

    def validate(self, value: Any, record: Dict) -> Tuple[bool, Optional[str]]:
        if not value:
            return True, None

        try:
            date_value = getdate(value)

            if self.min_date and date_value < getdate(self.min_date):
                return False, _("Date must be after {0}").format(self.min_date)

            if self.max_date and date_value > getdate(self.max_date):
                return False, _("Date must be before {0}").format(self.max_date)

            return True, None
        except Exception:
            return False, _("Invalid date format: {0}").format(value)


class NumericRangeRule(ValidationRule):
    """Validate numeric values are within specified range"""

    def __init__(self, config: Dict):
        super().__init__(config)
        self.min_value = config.get("min_value")
        self.max_value = config.get("max_value")

    def validate(self, value: Any, record: Dict) -> Tuple[bool, Optional[str]]:
        if not value:
            return True, None

        try:
            numeric_value = flt(value)

            if self.min_value is not None and numeric_value < self.min_value:
                return False, _("Value must be at least {0}").format(self.min_value)

            if self.max_value is not None and numeric_value > self.max_value:
                return False, _("Value must be at most {0}").format(self.max_value)

            return True, None
        except Exception:
            return False, _("Invalid numeric value: {0}").format(value)


class RegexValidationRule(ValidationRule):
    """Validate value against regular expression"""

    def __init__(self, config: Dict):
        super().__init__(config)
        self.pattern = config.get("pattern")
        self.flags = config.get("flags", 0)

    def validate(self, value: Any, record: Dict) -> Tuple[bool, Optional[str]]:
        if not value or not self.pattern:
            return True, None

        try:
            if re.match(self.pattern, str(value), self.flags):
                return True, None
            else:
                return False, _("Value does not match required pattern: {0}").format(value)
        except Exception as e:
            return False, _("Pattern validation error: {0}").format(str(e))


class DuplicateCheckRule(ValidationRule):
    """Check for duplicate values in target DocType"""

    def __init__(self, config: Dict):
        super().__init__(config)
        self.target_doctype = config.get("target_doctype")
        self.check_field = config.get("check_field", self.field_name)
        self.ignore_existing = config.get("ignore_existing", False)

    def validate(self, value: Any, record: Dict) -> Tuple[bool, Optional[str]]:
        if not value or not self.target_doctype:
            return True, None

        # Check if value already exists
        existing = frappe.db.get_value(self.target_doctype, {self.check_field: value})

        if existing:
            if self.ignore_existing:
                return True, None  # Allow if updating existing record
            else:
                return False, _("Duplicate value found: {0} already exists").format(value)

        return True, None


class LinkValidationRule(ValidationRule):
    """Validate linked document exists"""

    def __init__(self, config: Dict):
        super().__init__(config)
        self.link_doctype = config.get("link_doctype")
        self.create_missing = config.get("create_missing", False)

    def validate(self, value: Any, record: Dict) -> Tuple[bool, Optional[str]]:
        if not value or not self.link_doctype:
            return True, None

        if frappe.db.exists(self.link_doctype, value):
            return True, None

        if self.create_missing:
            # Create missing linked document (basic implementation)
            try:
                link_doc = frappe.new_doc(self.link_doctype)
                link_doc.name = value
                if hasattr(link_doc, "title"):
                    link_doc.title = value
                link_doc.insert()
                return True, None
            except Exception as e:
                return False, _("Failed to create missing link {0}: {1}").format(value, str(e))

        return False, _("Linked document {0} {1} does not exist").format(self.link_doctype, value)


class ArabicTextRule(ValidationRule):
    """Validate Arabic text format and content"""

    def __init__(self, config: Dict):
        super().__init__(config)
        self.min_arabic_ratio = config.get("min_arabic_ratio", 0.3)
        self.allow_mixed = config.get("allow_mixed", True)

    def validate(self, value: Any, record: Dict) -> Tuple[bool, Optional[str]]:
        if not value:
            return True, None

        text = str(value).strip()
        if not text:
            return True, None

        # Count Arabic characters
        arabic_chars = len(re.findall(r"[\u0600-\u06FF]", text))
        total_chars = len(re.findall(r"[A-Za-z\u0600-\u06FF]", text))

        if total_chars == 0:
            return True, None  # No alphabetic characters

        arabic_ratio = arabic_chars / total_chars

        if arabic_ratio < self.min_arabic_ratio and not self.allow_mixed:
            return False, _("Text must contain at least {0}% Arabic characters").format(
                int(self.min_arabic_ratio * 100)
            )

        return True, None


class DataCleansing:
    """Data cleansing utilities"""

    @staticmethod
    def clean_phone_number(phone: str, country_code: str = "+968") -> str:
        """Clean and standardize phone number"""
        if not phone:
            return phone

        # Remove all non-digits except +
        cleaned = re.sub(r"[^\d+]", "", phone)

        # Handle different formats
        if cleaned.startswith("00968"):
            cleaned = "+968" + cleaned[5:]
        elif cleaned.startswith("968") and not cleaned.startswith("+968"):
            cleaned = "+968" + cleaned[3:]
        elif not cleaned.startswith("+968") and cleaned.isdigit():
            cleaned = "+968" + cleaned

        return cleaned

    @staticmethod
    def clean_arabic_text(text: str) -> str:
        """Clean Arabic text by removing diacritics and normalizing"""
        if not text:
            return text

        # Remove Arabic diacritics (Tashkeel)
        text = re.sub(r"[\u064B-\u0652\u0670\u0640]", "", text)

        # Normalize Alef variations
        text = re.sub(r"[آأإ]", "ا", text)

        # Normalize Teh Marbuta
        text = re.sub(r"ة", "ه", text)

        # Remove extra whitespace
        text = " ".join(text.split())

        return text.strip()

    @staticmethod
    def clean_business_name(name: str) -> str:
        """Clean business name"""
        if not name:
            return name

        # Common business name cleanups
        name = name.strip()

        # Standardize common abbreviations
        replacements = {
            "LLC": "L.L.C",
            "ltd": "Ltd.",
            "LTD": "Ltd.",
            "co.": "Co.",
            "CO.": "Co.",
            "inc.": "Inc.",
            "INC.": "Inc.",
        }

        for old, new in replacements.items():
            name = re.sub(r"\b" + re.escape(old) + r"\b", new, name, flags=re.IGNORECASE)

        return name

    @staticmethod
    def clean_address(address: str) -> str:
        """Clean address text"""
        if not address:
            return address

        # Remove extra whitespace and normalize
        address = " ".join(address.split())

        # Capitalize first letter of each word
        address = " ".join(
            word.capitalize() if word.isascii() else word for word in address.split()
        )

        return address

    @staticmethod
    def standardize_date_format(date_value: Any) -> str:
        """Standardize date format"""
        if not date_value:
            return date_value

        try:
            # Try to parse various date formats
            if isinstance(date_value, str):
                # Common formats
                formats = ["%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"]

                for fmt in formats:
                    try:
                        date_obj = datetime.strptime(date_value.strip(), fmt)
                        return date_obj.strftime("%Y-%m-%d")
                    except ValueError:
                        continue

            # Use Frappe's date parsing
            return str(getdate(date_value))
        except Exception:
            return date_value  # Return original if parsing fails


class DuplicateDetection:
    """Duplicate detection algorithms"""

    @staticmethod
    def find_similar_customers(
        customer_data: Dict, similarity_threshold: float = 0.8
    ) -> List[Dict]:
        """Find similar customers based on name, phone, email"""
        similar_customers = []

        # Get existing customers
        existing_customers = frappe.get_list(
            "Customer",
            fields=["name", "customer_name", "email_id", "mobile_no"],
            limit=1000,  # Limit for performance
        )

        customer_name = customer_data.get("customer_name", "").lower()
        customer_email = customer_data.get("email_id", "").lower()
        customer_phone = customer_data.get("mobile_no", "")

        for existing in existing_customers:
            similarity_score = 0
            match_reasons = []

            # Name similarity
            if customer_name and existing.get("customer_name"):
                name_similarity = difflib.SequenceMatcher(
                    None, customer_name, existing["customer_name"].lower()
                ).ratio()
                if name_similarity > 0.7:
                    similarity_score += name_similarity * 0.5
                    match_reasons.append(f"Name similarity: {name_similarity:.2f}")

            # Email exact match
            if customer_email and existing.get("email_id"):
                if customer_email == existing["email_id"].lower():
                    similarity_score += 0.4
                    match_reasons.append("Email exact match")

            # Phone similarity (clean and compare)
            if customer_phone and existing.get("mobile_no"):
                clean_new = DataCleansing.clean_phone_number(customer_phone)
                clean_existing = DataCleansing.clean_phone_number(existing["mobile_no"])
                if clean_new == clean_existing:
                    similarity_score += 0.3
                    match_reasons.append("Phone exact match")

            # Add to similar if above threshold
            if similarity_score >= similarity_threshold:
                similar_customers.append(
                    {
                        "customer": existing,
                        "similarity_score": similarity_score,
                        "match_reasons": match_reasons,
                    }
                )

        return sorted(similar_customers, key=lambda x: x["similarity_score"], reverse=True)

    @staticmethod
    def find_similar_vehicles(vehicle_data: Dict, similarity_threshold: float = 0.9) -> List[Dict]:
        """Find similar vehicles based on VIN, license plate"""
        similar_vehicles = []

        # Get existing vehicles
        existing_vehicles = frappe.get_list(
            "Vehicle Profile",
            fields=["name", "vin_number", "license_plate", "make", "model", "year"],
            limit=1000,
        )

        vin = vehicle_data.get("vin_number", "").upper()
        license_plate = vehicle_data.get("license_plate", "").upper()

        for existing in existing_vehicles:
            similarity_score = 0
            match_reasons = []

            # VIN exact match (highest priority)
            if vin and existing.get("vin_number"):
                if vin == existing["vin_number"].upper():
                    similarity_score = 1.0
                    match_reasons.append("VIN exact match")
                    break

            # License plate exact match
            if license_plate and existing.get("license_plate"):
                if license_plate == existing["license_plate"].upper():
                    similarity_score += 0.8
                    match_reasons.append("License plate exact match")

            # Make, model, year combination
            if (
                vehicle_data.get("make") == existing.get("make")
                and vehicle_data.get("model") == existing.get("model")
                and vehicle_data.get("year") == existing.get("year")
            ):
                similarity_score += 0.3
                match_reasons.append("Make/Model/Year match")

            if similarity_score >= similarity_threshold:
                similar_vehicles.append(
                    {
                        "vehicle": existing,
                        "similarity_score": similarity_score,
                        "match_reasons": match_reasons,
                    }
                )

        return sorted(similar_vehicles, key=lambda x: x["similarity_score"], reverse=True)


class ValidationEngine:
    """Main validation engine"""

    def __init__(self, validation_config: Dict):
        self.config = validation_config
        self.rules = self._build_rules()
        self.cleansing = DataCleansing()
        self.duplicate_detection = DuplicateDetection()

    def _build_rules(self) -> Dict[str, List[ValidationRule]]:
        """Build validation rules from configuration"""
        rules = {}

        for field_name, field_rules in self.config.items():
            rules[field_name] = []

            for rule_config in field_rules:
                rule_type = rule_config.get("type")
                rule_config["field"] = field_name

                rule_classes = {
                    "required": RequiredFieldRule,
                    "email": EmailValidationRule,
                    "phone": PhoneValidationRule,
                    "business_license": BusinessLicenseRule,
                    "date_range": DateRangeRule,
                    "numeric_range": NumericRangeRule,
                    "regex": RegexValidationRule,
                    "duplicate_check": DuplicateCheckRule,
                    "link_validation": LinkValidationRule,
                    "arabic_text": ArabicTextRule,
                }

                if rule_type in rule_classes:
                    rules[field_name].append(rule_classes[rule_type](rule_config))

        return rules

    def validate_record(self, record: Dict, apply_cleansing: bool = True) -> Dict:
        """
        Validate a single record
        Returns: {
            'is_valid': bool,
            'errors': List[str],
            'warnings': List[str],
            'cleaned_record': Dict,
            'suggestions': Dict
        }
        """
        result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "cleaned_record": record.copy(),
            "suggestions": {},
        }

        # Apply data cleansing first
        if apply_cleansing:
            result["cleaned_record"] = self._apply_cleansing(result["cleaned_record"])

        # Apply validation rules
        for field_name, rules in self.rules.items():
            if field_name in result["cleaned_record"]:
                field_value = result["cleaned_record"][field_name]

                for rule in rules:
                    is_valid, error_message = rule.validate(field_value, result["cleaned_record"])

                    if not is_valid:
                        result["is_valid"] = False
                        result["errors"].append(error_message)

        return result

    def _apply_cleansing(self, record: Dict) -> Dict:
        """Apply data cleansing to record"""
        cleaned = record.copy()

        # Phone number cleansing
        phone_fields = ["mobile_no", "phone", "phone_number"]
        for field in phone_fields:
            if field in cleaned and cleaned[field]:
                cleaned[field] = self.cleansing.clean_phone_number(cleaned[field])

        # Arabic text cleansing
        arabic_fields = [f for f in cleaned.keys() if f.endswith("_ar") or "arabic" in f.lower()]
        for field in arabic_fields:
            if field in cleaned and cleaned[field]:
                cleaned[field] = self.cleansing.clean_arabic_text(cleaned[field])

        # Business name cleansing
        name_fields = ["customer_name", "supplier_name", "company_name", "business_name"]
        for field in name_fields:
            if field in cleaned and cleaned[field]:
                cleaned[field] = self.cleansing.clean_business_name(cleaned[field])

        # Address cleansing
        address_fields = ["address", "address_line_1", "address_line_2"]
        for field in address_fields:
            if field in cleaned and cleaned[field]:
                cleaned[field] = self.cleansing.clean_address(cleaned[field])

        # Date standardization
        date_fields = [f for f in cleaned.keys() if "date" in f.lower() or f.endswith("_date")]
        for field in date_fields:
            if field in cleaned and cleaned[field]:
                cleaned[field] = self.cleansing.standardize_date_format(cleaned[field])

        return cleaned

    def check_duplicates(self, record: Dict, doctype: str) -> Dict:
        """Check for potential duplicates"""
        result = {"has_duplicates": False, "duplicates": [], "confidence": 0}

        if doctype == "Customer":
            duplicates = self.duplicate_detection.find_similar_customers(record)
            if duplicates:
                result["has_duplicates"] = True
                result["duplicates"] = duplicates
                result["confidence"] = duplicates[0]["similarity_score"]

        elif doctype == "Vehicle Profile":
            duplicates = self.duplicate_detection.find_similar_vehicles(record)
            if duplicates:
                result["has_duplicates"] = True
                result["duplicates"] = duplicates
                result["confidence"] = duplicates[0]["similarity_score"]

        return result

    def validate_batch(self, records: List[Dict], doctype: str) -> Dict:
        """Validate a batch of records"""
        results = {
            "total_records": len(records),
            "valid_records": 0,
            "invalid_records": 0,
            "duplicate_records": 0,
            "validation_results": [],
            "summary": {"common_errors": {}, "cleansing_applied": 0, "performance_metrics": {}},
        }

        start_time = datetime.now()

        for i, record in enumerate(records):
            # Validate individual record
            validation_result = self.validate_record(record)

            # Check for duplicates
            duplicate_result = self.check_duplicates(record, doctype)

            record_result = {
                "record_index": i,
                "validation": validation_result,
                "duplicates": duplicate_result,
            }

            results["validation_results"].append(record_result)

            # Update counters
            if validation_result["is_valid"]:
                results["valid_records"] += 1
            else:
                results["invalid_records"] += 1

            if duplicate_result["has_duplicates"]:
                results["duplicate_records"] += 1

            # Track common errors
            for error in validation_result["errors"]:
                if error not in results["summary"]["common_errors"]:
                    results["summary"]["common_errors"][error] = 0
                results["summary"]["common_errors"][error] += 1

        # Performance metrics
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        results["summary"]["performance_metrics"] = {
            "processing_time_seconds": processing_time,
            "records_per_second": len(records) / processing_time if processing_time > 0 else 0,
            "validation_efficiency": (
                results["valid_records"] / len(records) * 100 if len(records) > 0 else 0
            ),
        }

        return results
