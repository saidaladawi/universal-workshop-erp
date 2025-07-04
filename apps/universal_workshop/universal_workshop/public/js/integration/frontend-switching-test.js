/**
 * Frontend Switching Test Suite - Universal Workshop ERP
 * 
 * Comprehensive testing for frontend switching functionality
 */

class FrontendSwitchingTestSuite {
    constructor() {
        this.testResults = [];
        this.currentTestIndex = 0;
        this.totalTests = 0;
        this.passedTests = 0;
        this.failedTests = 0;
        
        this.init();
    }
    
    init() {
        this.setupTestEnvironment();
        this.logInfo('Frontend Switching Test Suite initialized');
    }
    
    setupTestEnvironment() {
        // Ensure we have necessary objects
        if (typeof window.frontendSwitcher === 'undefined') {
            this.logError('Frontend Switcher not available');
            return false;
        }
        
        if (typeof window.UniversalWorkshopV2 === 'undefined') {
            this.logWarn('V2 Bridge not available - some tests will be skipped');
        }
        
        return true;
    }
    
    async runAllTests() {
        this.logInfo('🧪 Starting Frontend Switching Test Suite...');
        this.testResults = [];
        this.currentTestIndex = 0;
        this.passedTests = 0;
        this.failedTests = 0;
        
        const tests = [
            { name: 'Frontend Switcher Availability', test: this.testFrontendSwitcherAvailability.bind(this) },
            { name: 'User Preference Management', test: this.testUserPreferenceManagement.bind(this) },
            { name: 'V2 Bridge Connection', test: this.testV2BridgeConnection.bind(this) },
            { name: 'Frontend Migration Dialog', test: this.testFrontendMigrationDialog.bind(this) },
            { name: 'Component Embedding', test: this.testComponentEmbedding.bind(this) },
            { name: 'DocType Integration', test: this.testDocTypeIntegration.bind(this) },
            { name: 'Data Synchronization', test: this.testDataSynchronization.bind(this) },
            { name: 'Event System', test: this.testEventSystem.bind(this) },
            { name: 'Arabic/RTL Support', test: this.testArabicRTLSupport.bind(this) },
            { name: 'Mobile Compatibility', test: this.testMobileCompatibility.bind(this) },
            { name: 'Performance Benchmarks', test: this.testPerformance.bind(this) },
            { name: 'Error Handling', test: this.testErrorHandling.bind(this) }
        ];
        
        this.totalTests = tests.length;
        
        for (const test of tests) {
            this.currentTestIndex++;
            await this.runSingleTest(test.name, test.test);
        }
        
        this.generateFinalReport();
        return this.testResults;
    }
    
    async runSingleTest(name, testFn) {
        const startTime = performance.now();
        
        try {
            this.logInfo(`🔍 Running test: ${name}`);
            
            const result = await testFn();
            const duration = performance.now() - startTime;
            
            if (result.passed) {
                this.passedTests++;
                this.logSuccess(`✅ ${name}: PASSED (${duration.toFixed(2)}ms)`);
                if (result.details) {
                    this.logInfo(`   Details: ${result.details}`);
                }
            } else {
                this.failedTests++;
                this.logError(`❌ ${name}: FAILED (${duration.toFixed(2)}ms)`);
                this.logError(`   Error: ${result.error}`);
            }
            
            this.testResults.push({
                name,
                passed: result.passed,
                duration,
                error: result.error || null,
                details: result.details || null,
                index: this.currentTestIndex
            });
            
        } catch (error) {
            const duration = performance.now() - startTime;
            this.failedTests++;
            
            this.logError(`❌ ${name}: FAILED (${duration.toFixed(2)}ms)`);
            this.logError(`   Exception: ${error.message}`);
            
            this.testResults.push({
                name,
                passed: false,
                duration,
                error: error.message,
                details: null,
                index: this.currentTestIndex
            });
        }
    }
    
    // Test 1: Frontend Switcher Availability
    async testFrontendSwitcherAvailability() {
        try {
            // Check if frontend switcher is loaded
            if (typeof window.frontendSwitcher === 'undefined') {
                return { passed: false, error: 'Frontend switcher not loaded' };
            }
            
            // Check required methods
            const requiredMethods = [
                'switchFrontend', 'migrateToV2', 'checkV2Availability',
                'showV2MigrationDialog', 'initializeFrontendSwitcher'
            ];
            
            for (const method of requiredMethods) {
                if (typeof window.frontendSwitcher[method] !== 'function') {
                    return { passed: false, error: `Missing method: ${method}` };
                }
            }
            
            // Test initialization
            const initResult = window.frontendSwitcher.initializeFrontendSwitcher();
            
            return { 
                passed: true, 
                details: `Frontend switcher loaded with ${requiredMethods.length} methods`
            };
            
        } catch (error) {
            return { passed: false, error: error.message };
        }
    }
    
    // Test 2: User Preference Management
    async testUserPreferenceManagement() {
        try {
            // Test getting current preference
            const currentPreference = await window.frontendSwitcher.getUserPreference();
            
            // Test setting preference
            await window.frontendSwitcher.setUserPreference('v2');
            const newPreference = await window.frontendSwitcher.getUserPreference();
            
            if (newPreference !== 'v2') {
                return { passed: false, error: 'Failed to set user preference' };
            }
            
            // Reset to original preference
            await window.frontendSwitcher.setUserPreference(currentPreference);
            
            return { 
                passed: true, 
                details: `Preference management working (original: ${currentPreference})`
            };
            
        } catch (error) {
            return { passed: false, error: error.message };
        }
    }
    
    // Test 3: V2 Bridge Connection
    async testV2BridgeConnection() {
        try {
            if (typeof window.UniversalWorkshopV2 === 'undefined') {
                return { passed: true, details: 'V2 Bridge not available (expected in traditional mode)' };
            }
            
            // Test bridge availability
            const isAvailable = await window.UniversalWorkshopV2.isV2Available();
            
            if (!isAvailable) {
                return { passed: false, error: 'V2 Bridge reports not available' };
            }
            
            // Test basic bridge functionality
            const config = window.UniversalWorkshopV2.getConfig();
            if (!config || !config.assets) {
                return { passed: false, error: 'V2 Bridge config not available' };
            }
            
            return { 
                passed: true, 
                details: `V2 Bridge connected with ${Object.keys(config.assets).length} assets`
            };
            
        } catch (error) {
            return { passed: false, error: error.message };
        }
    }
    
    // Test 4: Frontend Migration Dialog
    async testFrontendMigrationDialog() {
        try {
            // Test showing migration dialog
            const dialogShown = window.frontendSwitcher.showV2MigrationDialog();
            
            if (!dialogShown) {
                return { passed: false, error: 'Migration dialog failed to show' };
            }
            
            // Wait a bit for dialog to render
            await this.sleep(500);
            
            // Check if dialog elements exist
            const dialogElement = document.querySelector('.v2-migration-dialog');
            if (!dialogElement) {
                return { passed: false, error: 'Migration dialog element not found' };
            }
            
            // Close the dialog
            const closeButton = dialogElement.querySelector('.btn-close, .close-dialog');
            if (closeButton) {
                closeButton.click();
            }
            
            return { 
                passed: true, 
                details: 'Migration dialog successfully shown and closed'
            };
            
        } catch (error) {
            return { passed: false, error: error.message };
        }
    }
    
    // Test 5: Component Embedding
    async testComponentEmbedding() {
        try {
            if (typeof window.UniversalWorkshopV2 === 'undefined') {
                return { passed: true, details: 'Component embedding skipped (V2 Bridge not available)' };
            }
            
            // Create a test container
            const testContainer = document.createElement('div');
            testContainer.id = 'component-embedding-test';
            testContainer.style.display = 'none';
            document.body.appendChild(testContainer);
            
            try {
                // Test embedding a simple component
                const embedded = await window.UniversalWorkshopV2.embedComponent(
                    '#component-embedding-test',
                    'TestComponent',
                    { test: true }
                );
                
                if (!embedded) {
                    return { passed: false, error: 'Component embedding returned false' };
                }
                
                return { 
                    passed: true, 
                    details: 'Component embedding successful'
                };
                
            } finally {
                // Clean up
                document.body.removeChild(testContainer);
            }
            
        } catch (error) {
            return { passed: false, error: error.message };
        }
    }
    
    // Test 6: DocType Integration
    async testDocTypeIntegration() {
        try {
            if (typeof window.doctypeEmbeddings === 'undefined') {
                return { passed: false, error: 'DocType embeddings not available' };
            }
            
            // Test getting embedding configuration
            const serviceOrderConfig = window.doctypeEmbeddings.getEmbeddingConfig('Service Order');
            
            if (!serviceOrderConfig) {
                return { passed: false, error: 'Service Order embedding config not found' };
            }
            
            if (!serviceOrderConfig.components || serviceOrderConfig.components.length === 0) {
                return { passed: false, error: 'Service Order config has no components' };
            }
            
            // Test Customer config
            const customerConfig = window.doctypeEmbeddings.getEmbeddingConfig('Customer');
            
            if (!customerConfig) {
                return { passed: false, error: 'Customer embedding config not found' };
            }
            
            return { 
                passed: true, 
                details: `DocType configs found: Service Order (${serviceOrderConfig.components.length} components), Customer (${customerConfig.components.length} components)`
            };
            
        } catch (error) {
            return { passed: false, error: error.message };
        }
    }
    
    // Test 7: Data Synchronization
    async testDataSynchronization() {
        try {
            if (typeof window.UniversalWorkshopV2 === 'undefined') {
                return { passed: true, details: 'Data sync skipped (V2 Bridge not available)' };
            }
            
            // Test syncing different data types
            const dataTypes = ['customers', 'serviceOrders', 'vehicles'];
            const syncResults = [];
            
            for (const dataType of dataTypes) {
                try {
                    const result = await window.UniversalWorkshopV2.syncState(dataType);
                    syncResults.push({ dataType, success: true, result });
                } catch (error) {
                    syncResults.push({ dataType, success: false, error: error.message });
                }
            }
            
            const successfulSyncs = syncResults.filter(r => r.success).length;
            
            if (successfulSyncs === 0) {
                return { passed: false, error: 'All data sync operations failed' };
            }
            
            return { 
                passed: true, 
                details: `Data sync: ${successfulSyncs}/${dataTypes.length} successful`
            };
            
        } catch (error) {
            return { passed: false, error: error.message };
        }
    }
    
    // Test 8: Event System
    async testEventSystem() {
        try {
            if (typeof window.UniversalWorkshopV2 === 'undefined') {
                return { passed: true, details: 'Event system skipped (V2 Bridge not available)' };
            }
            
            return new Promise((resolve) => {
                const testEventName = 'frontend_switching_test_event';
                const testData = { timestamp: Date.now(), test: 'event_system' };
                let eventReceived = false;
                
                // Set up timeout
                const timeout = setTimeout(() => {
                    if (!eventReceived) {
                        resolve({ passed: false, error: 'Event system test timeout' });
                    }
                }, 3000);
                
                // Set up event listener
                window.UniversalWorkshopV2.onEvent(testEventName, (receivedData) => {
                    clearTimeout(timeout);
                    eventReceived = true;
                    
                    if (receivedData.timestamp === testData.timestamp && receivedData.test === testData.test) {
                        resolve({ 
                            passed: true, 
                            details: 'Event system working correctly'
                        });
                    } else {
                        resolve({ passed: false, error: 'Event data mismatch' });
                    }
                });
                
                // Emit test event
                setTimeout(() => {
                    window.UniversalWorkshopV2.emitEvent(testEventName, testData);
                }, 100);
            });
            
        } catch (error) {
            return { passed: false, error: error.message };
        }
    }
    
    // Test 9: Arabic/RTL Support
    async testArabicRTLSupport() {
        try {
            // Test if Arabic CSS is loaded
            const stylesheets = Array.from(document.styleSheets);
            const arabicStylesheet = stylesheets.find(sheet => 
                sheet.href && sheet.href.includes('arabic-rtl.css')
            );
            
            if (!arabicStylesheet) {
                return { passed: false, error: 'Arabic RTL stylesheet not found' };
            }
            
            // Test RTL direction setting
            const testElement = document.createElement('div');
            testElement.className = 'rtl';
            document.body.appendChild(testElement);
            
            const computedStyle = window.getComputedStyle(testElement);
            const direction = computedStyle.direction;
            
            document.body.removeChild(testElement);
            
            if (direction !== 'rtl') {
                return { passed: false, error: 'RTL direction not applied correctly' };
            }
            
            return { 
                passed: true, 
                details: 'Arabic/RTL support properly configured'
            };
            
        } catch (error) {
            return { passed: false, error: error.message };
        }
    }
    
    // Test 10: Mobile Compatibility
    async testMobileCompatibility() {
        try {
            // Test mobile CSS
            const stylesheets = Array.from(document.styleSheets);
            const mobileStylesheet = stylesheets.find(sheet => 
                sheet.href && (sheet.href.includes('mobile') || sheet.href.includes('responsive'))
            );
            
            if (!mobileStylesheet) {
                return { passed: false, error: 'Mobile stylesheets not found' };
            }
            
            // Test viewport meta tag
            const viewportMeta = document.querySelector('meta[name="viewport"]');
            if (!viewportMeta) {
                return { passed: false, error: 'Viewport meta tag not found' };
            }
            
            // Test touch event support
            const touchSupported = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
            
            return { 
                passed: true, 
                details: `Mobile compatibility: CSS loaded, viewport configured, touch ${touchSupported ? 'supported' : 'not supported'}`
            };
            
        } catch (error) {
            return { passed: false, error: error.message };
        }
    }
    
    // Test 11: Performance Benchmarks
    async testPerformance() {
        try {
            const benchmarks = [];
            
            // Benchmark 1: Frontend switching time
            const switchStart = performance.now();
            if (typeof window.frontendSwitcher.checkV2Availability === 'function') {
                await window.frontendSwitcher.checkV2Availability();
            }
            const switchTime = performance.now() - switchStart;
            benchmarks.push({ name: 'Frontend switch check', time: switchTime });
            
            // Benchmark 2: Component loading time (if V2 available)
            if (typeof window.UniversalWorkshopV2 !== 'undefined') {
                const componentStart = performance.now();
                try {
                    await window.UniversalWorkshopV2.loadModule('main');
                    const componentTime = performance.now() - componentStart;
                    benchmarks.push({ name: 'V2 component loading', time: componentTime });
                } catch (error) {
                    benchmarks.push({ name: 'V2 component loading', time: -1, error: error.message });
                }
            }
            
            // Benchmark 3: Data sync time
            if (typeof window.UniversalWorkshopV2 !== 'undefined') {
                const syncStart = performance.now();
                try {
                    await window.UniversalWorkshopV2.syncState('customers');
                    const syncTime = performance.now() - syncStart;
                    benchmarks.push({ name: 'Data synchronization', time: syncTime });
                } catch (error) {
                    benchmarks.push({ name: 'Data synchronization', time: -1, error: error.message });
                }
            }
            
            // Check if any benchmark took too long
            const slowBenchmarks = benchmarks.filter(b => b.time > 2000); // 2 seconds
            
            if (slowBenchmarks.length > 0) {
                return { 
                    passed: false, 
                    error: `Slow performance detected: ${slowBenchmarks.map(b => `${b.name}: ${b.time.toFixed(2)}ms`).join(', ')}`
                };
            }
            
            const avgTime = benchmarks.reduce((sum, b) => sum + (b.time > 0 ? b.time : 0), 0) / benchmarks.filter(b => b.time > 0).length;
            
            return { 
                passed: true, 
                details: `Performance benchmarks completed, avg: ${avgTime.toFixed(2)}ms`
            };
            
        } catch (error) {
            return { passed: false, error: error.message };
        }
    }
    
    // Test 12: Error Handling
    async testErrorHandling() {
        try {
            let errorCount = 0;
            
            // Test 1: Invalid frontend switch
            try {
                await window.frontendSwitcher.switchFrontend('invalid_frontend');
                return { passed: false, error: 'Invalid frontend switch should have thrown error' };
            } catch (error) {
                errorCount++;
            }
            
            // Test 2: Invalid V2 operation (if V2 available)
            if (typeof window.UniversalWorkshopV2 !== 'undefined') {
                try {
                    await window.UniversalWorkshopV2.loadModule('invalid_module');
                    return { passed: false, error: 'Invalid module load should have thrown error' };
                } catch (error) {
                    errorCount++;
                }
            }
            
            // Test 3: Invalid component embedding (if V2 available)
            if (typeof window.UniversalWorkshopV2 !== 'undefined') {
                try {
                    await window.UniversalWorkshopV2.embedComponent('#non_existent_element', 'TestComponent', {});
                    return { passed: false, error: 'Invalid embedding should have thrown error' };
                } catch (error) {
                    errorCount++;
                }
            }
            
            return { 
                passed: true, 
                details: `Error handling working correctly (${errorCount} errors properly caught)`
            };
            
        } catch (error) {
            return { passed: false, error: error.message };
        }
    }
    
    // Utility Methods
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    generateFinalReport() {
        const successRate = (this.passedTests / this.totalTests * 100).toFixed(1);
        
        this.logInfo('\n' + '='.repeat(60));
        this.logInfo('🏁 FRONTEND SWITCHING TEST SUITE RESULTS');
        this.logInfo('='.repeat(60));
        this.logInfo(`📊 Tests: ${this.passedTests}/${this.totalTests} passed (${successRate}%)`);
        this.logInfo(`⏱️  Total Duration: ${this.getTotalDuration().toFixed(2)}ms`);
        this.logInfo(`📈 Average Duration: ${this.getAverageDuration().toFixed(2)}ms`);
        
        if (this.passedTests === this.totalTests) {
            this.logSuccess('🎉 ALL TESTS PASSED! Frontend switching is working correctly.');
        } else {
            this.logError('⚠️  SOME TESTS FAILED:');
            this.testResults.filter(r => !r.passed).forEach(result => {
                this.logError(`  ❌ ${result.name}: ${result.error}`);
            });
        }
        
        this.logInfo('='.repeat(60));
        
        // Generate detailed report
        this.generateDetailedReport();
    }
    
    generateDetailedReport() {
        const report = {
            timestamp: new Date().toISOString(),
            summary: {
                total: this.totalTests,
                passed: this.passedTests,
                failed: this.failedTests,
                successRate: (this.passedTests / this.totalTests * 100).toFixed(1),
                totalDuration: this.getTotalDuration(),
                averageDuration: this.getAverageDuration()
            },
            tests: this.testResults,
            environment: {
                userAgent: navigator.userAgent,
                url: window.location.href,
                timestamp: Date.now(),
                frontendSwitcherAvailable: typeof window.frontendSwitcher !== 'undefined',
                v2BridgeAvailable: typeof window.UniversalWorkshopV2 !== 'undefined',
                doctypeEmbeddingsAvailable: typeof window.doctypeEmbeddings !== 'undefined'
            }
        };
        
        // Store report in sessionStorage for access by other tools
        try {
            sessionStorage.setItem('frontend_switching_test_report', JSON.stringify(report));
            this.logInfo('📋 Detailed test report saved to sessionStorage');
        } catch (error) {
            this.logWarn('Failed to save test report to sessionStorage:', error.message);
        }
        
        return report;
    }
    
    getTotalDuration() {
        return this.testResults.reduce((total, result) => total + result.duration, 0);
    }
    
    getAverageDuration() {
        return this.totalTests > 0 ? this.getTotalDuration() / this.totalTests : 0;
    }
    
    // Logging Methods
    logInfo(message) {
        console.log(`[Frontend Switch Test] ${message}`);
    }
    
    logSuccess(message) {
        console.log(`%c[Frontend Switch Test] ${message}`, 'color: green; font-weight: bold;');
    }
    
    logWarn(message) {
        console.warn(`[Frontend Switch Test] ${message}`);
    }
    
    logError(message) {
        console.error(`[Frontend Switch Test] ${message}`);
    }
}

// Initialize and export
window.FrontendSwitchingTestSuite = FrontendSwitchingTestSuite;

// Auto-run tests if in test mode
if (window.location.search.includes('run_frontend_tests=1')) {
    $(document).ready(() => {
        setTimeout(() => {
            const testSuite = new FrontendSwitchingTestSuite();
            testSuite.runAllTests().catch(console.error);
        }, 2000);
    });
}

// Export for manual testing
window.runFrontendSwitchingTests = () => {
    const testSuite = new FrontendSwitchingTestSuite();
    return testSuite.runAllTests();
};

console.log('Frontend Switching Test Suite loaded. Run tests with: runFrontendSwitchingTests()');