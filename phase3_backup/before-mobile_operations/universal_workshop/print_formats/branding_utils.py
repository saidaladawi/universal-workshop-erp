"""
Print Format Branding Utilities
Handles integration of workshop branding elements into print formats
"""

import frappe
from frappe import _
from frappe.utils import get_url, flt
import base64
import os
from PIL import Image
import io


class PrintBrandingManager:
    """Manages branding elements for print formats"""

    def __init__(self, workshop_profile=None):
        """Initialize with workshop profile"""
        self.workshop_profile = workshop_profile or self.get_default_workshop()
        self.branding_data = self.get_branding_data()

    def get_default_workshop(self):
        """Get the default workshop profile"""
        try:
            workshop = frappe.get_list(
                "Workshop Profile", filters={"is_default": 1}, fields=["name"], limit=1
            )
            if workshop:
                return frappe.get_doc("Workshop Profile", workshop[0].name)

            # Fallback to first workshop
            workshop = frappe.get_list("Workshop Profile", fields=["name"], limit=1)
            if workshop:
                return frappe.get_doc("Workshop Profile", workshop[0].name)

        except Exception as e:
            frappe.log_error(f"Error getting default workshop: {e}")

        return None

    def get_branding_data(self):
        """Get comprehensive branding data for print formats"""
        if not self.workshop_profile:
            return self.get_default_branding()

        return {
            "workshop_name": self.workshop_profile.workshop_name or "",
            "workshop_name_ar": self.workshop_profile.workshop_name_ar or "",
            "logo_url": self.get_logo_for_print(),
            "logo_base64": self.get_logo_base64(),
            "primary_color": self.workshop_profile.primary_color or "#1f4e79",
            "secondary_color": self.workshop_profile.secondary_color or "#2980b9",
            "theme_data": self.get_theme_data(),
            "contact_info": self.get_contact_info(),
            "address_info": self.get_address_info(),
            "business_info": self.get_business_info(),
            "social_media": self.get_social_media_info(),
        }

    def get_default_branding(self):
        """Get default branding when no workshop profile exists"""
        return {
            "workshop_name": _("Universal Workshop"),
            "workshop_name_ar": "الورشة العالمية",
            "logo_url": "",
            "logo_base64": "",
            "primary_color": "#1f4e79",
            "secondary_color": "#2980b9",
            "theme_data": {},
            "contact_info": {},
            "address_info": {},
            "business_info": {},
            "social_media": {},
        }

    def get_logo_for_print(self, variant="print"):
        """Get optimized logo URL for print formats"""
        if not self.workshop_profile:
            return ""

        try:
            # Try to get optimized variant first
            variant_field = f"logo_{variant}"
            if hasattr(self.workshop_profile, variant_field):
                variant_url = getattr(self.workshop_profile, variant_field)
                if variant_url:
                    return get_url(variant_url)

            # Fallback to original logo
            if self.workshop_profile.workshop_logo:
                return get_url(self.workshop_profile.workshop_logo)

        except Exception as e:
            frappe.log_error(f"Error getting logo URL: {e}")

        return ""

    def get_logo_base64(self, variant="print"):
        """Get optimized logo as base64 for embedded print formats"""
        if not self.workshop_profile:
            return ""

        try:
            # Get the appropriate logo URL
            logo_url = self.get_logo_for_print(variant)
            if not logo_url:
                return ""

            # Extract file path from URL
            file_path = frappe.get_site_path(
                "public", "files", logo_url.lstrip("/files/").split("/files/")[-1]
            )

            if os.path.exists(file_path):
                with open(file_path, "rb") as img_file:
                    image_data = img_file.read()

                    # If we're using an already optimized variant, minimal processing
                    if variant in ["print", "large"]:
                        # Just convert to base64 for high-quality variants
                        return base64.b64encode(image_data).decode("utf-8")
                    else:
                        # Optimize for smaller variants
                        optimized_image = self.optimize_image_for_print(image_data)
                        return base64.b64encode(optimized_image).decode("utf-8")

        except Exception as e:
            frappe.log_error(f"Error converting logo to base64: {e}")

        return ""

    def get_logo_variants_info(self):
        """Get information about available logo variants"""
        if not self.workshop_profile:
            return {}

        variants = {}
        variant_types = ["thumbnail", "small", "medium", "large", "print", "favicon"]

        for variant in variant_types:
            field_name = f"logo_{variant}"
            if hasattr(self.workshop_profile, field_name):
                variant_url = getattr(self.workshop_profile, field_name)
                if variant_url:
                    variants[variant] = {
                        "url": variant_url,
                        "base64": self.get_logo_base64(variant),
                    }

        return variants

    def optimize_image_for_print(self, image_data, max_width=300, max_height=150):
        """Optimize image for print format usage"""
        try:
            image = Image.open(io.BytesIO(image_data))

            # Convert to RGB if necessary
            if image.mode in ("RGBA", "LA", "P"):
                background = Image.new("RGB", image.size, (255, 255, 255))
                if image.mode == "P":
                    image = image.convert("RGBA")
                background.paste(image, mask=image.split()[-1] if image.mode == "RGBA" else None)
                image = background

            # Resize while maintaining aspect ratio
            image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

            # Save optimized image
            output = io.BytesIO()
            image.save(output, format="JPEG", quality=85, optimize=True)
            return output.getvalue()

        except Exception as e:
            frappe.log_error(f"Error optimizing image: {e}")
            return image_data

    def get_theme_data(self):
        """Get current theme data for print styling"""
        if not self.workshop_profile:
            return {}

        try:
            theme_name = self.workshop_profile.theme_preference
            if theme_name:
                theme_doc = frappe.get_doc("Workshop Theme", theme_name)
                return frappe.parse_json(theme_doc.theme_data or "{}")
        except Exception as e:
            frappe.log_error(f"Error getting theme data: {e}")

        return {}

    def get_contact_info(self):
        """Get contact information for print headers/footers"""
        if not self.workshop_profile:
            return {}

        return {
            "phone": self.workshop_profile.phone or "",
            "email": self.workshop_profile.email or "",
            "website": self.workshop_profile.website or "",
            "whatsapp": self.workshop_profile.whatsapp_number or "",
        }

    def get_address_info(self):
        """Get address information for print formats"""
        if not self.workshop_profile:
            return {}

        return {
            "address_line_1": self.workshop_profile.address_line_1 or "",
            "address_line_1_ar": self.workshop_profile.address_line_1_ar or "",
            "address_line_2": self.workshop_profile.address_line_2 or "",
            "address_line_2_ar": self.workshop_profile.address_line_2_ar or "",
            "city": self.workshop_profile.city or "",
            "city_ar": self.workshop_profile.city_ar or "",
            "state": self.workshop_profile.state or "",
            "country": self.workshop_profile.country or "Oman",
            "postal_code": self.workshop_profile.postal_code or "",
        }

    def get_business_info(self):
        """Get business information for compliance printing"""
        if not self.workshop_profile:
            return {}

        return {
            "business_license": self.workshop_profile.business_license or "",
            "vat_number": self.workshop_profile.vat_number or "",
            "commercial_registration": self.workshop_profile.commercial_registration or "",
            "establishment_year": self.workshop_profile.establishment_year or "",
        }

    def get_social_media_info(self):
        """Get social media information for print formats"""
        if not self.workshop_profile:
            return {}

        return {
            "facebook": self.workshop_profile.facebook_url or "",
            "instagram": self.workshop_profile.instagram_url or "",
            "twitter": self.workshop_profile.twitter_url or "",
            "linkedin": self.workshop_profile.linkedin_url or "",
        }

    def generate_print_css(self, language="en"):
        """Generate dynamic CSS for print formats based on branding"""
        css_template = """
        <style>
        /* Workshop Branding CSS for Print Formats */
        .print-format {{
            font-family: {font_family};
            direction: {text_direction};
            color: #333;
        }}
        
        .workshop-header {{
            border-bottom: 2px solid {primary_color};
            margin-bottom: 20px;
            padding-bottom: 10px;
            text-align: {header_align};
        }}
        
        .workshop-logo {{
            max-height: 80px;
            max-width: 200px;
            margin-bottom: 10px;
        }}
        
        .workshop-name {{
            color: {primary_color};
            font-size: 24px;
            font-weight: bold;
            margin: 0;
        }}
        
        .workshop-tagline {{
            color: {secondary_color};
            font-size: 14px;
            margin: 5px 0;
        }}
        
        .contact-info {{
            font-size: 12px;
            color: #666;
            margin-top: 10px;
        }}
        
        .document-title {{
            color: {primary_color};
            font-size: 20px;
            font-weight: bold;
            text-align: center;
            margin: 20px 0;
            border-bottom: 1px solid {secondary_color};
            padding-bottom: 10px;
        }}
        
        .table-header {{
            background-color: {primary_color};
            color: white;
            font-weight: bold;
        }}
        
        .table-row:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        
        .total-section {{
            border-top: 2px solid {primary_color};
            margin-top: 20px;
            padding-top: 10px;
        }}
        
        .workshop-footer {{
            border-top: 1px solid {secondary_color};
            margin-top: 30px;
            padding-top: 15px;
            font-size: 11px;
            color: #666;
            text-align: center;
        }}
        
        .business-info {{
            font-size: 10px;
            color: #888;
            margin-top: 10px;
        }}
        
        /* Arabic-specific styles */
        .arabic-text {{
            font-family: 'Noto Sans Arabic', 'Tahoma', 'Arial Unicode MS', sans-serif;
            direction: rtl;
            text-align: right;
        }}
        
        /* Print-specific optimizations */
        @media print {{
            .workshop-header {{
                break-inside: avoid;
            }}
            
            .document-title {{
                break-after: avoid;
            }}
            
            .total-section {{
                break-inside: avoid;
            }}
        }}
        </style>
        """

        # Determine text direction and alignment based on language
        if language == "ar":
            text_direction = "rtl"
            header_align = "right"
            font_family = "'Noto Sans Arabic', 'Tahoma', 'Arial Unicode MS', sans-serif"
        else:
            text_direction = "ltr"
            header_align = "left"
            font_family = "'Helvetica Neue', Helvetica, Arial, sans-serif"

        return css_template.format(
            primary_color=self.branding_data["primary_color"],
            secondary_color=self.branding_data["secondary_color"],
            text_direction=text_direction,
            header_align=header_align,
            font_family=font_family,
        )

    def generate_header_html(self, language="en", include_logo=True):
        """Generate HTML header for print formats"""
        branding = self.branding_data

        # Determine workshop name based on language
        workshop_name = (
            branding["workshop_name_ar"] if language == "ar" else branding["workshop_name"]
        )
        if not workshop_name:
            workshop_name = branding["workshop_name"] or branding["workshop_name_ar"]

        # Logo HTML
        logo_html = ""
        if include_logo and branding["logo_base64"]:
            logo_html = f"""
            <img src="data:image/jpeg;base64,{branding['logo_base64']}" 
                 class="workshop-logo" alt="{workshop_name}">
            """
        elif include_logo and branding["logo_url"]:
            logo_html = f"""
            <img src="{branding['logo_url']}" 
                 class="workshop-logo" alt="{workshop_name}">
            """

        # Contact info
        contact_info = branding["contact_info"]
        contact_html = ""
        if any(contact_info.values()):
            contact_parts = []
            if contact_info.get("phone"):
                contact_parts.append(f"📞 {contact_info['phone']}")
            if contact_info.get("email"):
                contact_parts.append(f"✉️ {contact_info['email']}")
            if contact_info.get("website"):
                contact_parts.append(f"🌐 {contact_info['website']}")

            if contact_parts:
                separator = " | " if language != "ar" else " | "
                contact_html = f"""
                <div class="contact-info">
                    {separator.join(contact_parts)}
                </div>
                """

        # Address info
        address_info = branding["address_info"]
        address_html = ""
        if any(address_info.values()):
            if language == "ar":
                address_line_1 = address_info.get("address_line_1_ar") or address_info.get(
                    "address_line_1", ""
                )
                address_line_2 = address_info.get("address_line_2_ar") or address_info.get(
                    "address_line_2", ""
                )
                city = address_info.get("city_ar") or address_info.get("city", "")
            else:
                address_line_1 = address_info.get("address_line_1", "")
                address_line_2 = address_info.get("address_line_2", "")
                city = address_info.get("city", "")

            address_parts = [part for part in [address_line_1, address_line_2, city] if part]
            if address_parts:
                address_text = ", ".join(address_parts)
                address_html = f"""
                <div class="address-info" style="font-size: 12px; color: #666;">
                    📍 {address_text}
                </div>
                """

        header_html = f"""
        <div class="workshop-header">
            {logo_html}
            <h1 class="workshop-name">{workshop_name}</h1>
            {contact_html}
            {address_html}
        </div>
        """

        return header_html

    def generate_footer_html(self, language="en"):
        """Generate HTML footer for print formats"""
        branding = self.branding_data
        business_info = branding["business_info"]

        # Business compliance information
        business_parts = []
        if business_info.get("business_license"):
            business_parts.append(f"{_('Business License')}: {business_info['business_license']}")
        if business_info.get("vat_number"):
            business_parts.append(f"{_('VAT Number')}: {business_info['vat_number']}")
        if business_info.get("commercial_registration"):
            business_parts.append(f"{_('CR Number')}: {business_info['commercial_registration']}")

        business_html = ""
        if business_parts:
            separator = " | " if language != "ar" else " | "
            business_html = f"""
            <div class="business-info">
                {separator.join(business_parts)}
            </div>
            """

        footer_html = f"""
        <div class="workshop-footer">
            <p>{_('Thank you for choosing our services')}</p>
            {business_html}
        </div>
        """

        return footer_html


def get_print_branding_context(workshop_profile=None, language=None):
    """Get branding context for print format templates"""
    if not language:
        language = frappe.local.lang or "en"

    manager = PrintBrandingManager(workshop_profile)

    return {
        "branding": manager.branding_data,
        "print_css": manager.generate_print_css(language),
        "header_html": manager.generate_header_html(language),
        "footer_html": manager.generate_footer_html(language),
        "language": language,
        "is_arabic": language == "ar",
    }


@frappe.whitelist()
def get_workshop_branding_for_print(workshop_name=None, language=None):
    """API method to get branding data for print formats"""
    try:
        workshop_profile = None
        if workshop_name:
            workshop_profile = frappe.get_doc("Workshop Profile", workshop_name)

        return get_print_branding_context(workshop_profile, language)

    except Exception as e:
        frappe.log_error(f"Error getting workshop branding for print: {e}")
        return get_print_branding_context(None, language)


@frappe.whitelist()
def preview_print_format_with_branding(doctype, docname, print_format, language=None):
    """Preview print format with workshop branding applied"""
    try:
        # Get the document
        doc = frappe.get_doc(doctype, docname)

        # Get branding context
        branding_context = get_print_branding_context(language=language)

        # Get print format HTML
        from frappe.www.printview import get_print_format

        print_html = get_print_format(doctype, docname, print_format)

        # Inject branding
        branded_html = f"""
        {branding_context['print_css']}
        {branding_context['header_html']}
        {print_html}
        {branding_context['footer_html']}
        """

        return branded_html

    except Exception as e:
        frappe.log_error(f"Error previewing print format with branding: {e}")
        return str(e)
