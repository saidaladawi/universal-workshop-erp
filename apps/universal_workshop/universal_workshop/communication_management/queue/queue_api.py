import frappe
from frappe import _
from typing import Dict, List, Any, Optional
from .redis_queue_manager import get_queue_manager, QueueType, Priority
from .message_worker import get_communication_worker


@frappe.whitelist()
def get_queue_statistics(queue_type: str = None) -> Dict[str, Any]:
    """
    Get queue statistics for monitoring.
    
    Args:
        queue_type: Optional specific queue type (sms_queue, whatsapp_queue, etc.)
        
    Returns:
        Dict with queue statistics
    """
    try:
        queue_manager = get_queue_manager()
        
        # Convert string to enum if provided
        queue_enum = None
        if queue_type:
            queue_map = {
                "sms_queue": QueueType.SMS,
                "whatsapp_queue": QueueType.WHATSAPP,
                "email_queue": QueueType.EMAIL,
                "bulk_queue": QueueType.BULK
            }
            queue_enum = queue_map.get(queue_type.lower())
        
        # Get statistics
        stats = queue_manager.get_queue_stats(queue_enum)
        
        return {
            "success": True,
            "statistics": stats,
            "timestamp": frappe.utils.now_datetime().isoformat()
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting queue statistics: {e}", "QueueAPI")
        return {
            "success": False,
            "error": str(e),
            "message": _("Failed to retrieve queue statistics")
        }


@frappe.whitelist()
def get_dead_letter_messages(limit: int = 50) -> Dict[str, Any]:
    """
    Get messages from dead letter queue for manual review.
    
    Args:
        limit: Maximum number of messages to retrieve
        
    Returns:
        Dict with dead letter messages
    """
    try:
        queue_manager = get_queue_manager()
        
        # Get dead letter messages
        messages = queue_manager.get_dead_letter_messages(limit)
        
        return {
            "success": True,
            "messages": messages,
            "count": len(messages),
            "timestamp": frappe.utils.now_datetime().isoformat()
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting dead letter messages: {e}", "QueueAPI")
        return {
            "success": False,
            "error": str(e),
            "message": _("Failed to retrieve dead letter messages")
        }
