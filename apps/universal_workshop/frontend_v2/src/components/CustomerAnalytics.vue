<template>
  <div class="customer-analytics" :class="{ 'rtl': arabic }">
    <div class="analytics-header">
      <h4 class="analytics-title">
        <i class="fa fa-chart-line"></i>
        {{ arabic ? 'تحليلات العميل' : 'Customer Analytics' }}
      </h4>
      <div class="analytics-controls">
        <select v-model="timeRange" class="form-control" @change="loadAnalytics">
          <option value="1M">{{ arabic ? 'شهر واحد' : '1 Month' }}</option>
          <option value="3M">{{ arabic ? '3 أشهر' : '3 Months' }}</option>
          <option value="6M">{{ arabic ? '6 أشهر' : '6 Months' }}</option>
          <option value="12M">{{ arabic ? 'سنة واحدة' : '1 Year' }}</option>
          <option value="ALL">{{ arabic ? 'جميع البيانات' : 'All Time' }}</option>
        </select>
        <button @click="refreshAnalytics" class="btn btn-sm btn-outline-primary">
          <i class="fa fa-refresh" :class="{ 'fa-spin': loading }"></i>
          {{ arabic ? 'تحديث' : 'Refresh' }}
        </button>
      </div>
    </div>

    <div v-if="loading" class="analytics-loading">
      <div class="loading-spinner"></div>
      <span>{{ arabic ? 'جاري تحليل البيانات...' : 'Analyzing data...' }}</span>
    </div>

    <div v-else class="analytics-content">
      <!-- Key Metrics -->
      <div class="metrics-grid">
        <div class="metric-card revenue">
          <div class="metric-icon">
            <i class="fa fa-dollar-sign"></i>
          </div>
          <div class="metric-content">
            <div class="metric-value">{{ formatCurrency(analytics.totalRevenue) }}</div>
            <div class="metric-label">{{ arabic ? 'إجمالي الإيرادات' : 'Total Revenue' }}</div>
            <div class="metric-change" :class="{ 'positive': analytics.revenueChange > 0, 'negative': analytics.revenueChange < 0 }">
              <i :class="analytics.revenueChange > 0 ? 'fa fa-arrow-up' : 'fa fa-arrow-down'"></i>
              {{ Math.abs(analytics.revenueChange) }}%
            </div>
          </div>
        </div>

        <div class="metric-card orders">
          <div class="metric-icon">
            <i class="fa fa-shopping-cart"></i>
          </div>
          <div class="metric-content">
            <div class="metric-value">{{ analytics.totalOrders }}</div>
            <div class="metric-label">{{ arabic ? 'إجمالي الطلبات' : 'Total Orders' }}</div>
            <div class="metric-change" :class="{ 'positive': analytics.ordersChange > 0, 'negative': analytics.ordersChange < 0 }">
              <i :class="analytics.ordersChange > 0 ? 'fa fa-arrow-up' : 'fa fa-arrow-down'"></i>
              {{ Math.abs(analytics.ordersChange) }}%
            </div>
          </div>
        </div>

        <div class="metric-card frequency">
          <div class="metric-icon">
            <i class="fa fa-calendar"></i>
          </div>
          <div class="metric-content">
            <div class="metric-value">{{ analytics.visitFrequency }}x</div>
            <div class="metric-label">{{ arabic ? 'تكرار الزيارات' : 'Visit Frequency' }}</div>
            <div class="metric-sublabel">{{ arabic ? 'شهرياً' : 'per month' }}</div>
          </div>
        </div>

        <div class="metric-card satisfaction">
          <div class="metric-icon">
            <i class="fa fa-star"></i>
          </div>
          <div class="metric-content">
            <div class="metric-value">{{ analytics.satisfactionScore }}/5</div>
            <div class="metric-label">{{ arabic ? 'تقييم الرضا' : 'Satisfaction' }}</div>
            <div class="rating-stars">
              <i 
                v-for="i in 5" 
                :key="i"
                class="fa fa-star"
                :class="{ 'filled': i <= Math.round(analytics.satisfactionScore) }"
              ></i>
            </div>
          </div>
        </div>
      </div>

      <!-- Charts Section -->
      <div v-if="showCharts" class="charts-section">
        <!-- Revenue Trend Chart -->
        <div class="chart-container">
          <h5 class="chart-title">
            {{ arabic ? 'اتجاه الإيرادات' : 'Revenue Trend' }}
          </h5>
          <div class="chart-placeholder" ref="revenueChart">
            <canvas id="revenueChart" width="400" height="200"></canvas>
          </div>
        </div>

        <!-- Service Types Distribution -->
        <div class="chart-container">
          <h5 class="chart-title">
            {{ arabic ? 'توزيع أنواع الخدمات' : 'Service Types Distribution' }}
          </h5>
          <div class="chart-placeholder" ref="serviceChart">
            <canvas id="serviceChart" width="400" height="200"></canvas>
          </div>
        </div>
      </div>

      <!-- Service History Summary -->
      <div class="service-history">
        <h5 class="section-title">
          {{ arabic ? 'ملخص تاريخ الخدمات' : 'Service History Summary' }}
        </h5>
        
        <div class="history-stats">
          <div class="stat-item">
            <div class="stat-label">{{ arabic ? 'آخر زيارة:' : 'Last Visit:' }}</div>
            <div class="stat-value">{{ formatDate(analytics.lastVisit) }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">{{ arabic ? 'الخدمة المفضلة:' : 'Most Common Service:' }}</div>
            <div class="stat-value">{{ arabic ? analytics.mostCommonService?.name_ar || analytics.mostCommonService?.name : analytics.mostCommonService?.name }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">{{ arabic ? 'متوسط قيمة الفاتورة:' : 'Average Bill:' }}</div>
            <div class="stat-value">{{ formatCurrency(analytics.averageBill) }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">{{ arabic ? 'النقاط المكتسبة:' : 'Loyalty Points:' }}</div>
            <div class="stat-value">{{ analytics.loyaltyPoints }} {{ arabic ? 'نقطة' : 'points' }}</div>
          </div>
        </div>
      </div>

      <!-- Recent Services -->
      <div class="recent-services">
        <h5 class="section-title">
          {{ arabic ? 'الخدمات الأخيرة' : 'Recent Services' }}
        </h5>
        
        <div v-if="!analytics.recentServices?.length" class="no-services">
          <i class="fa fa-history fa-2x text-muted"></i>
          <p class="text-muted">{{ arabic ? 'لا توجد خدمات حديثة' : 'No recent services' }}</p>
        </div>
        
        <div v-else class="services-timeline">
          <div 
            v-for="service in analytics.recentServices" 
            :key="service.name"
            class="service-item"
          >
            <div class="service-date">
              {{ formatDate(service.date) }}
            </div>
            <div class="service-details">
              <div class="service-type">
                {{ arabic ? service.service_type_ar || service.service_type : service.service_type }}
              </div>
              <div class="service-vehicle">
                <i class="fa fa-car"></i>
                {{ service.vehicle }}
              </div>
              <div class="service-status">
                <span 
                  class="status-badge"
                  :class="`status-${service.status.toLowerCase().replace(' ', '-')}`"
                >
                  {{ arabic ? getStatusArabic(service.status) : service.status }}
                </span>
              </div>
            </div>
            <div class="service-amount">
              {{ formatCurrency(service.amount) }}
            </div>
          </div>
        </div>
      </div>

      <!-- Recommendations -->
      <div v-if="analytics.recommendations?.length" class="recommendations">
        <h5 class="section-title">
          {{ arabic ? 'التوصيات' : 'Recommendations' }}
        </h5>
        
        <div class="recommendations-list">
          <div 
            v-for="recommendation in analytics.recommendations" 
            :key="recommendation.id"
            class="recommendation-item"
            :class="`priority-${recommendation.priority}`"
          >
            <div class="recommendation-icon">
              <i :class="getRecommendationIcon(recommendation.type)"></i>
            </div>
            <div class="recommendation-content">
              <div class="recommendation-title">
                {{ arabic ? recommendation.title_ar || recommendation.title : recommendation.title }}
              </div>
              <div class="recommendation-description">
                {{ arabic ? recommendation.description_ar || recommendation.description : recommendation.description }}
              </div>
            </div>
            <div class="recommendation-action">
              <button 
                @click="applyRecommendation(recommendation)"
                class="btn btn-sm btn-outline-primary"
              >
                {{ arabic ? 'تطبيق' : 'Apply' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import { useFrappeAdapter } from '../api/frappe-adapter'
import { formatDistanceToNow, format } from 'date-fns'
import { ar } from 'date-fns/locale'

interface Props {
  doctype: string
  docname: string
  frm?: any
  showCharts?: boolean
  timeRange?: string
  arabic?: boolean
}

interface CustomerAnalytics {
  totalRevenue: number
  revenueChange: number
  totalOrders: number
  ordersChange: number
  visitFrequency: number
  satisfactionScore: number
  lastVisit: string
  mostCommonService: {
    name: string
    name_ar?: string
  }
  averageBill: number
  loyaltyPoints: number
  recentServices: Array<{
    name: string
    date: string
    service_type: string
    service_type_ar?: string
    vehicle: string
    status: string
    amount: number
  }>
  revenueData: Array<{
    period: string
    amount: number
  }>
  serviceDistribution: Array<{
    service: string
    count: number
    percentage: number
  }>
  recommendations: Array<{
    id: string
    type: string
    priority: 'high' | 'medium' | 'low'
    title: string
    title_ar?: string
    description: string
    description_ar?: string
  }>
}

const props = withDefaults(defineProps<Props>(), {
  showCharts: true,
  timeRange: '12M',
  arabic: false
})

const { call } = useFrappeAdapter()

// Reactive state
const loading = ref(false)
const timeRange = ref(props.timeRange)
const analytics = ref<CustomerAnalytics>({
  totalRevenue: 0,
  revenueChange: 0,
  totalOrders: 0,
  ordersChange: 0,
  visitFrequency: 0,
  satisfactionScore: 0,
  lastVisit: '',
  mostCommonService: { name: '' },
  averageBill: 0,
  loyaltyPoints: 0,
  recentServices: [],
  revenueData: [],
  serviceDistribution: [],
  recommendations: []
})

// Chart refs
const revenueChart = ref<HTMLElement>()
const serviceChart = ref<HTMLElement>()

// Methods
const loadAnalytics = async () => {
  if (!props.docname || props.docname === 'new') return
  
  loading.value = true
  try {
    const response = await call('universal_workshop.api.customers.get_customer_analytics', {
      customer: props.docname,
      time_range: timeRange.value
    })
    
    if (response) {
      analytics.value = { ...analytics.value, ...response }
      
      // Load charts after data is available
      if (props.showCharts) {
        await nextTick()
        renderCharts()
      }
    }
  } catch (error) {
    console.error('Failed to load customer analytics:', error)
  } finally {
    loading.value = false
  }
}

const refreshAnalytics = () => {
  loadAnalytics()
}

const renderCharts = () => {
  if (!props.showCharts) return
  
  try {
    renderRevenueChart()
    renderServiceChart()
  } catch (error) {
    console.warn('Charts library not available:', error)
  }
}

const renderRevenueChart = () => {
  const canvas = document.getElementById('revenueChart') as HTMLCanvasElement
  if (!canvas || !analytics.value.revenueData?.length) return
  
  // Simple chart rendering - in real implementation you'd use Chart.js or similar
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  
  // Draw simple line chart
  const data = analytics.value.revenueData
  const maxValue = Math.max(...data.map(d => d.amount))
  const width = canvas.width - 60
  const height = canvas.height - 60
  const stepX = width / (data.length - 1)
  const stepY = height / maxValue
  
  ctx.strokeStyle = '#007bff'
  ctx.lineWidth = 2
  ctx.beginPath()
  
  data.forEach((point, index) => {
    const x = 30 + index * stepX
    const y = canvas.height - 30 - (point.amount * stepY)
    
    if (index === 0) {
      ctx.moveTo(x, y)
    } else {
      ctx.lineTo(x, y)
    }
  })
  
  ctx.stroke()
  
  // Draw points
  ctx.fillStyle = '#007bff'
  data.forEach((point, index) => {
    const x = 30 + index * stepX
    const y = canvas.height - 30 - (point.amount * stepY)
    
    ctx.beginPath()
    ctx.arc(x, y, 4, 0, 2 * Math.PI)
    ctx.fill()
  })
}

const renderServiceChart = () => {
  const canvas = document.getElementById('serviceChart') as HTMLCanvasElement
  if (!canvas || !analytics.value.serviceDistribution?.length) return
  
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  
  // Draw simple pie chart
  const centerX = canvas.width / 2
  const centerY = canvas.height / 2
  const radius = Math.min(centerX, centerY) - 20
  
  let startAngle = 0
  const colors = ['#007bff', '#28a745', '#ffc107', '#dc3545', '#6c757d']
  
  analytics.value.serviceDistribution.forEach((segment, index) => {
    const sliceAngle = (segment.percentage / 100) * 2 * Math.PI
    
    ctx.fillStyle = colors[index % colors.length]
    ctx.beginPath()
    ctx.moveTo(centerX, centerY)
    ctx.arc(centerX, centerY, radius, startAngle, startAngle + sliceAngle)
    ctx.closePath()
    ctx.fill()
    
    startAngle += sliceAngle
  })
}

const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat(props.arabic ? 'ar-OM' : 'en-OM', {
    style: 'currency',
    currency: 'OMR'
  }).format(amount)
}

const formatDate = (dateString: string): string => {
  if (!dateString) return ''
  
  const date = new Date(dateString)
  const locale = props.arabic ? ar : undefined
  
  try {
    return formatDistanceToNow(date, { 
      addSuffix: true,
      locale 
    })
  } catch {
    return format(date, 'PP', { locale })
  }
}

const getStatusArabic = (status: string): string => {
  const statusMap: Record<string, string> = {
    'Draft': 'مسودة',
    'Scheduled': 'مجدول',
    'In Progress': 'قيد التنفيذ',
    'Completed': 'مكتمل',
    'Cancelled': 'ملغي'
  }
  return statusMap[status] || status
}

const getRecommendationIcon = (type: string): string => {
  const iconMap: Record<string, string> = {
    'maintenance': 'fa fa-wrench',
    'service': 'fa fa-cogs',
    'promotion': 'fa fa-tag',
    'loyalty': 'fa fa-star',
    'feedback': 'fa fa-comment',
    'followup': 'fa fa-phone'
  }
  return iconMap[type] || 'fa fa-lightbulb'
}

const applyRecommendation = async (recommendation: any) => {
  try {
    await call('universal_workshop.api.customers.apply_recommendation', {
      customer: props.docname,
      recommendation_id: recommendation.id
    })
    
    // Refresh analytics to reflect changes
    loadAnalytics()
  } catch (error) {
    console.error('Failed to apply recommendation:', error)
  }
}

// Lifecycle
onMounted(() => {
  loadAnalytics()
})

// Watch for prop changes
watch(() => props.docname, () => {
  if (props.docname && props.docname !== 'new') {
    loadAnalytics()
  }
})

watch(() => timeRange.value, () => {
  loadAnalytics()
})
</script>

<style scoped>
.customer-analytics {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.customer-analytics.rtl {
  direction: rtl;
  text-align: right;
}

.analytics-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.analytics-title {
  margin: 0;
  font-size: 1.1em;
  font-weight: 600;
  color: #333;
}

.analytics-controls {
  display: flex;
  gap: 10px;
  align-items: center;
}

.analytics-controls select {
  min-width: 120px;
}

.analytics-loading {
  text-align: center;
  padding: 40px;
  color: #666;
}

.loading-spinner {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 2px solid #f3f3f3;
  border-top: 2px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-right: 10px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.metric-card {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 20px;
  border-radius: 8px;
  border-left: 4px solid #007bff;
  background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
  transition: transform 0.2s, box-shadow 0.2s;
}

.metric-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.rtl .metric-card {
  border-left: none;
  border-right: 4px solid #007bff;
}

.metric-card.revenue {
  border-left-color: #28a745;
}

.metric-card.orders {
  border-left-color: #007bff;
}

.metric-card.frequency {
  border-left-color: #ffc107;
}

.metric-card.satisfaction {
  border-left-color: #dc3545;
}

.rtl .metric-card.revenue {
  border-right-color: #28a745;
}

.rtl .metric-card.orders {
  border-right-color: #007bff;
}

.rtl .metric-card.frequency {
  border-right-color: #ffc107;
}

.rtl .metric-card.satisfaction {
  border-right-color: #dc3545;
}

.metric-icon {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: rgba(0,123,255,0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5em;
  color: #007bff;
}

.revenue .metric-icon {
  background: rgba(40,167,69,0.1);
  color: #28a745;
}

.orders .metric-icon {
  background: rgba(0,123,255,0.1);
  color: #007bff;
}

.frequency .metric-icon {
  background: rgba(255,193,7,0.1);
  color: #ffc107;
}

.satisfaction .metric-icon {
  background: rgba(220,53,69,0.1);
  color: #dc3545;
}

.metric-content {
  flex: 1;
}

.metric-value {
  font-size: 1.8em;
  font-weight: 700;
  color: #333;
  margin-bottom: 4px;
}

.metric-label {
  font-size: 0.9em;
  color: #666;
  margin-bottom: 4px;
}

.metric-sublabel {
  font-size: 0.8em;
  color: #999;
}

.metric-change {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.85em;
  font-weight: 500;
}

.metric-change.positive {
  color: #28a745;
}

.metric-change.negative {
  color: #dc3545;
}

.rating-stars {
  display: flex;
  gap: 2px;
  margin-top: 4px;
}

.rating-stars .fa-star {
  color: #ddd;
  font-size: 0.9em;
}

.rating-stars .fa-star.filled {
  color: #ffc107;
}

.charts-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 30px;
}

.chart-container {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
}

.chart-title {
  margin: 0 0 15px 0;
  font-size: 1em;
  font-weight: 600;
  color: #333;
}

.chart-placeholder {
  position: relative;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.service-history,
.recent-services,
.recommendations {
  margin-bottom: 25px;
}

.section-title {
  margin: 0 0 15px 0;
  font-size: 1em;
  font-weight: 600;
  color: #333;
  padding-bottom: 8px;
  border-bottom: 2px solid #e9ecef;
}

.history-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.stat-item {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 6px;
  border-left: 3px solid #007bff;
}

.rtl .stat-item {
  border-left: none;
  border-right: 3px solid #007bff;
}

.stat-label {
  font-size: 0.85em;
  color: #666;
  margin-bottom: 5px;
}

.stat-value {
  font-weight: 600;
  color: #333;
}

.no-services {
  text-align: center;
  padding: 40px;
  color: #666;
}

.services-timeline {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.service-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 3px solid #007bff;
}

.rtl .service-item {
  border-left: none;
  border-right: 3px solid #007bff;
}

.service-date {
  min-width: 120px;
  font-size: 0.85em;
  color: #666;
  font-weight: 500;
}

.service-details {
  flex: 1;
}

.service-type {
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.service-vehicle {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85em;
  color: #666;
  margin-bottom: 4px;
}

.status-badge {
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 0.75em;
  font-weight: 500;
  text-transform: uppercase;
}

.status-draft {
  background: #f8f9fa;
  color: #6c757d;
}

.status-scheduled {
  background: #cce5ff;
  color: #0056b3;
}

.status-in-progress {
  background: #fff3cd;
  color: #856404;
}

.status-completed {
  background: #d4edda;
  color: #155724;
}

.status-cancelled {
  background: #f8d7da;
  color: #721c24;
}

.service-amount {
  font-weight: 600;
  color: #28a745;
  min-width: 100px;
  text-align: right;
}

.rtl .service-amount {
  text-align: left;
}

.recommendations-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.recommendation-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 3px solid #007bff;
}

.rtl .recommendation-item {
  border-left: none;
  border-right: 3px solid #007bff;
}

.recommendation-item.priority-high {
  border-left-color: #dc3545;
  background: #fff5f5;
}

.recommendation-item.priority-medium {
  border-left-color: #ffc107;
  background: #fffbf0;
}

.recommendation-item.priority-low {
  border-left-color: #28a745;
  background: #f8fff9;
}

.rtl .recommendation-item.priority-high {
  border-right-color: #dc3545;
}

.rtl .recommendation-item.priority-medium {
  border-right-color: #ffc107;
}

.rtl .recommendation-item.priority-low {
  border-right-color: #28a745;
}

.recommendation-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(0,123,255,0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2em;
  color: #007bff;
}

.recommendation-content {
  flex: 1;
}

.recommendation-title {
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.recommendation-description {
  font-size: 0.9em;
  color: #666;
  line-height: 1.4;
}

.form-control {
  padding: 6px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.btn {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-outline-primary {
  background: transparent;
  color: #007bff;
  border: 1px solid #007bff;
}

.btn-sm {
  padding: 4px 8px;
  font-size: 12px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* RTL adjustments */
.rtl .analytics-header {
  flex-direction: row-reverse;
}

.rtl .analytics-controls {
  flex-direction: row-reverse;
}

.rtl .metric-card {
  flex-direction: row-reverse;
}

.rtl .service-item {
  flex-direction: row-reverse;
}

.rtl .recommendation-item {
  flex-direction: row-reverse;
}

/* Responsive design */
@media (max-width: 768px) {
  .metrics-grid {
    grid-template-columns: 1fr;
  }
  
  .charts-section {
    grid-template-columns: 1fr;
  }
  
  .history-stats {
    grid-template-columns: 1fr;
  }
  
  .service-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .recommendation-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
}
</style>