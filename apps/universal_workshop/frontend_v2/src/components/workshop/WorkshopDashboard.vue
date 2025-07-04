<!--
  WorkshopDashboard Component - Universal Workshop Frontend V2
  
  A comprehensive dashboard layout for workshop management with real-time updates,
  KPI monitoring, and responsive design with Arabic/RTL support.
-->

<template>
  <div :class="dashboardClasses" :dir="isRTL ? 'rtl' : 'ltr'">
    <!-- Dashboard Header -->
    <div class="workshop-dashboard__header">
      <div class="workshop-dashboard__title-section">
        <h1 class="workshop-dashboard__title">
          {{ isRTL ? 'لوحة تحكم الورشة' : 'Workshop Dashboard' }}
        </h1>
        <p class="workshop-dashboard__subtitle">
          {{ getCurrentDateText() }}
        </p>
      </div>
      
      <div class="workshop-dashboard__header-actions">
        <UWButton
          variant="outline"
          size="sm"
          :icon-start="'refresh-cw'"
          @click="handleRefresh"
          :loading="refreshing"
        >
          {{ isRTL ? 'تحديث' : 'Refresh' }}
        </UWButton>
        
        <UWButton
          variant="primary"
          size="sm"
          :icon-start="'plus'"
          @click="handleNewServiceOrder"
        >
          {{ isRTL ? 'طلب خدمة جديد' : 'New Service Order' }}
        </UWButton>
      </div>
    </div>

    <!-- KPI Cards -->
    <div class="workshop-dashboard__kpi-section">
      <div class="workshop-dashboard__kpi-grid">
        <div 
          v-for="kpi in kpiMetrics" 
          :key="kpi.id"
          class="workshop-dashboard__kpi-card"
          :class="`workshop-dashboard__kpi-card--${kpi.trend}`"
        >
          <div class="workshop-dashboard__kpi-icon">
            <UWIcon :name="kpi.icon" size="lg" :color="kpi.iconColor" />
          </div>
          
          <div class="workshop-dashboard__kpi-content">
            <div class="workshop-dashboard__kpi-value">
              {{ formatKpiValue(kpi.value, kpi.type) }}
            </div>
            <div class="workshop-dashboard__kpi-label">
              {{ isRTL && kpi.labelAr ? kpi.labelAr : kpi.label }}
            </div>
            
            <div v-if="kpi.change" class="workshop-dashboard__kpi-change">
              <UWIcon 
                :name="kpi.trend === 'up' ? 'trending-up' : kpi.trend === 'down' ? 'trending-down' : 'minus'"
                size="sm"
              />
              <span>{{ Math.abs(kpi.change) }}%</span>
              <span class="workshop-dashboard__kpi-period">
                {{ isRTL ? 'من الأمس' : 'from yesterday' }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content Grid -->
    <div class="workshop-dashboard__main-content">
      <!-- Left Column -->
      <div class="workshop-dashboard__left-column">
        <!-- Active Service Orders -->
        <div class="workshop-dashboard__section">
          <div class="workshop-dashboard__section-header">
            <h2 class="workshop-dashboard__section-title">
              {{ isRTL ? 'طلبات الخدمة النشطة' : 'Active Service Orders' }}
            </h2>
            <div class="workshop-dashboard__section-actions">
              <UWSelect
                v-model="serviceOrderFilter"
                :options="serviceOrderFilters"
                size="sm"
                clearable
                placeholder="Filter"
              />
              <UWButton
                variant="ghost"
                size="sm"
                :icon-start="'eye'"
                @click="handleViewAllOrders"
              >
                {{ isRTL ? 'عرض الكل' : 'View All' }}
              </UWButton>
            </div>
          </div>
          
          <div class="workshop-dashboard__service-orders">
            <div v-if="loading.serviceOrders" class="workshop-dashboard__loading">
              <UWIcon name="loading" spin size="lg" />
              <span>{{ isRTL ? 'جاري التحميل...' : 'Loading...' }}</span>
            </div>
            
            <div v-else-if="filteredServiceOrders.length === 0" class="workshop-dashboard__empty">
              <UWIcon name="clipboard" size="lg" color="var(--color-text-tertiary)" />
              <span>{{ isRTL ? 'لا توجد طلبات خدمة نشطة' : 'No active service orders' }}</span>
            </div>
            
            <div v-else class="workshop-dashboard__orders-list">
              <UWServiceOrderCard
                v-for="order in filteredServiceOrders.slice(0, 5)"
                :key="order.id"
                v-bind="order"
                size="sm"
                variant="compact"
                @click="handleOrderClick(order)"
                @edit="handleOrderEdit(order)"
                @action="handleOrderAction(order, $event)"
              />
            </div>
          </div>
        </div>

        <!-- Service Bay Status -->
        <div class="workshop-dashboard__section">
          <div class="workshop-dashboard__section-header">
            <h2 class="workshop-dashboard__section-title">
              {{ isRTL ? 'حالة أماكن الخدمة' : 'Service Bay Status' }}
            </h2>
          </div>
          
          <div class="workshop-dashboard__service-bays">
            <div 
              v-for="bay in serviceBays" 
              :key="bay.id"
              class="workshop-dashboard__bay-card"
              :class="`workshop-dashboard__bay-card--${bay.status}`"
              @click="handleBayClick(bay)"
            >
              <div class="workshop-dashboard__bay-number">
                {{ isRTL ? `المكان ${bay.number}` : `Bay ${bay.number}` }}
              </div>
              
              <div class="workshop-dashboard__bay-status">
                <UWBadge 
                  :content="getBayStatusText(bay.status)"
                  :variant="getBayStatusVariant(bay.status)"
                  size="xs"
                />
              </div>
              
              <div v-if="bay.currentOrder" class="workshop-dashboard__bay-order">
                <div class="workshop-dashboard__bay-order-number">
                  {{ bay.currentOrder.orderNumber }}
                </div>
                <div class="workshop-dashboard__bay-vehicle">
                  {{ bay.currentOrder.vehicle?.make }} {{ bay.currentOrder.vehicle?.model }}
                </div>
                <div v-if="bay.estimatedCompletion" class="workshop-dashboard__bay-completion">
                  <UWIcon name="clock" size="xs" />
                  {{ formatTimeRemaining(bay.estimatedCompletion) }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Column -->
      <div class="workshop-dashboard__right-column">
        <!-- Technician Availability -->
        <div class="workshop-dashboard__section">
          <div class="workshop-dashboard__section-header">
            <h2 class="workshop-dashboard__section-title">
              {{ isRTL ? 'حالة الفنيين' : 'Technician Status' }}
            </h2>
          </div>
          
          <div class="workshop-dashboard__technicians">
            <div 
              v-for="technician in availableTechnicians" 
              :key="technician.id"
              class="workshop-dashboard__technician-item"
              @click="handleTechnicianClick(technician)"
            >
              <UWAvatar 
                :user="technician" 
                :status="technician.status"
                size="sm"
              />
              <div class="workshop-dashboard__technician-info">
                <div class="workshop-dashboard__technician-name">
                  {{ isRTL && technician.nameAr ? technician.nameAr : technician.name }}
                </div>
                <div class="workshop-dashboard__technician-workload">
                  {{ technician.currentJobs || 0 }}/{{ technician.maxJobs || 5 }} 
                  {{ isRTL ? 'مهام' : 'jobs' }}
                </div>
              </div>
              <div class="workshop-dashboard__technician-status">
                <UWBadge 
                  :content="getTechnicianStatusText(technician.status)"
                  :variant="getTechnicianStatusVariant(technician.status)"
                  size="xs"
                />
              </div>
            </div>
          </div>
        </div>

        <!-- Parts Inventory Alerts -->
        <div class="workshop-dashboard__section">
          <div class="workshop-dashboard__section-header">
            <h2 class="workshop-dashboard__section-title">
              {{ isRTL ? 'تنبيهات المخزون' : 'Inventory Alerts' }}
            </h2>
            <UWButton
              variant="ghost"
              size="sm"
              :icon-start="'package'"
              @click="handleViewInventory"
            >
              {{ isRTL ? 'المخزون' : 'Inventory' }}
            </UWButton>
          </div>
          
          <div class="workshop-dashboard__inventory-alerts">
            <div v-if="loading.inventory" class="workshop-dashboard__loading">
              <UWIcon name="loading" spin />
            </div>
            
            <div v-else-if="inventoryAlerts.length === 0" class="workshop-dashboard__no-alerts">
              <UWIcon name="check-circle" size="md" color="var(--color-success)" />
              <span>{{ isRTL ? 'لا توجد تنبيهات' : 'No alerts' }}</span>
            </div>
            
            <div v-else class="workshop-dashboard__alerts-list">
              <div 
                v-for="alert in inventoryAlerts.slice(0, 5)" 
                :key="alert.id"
                class="workshop-dashboard__alert-item"
                :class="`workshop-dashboard__alert-item--${alert.severity}`"
              >
                <UWIcon 
                  :name="getAlertIcon(alert.severity)" 
                  size="sm" 
                  :color="getAlertColor(alert.severity)"
                />
                <div class="workshop-dashboard__alert-content">
                  <div class="workshop-dashboard__alert-title">
                    {{ isRTL && alert.titleAr ? alert.titleAr : alert.title }}
                  </div>
                  <div class="workshop-dashboard__alert-message">
                    {{ isRTL && alert.messageAr ? alert.messageAr : alert.message }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Recent Activity -->
        <div class="workshop-dashboard__section">
          <div class="workshop-dashboard__section-header">
            <h2 class="workshop-dashboard__section-title">
              {{ isRTL ? 'النشاط الأخير' : 'Recent Activity' }}
            </h2>
          </div>
          
          <div class="workshop-dashboard__activity-feed">
            <div 
              v-for="activity in recentActivities.slice(0, 8)" 
              :key="activity.id"
              class="workshop-dashboard__activity-item"
            >
              <div class="workshop-dashboard__activity-icon">
                <UWIcon :name="getActivityIcon(activity.type)" size="sm" />
              </div>
              <div class="workshop-dashboard__activity-content">
                <div class="workshop-dashboard__activity-message">
                  {{ isRTL && activity.messageAr ? activity.messageAr : activity.message }}
                </div>
                <div class="workshop-dashboard__activity-time">
                  {{ formatRelativeTime(activity.timestamp) }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, inject, onMounted, onUnmounted } from 'vue'
import { UWButton } from '@/components/base'
import { UWIcon, UWBadge, UWAvatar } from '@/components/primitives'
import { UWSelect } from '@/components/forms'
import { UWServiceOrderCard } from './'

// Types
interface KpiMetric {
  id: string
  label: string
  labelAr?: string
  value: number
  type: 'number' | 'currency' | 'percentage'
  icon: string
  iconColor: string
  trend: 'up' | 'down' | 'stable'
  change?: number
}

interface ServiceBay {
  id: string
  number: number
  status: 'available' | 'occupied' | 'maintenance' | 'reserved'
  currentOrder?: any
  estimatedCompletion?: string | Date
}

interface Technician {
  id: string
  name: string
  nameAr?: string
  status: 'available' | 'busy' | 'offline' | 'break'
  currentJobs?: number
  maxJobs?: number
  avatar?: string
}

interface InventoryAlert {
  id: string
  title: string
  titleAr?: string
  message: string
  messageAr?: string
  severity: 'low' | 'medium' | 'high' | 'critical'
}

interface Activity {
  id: string
  type: string
  message: string
  messageAr?: string
  timestamp: string | Date
}

export interface WorkshopDashboardProps {
  kpiMetrics?: KpiMetric[]
  serviceOrders?: any[]
  serviceBays?: ServiceBay[]
  technicians?: Technician[]
  inventoryAlerts?: InventoryAlert[]
  recentActivities?: Activity[]
  loading?: {
    serviceOrders?: boolean
    inventory?: boolean
    kpis?: boolean
  }
  refreshInterval?: number
  autoRefresh?: boolean
}

export interface WorkshopDashboardEmits {
  'refresh': []
  'new-service-order': []
  'order-click': [order: any]
  'order-edit': [order: any]
  'order-action': [order: any, action: string]
  'bay-click': [bay: ServiceBay]
  'technician-click': [technician: Technician]
  'view-all-orders': []
  'view-inventory': []
}

const props = withDefaults(defineProps<WorkshopDashboardProps>(), {
  kpiMetrics: () => [],
  serviceOrders: () => [],
  serviceBays: () => [],
  technicians: () => [],
  inventoryAlerts: () => [],
  recentActivities: () => [],
  loading: () => ({}),
  refreshInterval: 30000, // 30 seconds
  autoRefresh: true
})

const emit = defineEmits<WorkshopDashboardEmits>()

// Injected context
const isRTL = inject('isRTL', false)

// Local state
const refreshing = ref(false)
const serviceOrderFilter = ref('')
const refreshTimer = ref<number | null>(null)

// Filter options
const serviceOrderFilters = [
  { label: 'All', labelAr: 'الكل', value: '' },
  { label: 'High Priority', labelAr: 'أولوية عالية', value: 'high' },
  { label: 'In Progress', labelAr: 'قيد التنفيذ', value: 'in_progress' },
  { label: 'Pending', labelAr: 'في الانتظار', value: 'pending' }
]

// Computed properties
const dashboardClasses = computed(() => [
  'workshop-dashboard',
  {
    'workshop-dashboard--rtl': isRTL,
    'workshop-dashboard--refreshing': refreshing.value
  }
])

const filteredServiceOrders = computed(() => {
  if (!serviceOrderFilter.value) return props.serviceOrders
  
  return props.serviceOrders.filter(order => {
    switch (serviceOrderFilter.value) {
      case 'high':
        return order.priority === 'high' || order.priority === 'urgent'
      case 'in_progress':
        return order.status === 'in_progress'
      case 'pending':
        return order.status === 'pending'
      default:
        return true
    }
  })
})

const availableTechnicians = computed(() => {
  return props.technicians.slice(0, 6) // Show top 6
})

// Methods
const getCurrentDateText = () => {
  const now = new Date()
  if (isRTL) {
    return now.toLocaleDateString('ar-SA', { 
      weekday: 'long', 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    })
  }
  return now.toLocaleDateString('en-US', { 
    weekday: 'long', 
    year: 'numeric', 
    month: 'long', 
    day: 'numeric' 
  })
}

const formatKpiValue = (value: number, type: string) => {
  switch (type) {
    case 'currency':
      return new Intl.NumberFormat(isRTL ? 'ar-OM' : 'en-OM', {
        style: 'currency',
        currency: 'OMR'
      }).format(value)
    case 'percentage':
      return `${value}%`
    default:
      return new Intl.NumberFormat(isRTL ? 'ar-OM' : 'en-OM').format(value)
  }
}

const getBayStatusText = (status: string) => {
  const statusMap = {
    available: { en: 'Available', ar: 'متاح' },
    occupied: { en: 'Occupied', ar: 'مشغول' },
    maintenance: { en: 'Maintenance', ar: 'صيانة' },
    reserved: { en: 'Reserved', ar: 'محجوز' }
  }
  
  const statusObj = statusMap[status as keyof typeof statusMap]
  return statusObj ? (isRTL ? statusObj.ar : statusObj.en) : status
}

const getBayStatusVariant = (status: string) => {
  const variantMap = {
    available: 'success',
    occupied: 'primary',
    maintenance: 'warning',
    reserved: 'secondary'
  }
  
  return variantMap[status as keyof typeof variantMap] || 'default'
}

const getTechnicianStatusText = (status: string) => {
  const statusMap = {
    available: { en: 'Available', ar: 'متاح' },
    busy: { en: 'Busy', ar: 'مشغول' },
    offline: { en: 'Offline', ar: 'غير متصل' },
    break: { en: 'Break', ar: 'استراحة' }
  }
  
  const statusObj = statusMap[status as keyof typeof statusMap]
  return statusObj ? (isRTL ? statusObj.ar : statusObj.en) : status
}

const getTechnicianStatusVariant = (status: string) => {
  const variantMap = {
    available: 'success',
    busy: 'warning',
    offline: 'error',
    break: 'secondary'
  }
  
  return variantMap[status as keyof typeof variantMap] || 'default'
}

const getAlertIcon = (severity: string) => {
  const iconMap = {
    low: 'info',
    medium: 'alert-circle',
    high: 'alert-triangle',
    critical: 'alert-octagon'
  }
  
  return iconMap[severity as keyof typeof iconMap] || 'info'
}

const getAlertColor = (severity: string) => {
  const colorMap = {
    low: 'var(--color-primary)',
    medium: 'var(--color-warning)',
    high: 'var(--color-error)',
    critical: 'var(--color-error)'
  }
  
  return colorMap[severity as keyof typeof colorMap] || 'var(--color-primary)'
}

const getActivityIcon = (type: string) => {
  const iconMap: Record<string, string> = {
    'order_created': 'plus',
    'order_completed': 'check',
    'technician_assigned': 'user-plus',
    'part_ordered': 'package',
    'payment_received': 'credit-card',
    'vehicle_arrived': 'car',
    'inspection_completed': 'search'
  }
  
  return iconMap[type] || 'activity'
}

const formatTimeRemaining = (completion: string | Date) => {
  const now = new Date()
  const target = new Date(completion)
  const diff = target.getTime() - now.getTime()
  
  if (diff <= 0) {
    return isRTL ? 'متأخر' : 'Overdue'
  }
  
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
  
  if (isRTL) {
    if (hours > 0) {
      return `${hours} ساعة ${minutes} دقيقة`
    }
    return `${minutes} دقيقة`
  }
  
  if (hours > 0) {
    return `${hours}h ${minutes}m`
  }
  return `${minutes}m`
}

const formatRelativeTime = (timestamp: string | Date) => {
  const now = new Date()
  const time = new Date(timestamp)
  const diff = now.getTime() - time.getTime()
  
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  
  if (isRTL) {
    if (days > 0) return `منذ ${days} يوم`
    if (hours > 0) return `منذ ${hours} ساعة`
    if (minutes > 0) return `منذ ${minutes} دقيقة`
    return 'الآن'
  }
  
  if (days > 0) return `${days}d ago`
  if (hours > 0) return `${hours}h ago`
  if (minutes > 0) return `${minutes}m ago`
  return 'now'
}

// Event handlers
const handleRefresh = async () => {
  refreshing.value = true
  try {
    emit('refresh')
    // Simulate refresh delay
    await new Promise(resolve => setTimeout(resolve, 1000))
  } finally {
    refreshing.value = false
  }
}

const handleNewServiceOrder = () => {
  emit('new-service-order')
}

const handleOrderClick = (order: any) => {
  emit('order-click', order)
}

const handleOrderEdit = (order: any) => {
  emit('order-edit', order)
}

const handleOrderAction = (order: any, action: string) => {
  emit('order-action', order, action)
}

const handleBayClick = (bay: ServiceBay) => {
  emit('bay-click', bay)
}

const handleTechnicianClick = (technician: Technician) => {
  emit('technician-click', technician)
}

const handleViewAllOrders = () => {
  emit('view-all-orders')
}

const handleViewInventory = () => {
  emit('view-inventory')
}

// Auto-refresh functionality
const startAutoRefresh = () => {
  if (props.autoRefresh && props.refreshInterval > 0) {
    refreshTimer.value = window.setInterval(() => {
      if (!refreshing.value) {
        handleRefresh()
      }
    }, props.refreshInterval)
  }
}

const stopAutoRefresh = () => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
    refreshTimer.value = null
  }
}

// Lifecycle
onMounted(() => {
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style lang="scss" scoped>
.workshop-dashboard {
  --dashboard-padding: var(--spacing-6);
  --dashboard-gap: var(--spacing-6);
  --section-padding: var(--spacing-4);
  --section-border-radius: var(--radius-lg);
  
  padding: var(--dashboard-padding);
  background: var(--color-background);
  min-height: 100vh;
  
  // RTL support
  &--rtl {
    direction: rtl;
    text-align: right;
  }
  
  &--refreshing {
    opacity: 0.9;
  }
}

.workshop-dashboard__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--dashboard-gap);
}

.workshop-dashboard__title {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin: 0 0 var(--spacing-1) 0;
}

.workshop-dashboard__subtitle {
  font-size: var(--font-size-lg);
  color: var(--color-text-secondary);
  margin: 0;
}

.workshop-dashboard__header-actions {
  display: flex;
  gap: var(--spacing-3);
}

.workshop-dashboard__kpi-section {
  margin-bottom: var(--dashboard-gap);
}

.workshop-dashboard__kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--spacing-4);
}

.workshop-dashboard__kpi-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
  padding: var(--section-padding);
  background: var(--color-background-elevated);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--section-border-radius);
  box-shadow: var(--shadow-sm);
  
  &--up {
    border-left: 4px solid var(--color-success);
    
    .workshop-dashboard--rtl & {
      border-left: none;
      border-right: 4px solid var(--color-success);
    }
  }
  
  &--down {
    border-left: 4px solid var(--color-error);
    
    .workshop-dashboard--rtl & {
      border-left: none;
      border-right: 4px solid var(--color-error);
    }
  }
  
  &--stable {
    border-left: 4px solid var(--color-warning);
    
    .workshop-dashboard--rtl & {
      border-left: none;
      border-right: 4px solid var(--color-warning);
    }
  }
}

.workshop-dashboard__kpi-content {
  flex: 1;
}

.workshop-dashboard__kpi-value {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-1);
}

.workshop-dashboard__kpi-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-2);
}

.workshop-dashboard__kpi-change {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  font-size: var(--font-size-sm);
  color: var(--color-text-tertiary);
}

.workshop-dashboard__main-content {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: var(--dashboard-gap);
}

.workshop-dashboard__section {
  background: var(--color-background-elevated);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--section-border-radius);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  
  &:not(:last-child) {
    margin-bottom: var(--spacing-4);
  }
}

.workshop-dashboard__section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--section-padding);
  border-bottom: 1px solid var(--color-border-subtle);
  background: var(--color-background-subtle);
}

.workshop-dashboard__section-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0;
}

.workshop-dashboard__section-actions {
  display: flex;
  gap: var(--spacing-2);
  align-items: center;
}

.workshop-dashboard__loading,
.workshop-dashboard__empty,
.workshop-dashboard__no-alerts {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-8);
  color: var(--color-text-secondary);
  gap: var(--spacing-2);
}

.workshop-dashboard__orders-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
  padding: var(--section-padding);
}

.workshop-dashboard__service-bays {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--spacing-3);
  padding: var(--section-padding);
}

.workshop-dashboard__bay-card {
  padding: var(--spacing-3);
  background: var(--color-background-subtle);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    box-shadow: var(--shadow-md);
  }
  
  &--available {
    border-left: 3px solid var(--color-success);
    
    .workshop-dashboard--rtl & {
      border-left: none;
      border-right: 3px solid var(--color-success);
    }
  }
  
  &--occupied {
    border-left: 3px solid var(--color-primary);
    
    .workshop-dashboard--rtl & {
      border-left: none;
      border-right: 3px solid var(--color-primary);
    }
  }
  
  &--maintenance {
    border-left: 3px solid var(--color-warning);
    
    .workshop-dashboard--rtl & {
      border-left: none;
      border-right: 3px solid var(--color-warning);
    }
  }
  
  &--reserved {
    border-left: 3px solid var(--color-secondary);
    
    .workshop-dashboard--rtl & {
      border-left: none;
      border-right: 3px solid var(--color-secondary);
    }
  }
}

.workshop-dashboard__bay-number {
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-1);
}

.workshop-dashboard__bay-status {
  margin-bottom: var(--spacing-2);
}

.workshop-dashboard__bay-order {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.workshop-dashboard__bay-order-number {
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-1);
}

.workshop-dashboard__bay-completion {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  margin-top: var(--spacing-1);
}

.workshop-dashboard__technicians {
  padding: var(--section-padding);
}

.workshop-dashboard__technician-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  padding: var(--spacing-2);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background-color 0.2s ease;
  
  &:hover {
    background: var(--color-background-subtle);
  }
  
  &:not(:last-child) {
    margin-bottom: var(--spacing-2);
  }
}

.workshop-dashboard__technician-info {
  flex: 1;
}

.workshop-dashboard__technician-name {
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-1);
}

.workshop-dashboard__technician-workload {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.workshop-dashboard__inventory-alerts {
  padding: var(--section-padding);
}

.workshop-dashboard__alerts-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.workshop-dashboard__alert-item {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-2);
  padding: var(--spacing-2);
  border-radius: var(--radius-sm);
  
  &--critical {
    background: var(--color-error-background);
  }
  
  &--high {
    background: var(--color-warning-background);
  }
}

.workshop-dashboard__alert-content {
  flex: 1;
}

.workshop-dashboard__alert-title {
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  margin-bottom: var(--spacing-1);
}

.workshop-dashboard__alert-message {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.workshop-dashboard__activity-feed {
  padding: var(--section-padding);
  max-height: 400px;
  overflow-y: auto;
}

.workshop-dashboard__activity-item {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-2);
  padding: var(--spacing-2) 0;
  
  &:not(:last-child) {
    border-bottom: 1px solid var(--color-border-subtle);
  }
}

.workshop-dashboard__activity-icon {
  flex-shrink: 0;
  margin-top: var(--spacing-1);
}

.workshop-dashboard__activity-content {
  flex: 1;
}

.workshop-dashboard__activity-message {
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-1);
}

.workshop-dashboard__activity-time {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

// Responsive design
@media (max-width: 1200px) {
  .workshop-dashboard__main-content {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .workshop-dashboard {
    --dashboard-padding: var(--spacing-4);
    --dashboard-gap: var(--spacing-4);
  }
  
  .workshop-dashboard__header {
    flex-direction: column;
    gap: var(--spacing-3);
  }
  
  .workshop-dashboard__header-actions {
    align-self: stretch;
    justify-content: space-between;
  }
  
  .workshop-dashboard__kpi-grid {
    grid-template-columns: 1fr;
    gap: var(--spacing-3);
  }
  
  .workshop-dashboard__service-bays {
    grid-template-columns: 1fr;
  }
  
  .workshop-dashboard__section-header {
    flex-direction: column;
    gap: var(--spacing-2);
    align-items: stretch;
  }
}
</style>