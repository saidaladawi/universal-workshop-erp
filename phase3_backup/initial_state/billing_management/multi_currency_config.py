# -*- coding: utf-8 -*-
# Copyright (c) 2024, Said Al-Adowi and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, get_datetime, format_datetime, now, today
import requests
import json
from datetime import datetime, timedelta


class OmanMultiCurrencyManager:
    """
    Multi-currency management system for Oman businesses
    Supports OMR (Omani Rial), USD, EUR, SAR, AED with automatic exchange rate updates
    """

    def __init__(self):
        self.base_currency = 'OMR'  # Oman Rial as base currency
        self.supported_currencies = ['OMR', 'USD', 'EUR', 'SAR', 'AED', 'GBP']
        self.currency_symbols = {
            'OMR': 'ر.ع.',
            'USD': '$',
            'EUR': '€',
            'SAR': 'ر.س',
            'AED': 'د.إ',
            'GBP': '£'
        }
        self.decimal_places = {
            'OMR': 3,  # Baisa precision
            'USD': 2,
            'EUR': 2,
            'SAR': 2,
            'AED': 2,
            'GBP': 2
        }

    def setup_currencies(self):
        """Setup currencies in ERPNext during installation"""
        try:
            for currency_code in self.supported_currencies:
                self.create_currency_if_not_exists(currency_code)
            
            # Set OMR as default company currency
            self.set_default_currency()
            
            # Initialize exchange rates
            self.initialize_exchange_rates()
            
        except Exception as e:
            frappe.log_error(f"Currency setup error: {str(e)}")

    def create_currency_if_not_exists(self, currency_code):
        """Create currency record if it doesn't exist"""
        if not frappe.db.exists('Currency', currency_code):
            currency_doc = frappe.new_doc('Currency')
            currency_doc.currency_name = currency_code
            currency_doc.enabled = 1
            currency_doc.fraction = self.get_currency_fraction_name(currency_code)
            currency_doc.fraction_units = self.get_currency_fraction_units(currency_code)
            currency_doc.number_format = self.get_currency_number_format(currency_code)
            currency_doc.symbol = self.currency_symbols.get(currency_code, currency_code)
            currency_doc.insert()
            print(f"Created currency: {currency_code}")

    def get_currency_fraction_name(self, currency_code):
        """Get currency fraction name"""
        fractions = {
            'OMR': 'Baisa',
            'USD': 'Cent',
            'EUR': 'Cent', 
            'SAR': 'Halala',
            'AED': 'Fils',
            'GBP': 'Penny'
        }
        return fractions.get(currency_code, 'Cent')

    def get_currency_fraction_units(self, currency_code):
        """Get currency fraction units"""
        units = {
            'OMR': 1000,  # 1 OMR = 1000 Baisa
            'USD': 100,
            'EUR': 100,
            'SAR': 100,
            'AED': 100,
            'GBP': 100
        }
        return units.get(currency_code, 100)

    def get_currency_number_format(self, currency_code):
        """Get currency number format"""
        formats = {
            'OMR': '#,###.###',  # 3 decimal places for Baisa
            'USD': '#,###.##',
            'EUR': '#,###.##',
            'SAR': '#,###.##',
            'AED': '#,###.##',
            'GBP': '#,###.##'
        }
        return formats.get(currency_code, '#,###.##')

    def set_default_currency(self):
        """Set OMR as default currency for the company"""
        try:
            companies = frappe.get_all('Company', fields=['name'])
            for company in companies:
                company_doc = frappe.get_doc('Company', company.name)
                if company_doc.default_currency != 'OMR':
                    company_doc.default_currency = 'OMR'
                    company_doc.save()
                    print(f"Set default currency to OMR for company: {company.name}")
        except Exception as e:
            frappe.log_error(f"Default currency setup error: {str(e)}")

    def initialize_exchange_rates(self):
        """Initialize exchange rates for supported currencies"""
        # Default rates (will be updated with live rates)
        default_rates = {
            ('USD', 'OMR'): 0.385,  # 1 USD = 0.385 OMR (approximate)
            ('EUR', 'OMR'): 0.420,  # 1 EUR = 0.420 OMR (approximate)
            ('SAR', 'OMR'): 0.103,  # 1 SAR = 0.103 OMR (approximate)
            ('AED', 'OMR'): 0.105,  # 1 AED = 0.105 OMR (approximate)
            ('GBP', 'OMR'): 0.486,  # 1 GBP = 0.486 OMR (approximate)
            ('OMR', 'USD'): 2.597,  # 1 OMR = 2.597 USD
            ('OMR', 'EUR'): 2.381,  # 1 OMR = 2.381 EUR
            ('OMR', 'SAR'): 9.737,  # 1 OMR = 9.737 SAR
            ('OMR', 'AED'): 9.534,  # 1 OMR = 9.534 AED
            ('OMR', 'GBP'): 2.057   # 1 OMR = 2.057 GBP
        }

        for (from_currency, to_currency), rate in default_rates.items():
            self.create_or_update_exchange_rate(from_currency, to_currency, rate)

    def create_or_update_exchange_rate(self, from_currency, to_currency, rate, date=None):
        """Create or update exchange rate"""
        if not date:
            date = today()
            
        existing_rate = frappe.db.get_value(
            'Currency Exchange',
            {
                'from_currency': from_currency,
                'to_currency': to_currency,
                'date': date
            },
            'name'
        )

        if existing_rate:
            # Update existing rate
            exchange_doc = frappe.get_doc('Currency Exchange', existing_rate)
            exchange_doc.exchange_rate = flt(rate, 6)
            exchange_doc.save()
        else:
            # Create new rate
            exchange_doc = frappe.new_doc('Currency Exchange')
            exchange_doc.from_currency = from_currency
            exchange_doc.to_currency = to_currency
            exchange_doc.date = date
            exchange_doc.exchange_rate = flt(rate, 6)
            exchange_doc.for_buying = 1
            exchange_doc.for_selling = 1
            exchange_doc.insert()

    def update_live_exchange_rates(self):
        """Update exchange rates from live API sources"""
        try:
            # Update rates for major currencies
            for currency in ['USD', 'EUR', 'SAR', 'AED', 'GBP']:
                if currency != self.base_currency:
                    # Get rate from OMR to currency
                    rate_from_omr = self.fetch_live_rate('OMR', currency)
                    if rate_from_omr:
                        self.create_or_update_exchange_rate('OMR', currency, rate_from_omr)
                    
                    # Get rate from currency to OMR
                    rate_to_omr = self.fetch_live_rate(currency, 'OMR')
                    if rate_to_omr:
                        self.create_or_update_exchange_rate(currency, 'OMR', rate_to_omr)

            frappe.db.commit()
            return True

        except Exception as e:
            frappe.log_error(f"Live exchange rate update error: {str(e)}")
            return False

    def fetch_live_rate(self, from_currency, to_currency):
        """Fetch live exchange rate from external API"""
        try:
            # Using Free Currency API (you can replace with preferred provider)
            api_url = f"https://api.freecurrencyapi.com/v1/latest"
            params = {
                'apikey': 'fca_live_YOUR_API_KEY_HERE',  # Replace with actual API key
                'base_currency': from_currency,
                'currencies': to_currency
            }
            
            response = requests.get(api_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                rate = data.get('data', {}).get(to_currency)
                
                if rate:
                    return flt(rate, 6)
            
            return None
            
        except Exception as e:
            frappe.log_error(f"Live rate fetch error for {from_currency} to {to_currency}: {str(e)}")
            return None

    def get_exchange_rate(self, from_currency, to_currency, date=None):
        """Get exchange rate between two currencies"""
        if from_currency == to_currency:
            return 1.0
        
        if not date:
            date = today()
        
        # Try to get exact date rate
        rate = frappe.db.get_value(
            'Currency Exchange',
            {
                'from_currency': from_currency,
                'to_currency': to_currency,
                'date': date
            },
            'exchange_rate'
        )
        
        if rate:
            return flt(rate)
        
        # Try to get latest available rate
        latest_rate = frappe.db.sql("""
            SELECT exchange_rate 
            FROM `tabCurrency Exchange`
            WHERE from_currency = %s AND to_currency = %s
            ORDER BY date DESC
            LIMIT 1
        """, (from_currency, to_currency))
        
        if latest_rate:
            return flt(latest_rate[0][0])
        
        # If no rate found, try reverse rate
        reverse_rate = self.get_reverse_rate(from_currency, to_currency, date)
        if reverse_rate:
            return 1.0 / reverse_rate
        
        # Return 1.0 as fallback
        return 1.0

    def get_reverse_rate(self, from_currency, to_currency, date=None):
        """Get reverse exchange rate"""
        if not date:
            date = today()
        
        rate = frappe.db.get_value(
            'Currency Exchange',
            {
                'from_currency': to_currency,
                'to_currency': from_currency,
                'date': date
            },
            'exchange_rate'
        )
        
        return flt(rate) if rate else None

    def convert_amount(self, amount, from_currency, to_currency, date=None):
        """Convert amount from one currency to another"""
        if from_currency == to_currency:
            return flt(amount, self.decimal_places.get(to_currency, 2))
        
        exchange_rate = self.get_exchange_rate(from_currency, to_currency, date)
        converted_amount = flt(amount) * flt(exchange_rate)
        
        return flt(converted_amount, self.decimal_places.get(to_currency, 2))

    def format_currency(self, amount, currency, show_symbol=True):
        """Format currency amount with proper symbol and precision"""
        precision = self.decimal_places.get(currency, 2)
        formatted_amount = f"{amount:,.{precision}f}"
        
        if show_symbol:
            symbol = self.currency_symbols.get(currency, currency)
            if currency in ['OMR', 'SAR', 'AED']:
                # Arabic currencies - symbol after amount
                return f"{formatted_amount} {symbol}"
            else:
                # Western currencies - symbol before amount
                return f"{symbol} {formatted_amount}"
        
        return formatted_amount

    def get_currency_in_words(self, amount, currency):
        """Convert currency amount to words (Arabic/English)"""
        # This is a placeholder - implement currency to words conversion
        # You can use libraries like num2words for English
        # and create Arabic number-to-words conversion
        
        if currency == 'OMR':
            return self.omr_to_words(amount)
        else:
            return f"{amount} {currency}"

    def omr_to_words(self, amount):
        """Convert OMR amount to Arabic words"""
        # Placeholder implementation
        # Should convert like: 123.456 OMR -> "مائة وثلاثة وعشرون ريالاً عمانياً وأربعمائة وستة وخمسون بيسة"
        
        omr_part = int(amount)
        baisa_part = int((amount - omr_part) * 1000)
        
        return f"{omr_part} ريال عماني و {baisa_part} بيسة"


# API Methods

@frappe.whitelist()
def get_supported_currencies():
    """Get list of supported currencies"""
    try:
        currency_manager = OmanMultiCurrencyManager()
        
        currencies = []
        for currency_code in currency_manager.supported_currencies:
            currencies.append({
                'code': currency_code,
                'symbol': currency_manager.currency_symbols.get(currency_code, currency_code),
                'decimal_places': currency_manager.decimal_places.get(currency_code, 2)
            })
        
        return {
            'success': True,
            'currencies': currencies,
            'base_currency': currency_manager.base_currency
        }
        
    except Exception as e:
        frappe.log_error(f"Get currencies error: {str(e)}")
        return {'success': False, 'error': str(e)}


@frappe.whitelist()
def convert_currency(amount, from_currency, to_currency, date=None):
    """Convert currency amount"""
    try:
        currency_manager = OmanMultiCurrencyManager()
        converted_amount = currency_manager.convert_amount(amount, from_currency, to_currency, date)
        
        return {
            'success': True,
            'original_amount': flt(amount, currency_manager.decimal_places.get(from_currency, 2)),
            'converted_amount': converted_amount,
            'from_currency': from_currency,
            'to_currency': to_currency,
            'exchange_rate': currency_manager.get_exchange_rate(from_currency, to_currency, date),
            'formatted_amount': currency_manager.format_currency(converted_amount, to_currency)
        }
        
    except Exception as e:
        frappe.log_error(f"Currency conversion error: {str(e)}")
        return {'success': False, 'error': str(e)}


@frappe.whitelist()
def get_exchange_rate(from_currency, to_currency, date=None):
    """Get exchange rate between currencies"""
    try:
        currency_manager = OmanMultiCurrencyManager()
        rate = currency_manager.get_exchange_rate(from_currency, to_currency, date)
        
        return {
            'success': True,
            'from_currency': from_currency,
            'to_currency': to_currency,
            'exchange_rate': rate,
            'date': date or today()
        }
        
    except Exception as e:
        frappe.log_error(f"Get exchange rate error: {str(e)}")
        return {'success': False, 'error': str(e)}


@frappe.whitelist()
def update_exchange_rates():
    """Update exchange rates from live sources"""
    try:
        currency_manager = OmanMultiCurrencyManager()
        success = currency_manager.update_live_exchange_rates()
        
        if success:
            return {
                'success': True,
                'message': 'Exchange rates updated successfully',
                'timestamp': now()
            }
        else:
            return {
                'success': False,
                'message': 'Failed to update some exchange rates',
                'timestamp': now()
            }
        
    except Exception as e:
        frappe.log_error(f"Exchange rate update error: {str(e)}")
        return {'success': False, 'error': str(e)}


# Installation and setup functions

def setup_multi_currency_system():
    """Setup multi-currency system during app installation"""
    try:
        currency_manager = OmanMultiCurrencyManager()
        currency_manager.setup_currencies()
        
        # Schedule automatic exchange rate updates
        setup_exchange_rate_scheduler()
        
        return True
        
    except Exception as e:
        frappe.log_error(f"Multi-currency setup error: {str(e)}")
        return False


def setup_exchange_rate_scheduler():
    """Setup scheduled job for exchange rate updates"""
    try:
        # This function should be called from hooks.py to schedule daily updates
        pass
    except Exception as e:
        frappe.log_error(f"Exchange rate scheduler setup error: {str(e)}")


# Scheduled task function (to be called from hooks.py)
def daily_exchange_rate_update():
    """Daily scheduled task to update exchange rates"""
    try:
        currency_manager = OmanMultiCurrencyManager()
        success = currency_manager.update_live_exchange_rates()
        
        if success:
            frappe.logger().info("Daily exchange rate update completed successfully")
        else:
            frappe.logger().warning("Daily exchange rate update completed with some errors")
            
    except Exception as e:
        frappe.log_error(f"Daily exchange rate update error: {str(e)}")


def validate_multi_currency_transaction(doc, method):
    """Validate multi-currency transactions"""
    try:
        if hasattr(doc, 'currency') and doc.currency:
            currency_manager = OmanMultiCurrencyManager()
            
            # Validate currency is supported
            if doc.currency not in currency_manager.supported_currencies:
                frappe.throw(_("Currency {0} is not supported").format(doc.currency))
            
            # Update conversion rate if needed
            if hasattr(doc, 'conversion_rate') and doc.currency != currency_manager.base_currency:
                latest_rate = currency_manager.get_exchange_rate(doc.currency, currency_manager.base_currency)
                if not doc.conversion_rate or abs(doc.conversion_rate - latest_rate) > 0.01:
                    doc.conversion_rate = latest_rate
                    
    except Exception as e:
        frappe.log_error(f"Multi-currency validation error: {str(e)}") 