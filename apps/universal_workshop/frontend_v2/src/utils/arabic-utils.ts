/**
 * Arabic Utilities - Universal Workshop Frontend V2
 * 
 * Re-exports Arabic utilities for consistent access
 */

// Re-export from localization module
export { ArabicUtils } from '@/localization/arabic/arabic-utils'
export { ArabicFormatter } from '@/localization/arabic/arabic-formatter'
export { RTLManager } from '@/localization/arabic/rtl-manager'

// Additional utility functions
export const formatArabicDate = (date: Date): string => {
  return new Intl.DateTimeFormat('ar-OM', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  }).format(date)
}

export const formatArabicNumber = (num: number): string => {
  return new Intl.NumberFormat('ar-OM', {
    useGrouping: true
  }).format(num)
}

export const formatArabicCurrency = (amount: number): string => {
  return new Intl.NumberFormat('ar-OM', {
    style: 'currency',
    currency: 'OMR'
  }).format(amount)
}

export const isRTLDirection = (): boolean => {
  return document.documentElement.dir === 'rtl' || 
         document.documentElement.lang === 'ar'
}