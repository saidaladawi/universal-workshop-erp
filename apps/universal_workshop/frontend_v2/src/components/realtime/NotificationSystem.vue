<!--
  Notification System - Universal Workshop Frontend V2
  
  Real-time notification system with Arabic support and sound alerts.
-->

<template>
  <div class="notification-system">
    <!-- Notification container -->
    <div class="notifications-container" :class="{ 'rtl': isRTL }">
      <TransitionGroup name="notification" tag="div">
        <div
          v-for="notification in displayedNotifications"
          :key="notification.id"
          class="notification"
          :class="[
            notification.type,
            { 'critical': notification.type === 'critical' }
          ]"
          @click="handleNotificationClick(notification)"
        >
          <!-- Notification icon -->
          <div class="notification-icon">
            <Icon :name="getNotificationIcon(notification.type)" />
          </div>

          <!-- Notification content -->
          <div class="notification-content">
            <h4 class="notification-title">{{ notification.title }}</h4>
            <p v-if="notification.message" class="notification-message">
              {{ notification.message }}
            </p>
            
            <!-- Action buttons -->
            <div v-if="notification.actions && notification.actions.length > 0" class="notification-actions">
              <Button
                v-for="action in notification.actions"
                :key="action.id"
                :variant="action.variant"
                size="sm"
                @click="handleActionClick(action, notification)"
              >
                {{ preferArabic ? action.labelAr : action.label }}
              </Button>
            </div>
          </div>

          <!-- Timestamp and dismiss -->
          <div class="notification-meta">
            <span class="notification-time">
              {{ formatRelativeTime(notification.timestamp) }}
            </span>
            
            <Button
              variant="ghost"
              size="sm"
              @click="dismissNotification(notification.id)"
            >
              <Icon name="x" />
            </Button>
          </div>

          <!-- Progress bar for auto-dismiss -->
          <div 
            v-if="notification.autoClose !== false && !notification.dismissed"
            class="notification-progress"
          >
            <div 
              class="progress-bar"
              :style="{ 
                animationDuration: `${notification.duration || 5000}ms`,
                animationPlayState: notification.paused ? 'paused' : 'running'
              }"
            ></div>
          </div>
        </div>
      </TransitionGroup>
    </div>

    <!-- Toast notifications (simpler, bottom notifications) -->
    <div class="toast-container" :class="{ 'rtl': isRTL }">
      <TransitionGroup name="toast" tag="div">
        <div
          v-for="toast in toastNotifications"
          :key="toast.id"
          class="toast"
          :class="toast.type"
          @mouseenter="pauseToast(toast.id)"
          @mouseleave="resumeToast(toast.id)"
        >
          <Icon :name="getNotificationIcon(toast.type)" />
          <span class="toast-message">{{ toast.message }}</span>
          
          <Button
            variant="ghost"
            size="xs"
            @click="dismissToast(toast.id)"
          >
            <Icon name="x" />
          </Button>
        </div>
      </TransitionGroup>
    </div>

    <!-- Notification center button -->
    <div class="notification-center-button" @click="toggleNotificationCenter">
      <Button variant="ghost" size="md" class="center-button">
        <Icon name="bell" />
        <span v-if="unreadCount > 0" class="notification-badge">
          {{ unreadCount > 99 ? '99+' : unreadCount }}
        </span>
      </Button>
    </div>

    <!-- Notification center panel -->
    <div v-if="showNotificationCenter" class="notification-center">
      <div class="center-header">
        <h3>{{ preferArabic ? 'مركز الإشعارات' : 'Notification Center' }}</h3>
        <div class="header-actions">
          <Button variant="outline" size="sm" @click="markAllAsRead">
            {{ preferArabic ? 'تعيين الكل كمقروء' : 'Mark All Read' }}
          </Button>
          <Button variant="ghost" size="sm" @click="showNotificationCenter = false">
            <Icon name="x" />
          </Button>
        </div>
      </div>

      <div class="center-filters">
        <Button
          v-for="filter in notificationFilters"
          :key="filter.type"
          :variant="selectedFilter === filter.type ? 'primary' : 'outline'"
          size="sm"
          @click="selectedFilter = filter.type"
        >
          {{ preferArabic ? filter.labelAr : filter.label }}
          <span v-if="filter.count > 0" class="filter-count">{{ filter.count }}</span>
        </Button>
      </div>

      <div class="center-content">
        <div
          v-for="notification in filteredCenterNotifications"
          :key="notification.id"
          class="center-notification"
          :class="{ 'unread': !notification.read }"
          @click="handleCenterNotificationClick(notification)"
        >
          <div class="center-notification-icon">
            <Icon :name="getNotificationIcon(notification.type)" />
          </div>
          
          <div class="center-notification-content">
            <h4>{{ notification.title }}</h4>
            <p>{{ notification.message }}</p>
            <span class="notification-timestamp">
              {{ formatFullTime(notification.timestamp) }}
            </span>
          </div>

          <div class="center-notification-actions">
            <Button
              v-if="!notification.read"
              variant="ghost"
              size="sm"
              @click.stop="markAsRead(notification.id)"
            >
              <Icon name="check" />
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              @click.stop="removeNotification(notification.id)"
            >
              <Icon name="trash" />
            </Button>
          </div>
        </div>

        <div v-if="filteredCenterNotifications.length === 0" class="center-empty">
          <Icon name="bell-off" size="xl" />
          <p>{{ preferArabic ? 'لا توجد إشعارات' : 'No notifications' }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useEventBus } from '@/composables/useEventBus'
import { Button, Icon } from '@/components/base'

// Props
defineProps<{
  preferArabic?: boolean
  isRTL?: boolean
  maxDisplayed?: number
  defaultDuration?: number
}>()

// Composables
const eventBus = useEventBus()

// State
const showNotificationCenter = ref(false)
const selectedFilter = ref('all')
const toastTimers = ref<Map<string, NodeJS.Timeout>>(new Map())
const pausedToasts = ref<Set<string>>(new Set())

// Computed
const displayedNotifications = computed(() => {
  return eventBus.notifications.value
    .filter(n => !n.dismissed && !n.isToast && n.type !== 'info')
    .slice(0, 5) // Show max 5 priority notifications
})

const toastNotifications = computed(() => {
  return eventBus.notifications.value
    .filter(n => !n.dismissed && (n.isToast || n.type === 'info'))
})

const unreadCount = computed(() => {
  return eventBus.notifications.value.filter(n => !n.read && !n.dismissed).length
})

const notificationFilters = computed(() => [
  {
    type: 'all',
    label: 'All',
    labelAr: 'الكل',
    count: eventBus.notifications.value.length
  },
  {
    type: 'unread',
    label: 'Unread',
    labelAr: 'غير مقروء',
    count: eventBus.notifications.value.filter(n => !n.read).length
  },
  {
    type: 'critical',
    label: 'Critical',
    labelAr: 'هام',
    count: eventBus.notifications.value.filter(n => n.type === 'critical').length
  },
  {
    type: 'high',
    label: 'High Priority',
    labelAr: 'أولوية عالية',
    count: eventBus.notifications.value.filter(n => n.type === 'high').length
  }
])

const filteredCenterNotifications = computed(() => {
  let notifications = eventBus.notifications.value

  switch (selectedFilter.value) {
    case 'unread':
      notifications = notifications.filter(n => !n.read)
      break
    case 'critical':
      notifications = notifications.filter(n => n.type === 'critical')
      break
    case 'high':
      notifications = notifications.filter(n => n.type === 'high')
      break
  }

  return notifications.slice(0, 50) // Limit to 50 for performance
})

// Methods
const getNotificationIcon = (type: string): string => {
  const iconMap: Record<string, string> = {
    'info': 'info',
    'success': 'check-circle',
    'warning': 'alert-triangle',
    'danger': 'alert-circle',
    'error': 'x-circle',
    'critical': 'alert-octagon',
    'high': 'alert-triangle',
    'medium': 'info',
    'low': 'bell'
  }

  return iconMap[type] || 'bell'
}

const formatRelativeTime = (timestamp: number): string => {
  const now = Date.now()
  const diff = now - timestamp
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  
  const preferArabic = true // Get from props
  
  if (preferArabic) {
    if (days > 0) return `منذ ${days} يوم${days > 1 ? '' : ''}`
    if (hours > 0) return `منذ ${hours} ساعة${hours > 1 ? '' : ''}`
    if (minutes > 0) return `منذ ${minutes} دقيقة${minutes > 1 ? '' : ''}`
    return 'الآن'
  } else {
    if (days > 0) return `${days}d ago`
    if (hours > 0) return `${hours}h ago`
    if (minutes > 0) return `${minutes}m ago`
    return 'now'
  }
}

const formatFullTime = (timestamp: number): string => {
  const preferArabic = true
  const locale = preferArabic ? 'ar-SA' : 'en-US'
  return new Date(timestamp).toLocaleString(locale)
}

const handleNotificationClick = (notification: any) => {
  markAsRead(notification.id)
  
  // Handle navigation if specified
  if (notification.route) {
    // Navigate to route
    console.log('Navigate to:', notification.route)
  }
}

const handleActionClick = (action: any, notification: any) => {
  // Execute action
  console.log('Action clicked:', action.action, notification)
  
  // Mark as read and dismiss
  markAsRead(notification.id)
  dismissNotification(notification.id)
}

const dismissNotification = (id: string) => {
  eventBus.removeNotification(id)
}

const dismissToast = (id: string) => {
  const timer = toastTimers.value.get(id)
  if (timer) {
    clearTimeout(timer)
    toastTimers.value.delete(id)
  }
  
  dismissNotification(id)
}

const pauseToast = (id: string) => {
  pausedToasts.value.add(id)
  
  const timer = toastTimers.value.get(id)
  if (timer) {
    clearTimeout(timer)
  }
}

const resumeToast = (id: string) => {
  pausedToasts.value.delete(id)
  
  // Restart timer with remaining time
  const notification = toastNotifications.value.find(n => n.id === id)
  if (notification) {
    scheduleToastDismissal(notification)
  }
}

const scheduleToastDismissal = (notification: any) => {
  if (notification.autoClose === false) return
  
  const duration = notification.duration || 5000
  const timer = setTimeout(() => {
    dismissToast(notification.id)
  }, duration)
  
  toastTimers.value.set(notification.id, timer)
}

const toggleNotificationCenter = () => {
  showNotificationCenter.value = !showNotificationCenter.value
}

const markAsRead = (id: string) => {
  eventBus.markNotificationRead(id)
}

const markAllAsRead = () => {
  eventBus.notifications.value.forEach(n => {
    if (!n.read) {
      eventBus.markNotificationRead(n.id)
    }
  })
}

const removeNotification = (id: string) => {
  eventBus.removeNotification(id)
}

const handleCenterNotificationClick = (notification: any) => {
  markAsRead(notification.id)
  
  if (notification.route) {
    showNotificationCenter.value = false
    // Navigate to route
    console.log('Navigate to:', notification.route)
  }
}

// Lifecycle
onMounted(() => {
  // Set up auto-dismiss timers for existing toast notifications
  toastNotifications.value.forEach(notification => {
    scheduleToastDismissal(notification)
  })

  // Watch for new toast notifications
  eventBus.subscribe('notification', (notification: any) => {
    if (notification.isToast || notification.type === 'info') {
      scheduleToastDismissal(notification)
    }
    
    // Play sound for high priority notifications
    if (['critical', 'high'].includes(notification.type) && notification.playSound !== false) {
      playNotificationSound(notification.type)
    }
  })

  // Request notification permission
  if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission()
  }
})

onUnmounted(() => {
  // Clear all timers
  toastTimers.value.forEach(timer => clearTimeout(timer))
  toastTimers.value.clear()
})

const playNotificationSound = (type: string) => {
  try {
    const soundFile = type === 'critical' ? 'critical-alert.mp3' : 'notification.mp3'
    const audio = new Audio(`/sounds/${soundFile}`)
    audio.volume = 0.6
    audio.play().catch(() => {
      // Ignore audio play errors (autoplay policy)
    })
  } catch {
    // Ignore audio errors
  }
}
</script>

<style lang="scss" scoped>
.notification-system {
  position: relative;
  z-index: 9999;
}

.notifications-container {
  position: fixed;
  top: var(--spacing-4);
  right: var(--spacing-4);
  z-index: 1000;
  max-width: 400px;
  
  &.rtl {
    right: auto;
    left: var(--spacing-4);
  }
}

.notification {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-3);
  padding: var(--spacing-4);
  margin-bottom: var(--spacing-3);
  background: var(--color-surface-primary);
  border: 1px solid var(--color-border-primary);
  border-radius: var(--radius-lg);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  cursor: pointer;
  position: relative;
  overflow: hidden;
  
  &.critical {
    border-color: var(--color-danger);
    animation: criticalPulse 1s infinite;
  }
  
  &.high {
    border-color: var(--color-warning);
  }
  
  &.success {
    border-color: var(--color-success);
  }
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
  }
}

.notification-icon {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  
  .notification.info & { color: var(--color-info); background: var(--color-info-50); }
  .notification.success & { color: var(--color-success); background: var(--color-success-50); }
  .notification.warning & { color: var(--color-warning); background: var(--color-warning-50); }
  .notification.danger & { color: var(--color-danger); background: var(--color-danger-50); }
  .notification.critical & { color: var(--color-danger); background: var(--color-danger-50); }
}

.notification-content {
  flex: 1;
  min-width: 0;
  
  .notification-title {
    margin: 0 0 var(--spacing-1) 0;
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-semibold);
    color: var(--color-text-primary);
  }
  
  .notification-message {
    margin: 0 0 var(--spacing-2) 0;
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
    line-height: var(--line-height-relaxed);
  }
}

.notification-actions {
  display: flex;
  gap: var(--spacing-2);
  flex-wrap: wrap;
}

.notification-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: var(--spacing-1);
  
  .notification-time {
    font-size: var(--font-size-xs);
    color: var(--color-text-tertiary);
  }
}

.notification-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: rgba(0, 0, 0, 0.1);
  
  .progress-bar {
    height: 100%;
    background: var(--color-primary);
    animation: progress linear forwards;
  }
}

.toast-container {
  position: fixed;
  bottom: var(--spacing-4);
  right: var(--spacing-4);
  z-index: 1000;
  max-width: 350px;
  
  &.rtl {
    right: auto;
    left: var(--spacing-4);
  }
}

.toast {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-3);
  margin-bottom: var(--spacing-2);
  background: var(--color-surface-primary);
  border: 1px solid var(--color-border-primary);
  border-radius: var(--radius-md);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  font-size: var(--font-size-sm);
  
  &.success { border-color: var(--color-success); }
  &.warning { border-color: var(--color-warning); }
  &.error { border-color: var(--color-danger); }
  
  .toast-message {
    flex: 1;
    color: var(--color-text-primary);
  }
}

.notification-center-button {
  position: fixed;
  top: var(--spacing-4);
  right: var(--spacing-4);
  z-index: 999;
  
  .center-button {
    position: relative;
    
    .notification-badge {
      position: absolute;
      top: -8px;
      right: -8px;
      background: var(--color-danger);
      color: white;
      font-size: var(--font-size-xs);
      font-weight: var(--font-weight-bold);
      padding: 2px 6px;
      border-radius: var(--radius-full);
      min-width: 18px;
      text-align: center;
    }
  }
}

.notification-center {
  position: fixed;
  top: 60px;
  right: var(--spacing-4);
  width: 400px;
  max-height: 600px;
  background: var(--color-surface-primary);
  border: 1px solid var(--color-border-primary);
  border-radius: var(--radius-lg);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  z-index: 1001;
  display: flex;
  flex-direction: column;
  
  .center-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-4);
    border-bottom: 1px solid var(--color-border-primary);
    
    h3 {
      margin: 0;
      font-size: var(--font-size-lg);
      font-weight: var(--font-weight-semibold);
    }
    
    .header-actions {
      display: flex;
      gap: var(--spacing-2);
    }
  }
  
  .center-filters {
    display: flex;
    gap: var(--spacing-2);
    padding: var(--spacing-3);
    border-bottom: 1px solid var(--color-border-primary);
    flex-wrap: wrap;
    
    .filter-count {
      margin-left: var(--spacing-1);
      background: var(--color-gray-200);
      color: var(--color-gray-700);
      font-size: var(--font-size-xs);
      padding: 2px 6px;
      border-radius: var(--radius-full);
    }
  }
  
  .center-content {
    flex: 1;
    overflow-y: auto;
    max-height: 400px;
  }
}

.center-notification {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-3);
  padding: var(--spacing-3);
  border-bottom: 1px solid var(--color-border-primary);
  cursor: pointer;
  
  &.unread {
    background: color-mix(in srgb, var(--color-primary) 5%, var(--color-surface-primary));
  }
  
  &:hover {
    background: var(--color-surface-secondary);
  }
  
  .center-notification-icon {
    flex-shrink: 0;
    width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .center-notification-content {
    flex: 1;
    min-width: 0;
    
    h4 {
      margin: 0 0 var(--spacing-1) 0;
      font-size: var(--font-size-sm);
      font-weight: var(--font-weight-medium);
    }
    
    p {
      margin: 0 0 var(--spacing-1) 0;
      font-size: var(--font-size-sm);
      color: var(--color-text-secondary);
      overflow: hidden;
      text-overflow: ellipsis;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
    }
    
    .notification-timestamp {
      font-size: var(--font-size-xs);
      color: var(--color-text-tertiary);
    }
  }
  
  .center-notification-actions {
    display: flex;
    gap: var(--spacing-1);
    opacity: 0;
    transition: opacity 0.2s ease;
  }
  
  &:hover .center-notification-actions {
    opacity: 1;
  }
}

.center-empty {
  text-align: center;
  padding: var(--spacing-8);
  color: var(--color-text-secondary);
  
  p {
    margin: var(--spacing-2) 0 0 0;
  }
}

// Animations
@keyframes criticalPulse {
  0%, 100% { border-color: var(--color-danger); }
  50% { border-color: var(--color-danger-300); }
}

@keyframes progress {
  from { width: 100%; }
  to { width: 0%; }
}

// Transitions
.notification-enter-active,
.notification-leave-active {
  transition: all 0.3s ease;
}

.notification-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.notification-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.toast-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

// Responsive design
@media (max-width: 768px) {
  .notifications-container,
  .toast-container {
    left: var(--spacing-2);
    right: var(--spacing-2);
    max-width: none;
  }
  
  .notification-center {
    left: var(--spacing-2);
    right: var(--spacing-2);
    width: auto;
  }
  
  .notification-center-button {
    right: var(--spacing-2);
  }
}
</style>