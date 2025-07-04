/**
 * Arabic Business Logic Engine - Universal Workshop Frontend V2
 * 
 * Advanced Arabic text processing for business contexts including
 * number formatting, calendar conversion, and currency handling.
 */

export interface BusinessContext {
  type: 'currency' | 'invoice_number' | 'quantity' | 'date' | 'address'
  showBothFormats?: boolean
  precision?: number
  locale?: string
}

export interface ArabicCurrencyOptions {
  currency: string
  locale: string
  showBoth: boolean
}

export interface FormattedAddress {
  arabic: string
  english: string
  combined: string
}

export interface Address {
  building?: string
  street?: string
  area?: string
  wilayat?: string
  governorate?: string
  postalCode?: string
}

export class ArabicNumberConverter {
  private static readonly ARABIC_NUMERALS = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩']
  private static readonly WESTERN_NUMERALS = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

  toArabic(value: number | string): string {
    return String(value).replace(/[0-9]/g, (digit) => 
      ArabicNumberConverter.ARABIC_NUMERALS[parseInt(digit, 10)]
    )
  }

  toWestern(arabicValue: string): string {
    return arabicValue.replace(/[٠-٩]/g, (digit) => {
      const index = ArabicNumberConverter.ARABIC_NUMERALS.indexOf(digit)
      return index !== -1 ? ArabicNumberConverter.WESTERN_NUMERALS[index] : digit
    })
  }

  formatWithSeparators(value: number, useArabicNumerals: boolean = false): string {
    const formatted = new Intl.NumberFormat('ar-OM').format(value)
    return useArabicNumerals ? this.toArabic(formatted) : formatted
  }
}

export class HijriCalendarConverter {
  private hijriMonths = [
    'محرم', 'صفر', 'ربيع الأول', 'ربيع الثاني', 'جمادى الأولى', 'جمادى الثانية',
    'رجب', 'شعبان', 'رمضان', 'شوال', 'ذو القعدة', 'ذو الحجة'
  ]

  gregorianToHijri(gregorianDate: Date): { year: number; month: number; day: number; monthName: string } {
    // Simplified conversion - in production use proper Hijri calendar library
    const hijriYear = gregorianDate.getFullYear() - 622
    const hijriMonth = (gregorianDate.getMonth() + 1) % 12 || 12
    const hijriDay = gregorianDate.getDate()

    return {
      year: hijriYear,
      month: hijriMonth,
      day: hijriDay,
      monthName: this.hijriMonths[hijriMonth - 1]
    }
  }

  formatHijriDate(hijriDate: { year: number; month: number; day: number; monthName: string }): string {
    return `${hijriDate.day} ${hijriDate.monthName} ${hijriDate.year} هـ`
  }
}

export class ArabicCurrencyFormatter {
  format(value: number, options: ArabicCurrencyOptions): string {
    const omrFormatter = new Intl.NumberFormat('ar-OM', {
      style: 'currency',
      currency: 'OMR',
      minimumFractionDigits: 3,
      maximumFractionDigits: 3
    })

    const arabicFormatted = omrFormatter.format(value)
    
    if (options.showBoth) {
      const englishFormatted = new Intl.NumberFormat('en-OM', {
        style: 'currency',
        currency: 'OMR',
        minimumFractionDigits: 3,
        maximumFractionDigits: 3
      }).format(value)
      
      return `${arabicFormatted} (${englishFormatted})`
    }

    return arabicFormatted
  }

  formatBaisa(value: number): string {
    // Convert OMR to Baisa (1 OMR = 1000 Baisa)
    const baisaValue = Math.round(value * 1000)
    return `${baisaValue} بيسة`
  }
}

export class ArabicBusinessEngine {
  private arabicNumberConverter: ArabicNumberConverter
  private calendarConverter: HijriCalendarConverter
  private currencyFormatter: ArabicCurrencyFormatter

  constructor() {
    this.arabicNumberConverter = new ArabicNumberConverter()
    this.calendarConverter = new HijriCalendarConverter()
    this.currencyFormatter = new ArabicCurrencyFormatter()
  }

  // Convert between Arabic and Western numerals with business context
  formatBusinessNumber(value: number, context: BusinessContext): string {
    switch (context.type) {
      case 'currency':
        return this.currencyFormatter.format(value, {
          currency: 'OMR',
          locale: 'ar-OM',
          showBoth: context.showBothFormats || false
        })
      
      case 'invoice_number':
        // Invoices typically use Western numerals even in Arabic
        return value.toString()
      
      case 'quantity':
        // Quantities can use Arabic numerals for display
        return this.arabicNumberConverter.formatWithSeparators(value, true)
      
      default:
        return this.arabicNumberConverter.formatWithSeparators(value)
    }
  }

  // Handle Arabic date formatting with Hijri calendar support
  formatDate(date: Date, format: 'gregorian' | 'hijri' | 'both' = 'gregorian', showHijri: boolean = false): string {
    const gregorianDate = date.toLocaleDateString('ar-SA', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      weekday: 'long'
    })

    if (format === 'gregorian') {
      return gregorianDate
    }

    const hijriDate = this.calendarConverter.gregorianToHijri(date)
    const hijriFormatted = this.calendarConverter.formatHijriDate(hijriDate)

    if (format === 'hijri') {
      return hijriFormatted
    }

    // Both formats
    return `${gregorianDate} - ${hijriFormatted}`
  }

  // Arabic address formatting for Omani context
  formatOmaniAddress(address: Address): FormattedAddress {
    const arabicAddress = this.formatAddressArabic(address)
    const englishAddress = this.formatAddressEnglish(address)
    
    return {
      arabic: arabicAddress,
      english: englishAddress,
      combined: `${arabicAddress}\n${englishAddress}`
    }
  }

  private formatAddressArabic(address: Address): string {
    const parts: string[] = []
    
    if (address.building) parts.push(`مبنى ${address.building}`)
    if (address.street) parts.push(`شارع ${address.street}`)
    if (address.area) parts.push(`منطقة ${address.area}`)
    if (address.wilayat) parts.push(`ولاية ${address.wilayat}`)
    if (address.governorate) parts.push(`محافظة ${address.governorate}`)
    if (address.postalCode) parts.push(`ص.ب ${address.postalCode}`)
    
    return parts.join('، ')
  }

  private formatAddressEnglish(address: Address): string {
    const parts: string[] = []
    
    if (address.building) parts.push(`Building ${address.building}`)
    if (address.street) parts.push(`${address.street} Street`)
    if (address.area) parts.push(`${address.area}`)
    if (address.wilayat) parts.push(`${address.wilayat} Wilayat`)
    if (address.governorate) parts.push(`${address.governorate} Governorate`)
    if (address.postalCode) parts.push(`P.O. Box ${address.postalCode}`)
    
    return parts.join(', ')
  }

  // Format Arabic text for business documents
  formatBusinessText(text: string, context: 'formal' | 'informal' = 'formal'): string {
    // Remove extra spaces and normalize text
    let formatted = text.trim().replace(/\s+/g, ' ')
    
    // Add proper Arabic punctuation
    formatted = formatted.replace(/\./g, '.')
    formatted = formatted.replace(/,/g, '،')
    formatted = formatted.replace(/;/g, '؛')
    formatted = formatted.replace(/\?/g, '؟')
    
    // Ensure proper text direction markers
    if (this.containsArabicText(formatted)) {
      formatted = '\u202D' + formatted + '\u202C' // Right-to-left override
    }
    
    return formatted
  }

  // Validate Arabic business data
  validateArabicBusinessData(data: any): { isValid: boolean; errors: string[] } {
    const errors: string[] = []
    
    // Validate Arabic text fields
    if (data.nameAr && !this.isValidArabicName(data.nameAr)) {
      errors.push('اسم غير صالح باللغة العربية')
    }
    
    // Validate Omani phone numbers
    if (data.phone && !this.isValidOmaniPhone(data.phone)) {
      errors.push('رقم هاتف عماني غير صالح')
    }
    
    // Validate Omani civil ID
    if (data.civilId && !this.isValidOmaniCivilId(data.civilId)) {
      errors.push('رقم هوية مدنية عمانية غير صالح')
    }
    
    return {
      isValid: errors.length === 0,
      errors
    }
  }

  private containsArabicText(text: string): boolean {
    const arabicRegex = /[\u0600-\u06FF\u0750-\u077F]/
    return arabicRegex.test(text)
  }

  private isValidArabicName(name: string): boolean {
    // Arabic names should contain only Arabic characters and spaces
    const arabicNameRegex = /^[\u0600-\u06FF\s]+$/
    return arabicNameRegex.test(name.trim())
  }

  private isValidOmaniPhone(phone: string): boolean {
    // Omani phone numbers: +968 XXXXXXXX or 968 XXXXXXXX or XXXXXXXX
    const omaniPhoneRegex = /^(\+968|968)?[79]\d{7}$/
    return omaniPhoneRegex.test(phone.replace(/\s+/g, ''))
  }

  private isValidOmaniCivilId(civilId: string): boolean {
    // Omani Civil ID format: 8 digits
    const civilIdRegex = /^\d{8}$/
    return civilIdRegex.test(civilId.replace(/\s+/g, ''))
  }

  // Generate Arabic invoice numbers with proper formatting
  generateArabicInvoiceNumber(prefix: string, sequenceNumber: number, year: number): string {
    const arabicYear = this.arabicNumberConverter.toArabic(year)
    const arabicSequence = this.arabicNumberConverter.toArabic(sequenceNumber.toString().padStart(6, '0'))
    
    return `${prefix}-${arabicYear}-${arabicSequence}`
  }

  // Convert Arabic amount to words (for checks and invoices)
  convertAmountToArabicWords(amount: number): string {
    // This is a simplified version - full implementation would handle all Arabic number words
    const ones = ['', 'واحد', 'اثنان', 'ثلاثة', 'أربعة', 'خمسة', 'ستة', 'سبعة', 'ثمانية', 'تسعة']
    const tens = ['', '', 'عشرون', 'ثلاثون', 'أربعون', 'خمسون', 'ستون', 'سبعون', 'ثمانون', 'تسعون']
    
    // Convert the integer part
    const integerPart = Math.floor(amount)
    const decimalPart = Math.round((amount - integerPart) * 1000) // For 3 decimal places (Baisa)
    
    let result = this.convertIntegerToArabicWords(integerPart)
    
    if (integerPart === 1) {
      result += ' ريال عماني'
    } else {
      result += ' ريال عماني'
    }
    
    if (decimalPart > 0) {
      result += ' و ' + this.convertIntegerToArabicWords(decimalPart) + ' بيسة'
    }
    
    return result
  }

  private convertIntegerToArabicWords(num: number): string {
    // Simplified implementation for demo purposes
    // Full implementation would handle all Arabic number rules
    if (num === 0) return 'صفر'
    if (num === 1) return 'واحد'
    if (num === 2) return 'اثنان'
    // ... add more number conversions
    
    return num.toString() // Fallback to digits
  }
}
