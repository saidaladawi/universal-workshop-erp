# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

"""Custom fields for automotive parts management in ERPNext Item doctype"""


def get_item_custom_fields():
	"""Get custom fields for Item doctype to support automotive parts"""

	custom_fields = {
		"Item": [
			# Section: Automotive Parts Information
			{
				"fieldname": "automotive_parts_section",
				"fieldtype": "Section Break",
				"label": "Automotive Parts Information",
				"insert_after": "description",
				"depends_on": 'eval:doc.item_group && (doc.item_group.includes("Auto Parts") || doc.item_group.includes("قطع غيار"))',
				"collapsible": 1,
			},
			# OEM Part Number (English)
			{
				"fieldname": "oem_part_number",
				"fieldtype": "Data",
				"label": "OEM Part Number",
				"insert_after": "automotive_parts_section",
				"length": 100,
				"search_index": 1,
				"in_list_view": 0,
				"unique": 0,
				"description": "Original Equipment Manufacturer part number",
			},
			# OEM Part Number (Arabic)
			{
				"fieldname": "oem_part_number_ar",
				"fieldtype": "Data",
				"label": "رقم القطعة الأصلية",
				"insert_after": "oem_part_number",
				"length": 100,
				"translatable": 1,
				"description": "رقم قطعة غيار الشركة المصنعة الأصلية",
			},
			# Column Break
			{
				"fieldname": "automotive_col_break_1",
				"fieldtype": "Column Break",
				"insert_after": "oem_part_number_ar",
			},
			# Aftermarket Part Number
			{
				"fieldname": "aftermarket_part_number",
				"fieldtype": "Data",
				"label": "Aftermarket Part Number",
				"insert_after": "automotive_col_break_1",
				"length": 100,
				"search_index": 1,
				"description": "Compatible aftermarket part number",
			},
			# Part Category (Arabic/English)
			{
				"fieldname": "part_category",
				"fieldtype": "Select",
				"label": "Part Category / فئة القطعة",
				"insert_after": "aftermarket_part_number",
				"options": "\nEngine Parts / قطع المحرك\nTransmission / ناقل الحركة\nBrake System / نظام الفرامل\nSuspension / نظام التعليق\nElectrical / النظام الكهربائي\nExhaust System / نظام العادم\nCooling System / نظام التبريد\nFuel System / نظام الوقود\nSteering / نظام التوجيه\nBody Parts / قطع الهيكل\nInterior / الداخلية\nFilters / المرشحات\nBelts & Hoses / الأحزمة والخراطيم\nFluids & Oils / السوائل والزيوت\nTires & Wheels / الإطارات والعجلات\nBattery & Ignition / البطارية والإشعال\nLights & Signals / الأضواء والإشارات\nOther / أخرى",
				"in_list_view": 1,
				"in_standard_filter": 1,
			},
			# Vehicle Compatibility Section
			{
				"fieldname": "vehicle_compatibility_section",
				"fieldtype": "Section Break",
				"label": "Vehicle Compatibility / توافق المركبات",
				"insert_after": "part_category",
				"collapsible": 1,
			},
			# Vehicle Make
			{
				"fieldname": "vehicle_make",
				"fieldtype": "Link",
				"label": "Vehicle Make / صانع المركبة",
				"insert_after": "vehicle_compatibility_section",
				"options": "Vehicle Make",
				"in_list_view": 0,
				"in_standard_filter": 1,
			},
			# Vehicle Model
			{
				"fieldname": "vehicle_model",
				"fieldtype": "Link",
				"label": "Vehicle Model / طراز المركبة",
				"insert_after": "vehicle_make",
				"options": "Vehicle Model",
				"depends_on": "vehicle_make",
			},
			# Column Break
			{"fieldname": "vehicle_col_break", "fieldtype": "Column Break", "insert_after": "vehicle_model"},
			# Year From
			{
				"fieldname": "year_from",
				"fieldtype": "Int",
				"label": "Year From / من سنة",
				"insert_after": "vehicle_col_break",
				"description": "Starting year of compatibility",
			},
			# Year To
			{
				"fieldname": "year_to",
				"fieldtype": "Int",
				"label": "Year To / إلى سنة",
				"insert_after": "year_from",
				"description": "Ending year of compatibility",
			},
			# Cross Reference Section
			{
				"fieldname": "cross_reference_section",
				"fieldtype": "Section Break",
				"label": "Cross References / المراجع المتقاطعة",
				"insert_after": "year_to",
				"collapsible": 1,
			},
			# Cross Reference Numbers Table
			{
				"fieldname": "cross_reference_numbers",
				"fieldtype": "Table",
				"label": "Cross Reference Numbers",
				"insert_after": "cross_reference_section",
				"options": "Part Cross Reference",
				"description": "Alternative part numbers from different manufacturers",
			},
			# Physical Specifications Section
			{
				"fieldname": "physical_specs_section",
				"fieldtype": "Section Break",
				"label": "Physical Specifications / المواصفات الفيزيائية",
				"insert_after": "cross_reference_numbers",
				"collapsible": 1,
			},
			# Dimensions
			{
				"fieldname": "part_length",
				"fieldtype": "Float",
				"label": "Length (mm) / الطول",
				"insert_after": "physical_specs_section",
				"precision": 2,
			},
			{
				"fieldname": "part_width",
				"fieldtype": "Float",
				"label": "Width (mm) / العرض",
				"insert_after": "part_length",
				"precision": 2,
			},
			{
				"fieldname": "part_height",
				"fieldtype": "Float",
				"label": "Height (mm) / الارتفاع",
				"insert_after": "part_width",
				"precision": 2,
			},
			# Column Break
			{"fieldname": "specs_col_break", "fieldtype": "Column Break", "insert_after": "part_height"},
			# Material
			{
				"fieldname": "part_material",
				"fieldtype": "Data",
				"label": "Material / المادة",
				"insert_after": "specs_col_break",
				"length": 100,
			},
			# Color
			{
				"fieldname": "part_color",
				"fieldtype": "Data",
				"label": "Color / اللون",
				"insert_after": "part_material",
				"length": 50,
			},
			# Installation Notes
			{
				"fieldname": "installation_notes",
				"fieldtype": "Text",
				"label": "Installation Notes / ملاحظات التركيب",
				"insert_after": "part_color",
				"translatable": 1,
			},
			# Inventory Management Section
			{
				"fieldname": "inventory_mgmt_section",
				"fieldtype": "Section Break",
				"label": "Inventory Management / إدارة المخزون",
				"insert_after": "installation_notes",
				"collapsible": 1,
			},
			# Minimum Stock Level
			{
				"fieldname": "min_stock_level",
				"fieldtype": "Float",
				"label": "Minimum Stock Level / أدنى مستوى مخزون",
				"insert_after": "inventory_mgmt_section",
				"default": 0,
				"precision": 2,
			},
			# Maximum Stock Level
			{
				"fieldname": "max_stock_level",
				"fieldtype": "Float",
				"label": "Maximum Stock Level / أقصى مستوى مخزون",
				"insert_after": "min_stock_level",
				"default": 0,
				"precision": 2,
			},
			# Column Break
			{
				"fieldname": "inventory_col_break",
				"fieldtype": "Column Break",
				"insert_after": "max_stock_level",
			},
			# Reorder Quantity
			{
				"fieldname": "reorder_quantity",
				"fieldtype": "Float",
				"label": "Reorder Quantity / كمية إعادة الطلب",
				"insert_after": "inventory_col_break",
				"default": 0,
				"precision": 2,
			},
			# Preferred Supplier
			{
				"fieldname": "preferred_supplier",
				"fieldtype": "Link",
				"label": "Preferred Supplier / المورد المفضل",
				"insert_after": "reorder_quantity",
				"options": "Supplier",
			},
			# Fast Moving Part
			{
				"fieldname": "is_fast_moving",
				"fieldtype": "Check",
				"label": "Fast Moving Part / قطعة سريعة الحركة",
				"insert_after": "preferred_supplier",
				"default": 0,
			},
			# Barcode & QR Code Section
			{
				"fieldname": "barcode_section",
				"fieldtype": "Section Break",
				"label": "Barcode & QR Code / رموز الباركود والكيو آر",
				"insert_after": "is_fast_moving",
				"collapsible": 1,
			},
			# Barcode
			{
				"fieldname": "barcode",
				"fieldtype": "Data",
				"label": "Barcode / الباركود",
				"insert_after": "barcode_section",
				"read_only": 1,
				"description": "Auto-generated barcode for part scanning",
			},
			# QR Code Data
			{
				"fieldname": "qr_code_data",
				"fieldtype": "Long Text",
				"label": "QR Code Data / بيانات الكيو آر كود",
				"insert_after": "barcode",
				"read_only": 1,
				"description": "JSON data embedded in QR code",
			},
			# Column Break
			{"fieldname": "col_break_barcode", "fieldtype": "Column Break", "insert_after": "qr_code_data"},
			# Barcode Format
			{
				"fieldname": "barcode_format",
				"fieldtype": "Select",
				"label": "Barcode Format / تنسيق الباركود",
				"insert_after": "col_break_barcode",
				"options": "Code128\nEAN13\nQR Code",
				"default": "Code128",
			},
			# Print Label Button
			{
				"fieldname": "print_barcode_label",
				"fieldtype": "Button",
				"label": "Print Label / طباعة اللصقة",
				"insert_after": "barcode_format",
				"description": "Generate and print barcode label",
			},
			# Generate Codes Button
			{
				"fieldname": "generate_codes",
				"fieldtype": "Button",
				"label": "Generate Codes / إنشاء الرموز",
				"insert_after": "print_barcode_label",
				"description": "Generate barcode and QR code for this item",
			},
		]
	}

	return custom_fields


def get_part_cross_reference_fields():
	"""Get fields for Part Cross Reference child table"""

	return [
		{
			"fieldname": "manufacturer",
			"fieldtype": "Link",
			"label": "Manufacturer / الشركة المصنعة",
			"options": "Supplier",
			"reqd": 1,
			"in_list_view": 1,
		},
		{
			"fieldname": "cross_ref_number",
			"fieldtype": "Data",
			"label": "Cross Reference Number",
			"reqd": 1,
			"in_list_view": 1,
			"length": 100,
		},
		{
			"fieldname": "reference_type",
			"fieldtype": "Select",
			"label": "Type / النوع",
			"options": "OEM\nAftermarket\nGeneric\nSupercessor",
			"in_list_view": 1,
			"default": "Aftermarket",
		},
		{
			"fieldname": "is_primary",
			"fieldtype": "Check",
			"label": "Primary Reference",
			"default": 0,
			"in_list_view": 1,
		},
	]


def get_barcode_qr_fields():
	"""Get barcode and QR code fields for Item DocType"""

	return [
		{
			"fieldname": "barcode_section",
			"fieldtype": "Section Break",
			"label": "Barcode & QR Code / رموز الباركود والكيو آر",
			"collapsible": 1,
		},
		{
			"fieldname": "barcode",
			"fieldtype": "Data",
			"label": "Barcode / الباركود",
			"read_only": 1,
			"description": "Auto-generated barcode for part scanning",
		},
		{
			"fieldname": "qr_code_data",
			"fieldtype": "Long Text",
			"label": "QR Code Data / بيانات الكيو آر كود",
			"read_only": 1,
			"description": "JSON data embedded in QR code",
		},
		{"fieldname": "col_break_barcode", "fieldtype": "Column Break"},
		{
			"fieldname": "barcode_format",
			"fieldtype": "Select",
			"label": "Barcode Format / تنسيق الباركود",
			"options": "Code128\nEAN13\nQR Code",
			"default": "Code128",
		},
		{
			"fieldname": "print_barcode_label",
			"fieldtype": "Button",
			"label": "Print Label / طباعة اللصقة",
			"description": "Generate and print barcode label",
		},
		{
			"fieldname": "generate_codes",
			"fieldtype": "Button",
			"label": "Generate Codes / إنشاء الرموز",
			"description": "Generate barcode and QR code for this item",
		},
	]


def install_item_custom_fields():
	"""Install automotive custom fields for Item doctype"""
	import frappe
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

	try:
		# Get custom fields definition
		custom_fields = get_item_custom_fields()

		# Install custom fields
		create_custom_fields(custom_fields, update=True)

		# Create database indexes for performance
		setup_automotive_indexes()

		frappe.msgprint("Automotive parts custom fields installed successfully")
		frappe.log_error("Custom fields installation completed", "Parts Inventory Setup")

	except Exception as e:
		frappe.log_error(f"Error installing custom fields: {e!s}", "Parts Inventory Setup Error")
		frappe.throw(f"Failed to install custom fields: {e!s}")


def setup_automotive_indexes():
	"""Setup database indexes for automotive parts search performance"""

	try:
		# Index for OEM part number search
		frappe.db.sql("""
            CREATE INDEX IF NOT EXISTS idx_item_oem_part_number
            ON `tabItem` (oem_part_number)
        """)

		# Index for aftermarket part number search
		frappe.db.sql("""
            CREATE INDEX IF NOT EXISTS idx_item_aftermarket_part_number
            ON `tabItem` (aftermarket_part_number)
        """)

		# Index for part category filtering
		frappe.db.sql("""
            CREATE INDEX IF NOT EXISTS idx_item_part_category
            ON `tabItem` (part_category)
        """)

		# Index for vehicle make compatibility
		frappe.db.sql("""
            CREATE INDEX IF NOT EXISTS idx_item_vehicle_make
            ON `tabItem` (vehicle_make)
        """)

		# Index for vehicle compatibility range
		frappe.db.sql("""
            CREATE INDEX IF NOT EXISTS idx_item_vehicle_years
            ON `tabItem` (year_from, year_to)
        """)

		# Composite index for parts search
		frappe.db.sql("""
            CREATE INDEX IF NOT EXISTS idx_item_automotive_search
            ON `tabItem` (part_category, vehicle_make, vehicle_model)
        """)

		frappe.db.commit()

	except Exception as e:
		frappe.log_error(f"Error creating automotive indexes: {e!s}", "Parts Inventory Index Error")
