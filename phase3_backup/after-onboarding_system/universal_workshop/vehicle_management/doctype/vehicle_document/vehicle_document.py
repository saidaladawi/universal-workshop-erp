import datetime
import mimetypes
import os

import frappe
from frappe import _
from frappe.model.document import Document


class VehicleDocument(Document):
	def autoname(self):
		"""Generate document code: VD-YYYY-NNNN"""
		year = datetime.datetime.now().year

		# Get last document number for current year
		last_doc = frappe.db.sql(
			"""
            SELECT document_code FROM `tabVehicle Document`
            WHERE document_code LIKE 'VD-{}-%%'
            ORDER BY creation DESC LIMIT 1
        """.format(year)
		)

		if last_doc:
			last_num = int(last_doc[0][0].split("-")[-1])
			new_num = last_num + 1
		else:
			new_num = 1

		self.document_code = f"VD-{year}-{new_num:04d}"

	def validate(self):
		"""Validate vehicle document data"""
		self.validate_file_attachment()
		self.set_customer_from_vehicle()
		self.set_arabic_translations()
		self.validate_expiry_date()
		self.set_file_metadata()
		self.handle_version_control()

	def validate_file_attachment(self):
		"""Validate file attachment requirements"""
		if not self.file_attachment:
			frappe.throw(_("File attachment is required"))

		# Get file info
		try:
			file_doc = frappe.get_doc("File", {"file_url": self.file_attachment})
			file_size_bytes = file_doc.file_size or 0
			file_size_mb = file_size_bytes / (1024 * 1024)

			# Validate file size (50MB max)
			if file_size_mb > 50:
				frappe.throw(_("File size cannot exceed 50MB. Current size: {0:.2f}MB").format(file_size_mb))

			# Validate file format
			allowed_formats = [
				# Images
				".jpg",
				".jpeg",
				".png",
				".gif",
				".bmp",
				".tiff",
				".webp",
				# Documents
				".pdf",
				".doc",
				".docx",
				".txt",
				".rtf",
				# Videos
				".mp4",
				".avi",
				".mov",
				".mkv",
				".wmv",
				".flv",
				".webm",
				# Other common formats
				".xls",
				".xlsx",
				".ppt",
				".pptx",
				".zip",
				".rar",
			]

			file_extension = os.path.splitext(file_doc.file_name or "")[1].lower()
			if file_extension not in allowed_formats:
				frappe.throw(_("File format {0} is not supported").format(file_extension))

		except Exception as e:
			frappe.log_error(f"Error validating file: {e!s}")

	def set_customer_from_vehicle(self):
		"""Set customer from vehicle link"""
		if self.vehicle and not self.customer:
			vehicle_doc = frappe.get_doc("Vehicle", self.vehicle)
			self.customer = vehicle_doc.owner

	def set_arabic_translations(self):
		"""Set Arabic translations for document types"""
		document_translations = {
			"Registration Certificate": "شهادة تسجيل",
			"Insurance Policy": "وثيقة التأمين",
			"Driver License": "رخصة قيادة",
			"Service Manual": "دليل الخدمة",
			"Warranty Certificate": "شهادة الضمان",
			"Inspection Report": "تقرير الفحص",
			"Accident Report": "تقرير حادث",
			"Repair Invoice": "فاتورة إصلاح",
			"Parts Invoice": "فاتورة قطع غيار",
			"Ownership Transfer": "نقل ملكية",
			"Customs Declaration": "إقرار جمركي",
			"Import Permit": "تصريح استيراد",
			"Technical Inspection": "فحص فني",
			"Emission Test": "اختبار انبعاثات",
			"Other": "أخرى",
		}

		if not self.title_ar and self.document_type and self.document_type in document_translations:
			vehicle_info = ""
			if self.vehicle:
				vehicle_doc = frappe.get_doc("Vehicle", self.vehicle)
				vehicle_info = f" - {vehicle_doc.make} {vehicle_doc.model}"

			self.title_ar = document_translations[self.document_type] + vehicle_info

	def validate_expiry_date(self):
		"""Validate expiry date for applicable documents"""
		if self.expiry_date and self.expiry_date <= datetime.date.today():
			self.status = "Expired"
		elif self.status == "Expired" and self.expiry_date and self.expiry_date > datetime.date.today():
			self.status = "Active"

	def set_file_metadata(self):
		"""Set file metadata from attachment"""
		if self.file_attachment:
			try:
				file_doc = frappe.get_doc("File", {"file_url": self.file_attachment})

				# Set file size in MB
				if file_doc.file_size:
					self.file_size_mb = round(file_doc.file_size / (1024 * 1024), 2)

				# Set file format
				if file_doc.file_name:
					self.file_format = os.path.splitext(file_doc.file_name)[1].upper().replace(".", "")

			except Exception as e:
				frappe.log_error(f"Error setting file metadata: {e!s}")

	def handle_version_control(self):
		"""Handle document versioning"""
		if not self.version:
			self.version = "1.0"

		# Check for existing documents with same vehicle and type
		existing_docs = frappe.get_all(
			"Vehicle Document",
			filters={
				"vehicle": self.vehicle,
				"document_type": self.document_type,
				"name": ["!=", self.name or ""],
				"status": ["!=", "Deleted"],
			},
			fields=["name", "version", "is_latest_version"],
			order_by="creation desc",
		)

		if existing_docs:
			# This is a new version
			if not self.previous_version:
				latest_doc = existing_docs[0]
				self.previous_version = latest_doc["name"]

				# Increment version
				try:
					last_version = float(latest_doc["version"])
					self.version = str(round(last_version + 0.1, 1))
				except Exception:
					self.version = "1.1"

			# Mark all previous versions as not latest
			for doc in existing_docs:
				frappe.db.set_value("Vehicle Document", doc["name"], "is_latest_version", 0)

		# Mark this as latest version
		self.is_latest_version = 1

	def before_save(self):
		"""Actions before saving"""
		self.set_upload_metadata()

	def set_upload_metadata(self):
		"""Set upload metadata"""
		if not self.uploaded_by:
			self.uploaded_by = frappe.session.user

		if not self.upload_date:
			self.upload_date = datetime.datetime.now()

	def on_update(self):
		"""Actions after update"""
		self.update_vehicle_documents_count()

	def update_vehicle_documents_count(self):
		"""Update document count in vehicle"""
		if self.vehicle:
			doc_count = frappe.db.count("Vehicle Document", {"vehicle": self.vehicle, "status": "Active"})

			frappe.db.set_value("Vehicle", self.vehicle, "documents_count", doc_count)

	@frappe.whitelist()
	def create_new_version(self, new_file, version_notes=None):
		"""Create a new version of this document"""
		new_doc = frappe.copy_doc(self)
		new_doc.file_attachment = new_file
		new_doc.previous_version = self.name
		new_doc.version_notes = version_notes
		new_doc.is_latest_version = 1
		new_doc.upload_date = datetime.datetime.now()
		new_doc.uploaded_by = frappe.session.user

		# Mark current document as not latest
		self.is_latest_version = 0
		self.save()

		new_doc.insert()
		return new_doc.name

	@frappe.whitelist()
	def archive_document(self, reason=None):
		"""Archive the document"""
		self.status = "Archived"
		if reason:
			self.add_comment("Info", f"Document archived. Reason: {reason}")
		self.save()

	@frappe.whitelist()
	def verify_document(self, verification_notes=None):
		"""Verify the document"""
		self.document_verified = 1
		self.verified_by = frappe.session.user
		self.verification_date = datetime.datetime.now()
		if verification_notes:
			self.verification_notes = verification_notes
		self.save()


# Utility functions
@frappe.whitelist()
def get_vehicle_documents(vehicle, document_type=None, latest_only=True):
	"""Get documents for a vehicle"""
	filters = {"vehicle": vehicle, "status": "Active"}

	if document_type:
		filters["document_type"] = document_type

	if latest_only:
		filters["is_latest_version"] = 1

	documents = frappe.get_all(
		"Vehicle Document",
		filters=filters,
		fields=[
			"name",
			"document_type",
			"title",
			"title_ar",
			"file_attachment",
			"upload_date",
			"version",
			"expiry_date",
			"file_size_mb",
			"file_format",
		],
		order_by="document_type, upload_date desc",
	)
	return documents


@frappe.whitelist()
def get_expiring_documents(days_ahead=30):
	"""Get documents expiring within specified days"""
	from datetime import timedelta

	end_date = datetime.date.today() + timedelta(days=days_ahead)

	documents = frappe.get_all(
		"Vehicle Document",
		filters={
			"status": "Active",
			"expiry_date": ["between", [datetime.date.today(), end_date]],
			"is_latest_version": 1,
		},
		fields=["name", "vehicle", "customer", "document_type", "title", "expiry_date", "file_attachment"],
		order_by="expiry_date asc",
	)

	return documents


@frappe.whitelist()
def get_document_history(vehicle, document_type):
	"""Get version history for a document type"""
	documents = frappe.get_all(
		"Vehicle Document",
		filters={"vehicle": vehicle, "document_type": document_type, "status": ["!=", "Deleted"]},
		fields=[
			"name",
			"version",
			"upload_date",
			"uploaded_by",
			"version_notes",
			"is_latest_version",
			"file_size_mb",
		],
		order_by="creation desc",
	)

	return documents


@frappe.whitelist()
def check_document_expiries():
	"""Daily job to check document expiries"""
	# Get documents expiring today
	expiring_today = frappe.get_all(
		"Vehicle Document",
		filters={"status": "Active", "expiry_date": datetime.date.today(), "is_latest_version": 1},
		fields=["name", "vehicle", "customer", "document_type", "title"],
	)

	# Mark as expired
	for doc in expiring_today:
		frappe.db.set_value("Vehicle Document", doc["name"], "status", "Expired")

		# Send notification to customer
		if doc["customer"]:
			send_expiry_notification(doc)


def send_expiry_notification(document):
	"""Send expiry notification to customer"""
	try:
		customer_doc = frappe.get_doc("Customer", document["customer"])
		vehicle_doc = frappe.get_doc("Vehicle", document["vehicle"])

		# Prepare notification content
		if frappe.db.get_value("Customer", document["customer"], "language") == "ar":
			subject = f"انتهاء صلاحية وثيقة - {document['title']}"
			message = f"""
            عزيزي/عزيزتي العميل،

            تم انتهاء صلاحية الوثيقة التالية:

            🚗 المركبة: {vehicle_doc.make} {vehicle_doc.model} ({vehicle_doc.license_plate})
            📄 نوع الوثيقة: {document["document_type"]}
            📅 تاريخ انتهاء الصلاحية: {datetime.date.today().strftime("%d/%m/%Y")}

            يرجى تحديث الوثيقة في أقرب وقت ممكن.
            شكراً لثقتكم بخدماتنا.
            """
		else:
			subject = f"Document Expired - {document['title']}"
			message = f"""
            Dear Customer,

            The following document has expired:

            🚗 Vehicle: {vehicle_doc.make} {vehicle_doc.model} ({vehicle_doc.license_plate})
            📄 Document Type: {document["document_type"]}
            📅 Expiry Date: {datetime.date.today().strftime("%d/%m/%Y")}

            Please update the document as soon as possible.
            Thank you for choosing our services.
            """

		# Send email notification
		if customer_doc.email_id:
			frappe.sendmail(recipients=[customer_doc.email_id], subject=subject, message=message)
	except Exception as e:
		frappe.log_error(f"Failed to send document expiry notification: {e!s}")


@frappe.whitelist()
def upload_document_batch(vehicle, documents_data):
	"""Batch upload multiple documents"""
	results = []

	for doc_data in documents_data:
		try:
			doc = frappe.new_doc("Vehicle Document")
			doc.vehicle = vehicle
			doc.document_type = doc_data.get("document_type")
			doc.title = doc_data.get("title")
			doc.title_ar = doc_data.get("title_ar")
			doc.file_attachment = doc_data.get("file_attachment")
			doc.description = doc_data.get("description")
			doc.description_ar = doc_data.get("description_ar")
			doc.expiry_date = doc_data.get("expiry_date")
			doc.tags = doc_data.get("tags")

			doc.insert()
			results.append({"success": True, "document": doc.name})

		except Exception as e:
			results.append({"success": False, "error": str(e)})

	return results


@frappe.whitelist()
def get_document_statistics(vehicle=None):
	"""Get document statistics"""
	filters = {"status": "Active"}
	if vehicle:
		filters["vehicle"] = vehicle

	# Count by document type
	type_counts = frappe.db.sql(
		"""
        SELECT document_type, COUNT(*) as count
        FROM `tabVehicle Document`
        WHERE status = 'Active' {vehicle_filter}
        GROUP BY document_type
        ORDER BY count DESC
    """.format(vehicle_filter=f"AND vehicle = '{vehicle}'" if vehicle else ""),
		as_dict=True,
	)

	# Get expiry statistics
	expiry_stats = frappe.db.sql(
		"""
        SELECT
            COUNT(CASE WHEN expiry_date < CURDATE() THEN 1 END) as expired,
            COUNT(CASE WHEN expiry_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY) THEN 1 END) as expiring_soon,
            COUNT(CASE WHEN expiry_date > DATE_ADD(CURDATE(), INTERVAL 30 DAY) OR expiry_date IS NULL THEN 1 END) as valid
        FROM `tabVehicle Document`
        WHERE status = 'Active' {vehicle_filter}
    """.format(vehicle_filter=f"AND vehicle = '{vehicle}'" if vehicle else ""),
		as_dict=True,
	)

	return {
		"type_counts": type_counts,
		"expiry_stats": expiry_stats[0] if expiry_stats else {"expired": 0, "expiring_soon": 0, "valid": 0},
	}
