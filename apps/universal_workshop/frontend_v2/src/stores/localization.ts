/**
 * Localization Store - Universal Workshop Frontend V2
 *
 * Manages Arabic/English localization, RTL layout, and cultural preferences
 * for the Omani automotive workshop environment.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface LocalizationState {
    currentLocale: 'ar' | 'en'
    preferArabic: boolean
    isRTL: boolean
    arabicNumbers: boolean
    hijriCalendar: boolean
    currency: 'OMR' | 'USD'
    dateFormat: 'DD/MM/YYYY' | 'MM/DD/YYYY' | 'arabic'
    timeFormat: '12h' | '24h'
}

export interface CulturalSettings {
    formalArabic: boolean
    dialectSupport: boolean
    culturalColors: boolean
    arabicFont: 'noto' | 'amiri' | 'cairo'
}

export const useLocalizationStore = defineStore('localization', () => {
    // Core localization state
    const currentLocale = ref<'ar' | 'en'>('ar')
    const preferArabic = ref<boolean>(true)
    const isRTL = ref<boolean>(true)
    const arabicNumbers = ref<boolean>(true)
    const hijriCalendar = ref<boolean>(false)
    const currency = ref<'OMR' | 'USD'>('OMR')
    const dateFormat = ref<'DD/MM/YYYY' | 'MM/DD/YYYY' | 'arabic'>('DD/MM/YYYY')
    const timeFormat = ref<'12h' | '24h'>('24h')

    // Cultural settings
    const formalArabic = ref<boolean>(true)
    const dialectSupport = ref<boolean>(true)
    const culturalColors = ref<boolean>(true)
    const arabicFont = ref<'noto' | 'amiri' | 'cairo'>('noto')

    // Translation cache
    const translations = ref<Record<string, Record<string, string>>>({})
    const loadedLanguages = ref<Set<string>>(new Set())

    // Computed getters
    const localizationState = computed<LocalizationState>(() => ({
        currentLocale: currentLocale.value,
        preferArabic: preferArabic.value,
        isRTL: isRTL.value,
        arabicNumbers: arabicNumbers.value,
        hijriCalendar: hijriCalendar.value,
        currency: currency.value,
        dateFormat: dateFormat.value,
        timeFormat: timeFormat.value
    }))

    const culturalSettings = computed<CulturalSettings>(() => ({
        formalArabic: formalArabic.value,
        dialectSupport: dialectSupport.value,
        culturalColors: culturalColors.value,
        arabicFont: arabicFont.value
    }))

    const directionality = computed(() => isRTL.value ? 'rtl' : 'ltr')

    // Translation methods
    const t = (key: string, fallback?: string): string => {
        const locale = currentLocale.value
        return translations.value[locale]?.[key] || fallback || key
    }

    const setLocale = async (locale: 'ar' | 'en') => {
        currentLocale.value = locale
        preferArabic.value = locale === 'ar'
        isRTL.value = locale === 'ar'

        // Load translations if not already loaded
        if (!loadedLanguages.value.has(locale)) {
            await loadTranslations(locale)
        }

        // Update document direction
        document.documentElement.dir = isRTL.value ? 'rtl' : 'ltr'
        document.documentElement.lang = locale
    }

    const loadTranslations = async (locale: string) => {
        try {
            // Load translation files dynamically
            const translationModule = await import(`@/localization/${locale}.json`)

            if (!translations.value[locale]) {
                translations.value[locale] = {}
            }

            Object.assign(translations.value[locale], translationModule.default)
            loadedLanguages.value.add(locale)
        } catch (error) {
            console.warn(`Failed to load translations for ${locale}:`, error)
        }
    }

    // Number formatting
    const formatNumber = (value: number, options?: Intl.NumberFormatOptions): string => {
        const locale = arabicNumbers.value ? 'ar-SA' : 'en-US'
        return new Intl.NumberFormat(locale, options).format(value)
    }

    const formatCurrency = (value: number): string => {
        const locale = arabicNumbers.value ? 'ar-OM' : 'en-OM'
        return new Intl.NumberFormat(locale, {
            style: 'currency',
            currency: currency.value,
            minimumFractionDigits: 3,
            maximumFractionDigits: 3
        }).format(value)
    }

    // Date formatting
    const formatDate = (date: Date, format?: string): string => {
        const locale = currentLocale.value === 'ar' ? 'ar-OM' : 'en-OM'
        const formatStr = format || dateFormat.value

        if (formatStr === 'arabic') {
            return new Intl.DateTimeFormat(locale, {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                calendar: hijriCalendar.value ? 'islamic-umalqura' : 'gregory'
            }).format(date)
        }

        return new Intl.DateTimeFormat(locale, {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit'
        }).format(date)
    }

    const formatTime = (date: Date): string => {
        const locale = currentLocale.value === 'ar' ? 'ar-OM' : 'en-OM'
        return new Intl.DateTimeFormat(locale, {
            hour: '2-digit',
            minute: '2-digit',
            hour12: timeFormat.value === '12h'
        }).format(date)
    }

    // Cultural helpers
    const getTextDirection = (text: string): 'ltr' | 'rtl' => {
        const arabicRegex = /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]/
        return arabicRegex.test(text) ? 'rtl' : 'ltr'
    }

    const isArabicText = (text: string): boolean => {
        const arabicRegex = /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]/
        return arabicRegex.test(text)
    }

    // Settings persistence
    const saveSettings = () => {
        const settings = {
            currentLocale: currentLocale.value,
            preferArabic: preferArabic.value,
            isRTL: isRTL.value,
            arabicNumbers: arabicNumbers.value,
            hijriCalendar: hijriCalendar.value,
            currency: currency.value,
            dateFormat: dateFormat.value,
            timeFormat: timeFormat.value,
            formalArabic: formalArabic.value,
            dialectSupport: dialectSupport.value,
            culturalColors: culturalColors.value,
            arabicFont: arabicFont.value
        }

        localStorage.setItem('workshop_localization', JSON.stringify(settings))
    }

    const loadSettings = () => {
        try {
            const saved = localStorage.getItem('workshop_localization')
            if (saved) {
                const settings = JSON.parse(saved)

                currentLocale.value = settings.currentLocale || 'ar'
                preferArabic.value = settings.preferArabic ?? true
                isRTL.value = settings.isRTL ?? true
                arabicNumbers.value = settings.arabicNumbers ?? true
                hijriCalendar.value = settings.hijriCalendar ?? false
                currency.value = settings.currency || 'OMR'
                dateFormat.value = settings.dateFormat || 'DD/MM/YYYY'
                timeFormat.value = settings.timeFormat || '24h'
                formalArabic.value = settings.formalArabic ?? true
                dialectSupport.value = settings.dialectSupport ?? true
                culturalColors.value = settings.culturalColors ?? true
                arabicFont.value = settings.arabicFont || 'noto'
            }
        } catch (error) {
            console.warn('Failed to load localization settings:', error)
        }
    }

    // Initialize
    const initialize = async () => {
        loadSettings()
        await setLocale(currentLocale.value)
    }

    return {
        // State
        currentLocale,
        preferArabic,
        isRTL,
        arabicNumbers,
        hijriCalendar,
        currency,
        dateFormat,
        timeFormat,
        formalArabic,
        dialectSupport,
        culturalColors,
        arabicFont,

        // Computed
        localizationState,
        culturalSettings,
        directionality,

        // Methods
        t,
        setLocale,
        loadTranslations,
        formatNumber,
        formatCurrency,
        formatDate,
        formatTime,
        getTextDirection,
        isArabicText,
        saveSettings,
        loadSettings,
        initialize
    }
})
