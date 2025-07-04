/**
 * Utilities Index - Universal Workshop Frontend V2
 * 
 * Central export point for all utility functions and systems.
 */

// Core utilities
export * from './feature-flags'
export * from './performance'

// Re-export commonly used utilities
export { featureFlags, isFeatureEnabled, getEnabledFeatures } from './feature-flags'
export { 
  performanceTester, 
  startPerformanceMonitoring, 
  stopPerformanceMonitoring, 
  runPerformanceTests,
  recordComponentMetric 
} from './performance'

// Types
export type { FeatureFlagConfig, FeatureFlagRules } from './feature-flags'
export type { 
  PerformanceMetric, 
  PerformanceBenchmark, 
  PerformanceReport 
} from './performance'

export default {
  featureFlags,
  performanceTester,
  isFeatureEnabled,
  getEnabledFeatures,
  startPerformanceMonitoring,
  stopPerformanceMonitoring,
  runPerformanceTests,
  recordComponentMetric
}