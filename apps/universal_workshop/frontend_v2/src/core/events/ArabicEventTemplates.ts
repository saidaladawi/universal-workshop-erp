/**
 * Arabic Event Templates - Universal Workshop Frontend V2
 * Phase 3: Sprint 3 Week 2 - Real-Time Event System Enhancement
 *
 * Comprehensive Arabic notification templates for workshop events
 * with Omani cultural considerations and business terminology.
 */

import { WorkshopEventType } from './EventTypes'

// Arabic notification template interface
export interface ArabicEventTemplate {
    id: string
    eventType: WorkshopEventType
    priority: 'critical' | 'high' | 'medium' | 'low'
    category: 'service' | 'customer' | 'technician' | 'inventory' | 'quality' | 'system' | 'financial'
    titleEn: string
    titleAr: string
    messageEn: string
    messageAr: string
    descriptionEn?: string
    descriptionAr?: string
    soundAlert?: boolean
    vibration?: boolean
    actions?: ArabicActionButton[]
    customFields?: Record<string, string>
    culturalNotes?: string
    businessContext?: string
}

// Arabic action button interface
export interface ArabicActionButton {
    id: string
    labelEn: string
    labelAr: string
    action: string
    variant: 'primary' | 'secondary' | 'success' | 'warning' | 'danger' | 'info'
    icon?: string
    requiresConfirmation?: boolean
    confirmationTextEn?: string
    confirmationTextAr?: string
}

// Template variables for dynamic content
export interface TemplateVariables {
    [key: string]: string | number | Date | boolean
}

// Template formatting utilities
export class ArabicTemplateFormatter {
    /**
     * Format Arabic numbers in notification text
     */
    static formatArabicNumbers(text: string, useArabicNumerals: boolean = true): string {
        if (!useArabicNumerals) return text

        const arabicNumerals = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩']
        return text.replace(/\d/g, digit => arabicNumerals[parseInt(digit)])
    }

    /**
     * Format currency in Arabic context
     */
    static formatCurrency(amount: number, currency: 'OMR' | 'USD' = 'OMR', locale: 'ar' | 'en' = 'ar'): string {
        const formatter = new Intl.NumberFormat(locale === 'ar' ? 'ar-OM' : 'en-OM', {
            style: 'currency',
            currency: currency,
            minimumFractionDigits: 3,
            maximumFractionDigits: 3
        })

        return formatter.format(amount)
    }

    /**
     * Format dates in Arabic context
     */
    static formatDate(date: Date, locale: 'ar' | 'en' = 'ar', includeTime: boolean = false): string {
        const options: Intl.DateTimeFormatOptions = {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            ...(includeTime && {
                hour: '2-digit',
                minute: '2-digit',
                hour12: locale === 'en'
            })
        }

        return new Intl.DateTimeFormat(locale === 'ar' ? 'ar-OM' : 'en-OM', options).format(date)
    }

    /**
     * Interpolate template variables into text
     */
    static interpolateTemplate(template: string, variables: TemplateVariables): string {
        return template.replace(/\{(\w+)\}/g, (match, key) => {
            const value = variables[key]
            if (value === undefined) return match

            if (typeof value === 'number') {
                return this.formatArabicNumbers(value.toString())
            } else if (value instanceof Date) {
                return this.formatDate(value, 'ar', true)
            } else {
                return String(value)
            }
        })
    }
}

/**
 * Arabic Event Templates Registry
 * Comprehensive collection of Arabic notification templates
 */
export class ArabicEventTemplateRegistry {
    private templates: Map<string, ArabicEventTemplate> = new Map()

    constructor() {
        this.initializeTemplates()
    }

    /**
     * Get template by ID
     */
    getTemplate(templateId: string): ArabicEventTemplate | undefined {
        return this.templates.get(templateId)
    }

    /**
     * Get templates by event type
     */
    getTemplatesByEventType(eventType: WorkshopEventType): ArabicEventTemplate[] {
        return Array.from(this.templates.values()).filter(template => template.eventType === eventType)
    }

    /**
     * Get templates by category
     */
    getTemplatesByCategory(category: string): ArabicEventTemplate[] {
        return Array.from(this.templates.values()).filter(template => template.category === category)
    }

    /**
     * Add custom template
     */
    addTemplate(template: ArabicEventTemplate): void {
        this.templates.set(template.id, template)
    }

    /**
     * Initialize all default templates
     */
    private initializeTemplates(): void {
        // Service Order Templates
        this.addServiceOrderTemplates()

        // Technician Templates
        this.addTechnicianTemplates()

        // Customer Templates
        this.addCustomerTemplates()

        // Inventory Templates
        this.addInventoryTemplates()

        // Quality Check Templates
        this.addQualityCheckTemplates()

        // System Templates
        this.addSystemTemplates()

        // Financial Templates
        this.addFinancialTemplates()
    }

    /**
     * Service Order Event Templates
     */
    private addServiceOrderTemplates(): void {
        // Service Started
        this.templates.set('service_started', {
            id: 'service_started',
            eventType: 'service_started',
            priority: 'high',
            category: 'service',
            titleEn: 'Service Started',
            titleAr: 'بدء الخدمة',
            messageEn: 'Your {vehicleType} service has been started by technician {technicianName} in bay {bayNumber}',
            messageAr: 'تم بدء خدمة {vehicleType} الخاصة بك بواسطة الفني {technicianName} في الرصيف رقم {bayNumber}',
            descriptionEn: 'We have begun working on your vehicle. Estimated completion time: {estimatedTime}',
            descriptionAr: 'لقد بدأنا العمل على مركبتك. الوقت المتوقع للإنجاز: {estimatedTime}',
            soundAlert: true,
            vibration: true,
            actions: [
                {
                    id: 'view_progress',
                    labelEn: 'View Progress',
                    labelAr: 'عرض التقدم',
                    action: 'view_service_progress',
                    variant: 'primary',
                    icon: 'eye'
                },
                {
                    id: 'contact_workshop',
                    labelEn: 'Contact Workshop',
                    labelAr: 'اتصل بالورشة',
                    action: 'contact_workshop',
                    variant: 'secondary',
                    icon: 'phone'
                }
            ],
            culturalNotes: 'Uses formal Arabic addressing customers with respect',
            businessContext: 'Immediate notification when service begins to maintain transparency'
        })

        // Service Completed
        this.templates.set('service_completed', {
            id: 'service_completed',
            eventType: 'service_completed',
            priority: 'high',
            category: 'service',
            titleEn: 'Service Completed',
            titleAr: 'اكتمال الخدمة',
            messageEn: 'Your {vehicleType} service has been completed successfully. Total cost: {totalCost}',
            messageAr: 'تم إكمال خدمة {vehicleType} الخاصة بك بنجاح. التكلفة الإجمالية: {totalCost}',
            descriptionEn: 'Quality check passed. Your vehicle is ready for pickup. Service duration: {serviceDuration}',
            descriptionAr: 'تم اجتياز فحص الجودة. مركبتك جاهزة للاستلام. مدة الخدمة: {serviceDuration}',
            soundAlert: true,
            vibration: true,
            actions: [
                {
                    id: 'view_invoice',
                    labelEn: 'View Invoice',
                    labelAr: 'عرض الفاتورة',
                    action: 'view_invoice',
                    variant: 'primary',
                    icon: 'file-text'
                },
                {
                    id: 'schedule_pickup',
                    labelEn: 'Schedule Pickup',
                    labelAr: 'جدولة الاستلام',
                    action: 'schedule_pickup',
                    variant: 'success',
                    icon: 'calendar'
                },
                {
                    id: 'pay_now',
                    labelEn: 'Pay Now',
                    labelAr: 'ادفع الآن',
                    action: 'pay_invoice',
                    variant: 'success',
                    icon: 'credit-card'
                }
            ],
            culturalNotes: 'Emphasizes successful completion and quality assurance',
            businessContext: 'Key moment for customer satisfaction and payment conversion'
        })

        // Additional Service Templates
        this.addServiceTemplate('service_paused', 'Service Paused', 'توقف الخدمة مؤقتاً',
            'Your service has been temporarily paused: {pauseReason}',
            'تم إيقاف خدمتك مؤقتاً: {pauseReason}')

        this.addServiceTemplate('service_resumed', 'Service Resumed', 'استئناف الخدمة',
            'Your service has been resumed by technician {technicianName}',
            'تم استئناف خدمتك بواسطة الفني {technicianName}')
    }

    /**
     * Technician Event Templates
     */
    private addTechnicianTemplates(): void {
        // Technician Assigned
        this.templates.set('technician_assigned', {
            id: 'technician_assigned',
            eventType: 'technician_status_changed',
            priority: 'medium',
            category: 'technician',
            titleEn: 'Technician Assigned',
            titleAr: 'تم تعيين فني',
            messageEn: 'Technician {technicianName} has been assigned to your {vehicleType}',
            messageAr: 'تم تعيين الفني {technicianName} لخدمة {vehicleType} الخاصة بك',
            descriptionEn: 'Experience: {experience} years, Specialization: {specialization}',
            descriptionAr: 'الخبرة: {experience} سنة، التخصص: {specialization}',
            soundAlert: false,
            vibration: false,
            actions: [
                {
                    id: 'view_technician_profile',
                    labelEn: 'View Profile',
                    labelAr: 'عرض الملف الشخصي',
                    action: 'view_technician_profile',
                    variant: 'primary',
                    icon: 'user'
                }
            ],
            culturalNotes: 'Builds trust by introducing the technician',
            businessContext: 'Personalizes service experience and builds confidence'
        })

        // Technician Status Updates
        this.addTechnicianStatusTemplate('technician_available', 'Technician Available', 'الفني متاح',
            'Technician {technicianName} is now available for service',
            'الفني {technicianName} متاح الآن للخدمة')

        this.addTechnicianStatusTemplate('technician_busy', 'Technician Busy', 'الفني مشغول',
            'Technician {technicianName} is currently working on another vehicle',
            'الفني {technicianName} يعمل حالياً على مركبة أخرى')
    }

    /**
     * Customer Event Templates
     */
    private addCustomerTemplates(): void {
        // Customer Arrival
        this.templates.set('customer_arrived', {
            id: 'customer_arrived',
            eventType: 'customer_arrived',
            priority: 'high',
            category: 'customer',
            titleEn: 'Customer Arrived',
            titleAr: 'وصول العميل',
            messageEn: 'Welcome to {workshopName}! Your service appointment is confirmed',
            messageAr: 'أهلاً وسهلاً بكم في {workshopName}! تم تأكيد موعد خدمتكم',
            descriptionEn: 'Please proceed to the customer service desk for check-in',
            descriptionAr: 'يرجى التوجه إلى مكتب خدمة العملاء لتسجيل الوصول',
            soundAlert: true,
            vibration: false,
            actions: [
                {
                    id: 'start_checkin',
                    labelEn: 'Start Check-in',
                    labelAr: 'بدء تسجيل الوصول',
                    action: 'start_checkin_process',
                    variant: 'primary',
                    icon: 'check-circle'
                },
                {
                    id: 'view_services',
                    labelEn: 'View Services',
                    labelAr: 'عرض الخدمات',
                    action: 'view_available_services',
                    variant: 'secondary',
                    icon: 'list'
                }
            ],
            culturalNotes: 'Warm traditional Arabic welcome',
            businessContext: 'First impression and immediate service start'
        })

        // Service Estimate
        this.addCustomerTemplate('service_estimate', 'Service Estimate', 'تقدير الخدمة',
            'Service estimate for your {vehicleType}: {estimatedCost}',
            'تقدير الخدمة لمركبة {vehicleType} الخاصة بك: {estimatedCost}')
    }

    /**
     * Inventory Event Templates
     */
    private addInventoryTemplates(): void {
        // Low Inventory Alert
        this.templates.set('parts_inventory_low', {
            id: 'parts_inventory_low',
            eventType: 'parts_inventory_low',
            priority: 'high',
            category: 'inventory',
            titleEn: 'Low Parts Inventory',
            titleAr: 'نقص في مخزون القطع',
            messageEn: 'Low inventory alert for {partName}. Current stock: {currentStock} units',
            messageAr: 'تنبيه نقص مخزون لقطعة {partName}. المخزون الحالي: {currentStock} وحدة',
            descriptionEn: 'Minimum stock level: {minimumStock}. Reorder recommended.',
            descriptionAr: 'مستوى المخزون الأدنى: {minimumStock}. يُنصح بإعادة الطلب.',
            soundAlert: true,
            vibration: false,
            actions: [
                {
                    id: 'reorder_part',
                    labelEn: 'Reorder Now',
                    labelAr: 'إعادة الطلب الآن',
                    action: 'reorder_part',
                    variant: 'warning',
                    icon: 'shopping-cart'
                },
                {
                    id: 'view_suppliers',
                    labelEn: 'View Suppliers',
                    labelAr: 'عرض الموردين',
                    action: 'view_suppliers',
                    variant: 'secondary',
                    icon: 'truck'
                }
            ],
            culturalNotes: 'Urgent tone appropriate for business context',
            businessContext: 'Critical for maintaining service capability'
        })

        // Parts Received
        this.addInventoryTemplate('parts_received', 'Parts Received', 'استلام القطع',
            'Parts delivery received: {partName} - {quantity} units',
            'تم استلام القطع: {partName} - {quantity} وحدة')

        // Parts Ordered
        this.addInventoryTemplate('parts_ordered', 'Parts Ordered', 'طلب القطع',
            'Parts order placed: {partName} - {quantity} units from {supplier}',
            'تم طلب القطع: {partName} - {quantity} وحدة من {supplier}')
    }

    /**
     * Quality Check Event Templates
     */
    private addQualityCheckTemplates(): void {
        // Quality Check Required
        this.templates.set('quality_check_required', {
            id: 'quality_check_required',
            eventType: 'quality_check_required',
            priority: 'high',
            category: 'quality',
            titleEn: 'Quality Check Required',
            titleAr: 'مطلوب فحص جودة',
            messageEn: 'Quality inspection required for {vehicleType} service order #{orderNumber}',
            messageAr: 'مطلوب فحص جودة لطلب خدمة {vehicleType} رقم #{orderNumber}',
            descriptionEn: 'Please perform quality check before vehicle delivery',
            descriptionAr: 'يرجى إجراء فحص الجودة قبل تسليم المركبة',
            soundAlert: true,
            vibration: false,
            actions: [
                {
                    id: 'start_quality_check',
                    labelEn: 'Start Quality Check',
                    labelAr: 'بدء فحص الجودة',
                    action: 'start_quality_check',
                    variant: 'primary',
                    icon: 'check-square'
                }
            ],
            culturalNotes: 'Emphasizes quality assurance importance',
            businessContext: 'Critical step before customer delivery'
        })

        // Quality Check Completed
        this.addQualityTemplate('quality_check_completed', 'Quality Check Completed', 'اكتمال فحص الجودة',
            'Quality check completed for service order #{orderNumber}. Status: {status}',
            'تم إكمال فحص الجودة لطلب الخدمة رقم #{orderNumber}. الحالة: {status}')
    }

    /**
     * System Event Templates
     */
    private addSystemTemplates(): void {
        // System Maintenance
        this.templates.set('system_maintenance', {
            id: 'system_maintenance',
            eventType: 'system_maintenance',
            priority: 'critical',
            category: 'system',
            titleEn: 'System Maintenance',
            titleAr: 'صيانة النظام',
            messageEn: 'Scheduled system maintenance from {startTime} to {endTime}',
            messageAr: 'صيانة نظام مجدولة من {startTime} إلى {endTime}',
            descriptionEn: 'Some features may be temporarily unavailable during maintenance',
            descriptionAr: 'قد تكون بعض الميزات غير متاحة مؤقتاً أثناء الصيانة',
            soundAlert: true,
            vibration: true,
            actions: [
                {
                    id: 'view_maintenance_details',
                    labelEn: 'View Details',
                    labelAr: 'عرض التفاصيل',
                    action: 'view_maintenance_details',
                    variant: 'info',
                    icon: 'info-circle'
                }
            ],
            culturalNotes: 'Professional tone for system communication',
            businessContext: 'Advance notice of service interruption'
        })

        // System Alert
        this.addSystemTemplate('system_alert', 'System Alert', 'تنبيه النظام',
            'System alert: {alertMessage}',
            'تنبيه النظام: {alertMessage}')

        // Backup Status
        this.addSystemTemplate('backup_completed', 'Backup Completed', 'اكتمال النسخ الاحتياطي',
            'System backup completed successfully at {backupTime}',
            'تم إكمال النسخ الاحتياطي للنظام بنجاح في {backupTime}')

        this.addSystemTemplate('backup_failed', 'Backup Failed', 'فشل النسخ الاحتياطي',
            'System backup failed. Please check system logs.',
            'فشل النسخ الاحتياطي للنظام. يرجى فحص سجلات النظام.')
    }

    /**
     * Financial Event Templates
     */
    private addFinancialTemplates(): void {
        // Invoice Generated
        this.templates.set('invoice_generated', {
            id: 'invoice_generated',
            eventType: 'invoice_generated',
            priority: 'high',
            category: 'financial',
            titleEn: 'Invoice Generated',
            titleAr: 'تم إنشاء الفاتورة',
            messageEn: 'Invoice #{invoiceNumber} generated for service order #{orderNumber}',
            messageAr: 'تم إنشاء الفاتورة رقم #{invoiceNumber} لطلب الخدمة رقم #{orderNumber}',
            descriptionEn: 'Total amount: {totalAmount}. Payment due: {dueDate}',
            descriptionAr: 'المبلغ الإجمالي: {totalAmount}. تاريخ استحقاق الدفع: {dueDate}',
            soundAlert: true,
            vibration: false,
            actions: [
                {
                    id: 'view_invoice',
                    labelEn: 'View Invoice',
                    labelAr: 'عرض الفاتورة',
                    action: 'view_invoice',
                    variant: 'primary',
                    icon: 'file-text'
                },
                {
                    id: 'pay_invoice',
                    labelEn: 'Pay Now',
                    labelAr: 'ادفع الآن',
                    action: 'pay_invoice',
                    variant: 'success',
                    icon: 'credit-card'
                }
            ],
            culturalNotes: 'Clear financial communication in Arabic',
            businessContext: 'Revenue collection and customer payment'
        })

        // Payment Received
        this.addFinancialTemplate('payment_received', 'Payment Received', 'تم استلام الدفع',
            'Payment received for invoice #{invoiceNumber}. Amount: {amount}',
            'تم استلام الدفع للفاتورة رقم #{invoiceNumber}. المبلغ: {amount}')

        // Payment Failed
        this.addFinancialTemplate('payment_failed', 'Payment Failed', 'فشل الدفع',
            'Payment failed for invoice #{invoiceNumber}. Reason: {failureReason}',
            'فشل الدفع للفاتورة رقم #{invoiceNumber}. السبب: {failureReason}')
    }

    // Helper methods for creating template variations
    private addServiceTemplate(id: string, titleEn: string, titleAr: string, messageEn: string, messageAr: string): void {
        this.templates.set(id, {
            id,
            eventType: id as WorkshopEventType,
            priority: 'medium',
            category: 'service',
            titleEn,
            titleAr,
            messageEn,
            messageAr,
            soundAlert: false,
            vibration: false,
            actions: []
        })
    }

    private addTechnicianStatusTemplate(id: string, titleEn: string, titleAr: string, messageEn: string, messageAr: string): void {
        this.templates.set(id, {
            id,
            eventType: 'technician_status_changed',
            priority: 'low',
            category: 'technician',
            titleEn,
            titleAr,
            messageEn,
            messageAr,
            soundAlert: false,
            vibration: false,
            actions: []
        })
    }

    private addCustomerTemplate(id: string, titleEn: string, titleAr: string, messageEn: string, messageAr: string): void {
        this.templates.set(id, {
            id,
            eventType: 'customer_notification_sent',
            priority: 'medium',
            category: 'customer',
            titleEn,
            titleAr,
            messageEn,
            messageAr,
            soundAlert: false,
            vibration: false,
            actions: []
        })
    }

    private addInventoryTemplate(id: string, titleEn: string, titleAr: string, messageEn: string, messageAr: string): void {
        this.templates.set(id, {
            id,
            eventType: id as WorkshopEventType,
            priority: 'medium',
            category: 'inventory',
            titleEn,
            titleAr,
            messageEn,
            messageAr,
            soundAlert: false,
            vibration: false,
            actions: []
        })
    }

    private addQualityTemplate(id: string, titleEn: string, titleAr: string, messageEn: string, messageAr: string): void {
        this.templates.set(id, {
            id,
            eventType: id as WorkshopEventType,
            priority: 'high',
            category: 'quality',
            titleEn,
            titleAr,
            messageEn,
            messageAr,
            soundAlert: true,
            vibration: false,
            actions: []
        })
    }

    private addSystemTemplate(id: string, titleEn: string, titleAr: string, messageEn: string, messageAr: string): void {
        this.templates.set(id, {
            id,
            eventType: id as WorkshopEventType,
            priority: 'medium',
            category: 'system',
            titleEn,
            titleAr,
            messageEn,
            messageAr,
            soundAlert: false,
            vibration: false,
            actions: []
        })
    }

    private addFinancialTemplate(id: string, titleEn: string, titleAr: string, messageEn: string, messageAr: string): void {
        this.templates.set(id, {
            id,
            eventType: id as WorkshopEventType,
            priority: 'high',
            category: 'financial',
            titleEn,
            titleAr,
            messageEn,
            messageAr,
            soundAlert: true,
            vibration: false,
            actions: []
        })
    }
}

// Export singleton instance
export const arabicEventTemplateRegistry = new ArabicEventTemplateRegistry()

// Export utility functions for template processing
export const processArabicTemplate = (
    templateId: string,
    variables: TemplateVariables,
    preferArabic: boolean = false
): { title: string; message: string; description?: string; actions: ArabicActionButton[] } | null => {
    const template = arabicEventTemplateRegistry.getTemplate(templateId)
    if (!template) return null

    const title = preferArabic ? template.titleAr : template.titleEn
    const message = preferArabic ? template.messageAr : template.messageEn
    const description = preferArabic ? template.descriptionAr : template.descriptionEn

    return {
        title: ArabicTemplateFormatter.interpolateTemplate(title, variables),
        message: ArabicTemplateFormatter.interpolateTemplate(message, variables),
        description: description ? ArabicTemplateFormatter.interpolateTemplate(description, variables) : undefined,
        actions: template.actions || []
    }
}

// Export template categories for filtering
export const TEMPLATE_CATEGORIES = {
    SERVICE: 'service',
    CUSTOMER: 'customer',
    TECHNICIAN: 'technician',
    INVENTORY: 'inventory',
    QUALITY: 'quality',
    SYSTEM: 'system',
    FINANCIAL: 'financial'
} as const

// Export priority levels
export const TEMPLATE_PRIORITIES = {
    CRITICAL: 'critical',
    HIGH: 'high',
    MEDIUM: 'medium',
    LOW: 'low'
} as const
