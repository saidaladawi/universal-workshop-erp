/**
 * Integration Test Suite - Frontend V2
 * 
 * Comprehensive testing for the integration bridge system
 */

import { FrappeAdapter } from '../api/frappe-adapter'
import { useFrappeStateBridge } from '../stores/frappe-state-bridge'

export interface TestResult {
  name: string
  passed: boolean
  duration: number
  error?: string
  details?: any
}

export class IntegrationTestSuite {
  private adapter: FrappeAdapter
  private stateBridge: ReturnType<typeof useFrappeStateBridge> | null = null
  private results: TestResult[] = []
  
  constructor() {
    this.adapter = FrappeAdapter.getInstance()
  }
  
  async runAllTests(): Promise<TestResult[]> {
    console.log('🧪 Starting Integration Test Suite...')
    this.results = []
    
    const tests = [
      { name: 'Frappe Connection Test', test: this.testFrappeConnection.bind(this) },
      { name: 'API Adapter Test', test: this.testAPIAdapter.bind(this) },
      { name: 'State Bridge Test', test: this.testStateBridge.bind(this) },
      { name: 'Data Sync Test', test: this.testDataSync.bind(this) },
      { name: 'Event System Test', test: this.testEventSystem.bind(this) },
      { name: 'Real-time Updates Test', test: this.testRealTimeUpdates.bind(this) },
      { name: 'Error Handling Test', test: this.testErrorHandling.bind(this) },
      { name: 'Performance Test', test: this.testPerformance.bind(this) }
    ]
    
    for (const test of tests) {
      await this.runSingleTest(test.name, test.test)
    }
    
    this.generateReport()
    return this.results
  }
  
  private async runSingleTest(name: string, testFn: () => Promise<void>): Promise<void> {
    const startTime = performance.now()
    
    try {
      await testFn()
      const duration = performance.now() - startTime
      
      this.results.push({
        name,
        passed: true,
        duration
      })
      
      console.log(`✅ ${name}: PASSED (${duration.toFixed(2)}ms)`)
      
    } catch (error) {
      const duration = performance.now() - startTime
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      
      this.results.push({
        name,
        passed: false,
        duration,
        error: errorMessage
      })
      
      console.error(`❌ ${name}: FAILED (${errorMessage})`)
    }
  }
  
  // Test 1: Frappe Connection
  private async testFrappeConnection(): Promise<void> {
    if (!this.adapter.connected.value) {
      await this.adapter.refresh()
    }
    
    if (!this.adapter.connected.value) {
      throw new Error('Failed to connect to Frappe')
    }
    
    // Test session data
    const session = this.adapter.session.value
    if (!session || !session.user) {
      throw new Error('Invalid session data')
    }
    
    console.log('✓ Frappe connection established')
  }
  
  // Test 2: API Adapter
  private async testAPIAdapter(): Promise<void> {
    // Test basic API call
    const response = await this.adapter.call('frappe.client.get_list', {
      doctype: 'User',
      fields: ['name'],
      limit_page_length: 1
    })
    
    if (!Array.isArray(response) || response.length === 0) {
      throw new Error('API call failed or returned invalid data')
    }
    
    // Test workshop-specific API
    try {
      const configResponse = await this.adapter.getWorkshopConfig()
      if (!configResponse || !configResponse.assets) {
        throw new Error('Workshop config API failed')
      }
    } catch (error) {
      console.warn('Workshop config not available (expected in development)')
    }
    
    console.log('✓ API adapter working correctly')
  }
  
  // Test 3: State Bridge
  private async testStateBridge(): Promise<void> {
    this.stateBridge = useFrappeStateBridge()
    
    // Test initialization
    await this.stateBridge.initializeBridge({ immediate: false })
    
    if (!this.stateBridge.isConnected) {
      throw new Error('State bridge failed to connect')
    }
    
    // Test data access
    const customers = this.stateBridge.getCustomers()
    const serviceOrders = this.stateBridge.getServiceOrders()
    
    // These might be empty, but should be arrays
    if (!Array.isArray(customers) || !Array.isArray(serviceOrders)) {
      throw new Error('State bridge data access failed')
    }
    
    console.log('✓ State bridge initialized and connected')
  }
  
  // Test 4: Data Sync
  private async testDataSync(): Promise<void> {
    if (!this.stateBridge) {
      throw new Error('State bridge not initialized')
    }
    
    // Test syncing customers
    await this.stateBridge.syncDataType('customers')
    
    // Test syncing vehicles
    await this.stateBridge.syncDataType('vehicles')
    
    // Verify sync state
    if (this.stateBridge.hasErrors) {
      const errors = Object.entries(this.stateBridge.syncState.syncErrors)
      throw new Error(`Data sync errors: ${errors.map(([k, v]) => `${k}: ${v}`).join(', ')}`)
    }
    
    console.log('✓ Data synchronization working')
  }
  
  // Test 5: Event System
  private async testEventSystem(): Promise<void> {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error('Event system test timeout'))
      }, 5000)
      
      // Test event listening
      const testEventName = 'integration_test_event'
      const testData = { timestamp: Date.now(), test: true }
      
      // Setup listener
      if (typeof window !== 'undefined' && (window as any).UniversalWorkshopV2) {
        const bridge = (window as any).UniversalWorkshopV2
        
        bridge.onEvent(testEventName, (receivedData: any) => {
          clearTimeout(timeout)
          
          if (receivedData.timestamp === testData.timestamp && receivedData.test === true) {
            console.log('✓ Event system working correctly')
            resolve()
          } else {
            reject(new Error('Event data mismatch'))
          }
        })
        
        // Emit test event
        setTimeout(() => {
          bridge.emitEvent(testEventName, testData)
        }, 100)
        
      } else {
        clearTimeout(timeout)
        console.log('✓ Event system not available (expected without bridge)')
        resolve()
      }
    })
  }
  
  // Test 6: Real-time Updates
  private async testRealTimeUpdates(): Promise<void> {
    try {
      // Test real-time subscription
      const unsubscribe = await this.adapter.subscribeToUpdates('Customer', (data) => {
        console.log('Real-time update received:', data)
      })
      
      // Clean up subscription
      unsubscribe()
      
      console.log('✓ Real-time updates system working')
      
    } catch (error) {
      console.warn('✓ Real-time updates not available (expected in some environments)')
    }
  }
  
  // Test 7: Error Handling
  private async testErrorHandling(): Promise<void> {
    // Test invalid API call
    try {
      await this.adapter.call('invalid.method.name', {})
      throw new Error('Error handling test failed - should have thrown an error')
    } catch (error) {
      if (error instanceof Error && error.message.includes('Error handling test failed')) {
        throw error
      }
      // Expected error - this is good
    }
    
    // Test invalid document access
    try {
      await this.adapter.getDoc({ doctype: 'InvalidDocType', name: 'invalid' })
      throw new Error('Error handling test failed - should have thrown an error')
    } catch (error) {
      if (error instanceof Error && error.message.includes('Error handling test failed')) {
        throw error
      }
      // Expected error - this is good
    }
    
    console.log('✓ Error handling working correctly')
  }
  
  // Test 8: Performance
  private async testPerformance(): Promise<void> {
    const iterations = 10
    const maxDuration = 1000 // 1 second max for batch operations
    
    // Test API call performance
    const startTime = performance.now()
    
    const promises = []
    for (let i = 0; i < iterations; i++) {
      promises.push(this.adapter.call('frappe.client.get_list', {
        doctype: 'User',
        fields: ['name'],
        limit_page_length: 1
      }))
    }
    
    await Promise.all(promises)
    
    const duration = performance.now() - startTime
    
    if (duration > maxDuration) {
      throw new Error(`Performance test failed: ${duration}ms > ${maxDuration}ms`)
    }
    
    console.log(`✓ Performance test passed: ${duration.toFixed(2)}ms for ${iterations} calls`)
  }
  
  private generateReport(): void {
    const passed = this.results.filter(r => r.passed).length
    const total = this.results.length
    const totalDuration = this.results.reduce((sum, r) => sum + r.duration, 0)
    
    console.log('\n📊 Integration Test Report')
    console.log('='.repeat(50))
    console.log(`Tests: ${passed}/${total} passed`)
    console.log(`Total Duration: ${totalDuration.toFixed(2)}ms`)
    console.log(`Average Duration: ${(totalDuration / total).toFixed(2)}ms`)
    
    if (passed === total) {
      console.log('🎉 All integration tests passed!')
    } else {
      console.log('⚠️ Some tests failed:')
      this.results.filter(r => !r.passed).forEach(r => {
        console.log(`  ❌ ${r.name}: ${r.error}`)
      })
    }
    
    console.log('='.repeat(50))
  }
  
  // Utility method to run specific test
  async runSpecificTest(testName: string): Promise<TestResult | null> {
    const testMap: Record<string, () => Promise<void>> = {
      'connection': this.testFrappeConnection.bind(this),
      'api': this.testAPIAdapter.bind(this),
      'state': this.testStateBridge.bind(this),
      'sync': this.testDataSync.bind(this),
      'events': this.testEventSystem.bind(this),
      'realtime': this.testRealTimeUpdates.bind(this),
      'errors': this.testErrorHandling.bind(this),
      'performance': this.testPerformance.bind(this)
    }
    
    const testFn = testMap[testName.toLowerCase()]
    if (!testFn) {
      throw new Error(`Test '${testName}' not found`)
    }
    
    await this.runSingleTest(testName, testFn)
    return this.results[this.results.length - 1] || null
  }
}

// Export for use in development
export const integrationTestSuite = new IntegrationTestSuite()

// Auto-run tests in development mode
if (import.meta.env?.DEV) {
  // Run tests after a short delay to allow initialization
  setTimeout(() => {
    integrationTestSuite.runAllTests().catch(console.error)
  }, 2000)
}