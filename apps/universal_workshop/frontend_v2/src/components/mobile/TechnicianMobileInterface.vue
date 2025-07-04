<!--
  TechnicianMobileInterface Component - Universal Workshop Frontend V2
  Advanced mobile interface for technicians with real-time updates,
  touch-optimized workflows, barcode scanning, and offline capabilities.
-->
<template>
  <div :class="interfaceClasses" :dir="isRTL ? 'rtl' : 'ltr'">
    <!-- Mobile Header with Technician Info -->
    <div class="mobile-header">
      <div class="technician-info">
        <div class="avatar-section">
          <img 
            :src="technician.photoUrl || defaultTechnicianAvatar" 
            :alt="technician.name"
            class="technician-avatar"
          >
          <div class="status-indicator" :class="technician.status">
            <Icon :name="getStatusIcon(technician.status)" />
          </div>
        </div>
        
        <div class="tech-details">
          <h2>{{ preferArabic ? technician.nameAr : technician.name }}</h2>
          <p class="tech-role">{{ preferArabic ? technician.roleAr : technician.role }}</p>
          <div class="tech-stats">
            <span class="active-tasks">
              {{ activeTasks.length }} {{ preferArabic ? 'مهام نشطة' : 'active tasks' }}
            </span>
          </div>
        </div>
        
        <div class="header-controls">
          <Button variant="outline" size="sm" @click="toggleAvailability">
            {{ technician.isAvailable 
              ? (preferArabic ? 'متاح' : 'Available')
              : (preferArabic ? 'مشغول' : 'Busy')
            }}
          </Button>
        </div>
      </div>
      
      <!-- Quick Stats Bar -->
      <div class="stats-bar">
        <div class="stat-item">
          <Icon name="clock" />
          <span>{{ formatWorkingHours(todayWorkingHours) }}</span>
        </div>
        <div class="stat-item">
          <Icon name="check-circle" />
          <span>{{ completedToday }}</span>
        </div>
        <div class="stat-item">
          <Icon name="star" />
          <span>{{ averageRating.toFixed(1) }}</span>
        </div>
      </div>
    </div>

    <!-- Service Tasks List -->
    <div class="tasks-section">
      <div class="section-header">
        <h3>{{ preferArabic ? 'مهامي اليوم' : 'My Tasks Today' }}</h3>
        <div class="task-filters">
          <Button
            v-for="filter in taskFilters"
            :key="filter.id"
            :variant="activeFilter === filter.id ? 'primary' : 'outline'"
            size="sm"
            @click="setActiveFilter(filter.id)"
          >
            {{ preferArabic ? filter.labelAr : filter.label }}
          </Button>
        </div>
      </div>
      
      <div class="tasks-list">
        <TransitionGroup name="task" tag="div">
          <div
            v-for="task in filteredTasks"
            :key="task.id"
            class="task-card"
            :class="getTaskCardClass(task)"
            @click="openTaskDetails(task.id)"
          >
            <!-- Task Header -->
            <div class="task-header">
              <div class="task-priority" :class="task.priority">
                <Icon :name="getPriorityIcon(task.priority)" />
              </div>
              
              <div class="task-info">
                <h4>{{ preferArabic ? task.titleAr : task.title }}</h4>
                <p class="customer-name">{{ task.customerName }}</p>
              </div>
              
              <div class="task-status" :class="task.status">
                {{ getTaskStatusText(task.status) }}
              </div>
            </div>

            <!-- Vehicle Info -->
            <div class="vehicle-info">
              <img :src="task.vehicle.imageUrl" :alt="task.vehicle.description">
              <div class="vehicle-details">
                <span class="vehicle-model">{{ task.vehicle.make }} {{ task.vehicle.model }}</span>
                <span class="plate-number">{{ task.vehicle.plateNumber }}</span>
              </div>
            </div>

            <!-- Task Progress -->
            <div class="task-progress">
              <div class="progress-bar">
                <div 
                  class="progress-fill" 
                  :style="{ width: `${task.progressPercentage}%` }"
                ></div>
              </div>
              <span class="progress-text">{{ task.progressPercentage }}%</span>
            </div>

            <!-- Quick Actions -->
            <div class="task-actions">
              <Button
                v-if="task.status === 'assigned'"
                variant="primary"
                size="sm"
                @click.stop="startTask(task.id)"
              >
                <Icon name="play" />
                {{ preferArabic ? 'بدء العمل' : 'Start Work' }}
              </Button>
              
              <Button
                v-if="task.status === 'in_progress'"
                variant="warning"
                size="sm"
                @click.stop="pauseTask(task.id)"
              >
                <Icon name="pause" />
                {{ preferArabic ? 'إيقاف مؤقت' : 'Pause' }}
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                @click.stop="openScanner(task.id)"
              >
                <Icon name="scan" />
                {{ preferArabic ? 'مسح' : 'Scan' }}
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                @click.stop="takePhoto(task.id)"
              >
                <Icon name="camera" />
                {{ preferArabic ? 'صورة' : 'Photo' }}
              </Button>
            </div>

            <!-- Time Tracking -->
            <div class="time-tracking" v-if="task.status === 'in_progress'">
              <Icon name="clock" />
              <span class="elapsed-time">{{ formatElapsedTime(task.startTime) }}</span>
              <span class="estimated-time">
                / {{ formatDuration(task.estimatedDuration) }}
              </span>
            </div>
          </div>
        </TransitionGroup>
      </div>
    </div>

    <!-- Bottom Navigation -->
    <div class="bottom-nav">
      <Button
        v-for="navItem in bottomNavItems"
        :key="navItem.id"
        :variant="activeNavItem === navItem.id ? 'primary' : 'ghost'"
        class="nav-item"
        @click="navigateTo(navItem.id)"
      >
        <Icon :name="navItem.icon" />
        <span>{{ preferArabic ? navItem.labelAr : navItem.label }}</span>
      </Button>
    </div>

    <!-- Floating Action Button -->
    <div class="fab-container">
      <Button
        variant="primary"
        size="lg"
        class="scan-fab"
        @click="openQuickScanner"
      >
        <Icon name="scan" />
      </Button>
    </div>

    <!-- Offline Sync Indicator -->
    <div class="sync-indicator" v-if="pendingSyncCount > 0">
      <Icon name="sync" :class="{ 'animate-spin': isSyncing }" />
      <span>{{ pendingSyncCount }} {{ preferArabic ? 'في الانتظار' : 'pending' }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'

// Stores
import { useTechnicianStore } from '@/stores/technician'
import { useTaskStore } from '@/stores/task'
import { useLocalizationStore } from '@/stores/localization'
import { useConnectivityStore } from '@/stores/connectivity'

// Composables
import { useRealTimeUpdates } from '@/composables/useRealTimeUpdates'
import { useBarcodeScanner } from '@/composables/useBarcodeScanner'
import { useMobileCamera } from '@/composables/useMobileCamera'
import { useOfflineSync } from '@/composables/useOfflineSync'
import { useTimeTracking } from '@/composables/useTimeTracking'

// Components
import { Button, Icon } from '@/components/ui'

// Types
interface TechnicianMobileInterfaceProps {
  technicianId?: string
  realTimeEnabled?: boolean
  offlineCapable?: boolean
}

// Props
const props = withDefaults(defineProps<TechnicianMobileInterfaceProps>(), {
  realTimeEnabled: true,
  offlineCapable: true
})

// Stores
const technicianStore = useTechnicianStore()
const taskStore = useTaskStore()
const localizationStore = useLocalizationStore()
const connectivityStore = useConnectivityStore()

// Store refs
const { technician, todayWorkingHours, completedToday, averageRating } = storeToRefs(technicianStore)
const { activeTasks } = storeToRefs(taskStore)
const { preferArabic, isRTL } = storeToRefs(localizationStore)
const { isOnline, pendingSyncCount, isSyncing } = storeToRefs(connectivityStore)

// Composables
const router = useRouter()
const realTimeUpdates = useRealTimeUpdates()
const barcodeScanner = useBarcodeScanner()
const mobileCamera = useMobileCamera()
const offlineSync = useOfflineSync()
const timeTracking = useTimeTracking()

// Reactive state
const activeFilter = ref('all')
const activeNavItem = ref('tasks')

// Computed properties
const interfaceClasses = computed(() => [
  'technician-mobile-interface',
  {
    'rtl': isRTL.value,
    'offline': !isOnline.value
  }
])

const taskFilters = computed(() => [
  { id: 'all', label: 'All', labelAr: 'الكل' },
  { id: 'assigned', label: 'Assigned', labelAr: 'مُعيَّن' },
  { id: 'in_progress', label: 'In Progress', labelAr: 'قيد التنفيذ' },
  { id: 'waiting', label: 'Waiting', labelAr: 'في الانتظار' }
])

const filteredTasks = computed(() => {
  if (activeFilter.value === 'all') return activeTasks.value
  return activeTasks.value.filter(task => task.status === activeFilter.value)
})

const bottomNavItems = computed(() => [
  { id: 'tasks', label: 'Tasks', labelAr: 'المهام', icon: 'list' },
  { id: 'inventory', label: 'Parts', labelAr: 'القطع', icon: 'package' },
  { id: 'history', label: 'History', labelAr: 'التاريخ', icon: 'history' },
  { id: 'profile', label: 'Profile', labelAr: 'الملف', icon: 'user' }
])

const defaultTechnicianAvatar = '/assets/universal_workshop/images/default-technician-avatar.png'

// Methods
const getStatusIcon = (status: string) => {
  const icons = {
    available: 'check-circle',
    busy: 'clock',
    break: 'coffee',
    offline: 'x-circle'
  }
  return icons[status as keyof typeof icons] || 'circle'
}

const getTaskCardClass = (task: any) => ({
  [`priority-${task.priority}`]: true,
  [`status-${task.status}`]: true,
  'overdue': task.isOverdue,
  'urgent': task.isUrgent
})

const getPriorityIcon = (priority: string) => {
  const icons = {
    low: 'arrow-down',
    medium: 'minus',
    high: 'arrow-up',
    urgent: 'alert-triangle'
  }
  return icons[priority as keyof typeof icons] || 'minus'
}

const getTaskStatusText = (status: string) => {
  const statusTexts = {
    assigned: { ar: 'مُعيَّن', en: 'Assigned' },
    in_progress: { ar: 'قيد التنفيذ', en: 'In Progress' },
    waiting_parts: { ar: 'انتظار قطع', en: 'Waiting Parts' },
    waiting_approval: { ar: 'انتظار موافقة', en: 'Waiting Approval' },
    completed: { ar: 'مكتمل', en: 'Completed' }
  }
  const text = statusTexts[status as keyof typeof statusTexts]
  return preferArabic.value ? text?.ar : text?.en
}

const formatWorkingHours = (minutes: number) => {
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  return `${hours}:${mins.toString().padStart(2, '0')}`
}

const formatElapsedTime = (startTime: Date) => {
  return timeTracking.formatElapsedTime(startTime)
}

const formatDuration = (minutes: number) => {
  return timeTracking.formatDuration(minutes)
}

// Event handlers
const toggleAvailability = async () => {
  await technicianStore.toggleAvailability()
}

const setActiveFilter = (filterId: string) => {
  activeFilter.value = filterId
}

const openTaskDetails = (taskId: string) => {
  router.push(`/mobile/technician/tasks/${taskId}`)
}

const startTask = async (taskId: string) => {
  try {
    await taskStore.startTask(taskId)
    await timeTracking.startTimer(taskId)
  } catch (error) {
    console.error('Failed to start task:', error)
  }
}

const pauseTask = async (taskId: string) => {
  try {
    await taskStore.pauseTask(taskId)
    await timeTracking.pauseTimer(taskId)
  } catch (error) {
    console.error('Failed to pause task:', error)
  }
}

const openScanner = async (taskId: string) => {
  try {
    const result = await barcodeScanner.scan()
    if (result) {
      router.push(`/mobile/technician/tasks/${taskId}/scan/${result.code}`)
    }
  } catch (error) {
    console.error('Barcode scanning failed:', error)
  }
}

const takePhoto = async (taskId: string) => {
  try {
    const photo = await mobileCamera.takePhoto()
    if (photo) {
      await taskStore.attachPhoto(taskId, photo)
    }
  } catch (error) {
    console.error('Photo capture failed:', error)
  }
}

const openQuickScanner = async () => {
  try {
    const result = await barcodeScanner.scan()
    if (result) {
      router.push(`/mobile/technician/scan/${result.code}`)
    }
  } catch (error) {
    console.error('Quick scan failed:', error)
  }
}

const navigateTo = (navItemId: string) => {
  activeNavItem.value = navItemId
  router.push(`/mobile/technician/${navItemId}`)
}

// Lifecycle hooks
onMounted(async () => {
  if (props.realTimeEnabled) {
    await realTimeUpdates.initialize()
    realTimeUpdates.subscribeToTechnicianUpdates(technician.value?.id)
  }
  
  if (props.offlineCapable) {
    await offlineSync.initialize()
  }
  
  await loadTechnicianData()
})

onUnmounted(() => {
  realTimeUpdates.cleanup()
  timeTracking.cleanup()
})

const loadTechnicianData = async () => {
  try {
    if (props.technicianId) {
      await technicianStore.loadTechnician(props.technicianId)
    }
    await taskStore.loadActiveTasks()
  } catch (error) {
    console.error('Failed to load technician data:', error)
  }
}
</script>

<style scoped>
.technician-mobile-interface {
  @apply min-h-screen bg-gray-50 pb-20;
  font-family: 'Noto Sans Arabic', 'Roboto', sans-serif;
}

.technician-mobile-interface.rtl {
  direction: rtl;
}

/* Mobile Header */
.mobile-header {
  @apply bg-white shadow-sm p-4;
}

.technician-info {
  @apply flex items-center justify-between mb-4;
}

.avatar-section {
  @apply relative;
}

.technician-avatar {
  @apply w-16 h-16 rounded-full object-cover border-2 border-white shadow-sm;
}

.status-indicator {
  @apply absolute -bottom-1 -right-1 w-6 h-6 rounded-full flex items-center justify-center text-white text-xs;
}

.status-indicator.available {
  @apply bg-green-500;
}

.status-indicator.busy {
  @apply bg-red-500;
}

.tech-details {
  @apply flex-1 ml-4;
}

.tech-details.rtl {
  @apply mr-4 ml-0;
}

.tech-details h2 {
  @apply text-lg font-bold text-gray-900;
}

.tech-role {
  @apply text-sm text-gray-600;
}

.tech-stats {
  @apply text-xs text-gray-500;
}

.stats-bar {
  @apply flex justify-between bg-gray-50 rounded-lg p-3;
}

.stat-item {
  @apply flex items-center space-x-2 text-sm;
}

.stat-item.rtl {
  @apply space-x-reverse;
}

/* Tasks Section */
.tasks-section {
  @apply p-4;
}

.section-header {
  @apply flex justify-between items-center mb-4;
}

.section-header h3 {
  @apply text-lg font-bold text-gray-900;
}

.task-filters {
  @apply flex space-x-2;
}

.task-filters.rtl {
  @apply space-x-reverse;
}

.tasks-list {
  @apply space-y-4;
}

/* Task Card */
.task-card {
  @apply bg-white rounded-xl shadow-sm border border-gray-200 p-4;
}

.task-card.priority-urgent {
  @apply border-red-300 bg-red-50;
}

.task-card.priority-high {
  @apply border-orange-300 bg-orange-50;
}

.task-header {
  @apply flex items-center justify-between mb-3;
}

.task-priority {
  @apply w-8 h-8 rounded-full flex items-center justify-center;
}

.task-priority.urgent {
  @apply bg-red-100 text-red-600;
}

.task-priority.high {
  @apply bg-orange-100 text-orange-600;
}

.task-priority.medium {
  @apply bg-yellow-100 text-yellow-600;
}

.task-priority.low {
  @apply bg-green-100 text-green-600;
}

.task-info {
  @apply flex-1 ml-3;
}

.task-info.rtl {
  @apply mr-3 ml-0;
}

.task-info h4 {
  @apply font-bold text-gray-900;
}

.customer-name {
  @apply text-sm text-gray-600;
}

.task-status {
  @apply px-2 py-1 rounded-full text-xs font-medium;
}

.task-status.assigned {
  @apply bg-blue-100 text-blue-800;
}

.task-status.in_progress {
  @apply bg-yellow-100 text-yellow-800;
}

.task-status.completed {
  @apply bg-green-100 text-green-800;
}

/* Vehicle Info */
.vehicle-info {
  @apply flex items-center space-x-3 mb-3;
}

.vehicle-info.rtl {
  @apply space-x-reverse;
}

.vehicle-info img {
  @apply w-12 h-12 rounded-lg object-cover;
}

.vehicle-details {
  @apply flex flex-col;
}

.vehicle-model {
  @apply font-medium text-gray-900;
}

.plate-number {
  @apply text-sm text-gray-600;
}

/* Task Progress */
.task-progress {
  @apply flex items-center space-x-3 mb-3;
}

.task-progress.rtl {
  @apply space-x-reverse;
}

.progress-bar {
  @apply flex-1 bg-gray-200 rounded-full h-2;
}

.progress-fill {
  @apply h-full bg-blue-500 rounded-full transition-all duration-300;
}

.progress-text {
  @apply text-sm font-medium text-gray-700;
}

/* Task Actions */
.task-actions {
  @apply flex space-x-2 mb-3;
}

.task-actions.rtl {
  @apply space-x-reverse;
}

/* Time Tracking */
.time-tracking {
  @apply flex items-center space-x-2 text-sm text-gray-600 bg-gray-50 rounded-lg p-2;
}

.time-tracking.rtl {
  @apply space-x-reverse;
}

.elapsed-time {
  @apply font-mono font-bold;
}

.estimated-time {
  @apply text-gray-500;
}

/* Bottom Navigation */
.bottom-nav {
  @apply fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 flex;
}

.nav-item {
  @apply flex-1 flex flex-col items-center py-2 space-y-1;
}

.nav-item span {
  @apply text-xs;
}

/* Floating Action Button */
.fab-container {
  @apply fixed bottom-20 right-6 z-50;
}

.fab-container.rtl {
  @apply left-6 right-auto;
}

.scan-fab {
  @apply w-14 h-14 rounded-full shadow-lg;
}

/* Sync Indicator */
.sync-indicator {
  @apply fixed top-4 right-4 bg-blue-500 text-white px-3 py-1 rounded-full text-sm flex items-center space-x-2;
}

.sync-indicator.rtl {
  @apply left-4 right-auto space-x-reverse;
}

/* Transitions */
.task-enter-active,
.task-leave-active {
  @apply transition-all duration-300;
}

.task-enter-from,
.task-leave-to {
  @apply opacity-0 transform translate-y-4;
}
</style> 