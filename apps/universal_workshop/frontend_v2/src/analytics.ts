/**
 * Analytics Entry Point - Universal Workshop Frontend V2
 * 
 * Dedicated entry point for analytics and performance monitoring.
 * Provides real-time KPIs, business intelligence, and performance tracking.
 */

import { AnalyticsEngine } from '@/modules/analytics/analytics-engine'
import { PerformanceMonitor } from '@/utils/performance/monitor'
import { RealTimeManager } from '@/modules/analytics/realtime-manager'
import { KPICalculator } from '@/modules/analytics/kpi-calculator'

// Analytics-specific styles
import '@/styles/analytics/dashboard.scss'
import '@/styles/analytics/charts.scss'

/**
 * Analytics application for business intelligence
 */
class AnalyticsApp {
  private analyticsEngine: AnalyticsEngine | null = null
  private performanceMonitor: PerformanceMonitor | null = null
  private realTimeManager: RealTimeManager | null = null
  private kpiCalculator: KPICalculator | null = null

  /**
   * Initialize analytics system
   */
  async initialize(): Promise<void> {
    try {
      // Initialize performance monitoring first
      this.performanceMonitor = PerformanceMonitor.getInstance()
      this.performanceMonitor.measurePageLoad()

      // Initialize analytics engine
      this.analyticsEngine = new AnalyticsEngine()
      await this.analyticsEngine.initialize()

      // Initialize real-time data management
      this.realTimeManager = RealTimeManager.getInstance()
      await this.realTimeManager.initialize()

      // Initialize KPI calculation engine
      this.kpiCalculator = new KPICalculator()
      await this.kpiCalculator.initialize()

      // Start real-time updates
      this.startRealTimeUpdates()

      console.log('📊 Analytics system initialized successfully')
    } catch (error) {
      console.error('❌ Failed to initialize analytics system:', error)
      throw error
    }
  }

  /**
   * Start real-time data updates
   */
  private startRealTimeUpdates(): void {
    if (!this.realTimeManager) return

    // Subscribe to workshop metrics
    this.realTimeManager.subscribe('workshop.metrics', (data) => {
      this.handleMetricsUpdate(data)
    })

    // Subscribe to inventory updates
    this.realTimeManager.subscribe('inventory.changes', (data) => {
      this.handleInventoryUpdate(data)
    })

    // Subscribe to financial data
    this.realTimeManager.subscribe('financial.updates', (data) => {
      this.handleFinancialUpdate(data)
    })
  }

  /**
   * Handle metrics updates
   */
  private handleMetricsUpdate(data: any): void {
    if (this.analyticsEngine) {
      this.analyticsEngine.updateMetrics(data)
    }
  }

  /**
   * Handle inventory updates
   */
  private handleInventoryUpdate(data: any): void {
    if (this.kpiCalculator) {
      this.kpiCalculator.updateInventoryKPIs(data)
    }
  }

  /**
   * Handle financial updates
   */
  private handleFinancialUpdate(data: any): void {
    if (this.kpiCalculator) {
      this.kpiCalculator.updateFinancialKPIs(data)
    }
  }

  /**
   * Get current analytics data
   */
  getAnalyticsData() {
    return {
      metrics: this.analyticsEngine?.getCurrentMetrics(),
      kpis: this.kpiCalculator?.getCurrentKPIs(),
      performance: this.performanceMonitor?.generateReport()
    }
  }

  /**
   * Generate analytics report
   */
  async generateReport(dateRange: { from: Date; to: Date }, filters?: any) {
    if (!this.analyticsEngine) {
      throw new Error('Analytics engine not initialized')
    }

    return await this.analyticsEngine.generateReport(dateRange, filters)
  }
}

// Global analytics app instance
const analyticsApp = new AnalyticsApp()

// Export for external use
export { analyticsApp as default, AnalyticsApp }

// Global browser access
if (typeof window !== 'undefined') {
  (window as any).AnalyticsApp = analyticsApp
}