<!--
  Live Service Tracker - Universal Workshop Frontend V2
  
  Real-time service order tracking with Arabic support and offline capability.
-->

<template>
  <div class="live-service-tracker" :class="{ 'rtl': isRTL }">
    <!-- Connection status indicator -->
    <div class="connection-status" :class="connectionState">
      <div class="status-indicator">
        <div class="status-dot" :class="connectionState"></div>
        <span class="status-text">
          {{ getConnectionText() }}
        </span>
      </div>
      
      <div v-if="hasQueuedEvents" class="queue-indicator">
        <Icon name="clock" />
        <span>{{ queueSize }} {{ preferArabic ? 'في الانتظار' : 'queued' }}</span>
      </div>
    </div>

    <!-- Live updates header -->
    <div class="tracker-header">
      <div class="header-left">
        <h2 class="tracker-title">
          {{ preferArabic ? 'تتبع الخدمات المباشر' : 'Live Service Tracking' }}
        </h2>
        <span class="live-badge">
          <Icon name="radio" />
          {{ preferArabic ? 'مباشر' : 'LIVE' }}
        </span>
      </div>

      <div class="header-controls">
        <Button variant="outline" size="sm" @click="toggleAutoRefresh">
          <Icon :name="autoRefresh ? 'pause' : 'play'" />
          {{ autoRefresh 
            ? (preferArabic ? 'إيقاف التحديث' : 'Pause Updates')
            : (preferArabic ? 'تشغيل التحديث' : 'Resume Updates')
          }}
        </Button>

        <Button variant="outline" size="sm" @click="requestFullUpdate">
          <Icon name="refresh" />
          {{ preferArabic ? 'تحديث شامل' : 'Full Refresh' }}
        </Button>
      </div>
    </div>

    <!-- Service orders grid -->
    <div class="service-orders-grid">
      <TransitionGroup name="service-card" tag="div" class="grid-container">
        <div
          v-for="(order, orderId) in activeServiceOrders"
          :key="orderId"
          class="service-order-card"
          :class="{
            'updated': recentlyUpdated.has(orderId),
            'critical': order.priority === 'critical',
            'overdue': isOverdue(order)
          }"
        >
          <!-- Order header -->
          <div class="order-header">
            <div class="order-info">
              <h3 class="order-id">{{ orderId }}</h3>
              <span class="customer-name">{{ order.customerName }}</span>
            </div>
            
            <div class="order-status" :class="order.status">
              <span class="status-text">{{ getStatusText(order.status) }}</span>
              <div class="status-progress" v-if="order.progress !== undefined">
                <div class="progress-fill" :style="{ width: `${order.progress}%` }"></div>
              </div>
            </div>
          </div>

          <!-- Vehicle info -->
          <div class="vehicle-info">
            <img 
              :src="order.vehicleImage || '/default-vehicle.png'" 
              :alt="order.vehicleDescription"
              class="vehicle-image"
            >
            <div class="vehicle-details">
              <h4>{{ order.vehicleMake }} {{ order.vehicleModel }}</h4>
              <p>{{ order.plateNumber }} • {{ order.year }}</p>
              <p class="mileage">{{ formatMileage(order.mileage) }}</p>
            </div>
          </div>

          <!-- Service details -->
          <div class="service-details">
            <div class="service-type">
              <Icon name="wrench" />
              <span>{{ preferArabic ? order.serviceTypeAr : order.serviceType }}</span>
            </div>
            
            <div class="estimated-time" v-if="order.estimatedDuration">
              <Icon name="clock" />
              <span>{{ formatDuration(order.estimatedDuration) }}</span>
            </div>

            <div class="assigned-tech" v-if="order.assignedTechnician">
              <Icon name="user" />
              <span>{{ order.assignedTechnician.name }}</span>
            </div>
          </div>

          <!-- Bay assignment -->
          <div class="bay-assignment" v-if="order.assignedBay">
            <div class="bay-info">
              <Icon name="location" />
              <span>{{ preferArabic ? order.assignedBay.nameAr : order.assignedBay.name }}</span>
            </div>
            
            <div class="bay-status" :class="order.assignedBay.status">
              {{ getBayStatusText(order.assignedBay.status) }}
            </div>
          </div>

          <!-- Real-time updates -->
          <div class="recent-updates" v-if="getOrderUpdates(orderId).length > 0">
            <h5>{{ preferArabic ? 'آخر التحديثات:' : 'Recent Updates:' }}</h5>
            <div class="update-list">
              <div
                v-for="update in getOrderUpdates(orderId).slice(0, 3)"
                :key="update.id"
                class="update-item"
              >
                <span class="update-time">{{ formatRelativeTime(update.timestamp) }}</span>
                <span class="update-text">
                  {{ preferArabic ? update.data.metadata.descriptionAr : update.data.metadata.description }}
                </span>
              </div>
            </div>
          </div>

          <!-- Quick actions -->
          <div class="quick-actions">
            <Button size="sm" variant="primary" @click="viewOrderDetails(orderId)">
              {{ preferArabic ? 'التفاصيل' : 'Details' }}
            </Button>
            
            <Button 
              v-if="canUpdateStatus(order)" 
              size="sm" 
              variant="secondary" 
              @click="showStatusDialog(orderId)"
            >
              {{ preferArabic ? 'تحديث الحالة' : 'Update Status' }}
            </Button>

            <Button 
              v-if="order.status === 'completed'" 
              size="sm" 
              variant="success" 
              @click="generateInvoice(orderId)"
            >
              {{ preferArabic ? 'إنشاء فاتورة' : 'Generate Invoice' }}
            </Button>
          </div>

          <!-- Update indicator -->
          <div 
            v-if="recentlyUpdated.has(orderId)" 
            class="update-indicator"
            @animationend="clearUpdateIndicator(orderId)"
          >
            <Icon name="bell" />
          </div>
        </div>
      </TransitionGroup>
    </div>

    <!-- Empty state -->
    <div v-if="activeServiceOrders.size === 0" class="empty-state">
      <Icon name="clipboard-list" size="xl" />
      <h3>{{ preferArabic ? 'لا توجد خدمات نشطة' : 'No Active Services' }}</h3>
      <p>{{ preferArabic 
        ? 'سيتم عرض أوامر الخدمة هنا عند إنشائها'
        : 'Service orders will appear here when created'
      }}</p>
    </div>

    <!-- Recent events panel -->
    <div class="recent-events-panel" v-if="showEventsPanel">
      <div class="panel-header">
        <h3>{{ preferArabic ? 'الأحداث الأخيرة' : 'Recent Events' }}</h3>
        <Button variant="outline" size="sm" @click="showEventsPanel = false">
          <Icon name="x" />
        </Button>
      </div>
      
      <div class="events-list">
        <div
          v-for="event in recentEvents.slice(0, 20)"
          :key="event.id"
          class="event-item"
          :class="event.type"
        >
          <div class="event-time">{{ formatTime(event.timestamp) }}</div>
          <div class="event-content">
            <strong>{{ preferArabic ? event.data.metadata.titleAr : event.data.metadata.title }}</strong>
            <p v-if="event.data.metadata.description">
              {{ preferArabic ? event.data.metadata.descriptionAr : event.data.metadata.description }}
            </p>
          </div>
          <div class="event-type">{{ event.type }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useEventBus, useServiceOrderEvents } from '@/composables/useEventBus'
import { Button, Icon } from '@/components/base'

// Props
defineProps<{
  preferArabic?: boolean
  isRTL?: boolean
}>()

// Emits
const emit = defineEmits<{
  orderSelected: [orderId: string]
  statusUpdate: [orderId: string, status: string]
}>()

// Composables
const eventBus = useEventBus({ autoConnect: true, preferArabic: true })
const serviceOrders = useServiceOrderEvents()

// State
const autoRefresh = ref(true)
const showEventsPanel = ref(false)
const recentlyUpdated = ref<Set<string>>(new Set())
const lastUpdateTime = ref<Map<string, number>>(new Map())

// Computed
const connectionState = computed(() => eventBus.connectionStatus.value.state)
const hasQueuedEvents = computed(() => eventBus.hasQueuedEvents.value)
const queueSize = computed(() => eventBus.connectionStatus.value.queueSize)
const activeServiceOrders = computed(() => serviceOrders.activeServiceOrders.value)
const recentEvents = computed(() => eventBus.recentEvents.value)

// Methods
const getConnectionText = (): string => {
  const state = connectionState.value
  const preferArabic = true // Get from props/store
  
  const texts = {
    connected: { en: 'Connected', ar: 'متصل' },
    disconnected: { en: 'Disconnected', ar: 'منقطع' },
    reconnecting: { en: 'Reconnecting...', ar: 'إعادة الاتصال...' }
  }
  
  return preferArabic ? texts[state].ar : texts[state].en
}

const getStatusText = (status: string): string => {
  const preferArabic = true
  const statusMap: Record<string, { en: string; ar: string }> = {
    'draft': { en: 'Draft', ar: 'مسودة' },
    'open': { en: 'Open', ar: 'مفتوح' },
    'assigned': { en: 'Assigned', ar: 'معين' },
    'in_progress': { en: 'In Progress', ar: 'قيد التنفيذ' },
    'completed': { en: 'Completed', ar: 'مكتمل' },
    'cancelled': { en: 'Cancelled', ar: 'ملغي' }
  }
  
  return preferArabic ? statusMap[status]?.ar || status : statusMap[status]?.en || status
}

const getBayStatusText = (status: string): string => {
  const preferArabic = true
  const statusMap: Record<string, { en: string; ar: string }> = {
    'available': { en: 'Available', ar: 'متاح' },
    'occupied': { en: 'Occupied', ar: 'مشغول' },
    'maintenance': { en: 'Maintenance', ar: 'صيانة' }
  }
  
  return preferArabic ? statusMap[status]?.ar || status : statusMap[status]?.en || status
}

const formatMileage = (mileage: number): string => {
  const preferArabic = true
  return preferArabic ? `${mileage.toLocaleString('ar')} كم` : `${mileage.toLocaleString()} km`
}

const formatDuration = (minutes: number): string => {
  const preferArabic = true
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  
  if (preferArabic) {
    if (hours > 0) {
      return `${hours} ساعة ${mins > 0 ? `${mins} دقيقة` : ''}`
    }
    return `${mins} دقيقة`
  } else {
    if (hours > 0) {
      return `${hours}h ${mins > 0 ? `${mins}m` : ''}`
    }
    return `${mins}m`
  }
}

const formatRelativeTime = (timestamp: number): string => {
  const now = Date.now()
  const diff = now - timestamp
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  
  const preferArabic = true
  
  if (preferArabic) {
    if (days > 0) return `منذ ${days} يوم${days > 1 ? 'ًا' : ''}`
    if (hours > 0) return `منذ ${hours} ساعة${hours > 1 ? 'ات' : ''}`
    if (minutes > 0) return `منذ ${minutes} دقيقة${minutes > 1 ? 'دقائق' : ''}`
    return 'الآن'
  } else {
    if (days > 0) return `${days}d ago`
    if (hours > 0) return `${hours}h ago`  
    if (minutes > 0) return `${minutes}m ago`
    return 'now'
  }
}

const formatTime = (timestamp: number): string => {
  return new Date(timestamp).toLocaleTimeString()
}

const isOverdue = (order: any): boolean => {
  if (!order.estimatedCompletion) return false
  return Date.now() > order.estimatedCompletion
}

const canUpdateStatus = (order: any): boolean => {
  return ['open', 'assigned', 'in_progress'].includes(order.status)
}

const getOrderUpdates = (orderId: string) => {
  return eventBus.getEntityEvents('service_order', orderId, 5)
}

const toggleAutoRefresh = () => {
  autoRefresh.value = !autoRefresh.value
}

const requestFullUpdate = async () => {
  await eventBus.requestBulkUpdate('service_order')
}

const viewOrderDetails = (orderId: string) => {
  emit('orderSelected', orderId)
}

const showStatusDialog = (orderId: string) => {
  // This would open a status update dialog
  console.log('Show status dialog for', orderId)
}

const generateInvoice = (orderId: string) => {
  // This would trigger invoice generation
  console.log('Generate invoice for', orderId)
}

const clearUpdateIndicator = (orderId: string) => {
  recentlyUpdated.value.delete(orderId)
}

// Event handlers
const handleServiceOrderUpdate = (event: any) => {
  if (!autoRefresh.value) return
  
  const orderId = event.data.entityId
  recentlyUpdated.value.add(orderId)
  lastUpdateTime.value.set(orderId, Date.now())
  
  // Clear indicator after animation
  setTimeout(() => {
    recentlyUpdated.value.delete(orderId)
  }, 3000)
}

// Lifecycle
onMounted(() => {
  // Subscribe to service order events
  eventBus.subscribe('service_order_updated', handleServiceOrderUpdate)
  eventBus.subscribe('service_order_assigned', handleServiceOrderUpdate)
  eventBus.subscribe('service_order_completed', handleServiceOrderUpdate)
  
  // Request initial data
  requestFullUpdate()
})

onUnmounted(() => {
  // Cleanup is handled by the composable
})
</script>

<style lang="scss" scoped>
.live-service-tracker {
  padding: var(--spacing-4);
  max-width: 1400px;
  margin: 0 auto;
}

.connection-status {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-2) var(--spacing-3);
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-4);
  font-size: var(--font-size-sm);
  
  &.connected {
    background: color-mix(in srgb, var(--color-success) 10%, var(--color-surface-primary));
    border: 1px solid var(--color-success-200);
  }
  
  &.disconnected {
    background: color-mix(in srgb, var(--color-danger) 10%, var(--color-surface-primary));
    border: 1px solid var(--color-danger-200);
  }
  
  &.reconnecting {
    background: color-mix(in srgb, var(--color-warning) 10%, var(--color-surface-primary));
    border: 1px solid var(--color-warning-200);
  }
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  
  &.connected { background: var(--color-success); animation: pulse 2s infinite; }
  &.disconnected { background: var(--color-danger); }
  &.reconnecting { background: var(--color-warning); animation: blink 1s infinite; }
}

.queue-indicator {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  color: var(--color-text-secondary);
}

.tracker-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-6);
  
  .header-left {
    display: flex;
    align-items: center;
    gap: var(--spacing-3);
  }
  
  .tracker-title {
    margin: 0;
    font-size: var(--font-size-2xl);
    font-weight: var(--font-weight-bold);
  }
  
  .live-badge {
    display: flex;
    align-items: center;
    gap: var(--spacing-1);
    padding: var(--spacing-1) var(--spacing-2);
    background: var(--color-primary);
    color: white;
    border-radius: var(--radius-full);
    font-size: var(--font-size-xs);
    font-weight: var(--font-weight-semibold);
    text-transform: uppercase;
  }
  
  .header-controls {
    display: flex;
    gap: var(--spacing-2);
  }
}

.service-orders-grid {
  .grid-container {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
    gap: var(--spacing-4);
  }
}

.service-order-card {
  background: var(--color-surface-primary);
  border: 1px solid var(--color-border-primary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-4);
  position: relative;
  transition: all 0.3s ease;
  
  &.updated {
    animation: cardPulse 0.5s ease;
    border-color: var(--color-primary);
  }
  
  &.critical {
    border-left: 4px solid var(--color-danger);
  }
  
  &.overdue {
    background: color-mix(in srgb, var(--color-warning) 5%, var(--color-surface-primary));
  }
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
}

.order-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-3);
  
  .order-info {
    .order-id {
      margin: 0 0 var(--spacing-1) 0;
      font-size: var(--font-size-lg);
      font-weight: var(--font-weight-bold);
    }
    
    .customer-name {
      color: var(--color-text-secondary);
      font-size: var(--font-size-sm);
    }
  }
  
  .order-status {
    text-align: right;
    
    .status-text {
      display: block;
      padding: var(--spacing-1) var(--spacing-2);
      border-radius: var(--radius-sm);
      font-size: var(--font-size-xs);
      font-weight: var(--font-weight-medium);
      text-transform: uppercase;
      
      &.draft { background: var(--color-gray-100); color: var(--color-gray-700); }
      &.open { background: var(--color-blue-100); color: var(--color-blue-700); }
      &.assigned { background: var(--color-yellow-100); color: var(--color-yellow-700); }
      &.in_progress { background: var(--color-orange-100); color: var(--color-orange-700); }
      &.completed { background: var(--color-green-100); color: var(--color-green-700); }
      &.cancelled { background: var(--color-red-100); color: var(--color-red-700); }
    }
    
    .status-progress {
      width: 60px;
      height: 4px;
      background: var(--color-gray-200);
      border-radius: var(--radius-full);
      margin-top: var(--spacing-1);
      overflow: hidden;
      
      .progress-fill {
        height: 100%;
        background: var(--color-primary);
        border-radius: var(--radius-full);
        transition: width 0.3s ease;
      }
    }
  }
}

.vehicle-info {
  display: flex;
  gap: var(--spacing-3);
  margin-bottom: var(--spacing-3);
  
  .vehicle-image {
    width: 60px;
    height: 40px;
    object-fit: cover;
    border-radius: var(--radius-sm);
    background: var(--color-gray-100);
  }
  
  .vehicle-details {
    flex: 1;
    
    h4 {
      margin: 0 0 var(--spacing-1) 0;
      font-size: var(--font-size-md);
      font-weight: var(--font-weight-semibold);
    }
    
    p {
      margin: 0;
      font-size: var(--font-size-sm);
      color: var(--color-text-secondary);
    }
    
    .mileage {
      font-weight: var(--font-weight-medium);
    }
  }
}

.service-details,
.bay-assignment {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-2);
  margin-bottom: var(--spacing-3);
  
  > div {
    display: flex;
    align-items: center;
    gap: var(--spacing-1);
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
  }
}

.recent-updates {
  margin-bottom: var(--spacing-3);
  
  h5 {
    margin: 0 0 var(--spacing-2) 0;
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-semibold);
    color: var(--color-text-secondary);
  }
  
  .update-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-1);
  }
  
  .update-item {
    display: flex;
    gap: var(--spacing-2);
    font-size: var(--font-size-xs);
    
    .update-time {
      color: var(--color-text-tertiary);
      font-weight: var(--font-weight-medium);
      min-width: 60px;
    }
    
    .update-text {
      color: var(--color-text-secondary);
      flex: 1;
    }
  }
}

.quick-actions {
  display: flex;
  gap: var(--spacing-2);
  flex-wrap: wrap;
}

.update-indicator {
  position: absolute;
  top: var(--spacing-2);
  right: var(--spacing-2);
  width: 24px;
  height: 24px;
  background: var(--color-primary);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: bounce 0.5s ease;
}

.empty-state {
  text-align: center;
  padding: var(--spacing-8);
  color: var(--color-text-secondary);
  
  h3 {
    margin: var(--spacing-4) 0 var(--spacing-2) 0;
    font-size: var(--font-size-xl);
  }
  
  p {
    margin: 0;
    font-size: var(--font-size-lg);
  }
}

// Animations
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0.3; }
}

@keyframes cardPulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.02); }
  100% { transform: scale(1); }
}

@keyframes bounce {
  0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
  40% { transform: translateY(-10px); }
  60% { transform: translateY(-5px); }
}

// Transitions
.service-card-enter-active,
.service-card-leave-active {
  transition: all 0.3s ease;
}

.service-card-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.service-card-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

// RTL support
.rtl {
  .service-order-card.critical {
    border-left: none;
    border-right: 4px solid var(--color-danger);
  }
  
  .order-status {
    text-align: left;
  }
  
  .update-indicator {
    right: auto;
    left: var(--spacing-2);
  }
}

// Responsive design
@media (max-width: 768px) {
  .service-orders-grid .grid-container {
    grid-template-columns: 1fr;
  }
  
  .tracker-header {
    flex-direction: column;
    gap: var(--spacing-3);
    align-items: stretch;
  }
  
  .header-controls {
    justify-content: center;
  }
}
</style>