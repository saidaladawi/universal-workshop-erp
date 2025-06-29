import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, getdate, cstr, add_days
import qrcode
import io
import base64
import uuid
from frappe.utils.pdf import get_pdf
import os


class TrainingCertification(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields to Document class

    def validate(self):
        """Validate certification data before saving"""
        self.validate_user_and_module()
        self.validate_validity_dates()
        self.set_certificate_details()

    def before_save(self):
        """Set computed fields before saving"""
        self.set_user_details()
        self.set_module_details()
        self.generate_certificate_number()
        self.generate_verification_code()
        self.set_default_values()

    def after_save(self):
        """Generate certificate PDF and QR code after saving"""
        if self.is_new():
            self.generate_qr_code()
            self.generate_certificate_pdf()

    def validate_user_and_module(self):
        """Validate required user and module data"""
        if not self.user:
            frappe.throw(_("User is required"))

        if not self.training_module:
            frappe.throw(_("Training Module is required"))

        # Check for duplicate active certifications
        existing = frappe.db.exists(
            "Training Certification",
            {
                "user": self.user,
                "training_module": self.training_module,
                "status": "Active",
                "name": ["!=", self.name],
            },
        )
        if existing:
            frappe.throw(_("Active certification already exists for this user and module"))

    def validate_validity_dates(self):
        """Validate certification validity dates"""
        if self.issued_on and self.valid_until:
            if getdate(self.valid_until) <= getdate(self.issued_on):
                frappe.throw(_("Valid Until date must be after Issued On date"))

    def set_certificate_details(self):
        """Set certificate titles and details"""
        if self.training_module:
            module_doc = frappe.get_doc("Training Module", self.training_module)

            if not self.certificate_title:
                self.certificate_title = f"Certificate of Completion - {module_doc.title}"

            if not self.certificate_title_ar:
                self.certificate_title_ar = (
                    f"شهادة إتمام - {module_doc.title_ar or module_doc.title}"
                )

    def set_user_details(self):
        """Set user details from User DocType"""
        if self.user:
            user_doc = frappe.get_doc("User", self.user)
            self.full_name = user_doc.full_name or user_doc.first_name

            # Link to Employee if exists
            employee = frappe.db.get_value("Employee", {"user_id": self.user}, "name")
            if employee:
                self.employee_id = employee

    def set_module_details(self):
        """Set training module details"""
        if self.training_module:
            module_doc = frappe.get_doc("Training Module", self.training_module)
            self.module_title = module_doc.title

    def generate_certificate_number(self):
        """Generate unique certificate number"""
        if not self.certificate_number:
            # Format: CERT-YYYY-MM-XXXXX
            from datetime import datetime

            now = datetime.now()

            # Get count of certificates this month
            month_count = frappe.db.count(
                "Training Certification",
                {"certificate_number": ["like", f"CERT-{now.year}-{now.month:02d}-%"]},
            )

            self.certificate_number = f"CERT-{now.year}-{now.month:02d}-{month_count + 1:05d}"

    def generate_verification_code(self):
        """Generate unique verification code"""
        if not self.verification_code:
            self.verification_code = str(uuid.uuid4()).replace("-", "").upper()[:12]

    def set_default_values(self):
        """Set default values for computed fields"""
        if not self.created_by:
            self.created_by = frappe.session.user

        if not self.created_date:
            self.created_date = now_datetime()

        if not self.authorized_by:
            self.authorized_by = frappe.session.user

    def generate_qr_code(self):
        """Generate QR code for certificate verification"""
        try:
            # Create verification URL
            site_url = frappe.utils.get_site_url(frappe.local.site)
            verification_url = f"{site_url}/verify-certificate/{self.verification_code}"

            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(verification_url)
            qr.make(fit=True)

            # Create QR code image
            qr_image = qr.make_image(fill_color="black", back_color="white")

            # Convert to base64
            buffer = io.BytesIO()
            qr_image.save(buffer, format="PNG")
            qr_base64 = base64.b64encode(buffer.getvalue()).decode()

            # Save as attachment
            file_doc = frappe.get_doc(
                {
                    "doctype": "File",
                    "file_name": f"qr_code_{self.name}.png",
                    "content": qr_base64,
                    "decode": True,
                    "attached_to_doctype": "Training Certification",
                    "attached_to_name": self.name,
                    "folder": "Home/Certificates",
                }
            )
            file_doc.insert()

            self.qr_code = file_doc.file_url
            self.save()

        except Exception as e:
            frappe.log_error(f"Failed to generate QR code: {str(e)}")

    def generate_certificate_pdf(self):
        """Generate certificate PDF using print format"""
        try:
            # Use default certificate template or create one
            print_format = self.certificate_template or "Training Certificate"

            # Generate PDF
            pdf_content = get_pdf(
                html=self.get_certificate_html(),
                options={
                    "page-size": "A4",
                    "orientation": "landscape" if frappe.local.lang == "ar" else "portrait",
                    "margin-top": "0.5in",
                    "margin-right": "0.5in",
                    "margin-bottom": "0.5in",
                    "margin-left": "0.5in",
                },
            )

            # Save PDF as attachment
            file_doc = frappe.get_doc(
                {
                    "doctype": "File",
                    "file_name": f"certificate_{self.certificate_number}.pdf",
                    "content": pdf_content,
                    "attached_to_doctype": "Training Certification",
                    "attached_to_name": self.name,
                    "folder": "Home/Certificates",
                }
            )
            file_doc.insert()

            self.file_url = file_doc.file_url
            self.save()

        except Exception as e:
            frappe.log_error(f"Failed to generate certificate PDF: {str(e)}")

    def get_certificate_html(self):
        """Generate HTML content for certificate"""
        # Get site URL for QR code
        site_url = frappe.utils.get_site_url(frappe.local.site)
        verification_url = f"{site_url}/verify-certificate/{self.verification_code}"

        # Determine language direction
        is_arabic = frappe.local.lang == "ar"
        direction = "rtl" if is_arabic else "ltr"

        certificate_title = self.certificate_title_ar if is_arabic else self.certificate_title
        issuing_authority = self.issuing_authority_ar if is_arabic else self.issuing_authority

        html_content = f"""
        <!DOCTYPE html>
        <html dir="{direction}">
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: 'Arial', sans-serif;
                    direction: {direction};
                    text-align: center;
                    margin: 0;
                    padding: 40px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                }}
                .certificate {{
                    background: white;
                    padding: 60px;
                    border: 10px solid #2c3e50;
                    border-radius: 20px;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                    max-width: 800px;
                    margin: 0 auto;
                }}
                .certificate-header {{
                    color: #2c3e50;
                    font-size: 48px;
                    font-weight: bold;
                    margin-bottom: 20px;
                    text-transform: uppercase;
                    letter-spacing: 3px;
                }}
                .certificate-title {{
                    color: #34495e;
                    font-size: 32px;
                    margin-bottom: 40px;
                    font-weight: 300;
                }}
                .recipient-name {{
                    color: #e74c3c;
                    font-size: 42px;
                    font-weight: bold;
                    margin: 30px 0;
                    text-decoration: underline;
                }}
                .competency-level {{
                    color: #27ae60;
                    font-size: 28px;
                    font-weight: bold;
                    margin: 20px 0;
                }}
                .details {{
                    margin: 40px 0;
                    font-size: 18px;
                    line-height: 1.6;
                    color: #34495e;
                }}
                .signature-section {{
                    display: flex;
                    justify-content: space-between;
                    margin-top: 60px;
                    align-items: flex-end;
                }}
                .signature-block {{
                    text-align: center;
                    flex: 1;
                }}
                .signature-line {{
                    border-bottom: 2px solid #2c3e50;
                    margin-bottom: 10px;
                    height: 40px;
                }}
                .qr-section {{
                    position: absolute;
                    top: 20px;
                    right: 20px;
                    text-align: center;
                }}
                .certificate-number {{
                    position: absolute;
                    bottom: 20px;
                    left: 20px;
                    font-size: 14px;
                    color: #7f8c8d;
                }}
                .verification-code {{
                    position: absolute;
                    bottom: 20px;
                    right: 20px;
                    font-size: 12px;
                    color: #7f8c8d;
                }}
            </style>
        </head>
        <body>
            <div class="certificate">
                <div class="certificate-number">
                    {_("Certificate No")}: {self.certificate_number}
                </div>
                
                <div class="qr-section">
                    <img src="{self.qr_code}" width="80" height="80" alt="QR Code">
                    <div style="font-size: 10px; margin-top: 5px;">{_("Verify Online")}</div>
                </div>
                
                <div class="certificate-header">
                    {_("Certificate of Achievement")}
                </div>
                
                <div class="certificate-title">
                    {certificate_title}
                </div>
                
                <div style="font-size: 24px; margin: 40px 0;">
                    {_("This is to certify that")}
                </div>
                
                <div class="recipient-name">
                    {self.full_name}
                </div>
                
                <div style="font-size: 20px; margin: 30px 0;">
                    {_("has successfully completed the training module")}
                </div>
                
                <div style="font-size: 28px; color: #3498db; font-weight: bold; margin: 20px 0;">
                    {self.module_title}
                </div>
                
                <div class="competency-level">
                    {_("Competency Level")}: {_(self.competency_level)}
                </div>
                
                <div class="details">
                    {_("Final Score")}: {self.quiz_score}% | 
                    {_("Completed On")}: {frappe.format_date(self.completed_on)} | 
                    {_("Valid Until")}: {frappe.format_date(self.valid_until)}
                </div>
                
                <div class="signature-section">
                    <div class="signature-block">
                        <div class="signature-line"></div>
                        <div>{_("Authorized Signature")}</div>
                        <div style="font-size: 14px; margin-top: 5px;">{issuing_authority}</div>
                    </div>
                    <div style="width: 100px;"></div>
                    <div class="signature-block">
                        <div class="signature-line"></div>
                        <div>{_("Date of Issue")}</div>
                        <div style="font-size: 14px; margin-top: 5px;">{frappe.format_date(self.issued_on)}</div>
                    </div>
                </div>
                
                <div class="verification-code">
                    {_("Verification Code")}: {self.verification_code}
                </div>
            </div>
        </body>
        </html>
        """

        return html_content

    @frappe.whitelist()
    def download_certificate(self):
        """Download certificate and increment download count"""
        if self.file_url:
            self.download_count += 1
            self.save()
            return {"file_url": self.file_url, "download_count": self.download_count}
        else:
            frappe.throw(_("Certificate file not available"))

    @frappe.whitelist()
    def regenerate_certificate(self):
        """Regenerate certificate PDF and QR code"""
        self.generate_qr_code()
        self.generate_certificate_pdf()
        return {"status": "success", "message": _("Certificate regenerated successfully")}

    def on_trash(self):
        """Clean up when certification is deleted"""
        # Remove associated files
        if self.file_url:
            file_doc = frappe.get_doc("File", {"file_url": self.file_url})
            if file_doc:
                file_doc.delete()

        if self.qr_code:
            file_doc = frappe.get_doc("File", {"file_url": self.qr_code})
            if file_doc:
                file_doc.delete()


# API Methods for certificate verification and management
@frappe.whitelist(allow_guest=True)
def verify_certificate(verification_code):
    """Verify certificate using verification code"""
    try:
        certificate = frappe.get_doc(
            "Training Certification", {"verification_code": verification_code}
        )

        if certificate:
            return {
                "valid": True,
                "certificate_number": certificate.certificate_number,
                "user_name": certificate.full_name,
                "module_title": certificate.module_title,
                "competency_level": certificate.competency_level,
                "issued_on": certificate.issued_on,
                "valid_until": certificate.valid_until,
                "status": certificate.status,
                "issuing_authority": certificate.issuing_authority,
            }
        else:
            return {"valid": False, "message": _("Certificate not found")}

    except Exception:
        return {"valid": False, "message": _("Invalid verification code")}


@frappe.whitelist()
def get_user_certifications(user):
    """Get all certifications for a user"""
    certifications = frappe.get_list(
        "Training Certification",
        filters={"user": user},
        fields=[
            "name",
            "certificate_number",
            "certificate_title",
            "competency_level",
            "issued_on",
            "valid_until",
            "status",
            "file_url",
            "download_count",
        ],
        order_by="issued_on desc",
    )

    return certifications


@frappe.whitelist()
def check_expiring_certifications(days_ahead=30):
    """Check for certifications expiring within specified days"""
    from frappe.utils import add_days, today

    expiry_date = add_days(today(), days_ahead)

    expiring = frappe.get_list(
        "Training Certification",
        filters={
            "status": "Active",
            "valid_until": ["<=", expiry_date],
            "valid_until": [">=", today()],
        },
        fields=["name", "user", "full_name", "certificate_title", "valid_until"],
    )

    return expiring


@frappe.whitelist()
def bulk_renewal_notification():
    """Send renewal notifications for expiring certificates"""
    expiring_certs = check_expiring_certifications(30)

    notification_count = 0
    for cert in expiring_certs:
        try:
            frappe.sendmail(
                recipients=[cert.user],
                subject=_("Certificate Renewal Required"),
                message=_(
                    "Your certification '{0}' will expire on {1}. Please renew before expiry."
                ).format(cert.certificate_title, cert.valid_until),
            )
            notification_count += 1
        except Exception as e:
            frappe.log_error(f"Failed to send renewal notification: {str(e)}")

    return {"notifications_sent": notification_count}
