<!--
  ServiceBayStatus Component - Universal Workshop Frontend V2
  
  A comprehensive component for displaying and managing service bay status
  with real-time updates, occupancy tracking, and workflow management.
-->

<template>
  <div :class="bayStatusClasses" :dir="isRTL ? 'rtl' : 'ltr'">
    <!-- Component Header -->
    <div v-if="showHeader" class="service-bay-status__header">
      <h3 class="service-bay-status__title">
        {{ isRTL ? 'حالة أماكن الخدمة' : 'Service Bay Status' }}
      </h3>
      <div class="service-bay-status__header-actions">
        <UWButton
          variant="outline"
          size="sm"
          :icon-start="'refresh-cw'"
          @click="handleRefresh"
          :loading="refreshing"
        >
          {{ isRTL ? 'تحديث' : 'Refresh' }}
        </UWButton>
        
        <UWSelect
          v-model="filterStatus"
          :options="statusFilterOptions"
          size="sm"
          clearable
          :placeholder="isRTL ? 'تصفية حسب الحالة' : 'Filter by status'"
        />
      </div>
    </div>

    <!-- Bay Grid -->
    <div class="service-bay-status__grid">
      <div
        v-for="bay in filteredBays"
        :key="bay.id"
        class="service-bay-status__bay-card"
        :class="[
          `service-bay-status__bay-card--${bay.status}`,
          {
            'service-bay-status__bay-card--selected': selectedBay?.id === bay.id,
            'service-bay-status__bay-card--overdue': isBayOverdue(bay),
            'service-bay-status__bay-card--urgent': bay.priority === 'urgent'
          }
        ]"
        @click="handleBayClick(bay)"
      >
        <!-- Bay Number & Status -->
        <div class="service-bay-status__bay-header">
          <div class="service-bay-status__bay-number">
            {{ isRTL ? `المكان ${bay.number}` : `Bay ${bay.number}` }}
          </div>
          
          <div class="service-bay-status__bay-status-indicator">
            <UWBadge 
              :content="getBayStatusText(bay.status)"
              :variant="getBayStatusVariant(bay.status)"
              size="sm"
              :dot="true"
            />
          </div>
        </div>

        <!-- Bay Type & Capacity -->
        <div v-if="bay.type || bay.capacity" class="service-bay-status__bay-info">
          <div v-if="bay.type" class="service-bay-status__bay-type">
            <UWIcon :name="getBayTypeIcon(bay.type)" size="sm" />
            <span>{{ getBayTypeText(bay.type) }}</span>
          </div>
          
          <div v-if="bay.capacity" class="service-bay-status__bay-capacity">
            {{ isRTL ? 'السعة:' : 'Capacity:' }} {{ bay.capacity }}
          </div>
        </div>

        <!-- Current Service Order -->
        <div v-if="bay.currentOrder" class="service-bay-status__current-order">
          <div class="service-bay-status__order-header">
            <div class="service-bay-status__order-number">
              {{ bay.currentOrder.orderNumber }}
            </div>
            <div v-if="bay.currentOrder.priority" class="service-bay-status__order-priority">
              <UWIcon 
                :name="getPriorityIcon(bay.currentOrder.priority)" 
                size="xs"
                :color="getPriorityColor(bay.currentOrder.priority)"
              />
            </div>
          </div>
          
          <div class="service-bay-status__vehicle-info">
            <UWIcon name="car" size="sm" />
            <span>
              {{ bay.currentOrder.vehicle?.make }} {{ bay.currentOrder.vehicle?.model }}
            </span>
          </div>
          
          <div v-if="bay.currentOrder.customer" class="service-bay-status__customer-info">
            <UWAvatar 
              :user="bay.currentOrder.customer" 
              size="xs"
            />
            <span>
              {{ isRTL && bay.currentOrder.customer.nameAr 
                ? bay.currentOrder.customer.nameAr 
                : bay.currentOrder.customer.name }}
            </span>
          </div>
          
          <div v-if="bay.currentOrder.serviceType" class="service-bay-status__service-type">
            <UWIcon :name="getServiceTypeIcon(bay.currentOrder.serviceType)" size="sm" />
            <span>{{ getServiceTypeText(bay.currentOrder.serviceType) }}</span>
          </div>
        </div>

        <!-- Technician Assignment -->
        <div v-if="bay.assignedTechnician" class="service-bay-status__technician">
          <div class="service-bay-status__technician-header">
            <span class="service-bay-status__technician-label">
              {{ isRTL ? 'الفني:' : 'Technician:' }}
            </span>
          </div>
          
          <div class="service-bay-status__technician-info">
            <UWAvatar 
              :user="bay.assignedTechnician" 
              :status="bay.assignedTechnician.status"
              size="xs"
            />
            <span>
              {{ isRTL && bay.assignedTechnician.nameAr 
                ? bay.assignedTechnician.nameAr 
                : bay.assignedTechnician.name }}
            </span>
          </div>
        </div>

        <!-- Timeline Information -->
        <div v-if="bay.timeline" class="service-bay-status__timeline">
          <div v-if="bay.timeline.startTime" class="service-bay-status__timeline-item">
            <UWIcon name="play" size="xs" />
            <span>
              {{ isRTL ? 'البداية:' : 'Started:' }} 
              {{ formatTime(bay.timeline.startTime) }}
            </span>
          </div>
          
          <div v-if="bay.timeline.estimatedCompletion" class="service-bay-status__timeline-item">
            <UWIcon name="clock" size="xs" />
            <span>
              {{ isRTL ? 'المتوقع:' : 'Est:' }} 
              {{ formatTime(bay.timeline.estimatedCompletion) }}
            </span>
          </div>
          
          <div v-if="bay.timeline.actualCompletion" class="service-bay-status__timeline-item">
            <UWIcon name="check" size="xs" />
            <span>
              {{ isRTL ? 'اكتمل:' : 'Completed:' }} 
              {{ formatTime(bay.timeline.actualCompletion) }}
            </span>
          </div>
        </div>

        <!-- Progress Bar -->
        <div v-if="bay.progress !== undefined && bay.status === 'occupied'" class="service-bay-status__progress">
          <div class="service-bay-status__progress-header">
            <span class="service-bay-status__progress-label">
              {{ isRTL ? 'التقدم:' : 'Progress:' }}
            </span>
            <span class="service-bay-status__progress-percentage">
              {{ bay.progress }}%
            </span>
          </div>
          
          <div class="service-bay-status__progress-bar">
            <div 
              class="service-bay-status__progress-fill"
              :style="{ width: `${bay.progress}%` }"
              :class="{
                'service-bay-status__progress-fill--complete': bay.progress >= 100,
                'service-bay-status__progress-fill--high': bay.progress >= 75,
                'service-bay-status__progress-fill--medium': bay.progress >= 50
              }"
            ></div>
          </div>
        </div>

        <!-- Available Bay Information -->
        <div v-if="bay.status === 'available'" class="service-bay-status__available-info">
          <UWIcon name="check-circle" size="md" color="var(--color-success)" />
          <span class="service-bay-status__available-text">
            {{ isRTL ? 'متاح للخدمة' : 'Ready for Service' }}
          </span>
          
          <div v-if="bay.nextScheduled" class="service-bay-status__next-scheduled">
            <UWIcon name="calendar" size="xs" />
            <span>
              {{ isRTL ? 'التالي:' : 'Next:' }} 
              {{ formatTime(bay.nextScheduled) }}
            </span>
          </div>
        </div>

        <!-- Maintenance Information -->
        <div v-if="bay.status === 'maintenance'" class="service-bay-status__maintenance-info">
          <UWIcon name="wrench" size="md" color="var(--color-warning)" />
          <span class="service-bay-status__maintenance-text">
            {{ isRTL ? 'قيد الصيانة' : 'Under Maintenance' }}
          </span>
          
          <div v-if="bay.maintenanceType" class="service-bay-status__maintenance-type">
            {{ getBayMaintenanceText(bay.maintenanceType) }}
          </div>
          
          <div v-if="bay.maintenanceUntil" class="service-bay-status__maintenance-until">
            <UWIcon name="clock" size="xs" />
            <span>
              {{ isRTL ? 'حتى:' : 'Until:' }} 
              {{ formatTime(bay.maintenanceUntil) }}
            </span>
          </div>
        </div>

        <!-- Action Buttons -->
        <div v-if="showActions" class="service-bay-status__actions">
          <UWButton
            v-if="bay.status === 'available' && canAssign"
            variant="primary"
            size="xs"
            :icon-start="'plus'"
            @click.stop="handleAssignOrder(bay)"
          >
            {{ isRTL ? 'تعيين' : 'Assign' }}
          </UWButton>
          
          <UWButton
            v-if="bay.status === 'occupied' && canComplete"
            variant="success"
            size="xs"
            :icon-start="'check'"
            @click.stop="handleCompleteOrder(bay)"
          >
            {{ isRTL ? 'إكمال' : 'Complete' }}
          </UWButton>
          
          <UWButton
            v-if="bay.status === 'maintenance' && canEndMaintenance"
            variant="warning"
            size="xs"
            :icon-start="'tool'"
            @click.stop="handleEndMaintenance(bay)"
          >
            {{ isRTL ? 'إنهاء الصيانة' : 'End Maintenance' }}
          </UWButton>
          
          <UWButton
            variant="ghost"
            size="xs"
            :icon-start="'more-horizontal'"
            @click.stop="handleMoreActions(bay)"
          >
            {{ isRTL ? 'المزيد' : 'More' }}
          </UWButton>
        </div>
      </div>
    </div>

    <!-- Summary Statistics -->
    <div v-if="showSummary" class="service-bay-status__summary">
      <div class="service-bay-status__summary-item">
        <div class="service-bay-status__summary-value">
          {{ baysSummary.available }}
        </div>
        <div class="service-bay-status__summary-label">
          {{ isRTL ? 'متاح' : 'Available' }}
        </div>
      </div>
      
      <div class="service-bay-status__summary-item">
        <div class="service-bay-status__summary-value">
          {{ baysSummary.occupied }}
        </div>
        <div class="service-bay-status__summary-label">
          {{ isRTL ? 'مشغول' : 'Occupied' }}
        </div>
      </div>
      
      <div class="service-bay-status__summary-item">
        <div class="service-bay-status__summary-value">
          {{ baysSummary.maintenance }}
        </div>
        <div class="service-bay-status__summary-label">
          {{ isRTL ? 'صيانة' : 'Maintenance' }}
        </div>
      </div>
      
      <div class="service-bay-status__summary-item">
        <div class="service-bay-status__summary-value">
          {{ Math.round(baysSummary.utilization) }}%
        </div>
        <div class="service-bay-status__summary-label">
          {{ isRTL ? 'معدل الاستخدام' : 'Utilization' }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, inject } from 'vue'
import { UWButton } from '@/components/base'
import { UWIcon, UWBadge, UWAvatar } from '@/components/primitives'
import { UWSelect } from '@/components/forms'

// Types
interface ServiceBay {
  id: string
  number: number
  status: 'available' | 'occupied' | 'maintenance' | 'reserved' | 'out_of_order'
  type?: 'standard' | 'heavy_duty' | 'quick_service' | 'inspection'
  capacity?: string
  priority?: 'low' | 'medium' | 'high' | 'urgent'
  currentOrder?: {
    id: string
    orderNumber: string
    priority?: 'low' | 'medium' | 'high' | 'urgent'
    serviceType?: string
    vehicle?: {
      make: string
      model: string
      plateNumber: string
    }
    customer?: {
      name: string
      nameAr?: string
      avatar?: string
    }
  }
  assignedTechnician?: {
    id: string
    name: string
    nameAr?: string
    status: 'available' | 'busy' | 'offline'
    avatar?: string
  }
  timeline?: {
    startTime?: string | Date
    estimatedCompletion?: string | Date
    actualCompletion?: string | Date
  }
  progress?: number // 0-100
  nextScheduled?: string | Date
  maintenanceType?: 'preventive' | 'corrective' | 'cleaning'
  maintenanceUntil?: string | Date
}

export interface ServiceBayStatusProps {
  bays: ServiceBay[]
  selectedBay?: ServiceBay | null
  showHeader?: boolean
  showActions?: boolean
  showSummary?: boolean
  canAssign?: boolean
  canComplete?: boolean
  canEndMaintenance?: boolean
  refreshing?: boolean
  layout?: 'grid' | 'list'
  size?: 'sm' | 'md' | 'lg'
}

export interface ServiceBayStatusEmits {
  'bay-click': [bay: ServiceBay]
  'assign-order': [bay: ServiceBay]
  'complete-order': [bay: ServiceBay]
  'end-maintenance': [bay: ServiceBay]
  'more-actions': [bay: ServiceBay]
  'refresh': []
}

const props = withDefaults(defineProps<ServiceBayStatusProps>(), {
  showHeader: true,
  showActions: true,
  showSummary: true,
  canAssign: true,
  canComplete: true,
  canEndMaintenance: true,
  refreshing: false,
  layout: 'grid',
  size: 'md',
  bays: () => []
})

const emit = defineEmits<ServiceBayStatusEmits>()

// Injected context
const isRTL = inject('isRTL', false)

// Local state
const filterStatus = ref('')

// Filter options
const statusFilterOptions = [
  { label: 'All Status', labelAr: 'جميع الحالات', value: '' },
  { label: 'Available', labelAr: 'متاح', value: 'available' },
  { label: 'Occupied', labelAr: 'مشغول', value: 'occupied' },
  { label: 'Maintenance', labelAr: 'صيانة', value: 'maintenance' },
  { label: 'Reserved', labelAr: 'محجوز', value: 'reserved' }
]

// Computed properties
const bayStatusClasses = computed(() => [
  'service-bay-status',
  `service-bay-status--${props.layout}`,
  `service-bay-status--${props.size}`,
  {
    'service-bay-status--rtl': isRTL
  }
])

const filteredBays = computed(() => {
  if (!filterStatus.value) return props.bays
  
  return props.bays.filter(bay => bay.status === filterStatus.value)
})

const baysSummary = computed(() => {
  const summary = {
    available: 0,
    occupied: 0,
    maintenance: 0,
    reserved: 0,
    total: props.bays.length,
    utilization: 0
  }
  
  props.bays.forEach(bay => {
    summary[bay.status]++
  })
  
  if (summary.total > 0) {
    summary.utilization = ((summary.occupied + summary.reserved) / summary.total) * 100
  }
  
  return summary
})

// Methods
const isBayOverdue = (bay: ServiceBay): boolean => {
  if (!bay.timeline?.estimatedCompletion || bay.status !== 'occupied') return false
  
  const now = new Date()
  const estimated = new Date(bay.timeline.estimatedCompletion)
  return now > estimated
}

const getBayStatusText = (status: string) => {
  const statusMap = {
    available: { en: 'Available', ar: 'متاح' },
    occupied: { en: 'Occupied', ar: 'مشغول' },
    maintenance: { en: 'Maintenance', ar: 'صيانة' },
    reserved: { en: 'Reserved', ar: 'محجوز' },
    out_of_order: { en: 'Out of Order', ar: 'خارج الخدمة' }
  }
  
  const statusObj = statusMap[status as keyof typeof statusMap]
  return statusObj ? (isRTL ? statusObj.ar : statusObj.en) : status
}

const getBayStatusVariant = (status: string) => {
  const variantMap = {
    available: 'success',
    occupied: 'primary',
    maintenance: 'warning',
    reserved: 'secondary',
    out_of_order: 'error'
  }
  
  return variantMap[status as keyof typeof variantMap] || 'default'
}

const getBayTypeIcon = (type: string) => {
  const iconMap = {
    standard: 'car',
    heavy_duty: 'truck',
    quick_service: 'zap',
    inspection: 'search'
  }
  
  return iconMap[type as keyof typeof iconMap] || 'car'
}

const getBayTypeText = (type: string) => {
  const typeMap = {
    standard: { en: 'Standard', ar: 'قياسي' },
    heavy_duty: { en: 'Heavy Duty', ar: 'خدمة شاقة' },
    quick_service: { en: 'Quick Service', ar: 'خدمة سريعة' },
    inspection: { en: 'Inspection', ar: 'فحص' }
  }
  
  const typeObj = typeMap[type as keyof typeof typeMap]
  return typeObj ? (isRTL ? typeObj.ar : typeObj.en) : type
}

const getBayMaintenanceText = (type: string) => {
  const maintenanceMap = {
    preventive: { en: 'Preventive', ar: 'وقائية' },
    corrective: { en: 'Corrective', ar: 'إصلاحية' },
    cleaning: { en: 'Cleaning', ar: 'تنظيف' }
  }
  
  const maintenanceObj = maintenanceMap[type as keyof typeof maintenanceMap]
  return maintenanceObj ? (isRTL ? maintenanceObj.ar : maintenanceObj.en) : type
}

const getPriorityIcon = (priority: string) => {
  const iconMap = {
    low: 'arrow-down',
    medium: 'minus',
    high: 'arrow-up',
    urgent: 'alert-triangle'
  }
  
  return iconMap[priority as keyof typeof iconMap] || 'minus'
}

const getPriorityColor = (priority: string) => {
  const colorMap = {
    low: 'var(--color-success)',
    medium: 'var(--color-warning)',
    high: 'var(--color-error)',
    urgent: 'var(--color-error)'
  }
  
  return colorMap[priority as keyof typeof colorMap] || 'var(--color-text-secondary)'
}

const getServiceTypeIcon = (serviceType: string) => {
  const iconMap: Record<string, string> = {
    'oil_change': 'droplet',
    'brake_service': 'disc',
    'engine_repair': 'wrench',
    'tire_rotation': 'rotate-cw',
    'inspection': 'search',
    'general': 'tool'
  }
  
  return iconMap[serviceType] || 'wrench'
}

const getServiceTypeText = (serviceType: string) => {
  return serviceType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

const formatTime = (time: string | Date) => {
  const d = new Date(time)
  if (isRTL) {
    return d.toLocaleTimeString('ar-SA', { hour: '2-digit', minute: '2-digit' })
  }
  return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
}

// Event handlers
const handleBayClick = (bay: ServiceBay) => {
  emit('bay-click', bay)
}

const handleAssignOrder = (bay: ServiceBay) => {
  emit('assign-order', bay)
}

const handleCompleteOrder = (bay: ServiceBay) => {
  emit('complete-order', bay)
}

const handleEndMaintenance = (bay: ServiceBay) => {
  emit('end-maintenance', bay)
}

const handleMoreActions = (bay: ServiceBay) => {
  emit('more-actions', bay)
}

const handleRefresh = () => {
  emit('refresh')
}
</script>

<style lang="scss" scoped>
.service-bay-status {
  --bay-padding: var(--spacing-4);
  --bay-border-radius: var(--radius-lg);
  --bay-gap: var(--spacing-4);
  
  // RTL support
  &--rtl {
    direction: rtl;
    text-align: right;
  }
  
  // Sizes
  &--sm {
    --bay-padding: var(--spacing-3);
    --bay-gap: var(--spacing-3);
    font-size: var(--font-size-sm);
  }
  
  &--lg {
    --bay-padding: var(--spacing-6);
    --bay-gap: var(--spacing-6);
    font-size: var(--font-size-lg);
  }
}

.service-bay-status__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--bay-gap);
  padding-bottom: var(--spacing-3);
  border-bottom: 1px solid var(--color-border-subtle);
}

.service-bay-status__title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0;
}

.service-bay-status__header-actions {
  display: flex;
  gap: var(--spacing-3);
  align-items: center;
}

.service-bay-status__grid {
  display: grid;
  gap: var(--bay-gap);
  
  .service-bay-status--grid & {
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  }
  
  .service-bay-status--list & {
    grid-template-columns: 1fr;
  }
}

.service-bay-status__bay-card {
  background: var(--color-background-elevated);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--bay-border-radius);
  padding: var(--bay-padding);
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  
  &:hover {
    box-shadow: var(--shadow-md);
    border-color: var(--color-border-primary);
  }
  
  &--selected {
    border-color: var(--color-primary);
    box-shadow: 0 0 0 1px var(--color-primary);
  }
  
  &--overdue {
    border-left: 4px solid var(--color-error);
    
    .service-bay-status--rtl & {
      border-left: none;
      border-right: 4px solid var(--color-error);
    }
  }
  
  &--urgent {
    box-shadow: 0 0 0 2px var(--color-error), var(--shadow-sm);
  }
  
  // Status-specific styling
  &--available {
    background: var(--color-success-background);
    border-color: var(--color-success-border);
  }
  
  &--occupied {
    background: var(--color-primary-background);
    border-color: var(--color-primary-border);
  }
  
  &--maintenance {
    background: var(--color-warning-background);
    border-color: var(--color-warning-border);
  }
  
  &--reserved {
    background: var(--color-secondary-background);
    border-color: var(--color-secondary-border);
  }
  
  &--out_of_order {
    background: var(--color-error-background);
    border-color: var(--color-error-border);
    opacity: 0.7;
  }
}

.service-bay-status__bay-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-3);
}

.service-bay-status__bay-number {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
}

.service-bay-status__bay-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-3);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.service-bay-status__bay-type {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
}

.service-bay-status__current-order {
  margin-bottom: var(--spacing-3);
  padding: var(--spacing-3);
  background: rgba(255, 255, 255, 0.5);
  border-radius: var(--radius-md);
}

.service-bay-status__order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-2);
}

.service-bay-status__order-number {
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.service-bay-status__vehicle-info,
.service-bay-status__customer-info,
.service-bay-status__service-type {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-1);
  
  &:last-child {
    margin-bottom: 0;
  }
}

.service-bay-status__technician {
  margin-bottom: var(--spacing-3);
}

.service-bay-status__technician-header {
  margin-bottom: var(--spacing-1);
}

.service-bay-status__technician-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.service-bay-status__technician-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
}

.service-bay-status__timeline {
  margin-bottom: var(--spacing-3);
}

.service-bay-status__timeline-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-1);
  
  &:last-child {
    margin-bottom: 0;
  }
}

.service-bay-status__progress {
  margin-bottom: var(--spacing-3);
}

.service-bay-status__progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-1);
}

.service-bay-status__progress-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.service-bay-status__progress-percentage {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

.service-bay-status__progress-bar {
  height: 6px;
  background: var(--color-background-subtle);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.service-bay-status__progress-fill {
  height: 100%;
  background: var(--color-primary);
  transition: width 0.3s ease;
  
  &--medium {
    background: var(--color-warning);
  }
  
  &--high {
    background: var(--color-success);
  }
  
  &--complete {
    background: var(--color-success);
  }
}

.service-bay-status__available-info,
.service-bay-status__maintenance-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: var(--spacing-4);
  margin-bottom: var(--spacing-3);
}

.service-bay-status__available-text,
.service-bay-status__maintenance-text {
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  margin: var(--spacing-2) 0;
}

.service-bay-status__next-scheduled,
.service-bay-status__maintenance-type,
.service-bay-status__maintenance-until {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.service-bay-status__actions {
  display: flex;
  gap: var(--spacing-2);
  justify-content: flex-end;
  padding-top: var(--spacing-3);
  border-top: 1px solid var(--color-border-subtle);
  margin-top: auto;
}

.service-bay-status__summary {
  display: flex;
  justify-content: space-around;
  margin-top: var(--bay-gap);
  padding-top: var(--spacing-4);
  border-top: 1px solid var(--color-border-subtle);
}

.service-bay-status__summary-item {
  text-align: center;
}

.service-bay-status__summary-value {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-1);
}

.service-bay-status__summary-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

// Responsive design
@media (max-width: 1200px) {
  .service-bay-status__grid {
    .service-bay-status--grid & {
      grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    }
  }
}

@media (max-width: 768px) {
  .service-bay-status__header {
    flex-direction: column;
    gap: var(--spacing-3);
    align-items: stretch;
  }
  
  .service-bay-status__header-actions {
    justify-content: space-between;
  }
  
  .service-bay-status__grid {
    .service-bay-status--grid & {
      grid-template-columns: 1fr;
    }
  }
  
  .service-bay-status__actions {
    flex-wrap: wrap;
    
    .uw-button {
      flex: 1;
      min-width: 80px;
    }
  }
  
  .service-bay-status__summary {
    flex-wrap: wrap;
    gap: var(--spacing-4);
  }
  
  .service-bay-status__summary-item {
    flex: 1;
    min-width: 80px;
  }
}
</style>