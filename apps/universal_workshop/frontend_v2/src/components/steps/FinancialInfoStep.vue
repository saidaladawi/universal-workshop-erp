<template>
  <div class="step-container">
    <div class="step-header">
      <div class="step-icon">💰</div>
      <h2 class="step-title">{{ $t('Financial & VAT Information') }}</h2>
      <p class="step-description">{{ $t('Configure pricing, VAT settings, and payment methods for Oman') }}</p>
    </div>

    <div class="step-content">
      <form @submit.prevent="handleSubmit" class="financial-form">
        <div class="form-section">
          <h3 class="section-title">{{ $t('VAT Configuration (Oman)') }}</h3>
          <div class="vat-info-card">
            <div class="vat-icon">🇴🇲</div>
            <div class="vat-details">
              <div class="vat-title">{{ $t('Oman VAT Rate: 5%') }}</div>
              <div class="vat-description">{{ $t('Standard VAT rate as per Oman Tax Authority regulations') }}</div>
            </div>
          </div>
          
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">{{ $t('VAT Registration Number') }} *</label>
              <input
                v-model="formData.vat_registration_number"
                type="text"
                class="form-control"
                :placeholder="$t('Enter VAT registration number')"
                pattern="[0-9]{15}"
                title="VAT number should be 15 digits"
                required
              />
              <div class="field-help">{{ $t('15-digit VAT registration number') }}</div>
            </div>

            <div class="form-group">
              <label class="form-label">{{ $t('VAT Certificate Upload') }}</label>
              <input
                type="file"
                class="form-control"
                accept=".pdf,.jpg,.jpeg,.png"
                @change="handleVATCertificateUpload"
              />
              <div class="field-help">{{ $t('Upload VAT registration certificate (PDF, JPG, PNG)') }}</div>
            </div>
          </div>
        </div>

        <div class="form-section">
          <h3 class="section-title">{{ $t('Pricing Configuration') }}</h3>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">{{ $t('Currency') }} *</label>
              <select v-model="formData.currency" class="form-control" required>
                <option value="OMR">{{ $t('Omani Rial (OMR)') }}</option>
                <option value="USD">{{ $t('US Dollar (USD)') }}</option>
                <option value="EUR">{{ $t('Euro (EUR)') }}</option>
                <option value="AED">{{ $t('UAE Dirham (AED)') }}</option>
              </select>
            </div>

            <div class="form-group">
              <label class="form-label">{{ $t('Labor Rate (per hour)') }} *</label>
              <div class="input-with-currency">
                <input
                  v-model.number="formData.labor_rate_per_hour"
                  type="number"
                  class="form-control"
                  :placeholder="$t('Enter hourly labor rate')"
                  min="1"
                  step="0.001"
                  required
                />
                <span class="currency-suffix">{{ formData.currency }}</span>
              </div>
            </div>
          </div>

          <div class="pricing-options">
            <label class="pricing-option">
              <input
                type="checkbox"
                v-model="formData.prices_include_vat"
                class="pricing-checkbox"
              />
              <div class="pricing-card">
                <div class="pricing-icon">📊</div>
                <div class="pricing-info">
                  <div class="pricing-title">{{ $t('Prices Include VAT') }}</div>
                  <div class="pricing-description">{{ $t('Display prices with VAT included (tax-inclusive)') }}</div>
                </div>
              </div>
            </label>

            <label class="pricing-option">
              <input
                type="checkbox"
                v-model="formData.auto_calculate_vat"
                class="pricing-checkbox"
              />
              <div class="pricing-card">
                <div class="pricing-icon">🧮</div>
                <div class="pricing-info">
                  <div class="pricing-title">{{ $t('Auto-Calculate VAT') }}</div>
                  <div class="pricing-description">{{ $t('Automatically calculate VAT on all invoices') }}</div>
                </div>
              </div>
            </label>
          </div>
        </div>

        <div class="form-section">
          <h3 class="section-title">{{ $t('Payment Methods') }}</h3>
          <div class="payment-methods-grid">
            <div
              v-for="method in paymentMethods"
              :key="method.key"
              class="payment-method"
            >
              <label class="method-label">
                <input
                  type="checkbox"
                  v-model="formData.accepted_payment_methods"
                  :value="method.key"
                  class="method-checkbox"
                />
                <div class="method-card">
                  <div class="method-icon">{{ method.icon }}</div>
                  <div class="method-info">
                    <div class="method-name">{{ method.name }}</div>
                    <div class="method-description">{{ method.description }}</div>
                  </div>
                </div>
              </label>
            </div>
          </div>
        </div>

        <div class="form-section">
          <h3 class="section-title">{{ $t('Invoice Settings') }}</h3>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">{{ $t('Invoice Number Prefix') }}</label>
              <input
                v-model="formData.invoice_number_prefix"
                type="text"
                class="form-control"
                :placeholder="$t('e.g., INV-, WS-, etc.')"
                maxlength="10"
              />
            </div>

            <div class="form-group">
              <label class="form-label">{{ $t('Starting Invoice Number') }}</label>
              <input
                v-model.number="formData.starting_invoice_number"
                type="number"
                class="form-control"
                :placeholder="$t('Starting number for invoices')"
                min="1"
              />
            </div>
          </div>

          <div class="invoice-options">
            <label class="invoice-option">
              <input
                type="checkbox"
                v-model="formData.qr_code_invoices"
                class="invoice-checkbox"
              />
              <div class="invoice-card">
                <div class="invoice-icon">📱</div>
                <div class="invoice-info">
                  <div class="invoice-title">{{ $t('QR Code on Invoices') }}</div>
                  <div class="invoice-description">{{ $t('Include QR codes for digital payment and verification') }}</div>
                </div>
              </div>
            </label>

            <label class="invoice-option">
              <input
                type="checkbox"
                v-model="formData.digital_receipts"
                class="invoice-checkbox"
              />
              <div class="invoice-card">
                <div class="invoice-icon">📧</div>
                <div class="invoice-info">
                  <div class="invoice-title">{{ $t('Digital Receipts') }}</div>
                  <div class="invoice-description">{{ $t('Send digital receipts via email and SMS') }}</div>
                </div>
              </div>
            </label>
          </div>
        </div>

        <div class="form-section">
          <h3 class="section-title">{{ $t('Financial Reporting') }}</h3>
          <div class="form-group">
            <label class="form-label">{{ $t('Accounting System Integration') }}</label>
            <select v-model="formData.accounting_system" class="form-control">
              <option value="">{{ $t('No integration') }}</option>
              <option value="quickbooks">{{ $t('QuickBooks') }}</option>
              <option value="xero">{{ $t('Xero') }}</option>
              <option value="sage">{{ $t('Sage') }}</option>
              <option value="custom">{{ $t('Custom system') }}</option>
            </select>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label">{{ $t('Financial Year Start') }}</label>
              <input
                v-model="formData.financial_year_start"
                type="date"
                class="form-control"
              />
            </div>

            <div class="form-group">
              <label class="form-label">{{ $t('Tax Filing Frequency') }}</label>
              <select v-model="formData.tax_filing_frequency" class="form-control">
                <option value="monthly">{{ $t('Monthly') }}</option>
                <option value="quarterly">{{ $t('Quarterly') }}</option>
                <option value="annually">{{ $t('Annually') }}</option>
              </select>
            </div>
          </div>
        </div>
      </form>
    </div>

    <div class="step-footer">
      <button
        type="button"
        @click="$emit('previous')"
        class="btn btn-secondary"
      >
        <span class="btn-icon">←</span>
        {{ $t('Previous') }}
      </button>
      
      <button
        type="button"
        @click="handleSubmit"
        class="btn btn-primary"
        :disabled="!isFormValid"
      >
        {{ $t('Continue') }}
        <span class="btn-icon">→</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const emit = defineEmits(['next', 'previous', 'validate'])

const props = defineProps<{
  modelValue?: any
  validationErrors?: any[]
  isLoading?: boolean
}>()

const paymentMethods = [
  {
    key: 'cash',
    name: 'Cash',
    description: 'Traditional cash payments',
    icon: '💵'
  },
  {
    key: 'bank_transfer',
    name: 'Bank Transfer',
    description: 'Direct bank transfers',
    icon: '🏦'
  },
  {
    key: 'credit_card',
    name: 'Credit Card',
    description: 'Visa, Mastercard, etc.',
    icon: '💳'
  },
  {
    key: 'debit_card',
    name: 'Debit Card',
    description: 'Local and international debit cards',
    icon: '💳'
  },
  {
    key: 'mobile_payment',
    name: 'Mobile Payment',
    description: 'Mobile wallets and apps',
    icon: '📱'
  },
  {
    key: 'check',
    name: 'Check',
    description: 'Bank checks',
    icon: '📝'
  }
]

const formData = ref({
  vat_registration_number: '',
  vat_certificate_file: null,
  currency: 'OMR',
  labor_rate_per_hour: 15.000,
  prices_include_vat: true,
  auto_calculate_vat: true,
  accepted_payment_methods: ['cash', 'bank_transfer', 'credit_card'],
  invoice_number_prefix: 'WS-',
  starting_invoice_number: 1,
  qr_code_invoices: true,
  digital_receipts: true,
  accounting_system: '',
  financial_year_start: '',
  tax_filing_frequency: 'quarterly',
  ...props.modelValue
})

const isFormValid = computed(() => {
  return formData.value.vat_registration_number && 
         formData.value.currency && 
         formData.value.labor_rate_per_hour &&
         formData.value.accepted_payment_methods.length > 0
})

const handleVATCertificateUpload = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files[0]) {
    formData.value.vat_certificate_file = target.files[0]
  }
}

const handleSubmit = () => {
  if (isFormValid.value) {
    emit('next')
  }
}

watch(formData, (newValue) => {
  emit('validate', newValue)
}, { deep: true })
</script>

<style scoped lang="scss">
.step-container {
  padding: 2rem;
  max-width: 800px;
  margin: 0 auto;
}

.step-header {
  text-align: center;
  margin-bottom: 2rem;

  .step-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
  }

  .step-title {
    font-size: 1.8rem;
    font-weight: 600;
    color: #1a202c;
    margin-bottom: 0.5rem;
  }

  .step-description {
    color: #718096;
    font-size: 1rem;
    margin: 0;
  }
}

.step-content {
  margin-bottom: 2rem;
}

.form-section {
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid #e2e8f0;

  .section-title {
    font-size: 1.2rem;
    font-weight: 600;
    color: #1a202c;
    margin-bottom: 1rem;
  }
}

.vat-info-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
  border-radius: 8px;
  margin-bottom: 1.5rem;

  .vat-icon {
    font-size: 2rem;
  }

  .vat-title {
    font-weight: 600;
    font-size: 1.1rem;
    margin-bottom: 0.25rem;
  }

  .vat-description {
    font-size: 0.9rem;
    opacity: 0.9;
  }
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
}

.form-group {
  margin-bottom: 1.5rem;

  .form-label {
    display: block;
    font-weight: 500;
    color: #374151;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
  }

  .form-control {
    width: 100%;
    padding: 0.75rem;
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    font-size: 1rem;
    transition: border-color 0.2s;

    &:focus {
      outline: none;
      border-color: #667eea;
      box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
  }

  .field-help {
    font-size: 0.8rem;
    color: #718096;
    margin-top: 0.25rem;
  }
}

.input-with-currency {
  position: relative;

  .currency-suffix {
    position: absolute;
    right: 12px;
    top: 50%;
    transform: translateY(-50%);
    font-weight: 600;
    color: #667eea;
    background: white;
    padding: 0 4px;
  }
}

.pricing-options,
.invoice-options {
  display: grid;
  gap: 1rem;
}

.pricing-option,
.invoice-option {
  display: block;
  cursor: pointer;
  position: relative;

  .pricing-checkbox,
  .invoice-checkbox {
    position: absolute;
    opacity: 0;
    pointer-events: none;
  }

  .pricing-card,
  .invoice-card {
    padding: 1rem;
    background: white;
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    display: flex;
    align-items: center;
    gap: 1rem;
    transition: all 0.2s;

    &:hover {
      border-color: #667eea;
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
    }
  }

  .pricing-checkbox:checked + .pricing-card,
  .invoice-checkbox:checked + .invoice-card {
    border-color: #667eea;
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3);
  }

  .pricing-icon,
  .invoice-icon {
    font-size: 1.5rem;
    min-width: 30px;
    text-align: center;
  }

  .pricing-title,
  .invoice-title {
    font-weight: 600;
    font-size: 1rem;
    margin-bottom: 0.25rem;
  }

  .pricing-description,
  .invoice-description {
    font-size: 0.85rem;
    opacity: 0.9;
    line-height: 1.3;
  }
}

.payment-methods-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.payment-method {
  .method-label {
    display: block;
    cursor: pointer;
    position: relative;
  }

  .method-checkbox {
    position: absolute;
    opacity: 0;
    pointer-events: none;
  }

  .method-card {
    padding: 1rem;
    background: white;
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    display: flex;
    align-items: center;
    gap: 1rem;
    transition: all 0.2s;

    &:hover {
      border-color: #667eea;
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
    }
  }

  .method-checkbox:checked + .method-card {
    border-color: #10b981;
    background: linear-gradient(135deg, #10b981, #059669);
    color: white;
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(16, 185, 129, 0.3);
  }

  .method-icon {
    font-size: 1.5rem;
    min-width: 30px;
    text-align: center;
  }

  .method-name {
    font-weight: 600;
    font-size: 1rem;
    margin-bottom: 0.25rem;
  }

  .method-description {
    font-size: 0.85rem;
    opacity: 0.9;
    line-height: 1.3;
  }
}

.step-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 2rem;
  border-top: 1px solid #e2e8f0;
}

.btn {
  padding: 0.875rem 2rem;
  border: none;
  border-radius: 50px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 0.5rem;

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  &.btn-primary {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);

    &:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
    }
  }

  &.btn-secondary {
    background: rgba(255, 255, 255, 0.9);
    color: #374151;
    border: 2px solid #e2e8f0;

    &:hover:not(:disabled) {
      background: #f7fafc;
      border-color: #cbd5e0;
    }
  }
}

.btn-icon {
  font-size: 1.1rem;
}
</style>