import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today, now, flt, cint, get_datetime
from datetime import datetime, timedelta
import json


class ExchangeRequest(Document):
    # pylint: disable=no-member

    def validate(self):
        """Comprehensive validation for exchange request"""
        self.validate_basic_fields()
        self.validate_exchange_eligibility()
        self.calculate_price_differences()
        self.check_inventory_availability()
        self.assess_compatibility_and_risk()
        self.set_auto_approval()
        self.fetch_original_transaction_data()

    def validate_basic_fields(self):
        """Validate required fields based on exchange type"""
        if not self.exchange_type:
            frappe.throw(_("نوع التبديل مطلوب / Exchange type is required"))
        if not self.original_sales_invoice:
            frappe.throw(_("فاتورة البيع الأصلية مطلوبة / Original sales invoice is required"))
        if not self.customer:
            frappe.throw(_("العميل مطلوب / Customer is required"))
        if not self.exchange_reason_details:
            frappe.throw(_("تفاصيل سبب التبديل مطلوبة / Exchange reason details are required"))

        # Validate items for parts exchange
        if self.exchange_type in ["Parts", "Both"]:
            if not self.original_item_code:
                frappe.throw(_("كود القطعة الأصلية مطلوب / Original item code is required"))
            if not self.exchange_item_code:
                frappe.throw(_("كود القطعة البديلة مطلوب / Exchange item code is required"))
            if self.original_item_code == self.exchange_item_code:
                frappe.throw(_("لا يمكن تبديل القطعة بنفسها / Cannot exchange item with itself"))

        # Validate service orders for service exchange
        if self.exchange_type in ["Service", "Both"]:
            if not self.original_service_order:
                frappe.throw(_("أمر الخدمة الأصلي مطلوب / Original service order is required"))
            if not self.exchange_service_order:
                frappe.throw(_("أمر الخدمة البديل مطلوب / Exchange service order is required"))

    def validate_exchange_eligibility(self):
        """Check if the exchange is eligible based on business rules"""
        # Check if original sales invoice exists and is valid
        if not frappe.db.exists("Sales Invoice", self.original_sales_invoice):
            frappe.throw(
                _("فاتورة البيع الأصلية غير موجودة / Original sales invoice does not exist")
            )

        sales_invoice = frappe.get_doc("Sales Invoice", self.original_sales_invoice)
        if sales_invoice.docstatus != 1:
            frappe.throw(
                _("فاتورة البيع الأصلية غير مرسلة / Original sales invoice is not submitted")
            )

        # Check exchange time limit (default 30 days)
        exchange_limit_days = (
            frappe.db.get_single_value("Workshop Settings", "exchange_limit_days") or 30
        )
        invoice_date = get_datetime(sales_invoice.posting_date)
        days_since_purchase = (get_datetime(today()) - invoice_date).days

        if days_since_purchase > exchange_limit_days:
            self.eligible_for_exchange = 0
            frappe.throw(
                _(
                    "انتهت مدة التبديل المسموحة ({0} يوم) / Exchange period expired ({0} days)"
                ).format(exchange_limit_days)
            )
        else:
            self.eligible_for_exchange = 1

        # Check if original item was actually purchased in this invoice
        if self.original_item_code:
            found_item = False
            for item in sales_invoice.items:
                if item.item_code == self.original_item_code:
                    found_item = True
                    # Validate quantity doesn't exceed purchased quantity
                    exchanged_qty = self.get_previously_exchanged_quantity()
                    remaining_qty = item.qty - exchanged_qty
                    if self.original_quantity > remaining_qty:
                        frappe.throw(
                            _(
                                "الكمية المطلوب تبديلها أكبر من المتاح / Exchange quantity exceeds available quantity"
                            )
                        )
                    break

            if not found_item:
                frappe.throw(
                    _(
                        "القطعة الأصلية غير موجودة في الفاتورة / Original item not found in sales invoice"
                    )
                )

    def get_previously_exchanged_quantity(self):
        """Get previously exchanged quantity for this item from this invoice"""
        exchanged_qty = frappe.db.sql(
            """
            SELECT SUM(original_quantity) 
            FROM `tabExchange Request` 
            WHERE original_sales_invoice = %s 
            AND original_item_code = %s 
            AND exchange_status IN ('Approved', 'Processed')
            AND name != %s
        """,
            (self.original_sales_invoice, self.original_item_code, self.name or ""),
        )

        return flt(exchanged_qty[0][0]) if exchanged_qty and exchanged_qty[0][0] else 0

    def fetch_original_transaction_data(self):
        """Fetch data from original sales invoice and items"""
        if self.original_sales_invoice and self.original_item_code:
            sales_invoice = frappe.get_doc("Sales Invoice", self.original_sales_invoice)
            for item in sales_invoice.items:
                if item.item_code == self.original_item_code:
                    self.original_rate = item.rate
                    self.original_warehouse = item.warehouse
                    break

        # Fetch exchange item data
        if self.exchange_item_code:
            item_doc = frappe.get_doc("Item", self.exchange_item_code)
            # Get current price list rate
            price_list = frappe.db.get_single_value("Selling Settings", "selling_price_list")
            if price_list:
                item_price = frappe.db.get_value(
                    "Item Price",
                    {"item_code": self.exchange_item_code, "price_list": price_list},
                    "price_list_rate",
                )
                if item_price:
                    self.exchange_rate = item_price

    def calculate_price_differences(self):
        """Calculate price differences and payment adjustments"""
        if not self.original_quantity or not self.exchange_quantity:
            return

        # Calculate original total value
        self.original_total_value = flt(self.original_quantity * (self.original_rate or 0), 3)

        # Calculate exchange total value
        self.exchange_total_value = flt(self.exchange_quantity * (self.exchange_rate or 0), 3)

        # Calculate price difference
        self.price_difference = flt(self.exchange_total_value - self.original_total_value, 3)

        # Apply handling fee if configured
        if not self.handling_fee:
            self.handling_fee = (
                frappe.db.get_single_value("Workshop Settings", "exchange_handling_fee") or 0
            )

        # Calculate final amounts
        if self.price_difference > 0:
            # Customer needs to pay additional amount
            self.additional_payment = flt(self.price_difference + self.handling_fee, 3)
            self.refund_amount = 0
            self.final_amount = self.additional_payment
        else:
            # Customer gets refund
            self.additional_payment = 0
            self.refund_amount = flt(abs(self.price_difference) - self.handling_fee, 3)
            self.final_amount = -self.refund_amount

    def check_inventory_availability(self):
        """Check inventory availability for exchange items"""
        if not self.exchange_item_code:
            return

        # Get available quantity in all warehouses
        available_qty = frappe.db.sql(
            """
            SELECT SUM(actual_qty) 
            FROM `tabBin` 
            WHERE item_code = %s 
            AND actual_qty > 0
        """,
            (self.exchange_item_code,),
        )

        total_available = flt(available_qty[0][0]) if available_qty and available_qty[0][0] else 0
        self.exchange_available_qty = total_available

        # Check if sufficient quantity is available
        if total_available < self.exchange_quantity:
            self.availability_status = "Out of Stock"
            # Calculate estimated delivery based on lead time
            item_doc = frappe.get_doc("Item", self.exchange_item_code)
            lead_time_days = getattr(item_doc, "lead_time_days", 7)
            if lead_time_days:
                self.estimated_delivery = frappe.utils.add_days(today(), lead_time_days)
        elif total_available >= self.exchange_quantity:
            self.availability_status = "Available"

        # Find best warehouse for exchange item
        warehouse_qty = frappe.db.sql(
            """
            SELECT warehouse, actual_qty 
            FROM `tabBin` 
            WHERE item_code = %s 
            AND actual_qty >= %s
            ORDER BY actual_qty DESC
            LIMIT 1
        """,
            (self.exchange_item_code, self.exchange_quantity),
        )

        if warehouse_qty:
            self.exchange_warehouse = warehouse_qty[0][0]

        # Set stock impact
        self.stock_impact_original = self.original_quantity  # Items returning to stock
        self.stock_impact_exchange = -self.exchange_quantity  # Items leaving stock

        # Check if stock transfer is required
        self.requires_stock_transfer = (
            1 if self.original_warehouse != self.exchange_warehouse else 0
        )

    def assess_compatibility_and_risk(self):
        """Assess compatibility between original and exchange items"""
        if not self.original_item_code or not self.exchange_item_code:
            return

        compatibility_score = 0

        # Get item details
        original_item = frappe.get_doc("Item", self.original_item_code)
        exchange_item = frappe.get_doc("Item", self.exchange_item_code)

        # Check item group compatibility (70% weight)
        if original_item.item_group == exchange_item.item_group:
            compatibility_score += 70
        elif self.is_compatible_item_group(original_item.item_group, exchange_item.item_group):
            compatibility_score += 50

        # Check brand compatibility (20% weight)
        if getattr(original_item, "brand", None) == getattr(exchange_item, "brand", None):
            compatibility_score += 20

        # Check price range compatibility (10% weight)
        price_diff_percentage = (
            abs(self.price_difference) / self.original_total_value * 100
            if self.original_total_value
            else 0
        )
        if price_diff_percentage <= 10:
            compatibility_score += 10
        elif price_diff_percentage <= 25:
            compatibility_score += 5

        self.compatibility_score = flt(compatibility_score, 2)

        # Set exchange complexity based on various factors
        complexity_factors = 0

        if price_diff_percentage > 50:
            complexity_factors += 1
        if self.requires_stock_transfer:
            complexity_factors += 1
        if self.availability_status != "Available":
            complexity_factors += 1
        if compatibility_score < 70:
            complexity_factors += 1

        if complexity_factors == 0:
            self.exchange_complexity = "Simple"
        elif complexity_factors <= 1:
            self.exchange_complexity = "Moderate"
        elif complexity_factors <= 2:
            self.exchange_complexity = "Complex"
        else:
            self.exchange_complexity = "Critical"

        # Set risk level
        if compatibility_score >= 90 and self.exchange_complexity == "Simple":
            self.risk_level = "Low"
        elif compatibility_score >= 70 and self.exchange_complexity in ["Simple", "Moderate"]:
            self.risk_level = "Medium"
        elif compatibility_score >= 50:
            self.risk_level = "High"
        else:
            self.risk_level = "Critical"

        # Set manager approval requirement
        self.requires_manager_approval = (
            1
            if (
                self.risk_level in ["High", "Critical"]
                or abs(self.price_difference) > 100
                or self.exchange_complexity in ["Complex", "Critical"]
            )
            else 0
        )

    def is_compatible_item_group(self, group1, group2):
        """Check if two item groups are compatible for exchange"""
        # This can be customized based on business rules
        compatible_groups = {
            "Engine Parts": ["Engine Components", "Engine Accessories"],
            "Brake System": ["Brake Parts", "Brake Components"],
            "Electrical": ["Electronics", "Electrical Components"],
            # Add more compatibility rules as needed
        }

        return group2 in compatible_groups.get(group1, [])

    def set_auto_approval(self):
        """Set automatic approval for low-risk exchanges"""
        auto_approval_limit = (
            frappe.db.get_single_value("Workshop Settings", "exchange_auto_approval_limit") or 25
        )

        if (
            self.eligible_for_exchange
            and self.risk_level == "Low"
            and self.exchange_complexity == "Simple"
            and abs(self.price_difference) <= auto_approval_limit
            and self.availability_status == "Available"
        ):
            self.auto_approved = 1
            if self.exchange_status == "Draft":
                self.exchange_status = "Approved"
                self.approved_by = frappe.session.user
                self.approval_date = now()

    def on_update(self):
        """Called when document is updated"""
        from universal_workshop.sales_service.utils.workflow_utils import WorkflowUtils

        WorkflowUtils.update_exchange_request_fields(self)
        WorkflowUtils.send_workflow_notification(self)

    def before_submit(self):
        """Actions before submitting the document"""
        if self.exchange_status == "Draft":
            self.exchange_status = "Pending Approval"

    def on_submit(self):
        """Actions after submitting the document"""
        # Send notification to customer
        self.send_customer_notification()

        # If auto-approved, process immediately
        if self.auto_approved and self.exchange_status == "Approved":
            self.process_exchange()

    def process_exchange(self):
        """Process the approved exchange request"""
        if self.exchange_status != "Approved":
            frappe.throw(
                _("يجب الموافقة على طلب التبديل أولاً / Exchange request must be approved first")
            )

        try:
            # Create stock entry for exchange
            if (
                self.exchange_type in ["Parts", "Both"]
                and self.original_item_code
                and self.exchange_item_code
            ):
                self.create_stock_entry()

            # Create new sales invoice for the exchange
            self.create_exchange_invoice()

            # Update status
            self.exchange_status = "Processed"
            self.processed_by = frappe.session.user
            self.processing_date = now()
            self.save()

            # Send processing notification
            self.send_processing_notification()

            frappe.msgprint(
                _("تم معالجة طلب التبديل بنجاح / Exchange request processed successfully")
            )

        except Exception as e:
            frappe.log_error(f"Error processing exchange request {self.name}: {str(e)}")
            frappe.throw(
                _("خطأ في معالجة طلب التبديل / Error processing exchange request: {0}").format(
                    str(e)
                )
            )

    def create_stock_entry(self):
        """Create stock entry for the exchange"""
        stock_entry = frappe.new_doc("Stock Entry")
        stock_entry.stock_entry_type = "Material Transfer"
        stock_entry.company = frappe.defaults.get_user_default("Company")

        # Return original item to stock
        stock_entry.append(
            "items",
            {
                "item_code": self.original_item_code,
                "qty": self.original_quantity,
                "t_warehouse": self.original_warehouse or "Stores - UW",
                "basic_rate": self.original_rate,
            },
        )

        # Issue exchange item from stock
        stock_entry.append(
            "items",
            {
                "item_code": self.exchange_item_code,
                "qty": self.exchange_quantity,
                "s_warehouse": self.exchange_warehouse or "Stores - UW",
                "basic_rate": self.exchange_rate,
            },
        )

        stock_entry.insert()
        stock_entry.submit()

        self.stock_entry = stock_entry.name

    def create_exchange_invoice(self):
        """Create new sales invoice for the exchange"""
        # Create sales invoice for the exchange item
        sales_invoice = frappe.new_doc("Sales Invoice")
        sales_invoice.customer = self.customer
        sales_invoice.company = frappe.defaults.get_user_default("Company")
        sales_invoice.set_against_income_account = 1

        # Add exchange item
        sales_invoice.append(
            "items",
            {
                "item_code": self.exchange_item_code,
                "qty": self.exchange_quantity,
                "rate": self.exchange_rate,
                "warehouse": self.exchange_warehouse or "Stores - UW",
            },
        )

        # Add handling fee if applicable
        if self.handling_fee > 0:
            sales_invoice.append(
                "items",
                {
                    "item_code": "EXCHANGE-FEE",  # This should be a service item
                    "item_name": "Exchange Handling Fee",
                    "qty": 1,
                    "rate": self.handling_fee,
                    "is_free_item": 0,
                },
            )

        sales_invoice.insert()
        sales_invoice.submit()

        self.new_sales_invoice = sales_invoice.name

    def send_customer_notification(self):
        """Send notification to customer about exchange request status"""
        try:
            customer_doc = frappe.get_doc("Customer", self.customer)
            if customer_doc.email_id:
                subject = _("طلب التبديل رقم {0} / Exchange Request {0}").format(self.name)
                message = self.get_notification_message()

                frappe.sendmail(
                    recipients=[customer_doc.email_id],
                    subject=subject,
                    message=message,
                    reference_doctype=self.doctype,
                    reference_name=self.name,
                )
        except Exception as e:
            frappe.log_error(f"Failed to send customer notification for {self.name}: {str(e)}")

    def send_processing_notification(self):
        """Send notification when exchange is processed"""
        try:
            customer_doc = frappe.get_doc("Customer", self.customer)
            if customer_doc.email_id:
                subject = _("تم معالجة طلب التبديل {0} / Exchange Request {0} Processed").format(
                    self.name
                )

                if self.final_amount > 0:
                    message = _(
                        "تم معالجة طلب التبديل الخاص بك. يرجى دفع المبلغ الإضافي {0} OMR / Your exchange has been processed. Please pay the additional amount of {0} OMR"
                    ).format(self.final_amount)
                elif self.final_amount < 0:
                    message = _(
                        "تم معالجة طلب التبديل الخاص بك. سيتم إرسال المبلغ المستحق {0} OMR خلال 3-5 أيام عمل / Your exchange has been processed. Refund of {0} OMR will be sent within 3-5 business days"
                    ).format(abs(self.final_amount))
                else:
                    message = _(
                        "تم معالجة طلب التبديل الخاص بك بنجاح / Your exchange has been processed successfully"
                    )

                frappe.sendmail(
                    recipients=[customer_doc.email_id],
                    subject=subject,
                    message=message,
                    reference_doctype=self.doctype,
                    reference_name=self.name,
                )
        except Exception as e:
            frappe.log_error(f"Failed to send processing notification for {self.name}: {str(e)}")

    def get_notification_message(self):
        """Get email notification message based on status"""
        if self.exchange_status == "Pending Approval":
            return _(
                "تم استلام طلب التبديل الخاص بك وهو قيد المراجعة / Your exchange request has been received and is under review"
            )
        elif self.exchange_status == "Approved":
            return _(
                "تم الموافقة على طلب التبديل الخاص بك وسيتم معالجته قريباً / Your exchange request has been approved and will be processed soon"
            )
        elif self.exchange_status == "Rejected":
            return _(
                "عذراً، تم رفض طلب التبديل الخاص بك / Sorry, your exchange request has been rejected"
            )
        else:
            return _(
                "تم تحديث حالة طلب التبديل الخاص بك / Your exchange request status has been updated"
            )

    def autoname(self):
        """Generate automatic name for the document"""
        self.name = frappe.model.naming.make_autoname("EX-.YYYY.-.#####")


# Whitelisted methods for API access
@frappe.whitelist()
def get_item_exchange_suggestions(original_item_code, customer=None):
    """Get suggested items for exchange based on compatibility"""
    if not original_item_code:
        return []

    original_item = frappe.get_doc("Item", original_item_code)

    # Get items from same group with similar characteristics
    suggestions = frappe.db.sql(
        """
        SELECT 
            item_code, 
            item_name, 
            brand,
            (SELECT price_list_rate FROM `tabItem Price` ip 
             WHERE ip.item_code = i.item_code 
             AND ip.price_list = %s LIMIT 1) as current_rate
        FROM `tabItem` i
        WHERE i.item_group = %s 
        AND i.item_code != %s
        AND i.disabled = 0
        AND i.has_variants = 0
        ORDER BY i.item_name
    """,
        (
            frappe.db.get_single_value("Selling Settings", "selling_price_list"),
            original_item.item_group,
            original_item_code,
        ),
        as_dict=True,
    )

    return suggestions


@frappe.whitelist()
def approve_exchange_request(exchange_request_name):
    """Approve an exchange request"""
    doc = frappe.get_doc("Exchange Request", exchange_request_name)
    if doc.exchange_status != "Pending Approval":
        frappe.throw(_("يمكن الموافقة على الطلبات المعلقة فقط / Can only approve pending requests"))

    doc.exchange_status = "Approved"
    doc.approved_by = frappe.session.user
    doc.approval_date = now()
    doc.save()

    return {
        "status": "success",
        "message": _("تم الموافقة على طلب التبديل / Exchange request approved"),
    }


@frappe.whitelist()
def reject_exchange_request(exchange_request_name, rejection_reason=None):
    """Reject an exchange request"""
    doc = frappe.get_doc("Exchange Request", exchange_request_name)
    if doc.exchange_status not in ["Pending Approval", "Draft"]:
        frappe.throw(
            _(
                "يمكن رفض الطلبات المعلقة أو المسودات فقط / Can only reject pending or draft requests"
            )
        )

    doc.exchange_status = "Rejected"
    doc.approved_by = frappe.session.user
    doc.approval_date = now()
    if rejection_reason:
        doc.admin_notes = rejection_reason
    doc.save()

    return {"status": "success", "message": _("تم رفض طلب التبديل / Exchange request rejected")}


@frappe.whitelist()
def calculate_exchange_preview(
    original_item_code, exchange_item_code, original_quantity=1, exchange_quantity=1
):
    """Calculate exchange preview before creating the request"""
    if not original_item_code or not exchange_item_code:
        return {}

    # Get item rates
    price_list = frappe.db.get_single_value("Selling Settings", "selling_price_list")

    original_rate = (
        frappe.db.get_value(
            "Item Price",
            {"item_code": original_item_code, "price_list": price_list},
            "price_list_rate",
        )
        or 0
    )

    exchange_rate = (
        frappe.db.get_value(
            "Item Price",
            {"item_code": exchange_item_code, "price_list": price_list},
            "price_list_rate",
        )
        or 0
    )

    # Calculate values
    original_total = flt(original_quantity) * flt(original_rate)
    exchange_total = flt(exchange_quantity) * flt(exchange_rate)
    price_difference = exchange_total - original_total

    # Get handling fee
    handling_fee = frappe.db.get_single_value("Workshop Settings", "exchange_handling_fee") or 0

    # Calculate final amount
    if price_difference > 0:
        final_amount = price_difference + handling_fee
        payment_type = "additional_payment"
    else:
        final_amount = abs(price_difference) - handling_fee
        payment_type = "refund"

    return {
        "original_rate": original_rate,
        "exchange_rate": exchange_rate,
        "original_total": original_total,
        "exchange_total": exchange_total,
        "price_difference": price_difference,
        "handling_fee": handling_fee,
        "final_amount": final_amount,
        "payment_type": payment_type,
    }
