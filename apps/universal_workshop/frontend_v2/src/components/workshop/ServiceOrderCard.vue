<!--
  ServiceOrderCard Component - Universal Workshop Frontend V2
  
  A comprehensive card component for displaying service order information
  with full Arabic/RTL support and interactive features for workshop management.
-->

<template>
  <div :class="cardClasses" :dir="isRTL ? 'rtl' : 'ltr'">
    <!-- Card Header -->
    <div class="service-order-card__header">
      <div class="service-order-card__header-main">
        <div class="service-order-card__title-section">
          <h3 class="service-order-card__order-number">
            {{ isRTL && orderNumberAr ? orderNumberAr : orderNumber }}
          </h3>
          <UWBadge 
            :content="getStatusText()"
            :variant="getStatusVariant()"
            size="sm"
          />
        </div>
        
        <div class="service-order-card__priority">
          <UWIcon 
            :name="getPriorityIcon()" 
            :color="getPriorityColor()"
            size="sm"
          />
          <span class="service-order-card__priority-text">
            {{ getPriorityText() }}
          </span>
        </div>
      </div>
      
      <div class="service-order-card__actions">
        <UWButton
          v-if="canEdit"
          variant="ghost"
          size="sm"
          :icon-start="'edit'"
          @click="handleEdit"
          :aria-label="isRTL ? 'تحرير' : 'Edit'"
        />
        
        <UWButton
          variant="ghost"
          size="sm"
          :icon-start="'more-vertical'"
          @click="toggleActions"
          :aria-label="isRTL ? 'المزيد من الإجراءات' : 'More actions'"
        />
      </div>
    </div>

    <!-- Vehicle Information -->
    <div class="service-order-card__vehicle-info">
      <div class="service-order-card__vehicle-icon">
        <UWIcon name="car" size="md" color="var(--color-primary)" />
      </div>
      
      <div class="service-order-card__vehicle-details">
        <div class="service-order-card__vehicle-name">
          {{ vehicle.make }} {{ vehicle.model }} {{ vehicle.year }}
        </div>
        <div class="service-order-card__vehicle-plate">
          {{ isRTL ? 'رقم اللوحة:' : 'Plate:' }} {{ vehicle.plateNumber }}
        </div>
        <div v-if="vehicle.vin" class="service-order-card__vehicle-vin">
          {{ isRTL ? 'رقم الهيكل:' : 'VIN:' }} {{ vehicle.vin }}
        </div>
      </div>
      
      <div v-if="vehicle.mileage" class="service-order-card__mileage">
        <UWIcon name="speedometer" size="sm" />
        <span>{{ formatNumber(vehicle.mileage) }} {{ isRTL ? 'كم' : 'km' }}</span>
      </div>
    </div>

    <!-- Customer Information -->
    <div class="service-order-card__customer-info">
      <UWAvatar 
        :user="customer" 
        size="sm"
      />
      <div class="service-order-card__customer-details">
        <div class="service-order-card__customer-name">
          {{ isRTL && customer.nameAr ? customer.nameAr : customer.name }}
        </div>
        <div v-if="customer.phone" class="service-order-card__customer-contact">
          <UWIcon name="phone" size="xs" />
          {{ customer.phone }}
        </div>
      </div>
    </div>

    <!-- Service Details -->
    <div class="service-order-card__service-details">
      <div class="service-order-card__service-type">
        <UWIcon :name="getServiceIcon()" size="sm" />
        <span>{{ getServiceTypeText() }}</span>
      </div>
      
      <div v-if="description" class="service-order-card__description">
        {{ isRTL && descriptionAr ? descriptionAr : description }}
      </div>
      
      <div v-if="estimatedDuration" class="service-order-card__duration">
        <UWIcon name="clock" size="sm" />
        <span>
          {{ isRTL ? 'مدة متوقعة:' : 'Est. Duration:' }} 
          {{ formatDuration(estimatedDuration) }}
        </span>
      </div>
    </div>

    <!-- Technician Assignment -->
    <div v-if="assignedTechnician" class="service-order-card__technician">
      <div class="service-order-card__technician-label">
        {{ isRTL ? 'الفني المكلف:' : 'Assigned Technician:' }}
      </div>
      <div class="service-order-card__technician-info">
        <UWAvatar 
          :user="assignedTechnician" 
          size="xs"
          :status="getTechnicianStatus()"
        />
        <span>{{ isRTL && assignedTechnician.nameAr ? assignedTechnician.nameAr : assignedTechnician.name }}</span>
      </div>
    </div>

    <!-- Timeline & Progress -->
    <div class="service-order-card__timeline">
      <div class="service-order-card__dates">
        <div class="service-order-card__scheduled-date">
          <UWIcon name="calendar" size="sm" />
          <span>
            {{ isRTL ? 'موعد مجدول:' : 'Scheduled:' }}
            {{ formatDate(scheduledDate) }}
          </span>
        </div>
        
        <div v-if="estimatedCompletion" class="service-order-card__completion-date">
          <UWIcon name="check-circle" size="sm" />
          <span>
            {{ isRTL ? 'إكمال متوقع:' : 'Est. Completion:' }}
            {{ formatDate(estimatedCompletion) }}
          </span>
        </div>
      </div>
      
      <div v-if="showProgress" class="service-order-card__progress">
        <div class="service-order-card__progress-bar">
          <div 
            class="service-order-card__progress-fill"
            :style="{ width: `${progress}%` }"
          ></div>
        </div>
        <span class="service-order-card__progress-text">
          {{ progress }}% {{ isRTL ? 'مكتمل' : 'Complete' }}
        </span>
      </div>
    </div>

    <!-- Cost Information -->
    <div v-if="showCost" class="service-order-card__cost">
      <div class="service-order-card__cost-estimated">
        <span class="service-order-card__cost-label">
          {{ isRTL ? 'التكلفة المتوقعة:' : 'Estimated Cost:' }}
        </span>
        <span class="service-order-card__cost-amount">
          {{ formatCurrency(estimatedCost) }} {{ isRTL ? 'ريال عماني' : 'OMR' }}
        </span>
      </div>
      
      <div v-if="actualCost && actualCost !== estimatedCost" class="service-order-card__cost-actual">
        <span class="service-order-card__cost-label">
          {{ isRTL ? 'التكلفة الفعلية:' : 'Actual Cost:' }}
        </span>
        <span class="service-order-card__cost-amount">
          {{ formatCurrency(actualCost) }} {{ isRTL ? 'ريال عماني' : 'OMR' }}
        </span>
      </div>
    </div>

    <!-- Action Menu -->
    <Transition name="slide-down">
      <div v-if="showActionMenu" class="service-order-card__action-menu">
        <UWButton
          v-for="action in availableActions"
          :key="action.key"
          variant="ghost"
          size="sm"
          :icon-start="action.icon"
          @click="handleAction(action.key)"
          class="service-order-card__action-item"
        >
          {{ isRTL && action.labelAr ? action.labelAr : action.label }}
        </UWButton>
      </div>
    </Transition>
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
  vin?: string
  mileage?: number
}

interface Customer {
  name: string
  nameAr?: string
  phone?: string
  email?: string
  avatar?: string
}

interface Technician {
  name: string
  nameAr?: string
  id: string
  status?: 'available' | 'busy' | 'offline'
  avatar?: string
  specialization?: string
}

interface ServiceOrderAction {
  key: string
  label: string
  labelAr?: string
  icon: string
  variant?: 'primary' | 'secondary' | 'danger'
}

export interface ServiceOrderCardProps {
  orderNumber: string
  orderNumberAr?: string
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled' | 'on_hold'
  priority: 'low' | 'medium' | 'high' | 'urgent'
  serviceType: string
  serviceTypeAr?: string
  description?: string
  descriptionAr?: string
  vehicle: Vehicle
  customer: Customer
  assignedTechnician?: Technician
  scheduledDate: string | Date
  estimatedCompletion?: string | Date
  estimatedDuration?: number // in minutes
  estimatedCost?: number
  actualCost?: number
  progress?: number // 0-100
  showProgress?: boolean
  showCost?: boolean
  canEdit?: boolean
  actions?: ServiceOrderAction[]
  size?: 'sm' | 'md' | 'lg'
  variant?: 'default' | 'compact' | 'detailed'
}

export interface ServiceOrderCardEmits {
  'edit': []
  'action': [actionKey: string]
  'click': []
  'technician-assign': [technicianId: string]
  'status-change': [status: string]
}

const props = withDefaults(defineProps<ServiceOrderCardProps>(), {
  showProgress: true,
  showCost: true,
  canEdit: true,
  size: 'md',
  variant: 'default',
  progress: 0,
  actions: () => []
})

const emit = defineEmits<ServiceOrderCardEmits>()

// Injected context
const isRTL = inject('isRTL', false)

// Local state
const showActionMenu = ref(false)

// Computed properties
const cardClasses = computed(() => [
  'service-order-card',
  `service-order-card--${props.size}`,
  `service-order-card--${props.variant}`,
  `service-order-card--${props.status}`,
  `service-order-card--${props.priority}`,
  {
    'service-order-card--rtl': isRTL,
    'service-order-card--has-technician': !!props.assignedTechnician,
    'service-order-card--show-progress': props.showProgress,
    'service-order-card--show-cost': props.showCost
  }
])

const availableActions = computed(() => {
  const defaultActions: ServiceOrderAction[] = [
    {
      key: 'view',
      label: 'View Details',
      labelAr: 'عرض التفاصيل',
      icon: 'eye'
    },
    {
      key: 'assign',
      label: 'Assign Technician',
      labelAr: 'تكليف فني',
      icon: 'user-plus'
    },
    {
      key: 'reschedule',
      label: 'Reschedule',
      labelAr: 'إعادة جدولة',
      icon: 'calendar'
    },
    {
      key: 'cancel',
      label: 'Cancel Order',
      labelAr: 'إلغاء الطلب',
      icon: 'x-circle',
      variant: 'danger'
    }
  ]
  
  return [...defaultActions, ...props.actions]
})

// Methods
const getStatusText = () => {
  const statusMap = {
    pending: { en: 'Pending', ar: 'في الانتظار' },
    in_progress: { en: 'In Progress', ar: 'قيد التنفيذ' },
    completed: { en: 'Completed', ar: 'مكتمل' },
    cancelled: { en: 'Cancelled', ar: 'ملغي' },
    on_hold: { en: 'On Hold', ar: 'معلق' }
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
    on_hold: 'secondary'
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

const getPriorityText = () => {
  const priorityMap = {
    low: { en: 'Low', ar: 'منخفض' },
    medium: { en: 'Medium', ar: 'متوسط' },
    high: { en: 'High', ar: 'عالي' },
    urgent: { en: 'Urgent', ar: 'عاجل' }
  }
  
  const priority = priorityMap[props.priority]
  return isRTL ? priority.ar : priority.en
}

const getServiceIcon = () => {
  // Map service types to icons (simplified)
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

const getTechnicianStatus = () => {
  return props.assignedTechnician?.status || 'offline'
}

const formatDate = (date: string | Date) => {
  const d = new Date(date)
  if (isRTL) {
    return d.toLocaleDateString('ar-SA')
  }
  return d.toLocaleDateString('en-US', { 
    month: 'short', 
    day: 'numeric', 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

const formatDuration = (minutes: number) => {
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  
  if (isRTL) {
    if (hours > 0) {
      return `${hours} ساعة ${mins} دقيقة`
    }
    return `${mins} دقيقة`
  }
  
  if (hours > 0) {
    return `${hours}h ${mins}m`
  }
  return `${mins}m`
}

const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat(isRTL ? 'ar-OM' : 'en-OM', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(amount)
}

const formatNumber = (num: number) => {
  return new Intl.NumberFormat(isRTL ? 'ar-OM' : 'en-OM').format(num)
}

const toggleActions = () => {
  showActionMenu.value = !showActionMenu.value
}

const handleEdit = () => {
  emit('edit')
}

const handleAction = (actionKey: string) => {
  showActionMenu.value = false
  emit('action', actionKey)
}

const handleCardClick = () => {
  emit('click')
}
</script>

<style lang="scss" scoped>
.service-order-card {
  --card-padding: var(--spacing-4);
  --card-border-radius: var(--radius-lg);
  --card-border-color: var(--color-border-subtle);
  --card-background: var(--color-background-elevated);
  --card-shadow: var(--shadow-md);
  
  position: relative;
  background: var(--card-background);
  border: 1px solid var(--card-border-color);
  border-radius: var(--card-border-radius);
  box-shadow: var(--card-shadow);
  padding: var(--card-padding);
  transition: all 0.2s ease;
  cursor: pointer;
  
  &:hover {
    box-shadow: var(--shadow-lg);
    transform: translateY(-2px);
  }
  
  // Sizes
  &--sm {
    --card-padding: var(--spacing-3);
    font-size: var(--font-size-sm);
  }
  
  &--lg {
    --card-padding: var(--spacing-6);
    font-size: var(--font-size-lg);
  }
  
  // Variants
  &--compact {
    .service-order-card__description,
    .service-order-card__timeline,
    .service-order-card__cost {
      display: none;
    }
  }
  
  &--detailed {
    .service-order-card__vehicle-vin,
    .service-order-card__customer-contact,
    .service-order-card__duration {
      display: block;
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
  
  &--on_hold {
    border-left: 4px solid var(--color-secondary);
  }
  
  // Priority indicators
  &--urgent {
    box-shadow: 0 0 0 2px var(--color-error), var(--card-shadow);
  }
  
  &--high {
    border-top: 2px solid var(--color-error);
  }
  
  // RTL support
  &--rtl {
    direction: rtl;
    text-align: right;
    
    &.service-order-card--pending,
    &.service-order-card--in_progress,
    &.service-order-card--completed,
    &.service-order-card--cancelled,
    &.service-order-card--on_hold {
      border-left: none;
      border-right: 4px solid;
    }
  }
}

.service-order-card__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-4);
}

.service-order-card__header-main {
  flex: 1;
}

.service-order-card__title-section {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  margin-bottom: var(--spacing-2);
}

.service-order-card__order-number {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0;
}

.service-order-card__priority {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.service-order-card__actions {
  display: flex;
  gap: var(--spacing-1);
}

.service-order-card__vehicle-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  padding: var(--spacing-3);
  background: var(--color-background-subtle);
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-4);
}

.service-order-card__vehicle-details {
  flex: 1;
}

.service-order-card__vehicle-name {
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-1);
}

.service-order-card__vehicle-plate,
.service-order-card__vehicle-vin {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.service-order-card__mileage {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.service-order-card__customer-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  margin-bottom: var(--spacing-4);
}

.service-order-card__customer-details {
  flex: 1;
}

.service-order-card__customer-name {
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

.service-order-card__customer-contact {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-top: var(--spacing-1);
}

.service-order-card__service-details {
  margin-bottom: var(--spacing-4);
}

.service-order-card__service-type {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-2);
}

.service-order-card__description {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: var(--line-height-relaxed);
  margin-bottom: var(--spacing-2);
}

.service-order-card__duration {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.service-order-card__technician {
  margin-bottom: var(--spacing-4);
}

.service-order-card__technician-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-1);
}

.service-order-card__technician-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

.service-order-card__timeline {
  margin-bottom: var(--spacing-4);
}

.service-order-card__dates {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
  margin-bottom: var(--spacing-3);
}

.service-order-card__scheduled-date,
.service-order-card__completion-date {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.service-order-card__progress {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.service-order-card__progress-bar {
  flex: 1;
  height: 4px;
  background: var(--color-background-subtle);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.service-order-card__progress-fill {
  height: 100%;
  background: var(--color-primary);
  transition: width 0.3s ease;
}

.service-order-card__progress-text {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  white-space: nowrap;
}

.service-order-card__cost {
  border-top: 1px solid var(--color-border-subtle);
  padding-top: var(--spacing-3);
}

.service-order-card__cost-estimated,
.service-order-card__cost-actual {
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  &:not(:last-child) {
    margin-bottom: var(--spacing-2);
  }
}

.service-order-card__cost-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.service-order-card__cost-amount {
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.service-order-card__action-menu {
  position: absolute;
  top: 100%;
  right: var(--spacing-2);
  background: var(--color-background-elevated);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  padding: var(--spacing-2);
  z-index: 10;
  min-width: 150px;
  
  .service-order-card--rtl & {
    right: auto;
    left: var(--spacing-2);
  }
}

.service-order-card__action-item {
  width: 100%;
  justify-content: flex-start;
  
  &:not(:last-child) {
    margin-bottom: var(--spacing-1);
  }
}

// Animations
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.2s ease;
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

// Responsive design
@media (max-width: 768px) {
  .service-order-card {
    --card-padding: var(--spacing-3);
  }
  
  .service-order-card__header {
    flex-direction: column;
    gap: var(--spacing-2);
  }
  
  .service-order-card__actions {
    align-self: flex-end;
  }
  
  .service-order-card__vehicle-info {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-2);
  }
  
  .service-order-card__dates {
    gap: var(--spacing-1);
  }
}
</style>