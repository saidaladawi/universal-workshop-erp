/**
 * Test Setup - Universal Workshop Frontend V2
 * 
 * Global test configuration and setup for Vitest
 */

import { beforeEach, afterEach, vi } from 'vitest'

// Mock global objects
Object.defineProperty(window, 'frappe', {
  value: {
    boot: {
      user: {
        name: 'test-user',
        full_name: 'Test User',
        roles: ['Workshop Manager']
      },
      feature_flags: {}
    },
    call: vi.fn(),
    msgprint: vi.fn(),
    throw: vi.fn()
  },
  writable: true
})

// Mock localStorage
Object.defineProperty(window, 'localStorage', {
  value: {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn()
  },
  writable: true
})

// Mock performance API
Object.defineProperty(window, 'performance', {
  value: {
    now: vi.fn(() => Date.now()),
    getEntriesByType: vi.fn(() => []),
    memory: {
      usedJSHeapSize: 1000000,
      totalJSHeapSize: 2000000,
      jsHeapSizeLimit: 4000000
    }
  },
  writable: true
})

// Reset mocks before each test
beforeEach(() => {
  vi.clearAllMocks()
})

// Cleanup after each test
afterEach(() => {
  vi.clearAllTimers()
})