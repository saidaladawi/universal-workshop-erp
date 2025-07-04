/**
 * Universal Workshop ERP - Barcode Scanner Integration
 * Combines QuaggaJS camera scanning with ERPNext v15 native barcode support
 * Copyright (c) 2024, Eng. Saeed Al-Adawi
 */

class UniversalBarcodeScanner {
    constructor(options = {}) {
        this.options = {
            target_element: options.target_element || '#barcode-scanner',
            callback: options.callback || this.defaultCallback,
            scan_type: options.scan_type || 'lookup',
            warehouse: options.warehouse || '',
            auto_close: options.auto_close !== false,
            continuous_scan: options.continuous_scan || false,
            play_sound: options.play_sound !== false,
            vibrate: options.vibrate !== false,
            show_results: options.show_results !== false,
            language: options.language || frappe.boot.lang || 'en',
            ...options
        };

        this.scanning = false;
        this.scanner_initialized = false;
        this.scan_results = [];
        this.last_scan_time = 0;
        this.scan_cooldown = 1000; // 1 second cooldown between scans

        this.init();
    }

    init() {
        // Load QuaggaJS if not already loaded
        this.loadQuaggaJS().then(() => {
            this.setupUI();
            this.bindEvents();
        }).catch(error => {
            console.error('Failed to load QuaggaJS:', error);
            frappe.msgprint(__('Barcode scanning library failed to load. Please refresh the page.'));
        });
    }

    async loadQuaggaJS() {
        if (window.Quagga) {
            return Promise.resolve();
        }

        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/quagga/0.12.1/quagga.min.js';
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    setupUI() {
        // Create scanner modal
        this.modal = new frappe.ui.Dialog({
            title: __('Barcode Scanner'),
            size: 'large',
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'scanner_area',
                    options: `
                        <div class="barcode-scanner-container">
                            <div id="barcode-scanner" class="barcode-scanner-viewport"></div>
                            <div class="scanner-overlay">
                                <div class="scanner-line"></div>
                                <div class="scanner-corners">
                                    <div class="corner top-left"></div>
                                    <div class="corner top-right"></div>
                                    <div class="corner bottom-left"></div>
                                    <div class="corner bottom-right"></div>
                                </div>
                            </div>
                            <div class="scanner-controls">
                                <button class="btn btn-primary" id="start-scan-btn">
                                    <i class="fa fa-camera"></i> ${__('Start Scanning')}
                                </button>
                                <button class="btn btn-secondary" id="stop-scan-btn" style="display: none;">
                                    <i class="fa fa-stop"></i> ${__('Stop Scanning')}
                                </button>
                                <button class="btn btn-info" id="manual-input-btn">
                                    <i class="fa fa-keyboard-o"></i> ${__('Manual Input')}
                                </button>
                            </div>
                            <div class="scan-results" style="display: none;">
                                <h5>${__('Scan Results')}</h5>
                                <div class="results-list"></div>
                            </div>
                        </div>
                    `
                },
                {
                    fieldtype: 'Select',
                    fieldname: 'scan_type',
                    label: __('Scan Type'),
                    options: [
                        { label: __('Lookup Item'), value: 'lookup' },
                        { label: __('Stock In'), value: 'stock_in' },
                        { label: __('Stock Out'), value: 'stock_out' },
                        { label: __('Transfer'), value: 'transfer' },
                        { label: __('Reconcile'), value: 'reconcile' }
                    ],
                    default: this.options.scan_type
                },
                {
                    fieldtype: 'Link',
                    fieldname: 'warehouse',
                    label: __('Warehouse'),
                    options: 'Warehouse',
                    default: this.options.warehouse
                },
                {
                    fieldtype: 'Float',
                    fieldname: 'quantity',
                    label: __('Quantity'),
                    default: 1,
                    depends_on: 'eval:["stock_in", "stock_out", "transfer", "reconcile"].includes(doc.scan_type)'
                }
            ],
            primary_action_label: __('Close'),
            primary_action: () => {
                this.stopScanning();
                this.modal.hide();
            }
        });

        // Add custom CSS
        this.addScannerStyles();
    }

    addScannerStyles() {
        if (document.getElementById('barcode-scanner-styles')) return;

        const styles = `
            <style id="barcode-scanner-styles">
                .barcode-scanner-container {
                    position: relative;
                    text-align: center;
                    padding: 20px;
                }
                
                .barcode-scanner-viewport {
                    position: relative;
                    width: 100%;
                    max-width: 640px;
                    height: 480px;
                    margin: 0 auto;
                    border: 2px solid #ddd;
                    background: #000;
                    display: none;
                }
                
                .scanner-overlay {
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    width: 200px;
                    height: 200px;
                    pointer-events: none;
                    z-index: 10;
                }
                
                .scanner-line {
                    position: absolute;
                    width: 100%;
                    height: 2px;
                    background: #ff0000;
                    top: 50%;
                    left: 0;
                    animation: scan-line 2s ease-in-out infinite;
                }
                
                @keyframes scan-line {
                    0%, 100% { top: 10%; }
                    50% { top: 90%; }
                }
                
                .scanner-corners {
                    position: absolute;
                    width: 100%;
                    height: 100%;
                }
                
                .corner {
                    position: absolute;
                    width: 20px;
                    height: 20px;
                    border: 3px solid #00ff00;
                }
                
                .corner.top-left {
                    top: 0;
                    left: 0;
                    border-right: none;
                    border-bottom: none;
                }
                
                .corner.top-right {
                    top: 0;
                    right: 0;
                    border-left: none;
                    border-bottom: none;
                }
                
                .corner.bottom-left {
                    bottom: 0;
                    left: 0;
                    border-right: none;
                    border-top: none;
                }
                
                .corner.bottom-right {
                    bottom: 0;
                    right: 0;
                    border-left: none;
                    border-top: none;
                }
                
                .scanner-controls {
                    margin: 20px 0;
                }
                
                .scanner-controls .btn {
                    margin: 0 10px;
                }
                
                .scan-results {
                    text-align: left;
                    margin-top: 20px;
                    max-height: 300px;
                    overflow-y: auto;
                }
                
                .result-item {
                    border: 1px solid #ddd;
                    padding: 10px;
                    margin: 5px 0;
                    border-radius: 4px;
                    background: #f9f9f9;
                }
                
                .result-item.success {
                    border-color: #5cb85c;
                    background: #dff0d8;
                }
                
                .result-item.error {
                    border-color: #d9534f;
                    background: #f2dede;
                }
                
                /* RTL Support for Arabic */
                [dir="rtl"] .barcode-scanner-container {
                    direction: rtl;
                }
                
                [dir="rtl"] .scanner-controls .btn {
                    margin: 0 10px 0 0;
                }
            </style>
        `;

        document.head.insertAdjacentHTML('beforeend', styles);
    }

    bindEvents() {
        // Wait for modal to be shown before binding events
        this.modal.$wrapper.on('shown.bs.modal', () => {
            this.bindScannerEvents();
        });

        this.modal.$wrapper.on('hidden.bs.modal', () => {
            this.stopScanning();
        });
    }

    bindScannerEvents() {
        const $wrapper = this.modal.$wrapper;

        // Start scanning button
        $wrapper.find('#start-scan-btn').on('click', () => {
            this.startScanning();
        });

        // Stop scanning button
        $wrapper.find('#stop-scan-btn').on('click', () => {
            this.stopScanning();
        });

        // Manual input button
        $wrapper.find('#manual-input-btn').on('click', () => {
            this.showManualInput();
        });

        // Handle keyboard input for handheld scanners
        $(document).on('keypress.barcode-scanner', (e) => {
            if (this.scanning) {
                this.handleKeyboardInput(e);
            }
        });
    }

    startScanning() {
        if (this.scanning) return;

        const scanner_element = this.modal.$wrapper.find('#barcode-scanner')[0];

        if (!scanner_element) {
            frappe.msgprint(__('Scanner element not found'));
            return;
        }

        // Check for camera availability
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            frappe.msgprint(__('Camera access not available. Use manual input instead.'));
            return;
        }

        // Show scanner viewport
        $(scanner_element).show();

        // Initialize QuaggaJS
        Quagga.init({
            inputStream: {
                name: "Live",
                type: "LiveStream",
                target: scanner_element,
                constraints: {
                    width: 640,
                    height: 480,
                    facingMode: "environment" // Use back camera on mobile
                }
            },
            locator: {
                patchSize: "medium",
                halfSample: true
            },
            numOfWorkers: 2,
            decoder: {
                readers: [
                    "code_128_reader",
                    "ean_reader",
                    "ean_8_reader",
                    "code_39_reader",
                    "code_39_vin_reader",
                    "codabar_reader",
                    "upc_reader",
                    "upc_e_reader",
                    "i2of5_reader"
                ]
            },
            locate: true
        }, (err) => {
            if (err) {
                console.error('QuaggaJS initialization error:', err);
                frappe.msgprint(__('Failed to initialize camera scanner: {0}', [err.message]));
                return;
            }

            console.log("QuaggaJS initialization finished. Ready to start");
            Quagga.start();
            this.scanning = true;
            this.scanner_initialized = true;

            // Update UI
            this.modal.$wrapper.find('#start-scan-btn').hide();
            this.modal.$wrapper.find('#stop-scan-btn').show();

            if (this.options.show_results) {
                this.modal.$wrapper.find('.scan-results').show();
            }
        });

        // Set up scan detection
        Quagga.onDetected((result) => {
            this.handleScanResult(result.codeResult.code, 'camera');
        });

        // Handle scan failures for debugging
        Quagga.onProcessed((result) => {
            if (result && result.codeResult) {
                // Optionally show processing feedback
            }
        });
    }

    stopScanning() {
        if (this.scanner_initialized) {
            Quagga.stop();
            this.scanner_initialized = false;
        }

        this.scanning = false;

        // Update UI
        this.modal.$wrapper.find('#barcode-scanner').hide();
        this.modal.$wrapper.find('#start-scan-btn').show();
        this.modal.$wrapper.find('#stop-scan-btn').hide();

        // Remove keyboard event listener
        $(document).off('keypress.barcode-scanner');
    }

    handleKeyboardInput(e) {
        // Handle handheld barcode scanner input
        // Most scanners send the barcode followed by Enter key
        if (e.which === 13 && this.keyboard_buffer) {
            e.preventDefault();
            const barcode = this.keyboard_buffer.trim();
            this.keyboard_buffer = '';

            if (barcode.length > 3) { // Minimum barcode length
                this.handleScanResult(barcode, 'keyboard');
            }
        } else if (e.which >= 32 && e.which <= 126) {
            // Printable characters
            this.keyboard_buffer = (this.keyboard_buffer || '') + String.fromCharCode(e.which);
        }
    }

    handleScanResult(barcode_data, scan_method = 'camera') {
        // Implement scan cooldown to prevent duplicate scans
        const now = Date.now();
        if (now - this.last_scan_time < this.scan_cooldown) {
            return;
        }
        this.last_scan_time = now;

        // Play sound and vibrate if enabled
        if (this.options.play_sound) {
            this.playBeepSound();
        }

        if (this.options.vibrate && navigator.vibrate) {
            navigator.vibrate(200);
        }

        // Get scan parameters from form
        const scan_type = this.modal.get_value('scan_type') || this.options.scan_type;
        const warehouse = this.modal.get_value('warehouse') || this.options.warehouse;
        const quantity = this.modal.get_value('quantity') || 1;

        // Show loading indicator
        const $results = this.modal.$wrapper.find('.results-list');
        $results.append(`
            <div class="result-item processing" data-barcode="${barcode_data}">
                <div class="row">
                    <div class="col-md-8">
                        <strong>${__('Processing')}: ${barcode_data}</strong>
                        <br><small>${__('Scan Method')}: ${scan_method}</small>
                    </div>
                    <div class="col-md-4 text-right">
                        <i class="fa fa-spinner fa-spin"></i>
                    </div>
                </div>
            </div>
        `);

        // Process scan via API
        frappe.call({
            method: 'universal_workshop.parts_inventory.barcode_scanner.scan_barcode',
            args: {
                barcode_data: barcode_data,
                scan_type: scan_type,
                warehouse: warehouse,
                quantity: quantity
            },
            callback: (response) => {
                this.processScanResponse(barcode_data, response.message, scan_method);
            },
            error: (error) => {
                this.processScanResponse(barcode_data, {
                    success: false,
                    message: __('Network error occurred'),
                    error: error
                }, scan_method);
            }
        });
    }

    processScanResponse(barcode_data, result, scan_method) {
        // Update the processing result
        const $processing = this.modal.$wrapper.find(`.result-item[data-barcode="${barcode_data}"]`);
        $processing.removeClass('processing');

        if (result.success) {
            $processing.addClass('success');
            const item = result.item || {};
            const action_msg = this.getActionMessage(result);

            $processing.html(`
                <div class="row">
                    <div class="col-md-8">
                        <strong>${item.item_name || item.item_code || barcode_data}</strong>
                        <br><small>${__('Code')}: ${item.item_code || 'N/A'}</small>
                        <br><small>${action_msg}</small>
                    </div>
                    <div class="col-md-4 text-right">
                        <i class="fa fa-check text-success"></i>
                        <br><small>${__('Method')}: ${scan_method}</small>
                    </div>
                </div>
            `);

            // Store result
            this.scan_results.push({
                barcode_data: barcode_data,
                result: result,
                timestamp: new Date(),
                scan_method: scan_method
            });

            // Call custom callback
            if (this.options.callback && typeof this.options.callback === 'function') {
                this.options.callback(result, barcode_data);
            }

            // Auto-close if not continuous scanning
            if (this.options.auto_close && !this.options.continuous_scan) {
                setTimeout(() => {
                    this.stopScanning();
                    this.modal.hide();
                }, 1500);
            }

        } else {
            $processing.addClass('error');
            $processing.html(`
                <div class="row">
                    <div class="col-md-8">
                        <strong>${__('Error')}: ${barcode_data}</strong>
                        <br><small>${result.message || __('Unknown error')}</small>
                    </div>
                    <div class="col-md-4 text-right">
                        <i class="fa fa-times text-danger"></i>
                        <br><small>${__('Method')}: ${scan_method}</small>
                    </div>
                </div>
            `);
        }

        // Auto-scroll to latest result
        const $results_container = this.modal.$wrapper.find('.scan-results');
        $results_container.scrollTop($results_container[0].scrollHeight);
    }

    getActionMessage(result) {
        const action = result.action || 'lookup';

        switch (action) {
            case 'lookup':
                const stock_info = result.stock_info || {};
                if (stock_info.warehouse_specific) {
                    return __('Stock: {0} in {1}', [stock_info.stock_qty || 0, stock_info.warehouse]);
                } else {
                    return __('Total Stock: {0}', [stock_info.total_stock || 0]);
                }
            case 'stock_in':
                return __('Stock In: {0} → {1}', [result.quantity, result.warehouse]);
            case 'stock_out':
                return __('Stock Out: {0} from {1}', [result.quantity, result.warehouse]);
            case 'transfer':
                return __('Transfer: {0} from {1} to {2}', [result.quantity, result.from_warehouse, result.to_warehouse]);
            case 'reconcile':
                return __('Reconcile: Counted {0}, System {1}', [result.counted_qty, result.current_qty]);
            default:
                return __('Action completed');
        }
    }

    showManualInput() {
        const manual_dialog = new frappe.ui.Dialog({
            title: __('Manual Barcode Input'),
            fields: [
                {
                    fieldtype: 'Data',
                    fieldname: 'barcode_input',
                    label: __('Barcode/Item Code'),
                    reqd: 1,
                    description: __('Enter barcode, item code, or part number')
                }
            ],
            primary_action_label: __('Scan'),
            primary_action: (values) => {
                if (values.barcode_input) {
                    this.handleScanResult(values.barcode_input, 'manual');
                    manual_dialog.hide();
                }
            }
        });

        manual_dialog.show();
        manual_dialog.get_field('barcode_input').df.onchange = () => {
            // Auto-submit on Enter key
            manual_dialog.get_field('barcode_input').$input.on('keypress', (e) => {
                if (e.which === 13) {
                    manual_dialog.primary_action();
                }
            });
        };
    }

    playBeepSound() {
        // Create audio context for beep sound
        if (window.AudioContext || window.webkitAudioContext) {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();

            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);

            oscillator.frequency.value = 800; // Beep frequency
            gainNode.gain.value = 0.3; // Volume

            oscillator.start();
            oscillator.stop(audioContext.currentTime + 0.1); // 100ms beep
        }
    }

    show() {
        this.modal.show();
    }

    hide() {
        this.stopScanning();
        this.modal.hide();
    }

    defaultCallback(result, barcode_data) {
        // Default callback - can be overridden
        console.log('Barcode scanned:', barcode_data, result);
    }

    getScanResults() {
        return this.scan_results;
    }

    clearResults() {
        this.scan_results = [];
        this.modal.$wrapper.find('.results-list').empty();
    }
}

// Global helper functions
window.UniversalBarcodeScanner = UniversalBarcodeScanner;

// Frappe integration
frappe.provide('frappe.ui.scanner');

frappe.ui.scanner.show = function (options = {}) {
    const scanner = new UniversalBarcodeScanner(options);
    scanner.show();
    return scanner;
};

// Add to ERPNext forms
frappe.ui.form.ControlData = class extends frappe.ui.form.ControlData {
    make_input() {
        super.make_input();

        // Add barcode scan button to fields with 'barcode' in name
        if (this.df.fieldname &&
            (this.df.fieldname.includes('barcode') ||
                this.df.fieldname.includes('item_code') ||
                this.df.options === 'Item')) {

            this.add_barcode_button();
        }
    }

    add_barcode_button() {
        const $btn = $(`
            <button class="btn btn-xs btn-default barcode-scan-btn" 
                    type="button" title="${__('Scan Barcode')}">
                <i class="fa fa-qrcode"></i>
            </button>
        `);

        $btn.click(() => {
            const scanner = new UniversalBarcodeScanner({
                callback: (result, barcode_data) => {
                    if (result.success && result.item) {
                        this.set_value(result.item.item_code);
                        this.refresh();
                    }
                },
                auto_close: true,
                scan_type: 'lookup'
            });
            scanner.show();
        });

        this.$input_area.append($btn);
    }
}; 