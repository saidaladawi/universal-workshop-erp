# Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class MobileScanSession(Document):
	"""
	Mobile Scan Session DocType
	Tracks mobile barcode scanning sessions for inventory management
	"""
	
	def before_insert(self):
		"""Set session defaults before insert"""
		if not self.session_id:
			self.session_id = frappe.generate_hash()
		
		if not self.start_time:
			self.start_time = frappe.utils.now()
		
		if not self.user:
			self.user = frappe.session.user
	
	def before_save(self):
		"""Update calculated fields before save"""
		self.total_scans = len(self.scans)
		
		if self.status == "Completed" and not self.end_time:
			self.end_time = frappe.utils.now()
	
	def validate(self):
		"""Validate session data"""
		if self.end_time and self.start_time:
			if self.end_time < self.start_time:
				frappe.throw("End time cannot be before start time")
		
		# Validate scan details
		for scan in self.scans:
			if not scan.item_code:
				frappe.throw("Item code is required for all scans")
			
			if scan.quantity <= 0:
				frappe.throw("Quantity must be greater than 0")
	
	def on_submit(self):
		"""Process session data on submit"""
		if self.status != "Completed":
			self.status = "Completed"
			self.end_time = frappe.utils.now()
			self.save()
		
		# Process scans based on mode
		self.process_session_scans()
	
	def process_session_scans(self):
		"""Process scans based on session mode"""
		if self.scan_mode in ["Receive", "Issue", "Adjust"]:
			self.create_stock_entries()
		elif self.scan_mode in ["Stock Take", "Cycle Count"]:
			self.create_stock_reconciliation()
	
	def create_stock_entries(self):
		"""Create stock entries for receive/issue/adjust operations"""
		if not self.scans:
			return
		
		# Group scans by operation type
		grouped_scans = {}
		for scan in self.scans:
			operation = scan.operation or self.scan_mode.lower()
			if operation not in grouped_scans:
				grouped_scans[operation] = []
			grouped_scans[operation].append(scan)
		
		# Create stock entries for each operation type
		for operation, scans in grouped_scans.items():
			try:
				stock_entry = self.create_stock_entry_for_operation(operation, scans)
				if stock_entry:
					frappe.msgprint(f"Stock Entry {stock_entry.name} created for {operation} operations")
			except Exception as e:
				frappe.log_error(f"Error creating stock entry for {operation}: {str(e)}")
				frappe.msgprint(f"Error processing {operation} scans: {str(e)}", alert=True)
	
	def create_stock_entry_for_operation(self, operation, scans):
		"""Create a single stock entry for an operation"""
		stock_entry_type = self.get_stock_entry_type(operation)
		if not stock_entry_type:
			return None
		
		stock_entry = frappe.new_doc("Stock Entry")
		stock_entry.stock_entry_type = stock_entry_type
		stock_entry.purpose = stock_entry_type
		stock_entry.posting_date = frappe.utils.today()
		stock_entry.posting_time = frappe.utils.nowtime()
		stock_entry.mobile_scan_session = self.name
		
		# Add items
		for scan in scans:
			if operation == "receive":
				stock_entry.append("items", {
					"item_code": scan.item_code,
					"qty": scan.quantity,
					"t_warehouse": scan.warehouse or self.warehouse,
					"basic_rate": scan.rate or 0,
					"barcode": scan.barcode
				})
			elif operation == "issue":
				stock_entry.append("items", {
					"item_code": scan.item_code,
					"qty": scan.quantity,
					"s_warehouse": scan.warehouse or self.warehouse,
					"barcode": scan.barcode
				})
			elif operation == "adjust":
				# For adjustments, we need current stock to calculate difference
				current_qty = frappe.db.get_value("Bin", {
					"item_code": scan.item_code,
					"warehouse": scan.warehouse or self.warehouse
				}, "actual_qty") or 0
				
				diff_qty = scan.quantity - current_qty
				if diff_qty > 0:
					stock_entry.append("items", {
						"item_code": scan.item_code,
						"qty": abs(diff_qty),
						"t_warehouse": scan.warehouse or self.warehouse,
						"barcode": scan.barcode
					})
				elif diff_qty < 0:
					stock_entry.append("items", {
						"item_code": scan.item_code,
						"qty": abs(diff_qty),
						"s_warehouse": scan.warehouse or self.warehouse,
						"barcode": scan.barcode
					})
		
		if stock_entry.items:
			stock_entry.insert()
			return stock_entry
		
		return None
	
	def get_stock_entry_type(self, operation):
		"""Get appropriate stock entry type for operation"""
		mapping = {
			"receive": "Material Receipt",
			"issue": "Material Issue",
			"adjust": "Material Transfer"
		}
		return mapping.get(operation)
	
	def create_stock_reconciliation(self):
		"""Create stock reconciliation for stock take/cycle count"""
		if not self.scans:
			return
		
		stock_recon = frappe.new_doc("Stock Reconciliation")
		stock_recon.purpose = "Stock Reconciliation"
		stock_recon.posting_date = frappe.utils.today()
		stock_recon.posting_time = frappe.utils.nowtime()
		stock_recon.mobile_scan_session = self.name
		
		# Add items
		for scan in scans:
			current_qty = frappe.db.get_value("Bin", {
				"item_code": scan.item_code,
				"warehouse": scan.warehouse or self.warehouse
			}, "actual_qty") or 0
			
			# Only add if there's a difference
			if scan.quantity != current_qty:
				stock_recon.append("items", {
					"item_code": scan.item_code,
					"warehouse": scan.warehouse or self.warehouse,
					"current_qty": current_qty,
					"qty": scan.quantity,
					"barcode": scan.barcode
				})
		
		if stock_recon.items:
			stock_recon.insert()
			frappe.msgprint(f"Stock Reconciliation {stock_recon.name} created")
			return stock_recon
		
		return None
	
	@frappe.whitelist()
	def complete_session(self):
		"""Complete the scanning session"""
		self.status = "Completed"
		self.end_time = frappe.utils.now()
		self.sync_status = "Synced"
		self.save()
		
		return {
			"success": True,
			"message": "Session completed successfully"
		}
	
	@frappe.whitelist()
	def add_scan(self, scan_data):
		"""Add a new scan to the session"""
		if self.status != "Active":
			frappe.throw("Cannot add scans to inactive session")
		
		self.append("scans", scan_data)
		self.save()
		
		return {
			"success": True,
			"scan_count": len(self.scans)
		}
