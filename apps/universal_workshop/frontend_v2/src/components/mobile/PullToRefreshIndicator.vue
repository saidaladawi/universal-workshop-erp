<!--
  PullToRefreshIndicator Component - Universal Workshop Frontend V2
  
  Visual indicator for pull-to-refresh functionality with smooth animations,
  Arabic/RTL support, and customizable styling.
-->

<template>
  <Transition name="pull-indicator">
    <div 
      v-if="isVisible"
      :class="indicatorClasses"
      :style="indicatorStyles"
      :dir="isRTL ? 'rtl' : 'ltr'"
    >
      <!-- Icon -->
      <div class="pull-indicator__icon-container">
        <UWIcon 
          v-if="!isRefreshing"
          :name="canRefresh ? 'check' : 'arrow-down'"
          :class="iconClasses"
          size="lg"
          :color="iconColor"
        />
        
        <UWIcon 
          v-else
          name="loader"
          class="pull-indicator__spinner"
          size="lg"
          :color="iconColor"
          spin
        />
      </div>

      <!-- Text -->
      <div class="pull-indicator__text">
        {{ getDisplayText() }}
      </div>

      <!-- Progress Bar -->
      <div v-if="showProgressBar" class="pull-indicator__progress">
        <div 
          class="pull-indicator__progress-fill"
          :style="{ width: `${progress * 100}%` }"
        ></div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { computed, inject } from 'vue'
import { UWIcon } from '@/components/primitives'
import type { PullToRefreshIndicatorProps } from '@/composables/usePullToRefresh'
import { defaultPullToRefreshMessages } from '@/composables/usePullToRefresh'

export interface PullToRefreshIndicatorProps {
  isPulling: boolean
  isRefreshing: boolean
  progress: number
  pullDistance: number
  canRefresh: boolean
  rotationDegrees: number
  threshold: number
  showProgressBar?: boolean
  variant?: 'default' | 'minimal' | 'detailed'
  size?: 'sm' | 'md' | 'lg'
  messages?: {
    pullToRefresh?: string
    releaseToRefresh?: string
    refreshing?: string
    pullToRefreshAr?: string
    releaseToRefreshAr?: string
    refreshingAr?: string
  }
}

const props = withDefaults(defineProps<PullToRefreshIndicatorProps>(), {
  showProgressBar: true,
  variant: 'default',
  size: 'md',
  messages: () => defaultPullToRefreshMessages
})

// Injected context
const isRTL = inject('isRTL', false)

// Computed properties
const isVisible = computed(() => 
  props.isPulling || props.isRefreshing
)

const indicatorClasses = computed(() => [
  'pull-indicator',
  `pull-indicator--${props.variant}`,
  `pull-indicator--${props.size}`,
  {
    'pull-indicator--rtl': isRTL,
    'pull-indicator--can-refresh': props.canRefresh,
    'pull-indicator--refreshing': props.isRefreshing,
    'pull-indicator--pulling': props.isPulling
  }
])

const iconClasses = computed(() => [
  'pull-indicator__icon',
  {
    'pull-indicator__icon--rotated': props.canRefresh && !props.isRefreshing
  }
])

const indicatorStyles = computed(() => ({
  transform: `translateY(${Math.max(0, props.pullDistance - props.threshold)}px)`,
  opacity: Math.min(props.progress * 2, 1)
}))

const iconColor = computed(() => {
  if (props.isRefreshing) return 'var(--color-primary)'
  if (props.canRefresh) return 'var(--color-success)'
  return 'var(--color-text-secondary)'
})

// Methods
const getDisplayText = (): string => {
  const messages = { ...defaultPullToRefreshMessages, ...props.messages }
  
  if (props.isRefreshing) {
    return isRTL ? messages.refreshingAr || messages.refreshing : messages.refreshing
  }
  
  if (props.canRefresh) {
    return isRTL ? messages.releaseToRefreshAr || messages.releaseToRefresh : messages.releaseToRefresh
  }
  
  return isRTL ? messages.pullToRefreshAr || messages.pullToRefresh : messages.pullToRefresh
}
</script>

<style lang="scss" scoped>
.pull-indicator {
  --indicator-size: 60px;
  --indicator-padding: var(--spacing-3);
  --indicator-background: var(--color-background-elevated);
  --indicator-border-color: var(--color-border-subtle);
  --indicator-text-color: var(--color-text-secondary);
  --indicator-border-radius: var(--radius-lg);
  
  position: fixed;
  top: var(--spacing-4);
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
  
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-2);
  
  min-width: 120px;
  height: var(--indicator-size);
  padding: var(--indicator-padding);
  
  background: var(--indicator-background);
  border: 1px solid var(--indicator-border-color);
  border-radius: var(--indicator-border-radius);
  box-shadow: var(--shadow-lg);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  
  // Size variants
  &--sm {
    --indicator-size: 48px;
    --indicator-padding: var(--spacing-2);
    min-width: 100px;
    
    .pull-indicator__text {
      font-size: var(--font-size-xs);
    }
  }
  
  &--lg {
    --indicator-size: 72px;
    --indicator-padding: var(--spacing-4);
    min-width: 140px;
    
    .pull-indicator__text {
      font-size: var(--font-size-sm);
    }
  }
  
  // Style variants
  &--minimal {
    background: transparent;
    border: none;
    box-shadow: none;
    backdrop-filter: none;
    -webkit-backdrop-filter: none;
    
    .pull-indicator__text {
      display: none;
    }
    
    .pull-indicator__progress {
      display: none;
    }
  }
  
  &--detailed {
    min-width: 160px;
    
    .pull-indicator__progress {
      margin-top: var(--spacing-1);
    }
  }
  
  // RTL support
  &--rtl {
    direction: rtl;
    text-align: right;
  }
  
  // State classes
  &--can-refresh {
    --indicator-border-color: var(--color-success-border);
    
    .pull-indicator__progress-fill {
      background: var(--color-success);
    }
  }
  
  &--refreshing {
    --indicator-border-color: var(--color-primary-border);
    
    .pull-indicator__progress-fill {
      background: var(--color-primary);
    }
  }
}

.pull-indicator__icon-container {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pull-indicator__icon {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  
  &--rotated {
    transform: rotate(180deg);
  }
}

.pull-indicator__spinner {
  animation: spin 1s linear infinite;
}

.pull-indicator__text {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  color: var(--indicator-text-color);
  text-align: center;
  white-space: nowrap;
  user-select: none;
}

.pull-indicator__progress {
  width: 80px;
  height: 2px;
  background: var(--color-background-subtle);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.pull-indicator__progress-fill {
  height: 100%;
  background: var(--color-primary);
  border-radius: var(--radius-full);
  transition: width 0.2s ease, background-color 0.3s ease;
}

// Animations
.pull-indicator-enter-active,
.pull-indicator-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.pull-indicator-enter-from {
  opacity: 0;
  transform: translateX(-50%) translateY(-20px) scale(0.8);
}

.pull-indicator-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-20px) scale(0.8);
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

// Safe area support
@supports (padding: max(0px)) {
  .pull-indicator {
    top: max(var(--spacing-4), env(safe-area-inset-top) + var(--spacing-2));
  }
}

// Dark mode adjustments
@media (prefers-color-scheme: dark) {
  .pull-indicator {
    --indicator-background: rgba(31, 41, 55, 0.8);
    --indicator-border-color: rgba(75, 85, 99, 0.3);
  }
}

// High contrast mode
@media (prefers-contrast: high) {
  .pull-indicator {
    --indicator-border-color: var(--color-text-primary);
    border-width: 2px;
  }
}

// Reduced motion
@media (prefers-reduced-motion: reduce) {
  .pull-indicator__icon,
  .pull-indicator__progress-fill,
  .pull-indicator-enter-active,
  .pull-indicator-leave-active {
    transition: none;
  }
  
  .pull-indicator__spinner {
    animation: none;
  }
}
</style>