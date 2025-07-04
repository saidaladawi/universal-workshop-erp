/**
 * Performance Testing & Benchmarking - Universal Workshop Frontend V2
 * 
 * Comprehensive performance monitoring and benchmarking system for
 * Vue 3 components with metrics collection and reporting.
 */

export interface PerformanceMetric {
  name: string
  value: number
  unit: 'ms' | 'mb' | 'count' | 'fps'
  timestamp: number
  component?: string
  operation?: string
  metadata?: Record<string, any>
}

export interface PerformanceBenchmark {
  name: string
  description: string
  descriptionAr: string
  component: string
  iterations: number
  warmupIterations: number
  metrics: PerformanceMetric[]
  baseline?: number
  threshold?: number
  status: 'pending' | 'running' | 'completed' | 'failed'
}

export interface PerformanceReport {
  id: string
  timestamp: number
  benchmarks: PerformanceBenchmark[]
  summary: {
    totalBenchmarks: number
    passedBenchmarks: number
    failedBenchmarks: number
    averageScore: number
    recommendations: string[]
    recommendationsAr: string[]
  }
  systemInfo: {
    userAgent: string
    memoryLimit: number
    hardwareConcurrency: number
    connectionType?: string
  }
}

export class ComponentPerformanceTester {
  private metrics: Map<string, PerformanceMetric[]> = new Map()
  private benchmarks: PerformanceBenchmark[] = []
  private observer?: PerformanceObserver
  private isMonitoring = false

  /**
   * Start performance monitoring
   */
  startMonitoring(): void {
    if (this.isMonitoring) return

    // Performance Observer for measuring component lifecycle
    if ('PerformanceObserver' in window) {
      this.observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          this.recordMetric({
            name: entry.name,
            value: entry.duration || entry.startTime,
            unit: 'ms',
            timestamp: Date.now(),
            operation: entry.entryType,
            metadata: { entryType: entry.entryType }
          })
        }
      })

      this.observer.observe({ entryTypes: ['measure', 'navigation', 'resource'] })
    }

    // Memory usage monitoring
    this.startMemoryMonitoring()

    // FPS monitoring
    this.startFPSMonitoring()

    this.isMonitoring = true
    console.log('📊 Performance monitoring started')
  }

  /**
   * Stop performance monitoring
   */
  stopMonitoring(): void {
    if (this.observer) {
      this.observer.disconnect()
      this.observer = undefined
    }
    this.isMonitoring = false
    console.log('📊 Performance monitoring stopped')
  }

  /**
   * Record a performance metric
   */
  recordMetric(metric: Omit<PerformanceMetric, 'timestamp'> & { timestamp?: number }): void {
    const fullMetric: PerformanceMetric = {
      ...metric,
      timestamp: metric.timestamp || Date.now()
    }

    const key = metric.component || 'global'
    if (!this.metrics.has(key)) {
      this.metrics.set(key, [])
    }
    this.metrics.get(key)!.push(fullMetric)
  }

  /**
   * Measure component render time
   */
  async measureComponentRender(componentName: string, renderFunction: () => Promise<void>): Promise<number> {
    const markStart = `${componentName}-render-start`
    const markEnd = `${componentName}-render-end`
    const measureName = `${componentName}-render-duration`

    performance.mark(markStart)
    await renderFunction()
    performance.mark(markEnd)
    
    performance.measure(measureName, markStart, markEnd)
    const measure = performance.getEntriesByName(measureName)[0] as PerformanceMeasure
    
    this.recordMetric({
      name: 'render-time',
      value: measure.duration,
      unit: 'ms',
      component: componentName,
      operation: 'render'
    })

    // Cleanup
    performance.clearMarks(markStart)
    performance.clearMarks(markEnd)
    performance.clearMeasures(measureName)

    return measure.duration
  }

  /**
   * Benchmark component performance
   */
  async benchmarkComponent(config: {
    name: string
    component: string
    description: string
    descriptionAr: string
    renderFunction: () => Promise<void>
    iterations?: number
    warmupIterations?: number
    threshold?: number
  }): Promise<PerformanceBenchmark> {
    const benchmark: PerformanceBenchmark = {
      name: config.name,
      description: config.description,
      descriptionAr: config.descriptionAr,
      component: config.component,
      iterations: config.iterations || 100,
      warmupIterations: config.warmupIterations || 10,
      metrics: [],
      threshold: config.threshold,
      status: 'running'
    }

    try {
      console.log(`🚀 Benchmarking ${config.name}...`)

      // Warmup iterations
      for (let i = 0; i < benchmark.warmupIterations; i++) {
        await config.renderFunction()
      }

      // Actual benchmark iterations
      const renderTimes: number[] = []
      for (let i = 0; i < benchmark.iterations; i++) {
        const renderTime = await this.measureComponentRender(config.component, config.renderFunction)
        renderTimes.push(renderTime)
      }

      // Calculate statistics
      const average = renderTimes.reduce((a, b) => a + b, 0) / renderTimes.length
      const min = Math.min(...renderTimes)
      const max = Math.max(...renderTimes)
      const p95 = this.percentile(renderTimes, 95)
      const p99 = this.percentile(renderTimes, 99)

      benchmark.metrics = [
        { name: 'average-render-time', value: average, unit: 'ms', timestamp: Date.now() },
        { name: 'min-render-time', value: min, unit: 'ms', timestamp: Date.now() },
        { name: 'max-render-time', value: max, unit: 'ms', timestamp: Date.now() },
        { name: 'p95-render-time', value: p95, unit: 'ms', timestamp: Date.now() },
        { name: 'p99-render-time', value: p99, unit: 'ms', timestamp: Date.now() }
      ]

      // Check against threshold
      if (benchmark.threshold && average > benchmark.threshold) {
        benchmark.status = 'failed'
        console.warn(`⚠️ Benchmark ${config.name} failed threshold: ${average.toFixed(2)}ms > ${benchmark.threshold}ms`)
      } else {
        benchmark.status = 'completed'
        console.log(`✅ Benchmark ${config.name} completed: ${average.toFixed(2)}ms average`)
      }

    } catch (error) {
      benchmark.status = 'failed'
      console.error(`❌ Benchmark ${config.name} failed:`, error)
    }

    this.benchmarks.push(benchmark)
    return benchmark
  }

  /**
   * Run comprehensive component test suite
   */
  async runTestSuite(): Promise<PerformanceReport> {
    console.log('🧪 Running component performance test suite...')
    
    this.benchmarks = []
    this.startMonitoring()

    try {
      // Button component benchmarks
      await this.benchmarkComponent({
        name: 'Button Render Performance',
        component: 'Button',
        description: 'Measures button component render performance',
        descriptionAr: 'قياس أداء عرض مكون الزر',
        renderFunction: async () => {
          // Simulate button rendering
          const div = document.createElement('div')
          div.innerHTML = '<button class="btn btn-primary">Test Button</button>'
          document.body.appendChild(div)
          await new Promise(resolve => setTimeout(resolve, 1))
          document.body.removeChild(div)
        },
        iterations: 50,
        threshold: 10
      })

      // Input component benchmarks  
      await this.benchmarkComponent({
        name: 'Input Render Performance',
        component: 'Input',
        description: 'Measures input component render performance',
        descriptionAr: 'قياس أداء عرض مكون الإدخال',
        renderFunction: async () => {
          const div = document.createElement('div')
          div.innerHTML = '<input type="text" class="form-control" placeholder="Test Input">'
          document.body.appendChild(div)
          await new Promise(resolve => setTimeout(resolve, 1))
          document.body.removeChild(div)
        },
        iterations: 50,
        threshold: 8
      })

      // Arabic text rendering benchmarks
      await this.benchmarkComponent({
        name: 'Arabic Text Render Performance',
        component: 'ArabicInput',
        description: 'Measures Arabic text component render performance',
        descriptionAr: 'قياس أداء عرض مكون النص العربي',
        renderFunction: async () => {
          const div = document.createElement('div')
          div.innerHTML = '<div dir="rtl" lang="ar">مرحبا بكم في النظام الشامل لإدارة الورش</div>'
          document.body.appendChild(div)
          await new Promise(resolve => setTimeout(resolve, 1))
          document.body.removeChild(div)
        },
        iterations: 30,
        threshold: 5
      })

      // Large list rendering
      await this.benchmarkComponent({
        name: 'Large List Render Performance',
        component: 'List',
        description: 'Measures large list component render performance',
        descriptionAr: 'قياس أداء عرض مكون القائمة الكبيرة',
        renderFunction: async () => {
          const div = document.createElement('div')
          const items = Array.from({ length: 100 }, (_, i) => `<div class="list-item">Item ${i}</div>`).join('')
          div.innerHTML = `<div class="list-container">${items}</div>`
          document.body.appendChild(div)
          await new Promise(resolve => setTimeout(resolve, 5))
          document.body.removeChild(div)
        },
        iterations: 20,
        threshold: 50
      })

    } finally {
      this.stopMonitoring()
    }

    return this.generateReport()
  }

  /**
   * Generate performance report
   */
  generateReport(): PerformanceReport {
    const passedBenchmarks = this.benchmarks.filter(b => b.status === 'completed').length
    const failedBenchmarks = this.benchmarks.filter(b => b.status === 'failed').length
    
    const averageScore = this.calculateOverallScore()
    const recommendations = this.generateRecommendations()

    const report: PerformanceReport = {
      id: `perf-report-${Date.now()}`,
      timestamp: Date.now(),
      benchmarks: [...this.benchmarks],
      summary: {
        totalBenchmarks: this.benchmarks.length,
        passedBenchmarks,
        failedBenchmarks,
        averageScore,
        recommendations: recommendations.en,
        recommendationsAr: recommendations.ar
      },
      systemInfo: this.getSystemInfo()
    }

    console.log('📋 Performance report generated:', report)
    return report
  }

  /**
   * Calculate percentile value
   */
  private percentile(values: number[], percentile: number): number {
    const sorted = [...values].sort((a, b) => a - b)
    const index = (percentile / 100) * (sorted.length - 1)
    const lower = Math.floor(index)
    const upper = Math.ceil(index)
    const weight = index % 1

    return lower === upper ? sorted[lower] : sorted[lower] * (1 - weight) + sorted[upper] * weight
  }

  /**
   * Monitor memory usage
   */
  private startMemoryMonitoring(): void {
    if ('memory' in performance) {
      setInterval(() => {
        const memory = (performance as any).memory
        this.recordMetric({
          name: 'memory-usage',
          value: memory.usedJSHeapSize / 1024 / 1024,
          unit: 'mb',
          operation: 'memory'
        })
      }, 5000)
    }
  }

  /**
   * Monitor frames per second
   */
  private startFPSMonitoring(): void {
    let lastTime = performance.now()
    let frameCount = 0

    const measureFPS = () => {
      frameCount++
      const currentTime = performance.now()
      
      if (currentTime - lastTime >= 1000) {
        const fps = Math.round((frameCount * 1000) / (currentTime - lastTime))
        this.recordMetric({
          name: 'fps',
          value: fps,
          unit: 'fps',
          operation: 'rendering'
        })
        
        frameCount = 0
        lastTime = currentTime
      }
      
      if (this.isMonitoring) {
        requestAnimationFrame(measureFPS)
      }
    }

    requestAnimationFrame(measureFPS)
  }

  /**
   * Calculate overall performance score
   */
  private calculateOverallScore(): number {
    if (this.benchmarks.length === 0) return 0

    const scores = this.benchmarks.map(benchmark => {
      if (benchmark.status !== 'completed') return 0
      
      const avgMetric = benchmark.metrics.find(m => m.name === 'average-render-time')
      if (!avgMetric) return 50
      
      // Score based on render time (lower is better)
      const renderTime = avgMetric.value
      if (renderTime < 5) return 100
      if (renderTime < 10) return 90
      if (renderTime < 20) return 70
      if (renderTime < 50) return 50
      return 20
    })

    return Math.round(scores.reduce((a: number, b: number) => a + b, 0) / scores.length)
  }

  /**
   * Generate performance recommendations
   */
  private generateRecommendations(): { en: string[]; ar: string[] } {
    const recommendations: { en: string[]; ar: string[] } = { en: [], ar: [] }

    const failedBenchmarks = this.benchmarks.filter(b => b.status === 'failed')
    
    if (failedBenchmarks.length > 0) {
      recommendations.en.push('Consider optimizing components that failed performance thresholds')
      recommendations.ar.push('فكر في تحسين المكونات التي فشلت في تحقيق عتبات الأداء')
    }

    const slowComponents = this.benchmarks.filter(b => {
      const avgMetric = b.metrics.find(m => m.name === 'average-render-time')
      return avgMetric && avgMetric.value > 20
    })

    if (slowComponents.length > 0) {
      recommendations.en.push('Implement virtual scrolling for large lists')
      recommendations.ar.push('تنفيذ التمرير الافتراضي للقوائم الكبيرة')
    }

    const memoryMetrics = Array.from(this.metrics.values())
      .flat()
      .filter(m => m.name === 'memory-usage')

    if (memoryMetrics.length > 0) {
      const avgMemory = memoryMetrics.reduce((a, b) => a + b.value, 0) / memoryMetrics.length
      if (avgMemory > 100) {
        recommendations.en.push('Consider implementing component lazy loading')
        recommendations.ar.push('فكر في تنفيذ التحميل البطيء للمكونات')
      }
    }

    return recommendations
  }

  /**
   * Get system information
   */
  private getSystemInfo() {
    return {
      userAgent: navigator.userAgent,
      memoryLimit: (navigator as any).deviceMemory || 0,
      hardwareConcurrency: navigator.hardwareConcurrency || 1,
      connectionType: (navigator as any).connection?.effectiveType
    }
  }

  /**
   * Get collected metrics
   */
  getMetrics(component?: string): PerformanceMetric[] {
    if (component) {
      return this.metrics.get(component) || []
    }
    return Array.from(this.metrics.values()).flat()
  }

  /**
   * Clear collected metrics
   */
  clearMetrics(): void {
    this.metrics.clear()
    this.benchmarks = []
  }

  /**
   * Export metrics to JSON
   */
  exportMetrics(): string {
    return JSON.stringify({
      metrics: Object.fromEntries(this.metrics),
      benchmarks: this.benchmarks,
      timestamp: Date.now()
    }, null, 2)
  }
}

// Global performance tester instance
export const performanceTester = new ComponentPerformanceTester()

// Utility functions for easy access
export function startPerformanceMonitoring(): void {
  performanceTester.startMonitoring()
}

export function stopPerformanceMonitoring(): void {
  performanceTester.stopMonitoring()
}

export function runPerformanceTests(): Promise<PerformanceReport> {
  return performanceTester.runTestSuite()
}

export function recordComponentMetric(metric: Omit<PerformanceMetric, 'timestamp'>): void {
  performanceTester.recordMetric(metric)
}

// Browser global access for debugging
if (typeof window !== 'undefined') {
  (window as any).WorkshopPerformance = {
    tester: performanceTester,
    start: startPerformanceMonitoring,
    stop: stopPerformanceMonitoring,
    runTests: runPerformanceTests,
    record: recordComponentMetric
  }
}

export default ComponentPerformanceTester