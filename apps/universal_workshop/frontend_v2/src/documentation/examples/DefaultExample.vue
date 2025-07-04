<!--
  Default Example - Universal Workshop Frontend V2
  
  Fallback example component when no specific example is found.
-->

<template>
  <div class="example-content">
    <div class="default-example">
      <div class="placeholder-icon">📋</div>
      <h3 class="placeholder-title">
        {{ preferArabic ? 'مثال غير متوفر' : 'Example Not Available' }}
      </h3>
      <p class="placeholder-message">
        {{ preferArabic 
          ? 'المثال المطلوب غير متوفر حالياً. يرجى المحاولة لاحقاً أو الاطلاع على الوثائق.'
          : 'The requested example is not available. Please try again later or refer to the documentation.'
        }}
      </p>
      <div class="placeholder-actions">
        <Button variant="outline" size="sm" @click="reportIssue">
          {{ preferArabic ? 'الإبلاغ عن مشكلة' : 'Report Issue' }}
        </Button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Button } from '@/components/base'

// Define props
const props = defineProps<{
  preferArabic?: boolean
  isRTL?: boolean
}>()

// Methods
const reportIssue = () => {
  const message = props.preferArabic
    ? 'تم الإبلاغ عن المشكلة. شكراً لك!'
    : 'Issue reported. Thank you!'
  
  alert(message)
}
</script>

<style lang="scss" scoped>
.example-content {
  padding: var(--spacing-6);
}

.default-example {
  text-align: center;
  padding: var(--spacing-8);
  border: 2px dashed var(--color-border-primary);
  border-radius: var(--radius-lg);
  background: var(--color-surface-secondary);
}

.placeholder-icon {
  font-size: 3rem;
  margin-bottom: var(--spacing-4);
}

.placeholder-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0 0 var(--spacing-3) 0;
}

.placeholder-message {
  color: var(--color-text-secondary);
  margin: 0 0 var(--spacing-4) 0;
  line-height: var(--line-height-relaxed);
  max-width: 400px;
  margin-left: auto;
  margin-right: auto;
}

.placeholder-actions {
  display: flex;
  justify-content: center;
  gap: var(--spacing-2);
}

// Dark mode support
[data-theme="dark"] {
  .default-example {
    background: var(--color-surface-tertiary);
    border-color: var(--color-border-secondary);
  }
}
</style>