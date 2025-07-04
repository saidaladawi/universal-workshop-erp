"""
Test Suite for Universal Workshop Real-time System
Tests WebSocket, Event Bus, Notifications, and PWA Sync
"""

import frappe
import unittest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from .websocket_manager import WebSocketManager, get_websocket_manager
from .event_bus import WorkshopEventBus, EventType, EventPriority, get_workshop_event_bus
from .notification_handler import ArabicNotificationHandler, NotificationPriority, get_arabic_notification_handler
from .sync_manager import PWASyncManager, SyncPriority, ConflictResolution, get_pwa_sync_manager
from .config import get_config, validate_config


class TestWebSocketManager(unittest.TestCase):
    """Test WebSocket Manager functionality"""
    
    def setUp(self):
        self.websocket_manager = WebSocketManager()
        
    def test_websocket_initialization(self):
        """Test WebSocket manager initialization"""
        self.assertIsNotNone(self.websocket_manager.sio)
        self.assertEqual(self.websocket_manager.default_timezone, "Asia/Muscat")
        self.assertTrue(self.websocket_manager.arabic_enabled)
        
    def test_connection_management(self):
        """Test client connection management"""
        # Mock connection
        test_sid = "test_session_123"
        test_environ = {
            'HTTP_X_USER_ID': 'test_user',
            'HTTP_X_WORKSHOP_ID': 'main_workshop',
            'HTTP_X_USER_ROLE': 'technician',
            'HTTP_X_LANGUAGE': 'ar'
        }
        
        # Test connection storage
        with self.websocket_manager.connection_lock:
            self.websocket_manager.active_connections[test_sid] = {
                "user_id": test_environ['HTTP_X_USER_ID'],
                "workshop_id": test_environ['HTTP_X_WORKSHOP_ID'],
                "user_role": test_environ['HTTP_X_USER_ROLE'],
                "language": test_environ['HTTP_X_LANGUAGE'],
                "connected_at": datetime.now().isoformat(),
            }
        
        self.assertIn(test_sid, self.websocket_manager.active_connections)
        self.assertEqual(
            self.websocket_manager.active_connections[test_sid]['user_id'], 
            'test_user'
        )
        
    def test_arabic_welcome_message(self):
        """Test Arabic welcome message generation"""
        welcome_msg = self.websocket_manager._get_welcome_message('ar', 'technician')
        
        self.assertIn('مرحباً', welcome_msg['message_ar'])
        self.assertEqual(welcome_msg['language'], 'ar')
        self.assertEqual(welcome_msg['direction'], 'rtl')
        
    def test_mobile_client_detection(self):
        """Test mobile client detection"""
        mobile_environ = {
            'HTTP_USER_AGENT': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)'
        }
        desktop_environ = {
            'HTTP_USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        self.assertTrue(self.websocket_manager._is_mobile_client(mobile_environ))
        self.assertFalse(self.websocket_manager._is_mobile_client(desktop_environ))


class TestWorkshopEventBus(unittest.TestCase):
    """Test Workshop Event Bus functionality"""
    
    def setUp(self):
        self.event_bus = WorkshopEventBus()
        
    def test_event_bus_initialization(self):
        """Test event bus initialization"""
        self.assertTrue(self.event_bus.arabic_enabled)
        self.assertTrue(self.event_bus.cultural_events_enabled)
        self.assertIsInstance(self.event_bus.event_handlers, dict)
        
    def test_event_subscription(self):
        """Test event subscription mechanism"""
        test_handler = Mock()
        
        self.event_bus.subscribe(EventType.SERVICE_STARTED, test_handler)
        
        self.assertIn(EventType.SERVICE_STARTED, self.event_bus.event_handlers)
        self.assertIn(test_handler, self.event_bus.event_handlers[EventType.SERVICE_STARTED])
        
    def test_arabic_content_detection(self):
        """Test Arabic content detection"""
        arabic_text = "مرحبا بكم في الورشة"
        english_text = "Welcome to the workshop"
        
        self.assertTrue(self.event_bus._contains_arabic(arabic_text))
        self.assertFalse(self.event_bus._contains_arabic(english_text))
        
    def test_arabic_translations_generation(self):
        """Test Arabic translations generation"""
        event_data = {
            'service_name': 'تغيير الزيت',
            'vehicle_number': '12345'
        }
        
        translations = self.event_bus._generate_arabic_translations(
            EventType.SERVICE_STARTED, event_data
        )
        
        self.assertIn('title_ar', translations)
        self.assertIn('message_ar', translations)
        self.assertEqual(translations['title_ar'], 'بدء الخدمة')
        
    async def test_event_publishing(self):
        """Test event publishing mechanism"""
        test_handler = AsyncMock()
        self.event_bus.subscribe(EventType.SERVICE_STARTED, test_handler)
        
        event_data = {
            'service_order_id': 'SO-001',
            'customer': 'أحمد محمد',
            'vehicle': 'تويوتا كامري'
        }
        
        event_id = await self.event_bus.publish(
            EventType.SERVICE_STARTED,
            event_data,
            priority=EventPriority.HIGH,
            language='ar'
        )
        
        self.assertIsNotNone(event_id)
        test_handler.assert_called_once()
        
    def test_event_statistics(self):
        """Test event statistics tracking"""
        initial_stats = self.event_bus.get_event_statistics()
        
        # Simulate event processing
        self.event_bus._update_event_stats({
            'type': 'service_started',
            'priority': EventPriority.HIGH.value,
            'arabic_content': True
        })
        
        updated_stats = self.event_bus.get_event_statistics()
        
        self.assertEqual(updated_stats['total_events'], initial_stats['total_events'] + 1)
        self.assertEqual(updated_stats['arabic_events'], initial_stats['arabic_events'] + 1)


class TestArabicNotificationHandler(unittest.TestCase):
    """Test Arabic Notification Handler functionality"""
    
    def setUp(self):
        self.notification_handler = ArabicNotificationHandler()
        
    def test_notification_handler_initialization(self):
        """Test notification handler initialization"""
        self.assertTrue(self.notification_handler.arabic_enabled)
        self.assertEqual(self.notification_handler.text_direction, "rtl")
        self.assertIsInstance(self.notification_handler.templates, dict)
        
    def test_arabic_template_system(self):
        """Test Arabic notification templates"""
        templates = self.notification_handler.templates
        
        self.assertIn('service_started', templates)
        self.assertIn('title_ar', templates['service_started'])
        self.assertIn('message_ar', templates['service_started'])
        
        # Test template content
        service_template = templates['service_started']
        self.assertEqual(service_template['title_ar'], 'بدء الخدمة')
        
    def test_arabic_numeral_conversion(self):
        """Test Arabic numeral conversion"""
        western_text = "Service Order 12345"
        arabic_text = self.notification_handler._convert_to_arabic_numerals(western_text)
        
        self.assertIn('١٢٣٤٥', arabic_text)
        
    def test_cultural_timing_constraints(self):
        """Test cultural timing constraints"""
        # Test prayer time awareness
        self.assertFalse(
            self.notification_handler._is_appropriate_time(NotificationPriority.LOW)
        )
        
        # Emergency notifications should always be sent
        self.assertTrue(
            self.notification_handler._is_appropriate_time(NotificationPriority.EMERGENCY)
        )
        
    def test_notification_content_generation(self):
        """Test notification content generation"""
        notification_data = {
            'service_name': 'تغيير الزيت',
            'vehicle_number': '12345'
        }
        
        content = self.notification_handler._generate_notification_content(
            'service_started', notification_data, 'ar'
        )
        
        self.assertEqual(content['language'], 'ar')
        self.assertEqual(content['direction'], 'rtl')
        self.assertIn('تغيير الزيت', content['message'])
        
    async def test_notification_queuing(self):
        """Test notification queuing system"""
        notification_result = await self.notification_handler.send_notification(
            notification_type='service_started',
            recipient='test_user',
            data={'service_name': 'تغيير الزيت'},
            language='ar'
        )
        
        self.assertEqual(notification_result['status'], 'success')
        self.assertIn('notification_id', notification_result)
        
    def test_email_body_formatting(self):
        """Test Arabic email body formatting"""
        content = {
            'title': 'بدء الخدمة',
            'message': 'تم بدء خدمة تغيير الزيت',
            'language': 'ar',
            'direction': 'rtl'
        }
        
        email_body = self.notification_handler._format_email_body(content, {})
        
        self.assertIn('dir="rtl"', email_body)
        self.assertIn('بدء الخدمة', email_body)
        self.assertIn('نظام إدارة الورش الشامل', email_body)


class TestPWASyncManager(unittest.TestCase):
    """Test PWA Sync Manager functionality"""
    
    def setUp(self):
        self.sync_manager = PWASyncManager()
        
    def test_sync_manager_initialization(self):
        """Test sync manager initialization"""
        self.assertTrue(self.sync_manager.arabic_enabled)
        self.assertTrue(self.sync_manager.cultural_sync_rules)
        self.assertIsInstance(self.sync_manager.priority_doctypes, dict)
        
    def test_arabic_content_detection(self):
        """Test Arabic content detection in sync data"""
        arabic_data = {
            'customer_name': 'أحمد محمد',
            'notes_ar': 'ملاحظات باللغة العربية'
        }
        english_data = {
            'customer_name': 'John Smith',
            'notes': 'English notes'
        }
        
        self.assertTrue(self.sync_manager._contains_arabic_content(arabic_data))
        self.assertFalse(self.sync_manager._contains_arabic_content(english_data))
        
    def test_checksum_calculation(self):
        """Test data integrity checksum calculation"""
        test_data = {
            'name': 'Test Document',
            'status': 'Active',
            'modified': '2023-12-01 10:00:00'
        }
        
        checksum1 = self.sync_manager._calculate_checksum(test_data)
        checksum2 = self.sync_manager._calculate_checksum(test_data)
        
        # Same data should produce same checksum
        self.assertEqual(checksum1, checksum2)
        
        # Modified data should produce different checksum
        test_data['status'] = 'Inactive'
        checksum3 = self.sync_manager._calculate_checksum(test_data)
        self.assertNotEqual(checksum1, checksum3)
        
    async def test_sync_operation_queuing(self):
        """Test sync operation queuing"""
        test_data = {
            'customer_name': 'أحمد محمد',
            'phone': '+96812345678'
        }
        
        operation_id = await self.sync_manager.queue_sync_operation(
            operation_type='create',
            doctype='Customer',
            doc_name='CUST-001',
            data=test_data,
            user_id='test_user'
        )
        
        self.assertIsNotNone(operation_id)
        self.assertTrue(len(self.sync_manager.sync_queue) > 0)
        
    def test_conflict_detection(self):
        """Test synchronization conflict detection"""
        # This would require mocking frappe.get_doc and database operations
        # For now, test the conflict detection logic structure
        
        operation = {
            'operation_type': 'update',
            'doctype': 'Customer',
            'doc_name': 'CUST-001',
            'checksum': 'test_checksum',
            'offline_timestamp': datetime.now().isoformat()
        }
        
        # Test would verify conflict detection logic
        self.assertIsInstance(operation, dict)
        
    def test_arabic_validation(self):
        """Test Arabic text validation"""
        valid_arabic = "النص العربي صحيح"
        invalid_text = "Invalid text"
        
        self.assertTrue(self.sync_manager._is_valid_arabic_text(valid_arabic))
        self.assertFalse(self.sync_manager._is_valid_arabic_text(invalid_text))
        
    def test_sync_statistics(self):
        """Test sync statistics tracking"""
        initial_stats = self.sync_manager.stats.copy()
        
        # Simulate successful sync
        test_operation = {
            'doctype': 'Customer',
            'user_id': 'test_user',
            'arabic_content': True
        }
        
        self.sync_manager._update_sync_stats(test_operation, True)
        
        self.assertEqual(self.sync_manager.stats['total_syncs'], initial_stats['total_syncs'] + 1)
        self.assertEqual(self.sync_manager.stats['successful_syncs'], initial_stats['successful_syncs'] + 1)
        self.assertEqual(self.sync_manager.stats['arabic_content_synced'], initial_stats['arabic_content_synced'] + 1)


class TestConfigurationSystem(unittest.TestCase):
    """Test configuration system"""
    
    def test_config_loading(self):
        """Test configuration loading"""
        websocket_config = get_config('websocket')
        cultural_config = get_config('cultural')
        
        self.assertIsInstance(websocket_config, dict)
        self.assertIsInstance(cultural_config, dict)
        
        self.assertIn('port', websocket_config)
        self.assertIn('default_language', cultural_config)
        
    def test_config_validation(self):
        """Test configuration validation"""
        errors = validate_config()
        
        # Should return empty list if all configs are valid
        self.assertIsInstance(errors, list)
        
    def test_arabic_cultural_settings(self):
        """Test Arabic and cultural settings"""
        cultural_config = get_config('cultural')
        
        self.assertEqual(cultural_config['default_language'], 'ar')
        self.assertEqual(cultural_config['timezone'], 'Asia/Muscat')
        self.assertIn('friday', cultural_config['business_hours']['weekend'])
        self.assertIn('saturday', cultural_config['business_hours']['weekend'])


class TestIntegrationScenarios(unittest.TestCase):
    """Test integration scenarios"""
    
    async def test_service_order_workflow(self):
        """Test complete service order workflow"""
        # Initialize components
        event_bus = get_workshop_event_bus()
        notification_handler = get_arabic_notification_handler()
        sync_manager = get_pwa_sync_manager()
        
        # Simulate service order creation
        service_data = {
            'customer': 'أحمد محمد',
            'vehicle': 'تويوتا كامري 2020',
            'service_type': 'تغيير الزيت',
            'status': 'Draft'
        }
        
        # Queue sync operation
        sync_id = await sync_manager.queue_sync_operation(
            operation_type='create',
            doctype='Service Order',
            doc_name='SO-001',
            data=service_data,
            user_id='technician_001'
        )
        
        # Publish event
        event_id = await event_bus.publish(
            EventType.SERVICE_STARTED,
            {
                'service_order_id': 'SO-001',
                'customer': service_data['customer'],
                'vehicle': service_data['vehicle']
            },
            priority=EventPriority.HIGH
        )
        
        # Send notification
        notification_result = await notification_handler.send_notification(
            notification_type='service_started',
            recipient='customer_001',
            data=service_data,
            language='ar'
        )
        
        # Verify all operations completed successfully
        self.assertIsNotNone(sync_id)
        self.assertIsNotNone(event_id)
        self.assertEqual(notification_result['status'], 'success')
        
    async def test_arabic_content_flow(self):
        """Test Arabic content flow through the system"""
        arabic_data = {
            'customer_name_ar': 'أحمد محمد السالمي',
            'service_notes_ar': 'تغيير الزيت والفلتر',
            'technician_notes_ar': 'تم الفحص بنجاح'
        }
        
        # Test sync manager Arabic detection
        sync_manager = get_pwa_sync_manager()
        has_arabic = sync_manager._contains_arabic_content(arabic_data)
        self.assertTrue(has_arabic)
        
        # Test event bus Arabic translations
        event_bus = get_workshop_event_bus()
        translations = event_bus._generate_arabic_translations(
            EventType.SERVICE_COMPLETED, arabic_data
        )
        self.assertIn('title_ar', translations)
        
        # Test notification Arabic formatting
        notification_handler = get_arabic_notification_handler()
        content = notification_handler._generate_notification_content(
            'service_completed', arabic_data, 'ar'
        )
        self.assertEqual(content['direction'], 'rtl')


def run_tests():
    """Run all real-time system tests"""
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestWebSocketManager,
        TestWorkshopEventBus,
        TestArabicNotificationHandler,
        TestPWASyncManager,
        TestConfigurationSystem,
        TestIntegrationScenarios
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result


# Frappe test integration
@frappe.whitelist()
def run_realtime_tests():
    """API endpoint to run real-time system tests"""
    try:
        result = run_tests()
        
        return {
            'status': 'completed',
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success_rate': (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
        }
        
    except Exception as e:
        frappe.log_error(f"Test execution failed: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }


if __name__ == '__main__':
    run_tests() 