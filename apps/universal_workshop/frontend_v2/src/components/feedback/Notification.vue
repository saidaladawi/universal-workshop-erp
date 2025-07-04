<!--
  Notification Component - Universal Workshop Frontend V2
  
  A persistent notification component for user alerts, messages, and system
  updates with read/unread states and Arabic/RTL support.
-->

<template>
  <div
    v-if="visible"
    :class="notificationClasses"
    :style="notificationStyles"
    role="article"
    :aria-labelledby="titleId"
    :aria-describedby="bodyId"
    :aria-live="variant === 'error' ? 'assertive' : 'polite'"
    @click="handleClick"
  >
    <!-- Avatar/Icon -->
    <div class="uw-notification-avatar">
      <!-- Custom avatar -->
      <img
        v-if="avatar"
        :src="avatar"
        :alt="avatarAlt || (preferArabic ? 'صورة المرسل' : 'Sender avatar')"
        class="uw-notification-avatar-img"
      />
      
      <!-- Icon -->
      <div v-else-if="showIcon || iconName" class="uw-notification-icon">
        <component
          :is="iconComponent"
          v-if="iconComponent"
          class="uw-notification-icon-svg"
        />
        <span v-else-if="iconName" v-html="iconName" />
        <svg v-else class="uw-notification-icon-svg" viewBox="0 0 24 24" fill="currentColor">
          <path :d="defaultIconPath" />
        </svg>
      </div>
      
      <!-- Unread indicator -->
      <div
        v-if="!isRead && showUnreadIndicator"
        class="uw-notification-unread-dot"
        :aria-label="preferArabic ? 'غير مقروء' : 'Unread'"
      />
    </div>
    
    <!-- Content -->
    <div class="uw-notification-content">
      <!-- Header -->
      <div class="uw-notification-header">
        <!-- Title -->
        <h3 v-if="title || titleAr" :id="titleId" class="uw-notification-title">
          <span v-if="preferArabic && titleAr">{{ titleAr }}</span>
          <span v-else-if="title">{{ title }}</span>
          <span v-else-if="titleAr">{{ titleAr }}</span>
        </h3>
        
        <!-- Metadata -->
        <div class="uw-notification-meta">
          <!-- Sender -->
          <span v-if="sender || senderAr" class="uw-notification-sender">
            <span v-if="preferArabic && senderAr">{{ senderAr }}</span>
            <span v-else-if="sender">{{ sender }}</span>
            <span v-else-if="senderAr">{{ senderAr }}</span>
          </span>
          
          <!-- Timestamp -->
          <time
            v-if="timestamp"
            :datetime="timestamp.toISOString()"
            class="uw-notification-time"
          >
            {{ formatTimestamp(timestamp) }}
          </time>
        </div>
      </div>
      
      <!-- Body -->
      <div :id="bodyId" class="uw-notification-body">
        <slot>
          <p v-if="message || messageAr">
            <span v-if="preferArabic && messageAr">{{ messageAr }}</span>
            <span v-else-if="message">{{ message }}</span>
            <span v-else-if="messageAr">{{ messageAr }}</span>
          </p>
        </slot>
      </div>
      
      <!-- Actions -->
      <div v-if="$slots.actions || actions?.length" class="uw-notification-actions">
        <slot name="actions">
          <button
            v-for="action in actions"
            :key="action.key"
            type="button"
            :class="getActionClasses(action)"
            :disabled="action.disabled"
            @click.stop="handleActionClick(action)"
          >
            {{ preferArabic && action.labelAr ? action.labelAr : action.label }}
          </button>
        </slot>
      </div>
    </div>
    
    <!-- Close/More actions -->
    <div class="uw-notification-controls">
      <!-- Mark as read/unread -->
      <button
        v-if="showReadToggle"
        type="button"
        class="uw-notification-read-toggle"
        :aria-label="readToggleLabel"
        :title="readToggleLabel"
        @click.stop="handleReadToggle"
      >
        <svg class="uw-notification-read-icon" viewBox="0 0 24 24" fill="currentColor">
          <path v-if="isRead" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
          <path v-else d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"/>
        </svg>
      </button>
      
      <!-- Close button -->
      <button
        v-if="closable"
        type="button"
        class="uw-notification-close"
        :aria-label="closeLabel"
        @click.stop="handleClose"
      >
        <svg class="uw-notification-close-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path d="M18 6L6 18M6 6l12 12" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, inject, ref, watch } from 'vue'

// Define action interface
export interface NotificationAction {
  key: string
  label: string
  labelAr?: string
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost'
  disabled?: boolean
  handler?: () => void
}

// Define component props
export interface NotificationProps {
  /** Notification variant/type */
  variant?: 'info' | 'success' | 'warning' | 'error' | 'system'
  /** Notification title */
  title?: string
  /** Arabic notification title */
  titleAr?: string
  /** Notification message */
  message?: string
  /** Arabic notification message */
  messageAr?: string
  /** Sender name */
  sender?: string
  /** Arabic sender name */
  senderAr?: string
  /** Avatar image URL */
  avatar?: string
  /** Avatar alt text */
  avatarAlt?: string
  /** Timestamp */
  timestamp?: Date
  /** Show icon */
  showIcon?: boolean
  /** Custom icon name/HTML */
  iconName?: string
  /** Custom icon component */
  iconComponent?: any
  /** Notification is closable */
  closable?: boolean
  /** Notification visible state */
  visible?: boolean
  /** Read state */
  isRead?: boolean
  /** Show read/unread toggle */
  showReadToggle?: boolean
  /** Show unread indicator dot */
  showUnreadIndicator?: boolean
  /** Notification is clickable */
  clickable?: boolean
  /** Notification actions */
  actions?: NotificationAction[]
  /** Prefer Arabic display */
  preferArabic?: boolean
  /** Custom CSS class */
  class?: string
}

// Define component emits
export interface NotificationEmits {
  'update:visible': [value: boolean]
  'update:isRead': [value: boolean]
  click: [event: MouseEvent]
  close: []
  'read-toggle': [isRead: boolean]
  'action-click': [action: NotificationAction]
}

// Setup props with defaults
const props = withDefaults(defineProps<NotificationProps>(), {
  variant: 'info',
  showIcon: true,
  closable: true,
  visible: true,
  isRead: false,
  showReadToggle: true,
  showUnreadIndicator: true,
  clickable: false,
  preferArabic: true,
})

// Setup emits
const emit = defineEmits<NotificationEmits>()

// Check if RTL context is available
const isRTL = inject('isRTL', true)

// Internal state
const internalVisible = ref(props.visible)
const internalIsRead = ref(props.isRead)

// Watch for external changes
watch(() => props.visible, (newValue) => {
  internalVisible.value = newValue
})

watch(() => props.isRead, (newValue) => {
  internalIsRead.value = newValue
})

// Watch for internal changes
watch(internalVisible, (newValue) => {
  emit('update:visible', newValue)
})

watch(internalIsRead, (newValue) => {
  emit('update:isRead', newValue)
})

// Unique IDs for accessibility
const titleId = computed(() => `notification-title-${Math.random().toString(36).substr(2, 9)}`)
const bodyId = computed(() => `notification-body-${Math.random().toString(36).substr(2, 9)}`)

// Labels for accessibility
const closeLabel = computed(() => {
  return props.preferArabic ? 'إغلاق الإشعار' : 'Close notification'
})

const readToggleLabel = computed(() => {
  if (props.preferArabic) {
    return internalIsRead.value ? 'تمييز كغير مقروء' : 'تمييز كمقروء'
  }
  return internalIsRead.value ? 'Mark as unread' : 'Mark as read'
})

// Default icon paths for each variant
const iconPaths = {
  info: "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z",
  success: "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z",
  warning: "M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z",
  error: "M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z",
  system: "M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
}

// Default icon path based on variant
const defaultIconPath = computed(() => iconPaths[props.variant])

// Format timestamp for display
const formatTimestamp = (date: Date): string => {
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)
  
  if (props.preferArabic) {
    if (minutes < 1) return 'الآن'
    if (minutes < 60) return `منذ ${minutes} دقيقة`
    if (hours < 24) return `منذ ${hours} ساعة`
    if (days < 7) return `منذ ${days} يوم`
    return date.toLocaleDateString('ar-SA')
  }
  
  if (minutes < 1) return 'now'
  if (minutes < 60) return `${minutes}m ago`
  if (hours < 24) return `${hours}h ago`
  if (days < 7) return `${days}d ago`
  return date.toLocaleDateString()
}

// Computed classes
const notificationClasses = computed(() => [
  'uw-notification',
  `uw-notification--${props.variant}`,
  {
    'uw-notification--unread': !internalIsRead.value,
    'uw-notification--clickable': props.clickable,
    'uw-notification--with-avatar': !!props.avatar,
    'uw-notification--with-actions': !!(props.actions?.length || props.$slots?.actions),
    'uw-notification--rtl': isRTL,
    'uw-notification--prefer-arabic': props.preferArabic,
  },
  props.class,
])

// Computed styles
const notificationStyles = computed(() => {
  const styles: Record<string, string> = {}
  return styles
})

// Get action button classes
const getActionClasses = (action: NotificationAction) => [
  'uw-notification-action',
  `uw-notification-action--${action.variant || 'outline'}`,
  {
    'uw-notification-action--disabled': action.disabled,
  },
]

// Event handlers
const handleClick = (event: MouseEvent) => {
  if (props.clickable) {
    emit('click', event)
    
    // Auto-mark as read when clicked
    if (!internalIsRead.value) {
      internalIsRead.value = true
      emit('read-toggle', true)
    }
  }
}

const handleClose = () => {
  internalVisible.value = false
  emit('close')
}

const handleReadToggle = () => {
  internalIsRead.value = !internalIsRead.value
  emit('read-toggle', internalIsRead.value)
}

const handleActionClick = (action: NotificationAction) => {
  if (action.disabled) return
  
  emit('action-click', action)
  if (action.handler) {
    action.handler()
  }
}

// Expose methods
defineExpose({
  visible: internalVisible,
  isRead: internalIsRead,
  close: handleClose,
  markAsRead: () => {
    internalIsRead.value = true
    emit('read-toggle', true)
  },
  markAsUnread: () => {
    internalIsRead.value = false
    emit('read-toggle', false)
  },
})
</script>

<style lang="scss" scoped>
.uw-notification {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-3);
  padding: var(--spacing-4);
  background: var(--color-surface-primary);
  border: 1px solid var(--color-border-primary);
  border-radius: var(--radius-lg);
  position: relative;
  transition: var(--transition-colors);
  
  // RTL support
  &--rtl {
    direction: rtl;
    text-align: right;
  }
  
  // Arabic font preference
  &--prefer-arabic {
    font-family: var(--font-family-arabic);
  }
  
  // Unread state
  &--unread {
    background: var(--color-surface-secondary);
    border-left: 4px solid var(--color-primary);
    
    &.uw-notification--rtl {
      border-left: none;
      border-right: 4px solid var(--color-primary);
    }
  }
  
  // Clickable state
  &--clickable {
    cursor: pointer;
    
    &:hover {
      background: var(--color-surface-secondary);
    }
  }
  
  // With avatar adjustments
  &--with-avatar {
    .uw-notification-avatar {
      width: 40px;
      height: 40px;
    }
  }
  
  // With actions spacing
  &--with-actions {
    .uw-notification-content {
      padding-bottom: var(--spacing-2);
    }
  }
}

// Variant border colors for unread state
.uw-notification--info.uw-notification--unread {
  border-left-color: var(--color-info);
  
  &.uw-notification--rtl {
    border-right-color: var(--color-info);
  }
}

.uw-notification--success.uw-notification--unread {
  border-left-color: var(--color-success);
  
  &.uw-notification--rtl {
    border-right-color: var(--color-success);
  }
}

.uw-notification--warning.uw-notification--unread {
  border-left-color: var(--color-warning);
  
  &.uw-notification--rtl {
    border-right-color: var(--color-warning);
  }
}

.uw-notification--error.uw-notification--unread {
  border-left-color: var(--color-error);
  
  &.uw-notification--rtl {
    border-right-color: var(--color-error);
  }
}

.uw-notification--system.uw-notification--unread {
  border-left-color: var(--color-secondary);
  
  &.uw-notification--rtl {
    border-right-color: var(--color-secondary);
  }
}

// Avatar styles
.uw-notification-avatar {
  position: relative;
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-full);
  overflow: hidden;
  background: var(--color-surface-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.uw-notification-avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.uw-notification-icon {
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  
  // Variant colors
  .uw-notification--info & { color: var(--color-info); }
  .uw-notification--success & { color: var(--color-success); }
  .uw-notification--warning & { color: var(--color-warning); }
  .uw-notification--error & { color: var(--color-error); }
  .uw-notification--system & { color: var(--color-secondary); }
}

.uw-notification-icon-svg {
  width: 100%;
  height: 100%;
  fill: currentColor;
}

.uw-notification-unread-dot {
  position: absolute;
  top: -2px;
  right: -2px;
  width: 8px;
  height: 8px;
  background: var(--color-primary);
  border: 2px solid var(--color-surface-primary);
  border-radius: var(--radius-full);
  
  .uw-notification--rtl & {
    right: auto;
    left: -2px;
  }
}

// Content styles
.uw-notification-content {
  flex: 1;
  min-width: 0;
}

.uw-notification-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-2);
  margin-bottom: var(--spacing-1);
  
  .uw-notification--rtl & {
    flex-direction: row-reverse;
  }
}

.uw-notification-title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0;
  line-height: var(--line-height-tight);
  flex: 1;
}

.uw-notification-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: var(--spacing-1);
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  flex-shrink: 0;
  
  .uw-notification--rtl & {
    align-items: flex-start;
  }
}

.uw-notification-sender {
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
}

.uw-notification-time {
  white-space: nowrap;
}

.uw-notification-body {
  font-size: var(--font-size-sm);
  line-height: var(--line-height-relaxed);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-2);
  
  p {
    margin: 0;
  }
}

// Actions styles
.uw-notification-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  margin-top: var(--spacing-3);
  flex-wrap: wrap;
}

.uw-notification-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-1) var(--spacing-3);
  border-radius: var(--radius-md);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  border: 1px solid transparent;
  cursor: pointer;
  transition: var(--transition-colors);
  text-decoration: none;
  
  &:focus {
    outline: 2px solid var(--color-primary);
    outline-offset: 2px;
  }
  
  &--disabled {
    opacity: 0.5;
    cursor: not-allowed;
    pointer-events: none;
  }
  
  // Action variants
  &--primary {
    background-color: var(--color-primary);
    color: var(--color-primary-foreground);
    
    &:hover:not(.uw-notification-action--disabled) {
      background-color: var(--color-primary-600);
    }
  }
  
  &--secondary {
    background-color: var(--color-secondary);
    color: var(--color-secondary-foreground);
    
    &:hover:not(.uw-notification-action--disabled) {
      background-color: var(--color-secondary-600);
    }
  }
  
  &--outline {
    border-color: var(--color-border-primary);
    background-color: transparent;
    color: var(--color-text-primary);
    
    &:hover:not(.uw-notification-action--disabled) {
      background-color: var(--color-surface-secondary);
    }
  }
  
  &--ghost {
    background-color: transparent;
    color: var(--color-text-primary);
    
    &:hover:not(.uw-notification-action--disabled) {
      background-color: var(--color-surface-secondary);
    }
  }
}

// Controls styles
.uw-notification-controls {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
  flex-shrink: 0;
}

.uw-notification-read-toggle,
.uw-notification-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--spacing-6);
  height: var(--spacing-6);
  border: none;
  background: transparent;
  color: var(--color-text-tertiary);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: var(--transition-colors);
  
  &:hover {
    background-color: var(--color-surface-secondary);
    color: var(--color-text-secondary);
  }
  
  &:focus {
    outline: 2px solid var(--color-primary);
    outline-offset: 2px;
  }
}

.uw-notification-read-icon,
.uw-notification-close-icon {
  width: var(--spacing-4);
  height: var(--spacing-4);
}

.uw-notification-read-toggle {
  .uw-notification--unread & {
    color: var(--color-primary);
  }
}

// Dark mode support
[data-theme="dark"] {
  .uw-notification {
    background: var(--color-surface-secondary);
    border-color: var(--color-border-secondary);
    
    &--unread {
      background: var(--color-surface-tertiary);
    }
  }
}

// Reduced motion
@media (prefers-reduced-motion: reduce) {
  .uw-notification,
  .uw-notification-action,
  .uw-notification-close,
  .uw-notification-read-toggle {
    transition: none;
  }
}

// High contrast mode
[data-contrast="high"] {
  .uw-notification {
    border-width: 2px;
    
    &--unread {
      border-left-width: 6px;
      
      &.uw-notification--rtl {
        border-right-width: 6px;
      }
    }
  }
}
</style>