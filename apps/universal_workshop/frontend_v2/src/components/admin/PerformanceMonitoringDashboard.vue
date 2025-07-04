<!--
  Performance Monitoring Dashboard - Universal Workshop Frontend V2
  Comprehensive performance monitoring with real-time metrics,
  Arabic interface, and advanced analytics for system optimization.
-->
<template>
  <div :class="dashboardClasses" :dir="isRTL ? 'rtl' : 'ltr'">
    <!-- Dashboard Header -->
    <div class="dashboard-header">
      <div class="header-info">
        <h1>{{ preferArabic ? 'مراقبة الأداء' : 'Performance Monitoring' }}</h1>
        <p class="last-updated">
          {{ preferArabic ? 'آخر تحديث:' : 'Last updated:' }}
          {{ formatDateTime(lastUpdated) }}
        </p>
      </div>
      
      <div class="header-controls">
        <div class="time-range-selector">
          <Button
            v-for="range in timeRanges"
            :key="range.value"
            :variant="selectedTimeRange === range.value ? 'primary' : 'outline'"
            size="sm"
            @click="setTimeRange(range.value)"
          >
            {{ preferArabic ? range.labelAr : range.label }}
          </Button>
        </div>
        
        <Button
          variant="outline"
          size="sm"
          @click="refreshMetrics"
          :disabled="isRefreshing"
        >
          <Icon name="refresh-cw" :class="{ 'animate-spin': isRefreshing }" />
          {{ preferArabic ? 'تحديث' : 'Refresh' }}
        </Button>
        
        <Button
          variant="outline"
          size="sm"
          @click="exportReport"
        >
          <Icon name="download" />
          {{ preferArabic ? 'تصدير التقرير' : 'Export Report' }}
        </Button>
      </div>
    </div>

    <!-- Overall Health Status -->
    <div class="health-status-section">
      <div class="health-cards">
        <div class="health-card" :class="getHealthStatusClass(overallHealth.status)">
          <div class="health-icon">
            <Icon :name="getHealthStatusIcon(overallHealth.status)" />
          </div>
          <div class="health-info">
            <h3>{{ preferArabic ? 'الحالة العامة' : 'Overall Health' }}</h3>
            <p class="health-score">{{ overallHealth.score }}/100</p>
            <p class="health-description">
              {{ preferArabic ? overallHealth.descriptionAr : overallHealth.description }}
            </p>
          </div>
        </div>

        <div class="health-card performance">
          <div class="health-icon">
            <Icon name="zap" />
          </div>
          <div class="health-info">
            <h3>{{ preferArabic ? 'الأداء' : 'Performance' }}</h3>
            <p class="metric-value">{{ performanceMetrics.responseTime }}ms</p>
            <p class="metric-change" :class="getChangeClass(performanceMetrics.responseTimeChange)">
              <Icon :name="getChangeIcon(performanceMetrics.responseTimeChange)" />
              {{ Math.abs(performanceMetrics.responseTimeChange) }}%
            </p>
          </div>
        </div>

        <div class="health-card availability">
          <div class="health-icon">
            <Icon name="shield-check" />
          </div>
          <div class="health-info">
            <h3>{{ preferArabic ? 'التوفر' : 'Availability' }}</h3>
            <p class="metric-value">{{ performanceMetrics.uptime }}%</p>
            <p class="metric-detail">
              {{ formatUptime(performanceMetrics.uptimeSeconds) }}
            </p>
          </div>
        </div>

        <div class="health-card errors">
          <div class="health-icon">
            <Icon name="alert-triangle" />
          </div>
          <div class="health-info">
            <h3>{{ preferArabic ? 'الأخطاء' : 'Errors' }}</h3>
            <p class="metric-value">{{ performanceMetrics.errorRate }}%</p>
            <p class="metric-detail">
              {{ performanceMetrics.totalErrors }} {{ preferArabic ? 'خطأ' : 'errors' }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Performance Charts -->
    <div class="charts-section">
      <div class="charts-grid">
        <!-- Response Time Chart -->
        <div class="chart-container">
          <div class="chart-header">
            <h3>{{ preferArabic ? 'زمن الاستجابة' : 'Response Time' }}</h3>
            <div class="chart-controls">
              <Button
                variant="ghost"
                size="xs"
                @click="toggleChartType('responseTime')"
              >
                <Icon :name="responseTimeChart.type === 'line' ? 'bar-chart' : 'line-chart'" />
              </Button>
            </div>
          </div>
          <div class="chart-content">
            <canvas ref="responseTimeChartRef" class="performance-chart"></canvas>
          </div>
        </div>

        <!-- Throughput Chart -->
        <div class="chart-container">
          <div class="chart-header">
            <h3>{{ preferArabic ? 'معدل الإنتاجية' : 'Throughput' }}</h3>
            <div class="chart-legend">
              <span class="legend-item requests">
                <span class="legend-color"></span>
                {{ preferArabic ? 'الطلبات' : 'Requests' }}
              </span>
              <span class="legend-item transactions">
                <span class="legend-color"></span>
                {{ preferArabic ? 'المعاملات' : 'Transactions' }}
              </span>
            </div>
          </div>
          <div class="chart-content">
            <canvas ref="throughputChartRef" class="performance-chart"></canvas>
          </div>
        </div>

        <!-- Error Rate Chart -->
        <div class="chart-container">
          <div class="chart-header">
            <h3>{{ preferArabic ? 'معدل الأخطاء' : 'Error Rate' }}</h3>
            <div class="chart-stats">
              <span class="stat-item">
                {{ preferArabic ? 'المتوسط:' : 'Avg:' }} {{ errorMetrics.average }}%
              </span>
              <span class="stat-item">
                {{ preferArabic ? 'الذروة:' : 'Peak:' }} {{ errorMetrics.peak }}%
              </span>
            </div>
          </div>
          <div class="chart-content">
            <canvas ref="errorRateChartRef" class="performance-chart"></canvas>
          </div>
        </div>

        <!-- Resource Usage Chart -->
        <div class="chart-container">
          <div class="chart-header">
            <h3>{{ preferArabic ? 'استخدام الموارد' : 'Resource Usage' }}</h3>
          </div>
          <div class="chart-content">
            <div class="resource-metrics">
              <div class="resource-item">
                <div class="resource-header">
                  <span>{{ preferArabic ? 'المعالج' : 'CPU' }}</span>
                  <span class="resource-value">{{ resourceUsage.cpu }}%</span>
                </div>
                <div class="resource-bar">
                  <div 
                    class="resource-fill cpu" 
                    :style="{ width: `${resourceUsage.cpu}%` }"
                  ></div>
                </div>
              </div>

              <div class="resource-item">
                <div class="resource-header">
                  <span>{{ preferArabic ? 'الذاكرة' : 'Memory' }}</span>
                  <span class="resource-value">{{ resourceUsage.memory }}%</span>
                </div>
                <div class="resource-bar">
                  <div 
                    class="resource-fill memory" 
                    :style="{ width: `${resourceUsage.memory}%` }"
                  ></div>
                </div>
              </div>

              <div class="resource-item">
                <div class="resource-header">
                  <span>{{ preferArabic ? 'التخزين' : 'Storage' }}</span>
                  <span class="resource-value">{{ resourceUsage.storage }}%</span>
                </div>
                <div class="resource-bar">
                  <div 
                    class="resource-fill storage" 
                    :style="{ width: `${resourceUsage.storage}%` }"
                  ></div>
                </div>
              </div>

              <div class="resource-item">
                <div class="resource-header">
                  <span>{{ preferArabic ? 'الشبكة' : 'Network' }}</span>
                  <span class="resource-value">{{ resourceUsage.network }}%</span>
                </div>
                <div class="resource-bar">
                  <div 
                    class="resource-fill network" 
                    :style="{ width: `${resourceUsage.network}%` }"
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Detailed Metrics Tables -->
    <div class="metrics-section">
      <div class="metrics-tabs">
        <Button
          v-for="tab in metricsTabs"
          :key="tab.id"
          :variant="activeMetricsTab === tab.id ? 'primary' : 'ghost'"
          @click="setActiveMetricsTab(tab.id)"
        >
          {{ preferArabic ? tab.labelAr : tab.label }}
        </Button>
      </div>

      <!-- API Endpoints Performance -->
      <div v-if="activeMetricsTab === 'endpoints'" class="metrics-content">
        <div class="table-container">
          <table class="metrics-table">
            <thead>
              <tr>
                <th>{{ preferArabic ? 'النقطة النهائية' : 'Endpoint' }}</th>
                <th>{{ preferArabic ? 'الطلبات' : 'Requests' }}</th>
                <th>{{ preferArabic ? 'متوسط الوقت' : 'Avg Time' }}</th>
                <th>{{ preferArabic ? 'معدل الأخطاء' : 'Error Rate' }}</th>
                <th>{{ preferArabic ? 'الحالة' : 'Status' }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="endpoint in endpointMetrics"
                :key="endpoint.path"
                :class="getEndpointStatusClass(endpoint.status)"
              >
                <td class="endpoint-path">{{ endpoint.path }}</td>
                <td class="requests-count">{{ formatNumber(endpoint.requests) }}</td>
                <td class="response-time">{{ endpoint.avgResponseTime }}ms</td>
                <td class="error-rate">
                  <span :class="getErrorRateClass(endpoint.errorRate)">
                    {{ endpoint.errorRate }}%
                  </span>
                </td>
                <td class="status">
                  <span class="status-badge" :class="endpoint.status">
                    {{ getStatusText(endpoint.status) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Database Performance -->
      <div v-if="activeMetricsTab === 'database'" class="metrics-content">
        <div class="db-metrics-grid">
          <div class="db-metric-card">
            <h4>{{ preferArabic ? 'الاستعلامات' : 'Queries' }}</h4>
            <div class="metric-value large">{{ formatNumber(databaseMetrics.totalQueries) }}</div>
            <div class="metric-detail">
              {{ databaseMetrics.avgQueryTime }}ms {{ preferArabic ? 'متوسط' : 'avg' }}
            </div>
          </div>

          <div class="db-metric-card">
            <h4>{{ preferArabic ? 'الاتصالات' : 'Connections' }}</h4>
            <div class="metric-value large">{{ databaseMetrics.activeConnections }}</div>
            <div class="metric-detail">
              {{ databaseMetrics.maxConnections }} {{ preferArabic ? 'حد أقصى' : 'max' }}
            </div>
          </div>

          <div class="db-metric-card">
            <h4>{{ preferArabic ? 'حجم قاعدة البيانات' : 'Database Size' }}</h4>
            <div class="metric-value large">{{ formatBytes(databaseMetrics.size) }}</div>
            <div class="metric-detail">
              +{{ formatBytes(databaseMetrics.growthRate) }}/{{ preferArabic ? 'يوم' : 'day' }}
            </div>
          </div>

          <div class="db-metric-card">
            <h4>{{ preferArabic ? 'معدل الإصابة' : 'Cache Hit Rate' }}</h4>
            <div class="metric-value large">{{ databaseMetrics.cacheHitRate }}%</div>
            <div class="metric-detail" :class="getCacheHitRateClass(databaseMetrics.cacheHitRate)">
              {{ getCacheHitRateText(databaseMetrics.cacheHitRate) }}
            </div>
          </div>
        </div>

        <!-- Slow Queries Table -->
        <div class="slow-queries-section">
          <h4>{{ preferArabic ? 'الاستعلامات البطيئة' : 'Slow Queries' }}</h4>
          <div class="table-container">
            <table class="metrics-table">
              <thead>
                <tr>
                  <th>{{ preferArabic ? 'الاستعلام' : 'Query' }}</th>
                  <th>{{ preferArabic ? 'الوقت' : 'Duration' }}</th>
                  <th>{{ preferArabic ? 'التكرار' : 'Frequency' }}</th>
                  <th>{{ preferArabic ? 'آخر تنفيذ' : 'Last Executed' }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="query in slowQueries" :key="query.id">
                  <td class="query-text">
                    <code>{{ truncateQuery(query.sql) }}</code>
                  </td>
                  <td class="duration">{{ query.duration }}ms</td>
                  <td class="frequency">{{ query.frequency }}</td>
                  <td class="timestamp">{{ formatDateTime(query.lastExecuted) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- User Experience Metrics -->
      <div v-if="activeMetricsTab === 'ux'" class="metrics-content">
        <div class="ux-metrics-grid">
          <div class="ux-metric-card">
            <div class="metric-icon">
              <Icon name="eye" />
            </div>
            <div class="metric-info">
              <h4>{{ preferArabic ? 'المستخدمون النشطون' : 'Active Users' }}</h4>
              <div class="metric-value">{{ formatNumber(uxMetrics.activeUsers) }}</div>
              <div class="metric-trend" :class="getChangeClass(uxMetrics.userGrowth)">
                <Icon :name="getChangeIcon(uxMetrics.userGrowth)" />
                {{ Math.abs(uxMetrics.userGrowth) }}%
              </div>
            </div>
          </div>

          <div class="ux-metric-card">
            <div class="metric-icon">
              <Icon name="clock" />
            </div>
            <div class="metric-info">
              <h4>{{ preferArabic ? 'متوسط مدة الجلسة' : 'Avg Session Duration' }}</h4>
              <div class="metric-value">{{ formatDuration(uxMetrics.avgSessionDuration) }}</div>
              <div class="metric-detail">
                {{ uxMetrics.totalSessions }} {{ preferArabic ? 'جلسة' : 'sessions' }}
              </div>
            </div>
          </div>

          <div class="ux-metric-card">
            <div class="metric-icon">
              <Icon name="mouse-pointer" />
            </div>
            <div class="metric-info">
              <h4>{{ preferArabic ? 'معدل النقر' : 'Click Rate' }}</h4>
              <div class="metric-value">{{ uxMetrics.clickThroughRate }}%</div>
              <div class="metric-detail">
                {{ formatNumber(uxMetrics.totalClicks) }} {{ preferArabic ? 'نقرة' : 'clicks' }}
              </div>
            </div>
          </div>

          <div class="ux-metric-card">
            <div class="metric-icon">
              <Icon name="trending-up" />
            </div>
            <div class="metric-info">
              <h4>{{ preferArabic ? 'معدل التحويل' : 'Conversion Rate' }}</h4>
              <div class="metric-value">{{ uxMetrics.conversionRate }}%</div>
              <div class="metric-trend" :class="getChangeClass(uxMetrics.conversionChange)">
                <Icon :name="getChangeIcon(uxMetrics.conversionChange)" />
                {{ Math.abs(uxMetrics.conversionChange) }}%
              </div>
            </div>
          </div>
        </div>

        <!-- Page Performance -->
        <div class="page-performance-section">
          <h4>{{ preferArabic ? 'أداء الصفحات' : 'Page Performance' }}</h4>
          <div class="table-container">
            <table class="metrics-table">
              <thead>
                <tr>
                  <th>{{ preferArabic ? 'الصفحة' : 'Page' }}</th>
                  <th>{{ preferArabic ? 'وقت التحميل' : 'Load Time' }}</th>
                  <th>{{ preferArabic ? 'الزيارات' : 'Views' }}</th>
                  <th>{{ preferArabic ? 'معدل الارتداد' : 'Bounce Rate' }}</th>
                  <th>{{ preferArabic ? 'النقاط' : 'Score' }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="page in pageMetrics" :key="page.path">
                  <td class="page-path">{{ page.path }}</td>
                  <td class="load-time">{{ page.loadTime }}ms</td>
                  <td class="page-views">{{ formatNumber(page.views) }}</td>
                  <td class="bounce-rate">
                    <span :class="getBounceRateClass(page.bounceRate)">
                      {{ page.bounceRate }}%
                    </span>
                  </td>
                  <td class="performance-score">
                    <div class="score-circle" :class="getScoreClass(page.score)">
                      {{ page.score }}
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- Alerts and Recommendations -->
    <div class="alerts-section" v-if="alerts.length > 0 || recommendations.length > 0">
      <div class="alerts-container" v-if="alerts.length > 0">
        <h3>{{ preferArabic ? 'التنبيهات' : 'Alerts' }}</h3>
        <div class="alerts-list">
          <div
            v-for="alert in alerts"
            :key="alert.id"
            class="alert-item"
            :class="alert.severity"
          >
            <div class="alert-icon">
              <Icon :name="getAlertIcon(alert.severity)" />
            </div>
            <div class="alert-content">
              <h4>{{ preferArabic ? alert.titleAr : alert.title }}</h4>
              <p>{{ preferArabic ? alert.messageAr : alert.message }}</p>
              <span class="alert-time">{{ formatDateTime(alert.timestamp) }}</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              @click="dismissAlert(alert.id)"
            >
              <Icon name="x" />
            </Button>
          </div>
        </div>
      </div>

      <div class="recommendations-container" v-if="recommendations.length > 0">
        <h3>{{ preferArabic ? 'التوصيات' : 'Recommendations' }}</h3>
        <div class="recommendations-list">
          <div
            v-for="recommendation in recommendations"
            :key="recommendation.id"
            class="recommendation-item"
          >
            <div class="recommendation-icon">
              <Icon name="lightbulb" />
            </div>
            <div class="recommendation-content">
              <h4>{{ preferArabic ? recommendation.titleAr : recommendation.title }}</h4>
              <p>{{ preferArabic ? recommendation.descriptionAr : recommendation.description }}</p>
              <div class="recommendation-impact">
                {{ preferArabic ? 'التأثير المتوقع:' : 'Expected impact:' }}
                <span class="impact-value">{{ recommendation.expectedImprovement }}%</span>
              </div>
            </div>
            <div class="recommendation-actions">
              <Button
                variant="primary"
                size="sm"
                @click="implementRecommendation(recommendation.id)"
              >
                {{ preferArabic ? 'تطبيق' : 'Apply' }}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                @click="dismissRecommendation(recommendation.id)"
              >
                {{ preferArabic ? 'تجاهل' : 'Dismiss' }}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { storeToRefs } from 'pinia'

// Stores
import { usePerformanceStore } from '@/stores/performance'
import { useLocalizationStore } from '@/stores/localization'
import { useNotificationStore } from '@/stores/notification'

// Composables
import { useRealTimeUpdates } from '@/composables/useRealTimeUpdates'
import { useChartRenderer } from '@/composables/useChartRenderer'

// Components
import { Button, Icon } from '@/components/ui'

// Types
interface PerformanceMonitoringDashboardProps {
  autoRefresh?: boolean
  refreshInterval?: number
}

// Props
const props = withDefaults(defineProps<PerformanceMonitoringDashboardProps>(), {
  autoRefresh: true,
  refreshInterval: 30000 // 30 seconds
})

// Stores
const performanceStore = usePerformanceStore()
const localizationStore = useLocalizationStore()
const notificationStore = useNotificationStore()

// Store refs
const { 
  overallHealth, 
  performanceMetrics, 
  resourceUsage,
  endpointMetrics,
  databaseMetrics,
  uxMetrics,
  alerts,
  recommendations
} = storeToRefs(performanceStore)
const { preferArabic, isRTL } = storeToRefs(localizationStore)

// Composables
const realTimeUpdates = useRealTimeUpdates()
const chartRenderer = useChartRenderer()

// Reactive state
const lastUpdated = ref(new Date())
const isRefreshing = ref(false)
const selectedTimeRange = ref('1h')
const activeMetricsTab = ref('endpoints')

// Chart refs
const responseTimeChartRef = ref<HTMLCanvasElement>()
const throughputChartRef = ref<HTMLCanvasElement>()
const errorRateChartRef = ref<HTMLCanvasElement>()

// Chart configurations
const responseTimeChart = ref({ type: 'line' })
const errorMetrics = ref({ average: 2.1, peak: 8.5 })
const slowQueries = ref([])
const pageMetrics = ref([])

// Auto refresh interval
let refreshInterval: NodeJS.Timeout | null = null

// Computed properties
const dashboardClasses = computed(() => [
  'performance-monitoring-dashboard',
  {
    'rtl': isRTL.value
  }
])

const timeRanges = computed(() => [
  { value: '1h', label: '1 Hour', labelAr: 'ساعة واحدة' },
  { value: '24h', label: '24 Hours', labelAr: '24 ساعة' },
  { value: '7d', label: '7 Days', labelAr: '7 أيام' },
  { value: '30d', label: '30 Days', labelAr: '30 يوم' }
])

const metricsTabs = computed(() => [
  { id: 'endpoints', label: 'API Endpoints', labelAr: 'نقاط API' },
  { id: 'database', label: 'Database', labelAr: 'قاعدة البيانات' },
  { id: 'ux', label: 'User Experience', labelAr: 'تجربة المستخدم' }
])

// Methods
const refreshMetrics = async () => {
  if (isRefreshing.value) return
  
  try {
    isRefreshing.value = true
    await performanceStore.refreshAllMetrics()
    lastUpdated.value = new Date()
    
    // Update charts
    await nextTick()
    updateCharts()
  } catch (error) {
    console.error('Failed to refresh metrics:', error)
    notificationStore.showError(
      preferArabic.value
        ? 'فشل في تحديث المقاييس'
        : 'Failed to refresh metrics'
    )
  } finally {
    isRefreshing.value = false
  }
}

const setTimeRange = (range: string) => {
  selectedTimeRange.value = range
  performanceStore.setTimeRange(range)
  updateCharts()
}

const setActiveMetricsTab = (tabId: string) => {
  activeMetricsTab.value = tabId
}

const updateCharts = async () => {
  await nextTick()
  
  if (responseTimeChartRef.value) {
    chartRenderer.renderResponseTimeChart(
      responseTimeChartRef.value,
      performanceMetrics.value.responseTimeHistory,
      { type: responseTimeChart.value.type }
    )
  }
  
  if (throughputChartRef.value) {
    chartRenderer.renderThroughputChart(
      throughputChartRef.value,
      performanceMetrics.value.throughputHistory
    )
  }
  
  if (errorRateChartRef.value) {
    chartRenderer.renderErrorRateChart(
      errorRateChartRef.value,
      performanceMetrics.value.errorHistory
    )
  }
}

const toggleChartType = (chartName: string) => {
  if (chartName === 'responseTime') {
    responseTimeChart.value.type = responseTimeChart.value.type === 'line' ? 'bar' : 'line'
    updateCharts()
  }
}

const exportReport = async () => {
  try {
    const report = await performanceStore.generateReport(selectedTimeRange.value)
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    
    const a = document.createElement('a')
    a.href = url
    a.download = `performance-report-${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Failed to export report:', error)
    notificationStore.showError(
      preferArabic.value
        ? 'فشل في تصدير التقرير'
        : 'Failed to export report'
    )
  }
}

const dismissAlert = (alertId: string) => {
  performanceStore.dismissAlert(alertId)
}

const dismissRecommendation = (recommendationId: string) => {
  performanceStore.dismissRecommendation(recommendationId)
}

const implementRecommendation = async (recommendationId: string) => {
  try {
    await performanceStore.implementRecommendation(recommendationId)
    notificationStore.showSuccess(
      preferArabic.value
        ? 'تم تطبيق التوصية بنجاح'
        : 'Recommendation applied successfully'
    )
  } catch (error) {
    console.error('Failed to implement recommendation:', error)
    notificationStore.showError(
      preferArabic.value
        ? 'فشل في تطبيق التوصية'
        : 'Failed to implement recommendation'
    )
  }
}

// Utility methods
const getHealthStatusClass = (status: string) => ({
  'excellent': status === 'excellent',
  'good': status === 'good',
  'warning': status === 'warning',
  'critical': status === 'critical'
})

const getHealthStatusIcon = (status: string) => {
  const icons = {
    excellent: 'check-circle',
    good: 'thumbs-up',
    warning: 'alert-triangle',
    critical: 'x-circle'
  }
  return icons[status as keyof typeof icons] || 'help-circle'
}

const getChangeClass = (change: number) => ({
  'positive': change > 0,
  'negative': change < 0,
  'neutral': change === 0
})

const getChangeIcon = (change: number) => {
  if (change > 0) return 'trending-up'
  if (change < 0) return 'trending-down'
  return 'minus'
}

const formatDateTime = (date: Date) => {
  return date.toLocaleString(preferArabic.value ? 'ar-SA' : 'en-US')
}

const formatUptime = (seconds: number) => {
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  
  if (preferArabic.value) {
    return `${days} يوم ${hours} ساعة ${minutes} دقيقة`
  } else {
    return `${days}d ${hours}h ${minutes}m`
  }
}

const formatNumber = (num: number) => {
  return new Intl.NumberFormat(preferArabic.value ? 'ar-SA' : 'en-US').format(num)
}

const formatBytes = (bytes: number) => {
  const sizes = preferArabic.value 
    ? ['بايت', 'كيلوبايت', 'ميجابايت', 'جيجابايت']
    : ['B', 'KB', 'MB', 'GB']
  
  if (bytes === 0) return '0 ' + sizes[0]
  
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
}

const formatDuration = (seconds: number) => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  
  if (preferArabic.value) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  } else {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
}

// Lifecycle hooks
onMounted(async () => {
  await refreshMetrics()
  
  if (props.autoRefresh) {
    refreshInterval = setInterval(refreshMetrics, props.refreshInterval)
  }
  
  // Subscribe to real-time updates
  realTimeUpdates.subscribeToPerformanceUpdates()
  
  // Initialize charts
  await nextTick()
  updateCharts()
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
  
  realTimeUpdates.unsubscribeFromPerformanceUpdates()
})
</script>

<style scoped>
.performance-monitoring-dashboard {
  @apply min-h-screen bg-gray-50 p-6;
  font-family: 'Noto Sans Arabic', 'Roboto', sans-serif;
}

.performance-monitoring-dashboard.rtl {
  direction: rtl;
}

/* Dashboard Header */
.dashboard-header {
  @apply flex justify-between items-center mb-8;
}

.header-info h1 {
  @apply text-3xl font-bold text-gray-900 mb-2;
}

.last-updated {
  @apply text-sm text-gray-600;
}

.header-controls {
  @apply flex items-center space-x-4;
}

.header-controls.rtl {
  @apply space-x-reverse;
}

.time-range-selector {
  @apply flex space-x-2;
}

.time-range-selector.rtl {
  @apply space-x-reverse;
}

/* Health Status Section */
.health-status-section {
  @apply mb-8;
}

.health-cards {
  @apply grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6;
}

.health-card {
  @apply bg-white rounded-xl shadow-sm border border-gray-200 p-6 flex items-center space-x-4;
}

.health-card.rtl {
  @apply space-x-reverse;
}

.health-card.excellent {
  @apply border-green-300 bg-green-50;
}

.health-card.good {
  @apply border-blue-300 bg-blue-50;
}

.health-card.warning {
  @apply border-yellow-300 bg-yellow-50;
}

.health-card.critical {
  @apply border-red-300 bg-red-50;
}

.health-icon {
  @apply w-12 h-12 rounded-full flex items-center justify-center;
}

.health-card.excellent .health-icon {
  @apply bg-green-100 text-green-600;
}

.health-card.good .health-icon {
  @apply bg-blue-100 text-blue-600;
}

.health-card.warning .health-icon {
  @apply bg-yellow-100 text-yellow-600;
}

.health-card.critical .health-icon {
  @apply bg-red-100 text-red-600;
}

.health-info h3 {
  @apply font-semibold text-gray-900 mb-1;
}

.health-score {
  @apply text-2xl font-bold text-gray-900;
}

.health-description {
  @apply text-sm text-gray-600;
}

.metric-value {
  @apply text-2xl font-bold text-gray-900;
}

.metric-change {
  @apply flex items-center space-x-1 text-sm;
}

.metric-change.rtl {
  @apply space-x-reverse;
}

.metric-change.positive {
  @apply text-green-600;
}

.metric-change.negative {
  @apply text-red-600;
}

.metric-detail {
  @apply text-sm text-gray-600;
}

/* Charts Section */
.charts-section {
  @apply mb-8;
}

.charts-grid {
  @apply grid grid-cols-1 lg:grid-cols-2 gap-6;
}

.chart-container {
  @apply bg-white rounded-xl shadow-sm border border-gray-200 p-6;
}

.chart-header {
  @apply flex justify-between items-center mb-4;
}

.chart-header h3 {
  @apply font-semibold text-gray-900;
}

.chart-controls {
  @apply flex space-x-2;
}

.chart-controls.rtl {
  @apply space-x-reverse;
}

.chart-legend {
  @apply flex space-x-4;
}

.chart-legend.rtl {
  @apply space-x-reverse;
}

.legend-item {
  @apply flex items-center space-x-2 text-sm;
}

.legend-item.rtl {
  @apply space-x-reverse;
}

.legend-color {
  @apply w-3 h-3 rounded-full;
}

.legend-item.requests .legend-color {
  @apply bg-blue-500;
}

.legend-item.transactions .legend-color {
  @apply bg-green-500;
}

.chart-stats {
  @apply flex space-x-4 text-sm text-gray-600;
}

.chart-stats.rtl {
  @apply space-x-reverse;
}

.performance-chart {
  @apply w-full h-64;
}

/* Resource Usage */
.resource-metrics {
  @apply space-y-4;
}

.resource-item {
  @apply space-y-2;
}

.resource-header {
  @apply flex justify-between items-center;
}

.resource-value {
  @apply font-mono font-bold;
}

.resource-bar {
  @apply w-full bg-gray-200 rounded-full h-3;
}

.resource-fill {
  @apply h-full rounded-full transition-all duration-500;
}

.resource-fill.cpu {
  @apply bg-blue-500;
}

.resource-fill.memory {
  @apply bg-green-500;
}

.resource-fill.storage {
  @apply bg-yellow-500;
}

.resource-fill.network {
  @apply bg-purple-500;
}

/* Metrics Section */
.metrics-section {
  @apply mb-8;
}

.metrics-tabs {
  @apply flex space-x-2 mb-6;
}

.metrics-tabs.rtl {
  @apply space-x-reverse;
}

.table-container {
  @apply bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden;
}

.metrics-table {
  @apply w-full;
}

.metrics-table th {
  @apply bg-gray-50 px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider;
}

.metrics-table.rtl th {
  @apply text-right;
}

.metrics-table td {
  @apply px-6 py-4 whitespace-nowrap text-sm text-gray-900;
}

.endpoint-path {
  @apply font-mono text-xs;
}

.status-badge {
  @apply px-2 py-1 rounded-full text-xs font-medium;
}

.status-badge.healthy {
  @apply bg-green-100 text-green-800;
}

.status-badge.warning {
  @apply bg-yellow-100 text-yellow-800;
}

.status-badge.critical {
  @apply bg-red-100 text-red-800;
}

/* Database Metrics */
.db-metrics-grid {
  @apply grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6;
}

.db-metric-card {
  @apply bg-gray-50 rounded-lg p-4;
}

.db-metric-card h4 {
  @apply font-medium text-gray-700 mb-2;
}

.metric-value.large {
  @apply text-3xl font-bold text-gray-900;
}

/* UX Metrics */
.ux-metrics-grid {
  @apply grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6;
}

.ux-metric-card {
  @apply bg-white rounded-lg shadow-sm border border-gray-200 p-6 flex items-center space-x-4;
}

.ux-metric-card.rtl {
  @apply space-x-reverse;
}

.metric-icon {
  @apply w-12 h-12 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center;
}

.metric-trend {
  @apply flex items-center space-x-1 text-sm;
}

.metric-trend.rtl {
  @apply space-x-reverse;
}

/* Alerts and Recommendations */
.alerts-section {
  @apply grid grid-cols-1 lg:grid-cols-2 gap-8;
}

.alerts-container h3,
.recommendations-container h3 {
  @apply text-xl font-bold text-gray-900 mb-4;
}

.alerts-list,
.recommendations-list {
  @apply space-y-4;
}

.alert-item {
  @apply bg-white rounded-lg shadow-sm border-l-4 p-4 flex items-start space-x-4;
}

.alert-item.rtl {
  @apply border-r-4 border-l-0 space-x-reverse;
}

.alert-item.critical {
  @apply border-red-500;
}

.alert-item.warning {
  @apply border-yellow-500;
}

.alert-item.info {
  @apply border-blue-500;
}

.alert-icon {
  @apply w-8 h-8 rounded-full flex items-center justify-center;
}

.alert-item.critical .alert-icon {
  @apply bg-red-100 text-red-600;
}

.alert-item.warning .alert-icon {
  @apply bg-yellow-100 text-yellow-600;
}

.alert-item.info .alert-icon {
  @apply bg-blue-100 text-blue-600;
}

.alert-content {
  @apply flex-1;
}

.alert-content h4 {
  @apply font-semibold text-gray-900 mb-1;
}

.alert-content p {
  @apply text-gray-700 mb-2;
}

.alert-time {
  @apply text-xs text-gray-500;
}

.recommendation-item {
  @apply bg-white rounded-lg shadow-sm border border-gray-200 p-4 flex items-start space-x-4;
}

.recommendation-item.rtl {
  @apply space-x-reverse;
}

.recommendation-icon {
  @apply w-8 h-8 bg-yellow-100 text-yellow-600 rounded-full flex items-center justify-center;
}

.recommendation-content {
  @apply flex-1;
}

.recommendation-content h4 {
  @apply font-semibold text-gray-900 mb-1;
}

.recommendation-content p {
  @apply text-gray-700 mb-2;
}

.recommendation-impact {
  @apply text-sm text-gray-600;
}

.impact-value {
  @apply font-semibold text-green-600;
}

.recommendation-actions {
  @apply flex space-x-2;
}

.recommendation-actions.rtl {
  @apply space-x-reverse;
}
</style> 