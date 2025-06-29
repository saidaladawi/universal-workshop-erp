# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

"""Barcode and QR code generation utilities for automotive parts inventory"""

import base64
import io
import json
import re

import barcode
import qrcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont

import frappe
from frappe import _


def generate_item_barcode(item_code, barcode_format="code128"):
	"""Generate barcode for automotive parts with configurable format"""

	try:
		# Get barcode class
		if barcode_format.lower() == "code128":
			barcode_class = barcode.get_barcode_class("code128")
		elif barcode_format.lower() == "ean13":
			barcode_class = barcode.get_barcode_class("ean13")
		else:
			barcode_class = barcode.get_barcode_class("code128")

		# Generate barcode
		barcode_instance = barcode_class(item_code, writer=ImageWriter())

		# Save to memory buffer
		buffer = io.BytesIO()
		barcode_instance.write(
			buffer,
			options={
				"module_width": 0.3,
				"module_height": 8.0,
				"quiet_zone": 2.5,
				"font_size": 10,
				"text_distance": 5.0,
				"background": "white",
				"foreground": "black",
			},
		)

		# Convert to base64
		buffer.seek(0)
		barcode_base64 = base64.b64encode(buffer.getvalue()).decode()

		return {
			"success": True,
			"barcode_base64": barcode_base64,
			"format": barcode_format,
			"data": item_code,
		}

	except Exception as e:
		frappe.log_error(f"Barcode generation error: {e!s}", "Barcode Generation")
		return {"success": False, "error": str(e)}


def generate_item_qr_code(item_code, include_details=True):
	"""Generate QR code for automotive parts with optional detailed information"""

	try:
		# Get item details if requested
		qr_data = {"item_code": item_code}

		if include_details:
			item = frappe.get_doc("Item", item_code)
			qr_data.update(
				{
					"item_name": item.item_name,
					"oem_part_number": getattr(item, "oem_part_number", ""),
					"aftermarket_part_number": getattr(item, "aftermarket_part_number", ""),
					"part_category": getattr(item, "part_category", ""),
					"vehicle_make": getattr(item, "vehicle_make", ""),
					"vehicle_model": getattr(item, "vehicle_model", ""),
					"standard_rate": float(item.standard_rate) if item.standard_rate else 0,
				}
			)

		# Convert to JSON string
		qr_content = json.dumps(qr_data, ensure_ascii=False)

		# Generate QR code
		qr = qrcode.QRCode(
			version=1,
			error_correction=qrcode.constants.ERROR_CORRECT_L,
			box_size=6,
			border=2,
		)
		qr.add_data(qr_content)
		qr.make(fit=True)

		# Create image
		qr_image = qr.make_image(fill_color="black", back_color="white")

		# Save to memory buffer
		buffer = io.BytesIO()
		qr_image.save(buffer, format="PNG")

		# Convert to base64
		buffer.seek(0)
		qr_base64 = base64.b64encode(buffer.getvalue()).decode()

		return {"success": True, "qr_code_base64": qr_base64, "data": qr_data, "content": qr_content}

	except Exception as e:
		frappe.log_error(f"QR code generation error: {e!s}", "QR Code Generation")
		return {"success": False, "error": str(e)}


def generate_composite_label(item_code, label_size=(400, 200), language="en"):
	"""Generate composite label with both barcode and QR code plus Arabic text"""

	try:
		# Get item details
		item = frappe.get_doc("Item", item_code)

		# Generate barcode and QR code
		barcode_result = generate_item_barcode(item_code)
		qr_result = generate_item_qr_code(item_code, include_details=False)

		if not barcode_result["success"] or not qr_result["success"]:
			return {"success": False, "error": "Failed to generate codes"}

		# Create composite image
		label_img = Image.new("RGB", label_size, color="white")
		draw = ImageDraw.Draw(label_img)

		# Load barcode image
		barcode_data = base64.b64decode(barcode_result["barcode_base64"])
		barcode_img = Image.open(io.BytesIO(barcode_data))

		# Load QR code image
		qr_data = base64.b64decode(qr_result["qr_code_base64"])
		qr_img = Image.open(io.BytesIO(qr_data))

		# Resize images to fit label
		barcode_img = barcode_img.resize((250, 80))
		qr_img = qr_img.resize((100, 100))

		# Position images
		label_img.paste(barcode_img, (10, 10))
		label_img.paste(qr_img, (280, 50))

		# Add text information
		try:
			# Try to load a font that supports Arabic
			font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
			font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
		except Exception:
			# Fallback to default font
			font = ImageFont.load_default()
			font_small = ImageFont.load_default()

		# Item name (English/Arabic based on language)
		item_name = item.item_name
		if language == "ar" and hasattr(item, "item_name_ar") and item.item_name_ar:
			item_name = item.item_name_ar

		# Draw text
		draw.text((10, 100), f"Item: {item_name}", fill="black", font=font)
		draw.text((10, 120), f"Code: {item_code}", fill="black", font=font_small)

		# OEM part number
		if hasattr(item, "oem_part_number") and item.oem_part_number:
			draw.text((10, 140), f"OEM: {item.oem_part_number}", fill="black", font=font_small)

		# Part category
		if hasattr(item, "part_category") and item.part_category:
			category = item.part_category
			if language == "ar":
				# Extract Arabic category name if available
				if " / " in category:
					category = category.split(" / ")[1]
			draw.text((10, 160), f"Category: {category}", fill="black", font=font_small)

		# Price
		if item.standard_rate:
			draw.text((10, 180), f"Price: OMR {item.standard_rate:.3f}", fill="black", font=font_small)

		# Save to memory buffer
		buffer = io.BytesIO()
		label_img.save(buffer, format="PNG")

		# Convert to base64
		buffer.seek(0)
		label_base64 = base64.b64encode(buffer.getvalue()).decode()

		return {
			"success": True,
			"label_base64": label_base64,
			"item_code": item_code,
			"size": label_size,
			"language": language,
		}

	except Exception as e:
		frappe.log_error(f"Label generation error: {e!s}", "Label Generation")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_item_barcode(item_code, format="code128"):
	"""API method to get barcode for item"""

	if not item_code:
		frappe.throw(_("Item code is required"))

	# Check if item exists
	if not frappe.db.exists("Item", item_code):
		frappe.throw(_("Item not found"))

	result = generate_item_barcode(item_code, format)
	return result


@frappe.whitelist()
def get_item_qr_code(item_code, include_details=True):
	"""API method to get QR code for item"""

	if not item_code:
		frappe.throw(_("Item code is required"))

	# Check if item exists
	if not frappe.db.exists("Item", item_code):
		frappe.throw(_("Item not found"))

	result = generate_item_qr_code(item_code, include_details)
	return result


@frappe.whitelist()
def get_item_label(item_code, width=400, height=200, language="en"):
	"""API method to get composite label for item"""

	if not item_code:
		frappe.throw(_("Item code is required"))

	# Check if item exists
	if not frappe.db.exists("Item", item_code):
		frappe.throw(_("Item not found"))

	label_size = (int(width), int(height))
	result = generate_composite_label(item_code, label_size, language)
	return result


@frappe.whitelist()
def search_item_by_barcode_data(barcode_data):
	"""Search for item by scanned barcode or QR code data"""

	if not barcode_data:
		return {"success": False, "error": "No barcode data provided"}

	try:
		# Try to parse as JSON (QR code)
		try:
			qr_data = json.loads(barcode_data)
			if isinstance(qr_data, dict) and "item_code" in qr_data:
				item_code = qr_data["item_code"]
			else:
				item_code = barcode_data
		except Exception:
			# Treat as simple barcode
			item_code = barcode_data

		# Search for item
		if frappe.db.exists("Item", item_code):
			item = frappe.get_doc("Item", item_code)

			# Get current stock levels
			stock_levels = frappe.get_all(
				"Stock Ledger Entry",
				filters={"item_code": item_code, "is_cancelled": 0},
				fields=["warehouse", "sum(actual_qty) as qty"],
				group_by="warehouse",
				having="sum(actual_qty) > 0",
			)

			return {
				"success": True,
				"item": {
					"item_code": item.item_code,
					"item_name": item.item_name,
					"oem_part_number": getattr(item, "oem_part_number", ""),
					"aftermarket_part_number": getattr(item, "aftermarket_part_number", ""),
					"part_category": getattr(item, "part_category", ""),
					"standard_rate": item.standard_rate,
					"stock_uom": item.stock_uom,
					"vehicle_make": getattr(item, "vehicle_make", ""),
					"vehicle_model": getattr(item, "vehicle_model", ""),
					"is_fast_moving": getattr(item, "is_fast_moving", 0),
					"min_stock_level": getattr(item, "min_stock_level", 0),
					"preferred_supplier": getattr(item, "preferred_supplier", ""),
				},
				"stock_levels": stock_levels,
			}
		else:
			return {"success": False, "error": f"Item not found: {item_code}"}

	except Exception as e:
		frappe.log_error(f"Barcode search error: {e!s}", "Barcode Search")
		return {"success": False, "error": str(e)}


def auto_generate_item_codes(doc, method):
	"""Auto-generate item codes and barcodes for automotive parts"""
	try:
		# Skip if item code is already set or this is not an automotive part
		if doc.item_code or not getattr(doc, 'is_automotive_part', False):
			return

		# Generate item code based on part category and OEM number
		item_code = generate_automotive_item_code(doc)

		if item_code:
			doc.item_code = item_code

		# Auto-generate barcode if needed
		if not doc.barcode and doc.item_code:
			barcode_result = generate_item_barcode(doc.item_code)
			if barcode_result.get('success'):
				# Save barcode to item
				doc.barcode = doc.item_code

		# Generate QR code data
		if not getattr(doc, 'qr_code_data', None):
			qr_result = generate_item_qr_code(doc.item_code, include_details=True)
			if qr_result.get('success'):
				doc.qr_code_data = qr_result.get('qr_code_base64')

	except Exception as e:
		frappe.log_error(f"Auto-generate item codes error: {str(e)}", "Parts Inventory")


def generate_automotive_item_code(item_doc):
    """Generate standardized item code for automotive parts"""
    try:
        # Get part category prefix
        category_map = {
            'Engine': 'ENG',
            'Transmission': 'TRA',
            'Brakes': 'BRK',
            'Suspension': 'SUS',
            'Electrical': 'ELE',
            'Body': 'BOD',
            'Interior': 'INT',
            'Exhaust': 'EXH',
            'Cooling': 'COL',
            'Fuel': 'FUE',
            'Other': 'OTH'
        }

        # Get category prefix
        category = getattr(item_doc, 'part_category', 'Other')
        prefix = category_map.get(category, 'OTH')

        # Get vehicle make code
        vehicle_make = getattr(item_doc, 'vehicle_make', '')
        make_code = vehicle_make[:3].upper() if vehicle_make else 'GEN'

        # Get OEM part number suffix
        oem_number = getattr(item_doc, 'oem_part_number', '')
        if oem_number:
            # Clean OEM number for use in item code
            oem_suffix = re.sub(r'[^A-Z0-9]', '', oem_number.upper())[:6]
        else:
            # Generate sequence number
            last_item = frappe.db.sql("""
                SELECT item_code FROM `tabItem`
                WHERE item_code LIKE %s
                ORDER BY creation DESC LIMIT 1
            """, f"{prefix}-{make_code}-%")

            if last_item:
                try:
                    last_seq = int(last_item[0][0].split('-')[-1])
                    oem_suffix = f"{last_seq + 1:06d}"
                except:
                    oem_suffix = "000001"
            else:
                oem_suffix = "000001"

        # Construct item code: PREFIX-MAKE-OEMSUFFIX
        item_code = f"{prefix}-{make_code}-{oem_suffix}"

        # Ensure uniqueness
        counter = 1
        original_code = item_code
        while frappe.db.exists("Item", item_code):
            item_code = f"{original_code}-{counter:02d}"
            counter += 1

        return item_code

    except Exception as e:
        frappe.log_error(f"Item code generation error: {str(e)}", "Parts Inventory")
        return None
