<!--
  TechnicianAssignment Component - Universal Workshop Frontend V2
  
  A comprehensive component for assigning technicians to service orders
  with skills matching, availability checking, and workload management.
-->

<template>
  <div :class="assignmentClasses" :dir="isRTL ? 'rtl' : 'ltr'">
    <!-- Header -->
    <div class="technician-assignment__header">
      <h3 class="technician-assignment__title">
        {{ isRTL ? 'تكليف فني' : 'Assign Technician' }}
      </h3>
      <p v-if="serviceOrder" class="technician-assignment__subtitle">
        {{ isRTL ? 'طلب خدمة:' : 'Service Order:' }} {{ serviceOrder.orderNumber }}
      </p>
    </div>

    <!-- Search & Filters -->
    <div class="technician-assignment__filters">
      <div class="technician-assignment__search">
        <UWInput
          v-model="searchQuery"
          :placeholder="isRTL ? 'البحث عن فني...' : 'Search technicians...'"
          icon-start="search"
          size="sm"
          clearable
        />
      </div>
      
      <div class="technician-assignment__filter-buttons">
        <UWButton
          v-for="filter in availabilityFilters"
          :key="filter.key"
          :variant="selectedFilter === filter.key ? 'primary' : 'outline'"
          size="sm"
          @click="setFilter(filter.key)"
        >
          {{ isRTL && filter.labelAr ? filter.labelAr : filter.label }}
        </UWButton>
      </div>
    </div>

    <!-- Service Requirements -->
    <div v-if="serviceOrder" class="technician-assignment__requirements">
      <h4 class="technician-assignment__section-title">
        {{ isRTL ? 'متطلبات الخدمة' : 'Service Requirements' }}
      </h4>
      
      <div class="technician-assignment__req-grid">
        <div class="technician-assignment__req-item">
          <UWIcon name="wrench" size="sm" />
          <span>{{ getServiceTypeText() }}</span>
        </div>
        
        <div v-if="serviceOrder.estimatedDuration" class="technician-assignment__req-item">
          <UWIcon name="clock" size="sm" />
          <span>{{ formatDuration(serviceOrder.estimatedDuration) }}</span>
        </div>
        
        <div v-if="serviceOrder.priority" class="technician-assignment__req-item">
          <UWIcon :name="getPriorityIcon()" size="sm" :color="getPriorityColor()" />
          <span>{{ getPriorityText() }}</span>
        </div>
        
        <div v-if="requiredSkills?.length" class="technician-assignment__req-item">
          <UWIcon name="star" size="sm" />
          <span>
            {{ isRTL ? 'المهارات المطلوبة:' : 'Required Skills:' }}
            {{ requiredSkills.join(', ') }}
          </span>
        </div>
      </div>
    </div>

    <!-- Technician List -->
    <div class="technician-assignment__list">
      <div v-if="loading" class="technician-assignment__loading">
        <UWIcon name="loading" spin size="lg" />
        <span>{{ isRTL ? 'جاري التحميل...' : 'Loading...' }}</span>
      </div>
      
      <div v-else-if="filteredTechnicians.length === 0" class="technician-assignment__empty">
        <UWIcon name="users" size="lg" color="var(--color-text-tertiary)" />
        <span>{{ isRTL ? 'لا يوجد فنيين متاحين' : 'No technicians available' }}</span>
      </div>
      
      <div v-else class="technician-assignment__technicians">
        <div
          v-for="technician in filteredTechnicians"
          :key="technician.id"
          class="technician-assignment__technician-card"
          :class="{
            'technician-assignment__technician-card--selected': selectedTechnician?.id === technician.id,
            'technician-assignment__technician-card--recommended': isRecommended(technician),
            'technician-assignment__technician-card--busy': technician.status === 'busy'
          }"
          @click="selectTechnician(technician)"
        >
          <!-- Technician Header -->
          <div class="technician-assignment__tech-header">
            <UWAvatar 
              :user="technician" 
              :status="technician.status"
              size="md"
            />
            
            <div class="technician-assignment__tech-info">
              <div class="technician-assignment__tech-name">
                {{ isRTL && technician.nameAr ? technician.nameAr : technician.name }}
              </div>
              <div class="technician-assignment__tech-title">
                {{ isRTL && technician.titleAr ? technician.titleAr : technician.title }}
              </div>
              <div class="technician-assignment__tech-status">
                <UWBadge 
                  :content="getStatusText(technician.status)"
                  :variant="getStatusVariant(technician.status)"
                  size="xs"
                />
              </div>
            </div>
            
            <div class="technician-assignment__tech-rating">
              <div class="technician-assignment__rating-stars">
                <div 
                  v-for="star in 5" 
                  :key="star"
                  class="technician-assignment__rating-star"
                  :class="{ 'technician-assignment__rating-star--active': star <= (technician.rating || 0) }"
                >
                  <UWIcon name="star" size="xs" />
                </div>
              </div>
              <span class="technician-assignment__rating-text">
                {{ technician.rating || 0 }}/5
              </span>
            </div>
          </div>

          <!-- Skills & Specializations -->
          <div v-if="technician.skills?.length" class="technician-assignment__tech-skills">
            <div class="technician-assignment__skills-label">
              {{ isRTL ? 'المهارات:' : 'Skills:' }}
            </div>
            <div class="technician-assignment__skills-list">
              <UWBadge
                v-for="skill in technician.skills.slice(0, 3)"
                :key="skill"
                :content="skill"
                variant="secondary"
                size="xs"
              />
              <span v-if="technician.skills.length > 3" class="technician-assignment__skills-more">
                +{{ technician.skills.length - 3 }} {{ isRTL ? 'أكثر' : 'more' }}
              </span>
            </div>
          </div>

          <!-- Current Workload -->
          <div class="technician-assignment__tech-workload">
            <div class="technician-assignment__workload-header">
              <span class="technician-assignment__workload-label">
                {{ isRTL ? 'العبء الحالي:' : 'Current Workload:' }}
              </span>
              <span class="technician-assignment__workload-count">
                {{ technician.currentJobs || 0 }}/{{ technician.maxJobs || 5 }}
              </span>
            </div>
            
            <div class="technician-assignment__workload-bar">
              <div 
                class="technician-assignment__workload-fill"
                :style="{ width: `${getWorkloadPercentage(technician)}%` }"
                :class="{
                  'technician-assignment__workload-fill--high': getWorkloadPercentage(technician) > 80,
                  'technician-assignment__workload-fill--medium': getWorkloadPercentage(technician) > 60
                }"
              ></div>
            </div>
          </div>

          <!-- Estimated Availability -->
          <div v-if="technician.nextAvailable" class="technician-assignment__tech-availability">
            <UWIcon name="clock" size="sm" />
            <span>
              {{ isRTL ? 'متاح في:' : 'Available at:' }}
              {{ formatTime(technician.nextAvailable) }}
            </span>
          </div>

          <!-- Match Score -->
          <div v-if="getMatchScore(technician) > 0" class="technician-assignment__match-score">
            <div class="technician-assignment__match-label">
              {{ isRTL ? 'درجة التطابق:' : 'Match Score:' }}
            </div>
            <div class="technician-assignment__match-percentage">
              {{ getMatchScore(technician) }}%
            </div>
          </div>

          <!-- Recommendation Badge -->
          <div v-if="isRecommended(technician)" class="technician-assignment__recommended-badge">
            <UWIcon name="star" size="sm" color="var(--color-warning)" />
            <span>{{ isRTL ? 'موصى به' : 'Recommended' }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Assignment Actions -->
    <div class="technician-assignment__actions">
      <UWButton
        variant="outline"
        @click="handleCancel"
        :disabled="loading"
      >
        {{ isRTL ? 'إلغاء' : 'Cancel' }}
      </UWButton>
      
      <UWButton
        :disabled="!selectedTechnician || loading"
        :loading="assigning"
        @click="handleAssign"
      >
        {{ isRTL ? 'تكليف الفني' : 'Assign Technician' }}
      </UWButton>
    </div>

    <!-- Assignment Details Modal (if needed) -->
    <div v-if="selectedTechnician && showDetails" class="technician-assignment__details">
      <div class="technician-assignment__details-content">
        <h4>{{ isRTL ? 'تفاصيل التكليف' : 'Assignment Details' }}</h4>
        
        <div class="technician-assignment__detail-item">
          <label>{{ isRTL ? 'تاريخ البدء المتوقع:' : 'Expected Start Time:' }}</label>
          <UWDatePicker
            v-model="expectedStartTime"
            :min-date="new Date()"
            show-time
          />
        </div>
        
        <div class="technician-assignment__detail-item">
          <label>{{ isRTL ? 'ملاحظات خاصة:' : 'Special Notes:' }}</label>
          <UWInput
            v-model="assignmentNotes"
            type="textarea"
            :placeholder="isRTL ? 'أي ملاحظات للفني...' : 'Any notes for the technician...'"
            rows="3"
          />
        </div>
        
        <div class="technician-assignment__detail-item">
          <UWCheckbox
            v-model="notifyTechnician"
            :label="isRTL ? 'إرسال إشعار للفني' : 'Notify technician'"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, inject, watch } from 'vue'
import { UWButton } from '@/components/base'
import { UWIcon, UWBadge, UWAvatar } from '@/components/primitives'
import { UWInput, UWDatePicker, UWCheckbox } from '@/components/forms'

// Types
interface Technician {
  id: string
  name: string
  nameAr?: string
  title: string
  titleAr?: string
  status: 'available' | 'busy' | 'offline' | 'break'
  rating?: number
  skills?: string[]
  specializations?: string[]
  currentJobs?: number
  maxJobs?: number
  nextAvailable?: string | Date
  avatar?: string
}

interface ServiceOrder {
  id: string
  orderNumber: string
  serviceType: string
  priority: 'low' | 'medium' | 'high' | 'urgent'
  estimatedDuration?: number
  requiredSkills?: string[]
}

interface TechnicianFilter {
  key: string
  label: string
  labelAr?: string
}

export interface TechnicianAssignmentProps {
  technicians: Technician[]
  serviceOrder?: ServiceOrder
  requiredSkills?: string[]
  loading?: boolean
  showDetails?: boolean
  autoRecommend?: boolean
  size?: 'sm' | 'md' | 'lg'
}

export interface TechnicianAssignmentEmits {
  'assign': [technicianId: string, details: AssignmentDetails]
  'cancel': []
  'technician-select': [technician: Technician]
}

interface AssignmentDetails {
  expectedStartTime?: Date
  notes?: string
  notifyTechnician: boolean
}

const props = withDefaults(defineProps<TechnicianAssignmentProps>(), {
  loading: false,
  showDetails: false,
  autoRecommend: true,
  size: 'md',
  technicians: () => [],
  requiredSkills: () => []
})

const emit = defineEmits<TechnicianAssignmentEmits>()

// Injected context
const isRTL = inject('isRTL', false)

// Local state
const searchQuery = ref('')
const selectedFilter = ref('all')
const selectedTechnician = ref<Technician | null>(null)
const assigning = ref(false)
const expectedStartTime = ref<Date | null>(null)
const assignmentNotes = ref('')
const notifyTechnician = ref(true)

// Filters
const availabilityFilters: TechnicianFilter[] = [
  { key: 'all', label: 'All', labelAr: 'الكل' },
  { key: 'available', label: 'Available', labelAr: 'متاح' },
  { key: 'busy', label: 'Busy', labelAr: 'مشغول' },
  { key: 'recommended', label: 'Recommended', labelAr: 'موصى به' }
]

// Computed properties
const assignmentClasses = computed(() => [
  'technician-assignment',
  `technician-assignment--${props.size}`,
  {
    'technician-assignment--rtl': isRTL,
    'technician-assignment--loading': props.loading
  }
])

const filteredTechnicians = computed(() => {
  let filtered = props.technicians

  // Search filter
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(tech => 
      tech.name.toLowerCase().includes(query) ||
      tech.nameAr?.toLowerCase().includes(query) ||
      tech.title.toLowerCase().includes(query) ||
      tech.skills?.some(skill => skill.toLowerCase().includes(query))
    )
  }

  // Availability filter
  if (selectedFilter.value !== 'all') {
    switch (selectedFilter.value) {
      case 'available':
        filtered = filtered.filter(tech => tech.status === 'available')
        break
      case 'busy':
        filtered = filtered.filter(tech => tech.status === 'busy')
        break
      case 'recommended':
        filtered = filtered.filter(tech => isRecommended(tech))
        break
    }
  }

  // Sort by recommendation score and availability
  return filtered.sort((a, b) => {
    const aRecommended = isRecommended(a) ? 1 : 0
    const bRecommended = isRecommended(b) ? 1 : 0
    
    if (aRecommended !== bRecommended) {
      return bRecommended - aRecommended
    }
    
    const aScore = getMatchScore(a)
    const bScore = getMatchScore(b)
    
    if (aScore !== bScore) {
      return bScore - aScore
    }
    
    // Sort by availability
    const statusOrder = { available: 0, break: 1, busy: 2, offline: 3 }
    return statusOrder[a.status] - statusOrder[b.status]
  })
})

// Methods
const setFilter = (filterKey: string) => {
  selectedFilter.value = filterKey
}

const selectTechnician = (technician: Technician) => {
  selectedTechnician.value = technician
  emit('technician-select', technician)
}

const isRecommended = (technician: Technician): boolean => {
  if (!props.autoRecommend) return false
  
  const matchScore = getMatchScore(technician)
  const isAvailable = technician.status === 'available'
  const hasLowWorkload = getWorkloadPercentage(technician) < 80
  const hasGoodRating = (technician.rating || 0) >= 4
  
  return matchScore >= 70 && isAvailable && hasLowWorkload && hasGoodRating
}

const getMatchScore = (technician: Technician): number => {
  if (!props.serviceOrder && !props.requiredSkills?.length) return 0
  
  let score = 0
  let maxScore = 0
  
  // Skills matching
  if (props.requiredSkills?.length && technician.skills?.length) {
    maxScore += 50
    const matchingSkills = props.requiredSkills.filter(skill => 
      technician.skills?.includes(skill)
    )
    score += (matchingSkills.length / props.requiredSkills.length) * 50
  }
  
  // Service type matching
  if (props.serviceOrder?.serviceType && technician.specializations?.length) {
    maxScore += 30
    if (technician.specializations.includes(props.serviceOrder.serviceType)) {
      score += 30
    }
  }
  
  // Rating bonus
  if (technician.rating) {
    maxScore += 20
    score += (technician.rating / 5) * 20
  }
  
  return maxScore > 0 ? Math.round((score / maxScore) * 100) : 0
}

const getWorkloadPercentage = (technician: Technician): number => {
  const current = technician.currentJobs || 0
  const max = technician.maxJobs || 5
  return Math.round((current / max) * 100)
}

const getStatusText = (status: string) => {
  const statusMap = {
    available: { en: 'Available', ar: 'متاح' },
    busy: { en: 'Busy', ar: 'مشغول' },
    offline: { en: 'Offline', ar: 'غير متصل' },
    break: { en: 'On Break', ar: 'في استراحة' }
  }
  
  const statusObj = statusMap[status as keyof typeof statusMap]
  return statusObj ? (isRTL ? statusObj.ar : statusObj.en) : status
}

const getStatusVariant = (status: string) => {
  const variantMap = {
    available: 'success',
    busy: 'warning',
    offline: 'error',
    break: 'secondary'
  }
  
  return variantMap[status as keyof typeof variantMap] || 'default'
}

const getServiceTypeText = () => {
  if (!props.serviceOrder) return ''
  return props.serviceOrder.serviceType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

const getPriorityIcon = () => {
  const iconMap = {
    low: 'arrow-down',
    medium: 'minus',
    high: 'arrow-up',
    urgent: 'alert-triangle'
  }
  
  return iconMap[props.serviceOrder?.priority || 'medium']
}

const getPriorityColor = () => {
  const colorMap = {
    low: 'var(--color-success)',
    medium: 'var(--color-warning)',
    high: 'var(--color-error)',
    urgent: 'var(--color-error)'
  }
  
  return colorMap[props.serviceOrder?.priority || 'medium']
}

const getPriorityText = () => {
  if (!props.serviceOrder?.priority) return ''
  
  const priorityMap = {
    low: { en: 'Low', ar: 'منخفض' },
    medium: { en: 'Medium', ar: 'متوسط' },
    high: { en: 'High', ar: 'عالي' },
    urgent: { en: 'Urgent', ar: 'عاجل' }
  }
  
  const priority = priorityMap[props.serviceOrder.priority]
  return isRTL ? priority.ar : priority.en
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

const formatTime = (time: string | Date) => {
  const d = new Date(time)
  if (isRTL) {
    return d.toLocaleTimeString('ar-SA', { hour: '2-digit', minute: '2-digit' })
  }
  return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
}

const handleCancel = () => {
  emit('cancel')
}

const handleAssign = async () => {
  if (!selectedTechnician.value) return
  
  assigning.value = true
  
  try {
    const details: AssignmentDetails = {
      expectedStartTime: expectedStartTime.value || undefined,
      notes: assignmentNotes.value,
      notifyTechnician: notifyTechnician.value
    }
    
    emit('assign', selectedTechnician.value.id, details)
  } finally {
    assigning.value = false
  }
}

// Auto-select first recommended technician
watch(() => props.technicians, () => {
  if (props.autoRecommend && !selectedTechnician.value) {
    const recommended = filteredTechnicians.value.find(isRecommended)
    if (recommended) {
      selectTechnician(recommended)
    }
  }
}, { immediate: true })
</script>

<style lang="scss" scoped>
.technician-assignment {
  --assignment-padding: var(--spacing-4);
  --assignment-border-radius: var(--radius-lg);
  --assignment-background: var(--color-background);
  
  background: var(--assignment-background);
  border-radius: var(--assignment-border-radius);
  padding: var(--assignment-padding);
  
  // Sizes
  &--sm {
    --assignment-padding: var(--spacing-3);
    font-size: var(--font-size-sm);
  }
  
  &--lg {
    --assignment-padding: var(--spacing-6);
    font-size: var(--font-size-lg);
  }
  
  // RTL support
  &--rtl {
    direction: rtl;
    text-align: right;
  }
  
  &--loading {
    opacity: 0.7;
    pointer-events: none;
  }
}

.technician-assignment__header {
  margin-bottom: var(--spacing-4);
}

.technician-assignment__title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0 0 var(--spacing-1) 0;
}

.technician-assignment__subtitle {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin: 0;
}

.technician-assignment__filters {
  display: flex;
  gap: var(--spacing-3);
  margin-bottom: var(--spacing-4);
  flex-wrap: wrap;
}

.technician-assignment__search {
  flex: 1;
  min-width: 200px;
}

.technician-assignment__filter-buttons {
  display: flex;
  gap: var(--spacing-2);
}

.technician-assignment__requirements {
  margin-bottom: var(--spacing-4);
  padding: var(--spacing-3);
  background: var(--color-background-subtle);
  border-radius: var(--radius-md);
}

.technician-assignment__section-title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-secondary);
  margin: 0 0 var(--spacing-2) 0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.technician-assignment__req-grid {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-3);
}

.technician-assignment__req-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.technician-assignment__list {
  margin-bottom: var(--spacing-4);
  max-height: 400px;
  overflow-y: auto;
}

.technician-assignment__loading,
.technician-assignment__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-8);
  color: var(--color-text-secondary);
  gap: var(--spacing-2);
}

.technician-assignment__technicians {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.technician-assignment__technician-card {
  position: relative;
  padding: var(--spacing-4);
  background: var(--color-background-elevated);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    box-shadow: var(--shadow-md);
    border-color: var(--color-border-primary);
  }
  
  &--selected {
    border-color: var(--color-primary);
    box-shadow: 0 0 0 1px var(--color-primary);
  }
  
  &--recommended {
    border-color: var(--color-warning);
    background: var(--color-warning-background);
  }
  
  &--busy {
    opacity: 0.7;
  }
}

.technician-assignment__tech-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  margin-bottom: var(--spacing-3);
}

.technician-assignment__tech-info {
  flex: 1;
}

.technician-assignment__tech-name {
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-1);
}

.technician-assignment__tech-title {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-1);
}

.technician-assignment__tech-rating {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
}

.technician-assignment__rating-stars {
  display: flex;
  gap: 2px;
}

.technician-assignment__rating-star {
  color: var(--color-border-subtle);
  
  &--active {
    color: var(--color-warning);
  }
}

.technician-assignment__rating-text {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.technician-assignment__tech-skills {
  margin-bottom: var(--spacing-3);
}

.technician-assignment__skills-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-1);
}

.technician-assignment__skills-list {
  display: flex;
  gap: var(--spacing-1);
  flex-wrap: wrap;
  align-items: center;
}

.technician-assignment__skills-more {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

.technician-assignment__tech-workload {
  margin-bottom: var(--spacing-2);
}

.technician-assignment__workload-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-1);
}

.technician-assignment__workload-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.technician-assignment__workload-count {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

.technician-assignment__workload-bar {
  height: 4px;
  background: var(--color-background-subtle);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.technician-assignment__workload-fill {
  height: 100%;
  background: var(--color-success);
  transition: width 0.3s ease;
  
  &--medium {
    background: var(--color-warning);
  }
  
  &--high {
    background: var(--color-error);
  }
}

.technician-assignment__tech-availability {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-2);
}

.technician-assignment__match-score {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-2);
  background: var(--color-primary-background);
  border-radius: var(--radius-sm);
  margin-bottom: var(--spacing-2);
}

.technician-assignment__match-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.technician-assignment__match-percentage {
  font-weight: var(--font-weight-semibold);
  color: var(--color-primary);
}

.technician-assignment__recommended-badge {
  position: absolute;
  top: var(--spacing-2);
  right: var(--spacing-2);
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  padding: var(--spacing-1) var(--spacing-2);
  background: var(--color-warning);
  color: white;
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  
  .technician-assignment--rtl & {
    right: auto;
    left: var(--spacing-2);
  }
}

.technician-assignment__actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-3);
  padding-top: var(--spacing-4);
  border-top: 1px solid var(--color-border-subtle);
}

.technician-assignment__details {
  margin-top: var(--spacing-4);
  padding-top: var(--spacing-4);
  border-top: 1px solid var(--color-border-subtle);
}

.technician-assignment__details-content {
  h4 {
    font-size: var(--font-size-md);
    font-weight: var(--font-weight-semibold);
    color: var(--color-text-primary);
    margin: 0 0 var(--spacing-3) 0;
  }
}

.technician-assignment__detail-item {
  margin-bottom: var(--spacing-3);
  
  label {
    display: block;
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    color: var(--color-text-secondary);
    margin-bottom: var(--spacing-1);
  }
}

// Responsive design
@media (max-width: 768px) {
  .technician-assignment__filters {
    flex-direction: column;
  }
  
  .technician-assignment__filter-buttons {
    justify-content: center;
  }
  
  .technician-assignment__req-grid {
    flex-direction: column;
    gap: var(--spacing-2);
  }
  
  .technician-assignment__tech-header {
    flex-wrap: wrap;
  }
  
  .technician-assignment__actions {
    flex-direction: column-reverse;
    
    .uw-button {
      width: 100%;
      justify-content: center;
    }
  }
}
</style>