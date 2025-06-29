# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from enum import Enum
from dataclasses import dataclass, asdict

import frappe
from frappe import _
from frappe.utils import now_datetime, get_datetime, flt, cint


class TransactionType(Enum):
    """Types of migration transactions"""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LINK = "link"
    UNLINK = "unlink"


class TransactionStatus(Enum):
    """Transaction execution status"""

    PENDING = "pending"
    EXECUTED = "executed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class TransactionRecord:
    """Individual transaction record"""

    transaction_id: str
    transaction_type: TransactionType
    doctype: str
    document_name: str
    field_name: Optional[str] = None
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    parent_transaction: Optional[str] = None
    child_transactions: List[str] = None
    status: TransactionStatus = TransactionStatus.PENDING
    timestamp: datetime = None
    error_message: Optional[str] = None
    rollback_timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = now_datetime()
        if self.child_transactions is None:
            self.child_transactions = []
        if self.metadata is None:
            self.metadata = {}


class TransactionManager:
    """Manages migration transactions and rollback operations"""

    def __init__(self, migration_job):
        self.migration_job = migration_job
        self.transactions: Dict[str, TransactionRecord] = {}
        self.execution_order: List[str] = []
        self.rollback_points: List[str] = []
        self.current_batch: Optional[str] = None
        self.batch_transactions: Dict[str, List[str]] = {}

    def create_transaction(
        self,
        transaction_type: TransactionType,
        doctype: str,
        document_name: str,
        field_name: Optional[str] = None,
        old_value: Optional[Any] = None,
        new_value: Optional[Any] = None,
        parent_transaction: Optional[str] = None,
    ) -> str:
        """Create a new transaction record"""

        # Generate unique transaction ID
        transaction_id = (
            f"{transaction_type.value}_{doctype}_{document_name}_{int(time.time() * 1000000)}"
        )

        transaction = TransactionRecord(
            transaction_id=transaction_id,
            transaction_type=transaction_type,
            doctype=doctype,
            document_name=document_name,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            parent_transaction=parent_transaction,
        )

        # Store transaction
        self.transactions[transaction_id] = transaction
        self.execution_order.append(transaction_id)

        # Add to current batch if active
        if self.current_batch:
            if self.current_batch not in self.batch_transactions:
                self.batch_transactions[self.current_batch] = []
            self.batch_transactions[self.current_batch].append(transaction_id)

        # Link to parent transaction
        if parent_transaction and parent_transaction in self.transactions:
            self.transactions[parent_transaction].child_transactions.append(transaction_id)

        return transaction_id

    def start_batch(self, batch_name: str) -> str:
        """Start a new transaction batch"""
        batch_id = f"batch_{batch_name}_{int(time.time())}"
        self.current_batch = batch_id
        self.batch_transactions[batch_id] = []
        return batch_id

    def end_batch(self) -> Optional[str]:
        """End current transaction batch"""
        if self.current_batch:
            batch_id = self.current_batch
            self.current_batch = None
            return batch_id
        return None

    def create_rollback_point(self, point_name: str) -> str:
        """Create a rollback point"""
        rollback_point_id = f"rollback_{point_name}_{int(time.time())}"
        self.rollback_points.append(rollback_point_id)

        # Store current state
        self._save_rollback_point(rollback_point_id)

        return rollback_point_id

    def execute_transaction(self, transaction_id: str) -> bool:
        """Execute a specific transaction"""
        if transaction_id not in self.transactions:
            raise ValueError(f"Transaction {transaction_id} not found")

        transaction = self.transactions[transaction_id]

        try:
            if transaction.transaction_type == TransactionType.CREATE:
                self._execute_create(transaction)
            elif transaction.transaction_type == TransactionType.UPDATE:
                self._execute_update(transaction)
            elif transaction.transaction_type == TransactionType.DELETE:
                self._execute_delete(transaction)
            elif transaction.transaction_type == TransactionType.LINK:
                self._execute_link(transaction)
            elif transaction.transaction_type == TransactionType.UNLINK:
                self._execute_unlink(transaction)

            transaction.status = TransactionStatus.EXECUTED
            self._log_transaction(transaction)
            return True

        except Exception as e:
            transaction.status = TransactionStatus.FAILED
            transaction.error_message = str(e)
            self._log_transaction(transaction)
            frappe.log_error(
                f"Transaction execution failed: {str(e)}", "Transaction Execution Error"
            )
            return False

    def _execute_create(self, transaction: TransactionRecord):
        """Execute document creation"""
        # Check if document already exists
        if frappe.db.exists(transaction.doctype, transaction.document_name):
            raise ValueError(
                f"Document {transaction.doctype} {transaction.document_name} already exists"
            )

        # Get document data from new_value
        if not transaction.new_value or not isinstance(transaction.new_value, dict):
            raise ValueError("Document data is required for creation")

        # Create document
        doc = frappe.new_doc(transaction.doctype)
        doc.update(transaction.new_value)

        # Set name if provided
        if transaction.document_name and transaction.document_name != "new":
            doc.name = transaction.document_name

        doc.insert()

        # Update transaction with actual document name
        transaction.document_name = doc.name
        transaction.metadata["actual_name"] = doc.name

    def _execute_update(self, transaction: TransactionRecord):
        """Execute document update"""
        # Get existing document
        if not frappe.db.exists(transaction.doctype, transaction.document_name):
            raise ValueError(
                f"Document {transaction.doctype} {transaction.document_name} not found"
            )

        doc = frappe.get_doc(transaction.doctype, transaction.document_name)

        # Store original value for rollback
        if transaction.field_name:
            transaction.old_value = getattr(doc, transaction.field_name, None)
            setattr(doc, transaction.field_name, transaction.new_value)
        else:
            # Full document update
            transaction.old_value = doc.as_dict()
            if isinstance(transaction.new_value, dict):
                doc.update(transaction.new_value)

        doc.save()
        transaction.metadata["updated_fields"] = (
            list(transaction.new_value.keys())
            if isinstance(transaction.new_value, dict)
            else [transaction.field_name]
        )

    def _execute_delete(self, transaction: TransactionRecord):
        """Execute document deletion"""
        # Get document before deletion for rollback
        if not frappe.db.exists(transaction.doctype, transaction.document_name):
            raise ValueError(
                f"Document {transaction.doctype} {transaction.document_name} not found"
            )

        doc = frappe.get_doc(transaction.doctype, transaction.document_name)
        transaction.old_value = doc.as_dict()

        # Delete document
        doc.delete()
        transaction.metadata["deleted_at"] = now_datetime()

    def _execute_link(self, transaction: TransactionRecord):
        """Execute document linking"""
        # Link implementation would depend on specific field types
        # This is a placeholder for complex linking operations
        if not transaction.field_name:
            raise ValueError("Field name is required for linking operations")

        if not frappe.db.exists(transaction.doctype, transaction.document_name):
            raise ValueError(
                f"Document {transaction.doctype} {transaction.document_name} not found"
            )

        doc = frappe.get_doc(transaction.doctype, transaction.document_name)
        transaction.old_value = getattr(doc, transaction.field_name, None)
        setattr(doc, transaction.field_name, transaction.new_value)
        doc.save()

    def _execute_unlink(self, transaction: TransactionRecord):
        """Execute document unlinking"""
        # Unlink implementation
        if not transaction.field_name:
            raise ValueError("Field name is required for unlinking operations")

        if not frappe.db.exists(transaction.doctype, transaction.document_name):
            raise ValueError(
                f"Document {transaction.doctype} {transaction.document_name} not found"
            )

        doc = frappe.get_doc(transaction.doctype, transaction.document_name)
        transaction.old_value = getattr(doc, transaction.field_name, None)
        setattr(doc, transaction.field_name, None)
        doc.save()

    def rollback_transaction(self, transaction_id: str) -> bool:
        """Rollback a specific transaction"""
        if transaction_id not in self.transactions:
            raise ValueError(f"Transaction {transaction_id} not found")

        transaction = self.transactions[transaction_id]

        if transaction.status != TransactionStatus.EXECUTED:
            raise ValueError(f"Transaction {transaction_id} is not in executed state")

        try:
            if transaction.transaction_type == TransactionType.CREATE:
                self._rollback_create(transaction)
            elif transaction.transaction_type == TransactionType.UPDATE:
                self._rollback_update(transaction)
            elif transaction.transaction_type == TransactionType.DELETE:
                self._rollback_delete(transaction)
            elif transaction.transaction_type == TransactionType.LINK:
                self._rollback_link(transaction)
            elif transaction.transaction_type == TransactionType.UNLINK:
                self._rollback_unlink(transaction)

            transaction.status = TransactionStatus.ROLLED_BACK
            transaction.rollback_timestamp = now_datetime()
            self._log_transaction(transaction)
            return True

        except Exception as e:
            transaction.error_message = f"Rollback failed: {str(e)}"
            self._log_transaction(transaction)
            frappe.log_error(f"Transaction rollback failed: {str(e)}", "Transaction Rollback Error")
            return False

    def _rollback_create(self, transaction: TransactionRecord):
        """Rollback document creation (delete the created document)"""
        if frappe.db.exists(transaction.doctype, transaction.document_name):
            doc = frappe.get_doc(transaction.doctype, transaction.document_name)
            doc.delete()

    def _rollback_update(self, transaction: TransactionRecord):
        """Rollback document update (restore original values)"""
        if not frappe.db.exists(transaction.doctype, transaction.document_name):
            raise ValueError(
                f"Document {transaction.doctype} {transaction.document_name} not found for rollback"
            )

        doc = frappe.get_doc(transaction.doctype, transaction.document_name)

        if transaction.field_name:
            # Restore single field
            setattr(doc, transaction.field_name, transaction.old_value)
        else:
            # Restore full document
            if isinstance(transaction.old_value, dict):
                # Clear current fields and restore old values
                for field, value in transaction.old_value.items():
                    if hasattr(doc, field):
                        setattr(doc, field, value)

        doc.save()

    def _rollback_delete(self, transaction: TransactionRecord):
        """Rollback document deletion (recreate the document)"""
        if transaction.old_value and isinstance(transaction.old_value, dict):
            doc = frappe.new_doc(transaction.doctype)
            doc.update(transaction.old_value)
            doc.insert()

    def _rollback_link(self, transaction: TransactionRecord):
        """Rollback document linking (restore original link)"""
        if not frappe.db.exists(transaction.doctype, transaction.document_name):
            raise ValueError(
                f"Document {transaction.doctype} {transaction.document_name} not found for rollback"
            )

        doc = frappe.get_doc(transaction.doctype, transaction.document_name)
        setattr(doc, transaction.field_name, transaction.old_value)
        doc.save()

    def _rollback_unlink(self, transaction: TransactionRecord):
        """Rollback document unlinking (restore original link)"""
        if not frappe.db.exists(transaction.doctype, transaction.document_name):
            raise ValueError(
                f"Document {transaction.doctype} {transaction.document_name} not found for rollback"
            )

        doc = frappe.get_doc(transaction.doctype, transaction.document_name)
        setattr(doc, transaction.field_name, transaction.old_value)
        doc.save()

    def rollback_batch(self, batch_id: str) -> Dict[str, bool]:
        """Rollback all transactions in a batch"""
        if batch_id not in self.batch_transactions:
            raise ValueError(f"Batch {batch_id} not found")

        results = {}
        transaction_ids = self.batch_transactions[batch_id]

        # Rollback in reverse order
        for transaction_id in reversed(transaction_ids):
            results[transaction_id] = self.rollback_transaction(transaction_id)

        return results

    def rollback_to_point(self, rollback_point_id: str) -> Dict[str, bool]:
        """Rollback all transactions after a specific rollback point"""
        if rollback_point_id not in self.rollback_points:
            raise ValueError(f"Rollback point {rollback_point_id} not found")

        # Find point index
        point_index = self.rollback_points.index(rollback_point_id)

        # Get all transactions after this point
        transactions_to_rollback = []
        for transaction_id in reversed(self.execution_order):
            transaction = self.transactions[transaction_id]
            if transaction.timestamp > self._get_rollback_point_timestamp(rollback_point_id):
                transactions_to_rollback.append(transaction_id)

        # Rollback transactions
        results = {}
        for transaction_id in transactions_to_rollback:
            results[transaction_id] = self.rollback_transaction(transaction_id)

        return results

    def rollback_all(self) -> Dict[str, bool]:
        """Rollback all executed transactions"""
        results = {}

        # Rollback in reverse execution order
        for transaction_id in reversed(self.execution_order):
            transaction = self.transactions[transaction_id]
            if transaction.status == TransactionStatus.EXECUTED:
                results[transaction_id] = self.rollback_transaction(transaction_id)

        return results

    def get_transaction_summary(self) -> Dict:
        """Get summary of all transactions"""
        summary = {
            "total_transactions": len(self.transactions),
            "by_status": {},
            "by_type": {},
            "by_doctype": {},
            "execution_time_range": {},
            "rollback_points_count": len(self.rollback_points),
            "batch_count": len(self.batch_transactions),
        }

        # Count by status
        for status in TransactionStatus:
            summary["by_status"][status.value] = 0

        # Count by type
        for transaction_type in TransactionType:
            summary["by_type"][transaction_type.value] = 0

        # Process transactions
        earliest_time = None
        latest_time = None

        for transaction in self.transactions.values():
            # Status count
            summary["by_status"][transaction.status.value] += 1

            # Type count
            summary["by_type"][transaction.transaction_type.value] += 1

            # DocType count
            if transaction.doctype not in summary["by_doctype"]:
                summary["by_doctype"][transaction.doctype] = 0
            summary["by_doctype"][transaction.doctype] += 1

            # Time range
            if earliest_time is None or transaction.timestamp < earliest_time:
                earliest_time = transaction.timestamp
            if latest_time is None or transaction.timestamp > latest_time:
                latest_time = transaction.timestamp

        if earliest_time and latest_time:
            summary["execution_time_range"] = {
                "start": earliest_time.isoformat(),
                "end": latest_time.isoformat(),
                "duration_seconds": (latest_time - earliest_time).total_seconds(),
            }

        return summary

    def export_transaction_log(self) -> Dict:
        """Export complete transaction log for persistence"""
        log_data = {
            "migration_job": self.migration_job.name,
            "export_timestamp": now_datetime().isoformat(),
            "transactions": {},
            "execution_order": self.execution_order,
            "rollback_points": self.rollback_points,
            "batch_transactions": self.batch_transactions,
            "summary": self.get_transaction_summary(),
        }

        # Convert transactions to serializable format
        for transaction_id, transaction in self.transactions.items():
            log_data["transactions"][transaction_id] = {
                "transaction_id": transaction.transaction_id,
                "transaction_type": transaction.transaction_type.value,
                "doctype": transaction.doctype,
                "document_name": transaction.document_name,
                "field_name": transaction.field_name,
                "old_value": self._serialize_value(transaction.old_value),
                "new_value": self._serialize_value(transaction.new_value),
                "parent_transaction": transaction.parent_transaction,
                "child_transactions": transaction.child_transactions,
                "status": transaction.status.value,
                "timestamp": transaction.timestamp.isoformat(),
                "error_message": transaction.error_message,
                "rollback_timestamp": (
                    transaction.rollback_timestamp.isoformat()
                    if transaction.rollback_timestamp
                    else None
                ),
                "metadata": transaction.metadata,
            }

        return log_data

    def import_transaction_log(self, log_data: Dict):
        """Import transaction log from persistent storage"""
        # Clear current state
        self.transactions.clear()
        self.execution_order.clear()
        self.rollback_points.clear()
        self.batch_transactions.clear()

        # Restore state
        self.execution_order = log_data.get("execution_order", [])
        self.rollback_points = log_data.get("rollback_points", [])
        self.batch_transactions = log_data.get("batch_transactions", {})

        # Restore transactions
        for transaction_id, transaction_data in log_data.get("transactions", {}).items():
            transaction = TransactionRecord(
                transaction_id=transaction_data["transaction_id"],
                transaction_type=TransactionType(transaction_data["transaction_type"]),
                doctype=transaction_data["doctype"],
                document_name=transaction_data["document_name"],
                field_name=transaction_data.get("field_name"),
                old_value=self._deserialize_value(transaction_data.get("old_value")),
                new_value=self._deserialize_value(transaction_data.get("new_value")),
                parent_transaction=transaction_data.get("parent_transaction"),
                child_transactions=transaction_data.get("child_transactions", []),
                status=TransactionStatus(transaction_data["status"]),
                timestamp=get_datetime(transaction_data["timestamp"]),
                error_message=transaction_data.get("error_message"),
                rollback_timestamp=(
                    get_datetime(transaction_data["rollback_timestamp"])
                    if transaction_data.get("rollback_timestamp")
                    else None
                ),
                metadata=transaction_data.get("metadata", {}),
            )

            self.transactions[transaction_id] = transaction

    def _serialize_value(self, value: Any) -> Any:
        """Serialize value for JSON storage"""
        if isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._serialize_value(item) for item in value]
        else:
            return value

    def _deserialize_value(self, value: Any) -> Any:
        """Deserialize value from JSON storage"""
        if isinstance(value, str):
            # Try to parse as datetime
            try:
                return get_datetime(value)
            except Exception:
                return value
        elif isinstance(value, dict):
            return {k: self._deserialize_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._deserialize_value(item) for item in value]
        else:
            return value

    def _log_transaction(self, transaction: TransactionRecord):
        """Log transaction to migration job"""
        if hasattr(self.migration_job, "log_transaction"):
            self.migration_job.log_transaction(
                action=transaction.transaction_type.value,
                doctype=transaction.doctype,
                record_name=transaction.document_name,
                data={
                    "transaction_id": transaction.transaction_id,
                    "field_name": transaction.field_name,
                    "old_value": transaction.old_value,
                    "new_value": transaction.new_value,
                    "status": transaction.status.value,
                    "timestamp": transaction.timestamp.isoformat(),
                    "metadata": transaction.metadata,
                },
            )

    def _save_rollback_point(self, rollback_point_id: str):
        """Save rollback point state"""
        # This would typically save to database or file
        # For now, just store in memory
        pass

    def _get_rollback_point_timestamp(self, rollback_point_id: str) -> datetime:
        """Get timestamp of rollback point"""
        # Extract timestamp from rollback point ID
        # This is a simplified implementation
        timestamp_str = rollback_point_id.split("_")[-1]
        return datetime.fromtimestamp(int(timestamp_str))


class RollbackManager:
    """Specialized manager for rollback operations"""

    def __init__(self, migration_job):
        self.migration_job = migration_job
        self.transaction_manager = TransactionManager(migration_job)

        # Load existing transaction log if available
        if hasattr(migration_job, "transaction_log") and migration_job.transaction_log:
            try:
                log_data = json.loads(migration_job.transaction_log)
                self.transaction_manager.import_transaction_log(log_data)
            except Exception as e:
                frappe.log_error(
                    f"Failed to load transaction log: {str(e)}", "Rollback Manager Error"
                )

    def validate_rollback_feasibility(self, transaction_id: str) -> Dict:
        """Validate if rollback is feasible for a transaction"""
        result = {"feasible": True, "warnings": [], "blockers": [], "dependencies": []}

        if transaction_id not in self.transaction_manager.transactions:
            result["feasible"] = False
            result["blockers"].append(f"Transaction {transaction_id} not found")
            return result

        transaction = self.transaction_manager.transactions[transaction_id]

        # Check transaction status
        if transaction.status != TransactionStatus.EXECUTED:
            result["feasible"] = False
            result["blockers"].append(
                f"Transaction is not in executed state: {transaction.status.value}"
            )
            return result

        # Check if document still exists (for updates/deletes)
        if transaction.transaction_type in [TransactionType.UPDATE, TransactionType.DELETE]:
            if not frappe.db.exists(transaction.doctype, transaction.document_name):
                result["feasible"] = False
                result["blockers"].append(
                    f"Document {transaction.doctype} {transaction.document_name} no longer exists"
                )

        # Check if created document still exists (for creates)
        if transaction.transaction_type == TransactionType.CREATE:
            if not frappe.db.exists(transaction.doctype, transaction.document_name):
                result["warnings"].append(
                    f"Created document {transaction.doctype} {transaction.document_name} has been deleted"
                )

        # Check for dependent transactions
        dependent_transactions = self._find_dependent_transactions(transaction_id)
        if dependent_transactions:
            result["dependencies"] = dependent_transactions
            result["warnings"].append(f"Found {len(dependent_transactions)} dependent transactions")

        return result

    def _find_dependent_transactions(self, transaction_id: str) -> List[str]:
        """Find transactions that depend on the given transaction"""
        dependent = []
        target_transaction = self.transaction_manager.transactions[transaction_id]

        for tid, transaction in self.transaction_manager.transactions.items():
            if tid == transaction_id:
                continue

            # Check if this transaction operates on the same document after the target
            if (
                transaction.doctype == target_transaction.doctype
                and transaction.document_name == target_transaction.document_name
                and transaction.timestamp > target_transaction.timestamp
                and transaction.status == TransactionStatus.EXECUTED
            ):
                dependent.append(tid)

        return dependent

    def create_rollback_plan(self, target: str, rollback_type: str = "transaction") -> Dict:
        """Create a comprehensive rollback plan"""
        plan = {
            "rollback_type": rollback_type,
            "target": target,
            "transactions_to_rollback": [],
            "execution_order": [],
            "estimated_time": 0,
            "risks": [],
            "prerequisites": [],
        }

        if rollback_type == "transaction":
            plan["transactions_to_rollback"] = [target]
            # Add dependent transactions
            dependent = self._find_dependent_transactions(target)
            plan["transactions_to_rollback"].extend(dependent)

        elif rollback_type == "batch":
            if target in self.transaction_manager.batch_transactions:
                plan["transactions_to_rollback"] = self.transaction_manager.batch_transactions[
                    target
                ]

        elif rollback_type == "rollback_point":
            # Get all transactions after rollback point
            for transaction_id in reversed(self.transaction_manager.execution_order):
                transaction = self.transaction_manager.transactions[transaction_id]
                if transaction.timestamp > self.transaction_manager._get_rollback_point_timestamp(
                    target
                ):
                    plan["transactions_to_rollback"].append(transaction_id)

        # Set execution order (reverse chronological)
        plan["execution_order"] = list(reversed(plan["transactions_to_rollback"]))

        # Estimate time (rough calculation)
        plan["estimated_time"] = (
            len(plan["transactions_to_rollback"]) * 2
        )  # 2 seconds per transaction

        # Assess risks
        for transaction_id in plan["transactions_to_rollback"]:
            feasibility = self.validate_rollback_feasibility(transaction_id)
            if not feasibility["feasible"]:
                plan["risks"].extend(feasibility["blockers"])
            plan["risks"].extend(feasibility["warnings"])

        return plan

    def execute_rollback_plan(self, plan: Dict) -> Dict:
        """Execute a rollback plan"""
        results = {
            "plan": plan,
            "start_time": now_datetime(),
            "end_time": None,
            "success": True,
            "transaction_results": {},
            "errors": [],
            "summary": {},
        }

        try:
            for transaction_id in plan["execution_order"]:
                try:
                    success = self.transaction_manager.rollback_transaction(transaction_id)
                    results["transaction_results"][transaction_id] = {
                        "success": success,
                        "timestamp": now_datetime(),
                    }

                    if not success:
                        results["success"] = False
                        results["errors"].append(f"Failed to rollback transaction {transaction_id}")

                except Exception as e:
                    results["success"] = False
                    results["errors"].append(
                        f"Error rolling back transaction {transaction_id}: {str(e)}"
                    )
                    results["transaction_results"][transaction_id] = {
                        "success": False,
                        "error": str(e),
                        "timestamp": now_datetime(),
                    }

            results["end_time"] = now_datetime()
            results["summary"] = {
                "total_transactions": len(plan["transactions_to_rollback"]),
                "successful_rollbacks": sum(
                    1 for r in results["transaction_results"].values() if r["success"]
                ),
                "failed_rollbacks": sum(
                    1 for r in results["transaction_results"].values() if not r["success"]
                ),
                "duration_seconds": (results["end_time"] - results["start_time"]).total_seconds(),
            }

        except Exception as e:
            results["success"] = False
            results["errors"].append(f"Critical error during rollback execution: {str(e)}")
            results["end_time"] = now_datetime()

        return results
