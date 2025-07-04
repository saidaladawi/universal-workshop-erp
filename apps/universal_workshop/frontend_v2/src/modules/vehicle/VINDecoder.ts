/**
 * VIN Decoder - Universal Workshop Frontend V2
 *
 * Advanced VIN decoding system with multiple API integrations,
 * Arabic vehicle data translation, and Omani compliance checking.
 */

export interface VehicleSpecification {
    vin: string
    make: string
    makeAr?: string
    model: string
    modelAr?: string
    year: number
    engineSize: string
    fuelType: string
    fuelTypeAr?: string
    transmission: string
    transmissionAr?: string
    drivetrain: string
    drivetrainAr?: string
    bodyType: string
    bodyTypeAr?: string
    color?: string
    colorAr?: string
    engineCode?: string
    countryOfOrigin: string
    countryOfOriginAr?: string
    manufacturingPlant?: string
    sequentialNumber?: string
    checkDigit?: string
    modelYear?: number
    assemblyPlant?: string
    trim?: string
    trimAr?: string
    doors?: number
    cylinders?: number
    displacement?: number
    horsepower?: number
    torque?: number
    fuelCapacity?: number
    weight?: number
    length?: number
    width?: number
    height?: number
    wheelbase?: number
    warranty?: {
        basic: string
        powertrain: string
        corrosion: string
    }
    omanCompliance?: {
        ropApproved: boolean
        registrationNumber?: string
        importDate?: Date
        customsClearance?: string
        techicalInspection?: {
            required: boolean
            frequency: string
            nextDue?: Date
        }
    }
    maintenanceSchedule?: MaintenanceItem[]
    commonIssues?: string[]
    commonIssuesAr?: string[]
    partsAvailability?: 'excellent' | 'good' | 'fair' | 'poor'
    estimatedValue?: {
        new: number
        current: number
        currency: 'OMR' | 'USD'
    }
}

export interface MaintenanceItem {
    id: string
    description: string
    descriptionAr?: string
    interval: number
    intervalType: 'km' | 'months'
    category: 'oil_change' | 'filter' | 'brake' | 'transmission' | 'cooling' | 'electrical' | 'suspension'
    priority: 'low' | 'medium' | 'high' | 'critical'
    estimatedCost: {
        parts: number
        labor: number
        total: number
        currency: 'OMR'
    }
    estimatedDuration: number // minutes
}

export interface VINDecodingResult {
    success: boolean
    vin: string
    specification?: VehicleSpecification
    confidence: number
    source: 'nhtsa' | 'autocheck' | 'carmd' | 'local_database' | 'manual'
    decodedAt: Date
    errors?: string[]
    warnings?: string[]
    alternativeSpecs?: VehicleSpecification[]
}

export class VINDecoder {
    private cache: Map<string, VINDecodingResult> = new Map()
    private apiKeys: {
        nhtsa?: string
        autocheck?: string
        carmd?: string
    }
    private arabicVehicleDatabase: Map<string, any> = new Map()
    private omanComplianceDatabase: Map<string, any> = new Map()

    constructor(apiKeys: any = {}) {
        this.apiKeys = apiKeys
        this.initializeArabicDatabase()
        this.initializeOmanDatabase()
    }

    /**
     * Main VIN decoding method with fallback strategy
     */
    async decodeVIN(vin: string, preferArabic: boolean = false): Promise<VINDecodingResult> {
        // Validate VIN format
        if (!this.isValidVIN(vin)) {
            return {
                success: false,
                vin,
                confidence: 0,
                source: 'manual',
                decodedAt: new Date(),
                errors: ['Invalid VIN format']
            }
        }

        // Check cache first
        const cacheKey = `${vin}_${preferArabic}`
        if (this.cache.has(cacheKey)) {
            return this.cache.get(cacheKey)!
        }

        // Try multiple decoding sources with fallback
        const decodingAttempts = [
            () => this.decodeWithNHTSA(vin),
            () => this.decodeWithAutoCheck(vin),
            () => this.decodeWithCarMD(vin),
            () => this.decodeWithLocalDatabase(vin),
            () => this.decodeManually(vin)
        ]

        let result: VINDecodingResult | null = null

        for (const attempt of decodingAttempts) {
            try {
                result = await attempt()
                if (result.success && result.confidence >= 0.7) {
                    break
                }
            } catch (error) {
                console.warn('VIN decoding attempt failed:', error)
            }
        }

        if (!result) {
            result = {
                success: false,
                vin,
                confidence: 0,
                source: 'manual',
                decodedAt: new Date(),
                errors: ['All decoding attempts failed']
            }
        }

        // Enhance with Arabic data and Oman compliance
        if (result.success && result.specification) {
            result.specification = await this.enhanceWithArabicData(result.specification, preferArabic)
            result.specification = await this.addOmanCompliance(result.specification)
            result.specification = await this.generateMaintenanceSchedule(result.specification)
        }

        // Cache the result
        this.cache.set(cacheKey, result)
        return result
    }

    /**
     * NHTSA API decoding (US database)
     */
    private async decodeWithNHTSA(vin: string): Promise<VINDecodingResult> {
        const url = `https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/${vin}?format=json`

        const response = await fetch(url)
        const data = await response.json()

        if (!data.Results || data.Results.length === 0) {
            throw new Error('No NHTSA data found')
        }

        const results = data.Results
        const specification: VehicleSpecification = {
            vin,
            make: this.getValueFromResults(results, 'Make') || '',
            model: this.getValueFromResults(results, 'Model') || '',
            year: parseInt(this.getValueFromResults(results, 'Model Year') || '0'),
            engineSize: this.getValueFromResults(results, 'Engine Number of Cylinders') || '',
            fuelType: this.getValueFromResults(results, 'Fuel Type - Primary') || '',
            transmission: this.getValueFromResults(results, 'Transmission Style') || '',
            drivetrain: this.getValueFromResults(results, 'Drive Type') || '',
            bodyType: this.getValueFromResults(results, 'Body Class') || '',
            countryOfOrigin: this.getValueFromResults(results, 'Plant Country') || '',
            manufacturingPlant: this.getValueFromResults(results, 'Plant Company Name') || '',
            trim: this.getValueFromResults(results, 'Trim') || '',
            doors: parseInt(this.getValueFromResults(results, 'Doors') || '0') || undefined,
            cylinders: parseInt(this.getValueFromResults(results, 'Engine Number of Cylinders') || '0') || undefined,
            displacement: parseFloat(this.getValueFromResults(results, 'Displacement (L)') || '0') || undefined
        }

        return {
            success: true,
            vin,
            specification,
            confidence: 0.9,
            source: 'nhtsa',
            decodedAt: new Date()
        }
    }

    /**
     * AutoCheck API decoding (Commercial service)
     */
    private async decodeWithAutoCheck(vin: string): Promise<VINDecodingResult> {
        if (!this.apiKeys.autocheck) {
            throw new Error('AutoCheck API key not configured')
        }

        // Implementation would go here
        // This is a placeholder for commercial API integration
        throw new Error('AutoCheck integration not implemented yet')
    }

    /**
     * CarMD API decoding (Maintenance focused)
     */
    private async decodeWithCarMD(vin: string): Promise<VINDecodingResult> {
        if (!this.apiKeys.carmd) {
            throw new Error('CarMD API key not configured')
        }

        // Implementation would go here
        // This would provide maintenance schedules and common issues
        throw new Error('CarMD integration not implemented yet')
    }

    /**
     * Local database decoding (Cached data)
     */
    private async decodeWithLocalDatabase(vin: string): Promise<VINDecodingResult> {
        // Extract basic info from VIN structure
        const wmi = vin.substring(0, 3) // World Manufacturer Identifier
        const vds = vin.substring(3, 9) // Vehicle Descriptor Section
        const vis = vin.substring(9, 17) // Vehicle Identifier Section

        const year = this.decodeYearFromVIN(vin.charAt(9))
        const make = this.decodeMakeFromWMI(wmi)

        if (!make || !year) {
            throw new Error('Cannot decode from local database')
        }

        const specification: VehicleSpecification = {
            vin,
            make,
            model: 'Unknown',
            year,
            engineSize: 'Unknown',
            fuelType: 'Unknown',
            transmission: 'Unknown',
            drivetrain: 'Unknown',
            bodyType: 'Unknown',
            countryOfOrigin: this.decodeCountryFromWMI(wmi)
        }

        return {
            success: true,
            vin,
            specification,
            confidence: 0.6,
            source: 'local_database',
            decodedAt: new Date(),
            warnings: ['Limited data from local database']
        }
    }

    /**
     * Manual decoding as last resort
     */
    private async decodeManually(vin: string): Promise<VINDecodingResult> {
        const year = this.decodeYearFromVIN(vin.charAt(9))
        const make = this.decodeMakeFromWMI(vin.substring(0, 3))

        const specification: VehicleSpecification = {
            vin,
            make: make || 'Unknown',
            model: 'Unknown',
            year: year || new Date().getFullYear(),
            engineSize: 'Unknown',
            fuelType: 'Unknown',
            transmission: 'Unknown',
            drivetrain: 'Unknown',
            bodyType: 'Unknown',
            countryOfOrigin: 'Unknown'
        }

        return {
            success: true,
            vin,
            specification,
            confidence: 0.3,
            source: 'manual',
            decodedAt: new Date(),
            warnings: ['Manual decoding - limited accuracy']
        }
    }

    /**
     * Enhance specification with Arabic translations
     */
    private async enhanceWithArabicData(spec: VehicleSpecification, preferArabic: boolean): Promise<VehicleSpecification> {
        if (!preferArabic) return spec

        const arabicData = this.arabicVehicleDatabase.get(`${spec.make}_${spec.model}`)

        if (arabicData) {
            spec.makeAr = arabicData.makeAr
            spec.modelAr = arabicData.modelAr
            spec.fuelTypeAr = this.translateFuelType(spec.fuelType)
            spec.transmissionAr = this.translateTransmission(spec.transmission)
            spec.drivetrainAr = this.translateDrivetrain(spec.drivetrain)
            spec.bodyTypeAr = this.translateBodyType(spec.bodyType)
            spec.countryOfOriginAr = this.translateCountry(spec.countryOfOrigin)
            spec.trimAr = arabicData.trimAr
            spec.colorAr = this.translateColor(spec.color)
        }

        return spec
    }

    /**
     * Add Oman-specific compliance information
     */
    private async addOmanCompliance(spec: VehicleSpecification): Promise<VehicleSpecification> {
        const compliance = this.omanComplianceDatabase.get(spec.vin)

        spec.omanCompliance = {
            ropApproved: compliance?.ropApproved || false,
            registrationNumber: compliance?.registrationNumber,
            importDate: compliance?.importDate,
            customsClearance: compliance?.customsClearance,
            techicalInspection: {
                required: true,
                frequency: 'annual',
                nextDue: this.calculateNextInspectionDate(spec.year)
            }
        }

        return spec
    }

    /**
     * Generate maintenance schedule based on vehicle specs
     */
    private async generateMaintenanceSchedule(spec: VehicleSpecification): Promise<VehicleSpecification> {
        const baseSchedule: MaintenanceItem[] = [
            {
                id: 'oil_change_5000',
                description: 'Engine Oil Change',
                descriptionAr: 'تغيير زيت المحرك',
                interval: 5000,
                intervalType: 'km',
                category: 'oil_change',
                priority: 'high',
                estimatedCost: {
                    parts: 25,
                    labor: 15,
                    total: 40,
                    currency: 'OMR'
                },
                estimatedDuration: 30
            },
            {
                id: 'oil_filter_5000',
                description: 'Oil Filter Replacement',
                descriptionAr: 'تغيير فلتر الزيت',
                interval: 5000,
                intervalType: 'km',
                category: 'filter',
                priority: 'high',
                estimatedCost: {
                    parts: 8,
                    labor: 10,
                    total: 18,
                    currency: 'OMR'
                },
                estimatedDuration: 15
            },
            {
                id: 'air_filter_10000',
                description: 'Air Filter Replacement',
                descriptionAr: 'تغيير فلتر الهواء',
                interval: 10000,
                intervalType: 'km',
                category: 'filter',
                priority: 'medium',
                estimatedCost: {
                    parts: 12,
                    labor: 8,
                    total: 20,
                    currency: 'OMR'
                },
                estimatedDuration: 10
            },
            {
                id: 'brake_pads_25000',
                description: 'Brake Pads Inspection/Replacement',
                descriptionAr: 'فحص/تغيير فحمات الفرامل',
                interval: 25000,
                intervalType: 'km',
                category: 'brake',
                priority: 'critical',
                estimatedCost: {
                    parts: 45,
                    labor: 35,
                    total: 80,
                    currency: 'OMR'
                },
                estimatedDuration: 60
            },
            {
                id: 'transmission_service_40000',
                description: 'Transmission Service',
                descriptionAr: 'خدمة ناقل الحركة',
                interval: 40000,
                intervalType: 'km',
                category: 'transmission',
                priority: 'high',
                estimatedCost: {
                    parts: 60,
                    labor: 40,
                    total: 100,
                    currency: 'OMR'
                },
                estimatedDuration: 90
            },
            {
                id: 'coolant_service_60000',
                description: 'Coolant System Service',
                descriptionAr: 'خدمة نظام التبريد',
                interval: 60000,
                intervalType: 'km',
                category: 'cooling',
                priority: 'medium',
                estimatedCost: {
                    parts: 30,
                    labor: 25,
                    total: 55,
                    currency: 'OMR'
                },
                estimatedDuration: 45
            }
        ]

        // Adjust schedule based on vehicle type and age
        spec.maintenanceSchedule = this.adjustScheduleForVehicle(baseSchedule, spec)

        return spec
    }

    /**
     * Utility methods
     */
    private isValidVIN(vin: string): boolean {
        if (vin.length !== 17) return false
        if (!/^[A-HJ-NPR-Z0-9]+$/i.test(vin)) return false
        if (/[IOQ]/i.test(vin)) return false

        // Check digit validation
        const checkDigit = this.calculateVINCheckDigit(vin)
        return checkDigit === vin.charAt(8)
    }

    private calculateVINCheckDigit(vin: string): string {
        const weights = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]
        const values: { [key: string]: number } = {
            'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8,
            'J': 1, 'K': 2, 'L': 3, 'M': 4, 'N': 5, 'P': 7, 'R': 9, 'S': 2,
            'T': 3, 'U': 4, 'V': 5, 'W': 6, 'X': 7, 'Y': 8, 'Z': 9,
            '0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9
        }

        let sum = 0
        for (let i = 0; i < 17; i++) {
            if (i === 8) continue // Skip check digit position
            sum += values[vin.charAt(i).toUpperCase()] * weights[i]
        }

        const remainder = sum % 11
        return remainder === 10 ? 'X' : remainder.toString()
    }

    private decodeYearFromVIN(yearCode: string): number {
        const yearCodes: { [key: string]: number } = {
            'A': 1980, 'B': 1981, 'C': 1982, 'D': 1983, 'E': 1984, 'F': 1985, 'G': 1986, 'H': 1987,
            'J': 1988, 'K': 1989, 'L': 1990, 'M': 1991, 'N': 1992, 'P': 1993, 'R': 1994, 'S': 1995,
            'T': 1996, 'V': 1997, 'W': 1998, 'X': 1999, 'Y': 2000, '1': 2001, '2': 2002, '3': 2003,
            '4': 2004, '5': 2005, '6': 2006, '7': 2007, '8': 2008, '9': 2009, 'A': 2010, 'B': 2011,
            'C': 2012, 'D': 2013, 'E': 2014, 'F': 2015, 'G': 2016, 'H': 2017, 'J': 2018, 'K': 2019,
            'L': 2020, 'M': 2021, 'N': 2022, 'P': 2023, 'R': 2024, 'S': 2025
        }

        return yearCodes[yearCode.toUpperCase()] || 0
    }

    private decodeMakeFromWMI(wmi: string): string {
        const wmiCodes: { [key: string]: string } = {
            '1FT': 'Ford', '1GC': 'Chevrolet', '1HD': 'Harley-Davidson',
            '2HG': 'Honda', '2T1': 'Toyota', '3VW': 'Volkswagen',
            '4T1': 'Toyota', '5NP': 'Hyundai', '6G2': 'Pontiac',
            'JHM': 'Honda', 'JTD': 'Toyota', 'KNA': 'Kia',
            'WBA': 'BMW', 'WDB': 'Mercedes-Benz', 'WVW': 'Volkswagen'
        }

        return wmiCodes[wmi] || ''
    }

    private decodeCountryFromWMI(wmi: string): string {
        const firstChar = wmi.charAt(0)

        if (['1', '4', '5'].includes(firstChar)) return 'United States'
        if (['2'].includes(firstChar)) return 'Canada'
        if (['3'].includes(firstChar)) return 'Mexico'
        if (['J'].includes(firstChar)) return 'Japan'
        if (['K'].includes(firstChar)) return 'South Korea'
        if (['L'].includes(firstChar)) return 'China'
        if (['S'].includes(firstChar)) return 'United Kingdom'
        if (['W'].includes(firstChar)) return 'Germany'
        if (['V'].includes(firstChar)) return 'France'
        if (['Z'].includes(firstChar)) return 'Italy'

        return 'Unknown'
    }

    private getValueFromResults(results: any[], variable: string): string | null {
        const result = results.find(r => r.Variable === variable)
        return result?.Value || null
    }

    private translateFuelType(fuelType: string): string {
        const translations: { [key: string]: string } = {
            'Gasoline': 'بنزين',
            'Diesel': 'ديزل',
            'Electric': 'كهربائي',
            'Hybrid': 'هجين',
            'CNG': 'غاز طبيعي مضغوط',
            'LPG': 'غاز البترول المسال'
        }
        return translations[fuelType] || fuelType
    }

    private translateTransmission(transmission: string): string {
        const translations: { [key: string]: string } = {
            'Manual': 'يدوي',
            'Automatic': 'أوتوماتيكي',
            'CVT': 'ناقل متغير باستمرار',
            'Semi-Automatic': 'شبه أوتوماتيكي'
        }
        return translations[transmission] || transmission
    }

    private translateDrivetrain(drivetrain: string): string {
        const translations: { [key: string]: string } = {
            'FWD': 'دفع أمامي',
            'RWD': 'دفع خلفي',
            'AWD': 'دفع رباعي',
            '4WD': 'دفع رباعي'
        }
        return translations[drivetrain] || drivetrain
    }

    private translateBodyType(bodyType: string): string {
        const translations: { [key: string]: string } = {
            'Sedan': 'سيدان',
            'SUV': 'سيارة رياضية متعددة الاستخدامات',
            'Hatchback': 'هاتشباك',
            'Coupe': 'كوبيه',
            'Convertible': 'قابل للتحويل',
            'Pickup': 'بيك أب',
            'Van': 'فان',
            'Wagon': 'ستيشن واجن'
        }
        return translations[bodyType] || bodyType
    }

    private translateCountry(country: string): string {
        const translations: { [key: string]: string } = {
            'United States': 'الولايات المتحدة',
            'Japan': 'اليابان',
            'Germany': 'ألمانيا',
            'South Korea': 'كوريا الجنوبية',
            'China': 'الصين',
            'United Kingdom': 'المملكة المتحدة',
            'France': 'فرنسا',
            'Italy': 'إيطاليا',
            'Canada': 'كندا',
            'Mexico': 'المكسيك'
        }
        return translations[country] || country
    }

    private translateColor(color?: string): string | undefined {
        if (!color) return undefined

        const translations: { [key: string]: string } = {
            'Black': 'أسود',
            'White': 'أبيض',
            'Silver': 'فضي',
            'Gray': 'رمادي',
            'Red': 'أحمر',
            'Blue': 'أزرق',
            'Green': 'أخضر',
            'Yellow': 'أصفر',
            'Orange': 'برتقالي',
            'Brown': 'بني',
            'Gold': 'ذهبي',
            'Beige': 'بيج'
        }
        return translations[color] || color
    }

    private calculateNextInspectionDate(vehicleYear: number): Date {
        const age = new Date().getFullYear() - vehicleYear
        const nextInspection = new Date()

        // Oman ROP rules: vehicles over 3 years need annual inspection
        if (age >= 3) {
            nextInspection.setFullYear(nextInspection.getFullYear() + 1)
        } else {
            nextInspection.setFullYear(nextInspection.getFullYear() + (3 - age))
        }

        return nextInspection
    }

    private adjustScheduleForVehicle(schedule: MaintenanceItem[], spec: VehicleSpecification): MaintenanceItem[] {
        // Adjust intervals based on vehicle age, type, and driving conditions in Oman
        const age = new Date().getFullYear() - spec.year
        const isLuxury = ['BMW', 'Mercedes-Benz', 'Audi', 'Lexus', 'Acura'].includes(spec.make)

        return schedule.map(item => {
            let adjustedItem = { ...item }

            // More frequent service for older vehicles
            if (age > 10) {
                adjustedItem.interval = Math.floor(item.interval * 0.8)
            } else if (age > 5) {
                adjustedItem.interval = Math.floor(item.interval * 0.9)
            }

            // Luxury vehicles may need more expensive parts
            if (isLuxury) {
                adjustedItem.estimatedCost = {
                    ...item.estimatedCost,
                    parts: Math.floor(item.estimatedCost.parts * 1.5),
                    total: Math.floor((item.estimatedCost.parts * 1.5) + item.estimatedCost.labor)
                }
            }

            // Adjust for Oman's harsh climate conditions
            if (item.category === 'cooling' || item.category === 'oil_change') {
                adjustedItem.interval = Math.floor(item.interval * 0.85) // More frequent due to heat
            }

            return adjustedItem
        })
    }

    private initializeArabicDatabase(): void {
        // Initialize with common vehicle makes/models in Arabic
        this.arabicVehicleDatabase.set('Toyota_Camry', {
            makeAr: 'تويوتا',
            modelAr: 'كامري',
            trimAr: 'فل'
        })

        this.arabicVehicleDatabase.set('Honda_Accord', {
            makeAr: 'هوندا',
            modelAr: 'أكورد',
            trimAr: 'توريو'
        })

        this.arabicVehicleDatabase.set('Nissan_Altima', {
            makeAr: 'نيسان',
            modelAr: 'ألتيما',
            trimAr: 'فل'
        })

        // Add more as needed...
    }

    private initializeOmanDatabase(): void {
        // Initialize with Oman-specific vehicle data
        // This would typically be loaded from a database
    }

    /**
     * Public methods for integration
     */

    async searchVehicleBySpecs(make: string, model: string, year: number): Promise<VehicleSpecification[]> {
        // Search for vehicles by specifications
        // This would query a database of known vehicles
        return []
    }

    async validateOmanRegistration(plateNumber: string, vin: string): Promise<boolean> {
        // Validate against Oman ROP database
        // This would integrate with government APIs
        return false
    }

    async estimateMaintenanceCosts(vin: string, mileage: number): Promise<MaintenanceItem[]> {
        const result = await this.decodeVIN(vin)
        if (!result.success || !result.specification?.maintenanceSchedule) {
            return []
        }

        return result.specification.maintenanceSchedule.filter(item => {
            // Return items that are due based on mileage
            return mileage >= item.interval
        })
    }

    clearCache(): void {
        this.cache.clear()
    }
}

export default VINDecoder
