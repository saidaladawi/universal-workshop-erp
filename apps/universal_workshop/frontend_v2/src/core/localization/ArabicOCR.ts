/**
 * Arabic OCR Engine - Universal Workshop Frontend V2
 *
 * Advanced OCR system for Arabic documents with business field extraction,
 * cultural compliance validation, and document classification.
 */

export interface OCRResult {
    success: boolean
    confidence: number
    text: string
    language: 'ar' | 'en' | 'mixed'
    documentType?: DocumentType
    extractedFields?: ExtractedFields
    boundingBoxes?: TextRegion[]
    processingTime: number
    errors?: string[]
    warnings?: string[]
}

export interface TextRegion {
    text: string
    confidence: number
    language: 'ar' | 'en'
    boundingBox: {
        x: number
        y: number
        width: number
        height: number
    }
    textDirection: 'ltr' | 'rtl'
    fontSize?: number
    fontWeight?: 'normal' | 'bold'
}

export interface ExtractedFields {
    [key: string]: FieldValue
}

export interface FieldValue {
    value: string
    confidence: number
    boundingBox?: TextRegion['boundingBox']
    normalized?: string
    validation?: {
        isValid: boolean
        errors?: string[]
    }
}

export type DocumentType =
    | 'vehicle_registration'
    | 'driving_license'
    | 'insurance_policy'
    | 'service_invoice'
    | 'parts_invoice'
    | 'mulkiya'
    | 'istimara'
    | 'commercial_registration'
    | 'customs_clearance'
    | 'technical_inspection'
    | 'unknown'

export interface DocumentClassificationResult {
    type: DocumentType
    confidence: number
    features: string[]
    templateMatch?: number
}

export interface BusinessFieldTemplate {
    documentType: DocumentType
    fields: {
        [fieldName: string]: {
            patterns: RegExp[]
            position?: 'top' | 'middle' | 'bottom' | 'left' | 'right'
            required: boolean
            dataType: 'text' | 'number' | 'date' | 'currency' | 'license_plate' | 'vin' | 'phone' | 'email'
            validation?: (value: string) => boolean
            normalization?: (value: string) => string
        }
    }
}

export class ArabicOCR {
    private tesseractWorker: any
    private isInitialized = false
    private documentTemplates: Map<DocumentType, BusinessFieldTemplate> = new Map()
    private culturalPatterns: Map<string, RegExp[]> = new Map()
    private omanSpecificPatterns: Map<string, RegExp[]> = new Map()

    constructor() {
        this.initializeTemplates()
        this.initializeCulturalPatterns()
        this.initializeOmanPatterns()
    }

    /**
     * Initialize the OCR engine
     */
    async initialize(): Promise<void> {
        if (this.isInitialized) return

        try {
            // Initialize Tesseract with Arabic language support
            const { createWorker } = await import('tesseract.js')
            this.tesseractWorker = await createWorker(['ara', 'eng'], 1, {
                logger: m => console.log('OCR:', m)
            })

            // Configure for Arabic text
            await this.tesseractWorker.setParameters({
                tessedit_char_whitelist: 'ابتثجحخدذرزسشصضطظعغفقكلمنهويءآأؤإئةىABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,:-+()[]{}/',
                preserve_interword_spaces: '1',
                tessedit_pageseg_mode: '6' // Uniform block of text
            })

            this.isInitialized = true
            console.log('✅ Arabic OCR Engine initialized successfully')
        } catch (error) {
            console.error('❌ Failed to initialize Arabic OCR:', error)
            throw new Error('OCR initialization failed')
        }
    }

    /**
     * Process image and extract Arabic text
     */
    async processImage(imageData: Blob | string | ImageData, options: {
        documentType?: DocumentType
        extractFields?: boolean
        preferArabic?: boolean
        enhanceImage?: boolean
    } = {}): Promise<OCRResult> {
        await this.initialize()

        const startTime = Date.now()

        try {
            // Enhance image if requested
            let processedImage = imageData
            if (options.enhanceImage) {
                processedImage = await this.enhanceImageForOCR(imageData)
            }

            // Perform OCR
            const { data } = await this.tesseractWorker.recognize(processedImage)

            const confidence = data.confidence / 100
            const text = this.cleanExtractedText(data.text)
            const language = this.detectLanguage(text)

            let result: OCRResult = {
                success: confidence > 0.3,
                confidence,
                text,
                language,
                boundingBoxes: this.extractTextRegions(data),
                processingTime: Date.now() - startTime
            }

            // Classify document type if not provided
            if (!options.documentType) {
                const classification = await this.classifyDocument(text, result.boundingBoxes || [])
                result.documentType = classification.type
            } else {
                result.documentType = options.documentType
            }

            // Extract business fields if requested
            if (options.extractFields && result.documentType !== 'unknown') {
                result.extractedFields = await this.extractBusinessFields(text, result.documentType, result.boundingBoxes || [])
            }

            // Validate extracted fields
            if (result.extractedFields) {
                result = await this.validateExtractedFields(result)
            }

            return result

        } catch (error) {
            console.error('OCR processing failed:', error)
            return {
                success: false,
                confidence: 0,
                text: '',
                language: 'ar',
                processingTime: Date.now() - startTime,
                errors: [error instanceof Error ? error.message : 'Unknown OCR error']
            }
        }
    }

    /**
     * Classify document type based on extracted text
     */
    private async classifyDocument(text: string, regions: TextRegion[]): Promise<DocumentClassificationResult> {
        const features: string[] = []
        let bestMatch: { type: DocumentType; confidence: number } = { type: 'unknown', confidence: 0 }

        for (const [documentType, template] of this.documentTemplates) {
            let matchScore = 0
            let totalPatterns = 0

            for (const [fieldName, fieldConfig] of Object.entries(template.fields)) {
                totalPatterns += fieldConfig.patterns.length

                for (const pattern of fieldConfig.patterns) {
                    if (pattern.test(text)) {
                        matchScore++
                        features.push(`${documentType}:${fieldName}`)
                    }
                }
            }

            const confidence = totalPatterns > 0 ? matchScore / totalPatterns : 0

            if (confidence > bestMatch.confidence) {
                bestMatch = { type: documentType, confidence }
            }
        }

        return {
            type: bestMatch.type,
            confidence: bestMatch.confidence,
            features
        }
    }

    /**
     * Extract business fields from classified document
     */
    private async extractBusinessFields(text: string, documentType: DocumentType, regions: TextRegion[]): Promise<ExtractedFields> {
        const template = this.documentTemplates.get(documentType)
        if (!template) return {}

        const extractedFields: ExtractedFields = {}

        for (const [fieldName, fieldConfig] of Object.entries(template.fields)) {
            let bestMatch: { value: string; confidence: number; boundingBox?: TextRegion['boundingBox'] } | null = null

            // Try each pattern for this field
            for (const pattern of fieldConfig.patterns) {
                const matches = text.match(pattern)
                if (matches && matches[1]) {
                    const value = matches[1].trim()
                    const confidence = this.calculateFieldConfidence(value, fieldConfig.dataType)

                    if (!bestMatch || confidence > bestMatch.confidence) {
                        bestMatch = {
                            value,
                            confidence,
                            boundingBox: this.findRegionForText(value, regions)?.boundingBox
                        }
                    }
                }
            }

            if (bestMatch) {
                extractedFields[fieldName] = {
                    value: bestMatch.value,
                    confidence: bestMatch.confidence,
                    boundingBox: bestMatch.boundingBox,
                    normalized: fieldConfig.normalization ? fieldConfig.normalization(bestMatch.value) : bestMatch.value,
                    validation: fieldConfig.validation ? {
                        isValid: fieldConfig.validation(bestMatch.value),
                        errors: fieldConfig.validation(bestMatch.value) ? undefined : [`Invalid ${fieldName} format`]
                    } : undefined
                }
            }
        }

        return extractedFields
    }

    /**
     * Enhance image for better OCR accuracy
     */
    private async enhanceImageForOCR(imageData: Blob | string | ImageData): Promise<ImageData> {
        return new Promise((resolve) => {
            const canvas = document.createElement('canvas')
            const ctx = canvas.getContext('2d')!
            const img = new Image()

            img.onload = () => {
                canvas.width = img.width
                canvas.height = img.height

                // Draw original image
                ctx.drawImage(img, 0, 0)

                // Get image data for processing
                const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
                const data = imageData.data

                // Apply image enhancements
                for (let i = 0; i < data.length; i += 4) {
                    // Convert to grayscale
                    const gray = data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114

                    // Apply contrast enhancement
                    const enhanced = this.enhanceContrast(gray)

                    // Apply threshold for binary image
                    const binary = enhanced > 128 ? 255 : 0

                    data[i] = binary     // Red
                    data[i + 1] = binary // Green
                    data[i + 2] = binary // Blue
                    // Alpha remains unchanged
                }

                resolve(imageData)
            }

            // Handle different image data types
            if (imageData instanceof Blob) {
                img.src = URL.createObjectURL(imageData)
            } else if (typeof imageData === 'string') {
                img.src = imageData
            } else {
                // ImageData - create canvas and draw
                canvas.width = imageData.width
                canvas.height = imageData.height
                ctx.putImageData(imageData, 0, 0)
                resolve(imageData)
            }
        })
    }

    /**
     * Clean and normalize extracted text
     */
    private cleanExtractedText(rawText: string): string {
        return rawText
            // Remove extra whitespace
            .replace(/\s+/g, ' ')
            // Remove common OCR artifacts
            .replace(/[|]/g, 'l')
            .replace(/[0O]/g, (match, offset, string) => {
                // Context-aware O/0 correction
                const before = string[offset - 1]
                const after = string[offset + 1]
                if (/[0-9]/.test(before) || /[0-9]/.test(after)) {
                    return '0'
                }
                return 'O'
            })
            // Fix Arabic text direction issues
            .replace(/(\d+)\s*([\u0600-\u06FF]+)/g, '$2 $1')
            .trim()
    }

    /**
     * Detect primary language in text
     */
    private detectLanguage(text: string): 'ar' | 'en' | 'mixed' {
        const arabicChars = (text.match(/[\u0600-\u06FF]/g) || []).length
        const englishChars = (text.match(/[A-Za-z]/g) || []).length
        const total = arabicChars + englishChars

        if (total === 0) return 'ar' // Default to Arabic for Oman

        const arabicRatio = arabicChars / total

        if (arabicRatio > 0.7) return 'ar'
        if (arabicRatio < 0.3) return 'en'
        return 'mixed'
    }

    /**
     * Extract text regions with bounding boxes
     */
    private extractTextRegions(tesseractData: any): TextRegion[] {
        const regions: TextRegion[] = []

        if (tesseractData.words) {
            for (const word of tesseractData.words) {
                if (word.confidence > 30 && word.text.trim()) {
                    regions.push({
                        text: word.text,
                        confidence: word.confidence / 100,
                        language: this.detectLanguage(word.text),
                        boundingBox: {
                            x: word.bbox.x0,
                            y: word.bbox.y0,
                            width: word.bbox.x1 - word.bbox.x0,
                            height: word.bbox.y1 - word.bbox.y0
                        },
                        textDirection: /[\u0600-\u06FF]/.test(word.text) ? 'rtl' : 'ltr'
                    })
                }
            }
        }

        return regions
    }

    /**
     * Calculate confidence score for extracted field
     */
    private calculateFieldConfidence(value: string, dataType: string): number {
        let confidence = 0.5 // Base confidence

        switch (dataType) {
            case 'license_plate':
                // Oman license plate format validation
                if (/^\d{1,6}$/.test(value) || /^[A-Z]{1,3}\s?\d{1,4}$/.test(value)) {
                    confidence = 0.9
                }
                break

            case 'vin':
                if (value.length === 17 && /^[A-HJ-NPR-Z0-9]+$/i.test(value)) {
                    confidence = 0.95
                }
                break

            case 'date':
                if (/\d{1,2}\/\d{1,2}\/\d{4}/.test(value) || /\d{4}-\d{2}-\d{2}/.test(value)) {
                    confidence = 0.8
                }
                break

            case 'currency':
                if (/\d+(\.\d{2})?\s?(OMR|ريال|رياל)/.test(value)) {
                    confidence = 0.85
                }
                break

            case 'phone':
                if (/^(\+968\s?)?\d{8}$/.test(value.replace(/\s/g, ''))) {
                    confidence = 0.9
                }
                break

            default:
                if (value.length > 2) {
                    confidence = 0.7
                }
        }

        return Math.min(confidence, 1.0)
    }

    /**
     * Find text region for specific text
     */
    private findRegionForText(text: string, regions: TextRegion[]): TextRegion | undefined {
        return regions.find(region =>
            region.text.includes(text) || text.includes(region.text)
        )
    }

    /**
     * Validate extracted fields against business rules
     */
    private async validateExtractedFields(result: OCRResult): Promise<OCRResult> {
        if (!result.extractedFields) return result

        const warnings: string[] = []

        for (const [fieldName, fieldValue] of Object.entries(result.extractedFields)) {
            // Cultural validation for Arabic names
            if (fieldName.includes('name') && fieldValue.value) {
                if (!/[\u0600-\u06FF]/.test(fieldValue.value)) {
                    warnings.push(`${fieldName} should contain Arabic characters`)
                }
            }

            // Oman-specific validations
            if (fieldName === 'license_plate') {
                if (!this.validateOmanLicensePlate(fieldValue.value)) {
                    warnings.push('License plate format does not match Oman standards')
                }
            }

            if (fieldName === 'phone_number') {
                if (!this.validateOmanPhoneNumber(fieldValue.value)) {
                    warnings.push('Phone number format does not match Oman standards')
                }
            }
        }

        if (warnings.length > 0) {
            result.warnings = (result.warnings || []).concat(warnings)
        }

        return result
    }

    /**
     * Validate Oman license plate format
     */
    private validateOmanLicensePlate(plateNumber: string): boolean {
        // Oman license plate patterns
        const patterns = [
            /^\d{1,6}$/, // Numeric only
            /^[A-Z]{1,3}\s?\d{1,4}$/, // Letters + numbers
            /^\d{1,3}\s?[A-Z]{1,3}$/ // Numbers + letters
        ]

        return patterns.some(pattern => pattern.test(plateNumber.toUpperCase()))
    }

    /**
     * Validate Oman phone number format
     */
    private validateOmanPhoneNumber(phoneNumber: string): boolean {
        const cleaned = phoneNumber.replace(/\s/g, '')

        // Oman mobile numbers start with 9, landlines with 2
        return /^(\+968)?[29]\d{7}$/.test(cleaned)
    }

    /**
     * Enhance image contrast
     */
    private enhanceContrast(grayValue: number): number {
        // Simple contrast enhancement
        return Math.min(255, Math.max(0, (grayValue - 128) * 1.5 + 128))
    }

    /**
     * Initialize document templates
     */
    private initializeTemplates(): void {
        // Vehicle Registration (Mulkiya) Template
        this.documentTemplates.set('vehicle_registration', {
            documentType: 'vehicle_registration',
            fields: {
                plate_number: {
                    patterns: [
                        /رقم اللوحة[:\s]*(\d+)/,
                        /Plate Number[:\s]*([A-Z0-9\s]+)/i,
                        /لوحة[:\s]*(\d+)/
                    ],
                    position: 'top',
                    required: true,
                    dataType: 'license_plate'
                },
                chassis_number: {
                    patterns: [
                        /رقم الهيكل[:\s]*([A-Z0-9]+)/,
                        /Chassis[:\s]*([A-Z0-9]+)/i,
                        /VIN[:\s]*([A-Z0-9]{17})/i
                    ],
                    required: true,
                    dataType: 'vin'
                },
                owner_name: {
                    patterns: [
                        /اسم المالك[:\s]*([^\n]+)/,
                        /Owner Name[:\s]*([^\n]+)/i,
                        /المالك[:\s]*([^\n]+)/
                    ],
                    required: true,
                    dataType: 'text'
                },
                make_model: {
                    patterns: [
                        /الماركة والطراز[:\s]*([^\n]+)/,
                        /Make & Model[:\s]*([^\n]+)/i,
                        /نوع السيارة[:\s]*([^\n]+)/
                    ],
                    required: true,
                    dataType: 'text'
                },
                year: {
                    patterns: [
                        /سنة الصنع[:\s]*(\d{4})/,
                        /Year[:\s]*(\d{4})/i,
                        /الطراز[:\s]*(\d{4})/
                    ],
                    required: true,
                    dataType: 'number'
                },
                expiry_date: {
                    patterns: [
                        /تاريخ الانتهاء[:\s]*(\d{1,2}\/\d{1,2}\/\d{4})/,
                        /Expiry Date[:\s]*(\d{1,2}\/\d{1,2}\/\d{4})/i,
                        /ينتهي في[:\s]*(\d{1,2}\/\d{1,2}\/\d{4})/
                    ],
                    required: true,
                    dataType: 'date'
                }
            }
        })

        // Driving License Template
        this.documentTemplates.set('driving_license', {
            documentType: 'driving_license',
            fields: {
                license_number: {
                    patterns: [
                        /رقم الرخصة[:\s]*(\d+)/,
                        /License Number[:\s]*(\d+)/i,
                        /رقم[:\s]*(\d+)/
                    ],
                    required: true,
                    dataType: 'number'
                },
                full_name: {
                    patterns: [
                        /الاسم الكامل[:\s]*([^\n]+)/,
                        /Full Name[:\s]*([^\n]+)/i,
                        /الاسم[:\s]*([^\n]+)/
                    ],
                    required: true,
                    dataType: 'text'
                },
                birth_date: {
                    patterns: [
                        /تاريخ الميلاد[:\s]*(\d{1,2}\/\d{1,2}\/\d{4})/,
                        /Date of Birth[:\s]*(\d{1,2}\/\d{1,2}\/\d{4})/i,
                        /المولد[:\s]*(\d{1,2}\/\d{1,2}\/\d{4})/
                    ],
                    required: true,
                    dataType: 'date'
                },
                license_class: {
                    patterns: [
                        /فئة الرخصة[:\s]*([^\n]+)/,
                        /License Class[:\s]*([^\n]+)/i,
                        /الفئة[:\s]*([^\n]+)/
                    ],
                    required: true,
                    dataType: 'text'
                }
            }
        })

        // Service Invoice Template
        this.documentTemplates.set('service_invoice', {
            documentType: 'service_invoice',
            fields: {
                invoice_number: {
                    patterns: [
                        /رقم الفاتورة[:\s]*(\d+)/,
                        /Invoice Number[:\s]*(\d+)/i,
                        /فاتورة رقم[:\s]*(\d+)/
                    ],
                    required: true,
                    dataType: 'number'
                },
                service_date: {
                    patterns: [
                        /تاريخ الخدمة[:\s]*(\d{1,2}\/\d{1,2}\/\d{4})/,
                        /Service Date[:\s]*(\d{1,2}\/\d{1,2}\/\d{4})/i,
                        /التاريخ[:\s]*(\d{1,2}\/\d{1,2}\/\d{4})/
                    ],
                    required: true,
                    dataType: 'date'
                },
                total_amount: {
                    patterns: [
                        /المبلغ الإجمالي[:\s]*(\d+(?:\.\d{2})?)\s*ريال/,
                        /Total Amount[:\s]*(\d+(?:\.\d{2})?)\s*OMR/i,
                        /الإجمالي[:\s]*(\d+(?:\.\d{2})?)/
                    ],
                    required: true,
                    dataType: 'currency'
                },
                customer_name: {
                    patterns: [
                        /اسم العميل[:\s]*([^\n]+)/,
                        /Customer Name[:\s]*([^\n]+)/i,
                        /العميل[:\s]*([^\n]+)/
                    ],
                    required: true,
                    dataType: 'text'
                },
                vehicle_info: {
                    patterns: [
                        /معلومات السيارة[:\s]*([^\n]+)/,
                        /Vehicle Info[:\s]*([^\n]+)/i,
                        /السيارة[:\s]*([^\n]+)/
                    ],
                    required: false,
                    dataType: 'text'
                }
            }
        })
    }

    /**
     * Initialize cultural patterns
     */
    private initializeCulturalPatterns(): void {
        // Arabic name patterns
        this.culturalPatterns.set('arabic_names', [
            /محمد|أحمد|علي|حسن|حسين|عبدالله|عبدالرحمن|خالد|سعد|فهد/,
            /فاطمة|عائشة|خديجة|زينب|مريم|سارة|نورا|هند|أمل|رقية/
        ])

        // Arabic place names in Oman
        this.culturalPatterns.set('oman_places', [
            /مسقط|صلالة|نزوى|صحار|عبري|الرستاق|البريمي|صور|خصب|مرباط/,
            /الباطنة|الداخلية|الشرقية|ظفار|مسندم|الوسطى|الظاهرة/
        ])

        // Common Arabic automotive terms
        this.culturalPatterns.set('automotive_arabic', [
            /سيارة|مركبة|سياره|عربة|آلية|شاحنة|حافلة|دراجة|بيك أب/,
            /محرك|فرامل|إطارات|بطارية|زيت|ماء|فلتر|شمعات|سير/
        ])
    }

    /**
     * Initialize Oman-specific patterns
     */
    private initializeOmanPatterns(): void {
        // Oman government entity names
        this.omanSpecificPatterns.set('government_entities', [
            /شرطة عمان السلطانية|وزارة النقل|هيئة تنظيم الخدمات العامة/,
            /بلدية مسقط|جمارك السلطنة|وزارة التجارة/
        ])

        // Oman license plate patterns
        this.omanSpecificPatterns.set('license_plates', [
            /^\d{1,6}$/,
            /^[A-Z]{1,3}\s?\d{1,4}$/,
            /^\d{1,3}\s?[A-Z]{1,3}$/
        ])

        // Oman postal codes
        this.omanSpecificPatterns.set('postal_codes', [
            /^1\d{2}$/  // Oman postal codes are 3 digits starting with 1
        ])
    }

    /**
     * Cleanup resources
     */
    async dispose(): Promise<void> {
        if (this.tesseractWorker) {
            await this.tesseractWorker.terminate()
            this.tesseractWorker = null
        }
        this.isInitialized = false
    }
}

export default ArabicOCR
