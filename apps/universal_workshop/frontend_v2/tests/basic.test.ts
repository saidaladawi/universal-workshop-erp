/**
 * Basic Tests - Universal Workshop Frontend V2
 * 
 * Fundamental tests to verify the build and testing system works
 */

import { describe, it, expect, vi } from 'vitest'
import { ArabicUtils } from '@/localization/arabic/arabic-utils'
import { FeatureFlagManager } from '@/utils/feature-flags'
import { PerformanceMonitor } from '@/utils/performance/monitor'

describe('Arabic Utils', () => {
  it('should convert Latin numerals to Arabic numerals', () => {
    const result = ArabicUtils.convertToArabicNumerals('123')
    expect(result).toBe('١٢٣')
  })

  it('should convert Arabic numerals to Latin numerals', () => {
    const result = ArabicUtils.convertToLatinNumerals('١٢٣')
    expect(result).toBe('123')
  })

  it('should detect Arabic text', () => {
    expect(ArabicUtils.containsArabic('مرحبا')).toBe(true)
    expect(ArabicUtils.containsArabic('Hello')).toBe(false)
  })

  it('should determine text direction', () => {
    expect(ArabicUtils.getTextDirection('مرحبا')).toBe('rtl')
    expect(ArabicUtils.getTextDirection('Hello')).toBe('ltr')
  })
})

describe('Feature Flag Manager', () => {
  it('should create singleton instance', () => {
    const instance1 = FeatureFlagManager.getInstance()
    const instance2 = FeatureFlagManager.getInstance()
    expect(instance1).toBe(instance2)
  })

  it('should return false for disabled features by default', () => {
    const manager = FeatureFlagManager.getInstance()
    expect(manager.isEnabled('newBranding')).toBe(false)
  })

  it('should enable features for session', () => {
    const manager = FeatureFlagManager.getInstance()
    manager.enableFeatureForSession('newBranding')
    expect(manager.isEnabled('newBranding')).toBe(true)
  })
})

describe('Performance Monitor', () => {
  it('should create singleton instance', () => {
    const instance1 = PerformanceMonitor.getInstance()
    const instance2 = PerformanceMonitor.getInstance()
    expect(instance1).toBe(instance2)
  })

  it('should generate performance report', () => {
    const monitor = PerformanceMonitor.getInstance()
    const report = monitor.generateReport()
    
    expect(report).toHaveProperty('totalMetrics')
    expect(report).toHaveProperty('recommendations')
    expect(report).toHaveProperty('generatedAt')
    expect(report.generatedAt).toBeInstanceOf(Date)
  })

  it('should measure component render time', () => {
    const monitor = PerformanceMonitor.getInstance()
    monitor.measureComponentRender('TestComponent', 50)
    
    const metrics = monitor.getCurrentMetrics()
    expect(metrics.length).toBeGreaterThan(0)
    
    const renderMetric = metrics.find(m => m.name === 'component_render_time')
    expect(renderMetric).toBeDefined()
    expect(renderMetric?.value).toBe(50)
  })
})

describe('Build System Integration', () => {
  it('should have TypeScript path aliases working', () => {
    // If this imports without error, path aliases are working
    expect(ArabicUtils).toBeDefined()
    expect(FeatureFlagManager).toBeDefined()
    expect(PerformanceMonitor).toBeDefined()
  })

  it('should have environment variables available', () => {
    // These would be set by Vite in a real environment
    expect(import.meta.env).toBeDefined()
  })
})

describe('Browser Compatibility', () => {
  it('should handle missing Frappe gracefully', () => {
    const originalFrappe = window.frappe
    delete (window as any).frappe
    
    // Should not throw errors
    expect(() => {
      const manager = FeatureFlagManager.getInstance()
      manager.isEnabled('newBranding')
    }).not.toThrow()
    
    // Restore
    window.frappe = originalFrappe
  })

  it('should handle missing localStorage gracefully', () => {
    const originalLocalStorage = window.localStorage
    delete (window as any).localStorage
    
    // Should not throw errors
    expect(() => {
      const manager = FeatureFlagManager.getInstance()
      manager.enableFeatureForSession('newBranding')
    }).not.toThrow()
    
    // Restore
    window.localStorage = originalLocalStorage
  })
})