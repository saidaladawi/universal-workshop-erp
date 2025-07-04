/**
 * Performance Monitor - Universal Workshop Frontend V2
 * 
 * Comprehensive performance monitoring with metrics collection,
 * real-time analysis, and optimization recommendations.
 */

export interface PerformanceMetric {
  name: string
  value: number
  timestamp: number
  category: 'loading' | 'runtime' | 'user' | 'resource'
  metadata?: Record<string, any>
}

export interface PerformanceReport {
  totalMetrics: number
  averageLoadTime: number
  averageRenderTime: number
  memoryUsage: number
  recommendations: string[]
  metrics: PerformanceMetric[]
  generatedAt: Date
}

export class PerformanceMonitor {
  private static instance: PerformanceMonitor | null = null
  private metrics: PerformanceMetric[] = []
  private observers: Set<PerformanceObserver> = new Set()
  private isMonitoring = false
  private startTime = performance.now()

  private constructor() {
    this.setupPerformanceObservers()
  }

  /**
   * Get singleton instance
   */
  static getInstance(): PerformanceMonitor {
    if (!PerformanceMonitor.instance) {
      PerformanceMonitor.instance = new PerformanceMonitor()
    }
    return PerformanceMonitor.instance
  }

  /**
   * Start performance monitoring
   */
  startMonitoring(): void {
    if (this.isMonitoring) return

    this.isMonitoring = true
    this.startTime = performance.now()
    this.setupResourceTiming()
    this.setupUserTiming()
    this.setupNavigationTiming()
    
    console.log('📊 Performance monitoring started')
  }

  /**
   * Stop performance monitoring
   */
  stopMonitoring(): void {
    this.isMonitoring = false
    this.observers.forEach(observer => observer.disconnect())
    this.observers.clear()
    
    console.log('⏹️ Performance monitoring stopped')
  }

  /**
   * Measure page load performance
   */
  measurePageLoad(): void {
    if (document.readyState === 'complete') {
      this.collectLoadMetrics()
    } else {
      window.addEventListener('load', () => {
        this.collectLoadMetrics()
      })
    }
  }

  /**
   * Collect page load metrics
   */
  private collectLoadMetrics(): void {
    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming

    if (navigation) {
      // DNS lookup time
      this.addMetric({
        name: 'dns_lookup_time',
        value: navigation.domainLookupEnd - navigation.domainLookupStart,
        timestamp: Date.now(),
        category: 'loading',
        metadata: { type: 'dns' }
      })

      // Connection time
      this.addMetric({
        name: 'connection_time',
        value: navigation.connectEnd - navigation.connectStart,
        timestamp: Date.now(),
        category: 'loading',
        metadata: { type: 'connection' }
      })

      // First byte time (TTFB)
      this.addMetric({
        name: 'time_to_first_byte',
        value: navigation.responseStart - navigation.requestStart,
        timestamp: Date.now(),
        category: 'loading',
        metadata: { type: 'ttfb' }
      })

      // DOM content loaded
      this.addMetric({
        name: 'dom_content_loaded',
        value: navigation.domContentLoadedEventEnd - navigation.navigationStart,
        timestamp: Date.now(),
        category: 'loading',
        metadata: { type: 'dom' }
      })

      // Total load time
      this.addMetric({
        name: 'total_load_time',
        value: navigation.loadEventEnd - navigation.navigationStart,
        timestamp: Date.now(),
        category: 'loading',
        metadata: { type: 'total' }
      })
    }

    // Core Web Vitals
    this.measureCoreWebVitals()
  }

  /**
   * Measure Core Web Vitals
   */
  private measureCoreWebVitals(): void {
    // Largest Contentful Paint (LCP)
    if ('PerformanceObserver' in window) {
      const lcpObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries()
        const lastEntry = entries[entries.length - 1] as any
        
        this.addMetric({
          name: 'largest_contentful_paint',
          value: lastEntry.startTime,
          timestamp: Date.now(),
          category: 'user',
          metadata: { 
            type: 'lcp',
            element: lastEntry.element?.tagName 
          }
        })
      })

      try {
        lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] })
        this.observers.add(lcpObserver)
      } catch (e) {
        console.warn('LCP observation not supported')
      }

      // First Input Delay (FID)
      const fidObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries()
        entries.forEach((entry: any) => {
          this.addMetric({
            name: 'first_input_delay',
            value: entry.processingStart - entry.startTime,
            timestamp: Date.now(),
            category: 'user',
            metadata: {
              type: 'fid',
              eventType: entry.name
            }
          })
        })
      })

      try {
        fidObserver.observe({ entryTypes: ['first-input'] })
        this.observers.add(fidObserver)
      } catch (e) {
        console.warn('FID observation not supported')
      }

      // Cumulative Layout Shift (CLS)
      const clsObserver = new PerformanceObserver((list) => {
        let clsValue = 0
        const entries = list.getEntries()
        
        entries.forEach((entry: any) => {
          if (!entry.hadRecentInput) {
            clsValue += entry.value
          }
        })

        this.addMetric({
          name: 'cumulative_layout_shift',
          value: clsValue,
          timestamp: Date.now(),
          category: 'user',
          metadata: { 
            type: 'cls',
            entryCount: entries.length 
          }
        })
      })

      try {
        clsObserver.observe({ entryTypes: ['layout-shift'] })
        this.observers.add(clsObserver)
      } catch (e) {
        console.warn('CLS observation not supported')
      }
    }
  }

  /**
   * Measure component render time
   */
  measureComponentRender(componentName: string, renderTime: number): void {
    this.addMetric({
      name: 'component_render_time',
      value: renderTime,
      timestamp: Date.now(),
      category: 'runtime',
      metadata: {
        component: componentName,
        type: 'render'
      }
    })
  }

  /**
   * Measure API call performance
   */
  measureApiCall(endpoint: string, duration: number, success: boolean): void {
    this.addMetric({
      name: 'api_call_duration',
      value: duration,
      timestamp: Date.now(),
      category: 'runtime',
      metadata: {
        endpoint,
        success,
        type: 'api'
      }
    })
  }

  /**
   * Measure memory usage
   */
  measureMemoryUsage(): void {
    if ('memory' in performance) {
      const memory = (performance as any).memory
      
      this.addMetric({
        name: 'memory_used_js_heap',
        value: memory.usedJSHeapSize,
        timestamp: Date.now(),
        category: 'runtime',
        metadata: {
          totalJSHeapSize: memory.totalJSHeapSize,
          jsHeapSizeLimit: memory.jsHeapSizeLimit,
          type: 'memory'
        }
      })
    }
  }

  /**
   * Setup performance observers
   */
  private setupPerformanceObservers(): void {
    if (!('PerformanceObserver' in window)) return

    // Monitor resource loading
    this.setupResourceTiming()
    // Monitor user timing marks
    this.setupUserTiming()
    // Monitor navigation timing
    this.setupNavigationTiming()
  }

  /**
   * Setup resource timing monitoring
   */
  private setupResourceTiming(): void {
    if (!('PerformanceObserver' in window)) return

    const resourceObserver = new PerformanceObserver((list) => {
      const entries = list.getEntries()
      entries.forEach((entry: PerformanceResourceTiming) => {
        this.addMetric({
          name: 'resource_load_time',
          value: entry.responseEnd - entry.startTime,
          timestamp: Date.now(),
          category: 'resource',
          metadata: {
            name: entry.name,
            type: entry.initiatorType,
            size: entry.transferSize,
            cached: entry.transferSize === 0
          }
        })
      })
    })

    try {
      resourceObserver.observe({ entryTypes: ['resource'] })
      this.observers.add(resourceObserver)
    } catch (e) {
      console.warn('Resource timing observation not supported')
    }
  }

  /**
   * Setup user timing monitoring
   */
  private setupUserTiming(): void {
    if (!('PerformanceObserver' in window)) return

    const userTimingObserver = new PerformanceObserver((list) => {
      const entries = list.getEntries()
      entries.forEach((entry) => {
        this.addMetric({
          name: 'user_timing',
          value: entry.duration || 0,
          timestamp: Date.now(),
          category: 'user',
          metadata: {
            name: entry.name,
            type: entry.entryType,
            startTime: entry.startTime
          }
        })
      })
    })

    try {
      userTimingObserver.observe({ entryTypes: ['mark', 'measure'] })
      this.observers.add(userTimingObserver)
    } catch (e) {
      console.warn('User timing observation not supported')
    }
  }

  /**
   * Setup navigation timing monitoring
   */
  private setupNavigationTiming(): void {
    if (!('PerformanceObserver' in window)) return

    const navigationObserver = new PerformanceObserver((list) => {
      const entries = list.getEntries()
      entries.forEach((entry: PerformanceNavigationTiming) => {
        this.addMetric({
          name: 'navigation_timing',
          value: entry.loadEventEnd - entry.navigationStart,
          timestamp: Date.now(),
          category: 'loading',
          metadata: {
            type: entry.type,
            redirectCount: entry.redirectCount,
            transferSize: entry.transferSize
          }
        })
      })
    })

    try {
      navigationObserver.observe({ entryTypes: ['navigation'] })
      this.observers.add(navigationObserver)
    } catch (e) {
      console.warn('Navigation timing observation not supported')
    }
  }

  /**
   * Add performance metric
   */
  private addMetric(metric: PerformanceMetric): void {
    this.metrics.push(metric)
    
    // Keep only last 1000 metrics to prevent memory leaks
    if (this.metrics.length > 1000) {
      this.metrics = this.metrics.slice(-1000)
    }

    // Report to server if configured
    this.reportMetric(metric)
  }

  /**
   * Report metric to server
   */
  private reportMetric(metric: PerformanceMetric): void {
    // Only report critical metrics to avoid spam
    const criticalMetrics = [
      'largest_contentful_paint',
      'first_input_delay',
      'cumulative_layout_shift',
      'total_load_time'
    ]

    if (criticalMetrics.includes(metric.name)) {
      try {
        if (typeof window !== 'undefined' && window.frappe?.call) {
          window.frappe.call({
            method: 'universal_workshop.analytics.record_performance_metric',
            args: { metric }
          }).catch(() => {
            // Silently fail to avoid blocking UI
          })
        }
      } catch (error) {
        // Silently handle errors
      }
    }
  }

  /**
   * Get current performance metrics
   */
  getCurrentMetrics(): PerformanceMetric[] {
    return [...this.metrics]
  }

  /**
   * Get metrics by category
   */
  getMetricsByCategory(category: PerformanceMetric['category']): PerformanceMetric[] {
    return this.metrics.filter(metric => metric.category === category)
  }

  /**
   * Get average metric value
   */
  getAverageMetric(metricName: string): number {
    const relevantMetrics = this.metrics.filter(m => m.name === metricName)
    if (relevantMetrics.length === 0) return 0
    
    const sum = relevantMetrics.reduce((acc, metric) => acc + metric.value, 0)
    return sum / relevantMetrics.length
  }

  /**
   * Generate comprehensive performance report
   */
  generateReport(): PerformanceReport {
    const loadingMetrics = this.getMetricsByCategory('loading')
    const runtimeMetrics = this.getMetricsByCategory('runtime')
    
    const averageLoadTime = this.getAverageMetric('total_load_time')
    const averageRenderTime = this.getAverageMetric('component_render_time')
    
    let memoryUsage = 0
    if ('memory' in performance) {
      memoryUsage = (performance as any).memory.usedJSHeapSize
    }

    const recommendations = this.generateRecommendations()

    return {
      totalMetrics: this.metrics.length,
      averageLoadTime,
      averageRenderTime,
      memoryUsage,
      recommendations,
      metrics: this.getCurrentMetrics(),
      generatedAt: new Date()
    }
  }

  /**
   * Generate performance recommendations
   */
  private generateRecommendations(): string[] {
    const recommendations: string[] = []
    
    const lcp = this.getAverageMetric('largest_contentful_paint')
    if (lcp > 2500) {
      recommendations.push('Optimize Largest Contentful Paint (LCP) - consider image optimization and server response time improvements')
    }

    const fid = this.getAverageMetric('first_input_delay')
    if (fid > 100) {
      recommendations.push('Reduce First Input Delay (FID) - minimize main thread blocking and defer non-critical JavaScript')
    }

    const cls = this.getAverageMetric('cumulative_layout_shift')
    if (cls > 0.1) {
      recommendations.push('Improve Cumulative Layout Shift (CLS) - specify image dimensions and avoid dynamic content insertion')
    }

    const loadTime = this.getAverageMetric('total_load_time')
    if (loadTime > 3000) {
      recommendations.push('Optimize page load time - consider code splitting, lazy loading, and CDN usage')
    }

    if ('memory' in performance) {
      const memory = (performance as any).memory
      const memoryUsagePercent = (memory.usedJSHeapSize / memory.jsHeapSizeLimit) * 100
      if (memoryUsagePercent > 80) {
        recommendations.push('High memory usage detected - review for memory leaks and optimize data structures')
      }
    }

    return recommendations
  }

  /**
   * Clear all metrics
   */
  clearMetrics(): void {
    this.metrics = []
  }

  /**
   * Export metrics for analysis
   */
  exportMetrics(): string {
    return JSON.stringify({
      metrics: this.metrics,
      report: this.generateReport(),
      exportedAt: new Date().toISOString()
    }, null, 2)
  }
}

export default PerformanceMonitor