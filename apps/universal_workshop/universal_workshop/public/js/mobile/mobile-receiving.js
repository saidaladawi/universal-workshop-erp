/**
 * Universal Workshop ERP - Mobile Receiving Interface
 * Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
 * 
 * Comprehensive mobile interface for Purchase Receipt, Quality Inspection,
 * and barcode scanning with Arabic RTL support.
 */

class MobileReceivingInterface {
    constructor() {
        this.currentLanguage = 'en';
        this.isScanning = false;
        this.currentForm = null;
        this.scannedItems = [];
        this.pendingReceipts = [];

        // Arabic translations
        this.translations = {
            'ar': {
                'receive_goods': 'استلام البضائع',
                'quality_check': 'فحص الجودة',
                'scan_items': 'مسح العناصر',
                'pending_receipts': 'الإيصالات المعلقة',
                'process_deliveries': 'معالجة التسليمات الواردة',
                'inspect_received_items': 'فحص العناصر المستلمة',
                'use_camera_to_scan': 'استخدم الكاميرا لمسح الباركود',
                'view_outstanding_orders': 'عرض الطلبات المعلقة',
                'barcode_scanner': 'ماسح الباركود',
                'start_scanning': 'بدء المسح',
                'stop_scanning': 'إيقاف المسح',
                'mobile_receiving': 'الاستقبال المحمول',
                'scanner': 'الماسح',
                'purchase_order': 'طلب شراء',
                'supplier': 'المورد',
                'item_code': 'كود العنصر',
                'quantity': 'الكمية',
                'received_qty': 'الكمية المستلمة',
                'notes': 'ملاحظات',
                'save_receipt': 'حفظ الإيصال',
                'quality_inspection': 'فحص الجودة',
                'inspection_status': 'حالة الفحص',
                'accepted': 'مقبول',
                'rejected': 'مرفوض',
                'sample_size': 'حجم العينة',
                'remarks': 'ملاحظات',
                'save_inspection': 'حفظ الفحص',
                'cancel': 'إلغاء',
                'loading': 'جاري التحميل...',
                'success': 'نجح',
                'error': 'خطأ',
                'warning': 'تحذير',
                'item_scanned_successfully': 'تم مسح العنصر بنجاح',
                'barcode_not_found': 'لم يتم العثور على الباركود',
                'camera_access_denied': 'تم رفض الوصول للكاميرا',
                'form_saved_successfully': 'تم حفظ النموذج بنجاح',
                'please_fill_required_fields': 'يرجى ملء الحقول المطلوبة',
                'confirm_submit': 'هل تريد إرسال هذا النموذج؟',
                'yes': 'نعم',
                'no': 'لا'
            }
        };

        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupLanguageToggle();
        this.loadPendingReceipts();
        this.setupBarcodeScanner();

        // Check if running as PWA
        if (window.navigator.standalone || window.matchMedia('(display-mode: standalone)').matches) {
            document.body.classList.add('pwa-mode');
        }
    }

    setupEventListeners() {
        // Quick action cards
        document.querySelectorAll('.quick-action-card').forEach(card => {
            card.addEventListener('click', () => {
                const action = card.dataset.action;
                this.handleQuickAction(action);
            });
        });

        // Scanner controls
        document.getElementById('scan-mode-toggle').addEventListener('click', () => {
            this.toggleScannerInterface();
        });

        document.getElementById('start-scan').addEventListener('click', () => {
            this.startBarcodeScanning();
        });

        document.getElementById('stop-scan').addEventListener('click', () => {
            this.stopBarcodeScanning();
        });

        // Form submissions
        document.addEventListener('submit', (e) => {
            if (e.target.classList.contains('mobile-form')) {
                e.preventDefault();
                this.handleFormSubmission(e.target);
            }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch (e.key) {
                    case 's':
                        e.preventDefault();
                        this.saveCurrentForm();
                        break;
                    case 'b':
                        e.preventDefault();
                        this.toggleScannerInterface();
                        break;
                }
            }
        });
    }

    setupLanguageToggle() {
        const toggleBtn = document.getElementById('toggle-language');
        const langText = document.getElementById('lang-text');

        toggleBtn.addEventListener('click', () => {
            this.currentLanguage = this.currentLanguage === 'en' ? 'ar' : 'en';
            this.updateLanguage();

            // Update button text
            langText.textContent = this.currentLanguage === 'en' ? 'عربي' : 'English';
        });
    }

    updateLanguage() {
        const html = document.documentElement;
        const isArabic = this.currentLanguage === 'ar';

        // Update HTML attributes
        html.setAttribute('lang', this.currentLanguage);
        html.setAttribute('dir', isArabic ? 'rtl' : 'ltr');

        // Update all translatable elements
        document.querySelectorAll('[data-translate]').forEach(element => {
            const key = element.dataset.translate;
            if (isArabic && this.translations.ar[key]) {
                element.textContent = this.translations.ar[key];
            } else {
                // Fallback to English or original text
                const originalText = element.getAttribute('data-original') || element.textContent;
                element.textContent = originalText;
            }
        });

        // Update header title
        const headerTitle = document.getElementById('header-title');
        headerTitle.textContent = isArabic ? 'الاستقبال المحمول' : 'Mobile Receiving';

        // Update scan text
        const scanText = document.getElementById('scan-text');
        scanText.textContent = isArabic ? 'الماسح' : 'Scanner';
    }

    handleQuickAction(action) {
        this.clearFormsContainer();

        switch (action) {
            case 'purchase-receipt':
                this.showPurchaseReceiptForm();
                break;
            case 'quality-inspection':
                this.showQualityInspectionForm();
                break;
            case 'barcode-scan':
                this.toggleScannerInterface();
                break;
            case 'pending-receipts':
                this.showPendingReceipts();
                break;
        }
    }

    showPurchaseReceiptForm() {
        const isArabic = this.currentLanguage === 'ar';

        const formHtml = `
            <form class="mobile-form" data-doctype="Purchase Receipt">
                <div class="form-section">
                    <h2 class="section-title">${isArabic ? 'إيصال شراء جديد' : 'New Purchase Receipt'}</h2>
                    
                    <div class="form-row">
                        <label class="form-label" for="purchase_order">${isArabic ? 'طلب الشراء' : 'Purchase Order'} *</label>
                        <select class="form-input" id="purchase_order" name="purchase_order" required>
                            <option value="">${isArabic ? 'اختر طلب شراء' : 'Select Purchase Order'}</option>
                        </select>
                    </div>
                    
                    <div class="form-row">
                        <label class="form-label" for="supplier">${isArabic ? 'المورد' : 'Supplier'}</label>
                        <input type="text" class="form-input" id="supplier" name="supplier" readonly>
                    </div>
                    
                    <div class="form-row">
                        <label class="form-label" for="posting_date">${isArabic ? 'تاريخ الاستلام' : 'Posting Date'} *</label>
                        <input type="date" class="form-input" id="posting_date" name="posting_date" required>
                    </div>
                </div>
                
                <div class="form-section">
                    <h3 class="section-title">${isArabic ? 'العناصر' : 'Items'}</h3>
                    
                    <div class="form-row">
                        <label class="form-label" for="barcode_scan">${isArabic ? 'مسح الباركود' : 'Scan Barcode'}</label>
                        <input type="text" class="form-input barcode-input" id="barcode_scan" 
                               placeholder="${isArabic ? 'امسح أو اكتب الباركود' : 'Scan or type barcode'}"
                               autocomplete="off">
                    </div>
                    
                    <div id="scanned-items" class="item-list"></div>
                    
                    <div id="manual-item-entry" style="display: none;">
                        <div class="form-row">
                            <label class="form-label" for="item_code">${isArabic ? 'كود العنصر' : 'Item Code'} *</label>
                            <input type="text" class="form-input" id="item_code" name="item_code">
                        </div>
                        
                        <div class="form-row">
                            <label class="form-label" for="received_qty">${isArabic ? 'الكمية المستلمة' : 'Received Quantity'} *</label>
                            <input type="number" class="form-input" id="received_qty" name="received_qty" min="0" step="0.01">
                        </div>
                        
                        <button type="button" class="btn btn-primary" onclick="mobileReceiving.addManualItem()">
                            ${isArabic ? 'إضافة عنصر' : 'Add Item'}
                        </button>
                    </div>
                </div>
                
                <div class="form-section">
                    <div class="form-row">
                        <label class="form-label" for="notes">${isArabic ? 'ملاحظات' : 'Notes'}</label>
                        <textarea class="form-input" id="notes" name="notes" rows="3" 
                                  placeholder="${isArabic ? 'إضافة ملاحظات اختيارية' : 'Add optional notes'}"></textarea>
                    </div>
                    
                    <div style="display: flex; gap: 1rem; margin-top: 1rem;">
                        <button type="submit" class="btn btn-success btn-full">
                            <span class="loading" style="display: none;"></span>
                            ${isArabic ? 'حفظ الإيصال' : 'Save Receipt'}
                        </button>
                        <button type="button" class="btn btn-secondary" onclick="mobileReceiving.clearFormsContainer()">
                            ${isArabic ? 'إلغاء' : 'Cancel'}
                        </button>
                    </div>
                </div>
            </form>
        `;

        this.insertForm(formHtml);
        this.setupPurchaseReceiptForm();
    }

    showQualityInspectionForm() {
        const isArabic = this.currentLanguage === 'ar';

        const formHtml = `
            <form class="mobile-form" data-doctype="Quality Inspection">
                <div class="form-section">
                    <h2 class="section-title">${isArabic ? 'فحص جودة جديد' : 'New Quality Inspection'}</h2>
                    
                    <div class="form-row">
                        <label class="form-label" for="reference_type">${isArabic ? 'نوع المرجع' : 'Reference Type'} *</label>
                        <select class="form-input" id="reference_type" name="reference_type" required>
                            <option value="Purchase Receipt">${isArabic ? 'إيصال شراء' : 'Purchase Receipt'}</option>
                            <option value="Stock Entry">${isArabic ? 'إدخال مخزون' : 'Stock Entry'}</option>
                        </select>
                    </div>
                    
                    <div class="form-row">
                        <label class="form-label" for="reference_name">${isArabic ? 'رقم المرجع' : 'Reference Number'} *</label>
                        <select class="form-input" id="reference_name" name="reference_name" required>
                            <option value="">${isArabic ? 'اختر مرجع' : 'Select Reference'}</option>
                        </select>
                    </div>
                    
                    <div class="form-row">
                        <label class="form-label" for="item_code">${isArabic ? 'كود العنصر' : 'Item Code'} *</label>
                        <input type="text" class="form-input barcode-input" id="item_code" name="item_code" required
                               placeholder="${isArabic ? 'امسح أو اكتب كود العنصر' : 'Scan or type item code'}">
                    </div>
                    
                    <div class="form-row">
                        <label class="form-label" for="sample_size">${isArabic ? 'حجم العينة' : 'Sample Size'} *</label>
                        <input type="number" class="form-input" id="sample_size" name="sample_size" min="1" required>
                    </div>
                </div>
                
                <div class="form-section">
                    <h3 class="section-title">${isArabic ? 'نتائج الفحص' : 'Inspection Results'}</h3>
                    
                    <div class="form-row">
                        <label class="form-label">${isArabic ? 'حالة الفحص' : 'Inspection Status'} *</label>
                        <div style="display: flex; gap: 1rem; margin-top: 0.5rem;">
                            <label style="display: flex; align-items: center; gap: 0.5rem;">
                                <input type="radio" name="status" value="Accepted" required>
                                <span>${isArabic ? 'مقبول' : 'Accepted'}</span>
                            </label>
                            <label style="display: flex; align-items: center; gap: 0.5rem;">
                                <input type="radio" name="status" value="Rejected" required>
                                <span>${isArabic ? 'مرفوض' : 'Rejected'}</span>
                            </label>
                        </div>
                    </div>
                    
                    <div class="form-row">
                        <label class="form-label" for="verified_by">${isArabic ? 'تم التحقق بواسطة' : 'Verified By'} *</label>
                        <input type="text" class="form-input" id="verified_by" name="verified_by" required
                               value="${frappe.session.user}" readonly>
                    </div>
                    
                    <div class="form-row">
                        <label class="form-label" for="inspection_date">${isArabic ? 'تاريخ الفحص' : 'Inspection Date'} *</label>
                        <input type="date" class="form-input" id="inspection_date" name="inspection_date" required>
                    </div>
                </div>
                
                <div class="form-section">
                    <div class="form-row">
                        <label class="form-label" for="remarks">${isArabic ? 'ملاحظات' : 'Remarks'}</label>
                        <textarea class="form-input" id="remarks" name="remarks" rows="4" 
                                  placeholder="${isArabic ? 'إضافة تفاصيل الفحص والملاحظات' : 'Add inspection details and remarks'}"></textarea>
                    </div>
                    
                    <div style="display: flex; gap: 1rem; margin-top: 1rem;">
                        <button type="submit" class="btn btn-success btn-full">
                            <span class="loading" style="display: none;"></span>
                            ${isArabic ? 'حفظ الفحص' : 'Save Inspection'}
                        </button>
                        <button type="button" class="btn btn-secondary" onclick="mobileReceiving.clearFormsContainer()">
                            ${isArabic ? 'إلغاء' : 'Cancel'}
                        </button>
                    </div>
                </div>
            </form>
        `;

        this.insertForm(formHtml);
        this.setupQualityInspectionForm();
    }

    setupPurchaseReceiptForm() {
        // Set today's date
        document.getElementById('posting_date').value = new Date().toISOString().split('T')[0];

        // Load purchase orders
        this.loadPurchaseOrders();

        // Setup barcode scanning for this form
        this.setupFormBarcodeScanning();

        // Purchase order change handler
        document.getElementById('purchase_order').addEventListener('change', (e) => {
            if (e.target.value) {
                this.loadPurchaseOrderDetails(e.target.value);
            }
        });
    }

    setupQualityInspectionForm() {
        // Set today's date
        document.getElementById('inspection_date').value = new Date().toISOString().split('T')[0];

        // Load reference documents
        this.loadReferenceDocuments();

        // Setup barcode scanning for item code
        this.setupFormBarcodeScanning();

        // Reference type change handler
        document.getElementById('reference_type').addEventListener('change', () => {
            this.loadReferenceDocuments();
        });

        // Reference name change handler
        document.getElementById('reference_name').addEventListener('change', (e) => {
            if (e.target.value) {
                this.loadReferenceItems(e.target.value);
            }
        });
    }

    setupFormBarcodeScanning() {
        const barcodeInputs = document.querySelectorAll('.barcode-input');

        barcodeInputs.forEach(input => {
            input.addEventListener('input', (e) => {
                const value = e.target.value.trim();
                if (value.length >= 8) { // Minimum barcode length
                    this.handleBarcodeInput(value, input);
                }
            });

            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    const value = e.target.value.trim();
                    if (value) {
                        this.handleBarcodeInput(value, input);
                    }
                }
            });
        });
    }

    handleBarcodeInput(barcode, inputElement) {
        // Show loading state
        this.showStatus('loading', this.currentLanguage === 'ar' ? 'جاري البحث...' : 'Searching...', 'warning');

        // Simulate API call to find item by barcode
        frappe.call({
            method: 'universal_workshop.purchasing_management.api.find_item_by_barcode',
            args: { barcode: barcode },
            callback: (r) => {
                if (r.message) {
                    this.addScannedItem(r.message);
                    this.showStatus('success',
                        this.currentLanguage === 'ar' ? 'تم مسح العنصر بنجاح' : 'Item scanned successfully',
                        'success');
                    inputElement.value = '';
                } else {
                    this.showStatus('error',
                        this.currentLanguage === 'ar' ? 'لم يتم العثور على الباركود' : 'Barcode not found',
                        'error');
                }
            },
            error: () => {
                this.showStatus('error',
                    this.currentLanguage === 'ar' ? 'خطأ في البحث' : 'Search error',
                    'error');
            }
        });
    }

    addScannedItem(itemData) {
        const existingItem = this.scannedItems.find(item => item.item_code === itemData.item_code);

        if (existingItem) {
            existingItem.received_qty += 1;
        } else {
            this.scannedItems.push({
                item_code: itemData.item_code,
                item_name: itemData.item_name,
                received_qty: 1,
                uom: itemData.stock_uom,
                warehouse: itemData.default_warehouse
            });
        }

        this.renderScannedItems();
    }

    renderScannedItems() {
        const container = document.getElementById('scanned-items');
        const isArabic = this.currentLanguage === 'ar';

        if (this.scannedItems.length === 0) {
            container.innerHTML = `<p style="text-align: center; color: var(--text-secondary);">
                ${isArabic ? 'لا توجد عناصر ممسوحة' : 'No scanned items'}
            </p>`;
            return;
        }

        let html = '';
        this.scannedItems.forEach((item, index) => {
            html += `
                <div class="item-card">
                    <div class="item-info">
                        <div class="item-code">${item.item_code}</div>
                        <div class="item-name">${item.item_name}</div>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <input type="number" value="${item.received_qty}" min="0" step="0.01"
                               onchange="mobileReceiving.updateItemQuantity(${index}, this.value)"
                               style="width: 80px; padding: 0.25rem; border: 1px solid var(--border-color); border-radius: 0.25rem;">
                        <button onclick="mobileReceiving.removeScannedItem(${index})" 
                                class="btn btn-secondary" style="padding: 0.25rem 0.5rem; font-size: 0.75rem;">
                            ${isArabic ? 'حذف' : 'Remove'}
                        </button>
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;
    }

    updateItemQuantity(index, quantity) {
        if (this.scannedItems[index]) {
            this.scannedItems[index].received_qty = parseFloat(quantity) || 0;
        }
    }

    removeScannedItem(index) {
        this.scannedItems.splice(index, 1);
        this.renderScannedItems();
    }

    setupBarcodeScanner() {
        // Camera access check
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            this.cameraAvailable = true;
        } else {
            console.warn('Camera API not available');
            this.cameraAvailable = false;
        }
    }

    toggleScannerInterface() {
        const scannerInterface = document.getElementById('scanner-interface');
        const isVisible = scannerInterface.style.display !== 'none';

        if (isVisible) {
            scannerInterface.style.display = 'none';
            this.stopBarcodeScanning();
        } else {
            scannerInterface.style.display = 'block';
            this.clearFormsContainer();
        }
    }

    startBarcodeScanning() {
        if (!this.cameraAvailable) {
            this.showStatus('error',
                this.currentLanguage === 'ar' ? 'الكاميرا غير متاحة' : 'Camera not available',
                'error');
            return;
        }

        const video = document.getElementById('scanner-video');

        navigator.mediaDevices.getUserMedia({
            video: {
                facingMode: 'environment',
                width: { ideal: 640 },
                height: { ideal: 480 }
            }
        })
            .then(stream => {
                video.srcObject = stream;
                this.isScanning = true;

                // Initialize Quagga for barcode detection
                Quagga.init({
                    inputStream: {
                        name: "Live",
                        type: "LiveStream",
                        target: video,
                        constraints: {
                            width: 640,
                            height: 480,
                            facingMode: "environment"
                        }
                    },
                    decoder: {
                        readers: [
                            "code_128_reader",
                            "ean_reader",
                            "ean_8_reader",
                            "code_39_reader",
                            "code_39_vin_reader",
                            "codabar_reader",
                            "upc_reader",
                            "upc_e_reader"
                        ]
                    }
                }, (err) => {
                    if (err) {
                        console.error('Quagga initialization failed:', err);
                        this.showStatus('error',
                            this.currentLanguage === 'ar' ? 'فشل في تهيئة الماسح' : 'Scanner initialization failed',
                            'error');
                        return;
                    }

                    Quagga.start();

                    // Listen for barcode detection
                    Quagga.onDetected((result) => {
                        if (this.isScanning) {
                            const code = result.codeResult.code;
                            this.handleScannedBarcode(code);
                        }
                    });
                });
            })
            .catch(err => {
                console.error('Camera access denied:', err);
                this.showStatus('error',
                    this.currentLanguage === 'ar' ? 'تم رفض الوصول للكاميرا' : 'Camera access denied',
                    'error');
            });
    }

    stopBarcodeScanning() {
        this.isScanning = false;

        if (typeof Quagga !== 'undefined') {
            Quagga.stop();
        }

        const video = document.getElementById('scanner-video');
        if (video.srcObject) {
            const tracks = video.srcObject.getTracks();
            tracks.forEach(track => track.stop());
            video.srcObject = null;
        }
    }

    handleScannedBarcode(barcode) {
        // Auto-fill barcode in active form
        const activeInput = document.querySelector('.barcode-input:focus') ||
            document.querySelector('.barcode-input');

        if (activeInput) {
            activeInput.value = barcode;
            this.handleBarcodeInput(barcode, activeInput);
        }

        // Provide haptic feedback if available
        if (navigator.vibrate) {
            navigator.vibrate(200);
        }

        // Play audio feedback
        this.playBeepSound();
    }

    playBeepSound() {
        // Create audio context for beep sound
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();

            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);

            oscillator.frequency.value = 800;
            oscillator.type = 'square';

            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);

            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.1);
        } catch (error) {
            console.log('Audio feedback not available');
        }
    }

    handleFormSubmission(form) {
        const formData = new FormData(form);
        const doctype = form.dataset.doctype;
        const submitBtn = form.querySelector('button[type="submit"]');
        const loading = submitBtn.querySelector('.loading');

        // Show loading state
        submitBtn.disabled = true;
        loading.style.display = 'inline-block';

        // Prepare data based on doctype
        let data = {};
        for (let [key, value] of formData.entries()) {
            data[key] = value;
        }

        // Add scanned items for Purchase Receipt
        if (doctype === 'Purchase Receipt' && this.scannedItems.length > 0) {
            data.items = this.scannedItems;
        }

        // Submit to server
        frappe.call({
            method: 'universal_workshop.purchasing_management.api.create_mobile_document',
            args: {
                doctype: doctype,
                data: data
            },
            callback: (r) => {
                if (r.message) {
                    this.showStatus('success',
                        this.currentLanguage === 'ar' ? 'تم حفظ النموذج بنجاح' : 'Form saved successfully',
                        'success');

                    // Clear form and redirect
                    setTimeout(() => {
                        this.clearFormsContainer();
                        this.scannedItems = [];
                    }, 2000);
                } else {
                    this.showStatus('error',
                        this.currentLanguage === 'ar' ? 'فشل في حفظ النموذج' : 'Failed to save form',
                        'error');
                }
            },
            error: () => {
                this.showStatus('error',
                    this.currentLanguage === 'ar' ? 'خطأ في الخادم' : 'Server error',
                    'error');
            },
            always: () => {
                // Hide loading state
                submitBtn.disabled = false;
                loading.style.display = 'none';
            }
        });
    }

    loadPurchaseOrders() {
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Purchase Order',
                filters: {
                    status: ['in', ['To Receive and Bill', 'To Receive']],
                    docstatus: 1
                },
                fields: ['name', 'supplier', 'transaction_date'],
                limit_page_length: 20
            },
            callback: (r) => {
                const select = document.getElementById('purchase_order');
                if (r.message) {
                    r.message.forEach(po => {
                        const option = document.createElement('option');
                        option.value = po.name;
                        option.textContent = `${po.name} - ${po.supplier}`;
                        select.appendChild(option);
                    });
                }
            }
        });
    }

    loadPurchaseOrderDetails(poName) {
        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Purchase Order',
                name: poName
            },
            callback: (r) => {
                if (r.message) {
                    document.getElementById('supplier').value = r.message.supplier;
                }
            }
        });
    }

    loadReferenceDocuments() {
        const referenceType = document.getElementById('reference_type').value;
        const select = document.getElementById('reference_name');

        // Clear existing options
        select.innerHTML = `<option value="">${this.currentLanguage === 'ar' ? 'اختر مرجع' : 'Select Reference'}</option>`;

        if (!referenceType) return;

        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: referenceType,
                filters: { docstatus: 1 },
                fields: ['name', 'posting_date'],
                limit_page_length: 20
            },
            callback: (r) => {
                if (r.message) {
                    r.message.forEach(doc => {
                        const option = document.createElement('option');
                        option.value = doc.name;
                        option.textContent = `${doc.name} - ${doc.posting_date}`;
                        select.appendChild(option);
                    });
                }
            }
        });
    }

    loadReferenceItems(referenceName) {
        const referenceType = document.getElementById('reference_type').value;

        frappe.call({
            method: 'universal_workshop.purchasing_management.api.get_reference_items',
            args: {
                doctype: referenceType,
                name: referenceName
            },
            callback: (r) => {
                if (r.message && r.message.length > 0) {
                    // Auto-fill first item if only one available
                    if (r.message.length === 1) {
                        document.getElementById('item_code').value = r.message[0].item_code;
                        document.getElementById('sample_size').value = Math.min(r.message[0].qty, 5);
                    }
                }
            }
        });
    }

    loadPendingReceipts() {
        const isArabic = this.currentLanguage === 'ar';

        frappe.call({
            method: 'universal_workshop.purchasing_management.api.get_pending_receipts',
            callback: (r) => {
                if (r.message) {
                    this.pendingReceipts = r.message;
                    this.showPendingReceiptsList();
                }
            }
        });
    }

    showPendingReceiptsList() {
        const isArabic = this.currentLanguage === 'ar';

        let html = `
            <div class="mobile-form">
                <h2 class="section-title">${isArabic ? 'الإيصالات المعلقة' : 'Pending Receipts'}</h2>
                <div class="item-list">
        `;

        if (this.pendingReceipts.length === 0) {
            html += `<p style="text-align: center; color: var(--text-secondary);">
                ${isArabic ? 'لا توجد إيصالات معلقة' : 'No pending receipts'}
            </p>`;
        } else {
            this.pendingReceipts.forEach(receipt => {
                html += `
                    <div class="item-card">
                        <div class="item-info">
                            <div class="item-code">${receipt.name}</div>
                            <div class="item-name">${receipt.supplier} - ${receipt.posting_date}</div>
                        </div>
                        <button class="btn btn-primary" onclick="mobileReceiving.viewReceipt('${receipt.name}')">
                            ${isArabic ? 'عرض' : 'View'}
                        </button>
                    </div>
                `;
            });
        }

        html += `
                </div>
                <button class="btn btn-secondary btn-full" onclick="mobileReceiving.clearFormsContainer()">
                    ${isArabic ? 'إغلاق' : 'Close'}
                </button>
            </div>
        `;

        this.insertForm(html);
    }

    viewReceipt(receiptName) {
        // Open receipt in new tab/window
        window.open(`/app/purchase-receipt/${receiptName}`, '_blank');
    }

    insertForm(html) {
        const container = document.getElementById('forms-container');
        container.innerHTML = html;
        container.scrollIntoView({ behavior: 'smooth' });
    }

    clearFormsContainer() {
        document.getElementById('forms-container').innerHTML = '';
        this.currentForm = null;
        this.scannedItems = [];
    }

    saveCurrentForm() {
        const form = document.querySelector('.mobile-form');
        if (form) {
            this.handleFormSubmission(form);
        }
    }

    showStatus(type, message, status = 'info') {
        const statusDiv = document.getElementById('status-message');

        statusDiv.className = `status-message status-${status}`;
        statusDiv.textContent = message;
        statusDiv.style.display = 'block';

        // Auto-hide after 5 seconds
        setTimeout(() => {
            statusDiv.style.display = 'none';
        }, 5000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.mobileReceiving = new MobileReceivingInterface();
});

// Service worker for PWA functionality
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/mobile-receiving-sw.js')
            .then(registration => {
                console.log('Service Worker registered successfully');
            })
            .catch(error => {
                console.log('Service Worker registration failed');
            });
    });
} 