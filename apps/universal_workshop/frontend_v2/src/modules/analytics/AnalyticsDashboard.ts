/**
 * Real-Time Analytics Dashboard - Universal Workshop Frontend V2
 *
 * Advanced business intelligence dashboard with Arabic support,
 * real-time KPI monitoring, and predictive analytics.
 */

import { ref, computed, reactive, onMounted, onUnmounted } from 'vue'
import { workshopEventBus } from '@/features/realtime/WorkshopEventBus'
import { useLocalizationStore } from '../../stores/localization'

export interface AnalyticsKPI {
  id: string
  name: string
  nameAr: string
  value: number
  previousValue: number
  target: number
  unit: 'currency' | 'number' | 'percentage' | 'duration'
  trend: 'up' | 'down' | 'stable'
  change: number
  priority: 'high' | 'medium' | 'low'
  category: 'financial' | 'operational' | 'customer' | 'quality'
}

export interface RealtimeMetric {
  timestamp: Date
  value: number
  metadata?: Record<string, any>
}

export interface BusinessReport {
  id: string
  title: string
  titleAr: string
  type: 'financial' | 'operational' | 'customer_satisfaction' | 'inventory' | 'compliance'
  periodType: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly'
  data: any[]
  generatedAt: Date
  currency?: string
  locale?: string
}

export interface PredictiveInsight {
  id: string
  type: 'revenue_forecast' | 'demand_prediction' | 'maintenance_alert' | 'customer_churn'
  confidence: number
  prediction: any
  timeframe: string
  actionable: boolean
  recommendations: string[]
  recommendationsAr: string[]
}

export class AnalyticsDashboard {
  private eventBus = workshopEventBus
  private localizationStore = useLocalizationStore()

  private realtimeMetrics = reactive<Map<string, RealtimeMetric[]>>(new Map())
  private kpis = ref<AnalyticsKPI[]>([])
  private reports = ref<BusinessReport[]>([])
  private insights = ref<PredictiveInsight[]>([])
  private isRealTimeEnabled = ref(true)
  private updateInterval = ref<number | null>(null)
  private unsubscribeFunctions: (() => void)[] = []

  constructor() {
    this.initializeKPIs()
    this.setupRealtimeUpdates()
  }

  // Initialize default KPIs
  private initializeKPIs(): void {
    this.kpis.value = [
      {
        id: 'daily_revenue',
        name: 'Daily Revenue',
        nameAr: 'الإيرادات اليومية',
        value: 0,
        previousValue: 0,
        target: 5000,
        unit: 'currency',
        trend: 'stable',
        change: 0,
        priority: 'high',
        category: 'financial'
      },
      {
        id: 'active_services',
        name: 'Active Services',
        nameAr: 'الخدمات النشطة',
        value: 0,
        previousValue: 0,
        target: 50,
        unit: 'number',
        trend: 'stable',
        change: 0,
        priority: 'high',
        category: 'operational'
      },
      {
        id: 'customer_satisfaction',
        name: 'Customer Satisfaction',
        nameAr: 'رضا العملاء',
        value: 0,
        previousValue: 0,
        target: 95,
        unit: 'percentage',
        trend: 'stable',
        change: 0,
        priority: 'high',
        category: 'customer'
      },
      {
        id: 'average_service_time',
        name: 'Avg. Service Time',
        nameAr: 'متوسط وقت الخدمة',
        value: 0,
        previousValue: 0,
        target: 120,
        unit: 'duration',
        trend: 'stable',
        change: 0,
        priority: 'medium',
        category: 'operational'
      },
      {
        id: 'parts_availability',
        name: 'Parts Availability',
        nameAr: 'توفر القطع',
        value: 0,
        previousValue: 0,
        target: 95,
        unit: 'percentage',
        trend: 'stable',
        change: 0,
        priority: 'medium',
        category: 'operational'
      },
      {
        id: 'technician_efficiency',
        name: 'Technician Efficiency',
        nameAr: 'كفاءة الفنيين',
        value: 0,
        previousValue: 0,
        target: 85,
        unit: 'percentage',
        trend: 'stable',
        change: 0,
        priority: 'medium',
        category: 'quality'
      }
    ]
  }

  // Setup real-time metric updates
  private setupRealtimeUpdates(): void {
    // Subscribe to analytics events using the WorkshopEventBus
    const unsubscribe1 = this.eventBus.on('service_update', this.handleMetricUpdate.bind(this))
    const unsubscribe2 = this.eventBus.on('system_alert', this.handleKPIUpdate.bind(this))

    this.unsubscribeFunctions.push(unsubscribe1, unsubscribe2)

    // Start periodic updates
    this.startPeriodicUpdates()
  }

  private handleMetricUpdate(event: { metricId: string; value: number; metadata?: any }): void {
    const { metricId, value, metadata } = event

    if (!this.realtimeMetrics.has(metricId)) {
      this.realtimeMetrics.set(metricId, [])
    }

    const metrics = this.realtimeMetrics.get(metricId)!
    metrics.push({
      timestamp: new Date(),
      value,
      metadata
    })

    // Keep only last 100 data points for performance
    if (metrics.length > 100) {
      metrics.splice(0, metrics.length - 100)
    }
  }

  private handleKPIUpdate(event: { kpiId: string; value: number; previousValue?: number }): void {
    const kpi = this.kpis.value.find(k => k.id === event.kpiId)
    if (kpi) {
      kpi.previousValue = event.previousValue || kpi.value
      kpi.value = event.value
      kpi.change = this.calculatePercentageChange(kpi.value, kpi.previousValue)
      kpi.trend = this.determineTrend(kpi.change)
    }
  }

  private calculatePercentageChange(current: number, previous: number): number {
    if (previous === 0) return 0
    return ((current - previous) / previous) * 100
  }

  private determineTrend(change: number): 'up' | 'down' | 'stable' {
    if (Math.abs(change) < 1) return 'stable'
    return change > 0 ? 'up' : 'down'
  }

  private startPeriodicUpdates(): void {
    this.updateInterval.value = window.setInterval(() => {
      this.refreshAnalytics()
    }, 30000) // Update every 30 seconds
  }

  private async refreshAnalytics(): Promise<void> {
    try {
      // Simulate API calls for real-time data
      await this.updateRevenueMetrics()
      await this.updateOperationalMetrics()
      await this.updateCustomerMetrics()
      await this.generatePredictiveInsights()
    } catch (error) {
      console.error('Failed to refresh analytics:', error)
    }
  }

  private async updateRevenueMetrics(): Promise<void> {
    // Simulate real-time revenue calculation
    const currentRevenue = this.calculateDailyRevenue()
    await this.eventBus.send({
      type: 'system_alert',
      source: 'analytics_dashboard',
      data: {
        kpiId: 'daily_revenue',
        value: currentRevenue,
        previousValue: this.kpis.value.find(k => k.id === 'daily_revenue')?.value
      },
      priority: 'medium'
    })
  }

  private async updateOperationalMetrics(): Promise<void> {
    // Simulate operational metrics updates
    const activeServices = await this.countActiveServices()
    const avgServiceTime = await this.calculateAverageServiceTime()
    const partsAvailability = await this.calculatePartsAvailability()

    await this.eventBus.send({
      type: 'system_alert',
      source: 'analytics_dashboard',
      data: {
        kpiId: 'active_services',
        value: activeServices
      },
      priority: 'medium'
    })

    await this.eventBus.send({
      type: 'system_alert',
      source: 'analytics_dashboard',
      data: {
        kpiId: 'average_service_time',
        value: avgServiceTime
      },
      priority: 'medium'
    })

    await this.eventBus.send({
      type: 'system_alert',
      source: 'analytics_dashboard',
      data: {
        kpiId: 'parts_availability',
        value: partsAvailability
      },
      priority: 'medium'
    })
  }

  private async updateCustomerMetrics(): Promise<void> {
    const satisfaction = await this.calculateCustomerSatisfaction()
    await this.eventBus.send({
      type: 'system_alert',
      source: 'analytics_dashboard',
      data: {
        kpiId: 'customer_satisfaction',
        value: satisfaction
      },
      priority: 'medium'
    })
  }

  // Business calculation methods
  private calculateDailyRevenue(): number {
    // Simulate revenue calculation from completed services
    const completedServices = this.getCompletedServicesToday()
    return completedServices.reduce((total, service) => total + service.amount, 0)
  }

  private async countActiveServices(): Promise<number> {
    // Count services with status 'in_progress' or 'assigned'
    return 25 // Simulated value
  }

  private async calculateAverageServiceTime(): Promise<number> {
    // Calculate average time for completed services
    return 95 // Simulated value in minutes
  }

  private async calculatePartsAvailability(): Promise<number> {
    // Calculate percentage of parts in stock vs required
    return 88 // Simulated percentage
  }

  private async calculateCustomerSatisfaction(): Promise<number> {
    // Calculate satisfaction from recent surveys/ratings
    return 92 // Simulated percentage
  }

  private getCompletedServicesToday(): any[] {
    // Simulate completed services data
    return [
      { id: '1', amount: 150.5, completedAt: new Date() },
      { id: '2', amount: 275.0, completedAt: new Date() },
      { id: '3', amount: 89.75, completedAt: new Date() }
    ]
  }

  // Generate Arabic business reports
  async generateArabicReport(type: BusinessReport['type'], period: BusinessReport['periodType']): Promise<BusinessReport> {
    const reportData = await this.fetchReportData(type, period)
    const preferArabic = this.localizationStore.preferArabic

    const report: BusinessReport = {
      id: `${type}_${period}_${Date.now()}`,
      title: this.getReportTitle(type, preferArabic),
      titleAr: this.getReportTitleAr(type),
      type,
      periodType: period,
      data: reportData,
      generatedAt: new Date(),
      currency: 'OMR',
      locale: preferArabic ? 'ar-OM' : 'en-OM'
    }

    this.reports.value.push(report)
    return report
  }

  private getReportTitle(type: BusinessReport['type'], preferArabic: boolean): string {
    const titles = {
      financial: preferArabic ? 'التقرير المالي' : 'Financial Report',
      operational: preferArabic ? 'تقرير العمليات' : 'Operational Report',
      customer_satisfaction: preferArabic ? 'تقرير رضا العملاء' : 'Customer Satisfaction Report',
      inventory: preferArabic ? 'تقرير المخزون' : 'Inventory Report',
      compliance: preferArabic ? 'تقرير الامتثال' : 'Compliance Report'
    }
    return titles[type]
  }

  private getReportTitleAr(type: BusinessReport['type']): string {
    const titlesAr = {
      financial: 'التقرير المالي',
      operational: 'تقرير العمليات',
      customer_satisfaction: 'تقرير رضا العملاء',
      inventory: 'تقرير المخزون',
      compliance: 'تقرير الامتثال'
    }
    return titlesAr[type]
  }

  private async fetchReportData(type: BusinessReport['type'], period: BusinessReport['periodType']): Promise<any[]> {
    // Simulate fetching report data from API
    return [
      { date: new Date(), value: 1500, category: 'revenue' },
      { date: new Date(), value: 25, category: 'services' },
      { date: new Date(), value: 92, category: 'satisfaction' }
    ]
  }

  // Generate predictive insights
  private async generatePredictiveInsights(): Promise<void> {
    try {
      const revenueInsight = await this.generateRevenueForecast()
      const demandInsight = await this.generateDemandPrediction()
      const maintenanceInsight = await this.generateMaintenanceAlert()

      this.insights.value = [revenueInsight, demandInsight, maintenanceInsight]
    } catch (error) {
      console.error('Failed to generate predictive insights:', error)
    }
  }

  private async generateRevenueForecast(): Promise<PredictiveInsight> {
    return {
      id: 'revenue_forecast_' + Date.now(),
      type: 'revenue_forecast',
      confidence: 85,
      prediction: {
        nextWeekRevenue: 8500,
        nextMonthRevenue: 35000,
        trend: 'increasing'
      },
      timeframe: '30 days',
      actionable: true,
      recommendations: [
        'Increase marketing efforts for high-value services',
        'Schedule additional technicians for peak periods',
        'Stock up on popular parts based on predicted demand'
      ],
      recommendationsAr: [
        'زيادة الجهود التسويقية للخدمات عالية القيمة',
        'جدولة فنيين إضافيين في فترات الذروة',
        'تخزين القطع الشائعة بناءً على الطلب المتوقع'
      ]
    }
  }

  private async generateDemandPrediction(): Promise<PredictiveInsight> {
    return {
      id: 'demand_prediction_' + Date.now(),
      type: 'demand_prediction',
      confidence: 78,
      prediction: {
        highDemandServices: ['brake_service', 'oil_change', 'tire_replacement'],
        peakHours: ['09:00-11:00', '14:00-16:00'],
        peakDays: ['Tuesday', 'Wednesday', 'Thursday']
      },
      timeframe: '14 days',
      actionable: true,
      recommendations: [
        'Adjust staffing for predicted peak hours',
        'Prepare service packages for high-demand services',
        'Optimize appointment scheduling'
      ],
      recommendationsAr: [
        'تعديل العمالة للساعات المتوقعة للذروة',
        'إعداد حزم خدمة للخدمات عالية الطلب',
        'تحسين جدولة المواعيد'
      ]
    }
  }

  private async generateMaintenanceAlert(): Promise<PredictiveInsight> {
    return {
      id: 'maintenance_alert_' + Date.now(),
      type: 'maintenance_alert',
      confidence: 92,
      prediction: {
        equipmentId: 'lift_bay_2',
        predictedFailureDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
        severity: 'medium',
        estimatedDowntime: '4-6 hours'
      },
      timeframe: '7 days',
      actionable: true,
      recommendations: [
        'Schedule preventive maintenance for Bay 2 lift',
        'Order replacement parts in advance',
        'Plan alternative bay assignments'
      ],
      recommendationsAr: [
        'جدولة الصيانة الوقائية لرافعة المكان 2',
        'طلب قطع الغيار مسبقاً',
        'التخطيط لتعيينات أماكن بديلة'
      ]
    }
  }

  // Export methods for use in components
  getKPIs = () => this.kpis.value
  getReports = () => this.reports.value
  getInsights = () => this.insights.value
  getRealtimeMetrics = (metricId: string) => this.realtimeMetrics.get(metricId) || []

  // Cleanup
  cleanup(): void {
    if (this.updateInterval.value) {
      clearInterval(this.updateInterval.value)
      this.updateInterval.value = null
    }

    // Unsubscribe from all event handlers
    this.unsubscribeFunctions.forEach(unsubscribe => unsubscribe())
    this.unsubscribeFunctions = []
  }
}

// Composable for using the analytics dashboard
export function useAnalyticsDashboard() {
  const dashboard = new AnalyticsDashboard()

  onMounted(() => {
    // Dashboard is already initialized
  })

  onUnmounted(() => {
    dashboard.cleanup()
  })

  return {
    kpis: dashboard.getKPIs(),
    reports: dashboard.getReports(),
    insights: dashboard.getInsights(),
    getMetrics: dashboard.getRealtimeMetrics,
    generateReport: dashboard.generateArabicReport.bind(dashboard),
    cleanup: dashboard.cleanup.bind(dashboard)
  }
}
