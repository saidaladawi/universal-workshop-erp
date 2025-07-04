<!--
  Analytics Dashboard - Universal Workshop Frontend V2
  
  Comprehensive real-time analytics dashboard with KPI widgets,
  charts, and Arabic/RTL support for workshop management.
-->

<template>
  <div :class="dashboardClasses" :dir="isRTL ? 'rtl' : 'ltr'">
    <!-- Dashboard Header -->
    <div class="analytics-dashboard__header">
      <div class="analytics-dashboard__title-section">
        <h1 class="analytics-dashboard__title">
          {{ preferArabic ? 'لوحة التحليلات' : 'Analytics Dashboard' }}
        </h1>
        <p class="analytics-dashboard__subtitle">
          {{ preferArabic ? 'تحليلات الورشة في الوقت الفعلي' : 'Real-time workshop analytics' }}
        </p>
      </div>

      <div class="analytics-dashboard__controls">
        <!-- Time Range Selector -->
        <div class="analytics-dashboard__time-range">
          <UWSelect
            v-model="selectedTimeRange"
            :options="timeRangeOptions"
            :placeholder="preferArabic ? 'اختر الفترة الزمنية' : 'Select time range'"
            @change="handleTimeRangeChange"
          />
        </div>

        <!-- Refresh Button -->
        <UWButton
          variant="outline"
          size="sm"
          :loading="isRefreshing"
          @click="refreshDashboard"
        >
          <UWIcon name="refresh-cw" size="sm" />
          {{ preferArabic ? 'تحديث' : 'Refresh' }}
        </UWButton>

        <!-- Dashboard Settings -->
        <UWButton
          variant="ghost"
          size="sm"
          @click="showSettings = true"
        >
          <UWIcon name="settings" size="sm" />
        </UWButton>
      </div>
    </div>

    <!-- Connection Status -->
    <div v-if="!isConnected" class="analytics-dashboard__connection-warning">
      <UWAlert
        type="warning"
        :title="preferArabic ? 'غير متصل' : 'Disconnected'"
        :message="preferArabic ? 'التحديثات المباشرة معطلة' : 'Real-time updates disabled'"
        :dismissible="false"
      />
    </div>

    <!-- KPI Grid -->
    <div class="analytics-dashboard__kpi-grid">
      <KPIWidget
        v-for="kpi in displayedKPIs"
        :key="kpi.id"
        :kpi="kpi"
        :prefer-arabic="preferArabic"
        :is-rtl="isRTL"
        :show-trend="showTrends"
        :show-target="showTargets"
        :show-mini-chart="showMiniCharts"
        :loading="isLoadingKPIs"
        :chart-data="getKPIChartData(kpi.id)"
        @drill-down="handleKPIDrillDown"
        @alert-click="handleKPIAlert"
      />
    </div>

    <!-- Charts Section -->
    <div class="analytics-dashboard__charts-section">
      <div class="analytics-dashboard__section-header">
        <h2 class="analytics-dashboard__section-title">
          {{ preferArabic ? 'المخططات البيانية' : 'Charts & Trends' }}
        </h2>
        
        <div class="analytics-dashboard__chart-controls">
          <UWButton
            v-for="chartType in chartTypes"
            :key="chartType.id"
            :variant="activeChartType === chartType.id ? 'primary' : 'outline'"
            size="sm"
            @click="setActiveChartType(chartType.id)"
          >
            {{ preferArabic ? chartType.labelAr : chartType.label }}
          </UWButton>
        </div>
      </div>

      <!-- Chart Container -->
      <div class="analytics-dashboard__chart-container">
        <canvas 
          ref="mainChart"
          class="analytics-dashboard__main-chart"
          :width="chartWidth"
          :height="chartHeight"
        ></canvas>
      </div>
    </div>

    <!-- Alerts Section -->
    <div v-if="predictiveAlerts.length > 0" class="analytics-dashboard__alerts-section">
      <div class="analytics-dashboard__section-header">
        <h2 class="analytics-dashboard__section-title">
          {{ preferArabic ? 'التنبيهات التنبؤية' : 'Predictive Alerts' }}
        </h2>
        
        <UWBadge 
          :content="predictiveAlerts.length"
          variant="error"
          size="sm"
        />
      </div>

      <div class="analytics-dashboard__alerts-grid">
        <div
          v-for="alert in predictiveAlerts"
          :key="alert.id"
          class="analytics-dashboard__alert-card"
          :class="`analytics-dashboard__alert-card--${alert.severity}`"
          @click="handleAlertClick(alert)"
        >
          <div class="analytics-dashboard__alert-header">
            <UWIcon 
              :name="getAlertIcon(alert.type)" 
              :color="getAlertColor(alert.severity)"
              size="md"
            />
            <div class="analytics-dashboard__alert-title">
              {{ preferArabic ? alert.titleAr : alert.titleEn }}
            </div>
            <div class="analytics-dashboard__alert-confidence">
              {{ alert.confidence.toFixed(1) }}%
            </div>
          </div>
          
          <div class="analytics-dashboard__alert-content">
            <p class="analytics-dashboard__alert-description">
              {{ preferArabic ? alert.descriptionAr : alert.descriptionEn }}
            </p>
            
            <div class="analytics-dashboard__alert-meta">
              <span class="analytics-dashboard__alert-date">
                {{ formatDate(alert.predictedDate) }}
              </span>
              <span v-if="alert.estimatedCost" class="analytics-dashboard__alert-cost">
                {{ formatCurrency(alert.estimatedCost) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Reports Section -->
    <div class="analytics-dashboard__reports-section">
      <div class="analytics-dashboard__section-header">
        <h2 class="analytics-dashboard__section-title">
          {{ preferArabic ? 'التقارير السريعة' : 'Quick Reports' }}
        </h2>
        
        <UWButton
          variant="primary"
          size="sm"
          @click="generateReport"
          :loading="isGeneratingReport"
        >
          <UWIcon name="file-text" size="sm" />
          {{ preferArabic ? 'إنشاء تقرير' : 'Generate Report' }}
        </UWButton>
      </div>

      <div class="analytics-dashboard__reports-grid">
        <div
          v-for="reportType in quickReportTypes"
          :key="reportType.id"
          class="analytics-dashboard__report-card"
          @click="generateQuickReport(reportType.id)"
        >
          <UWIcon :name="reportType.icon" size="lg" />
          <div class="analytics-dashboard__report-title">
            {{ preferArabic ? reportType.titleAr : reportType.title }}
          </div>
          <div class="analytics-dashboard__report-description">
            {{ preferArabic ? reportType.descriptionAr : reportType.description }}
          </div>
        </div>
      </div>
    </div>

    <!-- Settings Modal -->
    <UWModal
      v-model="showSettings"
      :title="preferArabic ? 'إعدادات لوحة التحليلات' : 'Dashboard Settings'"
      size="md"
    >
      <div class="analytics-dashboard__settings">
        <div class="analytics-dashboard__setting-group">
          <h3>{{ preferArabic ? 'خيارات العرض' : 'Display Options' }}</h3>
          
          <UWCheckbox
            v-model="showTrends"
            :label="preferArabic ? 'عرض الاتجاهات' : 'Show trends'"
          />
          
          <UWCheckbox
            v-model="showTargets"
            :label="preferArabic ? 'عرض الأهداف' : 'Show targets'"
          />
          
          <UWCheckbox
            v-model="showMiniCharts"
            :label="preferArabic ? 'عرض المخططات المصغرة' : 'Show mini charts'"
          />
        </div>

        <div class="analytics-dashboard__setting-group">
          <h3>{{ preferArabic ? 'التحديث التلقائي' : 'Auto Refresh' }}</h3>
          
          <UWSelect
            v-model="refreshInterval"
            :options="refreshIntervalOptions"
            :label="preferArabic ? 'فترة التحديث' : 'Refresh interval'"
          />
        </div>
      </div>
    </UWModal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { UWButton, UWSelect, UWModal, UWCheckbox } from '@/components/base'
import { UWIcon, UWBadge, UWAlert } from '@/components/primitives'
import KPIWidget from './KPIWidget.vue'
import { RealTimeAnalyticsEngine, type KPIMetric, type PredictiveAlert } from './RealTimeAnalyticsEngine'
import { workshopEventBus } from '@/features/realtime/WorkshopEventBus'

// Props & Emits
export interface AnalyticsDashboardProps {
  preferArabic?: boolean
  isRTL?: boolean
  autoRefresh?: boolean
  refreshInterval?: number
}

const props = withDefaults(defineProps<AnalyticsDashboardProps>(), {
  preferArabic: false,
  isRTL: false,
  autoRefresh: true,
  refreshInterval: 30000
})

// State
const analyticsEngine = ref<RealTimeAnalyticsEngine>()
const kpis = ref<KPIMetric[]>([])
const predictiveAlerts = ref<PredictiveAlert[]>([])
const isConnected = ref(false)
const isLoadingKPIs = ref(false)
const isRefreshing = ref(false)
const isGeneratingReport = ref(false)
const showSettings = ref(false)

// Dashboard settings
const selectedTimeRange = ref('today')
const activeChartType = ref('service_trends')
const showTrends = ref(true)
const showTargets = ref(true)
const showMiniCharts = ref(false)
const refreshInterval = ref(30000)

// Chart refs
const mainChart = ref<HTMLCanvasElement>()
const chartWidth = ref(800)
const chartHeight = ref(400)

// Sample chart data (would be replaced with real data)
const kpiChartData = ref<Record<string, number[]>>({})

// Options
const timeRangeOptions = computed(() => [
  { value: 'today', label: 'Today', labelAr: 'اليوم' },
  { value: 'week', label: 'This Week', labelAr: 'هذا الأسبوع' },
  { value: 'month', label: 'This Month', labelAr: 'هذا الشهر' },
  { value: 'quarter', label: 'This Quarter', labelAr: 'هذا الربع' }
])

const chartTypes = computed(() => [
  { id: 'service_trends', label: 'Service Trends', labelAr: 'اتجاهات الخدمة' },
  { id: 'revenue_analysis', label: 'Revenue Analysis', labelAr: 'تحليل الإيرادات' },
  { id: 'customer_satisfaction', label: 'Customer Satisfaction', labelAr: 'رضا العملاء' },
  { id: 'technician_performance', label: 'Technician Performance', labelAr: 'أداء الفنيين' }
])

const refreshIntervalOptions = computed(() => [
  { value: 15000, label: '15 seconds', labelAr: '15 ثانية' },
  { value: 30000, label: '30 seconds', labelAr: '30 ثانية' },
  { value: 60000, label: '1 minute', labelAr: 'دقيقة واحدة' },
  { value: 300000, label: '5 minutes', labelAr: '5 دقائق' }
])

const quickReportTypes = computed(() => [
  {
    id: 'daily_summary',
    title: 'Daily Summary',
    titleAr: 'ملخص يومي',
    description: 'Daily workshop performance summary',
    descriptionAr: 'ملخص الأداء اليومي للورشة',
    icon: 'calendar'
  },
  {
    id: 'efficiency_report',
    title: 'Efficiency Report',
    titleAr: 'تقرير الكفاءة',
    description: 'Technician and bay efficiency analysis',
    descriptionAr: 'تحليل كفاءة الفنيين والأرصفة',
    icon: 'trending-up'
  },
  {
    id: 'financial_overview',
    title: 'Financial Overview',
    titleAr: 'نظرة مالية عامة',
    description: 'Revenue, costs, and profitability',
    descriptionAr: 'الإيرادات والتكاليف والربحية',
    icon: 'dollar-sign'
  },
  {
    id: 'customer_insights',
    title: 'Customer Insights',
    titleAr: 'رؤى العملاء',
    description: 'Customer satisfaction and feedback',
    descriptionAr: 'رضا العملاء والتعليقات',
    icon: 'users'
  }
])

// Computed
const dashboardClasses = computed(() => [
  'analytics-dashboard',
  {
    'analytics-dashboard--rtl': props.isRTL,
    'analytics-dashboard--arabic': props.preferArabic,
    'analytics-dashboard--disconnected': !isConnected.value
  }
])

const displayedKPIs = computed(() => {
  return kpis.value.filter(kpi => {
    // Filter based on current settings
    return true // For now, show all KPIs
  })
})

// Methods
const initializeAnalytics = async (): Promise<void> => {
  try {
    analyticsEngine.value = new RealTimeAnalyticsEngine()
    await analyticsEngine.value.initialize()
    
    // Set up event listeners
    setupEventListeners()
    
    // Load initial data
    await loadDashboardData()
    
    console.log('📊 Analytics dashboard initialized')
  } catch (error) {
    console.error('❌ Failed to initialize analytics dashboard:', error)
  }
}

const setupEventListeners = (): void => {
  if (!analyticsEngine.value) return

  // Analytics engine events
  analyticsEngine.value.subscribe('kpis-updated', (updatedKPIs: KPIMetric[]) => {
    kpis.value = updatedKPIs
    updateKPIChartData()
  })

  analyticsEngine.value.subscribe('alerts-updated', (alerts: PredictiveAlert[]) => {
    predictiveAlerts.value = alerts
  })

  // Workshop event bus events
  workshopEventBus.on('connection', (event: any) => {
    isConnected.value = event.status === 'connected'
  })

  workshopEventBus.on('service_update', () => {
    refreshKPIs()
  })
}

const loadDashboardData = async (): Promise<void> => {
  try {
    isLoadingKPIs.value = true
    
    if (analyticsEngine.value) {
      // Load KPIs
      kpis.value = await analyticsEngine.value.getWorkshopKPIs()
      
      // Load predictive alerts
      predictiveAlerts.value = await analyticsEngine.value.getPredictiveAlerts()
      
      // Generate chart data
      updateKPIChartData()
    }
  } catch (error) {
    console.error('❌ Failed to load dashboard data:', error)
  } finally {
    isLoadingKPIs.value = false
  }
}

const updateKPIChartData = (): void => {
  // Generate sample chart data for each KPI
  kpis.value.forEach(kpi => {
    const data = []
    for (let i = 0; i < 7; i++) {
      const variation = (Math.random() - 0.5) * 0.2
      data.push(kpi.value * (1 + variation))
    }
    kpiChartData.value[kpi.id] = data
  })
}

const refreshDashboard = async (): Promise<void> => {
  try {
    isRefreshing.value = true
    await loadDashboardData()
    
    if (mainChart.value) {
      renderMainChart()
    }
  } catch (error) {
    console.error('❌ Failed to refresh dashboard:', error)
  } finally {
    isRefreshing.value = false
  }
}

const refreshKPIs = async (): Promise<void> => {
  if (analyticsEngine.value) {
    await analyticsEngine.value.refreshKPIs()
  }
}

const handleTimeRangeChange = (newRange: string): void => {
  selectedTimeRange.value = newRange
  // Refresh data for new time range
  loadDashboardData()
}

const setActiveChartType = (chartType: string): void => {
  activeChartType.value = chartType
  nextTick(() => renderMainChart())
}

const handleKPIDrillDown = (kpi: KPIMetric): void => {
  console.log('KPI drill down:', kpi.id)
  // Implement drill-down functionality
}

const handleKPIAlert = (kpi: KPIMetric): void => {
  console.log('KPI alert clicked:', kpi.id)
  // Handle KPI alert
}

const handleAlertClick = (alert: PredictiveAlert): void => {
  console.log('Alert clicked:', alert.id)
  // Show alert details
}

const generateReport = async (): Promise<void> => {
  try {
    isGeneratingReport.value = true
    
    if (analyticsEngine.value) {
      const report = await analyticsEngine.value.generateArabicReport('daily')
      console.log('📄 Report generated:', report.id)
      // Handle report generation
    }
  } catch (error) {
    console.error('❌ Failed to generate report:', error)
  } finally {
    isGeneratingReport.value = false
  }
}

const generateQuickReport = (reportType: string): void => {
  console.log('Generating quick report:', reportType)
  // Implement quick report generation
}

const getKPIChartData = (kpiId: string): number[] => {
  return kpiChartData.value[kpiId] || []
}

const getAlertIcon = (alertType: string): string => {
  const iconMap = {
    maintenance: 'wrench',
    inventory: 'package',
    quality: 'star',
    revenue: 'dollar-sign'
  }
  return iconMap[alertType as keyof typeof iconMap] || 'alert-triangle'
}

const getAlertColor = (severity: string): string => {
  const colorMap = {
    critical: 'var(--color-error)',
    high: 'var(--color-warning)',
    medium: 'var(--color-info)',
    low: 'var(--color-text-secondary)'
  }
  return colorMap[severity as keyof typeof colorMap] || 'var(--color-text-secondary)'
}

const formatDate = (date: Date): string => {
  const d = new Date(date)
  if (props.preferArabic) {
    return d.toLocaleDateString('ar-SA', { 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }
  return d.toLocaleDateString('en-US', { 
    month: 'short', 
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat(props.preferArabic ? 'ar-SA' : 'en-OM', {
    style: 'currency',
    currency: 'OMR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 2
  }).format(amount)
}

const renderMainChart = (): void => {
  if (!mainChart.value) return
  
  const canvas = mainChart.value
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  
  // Clear canvas
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  
  // Simple chart rendering based on active chart type
  ctx.fillStyle = 'var(--color-primary)'
  ctx.fillRect(50, 50, 100, 200)
  
  ctx.fillStyle = 'var(--color-success)'
  ctx.fillRect(200, 100, 100, 150)
  
  ctx.fillStyle = 'var(--color-warning)'
  ctx.fillRect(350, 75, 100, 175)
}

// Auto-refresh setup
let refreshTimer: NodeJS.Timeout | null = null

const setupAutoRefresh = (): void => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
  
  if (props.autoRefresh) {
    refreshTimer = setInterval(() => {
      refreshKPIs()
    }, refreshInterval.value)
  }
}

// Watchers
watch(() => refreshInterval.value, setupAutoRefresh)
watch(() => props.autoRefresh, setupAutoRefresh)

// Lifecycle
onMounted(async () => {
  await initializeAnalytics()
  setupAutoRefresh()
  
  nextTick(() => {
    if (mainChart.value) {
      renderMainChart()
    }
  })
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
  
  if (analyticsEngine.value) {
    analyticsEngine.value.destroy()
  }
})
</script>

<style lang="scss" scoped>
.analytics-dashboard {
  --dashboard-padding: var(--spacing-6);
  --section-spacing: var(--spacing-8);
  
  padding: var(--dashboard-padding);
  min-height: 100vh;
  background: var(--color-background);
  
  &--rtl {
    direction: rtl;
    text-align: right;
  }
}

.analytics-dashboard__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--section-spacing);
}

.analytics-dashboard__title-section {
  flex: 1;
}

.analytics-dashboard__title {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin: 0 0 var(--spacing-2) 0;
}

.analytics-dashboard__subtitle {
  font-size: var(--font-size-lg);
  color: var(--color-text-secondary);
  margin: 0;
}

.analytics-dashboard__controls {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
}

.analytics-dashboard__time-range {
  min-width: 200px;
}

.analytics-dashboard__connection-warning {
  margin-bottom: var(--section-spacing);
}

.analytics-dashboard__kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--spacing-4);
  margin-bottom: var(--section-spacing);
}

.analytics-dashboard__section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-4);
}

.analytics-dashboard__section-title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0;
}

.analytics-dashboard__chart-controls {
  display: flex;
  gap: var(--spacing-2);
}

.analytics-dashboard__charts-section {
  margin-bottom: var(--section-spacing);
}

.analytics-dashboard__chart-container {
  background: var(--color-background-elevated);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--spacing-4);
}

.analytics-dashboard__main-chart {
  width: 100%;
  height: 400px;
  display: block;
}

.analytics-dashboard__alerts-section {
  margin-bottom: var(--section-spacing);
}

.analytics-dashboard__alerts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: var(--spacing-4);
}

.analytics-dashboard__alert-card {
  background: var(--color-background-elevated);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--spacing-4);
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    box-shadow: var(--shadow-md);
    transform: translateY(-1px);
  }
  
  &--critical {
    border-left: 4px solid var(--color-error);
  }
  
  &--high {
    border-left: 4px solid var(--color-warning);
  }
  
  &--medium {
    border-left: 4px solid var(--color-info);
  }
  
  &--low {
    border-left: 4px solid var(--color-text-tertiary);
  }
}

.analytics-dashboard__alert-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  margin-bottom: var(--spacing-3);
}

.analytics-dashboard__alert-title {
  flex: 1;
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.analytics-dashboard__alert-confidence {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  background: var(--color-background-subtle);
  padding: var(--spacing-1) var(--spacing-2);
  border-radius: var(--radius-sm);
}

.analytics-dashboard__alert-description {
  color: var(--color-text-secondary);
  margin: 0 0 var(--spacing-3) 0;
  line-height: var(--line-height-relaxed);
}

.analytics-dashboard__alert-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: var(--font-size-sm);
  color: var(--color-text-tertiary);
}

.analytics-dashboard__reports-section {
  margin-bottom: var(--section-spacing);
}

.analytics-dashboard__reports-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--spacing-4);
}

.analytics-dashboard__report-card {
  background: var(--color-background-elevated);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--spacing-4);
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
  }
}

.analytics-dashboard__report-title {
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: var(--spacing-2) 0;
}

.analytics-dashboard__report-description {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.analytics-dashboard__settings {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-6);
}

.analytics-dashboard__setting-group {
  h3 {
    margin: 0 0 var(--spacing-3) 0;
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-semibold);
    color: var(--color-text-primary);
  }
  
  > * + * {
    margin-top: var(--spacing-3);
  }
}

// Responsive design
@media (max-width: 1024px) {
  .analytics-dashboard__kpi-grid {
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  }
  
  .analytics-dashboard__alerts-grid,
  .analytics-dashboard__reports-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .analytics-dashboard {
    --dashboard-padding: var(--spacing-4);
  }
  
  .analytics-dashboard__header {
    flex-direction: column;
    align-items: stretch;
    gap: var(--spacing-4);
  }
  
  .analytics-dashboard__controls {
    flex-wrap: wrap;
  }
  
  .analytics-dashboard__chart-controls {
    flex-wrap: wrap;
  }
}
</style>