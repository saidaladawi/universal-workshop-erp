import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today, now, flt, cint, get_datetime
from datetime import datetime, timedelta
import json


class ReturnRequest(Document):
    # pylint: disable=no-member

    def validate(self):
        """Comprehensive validation for return request"""
        self.validate_basic_fields()
        self.validate_return_eligibility()
        self.calculate_return_values()
        self.assess_fraud_risk()
        self.set_auto_approval()
        self.fetch_original_transaction_data()

    def on_update(self):
        """Called when document is updated"""
        from universal_workshop.sales_service.utils.workflow_utils import WorkflowUtils
        WorkflowUtils.update_return_request_fields(self)
        WorkflowUtils.send_workflow_notification(self)

    def validate_basic_fields(self):
        """Validate required fields based on request type"""
        if not self.request_type:
            frappe.throw(_("نوع الطلب مطلوب / Request type is required"))
        if not self.sales_invoice:
            frappe.throw(_("فاتورة البيع مطلوبة / Sales invoice is required"))
        if not self.customer:
            frappe.throw(_("العميل مطلوب / Customer is required"))
        if not self.reason_details:
            frappe.throw(_("تفاصيل السبب مطلوبة / Reason details are required"))
        
        # Validate items for parts return
        if self.request_type in ["Parts", "Both"]:
            if not self.item_code:
                frappe.throw(_("كود القطعة مطلوب / Item code is required"))
        
        # Validate service orders for service return
        if self.request_type in ["Service", "Both"]:
            if not self.service_order:
                frappe.throw(_("أمر الخدمة مطلوب / Service order is required"))

    def validate_return_eligibility(self):
        """Check if the return is eligible based on business rules"""
        # Check if sales invoice exists and is valid
        if not frappe.db.exists("Sales Invoice", self.sales_invoice):
            frappe.throw(_("فاتورة البيع غير موجودة / Sales invoice does not exist"))
        
        sales_invoice = frappe.get_doc("Sales Invoice", self.sales_invoice)
        if sales_invoice.docstatus != 1:
            frappe.throw(_("فاتورة البيع غير مرسلة / Sales invoice is not submitted"))
        
        # Check return time limit (default 30 days)
        return_limit_days = frappe.db.get_single_value("Workshop Settings", "return_limit_days") or 30
        invoice_date = get_datetime(sales_invoice.posting_date)
        days_since_purchase = (get_datetime(today()) - invoice_date).days
        
        if days_since_purchase > return_limit_days:
            self.eligible_for_return = 0
            frappe.throw(_("انتهت مدة الاسترداد المسموحة ({0} يوم) / Return period expired ({0} days)").format(return_limit_days))
        else:
            self.eligible_for_return = 1
        
        # Check if item was actually purchased in this invoice
        if self.item_code:
            found_item = False
            for item in sales_invoice.items:
                if item.item_code == self.item_code:
                    found_item = True
                    # Validate quantity doesn't exceed purchased quantity
                    returned_qty = self.get_previously_returned_quantity()
                    remaining_qty = item.qty - returned_qty
                    if self.quantity > remaining_qty:
                        frappe.throw(_("الكمية المطلوب إرجاعها أكبر من المتاح / Return quantity exceeds available quantity"))
                    break
            
            if not found_item:
                frappe.throw(_("القطعة غير موجودة في الفاتورة / Item not found in sales invoice"))

    def get_previously_returned_quantity(self):
        """Get previously returned quantity for this item from this invoice"""
        returned_qty = frappe.db.sql("""
            SELECT SUM(quantity) 
            FROM `tabReturn Request` 
            WHERE sales_invoice = %s 
            AND item_code = %s 
            AND return_status IN ('Approved', 'Completed')
            AND name != %s
        """, (self.sales_invoice, self.item_code, self.name or ""))
        
        return flt(returned_qty[0][0]) if returned_qty and returned_qty[0][0] else 0

    def fetch_original_transaction_data(self):
        """Fetch data from original sales invoice and items"""
        if self.sales_invoice and self.item_code:
            sales_invoice = frappe.get_doc("Sales Invoice", self.sales_invoice)
            for item in sales_invoice.items:
                if item.item_code == self.item_code:
                    self.original_rate = item.rate
                    self.warehouse = item.warehouse
                    break

    def calculate_return_values(self):
        """Calculate return values and refund amounts"""
        if not self.quantity or not self.original_rate:
            return
        
        # Calculate return value
        self.return_value = flt(self.quantity * self.original_rate, 3)
        
        # Apply restocking fee if configured
        if not self.restocking_fee:
            restocking_percentage = frappe.db.get_single_value("Workshop Settings", "restocking_fee_percentage") or 0
            if restocking_percentage > 0:
                self.restocking_fee = flt(self.return_value * restocking_percentage / 100, 3)
        
        # Calculate net refund amount
        self.refund_amount = flt(self.return_value - (self.restocking_fee or 0), 3)

    def assess_fraud_risk(self):
        """Assess fraud risk based on various factors"""
        risk_score = 0
        
        # Check customer history
        customer_returns = frappe.db.count("Return Request", 
                                          filters={"customer": self.customer, 
                                                 "return_status": ["in", ["Approved", "Completed"]]})
        
        if customer_returns > 5:  # Frequent returner
            risk_score += 20
        elif customer_returns > 10:  # Very frequent returner
            risk_score += 40
        
        # Check return value
        if self.return_value > 200:  # High value return
            risk_score += 20
        elif self.return_value > 500:  # Very high value return
            risk_score += 40
        
        # Check time since purchase
        if self.sales_invoice:
            sales_invoice = frappe.get_doc("Sales Invoice", self.sales_invoice)
            days_since_purchase = (get_datetime(today()) - get_datetime(sales_invoice.posting_date)).days
            
            if days_since_purchase < 1:  # Same day return
                risk_score += 30
            elif days_since_purchase > 25:  # Late return
                risk_score += 15
        
        # Check return reason
        suspicious_reasons = ["CHANGED_MIND", "FOUND_CHEAPER", "OTHER"]
        if self.return_reason in suspicious_reasons:
            risk_score += 10
        
        # Set risk level
        if risk_score <= 20:
            self.fraud_risk_level = "Low"
        elif risk_score <= 40:
            self.fraud_risk_level = "Medium"
        else:
            self.fraud_risk_level = "High"

    def set_auto_approval(self):
        """Set automatic approval for low-risk returns"""
        auto_approval_limit = frappe.db.get_single_value("Workshop Settings", "return_auto_approval_limit") or 50
        
        if (self.eligible_for_return and 
            self.fraud_risk_level == "Low" and 
            self.return_value <= auto_approval_limit):
            self.auto_approved = 1
            if self.return_status == "Draft":
                self.return_status = "Approved"
                self.approved_by = frappe.session.user
                self.approval_date = now()

    def before_submit(self):
        """Actions before submitting the document"""
        if not hasattr(self, 'workflow_state') or not self.workflow_state:
            self.workflow_state = "Pending Review"

    def on_submit(self):
        """Actions after submitting the document"""
        # Send notification to customer
        self.send_customer_notification()
        
        # If auto-approved, process immediately
        if self.auto_approved and self.return_status == "Approved":
            self.process_return()

    def process_return(self):
        """Process the approved return request"""
        if self.return_status != "Approved":
            frappe.throw(_("يجب الموافقة على طلب الاسترداد أولاً / Return request must be approved first"))
        
        try:
            # Create stock entry for return
            if self.request_type in ["Parts", "Both"] and self.item_code:
                self.create_stock_entry()
            
            # Create credit note for refund
            self.create_credit_note()
            
            # Update status
            self.return_status = "Completed"
            self.processed_by = frappe.session.user
            self.processing_date = now()
            self.save()
            
            # Send completion notification
            self.send_completion_notification()
            
            frappe.msgprint(_("تم معالجة طلب الاسترداد بنجاح / Return request processed successfully"))
            
        except Exception as e:
            frappe.log_error(f"Error processing return request {self.name}: {str(e)}")
            frappe.throw(_("خطأ في معالجة طلب الاسترداد / Error processing return request: {0}").format(str(e)))

    def create_stock_entry(self):
        """Create stock entry for the returned item"""
        stock_entry = frappe.new_doc("Stock Entry")
        stock_entry.stock_entry_type = "Material Receipt"
        stock_entry.company = frappe.defaults.get_user_default("Company")
        
        stock_entry.append("items", {
            "item_code": self.item_code,
            "qty": self.quantity,
            "t_warehouse": self.warehouse or "Stores - UW",
            "basic_rate": self.original_rate
        })
        
        stock_entry.insert()
        stock_entry.submit()
        
        self.stock_entry = stock_entry.name

    def create_credit_note(self):
        """Create credit note for the refund"""
        credit_note = frappe.new_doc("Sales Invoice")
        credit_note.customer = self.customer
        credit_note.company = frappe.defaults.get_user_default("Company")
        credit_note.is_return = 1
        credit_note.return_against = self.sales_invoice
        credit_note.set_against_income_account = 1
        
        # Add returned item
        credit_note.append("items", {
            "item_code": self.item_code,
            "qty": -self.quantity,  # Negative quantity for return
            "rate": self.original_rate,
            "warehouse": self.warehouse or "Stores - UW"
        })
        
        # Add restocking fee if applicable
        if self.restocking_fee > 0:
            credit_note.append("items", {
                "item_code": "RESTOCKING-FEE",  # This should be a service item
                "item_name": "Restocking Fee",
                "qty": 1,
                "rate": self.restocking_fee,
                "is_free_item": 0
            })
        
        credit_note.insert()
        credit_note.submit()
        
        self.credit_note = credit_note.name

    def send_customer_notification(self):
        """Send notification to customer about return request status"""
        try:
            customer_doc = frappe.get_doc("Customer", self.customer)
            if customer_doc.email_id:
                subject = _("طلب الاسترداد رقم {0} / Return Request {0}").format(self.name)
                message = self.get_notification_message()
                
                frappe.sendmail(
                    recipients=[customer_doc.email_id],
                    subject=subject,
                    message=message,
                    reference_doctype=self.doctype,
                    reference_name=self.name
                )
        except Exception as e:
            frappe.log_error(f"Failed to send customer notification for {self.name}: {str(e)}")

    def send_completion_notification(self):
        """Send notification when return is completed"""
        try:
            customer_doc = frappe.get_doc("Customer", self.customer)
            if customer_doc.email_id:
                subject = _("تم معالجة طلب الاسترداد {0} / Return Request {0} Processed").format(self.name)
                message = _("تم معالجة طلب الاسترداد الخاص بك. سيتم إرسال المبلغ المستحق {0} OMR خلال 3-5 أيام عمل / Your return has been processed. Refund of {0} OMR will be sent within 3-5 business days").format(self.refund_amount)
                
                frappe.sendmail(
                    recipients=[customer_doc.email_id],
                    subject=subject,
                    message=message,
                    reference_doctype=self.doctype,
                    reference_name=self.name
                )
        except Exception as e:
            frappe.log_error(f"Failed to send completion notification for {self.name}: {str(e)}")

    def get_notification_message(self):
        """Get email notification message based on status"""
        if self.return_status == "Pending Review":
            return _("تم استلام طلب الاسترداد الخاص بك وهو قيد المراجعة / Your return request has been received and is under review")
        elif self.return_status == "Approved":
            return _("تم الموافقة على طلب الاسترداد الخاص بك وسيتم معالجته قريباً / Your return request has been approved and will be processed soon")
        elif self.return_status == "Rejected":
            return _("عذراً، تم رفض طلب الاسترداد الخاص بك / Sorry, your return request has been rejected")
        else:
            return _("تم تحديث حالة طلب الاسترداد الخاص بك / Your return request status has been updated")

    def autoname(self):
        """Generate automatic name for the document"""
        self.name = frappe.model.naming.make_autoname("RET-.YYYY.-.#####")


# Whitelisted methods for API access
@frappe.whitelist()
def approve_return_request(return_request_name):
    """Approve a return request"""
    doc = frappe.get_doc("Return Request", return_request_name)
    if doc.return_status != "Pending Review":
        frappe.throw(_("يمكن الموافقة على الطلبات المعلقة فقط / Can only approve pending requests"))
    
    doc.return_status = "Approved"
    doc.approved_by = frappe.session.user
    doc.approval_date = now()
    doc.save()
    
    return {"status": "success", "message": _("تم الموافقة على طلب الاسترداد / Return request approved")}

@frappe.whitelist()
def reject_return_request(return_request_name, rejection_reason=None):
    """Reject a return request"""
    doc = frappe.get_doc("Return Request", return_request_name)
    if doc.return_status not in ["Pending Review", "Draft"]:
        frappe.throw(_("يمكن رفض الطلبات المعلقة أو المسودات فقط / Can only reject pending or draft requests"))
    
    doc.return_status = "Rejected"
    doc.approved_by = frappe.session.user
    doc.approval_date = now()
    if rejection_reason:
        doc.admin_notes = rejection_reason
    doc.save()
    
    return {"status": "success", "message": _("تم رفض طلب الاسترداد / Return request rejected")}
