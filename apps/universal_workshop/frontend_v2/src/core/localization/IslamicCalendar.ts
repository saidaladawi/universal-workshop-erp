/**
 * Islamic Calendar Integration for Universal Workshop ERP
 * Provides Hijri calendar, prayer times, and Islamic holidays integration
 * 
 * Features:
 * - Hijri to Gregorian calendar conversion
 * - Prayer times calculation for Muscat, Oman
 * - Islamic holidays and observances
 * - Cultural business logic integration
 * - Workshop scheduling adaptations
 * - Ramadan and special period handling
 */

import { ref, reactive, computed, onMounted } from 'vue'
import type { Ref } from 'vue'

// Types for Islamic calendar
interface HijriDate {
  year: number
  month: number
  day: number
  monthName: string
  monthNameAr: string
  weekday: string
  weekdayAr: string
  isLeapYear: boolean
}

interface PrayerTimes {
  fajr: string
  sunrise: string
  dhuhr: string
  asr: string
  maghrib: string
  isha: string
  timestamp: number
  location: {
    latitude: number
    longitude: number
    timezone: string
  }
}

interface IslamicHoliday {
  name: string
  nameAr: string
  date: Date
  hijriDate: HijriDate
  type: 'major' | 'minor' | 'observance'
  duration: number // days
  description: string
  descriptionAr: string
  businessImpact: 'closed' | 'reduced_hours' | 'normal'
  workshopRecommendation: string
}

interface RamadanInfo {
  isRamadan: boolean
  ramadanStart: Date
  ramadanEnd: Date
  currentDay: number
  totalDays: number
  specialHours: {
    start: string
    end: string
    breakTime: string
  }
  suhoorTime: string
  iftarTime: string
}

interface CulturalPeriod {
  name: string
  nameAr: string
  start: Date
  end: Date
  type: 'religious' | 'national' | 'cultural'
  businessAdjustments: {
    hours: { start: string; end: string }
    breaks: string[]
    restrictions: string[]
  }
}

class IslamicCalendar {
  // Muscat, Oman coordinates
  private readonly MUSCAT_COORDS = {
    latitude: 23.5859,
    longitude: 58.4059,
    timezone: 'Asia/Muscat'
  }

  // Hijri month names
  private readonly HIJRI_MONTHS = [
    { en: 'Muharram', ar: 'محرم' },
    { en: 'Safar', ar: 'صفر' },
    { en: 'Rabi\' al-awwal', ar: 'ربيع الأول' },
    { en: 'Rabi\' al-thani', ar: 'ربيع الثاني' },
    { en: 'Jumada al-awwal', ar: 'جمادى الأولى' },
    { en: 'Jumada al-thani', ar: 'جمادى الثانية' },
    { en: 'Rajab', ar: 'رجب' },
    { en: 'Sha\'ban', ar: 'شعبان' },
    { en: 'Ramadan', ar: 'رمضان' },
    { en: 'Shawwal', ar: 'شوال' },
    { en: 'Dhu al-Qi\'dah', ar: 'ذو القعدة' },
    { en: 'Dhu al-Hijjah', ar: 'ذو الحجة' }
  ]

  // Islamic weekdays
  private readonly WEEKDAYS = [
    { en: 'Sunday', ar: 'الأحد' },
    { en: 'Monday', ar: 'الإثنين' },
    { en: 'Tuesday', ar: 'الثلاثاء' },
    { en: 'Wednesday', ar: 'الأربعاء' },
    { en: 'Thursday', ar: 'الخميس' },
    { en: 'Friday', ar: 'الجمعة' },
    { en: 'Saturday', ar: 'السبت' }
  ]

  constructor() {
    this.initializeCalendar()
  }

  private initializeCalendar() {
    console.log('Islamic Calendar initialized for Muscat, Oman')
  }

  /**
   * Convert Gregorian date to Hijri
   */
  public gregorianToHijri(gregorianDate: Date): HijriDate {
    // Simplified Hijri conversion (in production, use a proper library like moment-hijri)
    const EPOCH = new Date('622-07-16') // Hijri epoch approximation
    const daysSinceEpoch = Math.floor((gregorianDate.getTime() - EPOCH.getTime()) / (1000 * 60 * 60 * 24))
    
    // Average Islamic year is 354.37 days
    const HIJRI_YEAR_DAYS = 354.37
    const year = Math.floor(daysSinceEpoch / HIJRI_YEAR_DAYS) + 1
    
    // Calculate month and day (simplified)
    const dayOfYear = daysSinceEpoch % HIJRI_YEAR_DAYS
    const month = Math.floor(dayOfYear / 29.5) + 1
    const day = Math.floor(dayOfYear % 29.5) + 1

    const monthIndex = Math.min(month - 1, 11)
    const weekdayIndex = gregorianDate.getDay()

    return {
      year,
      month,
      day,
      monthName: this.HIJRI_MONTHS[monthIndex].en,
      monthNameAr: this.HIJRI_MONTHS[monthIndex].ar,
      weekday: this.WEEKDAYS[weekdayIndex].en,
      weekdayAr: this.WEEKDAYS[weekdayIndex].ar,
      isLeapYear: this.isHijriLeapYear(year)
    }
  }

  /**
   * Convert Hijri date to Gregorian
   */
  public hijriToGregorian(hijriYear: number, hijriMonth: number, hijriDay: number): Date {
    // Simplified conversion (use proper library in production)
    const EPOCH = new Date('622-07-16')
    const totalDays = (hijriYear - 1) * 354.37 + (hijriMonth - 1) * 29.5 + hijriDay
    
    return new Date(EPOCH.getTime() + totalDays * 24 * 60 * 60 * 1000)
  }

  /**
   * Check if a Hijri year is a leap year
   */
  private isHijriLeapYear(year: number): boolean {
    // 11-year cycle with leap years at positions 2, 5, 7, 10, 13, 16, 18, 21, 24, 26, 29
    const leapYears = [2, 5, 7, 10, 13, 16, 18, 21, 24, 26, 29]
    const yearInCycle = year % 30
    return leapYears.includes(yearInCycle)
  }

  /**
   * Calculate prayer times for given date and location
   */
  public calculatePrayerTimes(date: Date, coords = this.MUSCAT_COORDS): PrayerTimes {
    const { latitude, longitude, timezone } = coords
    
    // Simplified prayer time calculation
    // In production, use a proper library like prayer-times or similar
    
    const dayOfYear = this.getDayOfYear(date)
    const declinationAngle = 23.45 * Math.sin((360 / 365) * (dayOfYear - 81) * Math.PI / 180)
    const latRad = latitude * Math.PI / 180
    const declRad = declinationAngle * Math.PI / 180
    
    // Calculate sunrise and sunset
    const hourAngle = Math.acos(-Math.tan(latRad) * Math.tan(declRad))
    const sunriseHour = 12 - (hourAngle * 180 / Math.PI) / 15
    const sunsetHour = 12 + (hourAngle * 180 / Math.PI) / 15
    
    // Prayer time calculations (simplified)
    const fajrHour = sunriseHour - 1.5 // 18 degrees before sunrise
    const dhuhrHour = 12 + (longitude / 15) // Solar noon
    const asrHour = dhuhrHour + 4 // Afternoon prayer
    const maghribHour = sunsetHour + 0.15 // Just after sunset
    const ishaHour = sunsetHour + 1.5 // 18 degrees after sunset

    return {
      fajr: this.formatTime(fajrHour),
      sunrise: this.formatTime(sunriseHour),
      dhuhr: this.formatTime(dhuhrHour),
      asr: this.formatTime(asrHour),
      maghrib: this.formatTime(maghribHour),
      isha: this.formatTime(ishaHour),
      timestamp: date.getTime(),
      location: coords
    }
  }

  /**
   * Get Islamic holidays for a given year
   */
  public getIslamicHolidays(year: number): IslamicHoliday[] {
    const holidays: IslamicHoliday[] = []
    
    // Major Islamic holidays (approximate dates)
    const islamicYear = year - 579 // Approximate Hijri year
    
    // Eid al-Fitr (1st Shawwal)
    const eidFitr = this.hijriToGregorian(islamicYear, 10, 1)
    holidays.push({
      name: 'Eid al-Fitr',
      nameAr: 'عيد الفطر',
      date: eidFitr,
      hijriDate: this.gregorianToHijri(eidFitr),
      type: 'major',
      duration: 3,
      description: 'Festival of Breaking the Fast',
      descriptionAr: 'عيد الفطر المبارك',
      businessImpact: 'closed',
      workshopRecommendation: 'ورشة مغلقة لمدة 3 أيام احتفالاً بعيد الفطر'
    })

    // Eid al-Adha (10th Dhu al-Hijjah)
    const eidAdha = this.hijriToGregorian(islamicYear, 12, 10)
    holidays.push({
      name: 'Eid al-Adha',
      nameAr: 'عيد الأضحى',
      date: eidAdha,
      hijriDate: this.gregorianToHijri(eidAdha),
      type: 'major',
      duration: 4,
      description: 'Festival of Sacrifice',
      descriptionAr: 'عيد الأضحى المبارك',
      businessImpact: 'closed',
      workshopRecommendation: 'ورشة مغلقة لمدة 4 أيام احتفالاً بعيد الأضحى'
    })

    // Islamic New Year (1st Muharram)
    const newYear = this.hijriToGregorian(islamicYear + 1, 1, 1)
    holidays.push({
      name: 'Islamic New Year',
      nameAr: 'رأس السنة الهجرية',
      date: newYear,
      hijriDate: this.gregorianToHijri(newYear),
      type: 'minor',
      duration: 1,
      description: 'First day of the Islamic calendar',
      descriptionAr: 'أول أيام السنة الهجرية الجديدة',
      businessImpact: 'reduced_hours',
      workshopRecommendation: 'ساعات عمل مخفضة بمناسبة رأس السنة الهجرية'
    })

    // Mawlid al-Nabi (12th Rabi' al-awwal)
    const mawlid = this.hijriToGregorian(islamicYear, 3, 12)
    holidays.push({
      name: 'Mawlid al-Nabi',
      nameAr: 'المولد النبوي الشريف',
      date: mawlid,
      hijriDate: this.gregorianToHijri(mawlid),
      type: 'major',
      duration: 1,
      description: 'Prophet Muhammad\'s Birthday',
      descriptionAr: 'ذكرى مولد النبي محمد صلى الله عليه وسلم',
      businessImpact: 'closed',
      workshopRecommendation: 'ورشة مغلقة بمناسبة المولد النبوي الشريف'
    })

    // Laylat al-Qadr (27th Ramadan)
    const laylatQadr = this.hijriToGregorian(islamicYear, 9, 27)
    holidays.push({
      name: 'Laylat al-Qadr',
      nameAr: 'ليلة القدر',
      date: laylatQadr,
      hijriDate: this.gregorianToHijri(laylatQadr),
      type: 'observance',
      duration: 1,
      description: 'Night of Power',
      descriptionAr: 'ليلة القدر المباركة',
      businessImpact: 'reduced_hours',
      workshopRecommendation: 'إنهاء العمل مبكراً في ليلة القدر'
    })

    return holidays.sort((a, b) => a.date.getTime() - b.date.getTime())
  }

  /**
   * Get Ramadan information for a given year
   */
  public getRamadanInfo(year: number): RamadanInfo {
    const islamicYear = year - 579
    const ramadanStart = this.hijriToGregorian(islamicYear, 9, 1)
    const ramadanEnd = this.hijriToGregorian(islamicYear, 9, 30)
    
    const now = new Date()
    const isRamadan = now >= ramadanStart && now <= ramadanEnd
    const currentDay = isRamadan ? 
      Math.floor((now.getTime() - ramadanStart.getTime()) / (1000 * 60 * 60 * 24)) + 1 : 0
    
    // Calculate Suhoor and Iftar times (simplified)
    const prayerTimes = this.calculatePrayerTimes(now)
    const suhoorTime = this.subtractMinutes(prayerTimes.fajr, 15)
    const iftarTime = prayerTimes.maghrib

    return {
      isRamadan,
      ramadanStart,
      ramadanEnd,
      currentDay,
      totalDays: 30,
      specialHours: {
        start: '09:00',
        end: '14:00',
        breakTime: iftarTime
      },
      suhoorTime,
      iftarTime
    }
  }

  /**
   * Check if current time is during prayer time
   */
  public isCurrentlyPrayerTime(prayerTimes: PrayerTimes): boolean {
    const now = new Date()
    const currentTime = now.getHours() * 60 + now.getMinutes()
    
    const prayers = [
      prayerTimes.fajr,
      prayerTimes.dhuhr,
      prayerTimes.asr,
      prayerTimes.maghrib,
      prayerTimes.isha
    ]

    for (const prayer of prayers) {
      const [hours, minutes] = prayer.split(':').map(Number)
      const prayerTime = hours * 60 + minutes
      
      // Check if within 15 minutes of prayer time
      if (Math.abs(currentTime - prayerTime) <= 15) {
        return true
      }
    }

    return false
  }

  /**
   * Get next prayer time
   */
  public getNextPrayer(prayerTimes: PrayerTimes): { name: string; nameAr: string; time: string } {
    const now = new Date()
    const currentTime = now.getHours() * 60 + now.getMinutes()
    
    const prayers = [
      { name: 'Fajr', nameAr: 'الفجر', time: prayerTimes.fajr },
      { name: 'Dhuhr', nameAr: 'الظهر', time: prayerTimes.dhuhr },
      { name: 'Asr', nameAr: 'العصر', time: prayerTimes.asr },
      { name: 'Maghrib', nameAr: 'المغرب', time: prayerTimes.maghrib },
      { name: 'Isha', nameAr: 'العشاء', time: prayerTimes.isha }
    ]

    for (const prayer of prayers) {
      const [hours, minutes] = prayer.time.split(':').map(Number)
      const prayerTime = hours * 60 + minutes
      
      if (prayerTime > currentTime) {
        return prayer
      }
    }

    // If no prayer left today, return tomorrow's Fajr
    return prayers[0]
  }

  /**
   * Get cultural periods (Ramadan, Hajj, etc.)
   */
  public getCulturalPeriods(year: number): CulturalPeriod[] {
    const periods: CulturalPeriod[] = []
    const islamicYear = year - 579

    // Ramadan period
    const ramadanStart = this.hijriToGregorian(islamicYear, 9, 1)
    const ramadanEnd = this.hijriToGregorian(islamicYear, 9, 30)
    
    periods.push({
      name: 'Ramadan',
      nameAr: 'شهر رمضان المبارك',
      start: ramadanStart,
      end: ramadanEnd,
      type: 'religious',
      businessAdjustments: {
        hours: { start: '09:00', end: '14:00' },
        breaks: ['13:30'], // Pre-Iftar break
        restrictions: ['no_food_drinks_public', 'reduced_physical_work']
      }
    })

    // Hajj period
    const hajjStart = this.hijriToGregorian(islamicYear, 12, 8)
    const hajjEnd = this.hijriToGregorian(islamicYear, 12, 13)
    
    periods.push({
      name: 'Hajj Period',
      nameAr: 'موسم الحج',
      start: hajjStart,
      end: hajjEnd,
      type: 'religious',
      businessAdjustments: {
        hours: { start: '08:00', end: '16:00' },
        breaks: ['12:00', '15:00'],
        restrictions: ['no_major_renovations']
      }
    })

    return periods
  }

  // Utility methods
  private getDayOfYear(date: Date): number {
    const start = new Date(date.getFullYear(), 0, 0)
    const diff = date.getTime() - start.getTime()
    return Math.floor(diff / (1000 * 60 * 60 * 24))
  }

  private formatTime(hour: number): string {
    const hours = Math.floor(hour)
    const minutes = Math.floor((hour - hours) * 60)
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`
  }

  private subtractMinutes(time: string, minutes: number): string {
    const [hours, mins] = time.split(':').map(Number)
    const totalMinutes = hours * 60 + mins - minutes
    const newHours = Math.floor(totalMinutes / 60)
    const newMins = totalMinutes % 60
    return `${newHours.toString().padStart(2, '0')}:${newMins.toString().padStart(2, '0')}`
  }
}

// Composable function for Vue components
export function useIslamicCalendar() {
  const calendar = new IslamicCalendar()
  
  const currentHijriDate = ref<HijriDate | null>(null)
  const todaysPrayerTimes = ref<PrayerTimes | null>(null)
  const currentRamadanInfo = ref<RamadanInfo | null>(null)
  const upcomingHolidays = ref<IslamicHoliday[]>([])
  const activeCulturalPeriods = ref<CulturalPeriod[]>([])
  
  const isLoading = ref(false)
  const lastUpdate = ref<Date | null>(null)

  // Computed properties
  const isRamadan = computed(() => 
    currentRamadanInfo.value?.isRamadan || false
  )

  const nextPrayer = computed(() => 
    todaysPrayerTimes.value ? 
    calendar.getNextPrayer(todaysPrayerTimes.value) : null
  )

  const isPrayerTime = computed(() =>
    todaysPrayerTimes.value ? 
    calendar.isCurrentlyPrayerTime(todaysPrayerTimes.value) : false
  )

  const todaysHoliday = computed(() => {
    const today = new Date()
    return upcomingHolidays.value.find(holiday => 
      holiday.date.toDateString() === today.toDateString()
    )
  })

  const workshopRecommendation = computed(() => {
    if (todaysHoliday.value) {
      return {
        type: 'holiday',
        message: todaysHoliday.value.workshopRecommendation,
        impact: todaysHoliday.value.businessImpact
      }
    }

    if (isRamadan.value) {
      return {
        type: 'ramadan',
        message: 'ساعات عمل مخفضة خلال شهر رمضان المبارك',
        impact: 'reduced_hours'
      }
    }

    if (isPrayerTime.value) {
      return {
        type: 'prayer',
        message: `وقت صلاة ${nextPrayer.value?.nameAr} - يُنصح بأخذ استراحة قصيرة`,
        impact: 'prayer_break'
      }
    }

    return null
  })

  // Methods
  async function updateCalendarData() {
    isLoading.value = true
    try {
      const now = new Date()
      const currentYear = now.getFullYear()

      // Update Hijri date
      currentHijriDate.value = calendar.gregorianToHijri(now)

      // Update prayer times
      todaysPrayerTimes.value = calendar.calculatePrayerTimes(now)

      // Update Ramadan info
      currentRamadanInfo.value = calendar.getRamadanInfo(currentYear)

      // Update holidays
      upcomingHolidays.value = calendar.getIslamicHolidays(currentYear)

      // Update cultural periods
      const allPeriods = calendar.getCulturalPeriods(currentYear)
      activeCulturalPeriods.value = allPeriods.filter(period => 
        now >= period.start && now <= period.end
      )

      lastUpdate.value = now
    } catch (error) {
      console.error('Failed to update Islamic calendar data:', error)
    } finally {
      isLoading.value = false
    }
  }

  function formatHijriDate(hijriDate: HijriDate, language: 'ar' | 'en' = 'ar'): string {
    if (language === 'ar') {
      return `${hijriDate.day} ${hijriDate.monthNameAr} ${hijriDate.year} هـ`
    } else {
      return `${hijriDate.day} ${hijriDate.monthName} ${hijriDate.year} AH`
    }
  }

  function formatPrayerTime(time: string, language: 'ar' | 'en' = 'ar'): string {
    const [hours, minutes] = time.split(':')
    if (language === 'ar') {
      const arabicHours = hours.replace(/[0-9]/g, (d) => '٠١٢٣٤٥٦٧٨٩'[parseInt(d)])
      const arabicMinutes = minutes.replace(/[0-9]/g, (d) => '٠١٢٣٤٥٦٧٨٩'[parseInt(d)])
      return `${arabicHours}:${arabicMinutes}`
    }
    return time
  }

  // Initialize calendar data
  onMounted(() => {
    updateCalendarData()
    
    // Update prayer times daily
    const updateInterval = setInterval(updateCalendarData, 24 * 60 * 60 * 1000)
    
    // Cleanup interval on unmount
    return () => clearInterval(updateInterval)
  })

  // Auto-refresh every hour to keep prayer times current
  setInterval(() => {
    if (todaysPrayerTimes.value) {
      const now = new Date()
      todaysPrayerTimes.value = calendar.calculatePrayerTimes(now)
    }
  }, 60 * 60 * 1000)

  return {
    // State
    currentHijriDate: readonly(currentHijriDate),
    todaysPrayerTimes: readonly(todaysPrayerTimes),
    currentRamadanInfo: readonly(currentRamadanInfo),
    upcomingHolidays: readonly(upcomingHolidays),
    activeCulturalPeriods: readonly(activeCulturalPeriods),
    isLoading: readonly(isLoading),
    lastUpdate: readonly(lastUpdate),

    // Computed
    isRamadan,
    nextPrayer,
    isPrayerTime,
    todaysHoliday,
    workshopRecommendation,

    // Methods
    updateCalendarData,
    formatHijriDate,
    formatPrayerTime,

    // Calendar access for advanced use
    calendar
  }
}

// Export readonly helper
function readonly<T>(ref: Ref<T>): Readonly<Ref<T>> {
  return ref as Readonly<Ref<T>>
}

export default IslamicCalendar