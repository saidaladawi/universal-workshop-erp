# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import json
from typing import Dict, List, Optional

import frappe
from frappe import _
from frappe.utils import now_datetime

from universal_workshop.data_migration.transaction_manager import (
    TransactionManager, RollbackManager, TransactionType, TransactionStatus
)


@frappe.whitelist()
def get_migration_transactions(migration_job_id: str) -> Dict:
    """Get all transactions for a migration job"""
    try:
        migration_job = frappe.get_doc('Migration Job', migration_job_id)
        transaction_manager = TransactionManager(migration_job)
        
        # Load existing transaction log
        if migration_job.transaction_log:
            log_data = json.loads(migration_job.transaction_log)
            transaction_manager.import_transaction_log(log_data)
        
        return transaction_manager.get_transaction_summary()
        
    except Exception as e:
        frappe.throw(_("Failed to get migration transactions: {0}").format(str(e)))


@frappe.whitelist()
def get_transaction_details(migration_job_id: str, transaction_id: str) -> Dict:
    """Get detailed information about a specific transaction"""
    try:
        migration_job = frappe.get_doc('Migration Job', migration_job_id)
        transaction_manager = TransactionManager(migration_job)
        
        # Load existing transaction log
        if migration_job.transaction_log:
            log_data = json.loads(migration_job.transaction_log)
            transaction_manager.import_transaction_log(log_data)
        
        if transaction_id not in transaction_manager.transactions:
            frappe.throw(_("Transaction {0} not found").format(transaction_id))
        
        transaction = transaction_manager.transactions[transaction_id]
        
        return {
            'transaction_id': transaction.transaction_id,
            'transaction_type': transaction.transaction_type.value,
            'doctype': transaction.doctype,
            'document_name': transaction.document_name,
            'field_name': transaction.field_name,
            'old_value': transaction.old_value,
            'new_value': transaction.new_value,
            'parent_transaction': transaction.parent_transaction,
            'child_transactions': transaction.child_transactions,
            'status': transaction.status.value,
            'timestamp': transaction.timestamp.isoformat() if transaction.timestamp else None,
            'error_message': transaction.error_message,
            'rollback_timestamp': transaction.rollback_timestamp.isoformat() if transaction.rollback_timestamp else None,
            'metadata': transaction.metadata
        }
        
    except Exception as e:
        frappe.throw(_("Failed to get transaction details: {0}").format(str(e)))


@frappe.whitelist()
def validate_rollback_feasibility(migration_job_id: str, transaction_id: str) -> Dict:
    """Validate if rollback is feasible for a transaction"""
    try:
        migration_job = frappe.get_doc('Migration Job', migration_job_id)
        rollback_manager = RollbackManager(migration_job)
        
        return rollback_manager.validate_rollback_feasibility(transaction_id)
        
    except Exception as e:
        frappe.throw(_("Failed to validate rollback feasibility: {0}").format(str(e)))


@frappe.whitelist()
def create_rollback_plan(
    migration_job_id: str, 
    target: str, 
    rollback_type: str = 'transaction'
) -> Dict:
    """Create a rollback plan"""
    try:
        migration_job = frappe.get_doc('Migration Job', migration_job_id)
        rollback_manager = RollbackManager(migration_job)
        
        valid_types = ['transaction', 'batch', 'rollback_point', 'all']
        if rollback_type not in valid_types:
            frappe.throw(_("Invalid rollback type. Must be one of: {0}").format(', '.join(valid_types)))
        
        plan = rollback_manager.create_rollback_plan(target, rollback_type)
        
        # Add Arabic translations for plan elements
        plan['rollback_type_ar'] = _get_rollback_type_arabic(rollback_type)
        plan['status_message'] = _("Rollback plan created successfully")
        plan['status_message_ar'] = "تم إنشاء خطة التراجع بنجاح"
        
        return plan
        
    except Exception as e:
        frappe.throw(_("Failed to create rollback plan: {0}").format(str(e)))


@frappe.whitelist()
def execute_rollback(migration_job_id: str, plan: str) -> Dict:
    """Execute a rollback plan"""
    try:
        migration_job = frappe.get_doc('Migration Job', migration_job_id)
        rollback_manager = RollbackManager(migration_job)
        
        # Parse plan if it's a string
        if isinstance(plan, str):
            plan = json.loads(plan)
        
        results = rollback_manager.execute_rollback_plan(plan)
        
        # Update migration job with rollback results
        migration_job.add_comment(
            'Comment',
            _("Rollback executed: {0} transactions processed, {1} successful").format(
                results['summary'].get('total_transactions', 0),
                results['summary'].get('successful_rollbacks', 0)
            )
        )
        
        # Add Arabic status messages
        if results['success']:
            results['status_message'] = _("Rollback completed successfully")
            results['status_message_ar'] = "تم التراجع بنجاح"
        else:
            results['status_message'] = _("Rollback completed with errors")
            results['status_message_ar'] = "تم التراجع مع وجود أخطاء"
        
        return results
        
    except Exception as e:
        frappe.throw(_("Failed to execute rollback: {0}").format(str(e)))


@frappe.whitelist()
def rollback_single_transaction(migration_job_id: str, transaction_id: str) -> Dict:
    """Rollback a single transaction"""
    try:
        migration_job = frappe.get_doc('Migration Job', migration_job_id)
        transaction_manager = TransactionManager(migration_job)
        
        # Load existing transaction log
        if migration_job.transaction_log:
            log_data = json.loads(migration_job.transaction_log)
            transaction_manager.import_transaction_log(log_data)
        
        # Validate feasibility first
        rollback_manager = RollbackManager(migration_job)
        feasibility = rollback_manager.validate_rollback_feasibility(transaction_id)
        
        if not feasibility['feasible']:
            return {
                'success': False,
                'error': _("Rollback not feasible: {0}").format('; '.join(feasibility['blockers'])),
                'error_ar': "التراجع غير ممكن: " + '; '.join(feasibility['blockers']),
                'feasibility': feasibility
            }
        
        # Execute rollback
        success = transaction_manager.rollback_transaction(transaction_id)
        
        if success:
            # Save updated transaction log
            log_data = transaction_manager.export_transaction_log()
            migration_job.transaction_log = json.dumps(log_data)
            migration_job.save()
            
            return {
                'success': True,
                'message': _("Transaction {0} rolled back successfully").format(transaction_id),
                'message_ar': f"تم التراجع عن المعاملة {transaction_id} بنجاح",
                'transaction_id': transaction_id,
                'rollback_timestamp': now_datetime().isoformat()
            }
        else:
            return {
                'success': False,
                'error': _("Failed to rollback transaction {0}").format(transaction_id),
                'error_ar': f"فشل في التراجع عن المعاملة {transaction_id}",
                'transaction_id': transaction_id
            }
        
    except Exception as e:
        frappe.throw(_("Failed to rollback transaction: {0}").format(str(e)))


@frappe.whitelist()
def rollback_batch(migration_job_id: str, batch_id: str) -> Dict:
    """Rollback all transactions in a batch"""
    try:
        migration_job = frappe.get_doc('Migration Job', migration_job_id)
        transaction_manager = TransactionManager(migration_job)
        
        # Load existing transaction log
        if migration_job.transaction_log:
            log_data = json.loads(migration_job.transaction_log)
            transaction_manager.import_transaction_log(log_data)
        
        results = transaction_manager.rollback_batch(batch_id)
        
        # Save updated transaction log
        log_data = transaction_manager.export_transaction_log()
        migration_job.transaction_log = json.dumps(log_data)
        migration_job.save()
        
        # Calculate summary
        successful_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        return {
            'success': successful_count == total_count,
            'batch_id': batch_id,
            'total_transactions': total_count,
            'successful_rollbacks': successful_count,
            'failed_rollbacks': total_count - successful_count,
            'transaction_results': results,
            'message': _("Batch rollback completed: {0}/{1} transactions successful").format(
                successful_count, total_count),
            'message_ar': f"تم التراجع الجماعي: {successful_count}/{total_count} معاملة نجحت"
        }
        
    except Exception as e:
        frappe.throw(_("Failed to rollback batch: {0}").format(str(e)))


@frappe.whitelist()
def rollback_to_point(migration_job_id: str, rollback_point_id: str) -> Dict:
    """Rollback to a specific rollback point"""
    try:
        migration_job = frappe.get_doc('Migration Job', migration_job_id)
        transaction_manager = TransactionManager(migration_job)
        
        # Load existing transaction log
        if migration_job.transaction_log:
            log_data = json.loads(migration_job.transaction_log)
            transaction_manager.import_transaction_log(log_data)
        
        results = transaction_manager.rollback_to_point(rollback_point_id)
        
        # Save updated transaction log
        log_data = transaction_manager.export_transaction_log()
        migration_job.transaction_log = json.dumps(log_data)
        migration_job.save()
        
        # Calculate summary
        successful_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        return {
            'success': successful_count == total_count,
            'rollback_point_id': rollback_point_id,
            'total_transactions': total_count,
            'successful_rollbacks': successful_count,
            'failed_rollbacks': total_count - successful_count,
            'transaction_results': results,
            'message': _("Rollback to point completed: {0}/{1} transactions successful").format(
                successful_count, total_count),
            'message_ar': f"تم التراجع إلى النقطة: {successful_count}/{total_count} معاملة نجحت"
        }
        
    except Exception as e:
        frappe.throw(_("Failed to rollback to point: {0}").format(str(e)))


@frappe.whitelist()
def rollback_all_transactions(migration_job_id: str) -> Dict:
    """Rollback all transactions for a migration job"""
    try:
        migration_job = frappe.get_doc('Migration Job', migration_job_id)
        transaction_manager = TransactionManager(migration_job)
        
        # Load existing transaction log
        if migration_job.transaction_log:
            log_data = json.loads(migration_job.transaction_log)
            transaction_manager.import_transaction_log(log_data)
        
        results = transaction_manager.rollback_all()
        
        # Save updated transaction log
        log_data = transaction_manager.export_transaction_log()
        migration_job.transaction_log = json.dumps(log_data)
        migration_job.save()
        
        # Update migration job status
        migration_job.status = 'Rolled Back'
        migration_job.save()
        
        # Calculate summary
        successful_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        return {
            'success': successful_count == total_count,
            'migration_job_id': migration_job_id,
            'total_transactions': total_count,
            'successful_rollbacks': successful_count,
            'failed_rollbacks': total_count - successful_count,
            'transaction_results': results,
            'message': _("Complete rollback finished: {0}/{1} transactions successful").format(
                successful_count, total_count),
            'message_ar': f"تم التراجع الكامل: {successful_count}/{total_count} معاملة نجحت"
        }
        
    except Exception as e:
        frappe.throw(_("Failed to rollback all transactions: {0}").format(str(e)))


@frappe.whitelist()
def create_rollback_point(migration_job_id: str, point_name: str) -> str:
    """Create a rollback point"""
    try:
        migration_job = frappe.get_doc('Migration Job', migration_job_id)
        transaction_manager = TransactionManager(migration_job)
        
        # Load existing transaction log
        if migration_job.transaction_log:
            log_data = json.loads(migration_job.transaction_log)
            transaction_manager.import_transaction_log(log_data)
        
        rollback_point_id = transaction_manager.create_rollback_point(point_name)
        
        # Save updated transaction log
        log_data = transaction_manager.export_transaction_log()
        migration_job.transaction_log = json.dumps(log_data)
        migration_job.save()
        
        return rollback_point_id
        
    except Exception as e:
        frappe.throw(_("Failed to create rollback point: {0}").format(str(e)))


@frappe.whitelist()
def get_rollback_points(migration_job_id: str) -> List[Dict]:
    """Get all rollback points for a migration job"""
    try:
        migration_job = frappe.get_doc('Migration Job', migration_job_id)
        transaction_manager = TransactionManager(migration_job)
        
        # Load existing transaction log
        if migration_job.transaction_log:
            log_data = json.loads(migration_job.transaction_log)
            transaction_manager.import_transaction_log(log_data)
        
        rollback_points = []
        for point_id in transaction_manager.rollback_points:
            # Extract information from point ID
            parts = point_id.split('_')
            point_name = '_'.join(parts[1:-1])  # Remove 'rollback' prefix and timestamp suffix
            timestamp = parts[-1]
            
            rollback_points.append({
                'id': point_id,
                'name': point_name,
                'timestamp': int(timestamp),
                'created_date': transaction_manager._get_rollback_point_timestamp(point_id).isoformat()
            })
        
        return rollback_points
        
    except Exception as e:
        frappe.throw(_("Failed to get rollback points: {0}").format(str(e)))


@frappe.whitelist()
def get_transaction_tree(migration_job_id: str) -> Dict:
    """Get transaction hierarchy tree"""
    try:
        migration_job = frappe.get_doc('Migration Job', migration_job_id)
        transaction_manager = TransactionManager(migration_job)
        
        # Load existing transaction log
        if migration_job.transaction_log:
            log_data = json.loads(migration_job.transaction_log)
            transaction_manager.import_transaction_log(log_data)
        
        # Build tree structure
        tree = {
            'root_transactions': [],
            'transaction_details': {}
        }
        
        for transaction_id, transaction in transaction_manager.transactions.items():
            # Build transaction node
            node = {
                'id': transaction.transaction_id,
                'type': transaction.transaction_type.value,
                'doctype': transaction.doctype,
                'document_name': transaction.document_name,
                'status': transaction.status.value,
                'timestamp': transaction.timestamp.isoformat() if transaction.timestamp else None,
                'children': transaction.child_transactions,
                'parent': transaction.parent_transaction
            }
            
            tree['transaction_details'][transaction_id] = node
            
            # Add to root if no parent
            if not transaction.parent_transaction:
                tree['root_transactions'].append(transaction_id)
        
        return tree
        
    except Exception as e:
        frappe.throw(_("Failed to get transaction tree: {0}").format(str(e)))


@frappe.whitelist()
def export_rollback_report(migration_job_id: str, format_type: str = 'json') -> Dict:
    """Export rollback report"""
    try:
        migration_job = frappe.get_doc('Migration Job', migration_job_id)
        transaction_manager = TransactionManager(migration_job)
        
        # Load existing transaction log
        if migration_job.transaction_log:
            log_data = json.loads(migration_job.transaction_log)
            transaction_manager.import_transaction_log(log_data)
        
        report_data = {
            'migration_job': {
                'id': migration_job_id,
                'title': migration_job.job_title,
                'title_ar': migration_job.job_title_ar,
                'status': migration_job.status,
                'created_date': migration_job.created_date.isoformat() if migration_job.created_date else None
            },
            'summary': transaction_manager.get_transaction_summary(),
            'complete_log': transaction_manager.export_transaction_log(),
            'rollback_points': transaction_manager.rollback_points,
            'batch_summary': {
                batch_id: len(transaction_ids) 
                for batch_id, transaction_ids in transaction_manager.batch_transactions.items()
            },
            'export_metadata': {
                'export_date': now_datetime().isoformat(),
                'format': format_type,
                'total_size': len(transaction_manager.transactions)
            }
        }
        
        if format_type == 'json':
            return report_data
        else:
            frappe.throw(_("Unsupported export format: {0}").format(format_type))
        
    except Exception as e:
        frappe.throw(_("Failed to export rollback report: {0}").format(str(e)))


def _get_rollback_type_arabic(rollback_type: str) -> str:
    """Get Arabic translation for rollback type"""
    translations = {
        'transaction': 'معاملة',
        'batch': 'دفعة',
        'rollback_point': 'نقطة التراجع',
        'all': 'الكل'
    }
    return translations.get(rollback_type, rollback_type)


@frappe.whitelist()
def get_rollback_statistics(migration_job_id: str) -> Dict:
    """Get rollback statistics and analytics"""
    try:
        migration_job = frappe.get_doc('Migration Job', migration_job_id)
        transaction_manager = TransactionManager(migration_job)
        
        # Load existing transaction log
        if migration_job.transaction_log:
            log_data = json.loads(migration_job.transaction_log)
            transaction_manager.import_transaction_log(log_data)
        
        stats = {
            'overview': transaction_manager.get_transaction_summary(),
            'rollback_success_rate': 0,
            'most_common_rollback_type': None,
            'rollback_frequency_by_hour': {},
            'average_rollback_time': 0,
            'rollback_impact_analysis': {
                'affected_doctypes': set(),
                'affected_documents': set(),
                'data_recovery_status': {}
            }
        }
        
        # Calculate rollback statistics
        rolled_back_transactions = [
            t for t in transaction_manager.transactions.values() 
            if t.status == TransactionStatus.ROLLED_BACK
        ]
        
        if rolled_back_transactions:
            stats['rollback_success_rate'] = len(rolled_back_transactions) / len(transaction_manager.transactions) * 100
            
            # Rollback type frequency
            type_counts = {}
            for transaction in rolled_back_transactions:
                t_type = transaction.transaction_type.value
                type_counts[t_type] = type_counts.get(t_type, 0) + 1
            
            if type_counts:
                stats['most_common_rollback_type'] = max(type_counts, key=type_counts.get)
            
            # Impact analysis
            for transaction in rolled_back_transactions:
                stats['rollback_impact_analysis']['affected_doctypes'].add(transaction.doctype)
                stats['rollback_impact_analysis']['affected_documents'].add(
                    f"{transaction.doctype}::{transaction.document_name}"
                )
        
        # Convert sets to lists for JSON serialization
        stats['rollback_impact_analysis']['affected_doctypes'] = list(
            stats['rollback_impact_analysis']['affected_doctypes']
        )
        stats['rollback_impact_analysis']['affected_documents'] = list(
            stats['rollback_impact_analysis']['affected_documents']
        )
        
        return stats
        
    except Exception as e:
        frappe.throw(_("Failed to get rollback statistics: {0}").format(str(e))) 