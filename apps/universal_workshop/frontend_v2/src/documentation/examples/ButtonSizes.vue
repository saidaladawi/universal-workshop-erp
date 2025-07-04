<!--
  Button Sizes Example - Universal Workshop Frontend V2
  
  Demonstrates all available button sizes with Arabic/RTL support.
-->

<template>
  <div class="example-content">
    <div class="example-label">
      {{ preferArabic ? 'أحجام الزر' : 'Button Sizes' }}
    </div>
    
    <div class="example-group example-group--center">
      <Button size="sm">
        {{ preferArabic ? 'صغير' : 'Small' }}
      </Button>
      
      <Button size="md">
        {{ preferArabic ? 'متوسط' : 'Medium' }}
      </Button>
      
      <Button size="lg">
        {{ preferArabic ? 'كبير' : 'Large' }}
      </Button>
      
      <Button size="xl">
        {{ preferArabic ? 'كبير جداً' : 'Extra Large' }}
      </Button>
    </div>
    
    <div class="example-group example-group--vertical">
      <div class="example-label">
        {{ preferArabic ? 'عرض كامل' : 'Full Width' }}
      </div>
      <Button full-width>
        {{ preferArabic ? 'زر بعرض كامل' : 'Full Width Button' }}
      </Button>
    </div>
    
    <div class="example-description">
      {{ preferArabic 
        ? 'اختر الحجم المناسب حسب السياق والأهمية'
        : 'Choose appropriate size based on context and importance'
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
  
  &--center {
    justify-content: center;
  }
  
  &--vertical {
    flex-direction: column;
    align-items: stretch;
  }
}

.example-description {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  font-style: italic;
}

@media (max-width: 640px) {
  .example-group:not(.example-group--vertical) {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>