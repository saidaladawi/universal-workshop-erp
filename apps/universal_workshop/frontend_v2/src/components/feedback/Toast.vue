<!--
  Toast Component - Universal Workshop Frontend V2
  
  A temporary notification component that appears and auto-dismisses,
  with support for different positions, variants, and Arabic/RTL layouts.
-->

<template>
  <Teleport to="body">
    <div
      v-if="visible"
      :class="toastClasses"
      :style="toastStyles"
      role="alert"
      :aria-live="variant === 'error' ? 'assertive' : 'polite'"
      @mouseenter="handleMouseEnter"
      @mouseleave="handleMouseLeave"
    >
      <!-- Progress indicator -->
      <div
        v-if="showProgress && duration > 0"
        class="uw-toast-progress"
        :style="progressStyles"
      />
      
      <!-- Icon -->
      <div v-if="showIcon || iconName" class="uw-toast-icon">
        <component
          :is="iconComponent"
          v-if="iconComponent"
          class="uw-toast-icon-svg"
        />
        <span v-else-if="iconName" v-html="iconName" />
        <svg v-else class="uw-toast-icon-svg" viewBox="0 0 24 24" fill="currentColor">
          <path :d="defaultIconPath" />
        </svg>
      </div>
      
      <!-- Content -->
      <div class="uw-toast-content">
        <!-- Title -->
        <div v-if="title || titleAr" class="uw-toast-title">
          <span v-if="preferArabic && titleAr">{{ titleAr }}</span>
          <span v-else-if="title">{{ title }}</span>
          <span v-else-if="titleAr">{{ titleAr }}</span>
        </div>
        
        <!-- Message -->
        <div class="uw-toast-message">
          <slot>
            <span v-if="preferArabic && messageAr">{{ messageAr }}</span>
            <span v-else-if="message">{{ message }}</span>
            <span v-else-if="messageAr">{{ messageAr }}</span>
          </slot>
        </div>
        
        <!-- Actions -->
        <div v-if="$slots.actions || actions?.length" class="uw-toast-actions">
          <slot name="actions">
            <button
              v-for="action in actions"
              :key="action.key"
              type="button"
              :class="getActionClasses(action)"
              @click="handleActionClick(action)"
            >
              {{ preferArabic && action.labelAr ? action.labelAr : action.label }}
            </button>
          </slot>
        </div>
      </div>
      
      <!-- Close button -->
      <button
        v-if="closable"
        type="button"
        class="uw-toast-close"
        :aria-label="closeLabel"
        @click="handleClose"
      >
        <svg class="uw-toast-close-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path d="M18 6L6 18M6 6l12 12" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, inject, ref, watch, onMounted, onUnmounted } from 'vue'

// Define action interface
export interface ToastAction {
  key: string
  label: string
  labelAr?: string
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost'
  handler?: () => void
}

// Define component props
export interface ToastProps {
  /** Toast variant/type */
  variant?: 'info' | 'success' | 'warning' | 'error'
  /** Toast title */
  title?: string
  /** Arabic toast title */
  titleAr?: string
  /** Toast message */
  message?: string
  /** Arabic toast message */
  messageAr?: string
  /** Show icon */
  showIcon?: boolean
  /** Custom icon name/HTML */
  iconName?: string
  /** Custom icon component */
  iconComponent?: any
  /** Toast is closable */
  closable?: boolean
  /** Toast visible state */
  visible?: boolean
  /** Auto-dismiss duration in ms (0 = no auto-dismiss) */
  duration?: number
  /** Show progress indicator */
  showProgress?: boolean
  /** Toast position */
  position?: 'top-right' | 'top-left' | 'top-center' | 'bottom-right' | 'bottom-left' | 'bottom-center'
  /** Z-index */
  zIndex?: number
  /** Toast actions */
  actions?: ToastAction[]
  /** Pause on hover */
  pauseOnHover?: boolean
  /** Prefer Arabic display */
  preferArabic?: boolean
  /** Custom CSS class */
  class?: string
}

// Define component emits
export interface ToastEmits {
  'update:visible': [value: boolean]
  close: []
  'action-click': [action: ToastAction]
  timeout: []
}

// Setup props with defaults
const props = withDefaults(defineProps<ToastProps>(), {
  variant: 'info',
  showIcon: true,
  closable: true,
  visible: true,
  duration: 5000,
  showProgress: true,
  position: 'top-right',
  zIndex: 1000,
  pauseOnHover: true,
  preferArabic: true,
})

// Setup emits
const emit = defineEmits<ToastEmits>()

// Check if RTL context is available
const isRTL = inject('isRTL', true)

// Internal state
const internalVisible = ref(props.visible)
const isPaused = ref(false)
const startTime = ref(0)
const remainingTime = ref(props.duration)
let timeoutId: number | null = null

// Watch for external visible changes
watch(() => props.visible, (newValue) => {
  internalVisible.value = newValue
  if (newValue) {
    startTimer()
  } else {
    clearTimer()
  }
})

// Watch for internal visible changes
watch(internalVisible, (newValue) => {
  emit('update:visible', newValue)
})

// Watch for duration changes
watch(() => props.duration, (newValue) => {
  remainingTime.value = newValue
  if (internalVisible.value && newValue > 0) {
    startTimer()
  }
})

// Start auto-dismiss timer
const startTimer = () => {
  if (props.duration <= 0) return
  
  clearTimer()
  startTime.value = Date.now()
  
  timeoutId = window.setTimeout(() => {
    if (!isPaused.value) {
      handleTimeout()
    }
  }, remainingTime.value)
}

// Clear timer
const clearTimer = () => {
  if (timeoutId) {
    clearTimeout(timeoutId)
    timeoutId = null
  }
}

// Handle timeout
const handleTimeout = () => {
  internalVisible.value = false
  emit('timeout')
  emit('close')
}

// Close label for accessibility
const closeLabel = computed(() => {
  return props.preferArabic ? 'إغلاق الإشعار' : 'Close notification'
})

// Default icon paths for each variant
const iconPaths = {
  info: "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z",
  success: "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z",
  warning: "M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z",
  error: "M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
}

// Default icon path based on variant
const defaultIconPath = computed(() => iconPaths[props.variant])

// Position styles
const positionStyles = computed(() => {
  const styles: Record<string, string> = {}
  
  switch (props.position) {
    case 'top-right':
      styles.top = 'var(--spacing-4)'
      styles.right = 'var(--spacing-4)'
      break
    case 'top-left':
      styles.top = 'var(--spacing-4)'
      styles.left = 'var(--spacing-4)'
      break
    case 'top-center':
      styles.top = 'var(--spacing-4)'
      styles.left = '50%'
      styles.transform = 'translateX(-50%)'
      break
    case 'bottom-right':
      styles.bottom = 'var(--spacing-4)'
      styles.right = 'var(--spacing-4)'
      break
    case 'bottom-left':
      styles.bottom = 'var(--spacing-4)'
      styles.left = 'var(--spacing-4)'
      break
    case 'bottom-center':
      styles.bottom = 'var(--spacing-4)'
      styles.left = '50%'
      styles.transform = 'translateX(-50%)'
      break
  }
  
  return styles
})

// Computed classes
const toastClasses = computed(() => [
  'uw-toast',
  `uw-toast--${props.variant}`,
  `uw-toast--${props.position}`,
  {
    'uw-toast--closable': props.closable,
    'uw-toast--with-actions': !!(props.actions?.length || props.$slots?.actions),
    'uw-toast--with-progress': props.showProgress && props.duration > 0,
    'uw-toast--rtl': isRTL,
    'uw-toast--prefer-arabic': props.preferArabic,
    'uw-toast--paused': isPaused.value,
  },
  props.class,
])

// Computed styles
const toastStyles = computed(() => ({
  ...positionStyles.value,
  zIndex: props.zIndex,
}))

// Progress styles
const progressStyles = computed(() => {
  const elapsed = isPaused.value ? 0 : Date.now() - startTime.value
  const progress = Math.max(0, Math.min(100, (elapsed / props.duration) * 100))
  
  return {
    width: `${100 - progress}%`,
    transition: isPaused.value ? 'none' : `width ${props.duration}ms linear`,
  }
})

// Get action button classes
const getActionClasses = (action: ToastAction) => [
  'uw-toast-action',
  `uw-toast-action--${action.variant || 'outline'}`,
]

// Event handlers
const handleClose = () => {
  clearTimer()
  internalVisible.value = false
  emit('close')
}

const handleActionClick = (action: ToastAction) => {
  emit('action-click', action)
  if (action.handler) {
    action.handler()
  }
}

const handleMouseEnter = () => {
  if (props.pauseOnHover && props.duration > 0) {
    isPaused.value = true
    clearTimer()
    
    // Calculate remaining time
    const elapsed = Date.now() - startTime.value
    remainingTime.value = Math.max(0, props.duration - elapsed)
  }
}

const handleMouseLeave = () => {
  if (props.pauseOnHover && props.duration > 0 && isPaused.value) {
    isPaused.value = false
    startTimer()
  }
}

// Lifecycle
onMounted(() => {
  if (props.visible && props.duration > 0) {
    startTimer()
  }
})

onUnmounted(() => {
  clearTimer()
})

// Expose methods
defineExpose({
  visible: internalVisible,
  close: handleClose,
  pause: () => { isPaused.value = true },
  resume: () => { isPaused.value = false },
})
</script>

<style lang="scss" scoped>
.uw-toast {
  position: fixed;
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-3);
  max-width: 420px;
  min-width: 300px;
  padding: var(--spacing-4);
  background: var(--color-surface-primary);
  border: 1px solid var(--color-border-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  backdrop-filter: blur(8px);
  animation: slideIn 0.3s ease-out;
  transition: all 0.3s ease-out;
  
  // RTL support
  &--rtl {
    direction: rtl;
    text-align: right;
  }
  
  // Arabic font preference
  &--prefer-arabic {
    font-family: var(--font-family-arabic);
  }
  
  // Closable padding adjustment
  &--closable {
    padding-right: var(--spacing-10);
  }
  
  // With actions spacing
  &--with-actions {
    .uw-toast-content {
      padding-bottom: var(--spacing-2);
    }
  }
  
  // With progress bar
  &--with-progress {
    padding-top: calc(var(--spacing-4) + 2px);
  }
  
  // Paused state
  &--paused {
    .uw-toast-progress {
      animation-play-state: paused;
    }
  }
}

// Slide-in animations for different positions
@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.uw-toast--top-right,
.uw-toast--top-left,
.uw-toast--top-center {
  animation: slideInFromTop 0.3s ease-out;
}

.uw-toast--bottom-right,
.uw-toast--bottom-left,
.uw-toast--bottom-center {
  animation: slideInFromBottom 0.3s ease-out;
}

@keyframes slideInFromTop {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideInFromBottom {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

// Variant styles
.uw-toast--info {
  border-color: var(--color-info-200);
  
  .uw-toast-progress {
    background-color: var(--color-info);
  }
  
  .uw-toast-icon {
    color: var(--color-info);
  }
}

.uw-toast--success {
  border-color: var(--color-success-200);
  
  .uw-toast-progress {
    background-color: var(--color-success);
  }
  
  .uw-toast-icon {
    color: var(--color-success);
  }
}

.uw-toast--warning {
  border-color: var(--color-warning-200);
  
  .uw-toast-progress {
    background-color: var(--color-warning);
  }
  
  .uw-toast-icon {
    color: var(--color-warning);
  }
}

.uw-toast--error {
  border-color: var(--color-error-200);
  
  .uw-toast-progress {
    background-color: var(--color-error);
  }
  
  .uw-toast-icon {
    color: var(--color-error);
  }
}

// Progress indicator
.uw-toast-progress {
  position: absolute;
  top: 0;
  left: 0;
  height: 2px;
  background-color: var(--color-primary);
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
  transition: width 0.1s ease-out;
  
  .uw-toast--rtl & {
    left: auto;
    right: 0;
  }
}

// Icon styles
.uw-toast-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1.25rem;
  height: 1.25rem;
  margin-top: 0.125rem;
}

.uw-toast-icon-svg {
  width: 100%;
  height: 100%;
  fill: currentColor;
}

// Content styles
.uw-toast-content {
  flex: 1;
  min-width: 0;
}

.uw-toast-title {
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-sm);
  line-height: var(--line-height-tight);
  margin-bottom: var(--spacing-1);
  color: var(--color-text-primary);
}

.uw-toast-message {
  font-size: var(--font-size-sm);
  line-height: var(--line-height-relaxed);
  color: var(--color-text-secondary);
}

// Actions styles
.uw-toast-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  margin-top: var(--spacing-3);
  flex-wrap: wrap;
}

.uw-toast-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-1) var(--spacing-2);
  border-radius: var(--radius-sm);
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
  
  // Action variants
  &--primary {
    background-color: var(--color-primary);
    color: var(--color-primary-foreground);
    
    &:hover {
      background-color: var(--color-primary-600);
    }
  }
  
  &--secondary {
    background-color: var(--color-secondary);
    color: var(--color-secondary-foreground);
    
    &:hover {
      background-color: var(--color-secondary-600);
    }
  }
  
  &--outline {
    border-color: var(--color-border-primary);
    background-color: transparent;
    
    &:hover {
      background-color: var(--color-surface-secondary);
    }
  }
  
  &--ghost {
    background-color: transparent;
    
    &:hover {
      background-color: var(--color-surface-secondary);
    }
  }
}

// Close button styles
.uw-toast-close {
  position: absolute;
  top: var(--spacing-3);
  right: var(--spacing-3);
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--spacing-6);
  height: var(--spacing-6);
  border: none;
  background: transparent;
  color: var(--color-text-secondary);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: var(--transition-colors);
  
  &:hover {
    background-color: var(--color-surface-secondary);
    color: var(--color-text-primary);
  }
  
  &:focus {
    outline: 2px solid var(--color-primary);
    outline-offset: 2px;
  }
  
  .uw-toast--rtl & {
    right: auto;
    left: var(--spacing-3);
  }
}

.uw-toast-close-icon {
  width: var(--spacing-4);
  height: var(--spacing-4);
}

// Responsive adjustments
@media (max-width: 640px) {
  .uw-toast {
    min-width: 280px;
    max-width: calc(100vw - var(--spacing-8));
  }
  
  .uw-toast--top-center,
  .uw-toast--bottom-center {
    left: var(--spacing-4);
    right: var(--spacing-4);
    transform: none;
    max-width: none;
  }
}

// Dark mode support
[data-theme="dark"] {
  .uw-toast {
    background: var(--color-surface-secondary);
    border-color: var(--color-border-secondary);
  }
}

// Reduced motion
@media (prefers-reduced-motion: reduce) {
  .uw-toast {
    animation: none;
  }
  
  .uw-toast-action,
  .uw-toast-close,
  .uw-toast-progress {
    transition: none;
  }
}

// High contrast mode
[data-contrast="high"] {
  .uw-toast {
    border-width: 2px;
  }
}
</style>