# Universal Workshop Real-time System
## نظام الوقت الفعلي للورشة الشاملة

A comprehensive real-time communication system for Universal Workshop ERP with Arabic-first design and PWA synchronization capabilities.

## Features / المميزات

### 🔄 Real-time WebSocket Communication
- **Arabic-first messaging system** - نظام الرسائل العربي الأولوي
- **Workshop floor live updates** - التحديثات المباشرة لأرضية الورشة  
- **Mobile technician synchronization** - مزامنة الفنيين المتنقلين
- **Cultural business event handling** - معالجة الأحداث التجارية الثقافية

### 📱 PWA Synchronization Manager
- **Offline-first data sync** - مزامنة البيانات في وضع عدم الاتصال أولاً
- **Conflict resolution with business logic** - حل التضارب بمنطق الأعمال
- **Arabic content optimization** - تحسين المحتوى العربي
- **Cultural business rules enforcement** - تطبيق قواعد الأعمال الثقافية

### 🔔 Arabic Notification Handler
- **Multi-channel notifications** (SMS, WhatsApp, Push, Voice, Email)
- **Cultural timing awareness** (prayer times, business hours)
- **Arabic text processing and formatting**
- **Oman-specific communication patterns**

### 🎯 Workshop Event Bus
- **Event-driven architecture** for workshop operations
- **Arabic-first event messaging**
- **Priority-based event processing**
- **Workshop coordination and tracking**

## Architecture / الهيكلة

```
realtime/
├── __init__.py                 # Module initialization
├── websocket_manager.py        # WebSocket server and connection management
├── event_bus.py               # Event-driven communication system
├── notification_handler.py    # Multi-channel Arabic notifications
├── sync_manager.py            # PWA offline/online synchronization
├── config.py                  # System configuration
├── test_realtime_system.py    # Comprehensive test suite
└── README.md                  # This documentation
```

## Installation / التثبيت

### 1. Install Dependencies / تثبيت التبعيات

```bash
# Install required Python packages
pip install python-socketio>=5.9.0
pip install redis>=5.0.0
pip install asyncio>=3.4.3
```

### 2. Configure Redis / تكوين Redis

```bash
# Ensure Redis is running
redis-server

# Test Redis connection
redis-cli ping
```

### 3. Update Site Configuration / تحديث تكوين الموقع

Add to your `site_config.json`:

```json
{
  "redis_cache": {
    "host": "localhost",
    "port": 6379,
    "db": 1
  },
  "socketio_port": 9000,
  "enable_realtime": true
}
```

## Configuration / التكوين

### WebSocket Configuration
```python
WEBSOCKET_CONFIG = {
    'host': '0.0.0.0',
    'port': 9000,
    'cors_allowed_origins': "*",
    'ping_timeout': 60,
    'ping_interval': 25
}
```

### Cultural Settings / الإعدادات الثقافية
```python
CULTURAL_CONFIG = {
    'default_language': 'ar',
    'timezone': 'Asia/Muscat',
    'business_hours': {
        'start': '07:00',
        'end': '18:00',
        'weekend': ['friday', 'saturday']
    },
    'prayer_times': {
        'fajr': '05:30',
        'dhuhr': '12:15',
        'asr': '15:45',
        'maghrib': '18:30',
        'isha': '20:00'
    }
}
```

## Usage / الاستخدام

### 1. WebSocket Connection / اتصال WebSocket

```javascript
// Client-side connection
const socket = io('http://localhost:9000', {
    extraHeaders: {
        'X-User-ID': 'user123',
        'X-Workshop-ID': 'main_workshop',
        'X-Language': 'ar'
    }
});

socket.on('connect', () => {
    console.log('متصل بالخادم');
});

socket.on('notification', (data) => {
    console.log('إشعار جديد:', data);
});
```

### 2. Publishing Events / نشر الأحداث

```python
from universal_workshop.realtime.event_bus import get_workshop_event_bus, EventType, EventPriority

event_bus = get_workshop_event_bus()

await event_bus.publish(
    EventType.SERVICE_STARTED,
    {
        'service_order_id': 'SO-001',
        'customer': 'أحمد محمد',
        'vehicle': 'تويوتا كامري',
        'service_name': 'تغيير الزيت'
    },
    priority=EventPriority.HIGH,
    workshop_id='main_workshop',
    language='ar'
)
```

### 3. Sending Notifications / إرسال الإشعارات

```python
from universal_workshop.realtime.notification_handler import get_arabic_notification_handler

notification_handler = get_arabic_notification_handler()

await notification_handler.send_notification(
    notification_type='service_completed',
    recipient='customer_001',
    data={
        'service_name': 'تغيير الزيت',
        'vehicle_number': '12345'
    },
    channels=['push', 'sms', 'whatsapp'],
    language='ar'
)
```

### 4. PWA Synchronization / مزامنة PWA

```python
from universal_workshop.realtime.sync_manager import get_pwa_sync_manager, SyncPriority

sync_manager = get_pwa_sync_manager()

await sync_manager.queue_sync_operation(
    operation_type='update',
    doctype='Service Order',
    doc_name='SO-001',
    data={
        'status': 'Completed',
        'completion_notes_ar': 'تم إنجاز العمل بنجاح'
    },
    user_id='technician_001',
    priority=SyncPriority.HIGH
)
```

## API Endpoints / نقاط الوصول للAPI

### Event Bus APIs
- `POST /api/realtime/events/publish` - Publish workshop event
- `GET /api/realtime/events/history` - Get event history
- `GET /api/realtime/events/stats` - Get event statistics

### Notification APIs
- `POST /api/realtime/notifications/send` - Send notification
- `GET /api/realtime/notifications/history` - Get delivery history
- `GET /api/realtime/notifications/stats` - Get delivery statistics

### Sync APIs
- `POST /api/realtime/sync/queue` - Queue sync operation
- `GET /api/realtime/sync/status` - Get sync status
- `POST /api/realtime/sync/resolve-conflict` - Resolve sync conflict

### WebSocket Events
- `connection_established` - Client connected
- `workshop_event` - Workshop floor event
- `notification` - Real-time notification
- `sync_update` - Synchronization update

## Event Types / أنواع الأحداث

| Event Type | Arabic Name | Description |
|------------|-------------|-------------|
| `SERVICE_STARTED` | بدء الخدمة | Service order started |
| `SERVICE_COMPLETED` | اكتمال الخدمة | Service order completed |
| `TECHNICIAN_ASSIGNED` | تعيين فني | Technician assigned to service |
| `CUSTOMER_ARRIVED` | وصول العميل | Customer arrived at workshop |
| `VEHICLE_READY` | جاهزية المركبة | Vehicle ready for pickup |
| `EMERGENCY_REPAIR` | إصلاح طارئ | Emergency repair needed |
| `PARTS_REQUESTED` | طلب قطع غيار | Parts request submitted |

## Notification Channels / قنوات الإشعارات

| Channel | Arabic Name | Description |
|---------|-------------|-------------|
| `push` | الدفع | Push notifications to mobile/web |
| `sms` | رسائل نصية | SMS messages |
| `whatsapp` | واتساب | WhatsApp messages |
| `email` | بريد إلكتروني | Email notifications |
| `voice` | صوتي | Voice call notifications |
| `in_app` | داخل التطبيق | In-app notifications |
| `websocket` | ويب سوكت | Real-time WebSocket messages |

## Sync Priorities / أولويات المزامنة

| Priority | Value | Use Case |
|----------|-------|----------|
| `CRITICAL` | 5 | Service Orders, Appointments |
| `HIGH` | 4 | Customers, Vehicles, Technicians |
| `NORMAL` | 2 | Items, Workshop Profiles |
| `LOW` | 1 | Non-critical data |

## Cultural Features / المميزات الثقافية

### 🕌 Prayer Time Awareness
- Notifications respect prayer times
- Low-priority messages delayed during prayer
- Emergency notifications always delivered

### 🇴🇲 Oman Business Hours
- Weekend: Friday & Saturday
- Business hours: 7:00 AM - 6:00 PM
- Cultural timing for non-urgent communications

### 🔤 Arabic Text Processing
- Right-to-left (RTL) text direction
- Arabic numeral conversion (١٢٣٤٥)
- Proper Arabic text encoding
- Cultural message formatting

### 📱 Mobile Optimization
- Offline-first PWA support
- Mobile technician workflows
- Touch-optimized Arabic interfaces
- Reduced data usage for mobile connections

## Testing / الاختبار

Run the comprehensive test suite:

```python
# Run all tests
from universal_workshop.realtime.test_realtime_system import run_tests
result = run_tests()

# Or via API
GET /api/realtime/test/run
```

Test categories:
- WebSocket connection management
- Event bus functionality
- Arabic notification handling
- PWA synchronization
- Configuration validation
- Integration scenarios

## Performance / الأداء

### Optimization Features
- **Connection pooling** for WebSocket connections
- **Message batching** for efficient sync
- **Compression** for large messages
- **Caching** for frequently accessed data
- **Rate limiting** to prevent abuse

### Monitoring
- Real-time connection count
- Event processing statistics
- Notification delivery rates
- Sync operation metrics
- Arabic content processing stats

## Security / الأمان

### Authentication & Authorization
- User-based WebSocket authentication
- Role-based event access control
- Workshop-specific data isolation
- Secure API endpoints

### Data Protection
- Encrypted WebSocket connections (WSS)
- Secure notification channels
- Data integrity checksums
- Audit logging for all operations

## Troubleshooting / استكشاف الأخطاء

### Common Issues

1. **WebSocket Connection Failed**
   ```bash
   # Check if port 9000 is available
   netstat -an | grep 9000
   
   # Verify Redis is running
   redis-cli ping
   ```

2. **Arabic Text Not Displaying**
   ```python
   # Check UTF-8 encoding
   import locale
   print(locale.getpreferredencoding())
   
   # Verify Arabic font support
   ```

3. **Notifications Not Sending**
   ```python
   # Check notification handler status
   from universal_workshop.realtime.notification_handler import get_arabic_notification_handler
   handler = get_arabic_notification_handler()
   stats = handler.get_delivery_statistics()
   print(stats)
   ```

4. **Sync Conflicts**
   ```python
   # Check conflict queue
   from universal_workshop.realtime.sync_manager import get_pwa_sync_manager
   sync_manager = get_pwa_sync_manager()
   conflicts = sync_manager.get_conflict_queue()
   print(f"Pending conflicts: {len(conflicts)}")
   ```

### Logging
Enable detailed logging in `config.py`:
```python
LOGGING_CONFIG = {
    'level': 'DEBUG',
    'enable_file_logging': True,
    'log_file_path': 'logs/realtime.log'
}
```

## Contributing / المساهمة

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure Arabic content support
5. Submit a pull request

### Code Style
- Follow PEP 8 for Python code
- Use Arabic comments for business logic
- Include both Arabic and English documentation
- Test with Arabic data samples

## License / الترخيص

MIT License - See LICENSE file for details

## Support / الدعم

For technical support or questions:
- Email: al.a.dawi@hotmail.com
- Create an issue in the repository
- Check the troubleshooting section above

---

**Universal Workshop ERP** - Comprehensive automotive workshop management with Arabic-first design and real-time capabilities.

**نظام إدارة الورش الشامل** - نظام شامل لإدارة ورش السيارات بتصميم عربي أولوي وقدرات الوقت الفعلي. 