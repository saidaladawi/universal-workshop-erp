<!--
  KPI Widget Component - Universal Workshop Frontend V2
  
  Real-time KPI display widget with Arabic support, trend indicators,
  and interactive drill-down capabilities for workshop analytics.
-->

<template>
  <div :class="widgetClasses" :dir="isRTL ? 'rtl' : 'ltr'">
    <!-- Widget Header -->
    <div class="kpi-widget__header">
      <div class="kpi-widget__title-section">
        <h3 class="kpi-widget__title">
          {{ preferArabic ? kpi.nameAr : kpi.nameEn }}
        </h3>
        <div v-if="showCategory" class="kpi-widget__category">
          {{ getCategoryText() }}
        </div>
      </div>
      
      <div class="kpi-widget__actions">
        <button
          v-if="allowDrillDown"
          class="kpi-widget__drill-down"
          @click="handleDrillDown"
          :aria-label="preferArabic ? 'عرض التفاصيل' : 'View details'"
        >
          <UWIcon name="external-link" size="sm" />
        </button>
        
        <div class="kpi-widget__status">
          <div 
            class="kpi-widget__status-indicator"
            :class="`kpi-widget__status-indicator--${getStatusLevel()}`"
            :title="getStatusText()"
          ></div>
        </div>
      </div>
    </div>

    <!-- KPI Value Display -->
    <div class="kpi-widget__value-section">
      <div class="kpi-widget__main-value">
        <span class="kpi-widget__value" :class="getValueClasses()">
          {{ formatKPIValue() }}
        </span>
        <span class="kpi-widget__unit" v-if="showUnit">
          {{ kpi.unit }}
        </span>
      </div>

      <!-- Trend Indicator -->
      <div v-if="showTrend" class="kpi-widget__trend">
        <div class="kpi-widget__trend-icon">
          <UWIcon 
            :name="getTrendIcon()" 
            :color="getTrendColor()"
            size="sm"
          />
        </div>
        <span class="kpi-widget__trend-value" :style="{ color: getTrendColor() }">
          {{ formatTrendValue() }}
        </span>
        <span class="kpi-widget__trend-period">
          {{ preferArabic ? 'مقارنة بالفترة السابقة' : 'vs previous period' }}
        </span>
      </div>

      <!-- Target Progress (if target exists) -->
      <div v-if="kpi.target && showTarget" class="kpi-widget__target">
        <div class="kpi-widget__target-label">
          {{ preferArabic ? 'الهدف:' : 'Target:' }} {{ formatValue(kpi.target, kpi.unit) }}
        </div>
        <div class="kpi-widget__progress-bar">
          <div 
            class="kpi-widget__progress-fill"
            :style="{ 
              width: `${getTargetProgress()}%`,
              backgroundColor: getProgressColor()
            }"
          ></div>
        </div>
        <div class="kpi-widget__progress-text">
          {{ getTargetProgress().toFixed(1) }}% {{ preferArabic ? 'من الهدف' : 'of target' }}
        </div>
      </div>
    </div>

    <!-- Mini Chart (if enabled) -->
    <div v-if="showMiniChart && chartData" class="kpi-widget__mini-chart">
      <canvas 
        ref="chartCanvas"
        class="kpi-widget__chart-canvas"
        :width="chartWidth"
        :height="chartHeight"
      ></canvas>
    </div>

    <!-- Last Updated -->
    <div class="kpi-widget__footer">
      <div class="kpi-widget__last-updated">
        <UWIcon name="clock" size="xs" />
        <span>
          {{ preferArabic ? 'آخر تحديث:' : 'Updated:' }}
          {{ formatLastUpdated() }}
        </span>
      </div>
      
      <div v-if="kpi.priority === 'critical'" class="kpi-widget__priority-badge">
        <UWBadge content="Critical" contentAr="حرج" variant="error" size="xs" />
      </div>
    </div>

    <!-- Loading Overlay -->
    <div v-if="loading" class="kpi-widget__loading">
      <UWIcon name="loading" spin size="lg" />
    </div>

    <!-- Alert Overlay -->
    <div v-if="hasAlert" class="kpi-widget__alert">
      <UWIcon name="alert-triangle" size="md" color="var(--color-warning)" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, inject, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { UWIcon, UWBadge } from '@/components/primitives'
import type { KPIMetric } from './RealTimeAnalyticsEngine'

// Types
export interface KPIWidgetProps {
  kpi: KPIMetric
  preferArabic?: boolean
  isRTL?: boolean
  showTrend?: boolean
  showTarget?: boolean
  showCategory?: boolean
  showUnit?: boolean
  showMiniChart?: boolean
  allowDrillDown?: boolean
  loading?: boolean
  variant?: 'default' | 'compact' | 'detailed'
  chartData?: number[]
  chartWidth?: number
  chartHeight?: number
}

export interface KPIWidgetEmits {
  'drill-down': [kpi: KPIMetric]
  'alert-click': [kpi: KPIMetric]
  'value-click': [kpi: KPIMetric]
}

const props = withDefaults(defineProps<KPIWidgetProps>(), {
  preferArabic: false,
  isRTL: false,
  showTrend: true,
  showTarget: true,
  showCategory: false,
  showUnit: true,
  showMiniChart: false,
  allowDrillDown: true,
  loading: false,
  variant: 'default',
  chartWidth: 100,
  chartHeight: 30
})

const emit = defineEmits<KPIWidgetEmits>()

// Injected context
const isRTL = inject('isRTL', false)
const preferArabic = inject('preferArabic', false)

// Refs
const chartCanvas = ref<HTMLCanvasElement>()

// Computed properties
const widgetClasses = computed(() => [
  'kpi-widget',
  `kpi-widget--${props.variant}`,
  `kpi-widget--${props.kpi.category}`,
  `kpi-widget--${props.kpi.priority}`,
  {
    'kpi-widget--rtl': isRTL || props.isRTL,
    'kpi-widget--arabic': preferArabic || props.preferArabic,
    'kpi-widget--loading': props.loading,
    'kpi-widget--has-target': !!props.kpi.target,
    'kpi-widget--has-alert': hasAlert.value,
    'kpi-widget--trend-up': props.kpi.trend === 'up',
    'kpi-widget--trend-down': props.kpi.trend === 'down',
    'kpi-widget--trend-stable': props.kpi.trend === 'stable'
  }
])

const hasAlert = computed(() => {
  if (!props.kpi.target) return false
  
  // Alert if value is significantly below target
  const progress = (props.kpi.value / props.kpi.target) * 100
  return progress < 80 && props.kpi.priority === 'critical'
})

const getValueClasses = computed(() => [
  'kpi-widget__value-text',
  {
    'kpi-widget__value-text--critical': hasAlert.value,
    'kpi-widget__value-text--success': isAboveTarget.value,
    'kpi-widget__value-text--warning': isBelowTarget.value
  }
])

const isAboveTarget = computed(() => {
  if (!props.kpi.target) return false
  return props.kpi.value >= props.kpi.target
})

const isBelowTarget = computed(() => {
  if (!props.kpi.target) return false
  const progress = (props.kpi.value / props.kpi.target) * 100
  return progress < 90
})

// Methods
const formatKPIValue = (): string => {
  return formatValue(props.kpi.value, props.kpi.unit)
}

const formatValue = (value: number, unit: string): string => {
  const locale = (preferArabic.value || props.preferArabic) ? 'ar-SA' : 'en-OM'
  
  switch (unit) {
    case 'OMR':
      return new Intl.NumberFormat(locale, {
        style: 'currency',
        currency: 'OMR',
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
      }).format(value)
      
    case '%':
      return new Intl.NumberFormat(locale, {
        style: 'percent',
        minimumFractionDigits: 1,
        maximumFractionDigits: 1
      }).format(value / 100)
      
    case '/5':
      return `${value.toFixed(1)}/5`
      
    default:
      return new Intl.NumberFormat(locale, {
        minimumFractionDigits: 0,
        maximumFractionDigits: 1
      }).format(value)
  }
}

const getTrendIcon = (): string => {
  switch (props.kpi.trend) {
    case 'up': return 'trending-up'
    case 'down': return 'trending-down'
    default: return 'minus'
  }
}

const getTrendColor = (): string => {
  switch (props.kpi.trend) {
    case 'up': return 'var(--color-success)'
    case 'down': return 'var(--color-error)'
    default: return 'var(--color-text-secondary)'
  }
}

const formatTrendValue = (): string => {
  const sign = props.kpi.change >= 0 ? '+' : ''
  if (props.kpi.unit === '%') {
    return `${sign}${props.kpi.changePercent.toFixed(1)}%`
  }
  return `${sign}${props.kpi.change.toFixed(1)}`
}

const getTargetProgress = (): number => {
  if (!props.kpi.target) return 0
  return Math.min((props.kpi.value / props.kpi.target) * 100, 100)
}

const getProgressColor = (): string => {
  const progress = getTargetProgress()
  if (progress >= 100) return 'var(--color-success)'
  if (progress >= 80) return 'var(--color-warning)'
  return 'var(--color-error)'
}

const getStatusLevel = (): string => {
  if (hasAlert.value) return 'critical'
  if (isAboveTarget.value) return 'success'
  if (isBelowTarget.value) return 'warning'
  return 'normal'
}

const getStatusText = (): string => {
  const status = getStatusLevel()
  const statusTexts = {
    critical: { en: 'Critical - Attention Required', ar: 'حرج - يتطلب انتباه' },
    warning: { en: 'Below Target', ar: 'أقل من الهدف' },
    success: { en: 'Above Target', ar: 'فوق الهدف' },
    normal: { en: 'Normal', ar: 'طبيعي' }
  }
  
  const text = statusTexts[status as keyof typeof statusTexts]
  return (preferArabic.value || props.preferArabic) ? text.ar : text.en
}

const getCategoryText = (): string => {
  const categories = {
    efficiency: { en: 'Efficiency', ar: 'الكفاءة' },
    quality: { en: 'Quality', ar: 'الجودة' },
    financial: { en: 'Financial', ar: 'مالي' },
    customer: { en: 'Customer', ar: 'العملاء' }
  }
  
  const category = categories[props.kpi.category as keyof typeof categories]
  return (preferArabic.value || props.preferArabic) ? category?.ar || props.kpi.category : category?.en || props.kpi.category
}

const formatLastUpdated = (): string => {
  const now = new Date()
  const updated = new Date(props.kpi.lastUpdated)
  const diffMs = now.getTime() - updated.getTime()
  const diffMinutes = Math.floor(diffMs / 60000)
  
  if (preferArabic.value || props.preferArabic) {
    if (diffMinutes < 1) return 'الآن'
    if (diffMinutes < 60) return `منذ ${diffMinutes} دقيقة`
    const hours = Math.floor(diffMinutes / 60)
    return `منذ ${hours} ساعة`
  } else {
    if (diffMinutes < 1) return 'now'
    if (diffMinutes < 60) return `${diffMinutes}m ago`
    const hours = Math.floor(diffMinutes / 60)
    return `${hours}h ago`
  }
}

const handleDrillDown = (): void => {
  emit('drill-down', props.kpi)
}

// Mini chart rendering
const renderMiniChart = (): void => {
  if (!chartCanvas.value || !props.chartData) return
  
  const canvas = chartCanvas.value
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  
  // Clear canvas
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  
  // Simple line chart
  const data = props.chartData
  const max = Math.max(...data)
  const min = Math.min(...data)
  const range = max - min || 1
  
  ctx.strokeStyle = getTrendColor()
  ctx.lineWidth = 2
  ctx.beginPath()
  
  data.forEach((value, index) => {
    const x = (index / (data.length - 1)) * canvas.width
    const y = canvas.height - ((value - min) / range) * canvas.height
    
    if (index === 0) {
      ctx.moveTo(x, y)
    } else {
      ctx.lineTo(x, y)
    }
  })
  
  ctx.stroke()
  
  // Fill area under curve
  ctx.globalAlpha = 0.1
  ctx.fillStyle = getTrendColor()
  ctx.lineTo(canvas.width, canvas.height)
  ctx.lineTo(0, canvas.height)
  ctx.closePath()
  ctx.fill()
  ctx.globalAlpha = 1
}

// Watchers
watch(() => props.chartData, () => {
  if (props.showMiniChart) {
    nextTick(() => renderMiniChart())
  }
}, { deep: true })

watch(() => props.kpi.trend, () => {
  if (props.showMiniChart) {
    nextTick(() => renderMiniChart())
  }
})

// Lifecycle
onMounted(() => {
  if (props.showMiniChart) {
    nextTick(() => renderMiniChart())
  }
})
</script>

<style lang="scss" scoped>
.kpi-widget {
  --widget-padding: var(--spacing-4);
  --widget-border-radius: var(--radius-lg);
  --widget-background: var(--color-background-elevated);
  --widget-border-color: var(--color-border-subtle);
  --widget-shadow: var(--shadow-sm);
  
  position: relative;
  background: var(--widget-background);
  border: 1px solid var(--widget-border-color);
  border-radius: var(--widget-border-radius);
  padding: var(--widget-padding);
  box-shadow: var(--widget-shadow);
  transition: all 0.2s ease;
  
  &:hover {
    box-shadow: var(--shadow-md);
    transform: translateY(-1px);
  }
  
  // Variants
  &--compact {
    --widget-padding: var(--spacing-3);
    
    .kpi-widget__target,
    .kpi-widget__mini-chart {
      display: none;
    }
  }
  
  &--detailed {
    .kpi-widget__category,
    .kpi-widget__target,
    .kpi-widget__mini-chart {
      display: block;
    }
  }
  
  // Categories
  &--efficiency {
    border-left: 4px solid var(--color-primary);
  }
  
  &--quality {
    border-left: 4px solid var(--color-success);
  }
  
  &--financial {
    border-left: 4px solid var(--color-warning);
  }
  
  &--customer {
    border-left: 4px solid var(--color-info);
  }
  
  // Priority
  &--critical {
    --widget-border-color: var(--color-error-border);
    
    &.kpi-widget--has-alert {
      background: linear-gradient(135deg, var(--widget-background) 0%, var(--color-error-background) 100%);
    }
  }
  
  // RTL support
  &--rtl {
    direction: rtl;
    text-align: right;
    
    &.kpi-widget--efficiency,
    &.kpi-widget--quality,
    &.kpi-widget--financial,
    &.kpi-widget--customer {
      border-left: none;
      border-right: 4px solid;
    }
  }
  
  // Loading state
  &--loading {
    pointer-events: none;
    opacity: 0.7;
  }
}

.kpi-widget__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-3);
}

.kpi-widget__title-section {
  flex: 1;
  min-width: 0;
}

.kpi-widget__title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0 0 var(--spacing-1) 0;
  line-height: var(--line-height-tight);
}

.kpi-widget__category {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.kpi-widget__actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.kpi-widget__drill-down {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: none;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--color-text-tertiary);
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    background: var(--color-background-subtle);
    color: var(--color-text-primary);
  }
}

.kpi-widget__status {
  position: relative;
}

.kpi-widget__status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  
  &--normal {
    background: var(--color-text-tertiary);
  }
  
  &--success {
    background: var(--color-success);
  }
  
  &--warning {
    background: var(--color-warning);
  }
  
  &--critical {
    background: var(--color-error);
    animation: pulse 2s infinite;
  }
}

.kpi-widget__value-section {
  margin-bottom: var(--spacing-4);
}

.kpi-widget__main-value {
  display: flex;
  align-items: baseline;
  gap: var(--spacing-1);
  margin-bottom: var(--spacing-2);
}

.kpi-widget__value {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  line-height: var(--line-height-none);
  
  &--critical {
    color: var(--color-error);
  }
  
  &--success {
    color: var(--color-success);
  }
  
  &--warning {
    color: var(--color-warning);
  }
}

.kpi-widget__unit {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  font-weight: var(--font-weight-medium);
}

.kpi-widget__trend {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  font-size: var(--font-size-xs);
  margin-bottom: var(--spacing-2);
}

.kpi-widget__trend-icon {
  display: flex;
  align-items: center;
}

.kpi-widget__trend-value {
  font-weight: var(--font-weight-semibold);
}

.kpi-widget__trend-period {
  color: var(--color-text-tertiary);
}

.kpi-widget__target {
  margin-bottom: var(--spacing-3);
}

.kpi-widget__target-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-1);
}

.kpi-widget__progress-bar {
  height: 4px;
  background: var(--color-background-subtle);
  border-radius: var(--radius-full);
  overflow: hidden;
  margin-bottom: var(--spacing-1);
}

.kpi-widget__progress-fill {
  height: 100%;
  border-radius: var(--radius-full);
  transition: width 0.3s ease, background-color 0.3s ease;
}

.kpi-widget__progress-text {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

.kpi-widget__mini-chart {
  margin-bottom: var(--spacing-3);
}

.kpi-widget__chart-canvas {
  width: 100%;
  height: 30px;
  display: block;
}

.kpi-widget__footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.kpi-widget__last-updated {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

.kpi-widget__priority-badge {
  display: flex;
  align-items: center;
}

.kpi-widget__loading {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.8);
  border-radius: var(--widget-border-radius);
  backdrop-filter: blur(2px);
  -webkit-backdrop-filter: blur(2px);
}

.kpi-widget__alert {
  position: absolute;
  top: var(--spacing-2);
  right: var(--spacing-2);
  z-index: 10;
  
  .kpi-widget--rtl & {
    right: auto;
    left: var(--spacing-2);
  }
}

// Animations
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

// Responsive adjustments
@media (max-width: 768px) {
  .kpi-widget {
    --widget-padding: var(--spacing-3);
  }
  
  .kpi-widget__value {
    font-size: var(--font-size-xl);
  }
}
</style>