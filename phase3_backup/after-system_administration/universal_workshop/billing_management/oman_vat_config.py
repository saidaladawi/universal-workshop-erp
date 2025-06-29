# -*- coding: utf-8 -*-
# Copyright (c) 2024, Said Al-Adowi and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _


class OmanVATConfig:
    """
    Configuration class for Oman VAT setup in ERPNext v15
    Based on ERPGulf Oman VAT module requirements
    """

    def __init__(self):
        self.vat_rate = 5.0  # Oman VAT rate is 5%
        self.currency = "OMR"  # Omani Rial
        self.decimal_places = 3  # Baisa precision (1 OMR = 1000 Baisa)
        self.company = self._get_default_company()

    def _get_default_company(self):
        """Get default company for VAT setup"""
        # Try user default first
        company = frappe.defaults.get_user_default("Company")
        if company:
            return company

        # Try global default
        try:
            company = frappe.db.get_single_value("Global Defaults", "default_company")
            if company:
                return company
        except:
            pass

        # Get first available company
        companies = frappe.get_list("Company", limit=1)
        if companies:
            return companies[0].name

        return None

    def setup_oman_vat_accounts(self):
        """
        Setup VAT accounts required for Oman compliance
        """
        try:
            # Skip VAT setup if no company is available during installation
            if not self.company:
                frappe.logger().info("Skipping VAT setup - no company available")
                return
            # Create Output VAT Account (Sales)
            output_vat_account = {
                "doctype": "Account",
                "account_name": "Output VAT 5%",
                "parent_account": "Duties and Taxes - UW",
                "account_type": "Tax",
                "account_currency": self.currency,
                "company": frappe.defaults.get_user_default("Company"),
                "is_group": 0,
            }

            if not frappe.db.exists("Account", output_vat_account["account_name"]):
                output_account = frappe.get_doc(output_vat_account)
                output_account.insert()
                frappe.db.commit()
                frappe.logger().info(
                    _("Created Output VAT account: {0}").format(output_vat_account["account_name"])
                )

            # Create Input VAT Account (Purchases)
            input_vat_account = {
                "doctype": "Account",
                "account_name": "Input VAT 5%",
                "parent_account": "Duties and Taxes - UW",
                "account_type": "Tax",
                "account_currency": self.currency,
                "company": frappe.defaults.get_user_default("Company"),
                "is_group": 0,
            }

            if not frappe.db.exists("Account", input_vat_account["account_name"]):
                input_account = frappe.get_doc(input_vat_account)
                input_account.insert()
                frappe.db.commit()
                frappe.logger().info(
                    _("Created Input VAT account: {0}").format(input_vat_account["account_name"])
                )

        except Exception as e:
            frappe.logger().error(_("Error creating VAT accounts: {0}").format(str(e)))
            frappe.throw(
                _("Failed to create VAT accounts. Please check permissions and try again.")
            )

    def setup_sales_tax_template(self):
        """
        Setup Sales Tax Template for Oman VAT
        """
        try:
            template_name = "Oman VAT 5% - Sales"

            if not frappe.db.exists("Sales Taxes and Charges Template", template_name):
                template = frappe.get_doc(
                    {
                        "doctype": "Sales Taxes and Charges Template",
                        "title": template_name,
                        "company": frappe.defaults.get_user_default("Company"),
                        "taxes": [
                            {
                                "charge_type": "On Net Total",
                                "account_head": "Output VAT 5%",
                                "description": "VAT @ 5%",
                                "rate": self.vat_rate,
                            }
                        ],
                    }
                )
                template.insert()
                frappe.db.commit()
                frappe.logger().info(_("Created Sales Tax Template: {0}").format(template_name))

        except Exception as e:
            frappe.logger().error(_("Error creating Sales Tax Template: {0}").format(str(e)))
            frappe.throw(_("Failed to create Sales Tax Template. Please check account setup."))

    def setup_purchase_tax_template(self):
        """
        Setup Purchase Tax Template for Oman VAT
        """
        try:
            template_name = "Oman VAT 5% - Purchase"

            if not frappe.db.exists("Purchase Taxes and Charges Template", template_name):
                template = frappe.get_doc(
                    {
                        "doctype": "Purchase Taxes and Charges Template",
                        "title": template_name,
                        "company": frappe.defaults.get_user_default("Company"),
                        "taxes": [
                            {
                                "charge_type": "On Net Total",
                                "account_head": "Input VAT 5%",
                                "description": "VAT @ 5%",
                                "rate": self.vat_rate,
                            }
                        ],
                    }
                )
                template.insert()
                frappe.db.commit()
                frappe.logger().info(_("Created Purchase Tax Template: {0}").format(template_name))

        except Exception as e:
            frappe.logger().error(_("Error creating Purchase Tax Template: {0}").format(str(e)))
            frappe.throw(_("Failed to create Purchase Tax Template. Please check account setup."))

    def setup_item_tax_templates(self):
        """
        Setup Item Tax Templates for different VAT scenarios
        """
        try:
            # Standard VAT 5%
            standard_template = {
                "doctype": "Item Tax Template",
                "title": "Oman Standard VAT 5%",
                "company": frappe.defaults.get_user_default("Company"),
                "taxes": [{"tax_type": "Output VAT 5%", "tax_rate": self.vat_rate}],
            }

            if not frappe.db.exists("Item Tax Template", standard_template["title"]):
                template = frappe.get_doc(standard_template)
                template.insert()
                frappe.db.commit()
                frappe.logger().info(
                    _("Created Item Tax Template: {0}").format(standard_template["title"])
                )

            # Zero-rated VAT (Exports)
            zero_template = {
                "doctype": "Item Tax Template",
                "title": "Oman Zero Rated VAT",
                "company": frappe.defaults.get_user_default("Company"),
                "taxes": [{"tax_type": "Output VAT 5%", "tax_rate": 0.0}],
            }

            if not frappe.db.exists("Item Tax Template", zero_template["title"]):
                template = frappe.get_doc(zero_template)
                template.insert()
                frappe.db.commit()
                frappe.logger().info(
                    _("Created Item Tax Template: {0}").format(zero_template["title"])
                )

        except Exception as e:
            frappe.logger().error(_("Error creating Item Tax Templates: {0}").format(str(e)))
            frappe.throw(_("Failed to create Item Tax Templates. Please check account setup."))

    def setup_currency_precision(self):
        """
        Setup currency precision for OMR (3 decimal places for Baisa)
        """
        try:
            # Update Currency settings for OMR
            if frappe.db.exists("Currency", self.currency):
                currency_doc = frappe.get_doc("Currency", self.currency)
                currency_doc.fraction_units = self.decimal_places
                currency_doc.save()
                frappe.db.commit()
                frappe.logger().info(
                    _("Updated OMR currency precision to {0} decimal places").format(
                        self.decimal_places
                    )
                )
            else:
                # Create OMR currency if doesn't exist
                currency_doc = frappe.get_doc(
                    {
                        "doctype": "Currency",
                        "currency_name": "Omani Rial",
                        "currency_symbol": "ر.ع.",
                        "fraction": "Baisa",
                        "fraction_units": self.decimal_places,
                        "number_format": "#,##0.000",
                        "smallest_currency_fraction_value": 0.001,
                    }
                )
                currency_doc.insert()
                frappe.db.commit()
                frappe.logger().info(
                    _("Created OMR currency with {0} decimal places").format(self.decimal_places)
                )

        except Exception as e:
            frappe.logger().error(_("Error setting up currency precision: {0}").format(str(e)))

    def validate_vat_number(self, vat_number):
        """
        Validate Oman VAT number format
        Format: OMxxxxxxxxxxxxxxx (OM followed by 15 digits)
        """
        import re

        if not vat_number:
            return True

        # Oman VAT format validation
        if not re.match(r"^OM\d{15}$", vat_number):
            frappe.throw(_("Invalid Oman VAT number format. Should be OMxxxxxxxxxxxxxxx"))

        return True

    def setup_complete_vat_configuration(self):
        """
        Complete setup of Oman VAT configuration
        """
        frappe.logger().info("Starting Oman VAT configuration setup...")

        # Setup currency precision first
        self.setup_currency_precision()

        # Setup VAT accounts
        self.setup_oman_vat_accounts()

        # Setup tax templates
        self.setup_sales_tax_template()
        self.setup_purchase_tax_template()

        # Setup item tax templates
        self.setup_item_tax_templates()

        frappe.logger().info("Oman VAT configuration completed successfully!")

        return {"status": "success", "message": _("Oman VAT configuration completed successfully")}


@frappe.whitelist()
def setup_oman_vat():
    """
    Whitelist method to setup Oman VAT configuration
    """
    vat_config = OmanVATConfig()
    return vat_config.setup_complete_vat_configuration()


@frappe.whitelist()
def validate_oman_vat_number(vat_number):
    """
    Whitelist method to validate Oman VAT number
    """
    vat_config = OmanVATConfig()
    return vat_config.validate_vat_number(vat_number)
