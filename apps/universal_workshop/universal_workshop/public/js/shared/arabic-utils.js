/**
 * Universal Workshop ERP - Arabic Utilities
 * Copyright (c) 2025, Said Al-Adowi and contributors
 * For license information, please see license.txt
 */

/**
 * Arabic Utilities Module
 * Provides comprehensive Arabic language and RTL support
 */
window.ArabicUtils = (function () {
    'use strict';

    // Arabic-Indic numerals mapping
    const ARABIC_NUMERALS = {
        '0': '٠', '1': '١', '2': '٢', '3': '٣', '4': '٤',
        '5': '٥', '6': '٦', '7': '٧', '8': '٨', '9': '٩'
    };

    // Western numerals mapping (reverse)
    const WESTERN_NUMERALS = {
        '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
        '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9'
    };

    // Arabic month names
    const ARABIC_MONTHS = [
        'يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
        'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'
    ];

    // Arabic day names
    const ARABIC_DAYS = [
        'الأحد', 'الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت'
    ];

    // Arabic text direction detection regex
    const ARABIC_REGEX = /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]/;

    /**
     * Check if text contains Arabic characters
     * @param {string} text - Text to check
     * @returns {boolean} True if text contains Arabic characters
     */
    function isArabicText(text) {
        if (!text || typeof text !== 'string') return false;
        return ARABIC_REGEX.test(text);
    }

    /**
     * Determine text direction based on content
     * @param {string} text - Text to analyze
     * @returns {string} 'rtl' or 'ltr'
     */
    function getTextDirection(text) {
        if (!text || typeof text !== 'string') return 'ltr';

        const arabicChars = (text.match(/[\u0600-\u06FF]/g) || []).length;
        const totalChars = text.replace(/\s/g, '').length;

        // If more than 30% Arabic characters, use RTL
        return (arabicChars / totalChars > 0.3) ? 'rtl' : 'ltr';
    }

    /**
     * Convert Western numerals to Arabic-Indic numerals
     * @param {string} text - Text containing Western numerals
     * @returns {string} Text with Arabic-Indic numerals
     */
    function convertToArabicNumerals(text) {
        if (!text || typeof text !== 'string') return text;

        return text.replace(/[0-9]/g, function (digit) {
            return ARABIC_NUMERALS[digit] || digit;
        });
    }

    /**
     * Convert Arabic-Indic numerals to Western numerals
     * @param {string} text - Text containing Arabic-Indic numerals
     * @returns {string} Text with Western numerals
     */
    function convertToWesternNumerals(text) {
        if (!text || typeof text !== 'string') return text;

        return text.replace(/[٠-٩]/g, function (digit) {
            return WESTERN_NUMERALS[digit] || digit;
        });
    }

    /**
     * Format date in Arabic
     * @param {Date|string} date - Date to format
     * @param {boolean} includeDay - Whether to include day name
     * @returns {string} Formatted Arabic date
     */
    function formatArabicDate(date, includeDay = true) {
        if (!date) return '';

        const dateObj = new Date(date);
        if (isNaN(dateObj.getTime())) return '';

        const day = convertToArabicNumerals(dateObj.getDate().toString());
        const month = ARABIC_MONTHS[dateObj.getMonth()];
        const year = convertToArabicNumerals(dateObj.getFullYear().toString());

        if (includeDay) {
            const dayName = ARABIC_DAYS[dateObj.getDay()];
            return `${dayName}، ${day} ${month} ${year}`;
        }

        return `${day} ${month} ${year}`;
    }

    /**
     * Format Arabic time
     * @param {Date|string} date - Date/time to format
     * @param {boolean} use24Hour - Use 24-hour format
     * @returns {string} Formatted Arabic time
     */
    function formatArabicTime(date, use24Hour = true) {
        if (!date) return '';

        const dateObj = new Date(date);
        if (isNaN(dateObj.getTime())) return '';

        let hours = dateObj.getHours();
        const minutes = dateObj.getMinutes().toString().padStart(2, '0');

        if (use24Hour) {
            hours = hours.toString().padStart(2, '0');
            return convertToArabicNumerals(`${hours}:${minutes}`);
        } else {
            const ampm = hours >= 12 ? 'م' : 'ص';
            hours = hours % 12;
            hours = hours ? hours : 12; // 0 should be 12
            return convertToArabicNumerals(`${hours}:${minutes}`) + ' ' + ampm;
        }
    }

    /**
     * Format currency for Oman (OMR)
     * @param {number} amount - Amount to format
     * @param {string} language - Language ('ar' or 'en')
     * @returns {string} Formatted currency
     */
    function formatOmrCurrency(amount, language = 'en') {
        if (typeof amount !== 'number') return '';

        const formattedAmount = amount.toFixed(3);

        if (language === 'ar') {
            const arabicAmount = convertToArabicNumerals(formattedAmount);
            return `ر.ع. ${arabicAmount}`;
        } else {
            return `OMR ${formattedAmount}`;
        }
    }

    /**
     * Apply RTL layout to element
     * @param {HTMLElement} element - Element to apply RTL to
     */
    function applyRTL(element) {
        if (!element) return;

        element.setAttribute('dir', 'rtl');
        element.classList.add('rtl');

        // Apply to form controls
        const formControls = element.querySelectorAll('input, textarea, select');
        formControls.forEach(control => {
            control.style.textAlign = 'right';
            control.style.direction = 'rtl';
        });
    }

    /**
     * Apply LTR layout to element
     * @param {HTMLElement} element - Element to apply LTR to
     */
    function applyLTR(element) {
        if (!element) return;

        element.setAttribute('dir', 'ltr');
        element.classList.remove('rtl');

        // Apply to form controls
        const formControls = element.querySelectorAll('input, textarea, select');
        formControls.forEach(control => {
            control.style.textAlign = 'left';
            control.style.direction = 'ltr';
        });
    }

    /**
     * Auto-detect and apply text direction to element
     * @param {HTMLElement} element - Element to analyze
     */
    function autoDetectDirection(element) {
        if (!element) return;

        const text = element.textContent || element.value || '';
        const direction = getTextDirection(text);

        if (direction === 'rtl') {
            applyRTL(element);
        } else {
            applyLTR(element);
        }
    }

    /**
     * Setup Arabic support for forms
     * @param {HTMLElement} form - Form element to enhance
     */
    function setupArabicForm(form) {
        if (!form) return;

        // Find Arabic fields (fields with _ar suffix or Arabic content)
        const fields = form.querySelectorAll('input, textarea, select');

        fields.forEach(field => {
            const fieldName = field.name || field.id || '';

            // Auto-apply RTL to Arabic fields
            if (fieldName.includes('_ar') || fieldName.includes('arabic')) {
                applyRTL(field);
                field.classList.add('arabic-text');
            }

            // Add event listener for dynamic direction detection
            if (field.tagName === 'INPUT' || field.tagName === 'TEXTAREA') {
                field.addEventListener('input', function () {
                    autoDetectDirection(this);
                });
            }
        });
    }

    /**
     * Setup Arabic support for tables
     * @param {HTMLElement} table - Table element to enhance
     */
    function setupArabicTable(table) {
        if (!table) return;

        // Apply RTL to table if it contains Arabic content
        const cells = table.querySelectorAll('td, th');
        let arabicCellCount = 0;

        cells.forEach(cell => {
            if (isArabicText(cell.textContent)) {
                arabicCellCount++;
                cell.style.textAlign = 'right';
                cell.style.direction = 'rtl';
            }
        });

        // If more than 30% of cells contain Arabic, apply RTL to entire table
        if (arabicCellCount / cells.length > 0.3) {
            applyRTL(table);
        }
    }

    /**
     * Initialize Arabic support for the page
     */
    function initializeArabicSupport() {
        // Check if Arabic language is enabled
        const isArabicEnabled = (
            document.documentElement.lang === 'ar' ||
            document.body.classList.contains('arabic') ||
            (window.frappe && frappe.boot && frappe.boot.lang === 'ar')
        );

        if (isArabicEnabled) {
            // Apply RTL to body
            document.body.setAttribute('dir', 'rtl');
            document.body.classList.add('rtl');

            // Load Arabic fonts
            loadArabicFonts();
        }

        // Setup forms
        const forms = document.querySelectorAll('form');
        forms.forEach(setupArabicForm);

        // Setup tables
        const tables = document.querySelectorAll('table');
        tables.forEach(setupArabicTable);

        // Setup dynamic content observation
        setupDynamicContentObserver();
    }

    /**
     * Load Arabic fonts
     */
    function loadArabicFonts() {
        // Load Google Fonts for Arabic
        const fontLink = document.createElement('link');
        fontLink.href = 'https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700&family=Amiri:wght@400;700&display=swap';
        fontLink.rel = 'stylesheet';
        document.head.appendChild(fontLink);
    }

    /**
     * Setup observer for dynamic content changes
     */
    function setupDynamicContentObserver() {
        const observer = new MutationObserver(function (mutations) {
            mutations.forEach(function (mutation) {
                mutation.addedNodes.forEach(function (node) {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        // Setup Arabic support for new forms
                        if (node.tagName === 'FORM') {
                            setupArabicForm(node);
                        }

                        // Setup Arabic support for new tables
                        if (node.tagName === 'TABLE') {
                            setupArabicTable(node);
                        }

                        // Setup for child elements
                        const childForms = node.querySelectorAll('form');
                        childForms.forEach(setupArabicForm);

                        const childTables = node.querySelectorAll('table');
                        childTables.forEach(setupArabicTable);
                    }
                });
            });
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    /**
     * Validate Arabic text input
     * @param {string} text - Text to validate
     * @returns {object} Validation result
     */
    function validateArabicText(text) {
        if (!text || typeof text !== 'string') {
            return { valid: false, error: 'النص مطلوب' };
        }

        // Check for minimum Arabic content
        if (!isArabicText(text)) {
            return { valid: false, error: 'يجب أن يحتوي النص على أحرف عربية' };
        }

        // Check for prohibited characters (if any)
        const prohibitedChars = /[<>{}]/g;
        if (prohibitedChars.test(text)) {
            return { valid: false, error: 'النص يحتوي على أحرف غير مسموحة' };
        }

        return { valid: true };
    }

    /**
     * Truncate Arabic text while preserving word boundaries
     * @param {string} text - Text to truncate
     * @param {number} maxLength - Maximum length
     * @returns {string} Truncated text
     */
    function truncateArabicText(text, maxLength) {
        if (!text || typeof text !== 'string') return '';
        if (text.length <= maxLength) return text;

        // Find last space before maxLength
        const truncated = text.substring(0, maxLength);
        const lastSpace = truncated.lastIndexOf(' ');

        if (lastSpace > 0) {
            return truncated.substring(0, lastSpace) + '...';
        }

        return truncated + '...';
    }

    // Public API
    return {
        // Text analysis
        isArabicText: isArabicText,
        getTextDirection: getTextDirection,
        validateArabicText: validateArabicText,
        truncateArabicText: truncateArabicText,

        // Number conversion
        convertToArabicNumerals: convertToArabicNumerals,
        convertToWesternNumerals: convertToWesternNumerals,

        // Date and time formatting
        formatArabicDate: formatArabicDate,
        formatArabicTime: formatArabicTime,

        // Currency formatting
        formatOmrCurrency: formatOmrCurrency,

        // Layout and direction
        applyRTL: applyRTL,
        applyLTR: applyLTR,
        autoDetectDirection: autoDetectDirection,

        // Form and table enhancement
        setupArabicForm: setupArabicForm,
        setupArabicTable: setupArabicTable,

        // Initialization
        initializeArabicSupport: initializeArabicSupport,

        // Constants
        ARABIC_MONTHS: ARABIC_MONTHS,
        ARABIC_DAYS: ARABIC_DAYS
    };
})();

// Initialize Arabic support when DOM is ready
document.addEventListener('DOMContentLoaded', function () {
    ArabicUtils.initializeArabicSupport();
});

// Initialize for Frappe framework
if (window.frappe) {
    frappe.ready(function () {
        ArabicUtils.initializeArabicSupport();
    });
}

// Export for Node.js (if applicable)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ArabicUtils;
} 