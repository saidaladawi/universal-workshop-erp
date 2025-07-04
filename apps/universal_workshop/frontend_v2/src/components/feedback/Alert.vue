<!--
  Alert Component - Universal Workshop Frontend V2
  
  A static alert component for displaying important messages with different
  variants and states, including Arabic/RTL support.
-->

<template>
  <div
    v-if="visible"
    :class="alertClasses"
    role="alert"
    :aria-live="variant === 'error' ? 'assertive' : 'polite'"
  >
    <!-- Icon -->
    <div v-if="showIcon || iconName" class="uw-alert-icon">
      <component
        :is="iconComponent"
        v-if="iconComponent"
        class="uw-alert-icon-svg"
      />
      <span v-else-if="iconName" v-html="iconName" />
      <svg v-else class="uw-alert-icon-svg" viewBox="0 0 24 24" fill="currentColor">
        <path :d="defaultIconPath" />
      </svg>
    </div>
    
    <!-- Content -->
    <div class="uw-alert-content">
      <!-- Title -->
      <div v-if="title || titleAr" class="uw-alert-title">
        <span v-if="preferArabic && titleAr">{{ titleAr }}</span>
        <span v-else-if="title">{{ title }}</span>
        <span v-else-if="titleAr">{{ titleAr }}</span>
      </div>
      
      <!-- Message -->
      <div class="uw-alert-message">
        <slot>
          <span v-if="preferArabic && messageAr">{{ messageAr }}</span>
          <span v-else-if="message">{{ message }}</span>
          <span v-else-if="messageAr">{{ messageAr }}</span>
        </slot>
      </div>
      
      <!-- Actions -->
      <div v-if="$slots.actions || actions?.length" class="uw-alert-actions">
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
      class="uw-alert-close"
      :aria-label="closeLabel"
      @click="handleClose"
    >
      <svg class="uw-alert-close-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <path d="M18 6L6 18M6 6l12 12" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed, inject, ref, watch } from 'vue'

// Define action interface
export interface AlertAction {
  key: string
  label: string
  labelAr?: string
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost'
  handler?: () => void
}

// Define component props
export interface AlertProps {
  /** Alert variant/type */
  variant?: 'info' | 'success' | 'warning' | 'error'
  /** Alert title */
  title?: string
  /** Arabic alert title */
  titleAr?: string
  /** Alert message */
  message?: string
  /** Arabic alert message */
  messageAr?: string
  /** Show icon */
  showIcon?: boolean
  /** Custom icon name/HTML */
  iconName?: string
  /** Custom icon component */
  iconComponent?: any
  /** Alert is closable */
  closable?: boolean
  /** Alert visible state */
  visible?: boolean
  /** Alert actions */
  actions?: AlertAction[]
  /** Prefer Arabic display */
  preferArabic?: boolean
  /** Custom CSS class */
  class?: string
}

// Define component emits
export interface AlertEmits {
  'update:visible': [value: boolean]
  close: []
  'action-click': [action: AlertAction]
}

// Setup props with defaults
const props = withDefaults(defineProps<AlertProps>(), {
  variant: 'info',
  showIcon: true,
  closable: false,
  visible: true,
  preferArabic: true,
})

// Setup emits
const emit = defineEmits<AlertEmits>()

// Check if RTL context is available
const isRTL = inject('isRTL', true)

// Internal visible state
const internalVisible = ref(props.visible)

// Watch for external visible changes
watch(() => props.visible, (newValue) => {
  internalVisible.value = newValue
})

// Watch for internal visible changes
watch(internalVisible, (newValue) => {
  emit('update:visible', newValue)
})

// Close label for accessibility
const closeLabel = computed(() => {
  return props.preferArabic ? 'إغلاق التنبيه' : 'Close alert'
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

// Computed classes
const alertClasses = computed(() => [
  'uw-alert',
  `uw-alert--${props.variant}`,
  {
    'uw-alert--closable': props.closable,
    'uw-alert--with-actions': !!(props.actions?.length || props.$slots?.actions),
    'uw-alert--rtl': isRTL,
    'uw-alert--prefer-arabic': props.preferArabic,
  },
  props.class,
])

// Get action button classes
const getActionClasses = (action: AlertAction) => [
  'uw-alert-action',
  `uw-alert-action--${action.variant || 'outline'}`,
]

// Event handlers
const handleClose = () => {
  internalVisible.value = false
  emit('close')
}

const handleActionClick = (action: AlertAction) => {
  emit('action-click', action)
  if (action.handler) {
    action.handler()
  }
}

// Expose internal visible state
defineExpose({
  visible: internalVisible,
  close: handleClose,
})
</script>

<style lang="scss" scoped>
.uw-alert {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-3);
  padding: var(--spacing-4);
  border-radius: var(--radius-md);
  border: 1px solid transparent;
  position: relative;
  
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
    .uw-alert-content {
      padding-bottom: var(--spacing-2);
    }
  }
}

// Variant styles
.uw-alert--info {
  background-color: var(--color-info-50);
  border-color: var(--color-info-200);
  color: var(--color-info-800);
  
  .uw-alert-icon {
    color: var(--color-info);
  }
}

.uw-alert--success {
  background-color: var(--color-success-50);
  border-color: var(--color-success-200);
  color: var(--color-success-800);
  
  .uw-alert-icon {
    color: var(--color-success);
  }
}

.uw-alert--warning {
  background-color: var(--color-warning-50);
  border-color: var(--color-warning-200);
  color: var(--color-warning-800);
  
  .uw-alert-icon {
    color: var(--color-warning);
  }
}

.uw-alert--error {
  background-color: var(--color-error-50);
  border-color: var(--color-error-200);
  color: var(--color-error-800);
  
  .uw-alert-icon {
    color: var(--color-error);
  }
}

// Icon styles
.uw-alert-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1.25rem;
  height: 1.25rem;
  margin-top: 0.125rem;
}

.uw-alert-icon-svg {
  width: 100%;
  height: 100%;
  fill: currentColor;
}

// Content styles
.uw-alert-content {
  flex: 1;
  min-width: 0;
}

.uw-alert-title {
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-base);
  line-height: var(--line-height-tight);
  margin-bottom: var(--spacing-1);
}

.uw-alert-message {
  font-size: var(--font-size-sm);
  line-height: var(--line-height-relaxed);
}

// Actions styles
.uw-alert-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  margin-top: var(--spacing-3);
  flex-wrap: wrap;
}

.uw-alert-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-2) var(--spacing-3);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
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
.uw-alert-close {
  position: absolute;
  top: var(--spacing-4);
  right: var(--spacing-4);
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--spacing-6);
  height: var(--spacing-6);
  border: none;
  background: transparent;
  color: currentColor;
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: var(--transition-colors);
  
  &:hover {
    background-color: rgba(0, 0, 0, 0.1);
  }
  
  &:focus {
    outline: 2px solid var(--color-primary);
    outline-offset: 2px;
  }
  
  .uw-alert--rtl & {
    right: auto;
    left: var(--spacing-4);
  }
}

.uw-alert-close-icon {
  width: var(--spacing-4);
  height: var(--spacing-4);
}

// Dark mode support
[data-theme="dark"] {
  .uw-alert--info {
    background-color: var(--color-info-950);
    border-color: var(--color-info-800);
    color: var(--color-info-200);
  }
  
  .uw-alert--success {
    background-color: var(--color-success-950);
    border-color: var(--color-success-800);
    color: var(--color-success-200);
  }
  
  .uw-alert--warning {
    background-color: var(--color-warning-950);
    border-color: var(--color-warning-800);
    color: var(--color-warning-200);
  }
  
  .uw-alert--error {
    background-color: var(--color-error-950);
    border-color: var(--color-error-800);
    color: var(--color-error-200);
  }
}

// Reduced motion
@media (prefers-reduced-motion: reduce) {
  .uw-alert-action,
  .uw-alert-close {
    transition: none;
  }
}
</style>