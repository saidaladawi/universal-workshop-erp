# Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import os
import io
import base64
from typing import Dict, List, Optional, Tuple, Any
from PIL import Image, ImageOps
import frappe
from frappe import _
from frappe.utils.file_manager import save_file, get_file_path, delete_file

# Handle EXIF import safely
try:
    from PIL.ExifTags import ORIENTATION
except ImportError:
    # Fallback for older PIL versions
    ORIENTATION = 274


class ImageOptimizer:
    """
    Comprehensive image optimization system for workshop logos.
    Handles multiple size variants, compression, and format optimization.
    """

    # Predefined size variants for different use cases
    SIZE_VARIANTS = {
        "thumbnail": (64, 64),  # Small icons, list views
        "small": (128, 128),  # Form headers, sidebar
        "medium": (256, 256),  # Main logo display
        "large": (512, 512),  # High-res display, print headers
        "print": (1024, 1024),  # High-quality print documents
        "favicon": (32, 32),  # Browser favicon
    }

    # Quality settings for different use cases
    QUALITY_SETTINGS = {
        "web": 85,  # Good balance for web display
        "print": 95,  # High quality for print
        "thumbnail": 75,  # Lower quality for small sizes
    }

    # Supported formats
    SUPPORTED_FORMATS = ["PNG", "JPEG", "JPG", "WEBP"]
    VECTOR_FORMATS = ["SVG"]

    def __init__(self, workshop_profile_name: str):
        """Initialize optimizer for specific workshop profile"""
        self.workshop_profile_name = workshop_profile_name
        self.base_path = f"workshop_logos/{workshop_profile_name}"

    def optimize_logo(self, file_url: str, generate_variants: bool = True) -> Dict[str, Any]:
        """
        Optimize uploaded logo and generate multiple size variants.

        Args:
            file_url (str): URL of the uploaded logo file
            generate_variants (bool): Whether to generate size variants

        Returns:
            Dict containing optimization results and variant URLs
        """
        try:
            # Get original file path
            file_path = get_file_path(file_url)
            if not file_path or not os.path.exists(file_path):
                raise Exception(_("Logo file not found"))

            # Check if it's a vector format (SVG)
            if file_path.lower().endswith(".svg"):
                return self._handle_svg_logo(file_url, file_path)

            # Open and process raster image
            with Image.open(file_path) as img:
                # Apply EXIF rotation if present
                img = self._apply_exif_rotation(img)

                # Convert to RGB if necessary (for JPEG output)
                if img.mode in ("RGBA", "LA", "P"):
                    # Create white background for transparency
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                    img_rgb = background
                else:
                    img_rgb = img.convert("RGB")

                # Generate optimized variants
                results = {
                    "original_size": img.size,
                    "file_size_before": os.path.getsize(file_path),
                    "variants": {},
                    "optimized_original": None,
                }

                # Optimize original image
                optimized_original = self._optimize_image(
                    img_rgb, "original", target_size=None, quality=self.QUALITY_SETTINGS["web"]
                )
                results["optimized_original"] = optimized_original

                if generate_variants:
                    # Generate size variants
                    for variant_name, target_size in self.SIZE_VARIANTS.items():
                        try:
                            variant_result = self._optimize_image(
                                img_rgb,
                                variant_name,
                                target_size=target_size,
                                quality=self._get_variant_quality(variant_name),
                            )
                            results["variants"][variant_name] = variant_result
                        except Exception as e:
                            frappe.log_error(f"Error creating {variant_name} variant: {str(e)}")

                # Calculate total optimization savings
                total_size_after = sum(
                    [v.get("file_size", 0) for v in results["variants"].values()]
                ) + results["optimized_original"].get("file_size", 0)

                results["total_size_after"] = total_size_after
                results["compression_ratio"] = (
                    (
                        (results["file_size_before"] - total_size_after)
                        / results["file_size_before"]
                        * 100
                    )
                    if results["file_size_before"] > 0
                    else 0
                )

                return results

        except Exception as e:
            frappe.log_error(f"Image optimization error: {str(e)}")
            raise Exception(_("Failed to optimize image: {0}").format(str(e)))

    def _handle_svg_logo(self, file_url: str, file_path: str) -> Dict[str, Any]:
        """Handle SVG logos (vector format)"""
        try:
            # For SVG, we can't generate raster variants easily
            # Instead, we'll create optimized copies and note that it's vector
            file_size = os.path.getsize(file_path)

            # Create a copy for each variant (same file, different naming)
            variants = {}
            for variant_name in self.SIZE_VARIANTS.keys():
                # Copy SVG file with variant naming
                variant_filename = f"{self.workshop_profile_name}_logo_{variant_name}.svg"

                with open(file_path, "rb") as f:
                    svg_content = f.read()

                # Save variant (same content, different name for organization)
                variant_file = save_file(
                    variant_filename,
                    svg_content,
                    "Workshop Profile",
                    self.workshop_profile_name,
                    folder=self.base_path,
                    is_private=0,
                )

                variants[variant_name] = {
                    "file_url": variant_file.file_url,
                    "file_size": file_size,
                    "dimensions": "vector",
                    "format": "SVG",
                }

            return {
                "original_size": "vector",
                "file_size_before": file_size,
                "variants": variants,
                "optimized_original": {
                    "file_url": file_url,
                    "file_size": file_size,
                    "format": "SVG",
                },
                "is_vector": True,
                "compression_ratio": 0,  # No compression for SVG
            }

        except Exception as e:
            frappe.log_error(f"SVG handling error: {str(e)}")
            raise Exception(_("Failed to process SVG logo: {0}").format(str(e)))

    def _apply_exif_rotation(self, img: Image.Image) -> Image.Image:
        """Apply EXIF rotation to correct image orientation"""
        try:
            exif = img._getexif()
            if exif is not None:
                orientation = exif.get(ORIENTATION)
                if orientation:
                    if orientation == 3:
                        img = img.rotate(180, expand=True)
                    elif orientation == 6:
                        img = img.rotate(270, expand=True)
                    elif orientation == 8:
                        img = img.rotate(90, expand=True)
            return img
        except:
            # If EXIF processing fails, return original image
            return img

    def _optimize_image(
        self,
        img: Image.Image,
        variant_name: str,
        target_size: Optional[Tuple[int, int]] = None,
        quality: int = 85,
    ) -> Dict[str, Any]:
        """
        Optimize image for specific variant.

        Args:
            img: PIL Image object
            variant_name: Name of the variant (e.g., 'thumbnail', 'large')
            target_size: Target dimensions (width, height)
            quality: JPEG quality (1-100)

        Returns:
            Dict with optimization results
        """
        try:
            # Create working copy
            working_img = img.copy()

            # Resize if target size specified
            if target_size:
                # Use high-quality resampling
                working_img = ImageOps.fit(
                    working_img, target_size, Image.Resampling.LANCZOS, centering=(0.5, 0.5)
                )

            # Determine output format
            output_format = "JPEG"  # Default to JPEG for better compression
            file_extension = ".jpg"

            # Use PNG for small sizes to preserve quality
            if target_size and max(target_size) <= 128:
                output_format = "PNG"
                file_extension = ".png"

            # Create filename
            filename = f"{self.workshop_profile_name}_logo_{variant_name}{file_extension}"

            # Optimize and save
            output_buffer = io.BytesIO()

            if output_format == "JPEG":
                working_img.save(
                    output_buffer, format="JPEG", quality=quality, optimize=True, progressive=True
                )
            else:  # PNG
                working_img.save(output_buffer, format="PNG", optimize=True)

            # Get optimized data
            optimized_data = output_buffer.getvalue()
            output_buffer.close()

            # Save optimized file
            saved_file = save_file(
                filename,
                optimized_data,
                "Workshop Profile",
                self.workshop_profile_name,
                folder=self.base_path,
                is_private=0,
            )

            return {
                "file_url": saved_file.file_url,
                "file_size": len(optimized_data),
                "dimensions": working_img.size,
                "format": output_format,
                "quality": quality,
                "filename": filename,
            }

        except Exception as e:
            frappe.log_error(f"Image optimization error for {variant_name}: {str(e)}")
            raise Exception(_("Failed to optimize {0} variant: {1}").format(variant_name, str(e)))

    def _get_variant_quality(self, variant_name: str) -> int:
        """Get appropriate quality setting for variant"""
        if variant_name in ["thumbnail", "favicon", "small"]:
            return self.QUALITY_SETTINGS["thumbnail"]
        elif variant_name in ["print", "large"]:
            return self.QUALITY_SETTINGS["print"]
        else:
            return self.QUALITY_SETTINGS["web"]

    def get_optimized_logo_url(self, variant: str = "medium") -> Optional[str]:
        """Get URL for specific logo variant"""
        try:
            # Look for existing optimized variant
            files = frappe.get_list(
                "File",
                filters={
                    "attached_to_doctype": "Workshop Profile",
                    "attached_to_name": self.workshop_profile_name,
                    "file_name": ["like", f"%_logo_{variant}.%"],
                },
                fields=["file_url"],
                order_by="creation desc",
                limit=1,
            )

            return files[0].file_url if files else None

        except Exception as e:
            frappe.log_error(f"Error getting optimized logo URL: {str(e)}")
            return None

    def cleanup_old_variants(self) -> int:
        """Clean up old logo variants and return count of deleted files"""
        try:
            # Get all logo files for this workshop
            old_files = frappe.get_list(
                "File",
                filters={
                    "attached_to_doctype": "Workshop Profile",
                    "attached_to_name": self.workshop_profile_name,
                    "file_name": ["like", f"%{self.workshop_profile_name}_logo_%"],
                },
                fields=["name", "file_url"],
            )

            deleted_count = 0
            for file_doc in old_files:
                try:
                    delete_file(file_doc.file_url)
                    deleted_count += 1
                except Exception as e:
                    frappe.log_error(f"Error deleting file {file_doc.file_url}: {str(e)}")

            return deleted_count

        except Exception as e:
            frappe.log_error(f"Error cleaning up logo variants: {str(e)}")
            return 0

    @staticmethod
    def get_image_info(file_url: str) -> Dict[str, Any]:
        """Get detailed information about an image file"""
        try:
            file_path = get_file_path(file_url)
            if not file_path or not os.path.exists(file_path):
                return {"error": "File not found"}

            file_size = os.path.getsize(file_path)

            # Handle SVG files
            if file_path.lower().endswith(".svg"):
                return {
                    "format": "SVG",
                    "mode": "vector",
                    "size": "vector",
                    "file_size": file_size,
                    "is_vector": True,
                }

            # Handle raster images
            with Image.open(file_path) as img:
                return {
                    "format": img.format,
                    "mode": img.mode,
                    "size": img.size,
                    "file_size": file_size,
                    "has_transparency": img.mode in ("RGBA", "LA") or "transparency" in img.info,
                    "is_vector": False,
                }

        except Exception as e:
            return {"error": str(e)}


# WhiteListed API Methods


@frappe.whitelist()
def optimize_workshop_logo(
    workshop_profile_name: str, file_url: str, generate_variants: bool = True
) -> Dict[str, Any]:
    """
    API method to optimize workshop logo and generate variants.

    Args:
        workshop_profile_name: Name of the Workshop Profile
        file_url: URL of the uploaded logo file
        generate_variants: Whether to generate size variants

    Returns:
        Dict with optimization results
    """
    try:
        optimizer = ImageOptimizer(workshop_profile_name)
        results = optimizer.optimize_logo(file_url, generate_variants)

        # Update Workshop Profile with optimized logo variants
        workshop_profile = frappe.get_doc("Workshop Profile", workshop_profile_name)

        # Store variant URLs in custom fields (if they exist)
        if "variants" in results:
            for variant_name, variant_data in results["variants"].items():
                field_name = f"logo_{variant_name}"
                if hasattr(workshop_profile, field_name):
                    setattr(workshop_profile, field_name, variant_data["file_url"])

        # Store optimization metadata
        workshop_profile.logo_optimization_data = frappe.as_json(results)
        workshop_profile.save()

        frappe.msgprint(
            _(
                "Logo optimized successfully! Generated {0} variants with {1:.1f}% size reduction."
            ).format(len(results.get("variants", {})), results.get("compression_ratio", 0)),
            title=_("Logo Optimization Complete"),
            indicator="green",
        )

        return results

    except Exception as e:
        frappe.log_error(f"Logo optimization API error: {str(e)}")
        frappe.throw(_("Failed to optimize logo: {0}").format(str(e)))


@frappe.whitelist()
def get_logo_variant_url(workshop_profile_name: str, variant: str = "medium") -> Optional[str]:
    """Get URL for specific logo variant"""
    try:
        optimizer = ImageOptimizer(workshop_profile_name)
        return optimizer.get_optimized_logo_url(variant)
    except Exception as e:
        frappe.log_error(f"Error getting logo variant: {str(e)}")
        return None


@frappe.whitelist()
def cleanup_logo_variants(workshop_profile_name: str) -> Dict[str, Any]:
    """Clean up old logo variants"""
    try:
        optimizer = ImageOptimizer(workshop_profile_name)
        deleted_count = optimizer.cleanup_old_variants()

        return {
            "success": True,
            "deleted_count": deleted_count,
            "message": _("Cleaned up {0} old logo files").format(deleted_count),
        }
    except Exception as e:
        frappe.log_error(f"Cleanup error: {str(e)}")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_image_analysis(file_url: str) -> Dict[str, Any]:
    """Get detailed analysis of an image file"""
    return ImageOptimizer.get_image_info(file_url)
