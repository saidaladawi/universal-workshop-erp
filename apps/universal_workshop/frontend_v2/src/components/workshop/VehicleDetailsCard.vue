<!--
  VehicleDetailsCard Component - Universal Workshop Frontend V2
  
  A comprehensive card component for displaying vehicle information
  with service history, maintenance schedule, and VIN decoding support.
-->

<template>
  <div :class="cardClasses" :dir="isRTL ? 'rtl' : 'ltr'">
    <!-- Card Header -->
    <div class="vehicle-card__header">
      <div class="vehicle-card__title-section">
        <h3 class="vehicle-card__vehicle-name">
          {{ vehicle.make }} {{ vehicle.model }} {{ vehicle.year }}
        </h3>
        <div class="vehicle-card__identifiers">
          <UWBadge 
            :content="vehicle.plateNumber"
            variant="secondary"
            size="sm"
            icon-start="car"
          />
          <UWBadge 
            v-if="vehicle.status"
            :content="getStatusText()"
            :variant="getStatusVariant()"
            size="sm"
          />
        </div>
      </div>
      
      <div class="vehicle-card__actions">
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

    <!-- Vehicle Image -->
    <div v-if="vehicle.imageUrl || showPlaceholder" class="vehicle-card__image-section">
      <div class="vehicle-card__image-container">
        <img
          v-if="vehicle.imageUrl"
          :src="vehicle.imageUrl"
          :alt="`${vehicle.make} ${vehicle.model}`"
          class="vehicle-card__image"
          @error="handleImageError"
        />
        <div v-else class="vehicle-card__image-placeholder">
          <UWIcon name="car" size="xl" color="var(--color-text-tertiary)" />
        </div>
      </div>
    </div>

    <!-- Vehicle Specifications -->
    <div class="vehicle-card__specifications">
      <div class="vehicle-card__spec-grid">
        <div class="vehicle-card__spec-item">
          <div class="vehicle-card__spec-label">
            {{ isRTL ? 'رقم الهيكل:' : 'VIN:' }}
          </div>
          <div class="vehicle-card__spec-value">
            {{ vehicle.vin || (isRTL ? 'غير محدد' : 'N/A') }}
          </div>
        </div>
        
        <div class="vehicle-card__spec-item">
          <div class="vehicle-card__spec-label">
            {{ isRTL ? 'المحرك:' : 'Engine:' }}
          </div>
          <div class="vehicle-card__spec-value">
            {{ vehicle.engineSize || (isRTL ? 'غير محدد' : 'N/A') }}
          </div>
        </div>
        
        <div class="vehicle-card__spec-item">
          <div class="vehicle-card__spec-label">
            {{ isRTL ? 'ناقل الحركة:' : 'Transmission:' }}
          </div>
          <div class="vehicle-card__spec-value">
            {{ getTransmissionText() }}
          </div>
        </div>
        
        <div class="vehicle-card__spec-item">
          <div class="vehicle-card__spec-label">
            {{ isRTL ? 'نوع الوقود:' : 'Fuel Type:' }}
          </div>
          <div class="vehicle-card__spec-value">
            {{ getFuelTypeText() }}
          </div>
        </div>
      </div>
    </div>

    <!-- Mileage & Condition -->
    <div class="vehicle-card__status-section">
      <div class="vehicle-card__mileage">
        <div class="vehicle-card__mileage-current">
          <UWIcon name="speedometer" size="md" color="var(--color-primary)" />
          <div class="vehicle-card__mileage-info">
            <div class="vehicle-card__mileage-value">
              {{ formatNumber(vehicle.mileage) }} {{ isRTL ? 'كم' : 'km' }}
            </div>
            <div class="vehicle-card__mileage-label">
              {{ isRTL ? 'المسافة المقطوعة' : 'Mileage' }}
            </div>
          </div>
        </div>
        
        <div v-if="vehicle.lastServiceMileage" class="vehicle-card__last-service">
          <div class="vehicle-card__last-service-label">
            {{ isRTL ? 'آخر خدمة:' : 'Last Service:' }}
          </div>
          <div class="vehicle-card__last-service-value">
            {{ formatNumber(vehicle.lastServiceMileage) }} {{ isRTL ? 'كم' : 'km' }}
          </div>
        </div>
      </div>
      
      <div v-if="vehicle.condition" class="vehicle-card__condition">
        <div class="vehicle-card__condition-label">
          {{ isRTL ? 'الحالة العامة:' : 'Condition:' }}
        </div>
        <div class="vehicle-card__condition-rating">
          <div 
            v-for="star in 5" 
            :key="star"
            class="vehicle-card__condition-star"
            :class="{ 'vehicle-card__condition-star--active': star <= vehicle.condition }"
          >
            <UWIcon name="star" size="sm" />
          </div>
          <span class="vehicle-card__condition-text">
            {{ getConditionText() }}
          </span>
        </div>
      </div>
    </div>

    <!-- Owner Information -->
    <div v-if="owner" class="vehicle-card__owner-section">
      <div class="vehicle-card__owner-header">
        <h4 class="vehicle-card__owner-title">
          {{ isRTL ? 'معلومات المالك' : 'Owner Information' }}
        </h4>
      </div>
      
      <div class="vehicle-card__owner-info">
        <UWAvatar 
          :user="owner" 
          size="sm"
        />
        <div class="vehicle-card__owner-details">
          <div class="vehicle-card__owner-name">
            {{ isRTL && owner.nameAr ? owner.nameAr : owner.name }}
          </div>
          <div v-if="owner.phone" class="vehicle-card__owner-contact">
            <UWIcon name="phone" size="xs" />
            {{ owner.phone }}
          </div>
        </div>
      </div>
    </div>

    <!-- Service History Summary -->
    <div v-if="showServiceHistory && serviceHistory?.length" class="vehicle-card__service-history">
      <div class="vehicle-card__service-header">
        <h4 class="vehicle-card__service-title">
          {{ isRTL ? 'آخر الخدمات' : 'Recent Services' }}
        </h4>
        <UWButton
          variant="ghost"
          size="sm"
          :icon-start="'eye'"
          @click="handleViewHistory"
        >
          {{ isRTL ? 'عرض الكل' : 'View All' }}
        </UWButton>
      </div>
      
      <div class="vehicle-card__service-list">
        <div 
          v-for="service in recentServices" 
          :key="service.id"
          class="vehicle-card__service-item"
        >
          <div class="vehicle-card__service-icon">
            <UWIcon :name="getServiceIcon(service.type)" size="sm" />
          </div>
          <div class="vehicle-card__service-details">
            <div class="vehicle-card__service-name">
              {{ isRTL && service.nameAr ? service.nameAr : service.name }}
            </div>
            <div class="vehicle-card__service-date">
              {{ formatDate(service.date) }}
            </div>
          </div>
          <div class="vehicle-card__service-status">
            <UWBadge 
              :content="getServiceStatusText(service.status)"
              :variant="getServiceStatusVariant(service.status)"
              size="xs"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Maintenance Schedule -->
    <div v-if="showMaintenanceSchedule && upcomingMaintenance?.length" class="vehicle-card__maintenance">
      <div class="vehicle-card__maintenance-header">
        <h4 class="vehicle-card__maintenance-title">
          {{ isRTL ? 'الصيانة القادمة' : 'Upcoming Maintenance' }}
        </h4>
      </div>
      
      <div class="vehicle-card__maintenance-list">
        <div 
          v-for="maintenance in upcomingMaintenance.slice(0, 3)" 
          :key="maintenance.id"
          class="vehicle-card__maintenance-item"
          :class="{ 'vehicle-card__maintenance-item--overdue': maintenance.isOverdue }"
        >
          <div class="vehicle-card__maintenance-icon">
            <UWIcon 
              :name="maintenance.isOverdue ? 'alert-triangle' : 'clock'"
              size="sm" 
              :color="maintenance.isOverdue ? 'var(--color-error)' : 'var(--color-warning)'"
            />
          </div>
          <div class="vehicle-card__maintenance-details">
            <div class="vehicle-card__maintenance-name">
              {{ isRTL && maintenance.nameAr ? maintenance.nameAr : maintenance.name }}
            </div>
            <div class="vehicle-card__maintenance-due">
              {{ formatMaintenanceDue(maintenance) }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Action Menu -->
    <Transition name="slide-down">
      <div v-if="showActionMenu" class="vehicle-card__action-menu">
        <UWButton
          v-for="action in availableActions"
          :key="action.key"
          variant="ghost"
          size="sm"
          :icon-start="action.icon"
          @click="handleAction(action.key)"
          class="vehicle-card__action-item"
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
  id: string
  make: string
  model: string
  year: number
  plateNumber: string
  vin?: string
  mileage: number
  lastServiceMileage?: number
  engineSize?: string
  transmission?: 'manual' | 'automatic' | 'cvt'
  fuelType?: 'gasoline' | 'diesel' | 'hybrid' | 'electric'
  condition?: number // 1-5 stars
  status?: 'active' | 'maintenance' | 'inactive'
  imageUrl?: string
}

interface Owner {
  id: string
  name: string
  nameAr?: string
  phone?: string
  email?: string
  avatar?: string
}

interface ServiceHistoryItem {
  id: string
  name: string
  nameAr?: string
  type: string
  date: string | Date
  status: 'completed' | 'in_progress' | 'cancelled'
  mileage: number
}

interface MaintenanceItem {
  id: string
  name: string
  nameAr?: string
  type: string
  dueDate?: string | Date
  dueMileage?: number
  isOverdue: boolean
}

interface VehicleAction {
  key: string
  label: string
  labelAr?: string
  icon: string
  variant?: 'primary' | 'secondary' | 'danger'
}

export interface VehicleDetailsCardProps {
  vehicle: Vehicle
  owner?: Owner
  serviceHistory?: ServiceHistoryItem[]
  upcomingMaintenance?: MaintenanceItem[]
  showServiceHistory?: boolean
  showMaintenanceSchedule?: boolean
  showPlaceholder?: boolean
  canEdit?: boolean
  actions?: VehicleAction[]
  size?: 'sm' | 'md' | 'lg'
  variant?: 'default' | 'compact' | 'detailed'
}

export interface VehicleDetailsCardEmits {
  'edit': []
  'action': [actionKey: string]
  'view-history': []
  'schedule-maintenance': [maintenanceId: string]
  'click': []
}

const props = withDefaults(defineProps<VehicleDetailsCardProps>(), {
  showServiceHistory: true,
  showMaintenanceSchedule: true,
  showPlaceholder: true,
  canEdit: true,
  size: 'md',
  variant: 'default',
  serviceHistory: () => [],
  upcomingMaintenance: () => [],
  actions: () => []
})

const emit = defineEmits<VehicleDetailsCardEmits>()

// Injected context
const isRTL = inject('isRTL', false)

// Local state
const showActionMenu = ref(false)

// Computed properties
const cardClasses = computed(() => [
  'vehicle-card',
  `vehicle-card--${props.size}`,
  `vehicle-card--${props.variant}`,
  {
    'vehicle-card--rtl': isRTL,
    'vehicle-card--has-image': !!props.vehicle.imageUrl,
    'vehicle-card--show-history': props.showServiceHistory,
    'vehicle-card--show-maintenance': props.showMaintenanceSchedule
  }
])

const recentServices = computed(() => {
  return props.serviceHistory?.slice(0, 3) || []
})

const availableActions = computed(() => {
  const defaultActions: VehicleAction[] = [
    {
      key: 'view',
      label: 'View Details',
      labelAr: 'عرض التفاصيل',
      icon: 'eye'
    },
    {
      key: 'schedule',
      label: 'Schedule Service',
      labelAr: 'جدولة خدمة',
      icon: 'calendar-plus'
    },
    {
      key: 'history',
      label: 'Service History',
      labelAr: 'تاريخ الخدمات',
      icon: 'history'
    },
    {
      key: 'inspection',
      label: 'Vehicle Inspection',
      labelAr: 'فحص المركبة',
      icon: 'search'
    }
  ]
  
  return [...defaultActions, ...props.actions]
})

// Methods
const getStatusText = () => {
  if (!props.vehicle.status) return ''
  
  const statusMap = {
    active: { en: 'Active', ar: 'نشط' },
    maintenance: { en: 'In Maintenance', ar: 'قيد الصيانة' },
    inactive: { en: 'Inactive', ar: 'غير نشط' }
  }
  
  const status = statusMap[props.vehicle.status]
  return isRTL ? status.ar : status.en
}

const getStatusVariant = () => {
  const variantMap = {
    active: 'success',
    maintenance: 'warning',
    inactive: 'secondary'
  }
  
  return variantMap[props.vehicle.status || 'active'] || 'default'
}

const getTransmissionText = () => {
  if (!props.vehicle.transmission) return isRTL ? 'غير محدد' : 'N/A'
  
  const transmissionMap = {
    manual: { en: 'Manual', ar: 'يدوي' },
    automatic: { en: 'Automatic', ar: 'أوتوماتيكي' },
    cvt: { en: 'CVT', ar: 'CVT' }
  }
  
  const transmission = transmissionMap[props.vehicle.transmission]
  return isRTL ? transmission.ar : transmission.en
}

const getFuelTypeText = () => {
  if (!props.vehicle.fuelType) return isRTL ? 'غير محدد' : 'N/A'
  
  const fuelMap = {
    gasoline: { en: 'Gasoline', ar: 'بنزين' },
    diesel: { en: 'Diesel', ar: 'ديزل' },
    hybrid: { en: 'Hybrid', ar: 'هجين' },
    electric: { en: 'Electric', ar: 'كهربائي' }
  }
  
  const fuel = fuelMap[props.vehicle.fuelType]
  return isRTL ? fuel.ar : fuel.en
}

const getConditionText = () => {
  if (!props.vehicle.condition) return ''
  
  const conditionMap = {
    1: { en: 'Poor', ar: 'سيء' },
    2: { en: 'Fair', ar: 'مقبول' },
    3: { en: 'Good', ar: 'جيد' },
    4: { en: 'Very Good', ar: 'جيد جداً' },
    5: { en: 'Excellent', ar: 'ممتاز' }
  }
  
  const condition = conditionMap[props.vehicle.condition as keyof typeof conditionMap]
  return isRTL ? condition.ar : condition.en
}

const getServiceIcon = (serviceType: string) => {
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

const getServiceStatusText = (status: string) => {
  const statusMap = {
    completed: { en: 'Completed', ar: 'مكتمل' },
    in_progress: { en: 'In Progress', ar: 'قيد التنفيذ' },
    cancelled: { en: 'Cancelled', ar: 'ملغي' }
  }
  
  const statusObj = statusMap[status as keyof typeof statusMap]
  return statusObj ? (isRTL ? statusObj.ar : statusObj.en) : status
}

const getServiceStatusVariant = (status: string) => {
  const variantMap = {
    completed: 'success',
    in_progress: 'primary',
    cancelled: 'error'
  }
  
  return variantMap[status as keyof typeof variantMap] || 'default'
}

const formatDate = (date: string | Date) => {
  const d = new Date(date)
  if (isRTL) {
    return d.toLocaleDateString('ar-SA')
  }
  return d.toLocaleDateString('en-US', { 
    month: 'short', 
    day: 'numeric',
    year: 'numeric'
  })
}

const formatNumber = (num: number) => {
  return new Intl.NumberFormat(isRTL ? 'ar-OM' : 'en-OM').format(num)
}

const formatMaintenanceDue = (maintenance: MaintenanceItem) => {
  if (maintenance.dueDate) {
    const dueText = isRTL ? 'مستحق:' : 'Due:'
    return `${dueText} ${formatDate(maintenance.dueDate)}`
  }
  
  if (maintenance.dueMileage) {
    const atText = isRTL ? 'عند:' : 'At:'
    const kmText = isRTL ? 'كم' : 'km'
    return `${atText} ${formatNumber(maintenance.dueMileage)} ${kmText}`
  }
  
  return isRTL ? 'قريباً' : 'Soon'
}

const handleImageError = () => {
  // Could emit an event or set a flag to show placeholder
  console.warn('Failed to load vehicle image')
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

const handleViewHistory = () => {
  emit('view-history')
}

const handleCardClick = () => {
  emit('click')
}
</script>

<style lang="scss" scoped>
.vehicle-card {
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
    .vehicle-card__service-history,
    .vehicle-card__maintenance,
    .vehicle-card__specifications {
      display: none;
    }
  }
  
  // RTL support
  &--rtl {
    direction: rtl;
    text-align: right;
  }
}

.vehicle-card__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-4);
}

.vehicle-card__title-section {
  flex: 1;
}

.vehicle-card__vehicle-name {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0 0 var(--spacing-2) 0;
}

.vehicle-card__identifiers {
  display: flex;
  gap: var(--spacing-2);
  flex-wrap: wrap;
}

.vehicle-card__actions {
  display: flex;
  gap: var(--spacing-1);
}

.vehicle-card__image-section {
  margin-bottom: var(--spacing-4);
}

.vehicle-card__image-container {
  position: relative;
  width: 100%;
  height: 200px;
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--color-background-subtle);
}

.vehicle-card__image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.vehicle-card__image-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  background: var(--color-background-subtle);
}

.vehicle-card__specifications {
  margin-bottom: var(--spacing-4);
}

.vehicle-card__spec-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-3);
}

.vehicle-card__spec-item {
  display: flex;
  flex-direction: column;
}

.vehicle-card__spec-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-1);
}

.vehicle-card__spec-value {
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

.vehicle-card__status-section {
  margin-bottom: var(--spacing-4);
  padding: var(--spacing-3);
  background: var(--color-background-subtle);
  border-radius: var(--radius-md);
}

.vehicle-card__mileage {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-3);
}

.vehicle-card__mileage-current {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.vehicle-card__mileage-value {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.vehicle-card__mileage-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.vehicle-card__last-service {
  text-align: right;
  
  .vehicle-card--rtl & {
    text-align: left;
  }
}

.vehicle-card__last-service-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.vehicle-card__last-service-value {
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

.vehicle-card__condition {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.vehicle-card__condition-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.vehicle-card__condition-rating {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
}

.vehicle-card__condition-star {
  color: var(--color-border-subtle);
  
  &--active {
    color: var(--color-warning);
  }
}

.vehicle-card__condition-text {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  margin-left: var(--spacing-2);
  
  .vehicle-card--rtl & {
    margin-left: 0;
    margin-right: var(--spacing-2);
  }
}

.vehicle-card__owner-section {
  margin-bottom: var(--spacing-4);
  padding-top: var(--spacing-3);
  border-top: 1px solid var(--color-border-subtle);
}

.vehicle-card__owner-title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-secondary);
  margin: 0 0 var(--spacing-2) 0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.vehicle-card__owner-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.vehicle-card__owner-details {
  flex: 1;
}

.vehicle-card__owner-name {
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

.vehicle-card__owner-contact {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-top: var(--spacing-1);
}

.vehicle-card__service-history,
.vehicle-card__maintenance {
  margin-bottom: var(--spacing-4);
  padding-top: var(--spacing-3);
  border-top: 1px solid var(--color-border-subtle);
}

.vehicle-card__service-header,
.vehicle-card__maintenance-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-3);
}

.vehicle-card__service-title,
.vehicle-card__maintenance-title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-secondary);
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.vehicle-card__service-list,
.vehicle-card__maintenance-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.vehicle-card__service-item,
.vehicle-card__maintenance-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-2);
  background: var(--color-background-subtle);
  border-radius: var(--radius-sm);
  
  &--overdue {
    background: var(--color-error-background);
    border: 1px solid var(--color-error-border);
  }
}

.vehicle-card__service-icon,
.vehicle-card__maintenance-icon {
  flex-shrink: 0;
}

.vehicle-card__service-details,
.vehicle-card__maintenance-details {
  flex: 1;
}

.vehicle-card__service-name,
.vehicle-card__maintenance-name {
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
}

.vehicle-card__service-date,
.vehicle-card__maintenance-due {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.vehicle-card__service-status {
  flex-shrink: 0;
}

.vehicle-card__action-menu {
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
  
  .vehicle-card--rtl & {
    right: auto;
    left: var(--spacing-2);
  }
}

.vehicle-card__action-item {
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
  .vehicle-card {
    --card-padding: var(--spacing-3);
  }
  
  .vehicle-card__header {
    flex-direction: column;
    gap: var(--spacing-2);
  }
  
  .vehicle-card__actions {
    align-self: flex-end;
  }
  
  .vehicle-card__spec-grid {
    grid-template-columns: 1fr;
  }
  
  .vehicle-card__mileage {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-2);
  }
  
  .vehicle-card__last-service {
    text-align: left;
    
    .vehicle-card--rtl & {
      text-align: right;
    }
  }
}
</style>