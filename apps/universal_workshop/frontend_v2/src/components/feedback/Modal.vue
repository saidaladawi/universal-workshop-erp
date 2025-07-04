<!--
  Modal Component - Universal Workshop Frontend V2
  
  An overlay dialog component with backdrop, focus management, and keyboard
  navigation support, including Arabic/RTL layouts and accessibility features.
-->

<template>
  <Teleport to="body">
    <Transition
      name="modal"
      @enter="handleEnter"
      @leave="handleLeave"
      @after-enter="handleAfterEnter"
      @after-leave="handleAfterLeave"
    >
      <div
        v-if="visible"
        ref="modalRef"
        :class="modalWrapperClasses"
        :style="modalWrapperStyles"
        role="dialog"
        :aria-modal="true"
        :aria-labelledby="titleId"
        :aria-describedby="bodyId"
        @click="handleBackdropClick"
        @keydown="handleKeydown"
      >
        <!-- Modal container -->
        <div
          :class="modalClasses"
          :style="modalStyles"
          @click.stop
        >
          <!-- Header -->
          <div v-if="$slots.header || title || titleAr" class="uw-modal-header">
            <slot name="header">
              <h2 :id="titleId" class="uw-modal-title">
                <span v-if="preferArabic && titleAr">{{ titleAr }}</span>
                <span v-else-if="title">{{ title }}</span>
                <span v-else-if="titleAr">{{ titleAr }}</span>
              </h2>
            </slot>
            
            <!-- Close button -->
            <button
              v-if="closable"
              type="button"
              class="uw-modal-close"
              :aria-label="closeLabel"
              @click="handleClose"
            >
              <svg class="uw-modal-close-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M18 6L6 18M6 6l12 12" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
          </div>
          
          <!-- Body -->
          <div :id="bodyId" class="uw-modal-body">
            <slot>
              <p v-if="message || messageAr">
                <span v-if="preferArabic && messageAr">{{ messageAr }}</span>
                <span v-else-if="message">{{ message }}</span>
                <span v-else-if="messageAr">{{ messageAr }}</span>
              </p>
            </slot>
          </div>
          
          <!-- Footer -->
          <div v-if="$slots.footer || actions?.length" class="uw-modal-footer">
            <slot name="footer">
              <div class="uw-modal-actions">
                <button
                  v-for="action in actions"
                  :key="action.key"
                  type="button"
                  :class="getActionClasses(action)"
                  :disabled="action.disabled"
                  @click="handleActionClick(action)"
                >
                  {{ preferArabic && action.labelAr ? action.labelAr : action.label }}
                </button>
              </div>
            </slot>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, inject, ref, watch, nextTick, onMounted, onUnmounted } from 'vue'

// Define action interface
export interface ModalAction {
  key: string
  label: string
  labelAr?: string
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger'
  disabled?: boolean
  handler?: () => void
}

// Define component props
export interface ModalProps {
  /** Modal visible state */
  visible?: boolean
  /** Modal title */
  title?: string
  /** Arabic modal title */
  titleAr?: string
  /** Modal message (for simple modals) */
  message?: string
  /** Arabic modal message */
  messageAr?: string
  /** Modal size */
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full'
  /** Modal is closable */
  closable?: boolean
  /** Close on backdrop click */
  closeOnBackdrop?: boolean
  /** Close on escape key */
  closeOnEscape?: boolean
  /** Show backdrop */
  showBackdrop?: boolean
  /** Blur backdrop */
  blurBackdrop?: boolean
  /** Prevent body scroll */
  preventScroll?: boolean
  /** Z-index */
  zIndex?: number
  /** Modal actions */
  actions?: ModalAction[]
  /** Prefer Arabic display */
  preferArabic?: boolean
  /** Custom CSS class */
  class?: string
}

// Define component emits
export interface ModalEmits {
  'update:visible': [value: boolean]
  open: []
  close: []
  'action-click': [action: ModalAction]
  'backdrop-click': []
  'escape-key': []
}

// Setup props with defaults
const props = withDefaults(defineProps<ModalProps>(), {
  visible: false,
  size: 'md',
  closable: true,
  closeOnBackdrop: true,
  closeOnEscape: true,
  showBackdrop: true,
  blurBackdrop: true,
  preventScroll: true,
  zIndex: 1000,
  preferArabic: true,
})

// Setup emits
const emit = defineEmits<ModalEmits>()

// Template refs
const modalRef = ref<HTMLElement>()

// Check if RTL context is available
const isRTL = inject('isRTL', true)

// Internal state
const internalVisible = ref(props.visible)
const focusableElements = ref<HTMLElement[]>([])
let previousActiveElement: HTMLElement | null = null

// Unique IDs for accessibility
const titleId = computed(() => `modal-title-${Math.random().toString(36).substr(2, 9)}`)
const bodyId = computed(() => `modal-body-${Math.random().toString(36).substr(2, 9)}`)

// Watch for external visible changes
watch(() => props.visible, (newValue) => {
  internalVisible.value = newValue
})

// Watch for internal visible changes
watch(internalVisible, (newValue) => {
  emit('update:visible', newValue)
  
  if (newValue) {
    emit('open')
    handleOpen()
  } else {
    emit('close')
    handleClose()
  }
})

// Close label for accessibility
const closeLabel = computed(() => {
  return props.preferArabic ? 'إغلاق النافذة' : 'Close modal'
})

// Size styles mapping
const sizeStyles = {
  xs: { maxWidth: '320px' },
  sm: { maxWidth: '480px' },
  md: { maxWidth: '640px' },
  lg: { maxWidth: '768px' },
  xl: { maxWidth: '1024px' },
  '2xl': { maxWidth: '1280px' },
  full: { maxWidth: '100vw', maxHeight: '100vh', margin: '0' },
}

// Computed classes
const modalWrapperClasses = computed(() => [
  'uw-modal-wrapper',
  {
    'uw-modal-wrapper--backdrop': props.showBackdrop,
    'uw-modal-wrapper--blur': props.blurBackdrop,
    'uw-modal-wrapper--rtl': isRTL,
  },
])

const modalClasses = computed(() => [
  'uw-modal',
  `uw-modal--${props.size}`,
  {
    'uw-modal--rtl': isRTL,
    'uw-modal--prefer-arabic': props.preferArabic,
  },
  props.class,
])

// Computed styles
const modalWrapperStyles = computed(() => ({
  zIndex: props.zIndex,
}))

const modalStyles = computed(() => {
  const styles = { ...sizeStyles[props.size] }
  return styles
})

// Get focusable elements within modal
const getFocusableElements = (): HTMLElement[] => {
  if (!modalRef.value) return []
  
  const selectors = [
    'button',
    '[href]',
    'input',
    'select',
    'textarea',
    '[tabindex]:not([tabindex="-1"])',
  ]
  
  const elements = modalRef.value.querySelectorAll(selectors.join(','))
  return Array.from(elements).filter(
    (el): el is HTMLElement => 
      el instanceof HTMLElement && 
      !el.disabled && 
      el.offsetParent !== null
  )
}

// Focus management
const trapFocus = (event: KeyboardEvent) => {
  if (!focusableElements.value.length) return
  
  const firstElement = focusableElements.value[0]
  const lastElement = focusableElements.value[focusableElements.value.length - 1]
  
  if (event.shiftKey && event.target === firstElement) {
    event.preventDefault()
    lastElement.focus()
  } else if (!event.shiftKey && event.target === lastElement) {
    event.preventDefault()
    firstElement.focus()
  }
}

// Get action button classes
const getActionClasses = (action: ModalAction) => [
  'uw-modal-action',
  `uw-modal-action--${action.variant || 'outline'}`,
  {
    'uw-modal-action--disabled': action.disabled,
  },
]

// Event handlers
const handleOpen = async () => {
  // Store currently focused element
  previousActiveElement = document.activeElement as HTMLElement
  
  // Prevent body scroll
  if (props.preventScroll) {
    document.body.style.overflow = 'hidden'
  }
  
  // Focus management
  await nextTick()
  focusableElements.value = getFocusableElements()
  
  if (focusableElements.value.length > 0) {
    focusableElements.value[0].focus()
  }
}

const handleCloseModal = () => {
  internalVisible.value = false
}

const handleClose = () => {
  // Restore body scroll
  if (props.preventScroll) {
    document.body.style.overflow = ''
  }
  
  // Restore focus
  if (previousActiveElement) {
    previousActiveElement.focus()
    previousActiveElement = null
  }
}

const handleBackdropClick = () => {
  emit('backdrop-click')
  if (props.closeOnBackdrop) {
    handleCloseModal()
  }
}

const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Escape') {
    emit('escape-key')
    if (props.closeOnEscape) {
      handleCloseModal()
    }
  } else if (event.key === 'Tab') {
    trapFocus(event)
  }
}

const handleActionClick = (action: ModalAction) => {
  if (action.disabled) return
  
  emit('action-click', action)
  if (action.handler) {
    action.handler()
  }
}

// Transition hooks
const handleEnter = () => {
  // Add any enter animation logic
}

const handleLeave = () => {
  // Add any leave animation logic
}

const handleAfterEnter = () => {
  // Focus first element after animation
  if (focusableElements.value.length > 0) {
    focusableElements.value[0].focus()
  }
}

const handleAfterLeave = () => {
  // Cleanup after animation
}

// Cleanup on unmount
onUnmounted(() => {
  if (props.preventScroll) {
    document.body.style.overflow = ''
  }
  if (previousActiveElement) {
    previousActiveElement.focus()
  }
})

// Expose methods
defineExpose({
  visible: internalVisible,
  close: handleCloseModal,
  focus: () => {
    if (focusableElements.value.length > 0) {
      focusableElements.value[0].focus()
    }
  },
})
</script>

<style lang="scss" scoped>
.uw-modal-wrapper {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-4);
  
  // RTL support
  &--rtl {
    direction: rtl;
  }
  
  // Backdrop
  &--backdrop {
    background-color: rgba(0, 0, 0, 0.5);
  }
  
  // Blur backdrop
  &--blur {
    backdrop-filter: blur(4px);
  }
}

.uw-modal {
  background: var(--color-surface-primary);
  border: 1px solid var(--color-border-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  max-height: calc(100vh - var(--spacing-8));
  overflow: hidden;
  display: flex;
  flex-direction: column;
  width: 100%;
  
  // RTL support
  &--rtl {
    direction: rtl;
    text-align: right;
  }
  
  // Arabic font preference
  &--prefer-arabic {
    font-family: var(--font-family-arabic);
  }
  
  // Size variants
  &--xs {
    max-width: 320px;
  }
  
  &--sm {
    max-width: 480px;
  }
  
  &--md {
    max-width: 640px;
  }
  
  &--lg {
    max-width: 768px;
  }
  
  &--xl {
    max-width: 1024px;
  }
  
  &--2xl {
    max-width: 1280px;
  }
  
  &--full {
    max-width: 100vw;
    max-height: 100vh;
    margin: 0;
    border-radius: 0;
  }
}

// Header styles
.uw-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-6) var(--spacing-6) var(--spacing-4);
  border-bottom: 1px solid var(--color-border-primary);
  flex-shrink: 0;
}

.uw-modal-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0;
  line-height: var(--line-height-tight);
}

// Close button styles
.uw-modal-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--spacing-8);
  height: var(--spacing-8);
  border: none;
  background: transparent;
  color: var(--color-text-secondary);
  cursor: pointer;
  border-radius: var(--radius-md);
  transition: var(--transition-colors);
  flex-shrink: 0;
  
  &:hover {
    background-color: var(--color-surface-secondary);
    color: var(--color-text-primary);
  }
  
  &:focus {
    outline: 2px solid var(--color-primary);
    outline-offset: 2px;
  }
}

.uw-modal-close-icon {
  width: var(--spacing-5);
  height: var(--spacing-5);
}

// Body styles
.uw-modal-body {
  flex: 1;
  padding: var(--spacing-6);
  overflow-y: auto;
  color: var(--color-text-secondary);
  line-height: var(--line-height-relaxed);
  
  // Custom scrollbar
  &::-webkit-scrollbar {
    width: 6px;
  }
  
  &::-webkit-scrollbar-track {
    background: var(--color-surface-secondary);
  }
  
  &::-webkit-scrollbar-thumb {
    background: var(--color-border-secondary);
    border-radius: 3px;
  }
  
  &::-webkit-scrollbar-thumb:hover {
    background: var(--color-border-primary);
  }
}

// Footer styles
.uw-modal-footer {
  padding: var(--spacing-4) var(--spacing-6) var(--spacing-6);
  border-top: 1px solid var(--color-border-primary);
  flex-shrink: 0;
}

.uw-modal-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  justify-content: flex-end;
  flex-wrap: wrap;
  
  .uw-modal--rtl & {
    justify-content: flex-start;
  }
}

.uw-modal-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-2) var(--spacing-4);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  border: 1px solid transparent;
  cursor: pointer;
  transition: var(--transition-colors);
  text-decoration: none;
  min-width: 80px;
  
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
    
    &:hover:not(.uw-modal-action--disabled) {
      background-color: var(--color-primary-600);
    }
  }
  
  &--secondary {
    background-color: var(--color-secondary);
    color: var(--color-secondary-foreground);
    
    &:hover:not(.uw-modal-action--disabled) {
      background-color: var(--color-secondary-600);
    }
  }
  
  &--outline {
    border-color: var(--color-border-primary);
    background-color: transparent;
    color: var(--color-text-primary);
    
    &:hover:not(.uw-modal-action--disabled) {
      background-color: var(--color-surface-secondary);
    }
  }
  
  &--ghost {
    background-color: transparent;
    color: var(--color-text-primary);
    
    &:hover:not(.uw-modal-action--disabled) {
      background-color: var(--color-surface-secondary);
    }
  }
  
  &--danger {
    background-color: var(--color-error);
    color: var(--color-error-foreground);
    
    &:hover:not(.uw-modal-action--disabled) {
      background-color: var(--color-error-600);
    }
  }
}

// Transitions
.modal-enter-active,
.modal-leave-active {
  transition: all 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .uw-modal,
.modal-leave-to .uw-modal {
  transform: scale(0.9) translateY(-20px);
}

// Responsive adjustments
@media (max-width: 640px) {
  .uw-modal-wrapper {
    padding: var(--spacing-2);
    align-items: flex-end;
  }
  
  .uw-modal {
    max-height: 90vh;
    width: 100%;
    
    &--xs,
    &--sm,
    &--md {
      max-width: none;
    }
  }
  
  .uw-modal-header {
    padding: var(--spacing-4);
  }
  
  .uw-modal-body {
    padding: var(--spacing-4);
  }
  
  .uw-modal-footer {
    padding: var(--spacing-3) var(--spacing-4) var(--spacing-4);
  }
  
  .uw-modal-actions {
    flex-direction: column;
    align-items: stretch;
    
    .uw-modal-action {
      width: 100%;
      justify-content: center;
    }
  }
}

// Dark mode support
[data-theme="dark"] {
  .uw-modal {
    background: var(--color-surface-secondary);
    border-color: var(--color-border-secondary);
  }
}

// High contrast mode
[data-contrast="high"] {
  .uw-modal {
    border-width: 2px;
  }
  
  .uw-modal-header {
    border-bottom-width: 2px;
  }
  
  .uw-modal-footer {
    border-top-width: 2px;
  }
}

// Reduced motion
@media (prefers-reduced-motion: reduce) {
  .modal-enter-active,
  .modal-leave-active {
    transition: opacity 0.2s ease;
  }
  
  .modal-enter-from .uw-modal,
  .modal-leave-to .uw-modal {
    transform: none;
  }
  
  .uw-modal-close,
  .uw-modal-action {
    transition: none;
  }
}
</style>