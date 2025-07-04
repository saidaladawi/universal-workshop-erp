<!--
  Advanced Resource Manager - Universal Workshop Frontend V2
  Comprehensive resource monitoring and optimization for performance management
-->

<template>
  <div class="resource-manager" :class="{ 'rtl': isRTL }">
    <!-- Header Section -->
    <div class="resource-header">
      <div class="header-content">
        <div class="title-section">
          <h2 class="main-title">
            {{ isRTL ? 'مدير الموارد المتقدم' : 'Advanced Resource Manager' }}
          </h2>
          <p class="subtitle">
            {{ isRTL 
              ? 'مراقبة وتحسين موارد النظام في الوقت الفعلي'
              : 'Real-time system resource monitoring and optimization'
            }}
          </p>
        </div>
        
        <div class="header-actions">
          <button 
            @click="refreshMetrics"
            :disabled="isLoading"
            class="refresh-btn"
          >
            <Icon name="refresh" :class="{ 'spinning': isLoading }" />
            {{ isRTL ? 'تحديث' : 'Refresh' }}
          </button>
          
          <button 
            @click="optimizeResources"
            :disabled="isOptimizing"
            class="optimize-btn"
          >
            <Icon name="zap" />
            {{ isRTL ? 'تحسين' : 'Optimize' }}
          </button>
        </div>
      </div>
    </div>

    <!-- System Overview Cards -->
    <div class="overview-grid">
      <div class="metric-card cpu-card">
        <div class="card-header">
          <Icon name="cpu" class="card-icon" />
          <h3>{{ isRTL ? 'المعالج' : 'CPU Usage' }}</h3>
        </div>
        <div class="metric-value">
          <span class="value">{{ resourceMetrics.cpu.toFixed(1) }}%</span>
          <div class="progress-bar">
            <div 
              class="progress-fill"
              :style="{ width: `${resourceMetrics.cpu}%` }"
              :class="getCpuStatusClass(resourceMetrics.cpu)"
            ></div>
          </div>
        </div>
        <div class="metric-details">
          <span class="detail-item">
            {{ isRTL ? 'النوى:' : 'Cores:' }} {{ systemInfo.cpuCores }}
          </span>
          <span class="detail-item">
            {{ isRTL ? 'التردد:' : 'Frequency:' }} {{ systemInfo.cpuFrequency }}
          </span>
        </div>
      </div>

      <div class="metric-card memory-card">
        <div class="card-header">
          <Icon name="memory" class="card-icon" />
          <h3>{{ isRTL ? 'الذاكرة' : 'Memory Usage' }}</h3>
        </div>
        <div class="metric-value">
          <span class="value">{{ formatBytes(resourceMetrics.memoryUsed) }}</span>
          <span class="total">/ {{ formatBytes(resourceMetrics.memoryTotal) }}</span>
          <div class="progress-bar">
            <div 
              class="progress-fill"
              :style="{ width: `${(resourceMetrics.memoryUsed / resourceMetrics.memoryTotal) * 100}%` }"
              :class="getMemoryStatusClass(resourceMetrics.memoryUsed / resourceMetrics.memoryTotal)"
            ></div>
          </div>
        </div>
      </div>

      <div class="metric-card storage-card">
        <div class="card-header">
          <Icon name="hard-drive" class="card-icon" />
          <h3>{{ isRTL ? 'التخزين' : 'Storage Usage' }}</h3>
        </div>
        <div class="metric-value">
          <span class="value">{{ formatBytes(resourceMetrics.storageUsed) }}</span>
          <span class="total">/ {{ formatBytes(resourceMetrics.storageTotal) }}</span>
          <div class="progress-bar">
            <div 
              class="progress-fill"
              :style="{ width: `${(resourceMetrics.storageUsed / resourceMetrics.storageTotal) * 100}%` }"
              :class="getStorageStatusClass(resourceMetrics.storageUsed / resourceMetrics.storageTotal)"
            ></div>
          </div>
        </div>
      </div>

      <div class="metric-card network-card">
        <div class="card-header">
          <Icon name="wifi" class="card-icon" />
          <h3>{{ isRTL ? 'الشبكة' : 'Network Activity' }}</h3>
        </div>
        <div class="metric-value">
          <div class="network-speeds">
            <div class="speed-item">
              <Icon name="download" class="speed-icon" />
              <span>{{ formatSpeed(resourceMetrics.networkDown) }}</span>
            </div>
            <div class="speed-item">
              <Icon name="upload" class="speed-icon" />
              <span>{{ formatSpeed(resourceMetrics.networkUp) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Detailed Charts Section -->
    <div class="charts-section">
      <div class="chart-container">
        <h3>{{ isRTL ? 'استخدام المعالج بمرور الوقت' : 'CPU Usage Over Time' }}</h3>
        <canvas ref="cpuChart" class="resource-chart"></canvas>
      </div>

      <div class="chart-container">
        <h3>{{ isRTL ? 'استخدام الذاكرة بمرور الوقت' : 'Memory Usage Over Time' }}</h3>
        <canvas ref="memoryChart" class="resource-chart"></canvas>
      </div>
    </div>

    <!-- Process Management -->
    <div class="process-section">
      <div class="section-header">
        <h3>{{ isRTL ? 'العمليات النشطة' : 'Active Processes' }}</h3>
        <div class="process-controls">
          <input 
            v-model="processFilter"
            :placeholder="isRTL ? 'البحث في العمليات...' : 'Search processes...'"
            class="process-search"
          />
          <select v-model="processSortBy" class="process-sort">
            <option value="cpu">{{ isRTL ? 'حسب المعالج' : 'By CPU' }}</option>
            <option value="memory">{{ isRTL ? 'حسب الذاكرة' : 'By Memory' }}</option>
            <option value="name">{{ isRTL ? 'حسب الاسم' : 'By Name' }}</option>
          </select>
        </div>
      </div>

      <div class="process-table">
        <div class="table-header">
          <div class="col-name">{{ isRTL ? 'اسم العملية' : 'Process Name' }}</div>
          <div class="col-cpu">{{ isRTL ? 'المعالج %' : 'CPU %' }}</div>
          <div class="col-memory">{{ isRTL ? 'الذاكرة' : 'Memory' }}</div>
          <div class="col-status">{{ isRTL ? 'الحالة' : 'Status' }}</div>
          <div class="col-actions">{{ isRTL ? 'الإجراءات' : 'Actions' }}</div>
        </div>

        <div class="table-body">
          <div 
            v-for="process in filteredProcesses" 
            :key="process.id"
            class="process-row"
          >
            <div class="col-name">
              <Icon :name="getProcessIcon(process.type)" class="process-icon" />
              <span class="process-name">{{ process.name }}</span>
            </div>
            <div class="col-cpu">
              <span class="cpu-usage" :class="getCpuUsageClass(process.cpuUsage)">
                {{ process.cpuUsage.toFixed(1) }}%
              </span>
            </div>
            <div class="col-memory">
              <span class="memory-usage">{{ formatBytes(process.memoryUsage) }}</span>
            </div>
            <div class="col-status">
              <span class="status-badge" :class="`status-${process.status}`">
                {{ isRTL ? getProcessStatusAr(process.status) : process.status }}
              </span>
            </div>
            <div class="col-actions">
              <button 
                @click="killProcess(process.id)"
                class="kill-btn"
                :disabled="process.critical"
                :title="isRTL ? 'إنهاء العملية' : 'Kill Process'"
              >
                <Icon name="x" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Resource Optimization Panel -->
    <div class="optimization-panel" v-if="showOptimization">
      <div class="panel-header">
        <h3>{{ isRTL ? 'توصيات التحسين' : 'Optimization Recommendations' }}</h3>
        <button @click="showOptimization = false" class="close-btn">
          <Icon name="x" />
        </button>
      </div>

      <div class="recommendations">
        <div 
          v-for="recommendation in optimizationRecommendations"
          :key="recommendation.id"
          class="recommendation-item"
        >
          <div class="recommendation-icon">
            <Icon :name="recommendation.icon" :class="recommendation.severity" />
          </div>
          <div class="recommendation-content">
            <h4>{{ isRTL ? recommendation.titleAr : recommendation.title }}</h4>
            <p>{{ isRTL ? recommendation.descriptionAr : recommendation.description }}</p>
          </div>
          <div class="recommendation-actions">
            <button 
              @click="applyRecommendation(recommendation.id)"
              class="apply-btn"
            >
              {{ isRTL ? 'تطبيق' : 'Apply' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- System Information Modal -->
    <Modal v-if="showSystemInfo" @close="showSystemInfo = false">
      <div class="system-info-modal">
        <h3>{{ isRTL ? 'معلومات النظام' : 'System Information' }}</h3>
        
        <div class="info-grid">
          <div class="info-item">
            <label>{{ isRTL ? 'نظام التشغيل:' : 'Operating System:' }}</label>
            <span>{{ systemInfo.os }}</span>
          </div>
          <div class="info-item">
            <label>{{ isRTL ? 'المتصفح:' : 'Browser:' }}</label>
            <span>{{ systemInfo.browser }}</span>
          </div>
          <div class="info-item">
            <label>{{ isRTL ? 'دقة الشاشة:' : 'Screen Resolution:' }}</label>
            <span>{{ systemInfo.screenResolution }}</span>
          </div>
          <div class="info-item">
            <label>{{ isRTL ? 'المنطقة الزمنية:' : 'Timezone:' }}</label>
            <span>{{ systemInfo.timezone }}</span>
          </div>
        </div>
      </div>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { Chart, registerables } from 'chart.js'
import Icon from '@/components/common/Icon.vue'
import Modal from '@/components/common/Modal.vue'

// Register Chart.js components
Chart.register(...registerables)

// Props
interface Props {
  refreshInterval?: number
  enableOptimization?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  refreshInterval: 5000,
  enableOptimization: true
})

// Composables
const { locale } = useI18n()
const isRTL = computed(() => locale.value === 'ar')

// Reactive state
const isLoading = ref(false)
const isOptimizing = ref(false)
const showOptimization = ref(false)
const showSystemInfo = ref(false)
const processFilter = ref('')
const processSortBy = ref('cpu')

// Chart references
const cpuChart = ref<HTMLCanvasElement>()
const memoryChart = ref<HTMLCanvasElement>()
let cpuChartInstance: Chart | null = null
let memoryChartInstance: Chart | null = null

// Resource metrics
const resourceMetrics = reactive({
  cpu: 0,
  memoryUsed: 0,
  memoryTotal: 8589934592, // 8GB
  storageUsed: 0,
  storageTotal: 1099511627776, // 1TB
  networkUp: 0,
  networkDown: 0
})

// System information
const systemInfo = reactive({
  os: '',
  browser: '',
  cpuCores: 0,
  cpuFrequency: '',
  screenResolution: '',
  timezone: ''
})

// Process list
const processes = ref<any[]>([])

// Historical data for charts
const cpuHistory = ref<number[]>([])
const memoryHistory = ref<number[]>([])
const timeLabels = ref<string[]>([])

// Optimization recommendations
const optimizationRecommendations = ref<any[]>([])

// Computed properties
const filteredProcesses = computed(() => {
  let filtered = processes.value

  // Apply filter
  if (processFilter.value) {
    filtered = filtered.filter(process => 
      process.name.toLowerCase().includes(processFilter.value.toLowerCase())
    )
  }

  // Apply sorting
  filtered.sort((a, b) => {
    switch (processSortBy.value) {
      case 'cpu':
        return b.cpuUsage - a.cpuUsage
      case 'memory':
        return b.memoryUsage - a.memoryUsage
      case 'name':
        return a.name.localeCompare(b.name)
      default:
        return 0
    }
  })

  return filtered
})

// Methods
const refreshMetrics = async () => {
  isLoading.value = true
  
  try {
    await updateResourceMetrics()
    await updateProcessList()
    updateCharts()
  } catch (error) {
    console.error('Failed to refresh metrics:', error)
  } finally {
    isLoading.value = false
  }
}

const updateResourceMetrics = async () => {
  // Simulate resource metrics (in real app, get from system APIs)
  resourceMetrics.cpu = Math.random() * 100
  resourceMetrics.memoryUsed = Math.random() * resourceMetrics.memoryTotal
  resourceMetrics.storageUsed = Math.random() * resourceMetrics.storageTotal
  resourceMetrics.networkUp = Math.random() * 1000000 // bytes/sec
  resourceMetrics.networkDown = Math.random() * 10000000 // bytes/sec

  // Update history
  cpuHistory.value.push(resourceMetrics.cpu)
  memoryHistory.value.push((resourceMetrics.memoryUsed / resourceMetrics.memoryTotal) * 100)
  timeLabels.value.push(new Date().toLocaleTimeString())

  // Keep only last 20 data points
  if (cpuHistory.value.length > 20) {
    cpuHistory.value.shift()
    memoryHistory.value.shift()
    timeLabels.value.shift()
  }
}

const updateProcessList = async () => {
  // Simulate process list (in real app, get from system APIs)
  processes.value = [
    {
      id: 1,
      name: 'Universal Workshop Frontend',
      type: 'web',
      cpuUsage: Math.random() * 50,
      memoryUsage: Math.random() * 1000000000,
      status: 'running',
      critical: true
    },
    {
      id: 2,
      name: 'ERPNext Backend',
      type: 'server',
      cpuUsage: Math.random() * 30,
      memoryUsage: Math.random() * 2000000000,
      status: 'running',
      critical: true
    },
    {
      id: 3,
      name: 'MariaDB',
      type: 'database',
      cpuUsage: Math.random() * 20,
      memoryUsage: Math.random() * 1500000000,
      status: 'running',
      critical: true
    }
  ]
}

const updateCharts = () => {
  if (cpuChartInstance) {
    cpuChartInstance.data.labels = timeLabels.value
    cpuChartInstance.data.datasets[0].data = cpuHistory.value
    cpuChartInstance.update()
  }

  if (memoryChartInstance) {
    memoryChartInstance.data.labels = timeLabels.value
    memoryChartInstance.data.datasets[0].data = memoryHistory.value
    memoryChartInstance.update()
  }
}

const initializeCharts = () => {
  if (cpuChart.value) {
    cpuChartInstance = new Chart(cpuChart.value, {
      type: 'line',
      data: {
        labels: timeLabels.value,
        datasets: [{
          label: isRTL.value ? 'استخدام المعالج %' : 'CPU Usage %',
          data: cpuHistory.value,
          borderColor: '#3B82F6',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          tension: 0.4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            max: 100
          }
        }
      }
    })
  }

  if (memoryChart.value) {
    memoryChartInstance = new Chart(memoryChart.value, {
      type: 'line',
      data: {
        labels: timeLabels.value,
        datasets: [{
          label: isRTL.value ? 'استخدام الذاكرة %' : 'Memory Usage %',
          data: memoryHistory.value,
          borderColor: '#10B981',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          tension: 0.4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            max: 100
          }
        }
      }
    })
  }
}

const optimizeResources = async () => {
  isOptimizing.value = true
  
  try {
    // Simulate optimization process
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    // Generate recommendations
    optimizationRecommendations.value = [
      {
        id: 1,
        title: 'Clear Browser Cache',
        titleAr: 'مسح ذاكرة التخزين المؤقت للمتصفح',
        description: 'Clear browser cache to free up memory',
        descriptionAr: 'مسح ذاكرة التخزين المؤقت لتحرير الذاكرة',
        icon: 'trash',
        severity: 'medium'
      },
      {
        id: 2,
        title: 'Close Unused Tabs',
        titleAr: 'إغلاق علامات التبويب غير المستخدمة',
        description: 'Close unused browser tabs to reduce memory usage',
        descriptionAr: 'إغلاق علامات التبويب غير المستخدمة لتقليل استخدام الذاكرة',
        icon: 'x-circle',
        severity: 'low'
      }
    ]
    
    showOptimization.value = true
  } catch (error) {
    console.error('Optimization failed:', error)
  } finally {
    isOptimizing.value = false
  }
}

const applyRecommendation = async (id: number) => {
  const recommendation = optimizationRecommendations.value.find(r => r.id === id)
  if (!recommendation) return

  try {
    // Apply the recommendation
    console.log('Applying recommendation:', recommendation.title)
    
    // Remove from list
    optimizationRecommendations.value = optimizationRecommendations.value.filter(r => r.id !== id)
  } catch (error) {
    console.error('Failed to apply recommendation:', error)
  }
}

const killProcess = async (processId: number) => {
  const process = processes.value.find(p => p.id === processId)
  if (!process || process.critical) return

  try {
    // Simulate killing process
    processes.value = processes.value.filter(p => p.id !== processId)
    console.log('Process killed:', process.name)
  } catch (error) {
    console.error('Failed to kill process:', error)
  }
}

// Utility functions
const formatBytes = (bytes: number): string => {
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  if (bytes === 0) return '0 B'
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return Math.round((bytes / Math.pow(1024, i)) * 100) / 100 + ' ' + sizes[i]
}

const formatSpeed = (bytesPerSecond: number): string => {
  return formatBytes(bytesPerSecond) + '/s'
}

const getCpuStatusClass = (usage: number): string => {
  if (usage > 80) return 'critical'
  if (usage > 60) return 'warning'
  return 'normal'
}

const getMemoryStatusClass = (ratio: number): string => {
  if (ratio > 0.9) return 'critical'
  if (ratio > 0.7) return 'warning'
  return 'normal'
}

const getStorageStatusClass = (ratio: number): string => {
  if (ratio > 0.95) return 'critical'
  if (ratio > 0.8) return 'warning'
  return 'normal'
}

const getCpuUsageClass = (usage: number): string => {
  if (usage > 80) return 'high'
  if (usage > 50) return 'medium'
  return 'low'
}

const getProcessIcon = (type: string): string => {
  const icons = {
    web: 'globe',
    server: 'server',
    database: 'database',
    system: 'cpu'
  }
  return icons[type as keyof typeof icons] || 'circle'
}

const getProcessStatusAr = (status: string): string => {
  const statusMap = {
    running: 'يعمل',
    stopped: 'متوقف',
    paused: 'مؤقت'
  }
  return statusMap[status as keyof typeof statusMap] || status
}

const getSystemInfo = () => {
  systemInfo.os = navigator.platform
  systemInfo.browser = navigator.userAgent.split(' ').pop() || 'Unknown'
  systemInfo.cpuCores = navigator.hardwareConcurrency || 0
  systemInfo.screenResolution = `${screen.width}x${screen.height}`
  systemInfo.timezone = Intl.DateTimeFormat().resolvedOptions().timeZone
}

// Lifecycle
onMounted(async () => {
  getSystemInfo()
  await refreshMetrics()
  initializeCharts()
  
  // Setup refresh interval
  const interval = setInterval(refreshMetrics, props.refreshInterval)
  
  onUnmounted(() => {
    clearInterval(interval)
    if (cpuChartInstance) cpuChartInstance.destroy()
    if (memoryChartInstance) memoryChartInstance.destroy()
  })
})
</script>

<style scoped>
.resource-manager {
  @apply p-6 space-y-6;
}

.resource-manager.rtl {
  direction: rtl;
}

.resource-header {
  @apply bg-white rounded-lg shadow-sm border p-6;
}

.header-content {
  @apply flex items-center justify-between;
}

.title-section h2 {
  @apply text-2xl font-bold text-gray-900 mb-2;
}

.subtitle {
  @apply text-gray-600;
}

.header-actions {
  @apply flex gap-3;
}

.refresh-btn, .optimize-btn {
  @apply px-4 py-2 rounded-lg font-medium flex items-center gap-2 transition-colors;
}

.refresh-btn {
  @apply bg-blue-50 text-blue-700 hover:bg-blue-100;
}

.optimize-btn {
  @apply bg-green-50 text-green-700 hover:bg-green-100;
}

.spinning {
  animation: spin 1s linear infinite;
}

.overview-grid {
  @apply grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6;
}

.metric-card {
  @apply bg-white rounded-lg shadow-sm border p-6;
}

.card-header {
  @apply flex items-center gap-3 mb-4;
}

.card-icon {
  @apply w-6 h-6 text-blue-600;
}

.card-header h3 {
  @apply font-semibold text-gray-900;
}

.metric-value {
  @apply space-y-2;
}

.value {
  @apply text-2xl font-bold text-gray-900;
}

.total {
  @apply text-gray-500 ml-2;
}

.progress-bar {
  @apply w-full h-2 bg-gray-200 rounded-full overflow-hidden;
}

.progress-fill {
  @apply h-full transition-all duration-500;
}

.progress-fill.normal {
  @apply bg-green-500;
}

.progress-fill.warning {
  @apply bg-yellow-500;
}

.progress-fill.critical {
  @apply bg-red-500;
}

.metric-details {
  @apply flex gap-4 text-sm text-gray-600 mt-3;
}

.network-speeds {
  @apply space-y-2;
}

.speed-item {
  @apply flex items-center gap-2;
}

.speed-icon {
  @apply w-4 h-4 text-gray-500;
}

.charts-section {
  @apply grid grid-cols-1 lg:grid-cols-2 gap-6;
}

.chart-container {
  @apply bg-white rounded-lg shadow-sm border p-6;
}

.chart-container h3 {
  @apply font-semibold text-gray-900 mb-4;
}

.resource-chart {
  @apply w-full h-64;
}

.process-section {
  @apply bg-white rounded-lg shadow-sm border p-6;
}

.section-header {
  @apply flex items-center justify-between mb-6;
}

.section-header h3 {
  @apply text-lg font-semibold text-gray-900;
}

.process-controls {
  @apply flex gap-3;
}

.process-search {
  @apply px-3 py-2 border rounded-lg;
}

.process-sort {
  @apply px-3 py-2 border rounded-lg;
}

.process-table {
  @apply border rounded-lg overflow-hidden;
}

.table-header, .process-row {
  @apply grid grid-cols-5 gap-4 p-4;
}

.table-header {
  @apply bg-gray-50 font-medium text-gray-700;
}

.process-row {
  @apply border-t hover:bg-gray-50;
}

.process-icon {
  @apply w-4 h-4 text-gray-500;
}

.process-name {
  @apply ml-2 font-medium;
}

.cpu-usage.high {
  @apply text-red-600 font-semibold;
}

.cpu-usage.medium {
  @apply text-yellow-600 font-semibold;
}

.cpu-usage.low {
  @apply text-green-600;
}

.status-badge {
  @apply px-2 py-1 rounded-full text-xs font-medium;
}

.status-running {
  @apply bg-green-100 text-green-700;
}

.status-stopped {
  @apply bg-red-100 text-red-700;
}

.status-paused {
  @apply bg-yellow-100 text-yellow-700;
}

.kill-btn {
  @apply p-1 text-red-600 hover:bg-red-50 rounded;
}

.optimization-panel {
  @apply bg-white rounded-lg shadow-sm border p-6;
}

.panel-header {
  @apply flex items-center justify-between mb-6;
}

.panel-header h3 {
  @apply text-lg font-semibold text-gray-900;
}

.close-btn {
  @apply p-1 text-gray-400 hover:text-gray-600;
}

.recommendations {
  @apply space-y-4;
}

.recommendation-item {
  @apply flex items-start gap-4 p-4 border rounded-lg;
}

.recommendation-icon {
  @apply flex-shrink-0;
}

.recommendation-icon .medium {
  @apply text-yellow-500;
}

.recommendation-icon .low {
  @apply text-blue-500;
}

.recommendation-content h4 {
  @apply font-medium text-gray-900 mb-1;
}

.recommendation-content p {
  @apply text-gray-600 text-sm;
}

.apply-btn {
  @apply px-3 py-1 bg-blue-50 text-blue-700 rounded-lg text-sm hover:bg-blue-100;
}

.system-info-modal {
  @apply p-6;
}

.system-info-modal h3 {
  @apply text-lg font-semibold mb-6;
}

.info-grid {
  @apply grid grid-cols-1 md:grid-cols-2 gap-4;
}

.info-item {
  @apply flex flex-col gap-1;
}

.info-item label {
  @apply text-sm font-medium text-gray-700;
}

.info-item span {
  @apply text-gray-900;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style> 