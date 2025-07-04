<!--
  MobileServiceCard Component - Universal Workshop Frontend V2
  
  Mobile-optimized service order card with touch-friendly interactions,
  swipe gestures, and compact layout for workshop management on mobile devices.
-->

<template>
  <div 
    :class="cardClasses" 
    :dir="isRTL ? 'rtl' : 'ltr'"
    @click="handleCardClick"
    @touchstart="handleTouchStart"
    @touchmove="handleTouchMove"
    @touchend="handleTouchEnd"
    :style="cardStyles"
  >
    <!-- Swipe Actions Background -->
    <div v-if="swipeOffset !== 0" class="mobile-service-card__swipe-actions">
      <div 
        v-if="swipeOffset > 0" 
        class="mobile-service-card__swipe-action mobile-service-card__swipe-action--left"
      >
        <UWIcon name="check" size="lg" color="white" />
        <span>{{ isRTL ? 'إكمال' : 'Complete' }}</span>
      </div>
      
      <div 
        v-if="swipeOffset < 0" 
        class="mobile-service-card__swipe-action mobile-service-card__swipe-action--right"
      >
        <UWIcon name="edit" size="lg" color="white" />
        <span>{{ isRTL ? 'تحرير' : 'Edit' }}</span>
      </div>
    </div>

    <!-- Card Content -->
    <div class="mobile-service-card__content">
      <!-- Header -->
      <div class="mobile-service-card__header">
        <div class="mobile-service-card__primary-info">
          <div class="mobile-service-card__order-number">
            {{ orderNumber }}
          </div>
          <UWBadge 
            :content="getStatusText()"
            :variant="getStatusVariant()"
            size="sm"
          />
        </div>
        
        <div class="mobile-service-card__priority">
          <UWIcon 
            :name="getPriorityIcon()" 
            size="sm"
            :color="getPriorityColor()"
          />
        </div>
      </div>

      <!-- Vehicle & Customer Info -->
      <div class="mobile-service-card__vehicle-customer">
        <div class="mobile-service-card__vehicle">
          <UWIcon name="car" size="sm" />
          <span class="mobile-service-card__vehicle-text">
            {{ vehicle.make }} {{ vehicle.model }} {{ vehicle.year }}
          </span>
          <span class="mobile-service-card__plate">
            {{ vehicle.plateNumber }}
          </span>
        </div>
        
        <div class="mobile-service-card__customer">
          <UWAvatar :user="customer" size="xs" />
          <span class="mobile-service-card__customer-name">
            {{ isRTL && customer.nameAr ? customer.nameAr : customer.name }}
          </span>
        </div>
      </div>

      <!-- Service Details -->
      <div class="mobile-service-card__service-info">
        <div class="mobile-service-card__service-type">
          <UWIcon :name="getServiceIcon()" size="sm" />
          <span>{{ getServiceTypeText() }}</span>
        </div>
        
        <div v-if="description" class="mobile-service-card__description">
          {{ truncateText(isRTL && descriptionAr ? descriptionAr : description, 60) }}
        </div>
      </div>

      <!-- Technician & Time Info -->
      <div class="mobile-service-card__bottom-info">
        <div v-if="assignedTechnician" class="mobile-service-card__technician">
          <UWAvatar 
            :user="assignedTechnician" 
            :status="assignedTechnician.status"
            size="xs"
          />
          <span class="mobile-service-card__technician-name">
            {{ isRTL && assignedTechnician.nameAr 
              ? assignedTechnician.nameAr 
              : assignedTechnician.name }}
          </span>
        </div>
        
        <div class="mobile-service-card__time-info">
          <div v-if="scheduledDate" class="mobile-service-card__scheduled">
            <UWIcon name="calendar" size="xs" />
            <span>{{ formatDate(scheduledDate) }}</span>
          </div>
          
          <div v-if="estimatedDuration" class="mobile-service-card__duration">
            <UWIcon name="clock" size="xs" />
            <span>{{ formatDuration(estimatedDuration) }}</span>
          </div>
        </div>
      </div>

      <!-- Progress Bar -->
      <div v-if="showProgress && progress !== undefined" class="mobile-service-card__progress">
        <div class="mobile-service-card__progress-bar">
          <div 
            class="mobile-service-card__progress-fill"
            :style="{ width: `${progress}%` }"
          ></div>
        </div>
        <span class="mobile-service-card__progress-text">
          {{ progress }}% {{ isRTL ? 'مكتمل' : 'complete' }}
        </span>
      </div>

      <!-- Action Buttons -->
      <div v-if="showActions" class="mobile-service-card__actions">
        <UWButton
          v-for="action in visibleActions"
          :key="action.key"
          :variant="action.variant || 'outline'"
          size="sm"
          :icon-start="action.icon"
          @click.stop="handleActionClick(action)"
        >
          {{ isRTL && action.labelAr ? action.labelAr : action.label }}
        </UWButton>
      </div>

      <!-- Cost Information -->
      <div v-if="showCost && (estimatedCost || actualCost)" class="mobile-service-card__cost">
        <div v-if="estimatedCost" class="mobile-service-card__cost-item">
          <span class="mobile-service-card__cost-label">
            {{ isRTL ? 'متوقع:' : 'Est:' }}
          </span>
          <span class="mobile-service-card__cost-value">
            {{ formatCurrency(estimatedCost) }}
          </span>
        </div>
        
        <div v-if="actualCost && actualCost !== estimatedCost" class="mobile-service-card__cost-item">
          <span class="mobile-service-card__cost-label">
            {{ isRTL ? 'فعلي:' : 'Actual:' }}
          </span>
          <span class="mobile-service-card__cost-value">
            {{ formatCurrency(actualCost) }}
          </span>
        </div>
      </div>
    </div>

    <!-- Floating Status Indicator -->
    <div v-if="status === 'urgent'" class="mobile-service-card__urgent-indicator">
      <UWIcon name="alert-triangle" size="sm" color="white" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, inject } from 'vue'
import { UWButton } from '@/components/base'
import { UWIcon, UWBadge, UWAvatar } from '@/components/primitives'

// Types
interface Vehicle {
  make: string
  model: string
  year: number
  plateNumber: string
}

interface Customer {
  name: string
  nameAr?: string
  avatar?: string
}

interface Technician {
  name: string
  nameAr?: string
  status: 'available' | 'busy' | 'offline'
  avatar?: string
}

interface Action {
  key: string
  label: string
  labelAr?: string
  icon: string
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger'
}

export interface MobileServiceCardProps {
  orderNumber: string
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled' | 'urgent'
  priority: 'low' | 'medium' | 'high' | 'urgent'
  serviceType: string
  serviceTypeAr?: string
  description?: string
  descriptionAr?: string
  vehicle: Vehicle
  customer: Customer
  assignedTechnician?: Technician
  scheduledDate?: string | Date
  estimatedDuration?: number // in minutes
  estimatedCost?: number
  actualCost?: number
  progress?: number // 0-100
  actions?: Action[]
  showProgress?: boolean
  showActions?: boolean
  showCost?: boolean
  maxActions?: number
  swipeEnabled?: boolean
  variant?: 'default' | 'compact' | 'detailed'
}

export interface MobileServiceCardEmits {
  'click': []
  'action': [actionKey: string]
  'swipe-complete': []
  'swipe-edit': []
}

const props = withDefaults(defineProps<MobileServiceCardProps>(), {
  showProgress: true,
  showActions: true,
  showCost: true,
  maxActions: 2,
  swipeEnabled: true,
  variant: 'default',
  actions: () => []
})

const emit = defineEmits<MobileServiceCardEmits>()

// Injected context
const isRTL = inject('isRTL', false)

// Touch/Swipe state
const swipeOffset = ref(0)
const startX = ref(0)
const isDragging = ref(false)
const swipeThreshold = 80

// Computed properties
const cardClasses = computed(() => [
  'mobile-service-card',
  `mobile-service-card--${props.variant}`,
  `mobile-service-card--${props.status}`,
  `mobile-service-card--${props.priority}`,
  {
    'mobile-service-card--rtl': isRTL,
    'mobile-service-card--swiping': isDragging.value,
    'mobile-service-card--has-technician': !!props.assignedTechnician,
    'mobile-service-card--urgent': props.status === 'urgent'
  }
])

const cardStyles = computed(() => ({
  transform: `translateX(${swipeOffset.value}px)`,
  transition: isDragging.value ? 'none' : 'transform 0.3s ease'
}))

const visibleActions = computed(() => {
  return props.actions.slice(0, props.maxActions)
})

// Methods
const getStatusText = () => {
  const statusMap = {
    pending: { en: 'Pending', ar: 'في الانتظار' },
    in_progress: { en: 'In Progress', ar: 'قيد التنفيذ' },
    completed: { en: 'Completed', ar: 'مكتمل' },
    cancelled: { en: 'Cancelled', ar: 'ملغي' },
    urgent: { en: 'Urgent', ar: 'عاجل' }
  }
  
  const status = statusMap[props.status]
  return isRTL ? status.ar : status.en
}

const getStatusVariant = () => {
  const variantMap = {
    pending: 'warning',
    in_progress: 'primary',
    completed: 'success',
    cancelled: 'error',
    urgent: 'error'
  }
  
  return variantMap[props.status] || 'default'
}

const getPriorityIcon = () => {
  const iconMap = {
    low: 'arrow-down',
    medium: 'minus',
    high: 'arrow-up',
    urgent: 'alert-triangle'
  }
  
  return iconMap[props.priority]
}

const getPriorityColor = () => {
  const colorMap = {
    low: 'var(--color-success)',
    medium: 'var(--color-warning)',
    high: 'var(--color-error)',
    urgent: 'var(--color-error)'
  }
  
  return colorMap[props.priority]
}

const getServiceIcon = () => {
  const serviceTypeIconMap: Record<string, string> = {
    'oil_change': 'droplet',
    'brake_service': 'disc',
    'engine_repair': 'wrench',
    'tire_rotation': 'rotate-cw',
    'general_maintenance': 'tool',
    'diagnostic': 'search'
  }
  
  return serviceTypeIconMap[props.serviceType] || 'wrench'
}

const getServiceTypeText = () => {
  if (isRTL && props.serviceTypeAr) {
    return props.serviceTypeAr
  }
  return props.serviceType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

const formatDate = (date: string | Date) => {
  const d = new Date(date)
  if (isRTL) {
    return d.toLocaleDateString('ar-SA', { month: 'short', day: 'numeric' })
  }
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

const formatDuration = (minutes: number) => {
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  
  if (isRTL) {
    if (hours > 0) {
      return `${hours}س ${mins}د`
    }
    return `${mins}د`
  }
  
  if (hours > 0) {
    return `${hours}h ${mins}m`
  }
  return `${mins}m`
}

const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat(isRTL ? 'ar-OM' : 'en-OM', {
    style: 'currency',
    currency: 'OMR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 2
  }).format(amount)
}

const truncateText = (text: string, maxLength: number) => {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

// Touch/Swipe handlers
const handleTouchStart = (event: TouchEvent) => {
  if (!props.swipeEnabled) return
  
  startX.value = event.touches[0].clientX
  isDragging.value = true
}

const handleTouchMove = (event: TouchEvent) => {
  if (!props.swipeEnabled || !isDragging.value) return
  
  const currentX = event.touches[0].clientX
  const deltaX = currentX - startX.value
  
  // Limit swipe distance
  const maxSwipe = 120
  swipeOffset.value = Math.max(-maxSwipe, Math.min(maxSwipe, deltaX))
}

const handleTouchEnd = () => {
  if (!props.swipeEnabled || !isDragging.value) return
  
  isDragging.value = false
  
  // Check if swipe threshold was reached
  if (Math.abs(swipeOffset.value) >= swipeThreshold) {
    if (swipeOffset.value > 0) {
      emit('swipe-complete')
    } else {
      emit('swipe-edit')
    }
  }
  
  // Reset swipe offset
  swipeOffset.value = 0
}

const handleCardClick = () => {
  if (isDragging.value || swipeOffset.value !== 0) return
  emit('click')
}

const handleActionClick = (action: Action) => {
  emit('action', action.key)
}
</script>

<style lang="scss" scoped>
.mobile-service-card {
  --card-padding: var(--spacing-4);
  --card-border-radius: var(--radius-lg);
  --card-background: var(--color-background-elevated);
  --card-border-color: var(--color-border-subtle);
  
  position: relative;
  background: var(--card-background);
  border: 1px solid var(--card-border-color);
  border-radius: var(--card-border-radius);
  margin-bottom: var(--spacing-3);
  cursor: pointer;
  overflow: hidden;
  touch-action: pan-y;
  
  // Variants
  &--compact {
    --card-padding: var(--spacing-3);
    
    .mobile-service-card__description,
    .mobile-service-card__cost {
      display: none;
    }
  }
  
  &--detailed {
    .mobile-service-card__actions {
      display: flex;
    }
  }
  
  // Status colors
  &--pending {
    border-left: 4px solid var(--color-warning);
  }
  
  &--in_progress {
    border-left: 4px solid var(--color-primary);
  }
  
  &--completed {
    border-left: 4px solid var(--color-success);
  }
  
  &--cancelled {
    border-left: 4px solid var(--color-error);
    opacity: 0.7;
  }
  
  &--urgent {
    border-left: 4px solid var(--color-error);
    box-shadow: 0 0 0 1px var(--color-error-border), var(--shadow-md);
  }
  
  // RTL support
  &--rtl {
    direction: rtl;
    text-align: right;
    
    &.mobile-service-card--pending,
    &.mobile-service-card--in_progress,
    &.mobile-service-card--completed,
    &.mobile-service-card--cancelled,
    &.mobile-service-card--urgent {
      border-left: none;
      border-right: 4px solid;
    }
  }
  
  &--swiping {
    z-index: 10;
  }
}

.mobile-service-card__swipe-actions {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.mobile-service-card__swipe-action {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-1);
  height: 100%;
  width: 80px;
  color: white;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  
  &--left {
    background: var(--color-success);
  }
  
  &--right {
    background: var(--color-primary);
  }
}

.mobile-service-card__content {
  padding: var(--card-padding);
  background: var(--card-background);
  position: relative;
  z-index: 5;
}

.mobile-service-card__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-3);
}

.mobile-service-card__primary-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  flex: 1;
}

.mobile-service-card__order-number {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.mobile-service-card__vehicle-customer {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
  margin-bottom: var(--spacing-3);
}

.mobile-service-card__vehicle {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.mobile-service-card__vehicle-text {
  flex: 1;
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

.mobile-service-card__plate {
  padding: var(--spacing-1) var(--spacing-2);
  background: var(--color-background-subtle);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
}

.mobile-service-card__customer {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.mobile-service-card__customer-name {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.mobile-service-card__service-info {
  margin-bottom: var(--spacing-3);
}

.mobile-service-card__service-type {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  margin-bottom: var(--spacing-2);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

.mobile-service-card__description {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: var(--line-height-relaxed);
}

.mobile-service-card__bottom-info {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: var(--spacing-3);
}

.mobile-service-card__technician {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.mobile-service-card__technician-name {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.mobile-service-card__time-info {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
  align-items: flex-end;
  
  .mobile-service-card--rtl & {
    align-items: flex-start;
  }
}

.mobile-service-card__scheduled,
.mobile-service-card__duration {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.mobile-service-card__progress {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  margin-bottom: var(--spacing-3);
}

.mobile-service-card__progress-bar {
  flex: 1;
  height: 4px;
  background: var(--color-background-subtle);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.mobile-service-card__progress-fill {
  height: 100%;
  background: var(--color-primary);
  transition: width 0.3s ease;
}

.mobile-service-card__progress-text {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  white-space: nowrap;
}

.mobile-service-card__actions {
  display: flex;
  gap: var(--spacing-2);
  margin-bottom: var(--spacing-2);
  
  .mobile-service-card--compact & {
    display: none;
  }
}

.mobile-service-card__cost {
  display: flex;
  justify-content: space-between;
  padding-top: var(--spacing-3);
  border-top: 1px solid var(--color-border-subtle);
}

.mobile-service-card__cost-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
}

.mobile-service-card__cost-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.mobile-service-card__cost-value {
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.mobile-service-card__urgent-indicator {
  position: absolute;
  top: var(--spacing-2);
  right: var(--spacing-2);
  width: 32px;
  height: 32px;
  background: var(--color-error);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  
  .mobile-service-card--rtl & {
    right: auto;
    left: var(--spacing-2);
  }
}

// Touch feedback
@media (hover: none) and (pointer: coarse) {
  .mobile-service-card:active {
    transform: scale(0.98);
    transition: transform 0.1s ease;
  }
}

// Responsive adjustments
@media (max-width: 360px) {
  .mobile-service-card {
    --card-padding: var(--spacing-3);
  }
  
  .mobile-service-card__actions {
    flex-direction: column;
    
    .uw-button {
      width: 100%;
      justify-content: center;
    }
  }
}
</style>