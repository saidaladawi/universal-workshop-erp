/**
 * Conflict Resolver - Universal Workshop Frontend V2
 * Phase 3: Sprint 3 Week 2 - Real-Time Synchronization
 *
 * Advanced conflict resolution system with Arabic-aware data handling
 * and cultural context preservation for Omani workshop operations.
 */

import { ref, reactive, computed } from 'vue'
import type { SyncConflict, ConflictResolutionOption } from './SyncManager'

// Conflict resolution strategies
export type ConflictResolutionStrategy =
    | 'timestamp_based'    // Most recent wins
    | 'priority_based'     // Based on user role/priority
    | 'field_level'        // Merge at field level
    | 'cultural_aware'     // Consider cultural context
    | 'business_rules'     // Apply business logic
    | 'user_guided'        // Interactive resolution

// Conflict complexity levels
export type ConflictComplexity = 'simple' | 'moderate' | 'complex' | 'critical'

// Arabic-specific conflict context
export interface ArabicConflictContext {
    hasArabicText: boolean
    hasRTLContent: boolean
    culturalImplications: string[]
    businessTerminology: string[]
    translationConsistency: boolean
    formalityLevel: 'formal' | 'informal' | 'mixed'
}

// Field-level conflict information
export interface FieldConflict {
    fieldName: string
    fieldNameAr: string
    localValue: any
    serverValue: any
    dataType: 'text' | 'number' | 'date' | 'boolean' | 'array' | 'object'
    isArabicField: boolean
    businessImpact: 'low' | 'medium' | 'high' | 'critical'
    autoResolvable: boolean
    resolutionSuggestion?: 'local' | 'server' | 'merge' | 'manual'
}

// Conflict resolution result
export interface ConflictResolutionResult {
    success: boolean
    resolvedData: any
    strategy: ConflictResolutionStrategy
    appliedAt: Date
    confidence: number // 0-100
    warnings: string[]
    warningsAr: string[]
    requiresUserConfirmation: boolean
    culturalNotes?: string[]
    businessNotes?: string[]
}

// Merge operation details
export interface MergeOperation {
    id: string
    fieldPath: string
    mergeType: 'replace' | 'append' | 'merge' | 'transform'
    sourceValue: any
    targetValue: any
    mergedValue: any
    confidence: number
    reasoning: string
    reasoningAr: string
}

/**
 * Advanced Conflict Resolver
 * Handles complex data conflicts with Arabic and cultural awareness
 */
export class ConflictResolver {
    private resolutionHistory: Map<string, ConflictResolutionResult[]> = new Map()
    private mergeStrategies: Map<string, (local: any, server: any) => any> = new Map()
    private businessRules: Map<string, (conflict: SyncConflict) => ConflictResolutionResult> = new Map()

    constructor() {
        this.initializeMergeStrategies()
        this.initializeBusinessRules()
    }

    /**
     * Analyze a conflict and determine its complexity
     */
    analyzeConflict(conflict: SyncConflict): {
        complexity: ConflictComplexity
        arabicContext: ArabicConflictContext
        fieldConflicts: FieldConflict[]
        recommendedStrategy: ConflictResolutionStrategy
        autoResolvable: boolean
    } {
        const fieldConflicts = this.analyzeFieldConflicts(conflict.localData, conflict.serverData)
        const arabicContext = this.analyzeArabicContext(conflict)
        const complexity = this.determineComplexity(fieldConflicts, arabicContext)
        const recommendedStrategy = this.recommendStrategy(complexity, arabicContext, conflict)
        const autoResolvable = this.isAutoResolvable(complexity, fieldConflicts)

        console.log(`🔍 Conflict analysis: ${complexity} complexity, ${fieldConflicts.length} field conflicts`)

        return {
            complexity,
            arabicContext,
            fieldConflicts,
            recommendedStrategy,
            autoResolvable
        }
    }

    /**
     * Resolve a conflict using the specified strategy
     */
    async resolveConflict(
        conflict: SyncConflict,
        strategy: ConflictResolutionStrategy,
        userInput?: any
    ): Promise<ConflictResolutionResult> {
        const startTime = Date.now()

        try {
            console.log(`⚡ Resolving conflict ${conflict.id} using ${strategy} strategy`)

            let result: ConflictResolutionResult

            switch (strategy) {
                case 'timestamp_based':
                    result = await this.resolveByTimestamp(conflict)
                    break
                case 'priority_based':
                    result = await this.resolveByPriority(conflict)
                    break
                case 'field_level':
                    result = await this.resolveByFieldLevel(conflict)
                    break
                case 'cultural_aware':
                    result = await this.resolveCulturallyAware(conflict)
                    break
                case 'business_rules':
                    result = await this.resolveByBusinessRules(conflict)
                    break
                case 'user_guided':
                    result = await this.resolveUserGuided(conflict, userInput)
                    break
                default:
                    throw new Error(`Unknown resolution strategy: ${strategy}`)
            }

            // Record resolution in history
            this.recordResolution(conflict.id, result)

            // Calculate resolution time
            const resolutionTime = Date.now() - startTime
            console.log(`✅ Conflict resolved in ${resolutionTime}ms with ${result.confidence}% confidence`)

            return result

        } catch (error) {
            console.error(`❌ Failed to resolve conflict ${conflict.id}:`, error)

            return {
                success: false,
                resolvedData: conflict.localData, // Fallback to local data
                strategy,
                appliedAt: new Date(),
                confidence: 0,
                warnings: [error instanceof Error ? error.message : 'Resolution failed'],
                warningsAr: ['فشل في حل التعارض'],
                requiresUserConfirmation: true
            }
        }
    }

    /**
     * Timestamp-based resolution (most recent wins)
     */
    private async resolveByTimestamp(conflict: SyncConflict): Promise<ConflictResolutionResult> {
        const localTimestamp = this.extractTimestamp(conflict.localData)
        const serverTimestamp = this.extractTimestamp(conflict.serverData)

        const useLocal = localTimestamp > serverTimestamp
        const resolvedData = useLocal ? conflict.localData : conflict.serverData

        return {
            success: true,
            resolvedData,
            strategy: 'timestamp_based',
            appliedAt: new Date(),
            confidence: 85,
            warnings: [],
            warningsAr: [],
            requiresUserConfirmation: false,
            businessNotes: [
                `Used ${useLocal ? 'local' : 'server'} data based on timestamp`,
                `${useLocal ? 'استخدمت البيانات المحلية' : 'استخدمت بيانات الخادم'} بناءً على الوقت`
            ]
        }
    }

    /**
     * Priority-based resolution (based on user role and context)
     */
    private async resolveByPriority(conflict: SyncConflict): Promise<ConflictResolutionResult> {
        const localPriority = this.getUserPriority(conflict.localData)
        const serverPriority = this.getUserPriority(conflict.serverData)

        const useLocal = localPriority >= serverPriority
        const resolvedData = useLocal ? conflict.localData : conflict.serverData

        return {
            success: true,
            resolvedData,
            strategy: 'priority_based',
            appliedAt: new Date(),
            confidence: 80,
            warnings: [],
            warningsAr: [],
            requiresUserConfirmation: false,
            businessNotes: [
                `Resolved based on user priority (${useLocal ? 'local' : 'server'} user has higher priority)`,
                `تم الحل بناءً على أولوية المستخدم`
            ]
        }
    }

    /**
     * Field-level resolution (merge compatible fields)
     */
    private async resolveByFieldLevel(conflict: SyncConflict): Promise<ConflictResolutionResult> {
        const fieldConflicts = this.analyzeFieldConflicts(conflict.localData, conflict.serverData)
        const mergeOperations: MergeOperation[] = []
        const resolvedData = { ...conflict.serverData } // Start with server data as base
        let confidence = 90
        const warnings: string[] = []
        const warningsAr: string[] = []

        for (const fieldConflict of fieldConflicts) {
            try {
                const mergeOp = await this.mergeField(fieldConflict)
                mergeOperations.push(mergeOp)

                // Apply merged value
                this.setNestedProperty(resolvedData, fieldConflict.fieldName, mergeOp.mergedValue)

                // Adjust confidence based on merge quality
                confidence = Math.min(confidence, mergeOp.confidence)

            } catch (error) {
                warnings.push(`Failed to merge field ${fieldConflict.fieldName}: ${error}`)
                warningsAr.push(`فشل في دمج الحقل ${fieldConflict.fieldNameAr}`)
                confidence -= 10
            }
        }

        return {
            success: true,
            resolvedData,
            strategy: 'field_level',
            appliedAt: new Date(),
            confidence: Math.max(confidence, 50),
            warnings,
            warningsAr,
            requiresUserConfirmation: confidence < 70,
            businessNotes: [
                `Merged ${mergeOperations.length} fields automatically`,
                `تم دمج ${mergeOperations.length} حقل تلقائياً`
            ]
        }
    }

    /**
     * Culturally-aware resolution (preserves Arabic context)
     */
    private async resolveCulturallyAware(conflict: SyncConflict): Promise<ConflictResolutionResult> {
        const arabicContext = this.analyzeArabicContext(conflict)
        const resolvedData = { ...conflict.localData }
        const warnings: string[] = []
        const warningsAr: string[] = []
        const culturalNotes: string[] = []

        // Preserve Arabic content consistency
        if (arabicContext.hasArabicText) {
            const arabicFields = this.extractArabicFields(conflict.localData, conflict.serverData)

            for (const [fieldName, { local, server }] of arabicFields) {
                if (this.isArabicContentBetter(local, server)) {
                    resolvedData[fieldName] = local
                    culturalNotes.push(`Preserved local Arabic content in ${fieldName}`)
                } else {
                    resolvedData[fieldName] = server
                    culturalNotes.push(`Used server Arabic content in ${fieldName}`)
                }
            }
        }

        // Preserve cultural business context
        if (arabicContext.culturalImplications.length > 0) {
            culturalNotes.push('Applied cultural context preservation rules')
            culturalNotes.push('تم تطبيق قواعد الحفاظ على السياق الثقافي')
        }

        return {
            success: true,
            resolvedData,
            strategy: 'cultural_aware',
            appliedAt: new Date(),
            confidence: 85,
            warnings,
            warningsAr,
            requiresUserConfirmation: false,
            culturalNotes,
            businessNotes: [
                'Resolution prioritized cultural and linguistic consistency',
                'إعطاء الأولوية للاتساق الثقافي واللغوي في الحل'
            ]
        }
    }

    /**
     * Business rules-based resolution
     */
    private async resolveByBusinessRules(conflict: SyncConflict): Promise<ConflictResolutionResult> {
        const ruleHandler = this.businessRules.get(conflict.entityType)

        if (ruleHandler) {
            return ruleHandler(conflict)
        }

        // Default business rules for workshop entities
        return this.applyDefaultBusinessRules(conflict)
    }

    /**
     * User-guided resolution with interactive input
     */
    private async resolveUserGuided(
        conflict: SyncConflict,
        userInput?: any
    ): Promise<ConflictResolutionResult> {
        if (!userInput) {
            return {
                success: false,
                resolvedData: conflict.localData,
                strategy: 'user_guided',
                appliedAt: new Date(),
                confidence: 0,
                warnings: ['User input required for resolution'],
                warningsAr: ['مطلوب إدخال المستخدم للحل'],
                requiresUserConfirmation: true
            }
        }

        // Apply user choices
        const resolvedData = this.applyUserChoices(conflict, userInput)

        return {
            success: true,
            resolvedData,
            strategy: 'user_guided',
            appliedAt: new Date(),
            confidence: 95, // High confidence with user input
            warnings: [],
            warningsAr: [],
            requiresUserConfirmation: false,
            businessNotes: [
                'Resolution based on user decisions',
                'الحل بناءً على قرارات المستخدم'
            ]
        }
    }

    /**
     * Analyze field-level conflicts
     */
    private analyzeFieldConflicts(localData: any, serverData: any): FieldConflict[] {
        const conflicts: FieldConflict[] = []
        const allKeys = new Set([...Object.keys(localData), ...Object.keys(serverData)])

        for (const key of allKeys) {
            const localValue = localData[key]
            const serverValue = serverData[key]

            if (this.valuesConflict(localValue, serverValue)) {
                conflicts.push({
                    fieldName: key,
                    fieldNameAr: this.getArabicFieldName(key),
                    localValue,
                    serverValue,
                    dataType: this.getDataType(localValue),
                    isArabicField: this.isArabicField(key) || this.containsArabicText(localValue),
                    businessImpact: this.assessBusinessImpact(key, localValue, serverValue),
                    autoResolvable: this.isFieldAutoResolvable(key, localValue, serverValue),
                    resolutionSuggestion: this.suggestFieldResolution(key, localValue, serverValue)
                })
            }
        }

        return conflicts
    }

    /**
     * Analyze Arabic-specific context
     */
    private analyzeArabicContext(conflict: SyncConflict): ArabicConflictContext {
        const localText = JSON.stringify(conflict.localData)
        const serverText = JSON.stringify(conflict.serverData)

        const hasArabicText = /[\u0600-\u06FF]/.test(localText) || /[\u0600-\u06FF]/.test(serverText)
        const hasRTLContent = hasArabicText // Simplified check

        const culturalImplications = this.identifyCulturalImplications(conflict)
        const businessTerminology = this.identifyBusinessTerminology(conflict)

        return {
            hasArabicText,
            hasRTLContent,
            culturalImplications,
            businessTerminology,
            translationConsistency: this.checkTranslationConsistency(conflict),
            formalityLevel: this.determineFormalityLevel(conflict)
        }
    }

    /**
     * Merge a single field with Arabic awareness
     */
    private async mergeField(fieldConflict: FieldConflict): Promise<MergeOperation> {
        const { fieldName, localValue, serverValue, dataType, isArabicField } = fieldConflict

        let mergedValue: any
        let confidence = 80
        let reasoning = 'Automatic field merge'
        let reasoningAr = 'دمج الحقل التلقائي'

        switch (dataType) {
            case 'text':
                if (isArabicField) {
                    mergedValue = this.mergeArabicText(localValue, serverValue)
                    reasoning = 'Arabic text merge with cultural preservation'
                    reasoningAr = 'دمج النص العربي مع الحفاظ على السياق الثقافي'
                } else {
                    mergedValue = this.mergeText(localValue, serverValue)
                }
                break

            case 'number':
                mergedValue = this.mergeNumbers(localValue, serverValue)
                confidence = 90
                break

            case 'date':
                mergedValue = this.mergeDates(localValue, serverValue)
                confidence = 85
                break

            case 'array':
                mergedValue = this.mergeArrays(localValue, serverValue)
                confidence = 75
                break

            case 'object':
                mergedValue = this.mergeObjects(localValue, serverValue)
                confidence = 70
                break

            default:
                mergedValue = localValue // Default to local value
                confidence = 60
                reasoning = 'Default to local value for unknown data type'
                reasoningAr = 'افتراضي للقيمة المحلية لنوع البيانات غير المعروف'
        }

        return {
            id: `merge_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
            fieldPath: fieldName,
            mergeType: 'merge',
            sourceValue: localValue,
            targetValue: serverValue,
            mergedValue,
            confidence,
            reasoning,
            reasoningAr
        }
    }

    // Helper methods for initialization
    private initializeMergeStrategies(): void {
        // Text merging strategy
        this.mergeStrategies.set('text', (local: string, server: string) => {
            if (local.length > server.length) return local
            return server
        })

        // Number merging strategy
        this.mergeStrategies.set('number', (local: number, server: number) => {
            return Math.max(local, server) // Use higher value
        })

        // Date merging strategy
        this.mergeStrategies.set('date', (local: Date, server: Date) => {
            return new Date(Math.max(local.getTime(), server.getTime()))
        })
    }

    private initializeBusinessRules(): void {
        // Service order business rules
        this.businessRules.set('service_order', (conflict: SyncConflict) => {
            const localStatus = conflict.localData.status
            const serverStatus = conflict.serverData.status

            // Business rule: Completed status cannot be overridden
            if (serverStatus === 'completed' && localStatus !== 'completed') {
                return {
                    success: true,
                    resolvedData: conflict.serverData,
                    strategy: 'business_rules',
                    appliedAt: new Date(),
                    confidence: 95,
                    warnings: [],
                    warningsAr: [],
                    requiresUserConfirmation: false,
                    businessNotes: [
                        'Preserved completed service status from server',
                        'تم الحفاظ على حالة الخدمة المكتملة من الخادم'
                    ]
                }
            }

            return this.applyDefaultBusinessRules(conflict)
        })

        // Customer business rules
        this.businessRules.set('customer', (conflict: SyncConflict) => {
            // Always preserve contact information from most recent update
            const resolvedData = { ...conflict.serverData }

            // But keep local preferences and cultural settings
            if (conflict.localData.preferredLanguage) {
                resolvedData.preferredLanguage = conflict.localData.preferredLanguage
            }
            if (conflict.localData.culturalPreferences) {
                resolvedData.culturalPreferences = conflict.localData.culturalPreferences
            }

            return {
                success: true,
                resolvedData,
                strategy: 'business_rules',
                appliedAt: new Date(),
                confidence: 88,
                warnings: [],
                warningsAr: [],
                requiresUserConfirmation: false,
                culturalNotes: [
                    'Preserved cultural preferences and language settings',
                    'تم الحفاظ على التفضيلات الثقافية وإعدادات اللغة'
                ]
            }
        })
    }

    // Helper methods for data analysis and merging
    private determineComplexity(
        fieldConflicts: FieldConflict[],
        arabicContext: ArabicConflictContext
    ): ConflictComplexity {
        if (fieldConflicts.length === 0) return 'simple'

        const criticalConflicts = fieldConflicts.filter(f => f.businessImpact === 'critical').length
        const arabicConflicts = fieldConflicts.filter(f => f.isArabicField).length

        if (criticalConflicts > 0 || arabicContext.culturalImplications.length > 2) {
            return 'critical'
        }

        if (fieldConflicts.length > 5 || arabicConflicts > 2) {
            return 'complex'
        }

        if (fieldConflicts.length > 2 || arabicConflicts > 0) {
            return 'moderate'
        }

        return 'simple'
    }

    private recommendStrategy(
        complexity: ConflictComplexity,
        arabicContext: ArabicConflictContext,
        conflict: SyncConflict
    ): ConflictResolutionStrategy {
        if (complexity === 'critical') return 'user_guided'
        if (arabicContext.hasArabicText && arabicContext.culturalImplications.length > 0) {
            return 'cultural_aware'
        }
        if (complexity === 'complex') return 'field_level'
        if (complexity === 'moderate') return 'business_rules'
        return 'timestamp_based'
    }

    private isAutoResolvable(complexity: ConflictComplexity, fieldConflicts: FieldConflict[]): boolean {
        if (complexity === 'critical') return false
        return fieldConflicts.every(f => f.autoResolvable)
    }

    private valuesConflict(localValue: any, serverValue: any): boolean {
        if (localValue === serverValue) return false
        if (typeof localValue !== typeof serverValue) return true

        if (typeof localValue === 'object' && localValue !== null && serverValue !== null) {
            return JSON.stringify(localValue) !== JSON.stringify(serverValue)
        }

        return true
    }

    private getDataType(value: any): string {
        if (value === null || value === undefined) return 'object'
        if (Array.isArray(value)) return 'array'
        if (value instanceof Date) return 'date'
        return typeof value
    }

    private isArabicField(fieldName: string): boolean {
        return fieldName.endsWith('Ar') || fieldName.endsWith('_ar') || fieldName.includes('arabic')
    }

    private containsArabicText(value: any): boolean {
        if (typeof value === 'string') {
            return /[\u0600-\u06FF]/.test(value)
        }
        return false
    }

    private assessBusinessImpact(fieldName: string, localValue: any, serverValue: any): 'low' | 'medium' | 'high' | 'critical' {
        const criticalFields = ['status', 'payment_status', 'total_amount', 'customer_id']
        const highImpactFields = ['service_date', 'technician_id', 'priority']

        if (criticalFields.includes(fieldName)) return 'critical'
        if (highImpactFields.includes(fieldName)) return 'high'
        if (this.isArabicField(fieldName)) return 'medium'
        return 'low'
    }

    private isFieldAutoResolvable(fieldName: string, localValue: any, serverValue: any): boolean {
        // Critical business fields require manual resolution
        const manualFields = ['status', 'payment_status', 'total_amount']
        if (manualFields.includes(fieldName)) return false

        // Simple data types are generally auto-resolvable
        const dataType = this.getDataType(localValue)
        return ['text', 'number', 'date'].includes(dataType)
    }

    private suggestFieldResolution(fieldName: string, localValue: any, serverValue: any): 'local' | 'server' | 'merge' | 'manual' {
        const dataType = this.getDataType(localValue)

        if (this.assessBusinessImpact(fieldName, localValue, serverValue) === 'critical') {
            return 'manual'
        }

        if (dataType === 'text' && !this.isArabicField(fieldName)) {
            return 'merge'
        }

        return 'server' // Default to server for simplicity
    }

    private getArabicFieldName(fieldName: string): string {
        const arabicFieldNames: Record<string, string> = {
            'name': 'الاسم',
            'description': 'الوصف',
            'status': 'الحالة',
            'notes': 'الملاحظات',
            'address': 'العنوان',
            'phone': 'الهاتف',
            'email': 'البريد الإلكتروني'
        }

        return arabicFieldNames[fieldName] || fieldName
    }

    private extractTimestamp(data: any): number {
        if (data.updatedAt) return new Date(data.updatedAt).getTime()
        if (data.modifiedAt) return new Date(data.modifiedAt).getTime()
        if (data.timestamp) return new Date(data.timestamp).getTime()
        return 0
    }

    private getUserPriority(data: any): number {
        if (data.userRole === 'admin') return 100
        if (data.userRole === 'manager') return 80
        if (data.userRole === 'technician') return 60
        if (data.userRole === 'customer') return 40
        return 50 // Default priority
    }

    private setNestedProperty(obj: any, path: string, value: any): void {
        const keys = path.split('.')
        let current = obj

        for (let i = 0; i < keys.length - 1; i++) {
            if (!(keys[i] in current)) {
                current[keys[i]] = {}
            }
            current = current[keys[i]]
        }

        current[keys[keys.length - 1]] = value
    }

    private extractArabicFields(localData: any, serverData: any): Map<string, { local: any; server: any }> {
        const arabicFields = new Map<string, { local: any; server: any }>()

        for (const key of Object.keys(localData)) {
            if (this.isArabicField(key) || this.containsArabicText(localData[key])) {
                arabicFields.set(key, {
                    local: localData[key],
                    server: serverData[key]
                })
            }
        }

        return arabicFields
    }

    private isArabicContentBetter(local: any, server: any): boolean {
        if (typeof local !== 'string' || typeof server !== 'string') return false

        // Prefer longer, more complete Arabic text
        if (local.length > server.length && /[\u0600-\u06FF]/.test(local)) return true

        // Prefer text with proper Arabic punctuation and formatting
        const arabicPunctuation = /[،؛؟]/
        if (arabicPunctuation.test(local) && !arabicPunctuation.test(server)) return true

        return false
    }

    private identifyCulturalImplications(conflict: SyncConflict): string[] {
        const implications: string[] = []

        // Check for cultural markers in data
        if (conflict.localData.country === 'OM' || conflict.serverData.country === 'OM') {
            implications.push('omani_context')
        }

        if (conflict.isArabicContent) {
            implications.push('arabic_language')
            implications.push('rtl_layout')
        }

        return implications
    }

    private identifyBusinessTerminology(conflict: SyncConflict): string[] {
        const terminology: string[] = []

        const businessTerms = ['ريال', 'عماني', 'ورشة', 'صيانة', 'قطع غيار']
        const dataStr = JSON.stringify(conflict.localData) + JSON.stringify(conflict.serverData)

        for (const term of businessTerms) {
            if (dataStr.includes(term)) {
                terminology.push(term)
            }
        }

        return terminology
    }

    private checkTranslationConsistency(conflict: SyncConflict): boolean {
        // Check if Arabic and English versions are consistent
        const data = { ...conflict.localData, ...conflict.serverData }

        for (const key of Object.keys(data)) {
            if (key.endsWith('Ar')) {
                const englishKey = key.replace('Ar', '')
                if (data[englishKey] && data[key]) {
                    // Basic consistency check (would be more sophisticated in practice)
                    return true
                }
            }
        }

        return false
    }

    private determineFormalityLevel(conflict: SyncConflict): 'formal' | 'informal' | 'mixed' {
        const arabicText = Object.values(conflict.localData)
            .concat(Object.values(conflict.serverData))
            .filter(v => typeof v === 'string' && /[\u0600-\u06FF]/.test(v))
            .join(' ')

        // Simple heuristic for formality detection
        const formalMarkers = ['سيادتكم', 'حضرتكم', 'المحترم']
        const informalMarkers = ['أهلاً', 'مرحباً']

        const hasFormal = formalMarkers.some(marker => arabicText.includes(marker))
        const hasInformal = informalMarkers.some(marker => arabicText.includes(marker))

        if (hasFormal && hasInformal) return 'mixed'
        if (hasFormal) return 'formal'
        if (hasInformal) return 'informal'
        return 'formal' // Default to formal for business context
    }

    private applyDefaultBusinessRules(conflict: SyncConflict): ConflictResolutionResult {
        // Default: Use server data but preserve local user preferences
        const resolvedData = { ...conflict.serverData }

        // Preserve local preferences
        const preferenceFields = ['language', 'theme', 'notifications', 'culturalPreferences']
        for (const field of preferenceFields) {
            if (conflict.localData[field] !== undefined) {
                resolvedData[field] = conflict.localData[field]
            }
        }

        return {
            success: true,
            resolvedData,
            strategy: 'business_rules',
            appliedAt: new Date(),
            confidence: 75,
            warnings: [],
            warningsAr: [],
            requiresUserConfirmation: false,
            businessNotes: [
                'Applied default business rules with preference preservation',
                'تم تطبيق قواعد العمل الافتراضية مع الحفاظ على التفضيلات'
            ]
        }
    }

    private applyUserChoices(conflict: SyncConflict, userInput: any): any {
        const resolvedData = { ...conflict.localData }

        // Apply user's field-by-field choices
        if (userInput.fieldChoices) {
            for (const [field, choice] of Object.entries(userInput.fieldChoices)) {
                if (choice === 'local') {
                    resolvedData[field] = conflict.localData[field]
                } else if (choice === 'server') {
                    resolvedData[field] = conflict.serverData[field]
                } else if (choice === 'custom' && userInput.customValues?.[field]) {
                    resolvedData[field] = userInput.customValues[field]
                }
            }
        }

        return resolvedData
    }

    private mergeArabicText(local: string, server: string): string {
        // Preserve Arabic text with better cultural context
        if (local.length > server.length && /[\u0600-\u06FF]/.test(local)) {
            return local
        }
        return server
    }

    private mergeText(local: string, server: string): string {
        // Simple text merge - could be more sophisticated
        return local.length > server.length ? local : server
    }

    private mergeNumbers(local: number, server: number): number {
        // Use the more recent/higher value for numbers
        return Math.max(local, server)
    }

    private mergeDates(local: Date, server: Date): Date {
        // Use the more recent date
        return new Date(Math.max(local.getTime(), server.getTime()))
    }

    private mergeArrays(local: any[], server: any[]): any[] {
        // Merge arrays by combining unique elements
        const combined = [...local, ...server]
        return Array.from(new Set(combined.map(JSON.stringify))).map(JSON.parse)
    }

    private mergeObjects(local: any, server: any): any {
        // Deep merge objects
        return { ...server, ...local }
    }

    private recordResolution(conflictId: string, result: ConflictResolutionResult): void {
        if (!this.resolutionHistory.has(conflictId)) {
            this.resolutionHistory.set(conflictId, [])
        }
        this.resolutionHistory.get(conflictId)!.push(result)
    }

    // Public methods for getting resolution history and statistics
    getResolutionHistory(conflictId?: string): ConflictResolutionResult[] | Map<string, ConflictResolutionResult[]> {
        if (conflictId) {
            return this.resolutionHistory.get(conflictId) || []
        }
        return this.resolutionHistory
    }

    getResolutionStatistics() {
        let totalResolutions = 0
        let successfulResolutions = 0
        const strategyUsage = new Map<ConflictResolutionStrategy, number>()

        for (const results of this.resolutionHistory.values()) {
            for (const result of results) {
                totalResolutions++
                if (result.success) successfulResolutions++

                const count = strategyUsage.get(result.strategy) || 0
                strategyUsage.set(result.strategy, count + 1)
            }
        }

        return {
            totalResolutions,
            successfulResolutions,
            successRate: totalResolutions > 0 ? (successfulResolutions / totalResolutions) * 100 : 0,
            strategyUsage: Object.fromEntries(strategyUsage)
        }
    }
}

// Export singleton instance
export const conflictResolver = new ConflictResolver()

// Export for use in composables
export function useConflictResolver() {
    return {
        conflictResolver,
        analyzeConflict: conflictResolver.analyzeConflict.bind(conflictResolver),
        resolveConflict: conflictResolver.resolveConflict.bind(conflictResolver),
        getResolutionHistory: conflictResolver.getResolutionHistory.bind(conflictResolver),
        getResolutionStatistics: conflictResolver.getResolutionStatistics.bind(conflictResolver)
    }
}
