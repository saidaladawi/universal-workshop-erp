/**
 * Analytics Module Exports - Universal Workshop Frontend V2
 * 
 * Comprehensive real-time analytics system with Arabic/RTL support,
 * KPI widgets, dashboard components, and business intelligence features.
 */

// Core Analytics Engine
export { RealTimeAnalyticsEngine, analyticsEngine } from './RealTimeAnalyticsEngine'

// Dashboard Components
export { default as AnalyticsDashboard } from './AnalyticsDashboard.vue'
export { default as KPIWidget } from './KPIWidget.vue'

// Type Definitions
export type {
  KPIMetric,
  AnalyticsReport,
  PredictiveAlert
} from './RealTimeAnalyticsEngine'

export type {
  KPIWidgetProps,
  KPIWidgetEmits
} from './KPIWidget.vue'

export type {
  AnalyticsDashboardProps
} from './AnalyticsDashboard.vue'

// Analytics Utilities
export const ANALYTICS_CONFIG = {
  UPDATE_INTERVAL: 30000, // 30 seconds
  WEBSOCKET_URL: 'ws://localhost:8080/analytics',
  CACHE_DURATION: 300000, // 5 minutes
  MAX_METRICS_CACHE: 100,
  MAX_ALERTS_CACHE: 50
} as const

// KPI Categories
export const KPI_CATEGORIES = {
  EFFICIENCY: 'efficiency',
  QUALITY: 'quality', 
  FINANCIAL: 'financial',
  CUSTOMER: 'customer'
} as const

// Alert Severities
export const ALERT_SEVERITIES = {
  CRITICAL: 'critical',
  HIGH: 'high',
  MEDIUM: 'medium',
  LOW: 'low'
} as const

// Arabic Translations
export const ANALYTICS_TRANSLATIONS = {
  dashboard: {
    en: 'Analytics Dashboard',
    ar: 'لوحة التحليلات'
  },
  realTime: {
    en: 'Real-time workshop analytics',
    ar: 'تحليلات الورشة في الوقت الفعلي'
  },
  kpis: {
    en: 'Key Performance Indicators',
    ar: 'مؤشرات الأداء الرئيسية'
  },
  alerts: {
    en: 'Predictive Alerts',
    ar: 'التنبيهات التنبؤية'
  },
  reports: {
    en: 'Quick Reports',
    ar: 'التقارير السريعة'
  },
  disconnected: {
    en: 'Disconnected',
    ar: 'غير متصل'
  },
  lastUpdated: {
    en: 'Updated',
    ar: 'آخر تحديث'
  },
  target: {
    en: 'Target',
    ar: 'الهدف'
  },
  trend: {
    en: 'vs previous period',
    ar: 'مقارنة بالفترة السابقة'
  }
} as const

// Helper Functions
export const formatArabicNumber = (value: number, preferArabic: boolean = false): string => {
  return preferArabic ? value.toLocaleString('ar-SA') : value.toLocaleString('en-US')
}

export const formatArabicCurrency = (amount: number, preferArabic: boolean = false): string => {
  return new Intl.NumberFormat(preferArabic ? 'ar-SA' : 'en-OM', {
    style: 'currency',
    currency: 'OMR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 2
  }).format(amount)
}

export const formatArabicPercentage = (value: number, preferArabic: boolean = false): string => {
  return new Intl.NumberFormat(preferArabic ? 'ar-SA' : 'en-OM', {
    style: 'percent',
    minimumFractionDigits: 1,
    maximumFractionDigits: 1
  }).format(value / 100)
}

export const getKPICategoryColor = (category: string): string => {
  const colorMap = {
    efficiency: 'var(--color-primary)',
    quality: 'var(--color-success)', 
    financial: 'var(--color-warning)',
    customer: 'var(--color-info)'
  }
  return colorMap[category as keyof typeof colorMap] || 'var(--color-text-secondary)'
}

export const getAlertSeverityColor = (severity: string): string => {
  const colorMap = {
    critical: 'var(--color-error)',
    high: 'var(--color-warning)', 
    medium: 'var(--color-info)',
    low: 'var(--color-text-secondary)'
  }
  return colorMap[severity as keyof typeof colorMap] || 'var(--color-text-secondary)'
}

export const getTrendIcon = (trend: 'up' | 'down' | 'stable'): string => {
  const iconMap = {
    up: 'trending-up',
    down: 'trending-down',
    stable: 'minus'
  }
  return iconMap[trend] || 'minus'
}

export const getTrendColor = (trend: 'up' | 'down' | 'stable'): string => {
  const colorMap = {
    up: 'var(--color-success)',
    down: 'var(--color-error)', 
    stable: 'var(--color-text-secondary)'
  }
  return colorMap[trend] || 'var(--color-text-secondary)'
}

// Analytics Module Metadata
export const ANALYTICS_MODULE = {
  name: 'Analytics',
  nameAr: 'التحليلات',
  version: '1.0.0',
  description: 'Real-time analytics and business intelligence for Universal Workshop',
  descriptionAr: 'التحليلات في الوقت الفعلي وذكاء الأعمال للورشة الشاملة',
  features: [
    'Real-time KPI monitoring',
    'Predictive maintenance alerts', 
    'Arabic business reports',
    'Customer satisfaction tracking',
    'Revenue optimization insights'
  ],
  featuresAr: [
    'مراقبة مؤشرات الأداء في الوقت الفعلي',
    'تنبيهات الصيانة التنبؤية',
    'تقارير الأعمال باللغة العربية', 
    'تتبع رضا العملاء',
    'رؤى تحسين الإيرادات'
  ]
} as const