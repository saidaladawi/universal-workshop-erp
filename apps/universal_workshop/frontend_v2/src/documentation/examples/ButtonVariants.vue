<!--
  Button Variants Example - Universal Workshop Frontend V2
  
  Demonstrates all available button variants with Arabic/RTL support.
-->

<template>
  <div class="example-content">
    <div class="example-label">
      {{ preferArabic ? 'متغيرات الزر' : 'Button Variants' }}
    </div>
    
    <div class="example-group">
      <Button variant="primary">
        {{ preferArabic ? 'أساسي' : 'Primary' }}
      </Button>
      
      <Button variant="secondary">
        {{ preferArabic ? 'ثانوي' : 'Secondary' }}
      </Button>
      
      <Button variant="outline">
        {{ preferArabic ? 'محدد' : 'Outline' }}
      </Button>
      
      <Button variant="ghost">
        {{ preferArabic ? 'شفاف' : 'Ghost' }}
      </Button>
      
      <Button variant="danger">
        {{ preferArabic ? 'خطر' : 'Danger' }}
      </Button>
    </div>
    
    <div class="example-description">
      {{ preferArabic 
        ? 'استخدم متغيرات مختلفة حسب أهمية الإجراء في السياق'
        : 'Use different variants based on the action importance in context'
      }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { Button } from '@/components/base'

// Define props
defineProps<{
  preferArabic?: boolean
  isRTL?: boolean
}>()
</script>

<style lang="scss" scoped>
.example-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}

.example-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
}

.example-group {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-3);
  align-items: center;
}

.example-description {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  font-style: italic;
}

@media (max-width: 640px) {
  .example-group {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>