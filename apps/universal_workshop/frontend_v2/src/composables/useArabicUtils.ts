/**
 * Arabic Utilities Composable
 * Provides reactive utilities for Arabic/RTL support
 */

import { computed } from 'vue'

export function useArabicUtils() {
  // Check if current locale is RTL
  const isRTL = computed(() => {
    if (typeof window === 'undefined') return false
    
    // Check document direction
    const docDir = document.documentElement.dir
    if (docDir === 'rtl') return true
    
    // Check language
    const lang = document.documentElement.lang || navigator.language
    return lang.startsWith('ar')
  })
  
  // Convert numbers to Arabic numerals
  const toArabicNumerals = (input: string | number): string => {
    const arabicNumerals = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩']
    return input.toString().replace(/[0-9]/g, (digit) => arabicNumerals[parseInt(digit)])
  }
  
  // Convert Arabic numerals to Latin
  const toLatinNumerals = (input: string): string => {
    const arabicNumerals = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩']
    let result = input
    arabicNumerals.forEach((arabic, index) => {
      result = result.replace(new RegExp(arabic, 'g'), index.toString())
    })
    return result
  }
  
  // Check if text contains Arabic characters
  const containsArabic = (text: string): boolean => {
    return /[\u0600-\u06FF]/.test(text)
  }
  
  // Get text direction based on content
  const getTextDirection = (text: string): 'ltr' | 'rtl' => {
    return containsArabic(text) ? 'rtl' : 'ltr'
  }
  
  // Format currency for Arabic/English
  const formatCurrency = (amount: number, currency = 'OMR'): string => {
    if (isRTL.value) {
      const arabicAmount = toArabicNumerals(amount.toFixed(3))
      return `ر.ع. ${arabicAmount}`
    } else {
      return `${currency} ${amount.toFixed(3)}`
    }
  }
  
  // Format date for Arabic/English
  const formatDate = (date: string | Date, format: 'short' | 'long' = 'short'): string => {
    const dateObj = typeof date === 'string' ? new Date(date) : date
    
    if (isRTL.value) {
      return new Intl.DateTimeFormat('ar-OM', {
        year: 'numeric',
        month: format === 'long' ? 'long' : 'short',
        day: 'numeric'
      }).format(dateObj)
    } else {
      return new Intl.DateTimeFormat('en-OM', {
        year: 'numeric',
        month: format === 'long' ? 'long' : 'short',
        day: 'numeric'
      }).format(dateObj)
    }
  }
  
  return {
    isRTL,
    toArabicNumerals,
    toLatinNumerals,
    containsArabic,
    getTextDirection,
    formatCurrency,
    formatDate
  }
}