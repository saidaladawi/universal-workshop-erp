/**
 * Arabic Utilities - Universal Workshop Frontend V2
 * 
 * Comprehensive Arabic language support including RTL layout,
 * number formatting, text direction detection, and localization helpers.
 */

import type { Direction, Language } from '@/types/workshop'

export class ArabicUtils {
  private static readonly ARABIC_NUMERALS = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩']
  private static readonly LATIN_NUMERALS = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
  
  private static readonly ARABIC_UNICODE_RANGES = [
    [0x0600, 0x06FF], // Arabic
    [0x0750, 0x077F], // Arabic Supplement
    [0x08A0, 0x08FF], // Arabic Extended-A
    [0xFB50, 0xFDFF], // Arabic Presentation Forms-A
    [0xFE70, 0xFEFF], // Arabic Presentation Forms-B
  ]

  /**
   * Convert Latin numerals to Arabic numerals
   */
  static convertToArabicNumerals(text: string): string {
    return text.replace(/[0-9]/g, (digit) => 
      this.ARABIC_NUMERALS[parseInt(digit, 10)]
    )
  }

  /**
   * Convert Arabic numerals to Latin numerals
   */
  static convertToLatinNumerals(text: string): string {
    return text.replace(/[٠-٩]/g, (digit) => 
      this.LATIN_NUMERALS[this.ARABIC_NUMERALS.indexOf(digit)]
    )
  }

  /**
   * Detect if text contains Arabic characters
   */
  static containsArabic(text: string): boolean {
    return this.ARABIC_UNICODE_RANGES.some(([start, end]) => {
      for (let i = 0; i < text.length; i++) {
        const charCode = text.charCodeAt(i)
        if (charCode >= start && charCode <= end) {
          return true
        }
      }
      return false
    })
  }

  /**
   * Detect text direction based on content
   */
  static getTextDirection(text: string): Direction {
    if (!text || text.trim().length === 0) {
      return 'ltr'
    }

    return this.containsArabic(text) ? 'rtl' : 'ltr'
  }

  /**
   * Check if current locale is Arabic
   */
  static isArabicLocale(locale?: string): boolean {
    const currentLocale = locale || 
      document.documentElement.lang || 
      navigator.language || 
      'en'
    
    return currentLocale.toLowerCase().startsWith('ar')
  }

  /**
   * Format number according to Arabic locale
   */
  static formatNumber(
    number: number, 
    options: {
      useArabicNumerals?: boolean
      currency?: string
      style?: 'decimal' | 'currency' | 'percent'
      minimumFractionDigits?: number
      maximumFractionDigits?: number
    } = {}
  ): string {
    const {
      useArabicNumerals = true,
      currency = 'OMR',
      style = 'decimal',
      minimumFractionDigits,
      maximumFractionDigits
    } = options

    let formatted: string

    if (style === 'currency') {
      formatted = new Intl.NumberFormat('ar-OM', {
        style: 'currency',
        currency,
        minimumFractionDigits,
        maximumFractionDigits
      }).format(number)
    } else if (style === 'percent') {
      formatted = new Intl.NumberFormat('ar-OM', {
        style: 'percent',
        minimumFractionDigits,
        maximumFractionDigits
      }).format(number)
    } else {
      formatted = new Intl.NumberFormat('ar-OM', {
        minimumFractionDigits,
        maximumFractionDigits
      }).format(number)
    }

    return useArabicNumerals ? this.convertToArabicNumerals(formatted) : formatted
  }

  /**
   * Format currency for Omani market
   */
  static formatCurrency(
    amount: number,
    options: {
      useArabicNumerals?: boolean
      showCurrencySymbol?: boolean
      precision?: number
    } = {}
  ): string {
    const {
      useArabicNumerals = true,
      showCurrencySymbol = true,
      precision = 3
    } = options

    const formatted = this.formatNumber(amount, {
      style: showCurrencySymbol ? 'currency' : 'decimal',
      currency: 'OMR',
      minimumFractionDigits: precision,
      maximumFractionDigits: precision,
      useArabicNumerals
    })

    return formatted
  }

  /**
   * Format date according to Arabic locale
   */
  static formatDate(
    date: Date,
    options: {
      style?: 'short' | 'medium' | 'long' | 'full'
      useArabicNumerals?: boolean
      includeTime?: boolean
    } = {}
  ): string {
    const {
      style = 'medium',
      useArabicNumerals = true,
      includeTime = false
    } = options

    const formatOptions: Intl.DateTimeFormatOptions = {
      dateStyle: style as any
    }

    if (includeTime) {
      formatOptions.timeStyle = 'short'
    }

    let formatted = new Intl.DateTimeFormat('ar-OM', formatOptions).format(date)

    return useArabicNumerals ? this.convertToArabicNumerals(formatted) : formatted
  }

  /**
   * Apply RTL styling to element
   */
  static applyRTLStyling(element: HTMLElement): void {
    element.dir = 'rtl'
    element.style.textAlign = 'right'
    element.classList.add('rtl-element')
  }

  /**
   * Remove RTL styling from element
   */
  static removeRTLStyling(element: HTMLElement): void {
    element.dir = 'ltr'
    element.style.textAlign = 'left'
    element.classList.remove('rtl-element')
  }

  /**
   * Auto-detect and apply text direction to element
   */
  static autoApplyDirection(element: HTMLElement, text?: string): void {
    const textToAnalyze = text || element.textContent || element.innerText || ''
    const direction = this.getTextDirection(textToAnalyze)
    
    element.dir = direction
    element.style.textAlign = direction === 'rtl' ? 'right' : 'left'
  }

  /**
   * Get plural form for Arabic text
   */
  static getArabicPlural(
    count: number,
    singular: string,
    dual?: string,
    plural?: string
  ): string {
    if (count === 0) {
      return plural || singular
    } else if (count === 1) {
      return singular
    } else if (count === 2 && dual) {
      return dual
    } else {
      return plural || singular
    }
  }

  /**
   * Validate Arabic text input
   */
  static isValidArabicText(text: string): boolean {
    if (!text || text.trim().length === 0) {
      return false
    }

    // Check if text contains valid Arabic characters
    const hasArabic = this.containsArabic(text)
    
    // Allow numbers, spaces, and basic punctuation
    const allowedPattern = /^[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF\s\d\.\,\!\?\-\(\)]+$/
    
    return hasArabic && allowedPattern.test(text)
  }

  /**
   * Clean Arabic text by removing unwanted characters
   */
  static cleanArabicText(text: string): string {
    return text
      .replace(/[\u200C\u200D\u200E\u200F]/g, '') // Remove invisible characters
      .replace(/\s+/g, ' ') // Normalize whitespace
      .trim()
  }

  /**
   * Get RTL-aware padding/margin values
   */
  static getRTLSpacing(
    top: string,
    right: string,
    bottom: string,
    left: string,
    isRTL: boolean = false
  ): string {
    if (isRTL) {
      return `${top} ${left} ${bottom} ${right}`
    }
    return `${top} ${right} ${bottom} ${left}`
  }

  /**
   * Convert CSS property for RTL
   */
  static convertCSSForRTL(property: string, value: string, isRTL: boolean = false): { property: string; value: string } {
    if (!isRTL) {
      return { property, value }
    }

    // Handle directional properties
    const rtlMappings: Record<string, string> = {
      'padding-left': 'padding-right',
      'padding-right': 'padding-left',
      'margin-left': 'margin-right',
      'margin-right': 'margin-left',
      'border-left': 'border-right',
      'border-right': 'border-left',
      'left': 'right',
      'right': 'left',
      'text-align': value === 'left' ? 'right' : value === 'right' ? 'left' : value
    }

    const mappedProperty = rtlMappings[property] || property
    const mappedValue = property === 'text-align' ? rtlMappings[property] : value

    return { 
      property: mappedProperty, 
      value: mappedValue || value 
    }
  }

  /**
   * Setup global Arabic environment
   */
  static setupGlobalArabicEnvironment(): void {
    const isArabic = this.isArabicLocale()
    
    if (isArabic) {
      document.documentElement.dir = 'rtl'
      document.documentElement.lang = 'ar'
      document.documentElement.classList.add('arabic-layout')
      
      // Add RTL stylesheet if it exists
      const rtlLink = document.createElement('link')
      rtlLink.rel = 'stylesheet'
      rtlLink.href = '/assets/universal_workshop/css/arabic-rtl.css'
      rtlLink.onload = () => console.log('✅ Arabic RTL styles loaded')
      rtlLink.onerror = () => console.log('⚠️ Arabic RTL styles not found')
      document.head.appendChild(rtlLink)
    }
  }

  /**
   * Create bilingual text element
   */
  static createBilingualElement(
    englishText: string,
    arabicText: string,
    preferArabic: boolean = false
  ): HTMLElement {
    const container = document.createElement('div')
    container.className = 'bilingual-text'
    
    const enElement = document.createElement('span')
    enElement.className = 'text-en'
    enElement.textContent = englishText
    enElement.dir = 'ltr'
    
    const arElement = document.createElement('span')
    arElement.className = 'text-ar'
    arElement.textContent = arabicText
    arElement.dir = 'rtl'
    
    if (preferArabic) {
      container.appendChild(arElement)
      container.appendChild(enElement)
    } else {
      container.appendChild(enElement)
      container.appendChild(arElement)
    }
    
    return container
  }
}

export default ArabicUtils