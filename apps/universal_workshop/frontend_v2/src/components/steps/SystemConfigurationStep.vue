<template>
  <div class="system-configuration-step">
    <div class="step-header">
      <div class="step-icon">⚙️</div>
      <h2 class="step-title">{{ texts.steps.system_configuration }}</h2>
      <p class="step-description">
        {{ isArabic 
          ? 'قم بتكوين الإعدادات التشغيلية الأساسية لورشتك'
          : 'Configure basic operational settings for your workshop'
        }}
      </p>
    </div>

    <div class="form-container">
      <!-- Operating Hours Section -->
      <div class="settings-section">
        <h3 class="section-title">
          <i>🕒</i>
          {{ isArabic ? 'ساعات العمل' : 'Operating Hours' }}
        </h3>
        
        <div class="time-grid">
          <div class="form-group">
            <label class="form-label">
              {{ isArabic ? 'وقت الافتتاح' : 'Opening Time' }}
              <span class="required">*</span>
            </label>
            <input
              v-model="formData.operating_hours_start"
              type="time"
              class="form-input time-input"
              :class="{ 'error': validationErrors.operating_hours_start }"
            />
            <div v-if="validationErrors.operating_hours_start" class="field-error">
              {{ validationErrors.operating_hours_start }}
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">
              {{ isArabic ? 'وقت الإغلاق' : 'Closing Time' }}
              <span class="required">*</span>
            </label>
            <input
              v-model="formData.operating_hours_end"
              type="time"
              class="form-input time-input"
              :class="{ 'error': validationErrors.operating_hours_end }"
            />
            <div v-if="validationErrors.operating_hours_end" class="field-error">
              {{ validationErrors.operating_hours_end }}
            </div>
          </div>
        </div>

        <!-- Working Days -->
        <div class="form-group">
          <label class="form-label">
            {{ isArabic ? 'أيام العمل' : 'Working Days' }}
          </label>
          <div class="days-selector">
            <div 
              v-for="day in workingDays" 
              :key="day.value"
              class="day-option"
              :class="{ 'selected': formData.working_days.includes(day.value) }"
              @click="toggleWorkingDay(day.value)"
            >
              <div class="day-name">{{ isArabic ? day.name_ar : day.name_en }}</div>
              <div class="day-short">{{ isArabic ? day.short_ar : day.short_en }}</div>
            </div>
          </div>
          <div class="field-hint">
            {{ isArabic 
              ? 'اختر أيام عمل الورشة (الافتراضي: السبت - الخميس)'
              : 'Select workshop working days (Default: Saturday - Thursday)'
            }}
          </div>
        </div>

        <!-- Quick Presets -->
        <div class="time-presets">
          <div class="preset-label">{{ isArabic ? 'إعدادات سريعة:' : 'Quick Presets:' }}</div>
          <div class="preset-buttons">
            <button 
              v-for="preset in timePresets" 
              :key="preset.name"
              @click="applyTimePreset(preset)"
              class="preset-btn"
              type="button"
            >
              {{ isArabic ? preset.name_ar : preset.name_en }}
              <span class="preset-time">{{ preset.start }} - {{ preset.end }}</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Currency & Financial Settings -->
      <div class="settings-section">
        <h3 class="section-title">
          <i>💰</i>
          {{ isArabic ? 'الإعدادات المالية' : 'Financial Settings' }}
        </h3>

        <div class="currency-grid">
          <div class="form-group">
            <label class="form-label">
              {{ isArabic ? 'العملة الأساسية' : 'Primary Currency' }}
              <span class="required">*</span>
            </label>
            <div class="currency-options">
              <div 
                v-for="currency in currencyOptions" 
                :key="currency.code"
                class="currency-option"
                :class="{ 'selected': formData.currency === currency.code }"
                @click="selectCurrency(currency.code)"
              >
                <div class="currency-flag">{{ currency.flag }}</div>
                <div class="currency-info">
                  <div class="currency-name">{{ isArabic ? currency.name_ar : currency.name_en }}</div>
                  <div class="currency-code">{{ currency.code }}</div>
                </div>
                <div class="currency-symbol">{{ currency.symbol }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- VAT Settings -->
        <div class="vat-section">
          <div class="form-group">
            <div class="checkbox-container">
              <label class="checkbox-label">
                <input
                  v-model="formData.vat_registered"
                  type="checkbox"
                  class="checkbox-input"
                  @change="onVatChange"
                />
                <div class="checkbox-custom">
                  <i v-if="formData.vat_registered">✓</i>
                </div>
                <span class="checkbox-text">
                  {{ isArabic 
                    ? 'مسجل في ضريبة القيمة المضافة'
                    : 'VAT Registered Business'
                  }}
                </span>
              </label>
            </div>
            <div class="field-hint">
              {{ isArabic 
                ? 'معدل ضريبة القيمة المضافة في عُمان: 5%'
                : 'Oman VAT rate: 5%'
              }}
            </div>
          </div>

          <div v-if="formData.vat_registered" class="vat-details">
            <div class="form-group">
              <label class="form-label">
                {{ isArabic ? 'رقم التسجيل الضريبي' : 'VAT Registration Number' }}
                <span class="required">*</span>
              </label>
              <input
                v-model="formData.vat_number"
                type="text"
                class="form-input"
                :class="{ 'error': validationErrors.vat_number }"
                :placeholder="isArabic ? 'OMxxxxxxxxxxxxxxx' : 'OMxxxxxxxxxxxxxxx'"
                @input="formatVatNumber"
                maxlength="17"
              />
              <div v-if="validationErrors.vat_number" class="field-error">
                {{ validationErrors.vat_number }}
              </div>
              <div v-else class="field-hint">
                {{ isArabic 
                  ? 'رقم التسجيل الضريبي العماني (OM + 15 رقم)'
                  : 'Oman VAT registration number (OM + 15 digits)'
                }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Service Configuration -->
      <div class="settings-section">
        <h3 class="section-title">
          <i>🔧</i>
          {{ isArabic ? 'إعدادات الخدمة' : 'Service Configuration' }}
        </h3>

        <div class="service-grid">
          <div class="form-group">
            <label class="form-label">
              {{ isArabic ? 'نوع الورشة الأساسي' : 'Primary Workshop Type' }}
            </label>
            <select v-model="formData.workshop_type" class="form-input">
              <option value="">{{ isArabic ? 'اختر نوع الورشة' : 'Select workshop type' }}</option>
              <option value="general">{{ isArabic ? 'صيانة عامة' : 'General Maintenance' }}</option>
              <option value="engine">{{ isArabic ? 'المحركات والقوى المحركة' : 'Engine & Powertrain' }}</option>
              <option value="bodywork">{{ isArabic ? 'أعمال الهيكل والطلاء' : 'Bodywork & Paint' }}</option>
              <option value="electrical">{{ isArabic ? 'الأنظمة الكهربائية' : 'Electrical Systems' }}</option>
              <option value="tires">{{ isArabic ? 'الإطارات والعجلات' : 'Tires & Wheels' }}</option>
              <option value="air_conditioning">{{ isArabic ? 'تكييف الهواء' : 'Air Conditioning' }}</option>
              <option value="specialized">{{ isArabic ? 'متخصص (محددة لاحقاً)' : 'Specialized (Define Later)' }}</option>
            </select>
          </div>

          <div class="form-group">
            <label class="form-label">
              {{ isArabic ? 'السعة اليومية (عدد المركبات)' : 'Daily Capacity (Vehicles)' }}
            </label>
            <div class="capacity-selector">
              <input
                v-model.number="formData.daily_capacity"
                type="number"
                class="form-input capacity-input"
                min="1"
                max="50"
                :placeholder="isArabic ? '10' : '10'"
              />
              <div class="capacity-slider">
                <input
                  v-model.number="formData.daily_capacity"
                  type="range"
                  min="1"
                  max="50"
                  class="slider"
                />
                <div class="slider-labels">
                  <span>1</span>
                  <span>25</span>
                  <span>50+</span>
                </div>
              </div>
            </div>
            <div class="field-hint">
              {{ isArabic 
                ? 'عدد المركبات التي يمكن خدمتها يومياً'
                : 'Number of vehicles that can be serviced daily'
              }}
            </div>
          </div>
        </div>
      </div>

      <!-- System Preferences -->
      <div class="settings-section">
        <h3 class="section-title">
          <i>🌐</i>
          {{ isArabic ? 'تفضيلات النظام' : 'System Preferences' }}
        </h3>

        <div class="preferences-grid">
          <div class="form-group">
            <label class="form-label">
              {{ isArabic ? 'المنطقة الزمنية' : 'Timezone' }}
            </label>
            <select v-model="formData.timezone" class="form-input">
              <option value="Asia/Muscat">{{ isArabic ? 'توقيت مسقط (+04:00)' : 'Muscat Time (+04:00)' }}</option>
              <option value="Asia/Dubai">{{ isArabic ? 'توقيت دبي (+04:00)' : 'Dubai Time (+04:00)' }}</option>
              <option value="Asia/Riyadh">{{ isArabic ? 'توقيت الرياض (+03:00)' : 'Riyadh Time (+03:00)' }}</option>
            </select>
          </div>

          <div class="form-group">
            <label class="form-label">
              {{ isArabic ? 'تنسيق التاريخ' : 'Date Format' }}
            </label>
            <select v-model="formData.date_format" class="form-input">
              <option value="dd/mm/yyyy">DD/MM/YYYY ({{ isArabic ? 'أوروبي' : 'European' }})</option>
              <option value="mm/dd/yyyy">MM/DD/YYYY ({{ isArabic ? 'أمريكي' : 'American' }})</option>
              <option value="yyyy-mm-dd">YYYY-MM-DD (ISO)</option>
            </select>
          </div>
        </div>

        <!-- Notification Settings -->
        <div class="form-group">
          <label class="form-label">
            {{ isArabic ? 'إعدادات الإشعارات' : 'Notification Settings' }}
          </label>
          <div class="notification-options">
            <div class="notification-item">
              <input
                v-model="formData.email_notifications"
                type="checkbox"
                class="checkbox-input"
                id="email-notifications"
              />
              <label for="email-notifications" class="notification-label">
                <div class="checkbox-custom">
                  <i v-if="formData.email_notifications">✓</i>
                </div>
                <div class="notification-content">
                  <div class="notification-title">
                    <i>📧</i>
                    {{ isArabic ? 'إشعارات البريد الإلكتروني' : 'Email Notifications' }}
                  </div>
                  <div class="notification-desc">
                    {{ isArabic ? 'تلقي الإشعارات عبر البريد الإلكتروني' : 'Receive notifications via email' }}
                  </div>
                </div>
              </label>
            </div>

            <div class="notification-item">
              <input
                v-model="formData.sms_notifications"
                type="checkbox"
                class="checkbox-input"
                id="sms-notifications"
              />
              <label for="sms-notifications" class="notification-label">
                <div class="checkbox-custom">
                  <i v-if="formData.sms_notifications">✓</i>
                </div>
                <div class="notification-content">
                  <div class="notification-title">
                    <i>📱</i>
                    {{ isArabic ? 'إشعارات الرسائل النصية' : 'SMS Notifications' }}
                  </div>
                  <div class="notification-desc">
                    {{ isArabic ? 'تلقي الإشعارات عبر الرسائل النصية' : 'Receive notifications via SMS' }}
                  </div>
                </div>
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- Optional Advanced Settings -->
      <div class="settings-section optional">
        <div class="section-header">
          <h3 class="section-title">
            <i>🚀</i>
            {{ isArabic ? 'إعدادات متقدمة (اختيارية)' : 'Advanced Settings (Optional)' }}
          </h3>
          <button 
            type="button"
            @click="showAdvanced = !showAdvanced"
            class="toggle-btn"
          >
            {{ showAdvanced 
              ? (isArabic ? 'إخفاء' : 'Hide')
              : (isArabic ? 'إظهار' : 'Show')
            }}
            <i>{{ showAdvanced ? '↑' : '↓' }}</i>
          </button>
        </div>

        <div v-if="showAdvanced" class="advanced-settings">
          <div class="form-group">
            <label class="form-label">
              {{ isArabic ? 'حد التنبيه لقطع الغيار' : 'Parts Low Stock Alert' }}
            </label>
            <input
              v-model.number="formData.low_stock_threshold"
              type="number"
              class="form-input"
              min="1"
              max="100"
              :placeholder="isArabic ? '10' : '10'"
            />
            <div class="field-hint">
              {{ isArabic 
                ? 'عدد القطع المتبقية للتنبيه عند نفاد المخزون'
                : 'Number of parts remaining to trigger low stock alert'
              }}
            </div>
          </div>

          <div class="form-group">
            <div class="checkbox-container">
              <label class="checkbox-label">
                <input
                  v-model="formData.auto_backup"
                  type="checkbox"
                  class="checkbox-input"
                />
                <div class="checkbox-custom">
                  <i v-if="formData.auto_backup">✓</i>
                </div>
                <span class="checkbox-text">
                  {{ isArabic 
                    ? 'تفعيل النسخ الاحتياطي التلقائي'
                    : 'Enable automatic backup'
                  }}
                </span>
              </label>
            </div>
            <div class="field-hint">
              {{ isArabic 
                ? 'نسخ احتياطي يومي لبيانات الورشة'
                : 'Daily backup of workshop data'
              }}
            </div>
          </div>
        </div>
      </div>

      <!-- Setup Summary -->
      <div class="setup-summary">
        <h3 class="summary-title">
          <i>📋</i>
          {{ isArabic ? 'ملخص الإعداد' : 'Setup Summary' }}
        </h3>
        <div class="summary-content">
          <div class="summary-item">
            <span class="summary-label">{{ isArabic ? 'ساعات العمل:' : 'Operating Hours:' }}</span>
            <span class="summary-value">
              {{ formData.operating_hours_start || '08:00' }} - {{ formData.operating_hours_end || '18:00' }}
            </span>
          </div>
          <div class="summary-item">
            <span class="summary-label">{{ isArabic ? 'العملة:' : 'Currency:' }}</span>
            <span class="summary-value">{{ formData.currency || 'OMR' }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">{{ isArabic ? 'ضريبة القيمة المضافة:' : 'VAT:' }}</span>
            <span class="summary-value">
              {{ formData.vat_registered 
                ? (isArabic ? 'مسجل (5%)' : 'Registered (5%)')
                : (isArabic ? 'غير مسجل' : 'Not registered')
              }}
            </span>
          </div>
          <div class="summary-item">
            <span class="summary-label">{{ isArabic ? 'السعة اليومية:' : 'Daily Capacity:' }}</span>
            <span class="summary-value">{{ formData.daily_capacity || 10 }} {{ isArabic ? 'مركبة' : 'vehicles' }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SystemConfigurationStep',
  props: {
    texts: Object,
    data: Object,
    validationErrors: Object,
    isArabic: Boolean
  },
  
  data() {
    return {
      formData: {
        operating_hours_start: '08:00',
        operating_hours_end: '18:00',
        working_days: ['saturday', 'sunday', 'monday', 'tuesday', 'wednesday', 'thursday'],
        currency: 'OMR',
        vat_registered: false,
        vat_number: '',
        workshop_type: '',
        daily_capacity: 10,
        timezone: 'Asia/Muscat',
        date_format: 'dd/mm/yyyy',
        email_notifications: true,
        sms_notifications: false,
        low_stock_threshold: 10,
        auto_backup: true
      },
      
      showAdvanced: false,
      
      workingDays: [
        { value: 'saturday', name_en: 'Saturday', name_ar: 'السبت', short_en: 'Sat', short_ar: 'سبت' },
        { value: 'sunday', name_en: 'Sunday', name_ar: 'الأحد', short_en: 'Sun', short_ar: 'أحد' },
        { value: 'monday', name_en: 'Monday', name_ar: 'الاثنين', short_en: 'Mon', short_ar: 'اثن' },
        { value: 'tuesday', name_en: 'Tuesday', name_ar: 'الثلاثاء', short_en: 'Tue', short_ar: 'ثلا' },
        { value: 'wednesday', name_en: 'Wednesday', name_ar: 'الأربعاء', short_en: 'Wed', short_ar: 'أرب' },
        { value: 'thursday', name_en: 'Thursday', name_ar: 'الخميس', short_en: 'Thu', short_ar: 'خمي' },
        { value: 'friday', name_en: 'Friday', name_ar: 'الجمعة', short_en: 'Fri', short_ar: 'جمع' }
      ],
      
      timePresets: [
        { 
          name_en: 'Standard', 
          name_ar: 'قياسي',
          start: '08:00', 
          end: '18:00' 
        },
        { 
          name_en: 'Extended', 
          name_ar: 'مُمدد',
          start: '07:00', 
          end: '20:00' 
        },
        { 
          name_en: 'Evening', 
          name_ar: 'مسائي',
          start: '14:00', 
          end: '22:00' 
        }
      ],
      
      currencyOptions: [
        {
          code: 'OMR',
          symbol: 'ر.ع.',
          flag: '🇴🇲',
          name_en: 'Omani Rial',
          name_ar: 'الريال العماني'
        },
        {
          code: 'USD',
          symbol: '$',
          flag: '🇺🇸',
          name_en: 'US Dollar',
          name_ar: 'الدولار الأمريكي'
        },
        {
          code: 'EUR',
          symbol: '€',
          flag: '🇪🇺',
          name_en: 'Euro',
          name_ar: 'اليورو'
        },
        {
          code: 'AED',
          symbol: 'د.إ',
          flag: '🇦🇪',
          name_en: 'UAE Dirham',
          name_ar: 'الدرهم الإماراتي'
        }
      ]
    }
  },
  
  watch: {
    data: {
      immediate: true,
      handler(newData) {
        if (newData) {
          this.formData = { ...this.formData, ...newData }
        }
      }
    },
    
    formData: {
      deep: true,
      handler() {
        this.$emit('update', this.formData)
        this.validateForm()
      }
    }
  },
  
  methods: {
    toggleWorkingDay(day) {
      const index = this.formData.working_days.indexOf(day)
      if (index > -1) {
        this.formData.working_days.splice(index, 1)
      } else {
        this.formData.working_days.push(day)
      }
    },
    
    applyTimePreset(preset) {
      this.formData.operating_hours_start = preset.start
      this.formData.operating_hours_end = preset.end
    },
    
    selectCurrency(code) {
      this.formData.currency = code
    },
    
    onVatChange() {
      if (!this.formData.vat_registered) {
        this.formData.vat_number = ''
      }
    },
    
    formatVatNumber() {
      // Auto-format VAT number for Oman (OM + 15 digits)
      let value = this.formData.vat_number.toUpperCase().replace(/[^OM0-9]/g, '')
      
      if (!value.startsWith('OM')) {
        value = 'OM' + value.replace(/OM/g, '')
      }
      
      // Limit to OM + 15 digits
      if (value.length > 17) {
        value = value.substring(0, 17)
      }
      
      this.formData.vat_number = value
    },
    
    validateForm() {
      const errors = {}
      
      // Validate operating hours
      if (!this.formData.operating_hours_start) {
        errors.operating_hours_start = this.isArabic ? 'وقت الافتتاح مطلوب' : 'Opening time is required'
      }
      
      if (!this.formData.operating_hours_end) {
        errors.operating_hours_end = this.isArabic ? 'وقت الإغلاق مطلوب' : 'Closing time is required'
      }
      
      // Validate time logic
      if (this.formData.operating_hours_start && this.formData.operating_hours_end) {
        const start = new Date(`2000-01-01T${this.formData.operating_hours_start}:00`)
        const end = new Date(`2000-01-01T${this.formData.operating_hours_end}:00`)
        
        if (start >= end) {
          errors.operating_hours_end = this.isArabic 
            ? 'وقت الإغلاق يجب أن يكون بعد وقت الافتتاح'
            : 'Closing time must be after opening time'
        }
      }
      
      // Validate currency
      if (!this.formData.currency) {
        errors.currency = this.isArabic ? 'العملة مطلوبة' : 'Currency is required'
      }
      
      // Validate VAT number if VAT registered
      if (this.formData.vat_registered) {
        if (!this.formData.vat_number) {
          errors.vat_number = this.isArabic ? 'رقم التسجيل الضريبي مطلوب' : 'VAT number is required'
        } else if (!/^OM\d{15}$/.test(this.formData.vat_number)) {
          errors.vat_number = this.isArabic 
            ? 'صيغة رقم التسجيل الضريبي غير صحيحة'
            : 'Invalid VAT number format'
        }
      }
      
      // Validate working days
      if (this.formData.working_days.length === 0) {
        errors.working_days = this.isArabic ? 'يجب اختيار يوم عمل واحد على الأقل' : 'At least one working day must be selected'
      }
      
      const isValid = Object.keys(errors).length === 0
      this.$emit('validate', isValid, errors)
    }
  },
  
  mounted() {
    if (this.data) {
      this.formData = { ...this.formData, ...this.data }
    }
    
    this.validateForm()
  }
}
</script>

<style scoped>
.system-configuration-step {
  max-width: 700px;
  margin: 0 auto;
}

.step-header {
  text-align: center;
  margin-bottom: 3rem;
}

.step-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  display: block;
}

.step-title {
  font-size: 2rem;
  font-weight: 700;
  margin: 0 0 1rem 0;
  color: #1e293b;
}

.step-description {
  font-size: 1.1rem;
  color: #64748b;
  margin: 0;
  line-height: 1.6;
}

.form-container {
  display: flex;
  flex-direction: column;
  gap: 3rem;
}

/* Settings Sections */
.settings-section {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 2rem;
}

.settings-section.optional {
  background: #fafbfc;
  border-color: #e5e7eb;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.4rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 1.5rem 0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.toggle-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 20px;
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.toggle-btn:hover {
  background: #5a67d8;
}

/* Form Controls */
.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.form-label {
  font-weight: 600;
  color: #374151;
  font-size: 1rem;
}

.required {
  color: #ef4444;
}

.form-input {
  width: 100%;
  padding: 1rem;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  font-size: 1rem;
  transition: all 0.3s ease;
  background: white;
}

.form-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-input.error {
  border-color: #ef4444;
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
}

/* Time Grid */
.time-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.time-input {
  font-family: monospace;
  font-size: 1.2rem;
  text-align: center;
}

/* Working Days */
.days-selector {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.day-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.75rem 0.5rem;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: white;
}

.day-option:hover {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.02);
}

.day-option.selected {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.1);
  color: #667eea;
  font-weight: 600;
}

.day-name {
  font-size: 0.8rem;
  font-weight: 600;
}

.day-short {
  font-size: 0.7rem;
  opacity: 0.7;
}

/* Time Presets */
.time-presets {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1rem;
}

.preset-label {
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.75rem;
  font-size: 0.9rem;
}

.preset-buttons {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.preset-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.75rem 1rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.9rem;
}

.preset-btn:hover {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

.preset-time {
  font-size: 0.8rem;
  opacity: 0.7;
  margin-top: 0.25rem;
}

/* Currency Options */
.currency-options {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.currency-option {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: white;
}

.currency-option:hover {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.02);
}

.currency-option.selected {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.05);
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.currency-flag {
  font-size: 2rem;
  flex-shrink: 0;
}

.currency-info {
  flex: 1;
}

.currency-name {
  font-weight: 600;
  color: #1e293b;
}

.currency-code {
  font-size: 0.9rem;
  color: #6b7280;
}

.currency-symbol {
  font-size: 1.5rem;
  font-weight: 700;
  color: #667eea;
}

/* VAT Section */
.vat-section {
  margin-top: 1.5rem;
}

.vat-details {
  margin-top: 1rem;
  padding: 1rem;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

/* Capacity Selector */
.capacity-selector {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.capacity-input {
  max-width: 200px;
}

.capacity-slider {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.slider {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: #e5e7eb;
  outline: none;
  cursor: pointer;
}

.slider::-webkit-slider-thumb {
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #667eea;
  cursor: pointer;
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
  color: #6b7280;
}

/* Checkboxes */
.checkbox-container {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
}

.checkbox-label {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  cursor: pointer;
  line-height: 1.5;
}

.checkbox-input {
  display: none;
}

.checkbox-custom {
  width: 24px;
  height: 24px;
  border: 2px solid #d1d5db;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  flex-shrink: 0;
  margin-top: 0.125rem;
}

.checkbox-input:checked + .checkbox-custom {
  background: #667eea;
  border-color: #667eea;
  color: white;
}

.checkbox-text {
  color: #374151;
  font-size: 0.95rem;
}

/* Notification Options */
.notification-options {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.notification-item {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
}

.notification-label {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  cursor: pointer;
  flex: 1;
  padding: 1rem;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.notification-label:hover {
  border-color: #d1d5db;
  background: #fafbfc;
}

.notification-content {
  flex: 1;
}

.notification-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 0.25rem;
}

.notification-desc {
  font-size: 0.9rem;
  color: #6b7280;
}

/* Setup Summary */
.setup-summary {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.05), rgba(118, 75, 162, 0.05));
  border: 2px solid rgba(102, 126, 234, 0.1);
  border-radius: 16px;
  padding: 2rem;
}

.summary-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.3rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 1.5rem 0;
}

.summary-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: white;
  border-radius: 8px;
  border: 1px solid rgba(102, 126, 234, 0.1);
}

.summary-label {
  font-weight: 600;
  color: #374151;
}

.summary-value {
  color: #667eea;
  font-weight: 600;
}

/* Error and Hint Messages */
.field-error {
  color: #ef4444;
  font-size: 0.9rem;
  margin-top: -0.5rem;
}

.field-hint {
  color: #6b7280;
  font-size: 0.9rem;
  margin-top: -0.5rem;
}

/* Responsive */
@media (max-width: 768px) {
  .time-grid {
    grid-template-columns: 1fr;
  }
  
  .currency-options {
    grid-template-columns: 1fr;
  }
  
  .days-selector {
    grid-template-columns: repeat(4, 1fr);
  }
  
  .summary-content {
    grid-template-columns: 1fr;
  }
  
  .settings-section {
    padding: 1.5rem;
  }
  
  .preset-buttons {
    flex-direction: column;
  }
}
</style>