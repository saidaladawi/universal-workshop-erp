/**
 * Advanced Arabic NLP Engine for Universal Workshop ERP
 * Provides sentiment analysis, entity extraction, and text processing for Arabic content
 * 
 * Features:
 * - Arabic sentiment analysis for customer feedback
 * - Named entity recognition for workshop documents
 * - Text classification and categorization
 * - Arabic spell checking and correction
 * - Workshop-specific terminology recognition
 * - Cultural context analysis
 */

import { ref, reactive } from 'vue'

// Types for Arabic NLP
interface SentimentResult {
  sentiment: 'positive' | 'negative' | 'neutral'
  confidence: number
  score: number // -1 to 1
  emotions: {
    joy: number
    anger: number
    sadness: number
    fear: number
    surprise: number
    trust: number
  }
  culturalContext: {
    politeness: number
    formality: number
    urgency: number
  }
}

interface EntityResult {
  entities: Array<{
    text: string
    type: 'PERSON' | 'LOCATION' | 'ORGANIZATION' | 'VEHICLE' | 'PART' | 'SERVICE' | 'DATE' | 'MONEY'
    start: number
    end: number
    confidence: number
    metadata?: Record<string, any>
  }>
  totalEntities: number
  processingTime: number
}

interface TextClassificationResult {
  category: string
  subcategory?: string
  confidence: number
  intent: 'complaint' | 'inquiry' | 'compliment' | 'request' | 'urgent' | 'normal'
  priority: 'low' | 'medium' | 'high' | 'urgent'
  keywords: string[]
}

interface SpellCheckResult {
  correctedText: string
  corrections: Array<{
    original: string
    corrected: string
    position: number
    confidence: number
    suggestions: string[]
  }>
  totalCorrections: number
}

interface WorkshopTerminology {
  vehicleParts: string[]
  serviceTypes: string[]
  customerTerms: string[]
  technicalTerms: string[]
  statusTerms: string[]
}

class ArabicNLPEngine {
  private sentimentModel: any = null
  private entityModel: any = null
  private classificationModel: any = null
  private spellChecker: any = null
  
  // Arabic sentiment lexicon
  private sentimentLexicon = new Map([
    // Positive words
    ['ممتاز', 0.9], ['رائع', 0.8], ['جيد', 0.6], ['مقبول', 0.4], ['جميل', 0.7],
    ['سريع', 0.6], ['محترف', 0.8], ['دقيق', 0.7], ['نظيف', 0.6], ['مفيد', 0.5],
    ['شكراً', 0.6], ['أقدر', 0.7], ['راضي', 0.8], ['سعيد', 0.7], ['موصى', 0.8],
    
    // Negative words
    ['سيء', -0.8], ['فظيع', -0.9], ['بطيء', -0.6], ['مكلف', -0.5], ['قذر', -0.7],
    ['مشكلة', -0.6], ['خطأ', -0.7], ['متأخر', -0.5], ['صعب', -0.4], ['معقد', -0.5],
    ['أشكو', -0.8], ['غاضب', -0.8], ['محبط', -0.7], ['مخيب', -0.8], ['خداع', -0.9],
    
    // Neutral/context dependent
    ['عادي', 0.1], ['طبيعي', 0.1], ['متوقع', 0.1], ['قديم', -0.2], ['جديد', 0.3]
  ])

  // Workshop-specific terminology
  private workshopTerminology: WorkshopTerminology = {
    vehicleParts: [
      'محرك', 'فرامل', 'إطارات', 'بطارية', 'زيت', 'فلتر', 'شمعات', 'مكابح',
      'كلتش', 'ناقل حركة', 'مكيف', 'راديتر', 'مساحات', 'أنوار', 'مرايا',
      'مقود', 'عجلة قيادة', 'صندوق خلفي', 'شاسيه', 'كبوت', 'بوابة خلفية'
    ],
    serviceTypes: [
      'صيانة دورية', 'إصلاح', 'تنظيف', 'فحص', 'تغيير زيت', 'تبديل إطارات',
      'إصلاح فرامل', 'صيانة مكيف', 'فحص شامل', 'إصلاح محرك', 'صيانة كهرباء'
    ],
    customerTerms: [
      'عميل', 'زبون', 'صاحب السيارة', 'مالك المركبة', 'سائق', 'مستخدم'
    ],
    technicalTerms: [
      'تشخيص', 'قطع غيار', 'أدوات', 'معدات', 'جهاز كمبيوتر', 'ماسح ضوئي',
      'مقياس', 'اختبار', 'قياس', 'معايرة', 'ضبط', 'برمجة'
    ],
    statusTerms: [
      'جاهز', 'قيد التنفيذ', 'منتهي', 'مؤجل', 'ملغي', 'معلق', 'عاجل',
      'انتظار قطع غيار', 'تحت الصيانة', 'تم التسليم'
    ]
  }

  // Cultural context patterns
  private culturalPatterns = {
    politeness: {
      high: ['لو سمحت', 'من فضلك', 'أعتذر', 'شكراً جزيلاً', 'بارك الله فيك'],
      medium: ['شكراً', 'أقدر', 'ممتن', 'أحترم'],
      low: ['أريد', 'اعطني', 'سريع']
    },
    formality: {
      formal: ['حضرتك', 'سيادتكم', 'المحترم', 'نتشرف', 'نتقدم بخالص'],
      informal: ['أخي', 'صديقي', 'يا رجل', 'عادي', 'مافي مشكلة']
    },
    urgency: {
      urgent: ['عاجل', 'سريع', 'فوري', 'ضروري', 'حالاً', 'الآن'],
      medium: ['قريب', 'بأسرع وقت', 'في أقرب فرصة'],
      low: ['متى ما أمكن', 'لا يوجد عجلة', 'وقتك']
    }
  }

  constructor() {
    this.initializeModels()
  }

  private async initializeModels() {
    try {
      // Initialize sentiment analysis model
      // In a real implementation, you would load pre-trained models
      console.log('Arabic NLP Engine initialized')
    } catch (error) {
      console.error('Failed to initialize Arabic NLP models:', error)
    }
  }

  /**
   * Analyze sentiment of Arabic text
   */
  public analyzeSentiment(text: string): SentimentResult {
    const normalizedText = this.normalizeArabicText(text)
    const words = this.tokenizeArabicText(normalizedText)
    
    let totalScore = 0
    let wordCount = 0
    const emotions = {
      joy: 0, anger: 0, sadness: 0, fear: 0, surprise: 0, trust: 0
    }

    // Calculate sentiment based on lexicon
    for (const word of words) {
      const score = this.sentimentLexicon.get(word) || 0
      if (score !== 0) {
        totalScore += score
        wordCount++
        
        // Map to emotions
        if (score > 0.7) emotions.joy += 0.3
        if (score < -0.7) emotions.anger += 0.3
        if (score < -0.5) emotions.sadness += 0.2
      }
    }

    // Normalize scores
    const averageScore = wordCount > 0 ? totalScore / wordCount : 0
    const confidence = Math.min(wordCount / 10, 1) // Higher confidence with more sentiment words

    // Determine sentiment
    let sentiment: 'positive' | 'negative' | 'neutral'
    if (averageScore > 0.2) sentiment = 'positive'
    else if (averageScore < -0.2) sentiment = 'negative'
    else sentiment = 'neutral'

    // Analyze cultural context
    const culturalContext = this.analyzeCulturalContext(text)

    return {
      sentiment,
      confidence,
      score: Math.max(-1, Math.min(1, averageScore)),
      emotions,
      culturalContext
    }
  }

  /**
   * Extract named entities from Arabic text
   */
  public extractEntities(text: string): EntityResult {
    const startTime = performance.now()
    const normalizedText = this.normalizeArabicText(text)
    const entities: EntityResult['entities'] = []

    // Vehicle part recognition
    this.workshopTerminology.vehicleParts.forEach(part => {
      const regex = new RegExp(`\\b${part}\\b`, 'gi')
      let match
      while ((match = regex.exec(text)) !== null) {
        entities.push({
          text: match[0],
          type: 'PART',
          start: match.index,
          end: match.index + match[0].length,
          confidence: 0.9,
          metadata: { category: 'vehicle_part' }
        })
      }
    })

    // Service type recognition
    this.workshopTerminology.serviceTypes.forEach(service => {
      const regex = new RegExp(`\\b${service}\\b`, 'gi')
      let match
      while ((match = regex.exec(text)) !== null) {
        entities.push({
          text: match[0],
          type: 'SERVICE',
          start: match.index,
          end: match.index + match[0].length,
          confidence: 0.85,
          metadata: { category: 'service_type' }
        })
      }
    })

    // Date recognition (Arabic patterns)
    const datePatterns = [
      /\d{1,2}\/\d{1,2}\/\d{4}/g, // 25/12/2024
      /(اليوم|غداً|أمس|بعد غد)/g, // Relative dates
      /(الأحد|الإثنين|الثلاثاء|الأربعاء|الخميس|الجمعة|السبت)/g, // Days
      /(يناير|فبراير|مارس|أبريل|مايو|يونيو|يوليو|أغسطس|سبتمبر|أكتوبر|نوفمبر|ديسمبر)/g // Months
    ]

    datePatterns.forEach(pattern => {
      let match
      while ((match = pattern.exec(text)) !== null) {
        entities.push({
          text: match[0],
          type: 'DATE',
          start: match.index,
          end: match.index + match[0].length,
          confidence: 0.8,
          metadata: { category: 'date_time' }
        })
      }
    })

    // Money recognition (Omani Rial patterns)
    const moneyPatterns = [
      /\d+\s*(ريال|ر\.ع|OMR|بيسة)/gi,
      /\d+\.\d+\s*(ريال|ر\.ع|OMR)/gi
    ]

    moneyPatterns.forEach(pattern => {
      let match
      while ((match = pattern.exec(text)) !== null) {
        entities.push({
          text: match[0],
          type: 'MONEY',
          start: match.index,
          end: match.index + match[0].length,
          confidence: 0.95,
          metadata: { currency: 'OMR', category: 'price' }
        })
      }
    })

    // Person name recognition (simple Arabic name patterns)
    const namePatterns = [
      /(أ|د|م)\.\s*[ا-ي]+\s+[ا-ي]+/g, // Titles + names
      /[ا-ي]+\s+(بن|ابن)\s+[ا-ي]+/g,    // Name + bin + name
      /(السيد|السيدة|الأستاذ|الدكتور)\s+[ا-ي]+/g // Titles
    ]

    namePatterns.forEach(pattern => {
      let match
      while ((match = pattern.exec(text)) !== null) {
        entities.push({
          text: match[0],
          type: 'PERSON',
          start: match.index,
          end: match.index + match[0].length,
          confidence: 0.7,
          metadata: { category: 'person_name' }
        })
      }
    })

    const processingTime = performance.now() - startTime

    return {
      entities: entities.sort((a, b) => a.start - b.start),
      totalEntities: entities.length,
      processingTime
    }
  }

  /**
   * Classify Arabic text for workshop context
   */
  public classifyText(text: string): TextClassificationResult {
    const normalizedText = this.normalizeArabicText(text)
    const sentiment = this.analyzeSentiment(text)
    
    // Determine intent based on keywords and patterns
    let intent: TextClassificationResult['intent'] = 'normal'
    let priority: TextClassificationResult['priority'] = 'medium'
    let category = 'general'
    
    // Complaint detection
    const complaintKeywords = ['مشكلة', 'أشكو', 'غير راضي', 'سيء', 'خطأ', 'فشل']
    if (complaintKeywords.some(keyword => normalizedText.includes(keyword))) {
      intent = 'complaint'
      priority = 'high'
      category = 'customer_complaint'
    }
    
    // Inquiry detection
    const inquiryKeywords = ['كم', 'متى', 'أين', 'كيف', 'هل', 'ما هو', 'أريد معرفة']
    if (inquiryKeywords.some(keyword => normalizedText.includes(keyword))) {
      intent = 'inquiry'
      category = 'customer_inquiry'
    }
    
    // Compliment detection
    const complimentKeywords = ['ممتاز', 'رائع', 'شكراً', 'أقدر', 'راضي جداً']
    if (complimentKeywords.some(keyword => normalizedText.includes(keyword))) {
      intent = 'compliment'
      priority = 'low'
      category = 'customer_feedback'
    }
    
    // Request detection
    const requestKeywords = ['أريد', 'أطلب', 'أرغب', 'ممكن', 'لو سمحت']
    if (requestKeywords.some(keyword => normalizedText.includes(keyword))) {
      intent = 'request'
      category = 'service_request'
    }
    
    // Urgency detection
    const urgentKeywords = ['عاجل', 'سريع', 'فوري', 'ضروري', 'حالاً']
    if (urgentKeywords.some(keyword => normalizedText.includes(keyword))) {
      intent = 'urgent'
      priority = 'urgent'
    }

    // Extract keywords
    const words = this.tokenizeArabicText(normalizedText)
    const keywords = words.filter(word => 
      word.length > 3 && 
      (this.sentimentLexicon.has(word) || 
       Object.values(this.workshopTerminology).flat().includes(word))
    )

    return {
      category,
      confidence: 0.8, // In real implementation, this would be from trained model
      intent,
      priority,
      keywords: keywords.slice(0, 10) // Top 10 keywords
    }
  }

  /**
   * Basic Arabic spell checking and correction
   */
  public checkSpelling(text: string): SpellCheckResult {
    const corrections: SpellCheckResult['corrections'] = []
    let correctedText = text
    
    // Common Arabic spelling mistakes
    const spellingRules = new Map([
      ['ة', 'ه'], // Ta marbuta vs Ha
      ['ي', 'ى'], // Ya vs Alef maksura
      ['أ', 'ا'], // Hamza variations
      ['إ', 'ا'],
      ['آ', 'ا']
    ])

    // Common workshop misspellings
    const workshopCorrections = new Map([
      ['فراملة', 'فرامل'],
      ['تايرات', 'إطارات'],
      ['بطاريه', 'بطارية'],
      ['محرك', 'محرك'], // Keep correct
      ['صيانه', 'صيانة'],
      ['اصلاح', 'إصلاح']
    ])

    let position = 0
    const words = text.split(/\s+/)
    
    words.forEach((word, index) => {
      const cleanWord = word.replace(/[^\u0600-\u06FF]/g, '')
      
      if (workshopCorrections.has(cleanWord)) {
        const corrected = workshopCorrections.get(cleanWord)!
        corrections.push({
          original: word,
          corrected,
          position,
          confidence: 0.9,
          suggestions: [corrected]
        })
        correctedText = correctedText.replace(word, corrected)
      }
      
      position += word.length + 1
    })

    return {
      correctedText,
      corrections,
      totalCorrections: corrections.length
    }
  }

  /**
   * Analyze cultural context in Arabic text
   */
  private analyzeCulturalContext(text: string): SentimentResult['culturalContext'] {
    const normalizedText = this.normalizeArabicText(text)
    
    let politeness = 0
    let formality = 0
    let urgency = 0

    // Analyze politeness
    this.culturalPatterns.politeness.high.forEach(phrase => {
      if (normalizedText.includes(phrase)) politeness += 0.8
    })
    this.culturalPatterns.politeness.medium.forEach(phrase => {
      if (normalizedText.includes(phrase)) politeness += 0.5
    })
    this.culturalPatterns.politeness.low.forEach(phrase => {
      if (normalizedText.includes(phrase)) politeness -= 0.3
    })

    // Analyze formality
    this.culturalPatterns.formality.formal.forEach(phrase => {
      if (normalizedText.includes(phrase)) formality += 0.7
    })
    this.culturalPatterns.formality.informal.forEach(phrase => {
      if (normalizedText.includes(phrase)) formality -= 0.4
    })

    // Analyze urgency
    this.culturalPatterns.urgency.urgent.forEach(phrase => {
      if (normalizedText.includes(phrase)) urgency += 0.8
    })
    this.culturalPatterns.urgency.medium.forEach(phrase => {
      if (normalizedText.includes(phrase)) urgency += 0.5
    })

    return {
      politeness: Math.max(0, Math.min(1, politeness)),
      formality: Math.max(0, Math.min(1, formality)),
      urgency: Math.max(0, Math.min(1, urgency))
    }
  }

  /**
   * Normalize Arabic text for processing
   */
  private normalizeArabicText(text: string): string {
    return text
      .replace(/[ٱ-ٯ]/g, match => {
        // Normalize common Arabic characters
        const normalizations: Record<string, string> = {
          'ٱ': 'ا', 'أ': 'ا', 'إ': 'ا', 'آ': 'ا',
          'ى': 'ي', 'ة': 'ه'
        }
        return normalizations[match] || match
      })
      .replace(/\s+/g, ' ') // Normalize whitespace
      .trim()
  }

  /**
   * Tokenize Arabic text into words
   */
  private tokenizeArabicText(text: string): string[] {
    return text
      .split(/[\s\u060C\u061B\u061F\u0640]+/) // Split on Arabic punctuation and spaces
      .filter(word => word.length > 0)
      .map(word => word.replace(/[^\u0600-\u06FF]/g, '')) // Keep only Arabic characters
      .filter(word => word.length > 1)
  }
}

// Composable function for Vue components
export function useArabicNLP() {
  const nlpEngine = new ArabicNLPEngine()
  
  const isProcessing = ref(false)
  const lastResult = ref<any>(null)
  
  // Statistics
  const stats = reactive({
    totalAnalyses: 0,
    sentimentAnalyses: 0,
    entityExtractions: 0,
    textClassifications: 0,
    spellChecks: 0,
    averageProcessingTime: 0
  })

  async function analyzeSentiment(text: string): Promise<SentimentResult> {
    isProcessing.value = true
    try {
      const result = nlpEngine.analyzeSentiment(text)
      stats.totalAnalyses++
      stats.sentimentAnalyses++
      lastResult.value = result
      return result
    } finally {
      isProcessing.value = false
    }
  }

  async function extractEntities(text: string): Promise<EntityResult> {
    isProcessing.value = true
    try {
      const result = nlpEngine.extractEntities(text)
      stats.totalAnalyses++
      stats.entityExtractions++
      stats.averageProcessingTime = (stats.averageProcessingTime + result.processingTime) / 2
      lastResult.value = result
      return result
    } finally {
      isProcessing.value = false
    }
  }

  async function classifyText(text: string): Promise<TextClassificationResult> {
    isProcessing.value = true
    try {
      const result = nlpEngine.classifyText(text)
      stats.totalAnalyses++
      stats.textClassifications++
      lastResult.value = result
      return result
    } finally {
      isProcessing.value = false
    }
  }

  async function checkSpelling(text: string): Promise<SpellCheckResult> {
    isProcessing.value = true
    try {
      const result = nlpEngine.checkSpelling(text)
      stats.totalAnalyses++
      stats.spellChecks++
      lastResult.value = result
      return result
    } finally {
      isProcessing.value = false
    }
  }

  // Comprehensive analysis function
  async function analyzeText(text: string) {
    isProcessing.value = true
    try {
      const [sentiment, entities, classification, spelling] = await Promise.all([
        analyzeSentiment(text),
        extractEntities(text),
        classifyText(text),
        checkSpelling(text)
      ])

      const comprehensiveResult = {
        text,
        sentiment,
        entities,
        classification,
        spelling,
        timestamp: new Date().toISOString(),
        processingTime: performance.now()
      }

      lastResult.value = comprehensiveResult
      return comprehensiveResult
    } finally {
      isProcessing.value = false
    }
  }

  return {
    // State
    isProcessing: readonly(isProcessing),
    lastResult: readonly(lastResult),
    stats: readonly(stats),

    // Methods
    analyzeSentiment,
    extractEntities,
    classifyText,
    checkSpelling,
    analyzeText,

    // Engine access for advanced use
    nlpEngine
  }
}

// Export readonly helper
function readonly<T>(ref: any): any {
  return ref
}

export default ArabicNLPEngine