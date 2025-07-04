<!--
  Example Renderer - Universal Workshop Frontend V2
  
  Dynamic component example renderer that loads and displays component
  examples with live props and Arabic/RTL support.
-->

<template>
  <div :class="rendererClasses">
    <component
      :is="exampleComponent"
      v-if="exampleComponent"
      v-bind="computedProps"
      :prefer-arabic="preferArabic"
      :is-rtl="isRTL"
      @error="handleError"
    />
    
    <!-- Error State -->
    <div v-else-if="hasError" class="example-error">
      <div class="error-icon">⚠️</div>
      <div class="error-content">
        <h4 class="error-title">
          {{ preferArabic ? 'خطأ في تحميل المثال' : 'Example Loading Error' }}
        </h4>
        <p class="error-message">
          {{ errorMessage }}
        </p>
        <Button
          variant="outline"
          size="sm"
          @click="retryLoad"
        >
          {{ preferArabic ? 'إعادة المحاولة' : 'Retry' }}
        </Button>
      </div>
    </div>
    
    <!-- Loading State -->
    <div v-else class="example-loading">
      <div class="loading-spinner"></div>
      <p>{{ preferArabic ? 'جارٍ تحميل المثال...' : 'Loading example...' }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, defineAsyncComponent } from 'vue'
import { Button } from '@/components/base'

// Define component props
export interface ExampleRendererProps {
  template: string
  props?: Record<string, any>
  preferArabic?: boolean
  isRTL?: boolean
}

// Setup props with defaults
const props = withDefaults(defineProps<ExampleRendererProps>(), {
  props: () => ({}),
  preferArabic: true,
  isRTL: true,
})

// Component state
const hasError = ref(false)
const errorMessage = ref('')
const loadAttempts = ref(0)
const maxAttempts = 3

// Example component templates registry
const exampleTemplates = {
  // Button Examples
  ButtonVariants: defineAsyncComponent({
    loader: () => import('./examples/ButtonVariants.vue'),
    loadingComponent: () => null,
    errorComponent: () => null,
    delay: 200,
    timeout: 3000,
  }),
  
  ButtonSizes: defineAsyncComponent({
    loader: () => import('./examples/ButtonSizes.vue'),
    loadingComponent: () => null,
    errorComponent: () => null,
    delay: 200,
    timeout: 3000,
  }),
  
  ButtonStates: defineAsyncComponent({
    loader: () => import('./examples/ButtonStates.vue'),
    loadingComponent: () => null,
    errorComponent: () => null,
    delay: 200,
    timeout: 3000,
  }),
  
  // Input Examples
  InputBasic: defineAsyncComponent({
    loader: () => import('./examples/InputBasic.vue'),
    loadingComponent: () => null,
    errorComponent: () => null,
    delay: 200,
    timeout: 3000,
  }),
  
  // Card Examples
  CardBasic: defineAsyncComponent({
    loader: () => import('./examples/CardBasic.vue'),
    loadingComponent: () => null,
    errorComponent: () => null,
    delay: 200,
    timeout: 3000,
  }),
  
  // Form Examples
  FormValidation: defineAsyncComponent({
    loader: () => import('./examples/FormValidation.vue'),
    loadingComponent: () => null,
    errorComponent: () => null,
    delay: 200,
    timeout: 3000,
  }),
  
  FormFieldBasic: defineAsyncComponent({
    loader: () => import('./examples/FormFieldBasic.vue'),
    loadingComponent: () => null,
    errorComponent: () => null,
    delay: 200,
    timeout: 3000,
  }),
  
  // Layout Examples
  ContainerSizes: defineAsyncComponent({
    loader: () => import('./examples/ContainerSizes.vue'),
    loadingComponent: () => null,
    errorComponent: () => null,
    delay: 200,
    timeout: 3000,
  }),
  
  GridBasic: defineAsyncComponent({
    loader: () => import('./examples/GridBasic.vue'),
    loadingComponent: () => null,
    errorComponent: () => null,
    delay: 200,
    timeout: 3000,
  }),
  
  // Fallback for unknown templates
  DefaultExample: defineAsyncComponent({
    loader: () => import('./examples/DefaultExample.vue'),
    loadingComponent: () => null,
    errorComponent: () => null,
    delay: 200,
    timeout: 3000,
  }),
}

// Computed values
const rendererClasses = computed(() => [
  'example-renderer',
  {
    'example-renderer--rtl': props.isRTL,
    'example-renderer--arabic': props.preferArabic,
    'example-renderer--error': hasError.value,
  },
])

const exampleComponent = computed(() => {
  if (hasError.value) return null
  
  // Get the component from the registry
  const template = props.template as keyof typeof exampleTemplates
  return exampleTemplates[template] || exampleTemplates.DefaultExample
})

const computedProps = computed(() => {
  return {
    ...props.props,
    preferArabic: props.preferArabic,
    isRTL: props.isRTL,
  }
})

// Methods
const handleError = (error: Error) => {
  console.error('Example component error:', error)
  hasError.value = true
  errorMessage.value = props.preferArabic 
    ? `فشل في تحميل المثال: ${props.template}`
    : `Failed to load example: ${props.template}`
}

const retryLoad = () => {
  if (loadAttempts.value < maxAttempts) {
    loadAttempts.value++
    hasError.value = false
    errorMessage.value = ''
  } else {
    errorMessage.value = props.preferArabic
      ? 'تم تجاوز الحد الأقصى لمحاولات التحميل'
      : 'Maximum retry attempts exceeded'
  }
}

// Watch for template changes
watch(() => props.template, () => {
  hasError.value = false
  errorMessage.value = ''
  loadAttempts.value = 0
})

// Handle component loading errors
watch(exampleComponent, (newComponent) => {
  if (newComponent && typeof newComponent === 'object' && 'error' in newComponent) {
    handleError(newComponent.error as Error)
  }
})
</script>

<style lang="scss" scoped>
.example-renderer {
  position: relative;
  min-height: 80px;
  
  // RTL support
  &--rtl {
    direction: rtl;
    text-align: right;
  }
  
  // Arabic font preference
  &--arabic {
    font-family: var(--font-family-arabic);
  }
  
  // Error state styling
  &--error {
    background: var(--color-error-50);
    border: 1px solid var(--color-error-200);
    border-radius: var(--radius-md);
  }
}

// Error state styles
.example-error {
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
  padding: var(--spacing-6);
  text-align: center;
  
  @media (max-width: 640px) {
    flex-direction: column;
    text-align: center;
  }
}

.error-icon {
  font-size: 2rem;
  flex-shrink: 0;
}

.error-content {
  flex: 1;
  
  @media (max-width: 640px) {
    text-align: center;
  }
}

.error-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-error);
  margin: 0 0 var(--spacing-2) 0;
}

.error-message {
  color: var(--color-error-700);
  margin: 0 0 var(--spacing-3) 0;
  font-size: var(--font-size-sm);
  line-height: var(--line-height-relaxed);
}

// Loading state styles
.example-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-8);
  color: var(--color-text-secondary);
  
  p {
    margin: var(--spacing-3) 0 0 0;
    font-size: var(--font-size-sm);
  }
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 2px solid var(--color-border-primary);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

// Example content styling
.example-renderer :deep(.example-content) {
  padding: var(--spacing-4);
  
  // Ensure examples have proper spacing
  > * + * {
    margin-top: var(--spacing-3);
  }
  
  // Style example groups
  .example-group {
    display: flex;
    flex-wrap: wrap;
    gap: var(--spacing-3);
    align-items: center;
    
    &--vertical {
      flex-direction: column;
      align-items: stretch;
    }
    
    &--center {
      justify-content: center;
    }
  }
  
  // Style example labels
  .example-label {
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    color: var(--color-text-secondary);
    margin-bottom: var(--spacing-2);
  }
  
  // Style code snippets in examples
  .example-code {
    font-family: var(--font-family-mono);
    background: var(--color-surface-secondary);
    padding: var(--spacing-2) var(--spacing-3);
    border-radius: var(--radius-sm);
    font-size: var(--font-size-sm);
    color: var(--color-text-primary);
  }
}

// Responsive adjustments
@media (max-width: 640px) {
  .example-renderer :deep(.example-content) {
    padding: var(--spacing-3);
    
    .example-group {
      flex-direction: column;
      align-items: stretch;
    }
  }
}

// Animation
@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

// Dark mode support
[data-theme="dark"] {
  .example-error {
    background: var(--color-error-950);
    border-color: var(--color-error-800);
  }
  
  .error-title {
    color: var(--color-error-200);
  }
  
  .error-message {
    color: var(--color-error-300);
  }
}

// Reduced motion
@media (prefers-reduced-motion: reduce) {
  .loading-spinner {
    animation: none;
  }
}

// High contrast mode
[data-contrast="high"] {
  .example-error {
    border-width: 2px;
  }
  
  .error-title {
    font-weight: var(--font-weight-bold);
  }
}
</style>