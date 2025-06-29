# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

"""Arabic text utilities for Universal Workshop ERP"""

import re
import unicodedata
from datetime import datetime
from frappe import _


class ArabicTextUtils:
    """Utility class for Arabic text processing and formatting"""

    @staticmethod
    def normalize_arabic_text(text):
        """Normalize Arabic text for better search and comparison"""
        if not text:
            return ""

        # Remove diacritics (Tashkeel)
        text = re.sub(r"[\u064B-\u0652\u0670\u0640]", "", text)

        # Normalize Alef variations
        text = re.sub(r"[آأإ]", "ا", text)

        # Normalize Teh Marbuta
        text = re.sub(r"ة", "ه", text)

        # Normalize Yeh variations
        text = re.sub(r"[ىي]", "ي", text)

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text.strip())

        return text

    @staticmethod
    def is_arabic_text(text):
        """Check if text contains Arabic characters"""
        if not text:
            return False

        arabic_pattern = re.compile(
            r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+"
        )
        return bool(arabic_pattern.search(text))

    @staticmethod
    def get_text_direction(text):
        """Determine text direction for mixed content"""
        if not text:
            return "ltr"

        arabic_chars = len(re.findall(r"[\u0600-\u06FF]", text))
        total_chars = len(re.findall(r"[A-Za-z\u0600-\u06FF]", text))

        if total_chars == 0:
            return "ltr"

        # If more than 30% is Arabic, consider it RTL
        if arabic_chars / total_chars > 0.3:
            return "rtl"

        return "ltr"

    @staticmethod
    def convert_to_arabic_numerals(text):
        """Convert Western numerals to Arabic-Indic numerals"""
        if not text:
            return text

        arabic_numerals = {
            "0": "٠",
            "1": "١",
            "2": "٢",
            "3": "٣",
            "4": "٤",
            "5": "٥",
            "6": "٦",
            "7": "٧",
            "8": "٨",
            "9": "٩",
        }

        for western, arabic in arabic_numerals.items():
            text = text.replace(western, arabic)

        return text

    @staticmethod
    def convert_to_western_numerals(text):
        """Convert Arabic-Indic numerals to Western numerals"""
        if not text:
            return text

        western_numerals = {
            "٠": "0",
            "١": "1",
            "٢": "2",
            "٣": "3",
            "٤": "4",
            "٥": "5",
            "٦": "6",
            "٧": "7",
            "٨": "8",
            "٩": "9",
        }

        for arabic, western in western_numerals.items():
            text = text.replace(arabic, western)

        return text

    @staticmethod
    def format_arabic_currency(amount, currency="OMR", language="ar"):
        """Format currency for Arabic locale (Omani Rial)"""
        if not amount:
            return ""

        if language == "ar":
            # Arabic format: ر.ع. ١٢٣.٤٥٦
            arabic_amount = ArabicTextUtils.convert_to_arabic_numerals(f"{amount:,.3f}")
            return f"ر.ع. {arabic_amount}"
        else:
            # English format: OMR 123.456
            return f"{currency} {amount:,.3f}"

    @staticmethod
    def truncate_arabic_text(text, max_length):
        """Truncate Arabic text preserving word boundaries"""
        if not text or len(text) <= max_length:
            return text

        # Find last space before max_length
        truncated = text[:max_length]
        last_space = truncated.rfind(" ")

        if last_space > 0:
            return truncated[:last_space] + "..."

        return truncated + "..."

    @staticmethod
    def get_arabic_text_length(text):
        """Get accurate length for Arabic text (handles RTL)"""
        if not text:
            return 0

        # Remove combining characters for accurate count
        return len("".join(c for c in text if unicodedata.category(c) != "Mn"))

    @staticmethod
    def format_arabic_address(address_parts):
        """Format address components for Arabic layout"""
        if not address_parts:
            return ""

        # Arabic addresses read: Building, Street, District, City
        components = []

        if address_parts.get("building"):
            components.append(address_parts["building"])

        if address_parts.get("street"):
            components.append(address_parts["street"])

        if address_parts.get("district"):
            components.append(address_parts["district"])

        if address_parts.get("city"):
            components.append(address_parts["city"])

        return "، ".join(components)

    @staticmethod
    def get_arabic_month_name(month_num):
        """Get Arabic month name by number (1-12)"""
        arabic_months = [
            "يناير",
            "فبراير",
            "مارس",
            "أبريل",
            "مايو",
            "يونيو",
            "يوليو",
            "أغسطس",
            "سبتمبر",
            "أكتوبر",
            "نوفمبر",
            "ديسمبر",
        ]

        if 1 <= month_num <= 12:
            return arabic_months[month_num - 1]

        return ""

    @staticmethod
    def get_arabic_day_name(day_num):
        """Get Arabic day name by number (0=Sunday, 6=Saturday)"""
        arabic_days = [
            "الأحد",
            "الاثنين",
            "الثلاثاء",
            "الأربعاء",
            "الخميس",
            "الجمعة",
            "السبت",
        ]

        if 0 <= day_num <= 6:
            return arabic_days[day_num]

        return ""

    @staticmethod
    def format_arabic_date(date_obj, include_day=True):
        """Format date in Arabic"""
        if not date_obj:
            return ""

        try:
            if isinstance(date_obj, str):
                # Try to parse string date
                try:
                    date_obj = datetime.strptime(date_obj, "%Y-%m-%d")
                except ValueError:
                    try:
                        date_obj = datetime.strptime(date_obj, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        return ""

            if not isinstance(date_obj, datetime):
                return ""

            day = ArabicTextUtils.convert_to_arabic_numerals(str(date_obj.day))
            month = ArabicTextUtils.get_arabic_month_name(date_obj.month)
            year = ArabicTextUtils.convert_to_arabic_numerals(str(date_obj.year))

            if include_day:
                day_name = ArabicTextUtils.get_arabic_day_name(date_obj.weekday())
                return f"{day_name}، {day} {month} {year}"

            return f"{day} {month} {year}"

        except Exception:
            return ""

    @staticmethod
    def clean_search_term(search_term):
        """Clean and normalize search term for better results"""
        if not search_term:
            return ""

        # Normalize the search term
        normalized = ArabicTextUtils.normalize_arabic_text(search_term)

        # Remove special characters except space and Arabic punctuation
        cleaned = re.sub(r"[^\w\s\u0600-\u06FF،؟]", "", normalized)

        # Remove extra whitespace
        cleaned = re.sub(r"\s+", " ", cleaned.strip())

        return cleaned


# Standalone functions for compatibility and template use


def normalize_arabic_text(text):
    """Clean and normalize search term for better results"""
    return ArabicTextUtils.normalize_arabic_text(text)


def is_arabic_text(text):
    """Check if text contains Arabic characters"""
    return ArabicTextUtils.is_arabic_text(text)


def get_text_direction(text):
    """Determine text direction for mixed content"""
    return ArabicTextUtils.get_text_direction(text)


def convert_to_arabic_numerals(text):
    """Convert Western numerals to Arabic-Indic numerals"""
    return ArabicTextUtils.convert_to_arabic_numerals(text)


def convert_to_western_numerals(text):
    """Convert Arabic-Indic numerals to Western numerals"""
    return ArabicTextUtils.convert_to_western_numerals(text)


def format_arabic_currency(amount, currency="OMR", language="ar"):
    """Format currency for Arabic locale (Omani Rial)"""
    return ArabicTextUtils.format_arabic_currency(amount, currency, language)


def truncate_arabic_text(text, max_length):
    """Truncate Arabic text preserving word boundaries"""
    return ArabicTextUtils.truncate_arabic_text(text, max_length)


def get_arabic_text_length(text):
    """Get accurate length for Arabic text (handles RTL)"""
    return ArabicTextUtils.get_arabic_text_length(text)


def format_arabic_address(address_parts):
    """Format address components for Arabic layout"""
    return ArabicTextUtils.format_arabic_address(address_parts)


def get_arabic_month_name(month_num):
    """Get Arabic month name by number (1-12)"""
    return ArabicTextUtils.get_arabic_month_name(month_num)


def get_arabic_day_name(day_num):
    """Get Arabic day name by number (0=Sunday, 6=Saturday)"""
    return ArabicTextUtils.get_arabic_day_name(day_num)


def format_arabic_date(date_obj, include_day=True):
    """Format date in Arabic - Main template function"""
    return ArabicTextUtils.format_arabic_date(date_obj, include_day)


def clean_search_term(search_term):
    """Clean and normalize search term for better results"""
    return ArabicTextUtils.clean_search_term(search_term)


# Additional utility functions for specific use cases


def format_arabic_time(date_obj, use_24_hour=True):
    """Format time in Arabic"""
    if not isinstance(date_obj, datetime):
        return ""

    hours = date_obj.hour
    minutes = f"{date_obj.minute:02d}"

    if use_24_hour:
        hours_str = f"{hours:02d}"
        time_str = f"{hours_str}:{minutes}"
        return convert_to_arabic_numerals(time_str)
    else:
        ampm = "م" if hours >= 12 else "ص"
        hours = hours % 12
        hours = hours if hours else 12  # 0 should be 12
        time_str = f"{hours}:{minutes}"
        return convert_to_arabic_numerals(time_str) + " " + ampm


def format_omr_currency(amount, language="en"):
    """Format currency for Oman (OMR)"""
    if not isinstance(amount, (int, float)):
        return ""

    formatted_amount = f"{amount:.3f}"

    if language == "ar":
        arabic_amount = convert_to_arabic_numerals(formatted_amount)
        return f"ر.ع. {arabic_amount}"
    else:
        return f"OMR {formatted_amount}"


def validate_arabic_text(text):
    """Validate Arabic text input"""
    if not text or not isinstance(text, str):
        return {"valid": False, "error": _("Arabic text is required")}

    # Check for minimum Arabic content
    if not is_arabic_text(text):
        return {"valid": False, "error": _("Text must contain Arabic characters")}

    # Check for prohibited characters
    prohibited_chars = re.compile(r"[<>{}]")
    if prohibited_chars.search(text):
        return {"valid": False, "error": _("Text contains prohibited characters")}

    return {"valid": True}


def convert_hijri_date(gregorian_date):
    """Convert Gregorian date to Hijri calendar (if hijri-converter is available)"""
    try:
        from hijri_converter import Gregorian

        if not isinstance(gregorian_date, datetime):
            return None

        hijri = Gregorian(gregorian_date.year, gregorian_date.month, gregorian_date.day).to_hijri()

        return {
            "day": hijri.day,
            "month": hijri.month,
            "year": hijri.year,
            "formatted": f"{hijri.day}/{hijri.month}/{hijri.year} هـ",
        }
    except ImportError:
        # hijri-converter not available
        return None
    except Exception:
        return None
