// Copyright (c) 2025, Universal Workshop ERP
// For license information, see license.txt

frappe.ui.form.on('Barcode Scanner', {
    refresh: function(frm) {
        frm.add_custom_button(__('Scan Barcode'), function() {
            frm.trigger('start_scanning');
        });
        
        frm.add_custom_button(__('Process Stock Movement'), function() {
            frm.trigger('process_stock_movement');
        });
        
        // Setup barcode input field
        if (frm.fields_dict.barcode_data) {
            frm.fields_dict.barcode_data.$input.on('keypress', function(e) {
                if (e.which === 13) { // Enter key
                    frm.trigger('process_barcode_scan');
                }
            });
        }
    },
    
    start_scanning: function(frm) {
        // Initialize camera or scanner
        if (frm.doc.scanner_type === 'Mobile Camera' || frm.doc.scanner_type === 'Webcam') {
            frm.trigger('initialize_camera_scanning');
        } else {
            frm.trigger('focus_barcode_field');
        }
    },
    
    initialize_camera_scanning: function(frm) {
        // This would integrate with a camera scanning library
        frappe.msgprint(__('Camera scanning not yet implemented. Please use manual input.'));
    },
    
    focus_barcode_field: function(frm) {
        if (frm.fields_dict.barcode_data) {
            frm.fields_dict.barcode_data.$input.focus();
            frappe.msgprint(__('Ready for barcode scan. Please scan or enter barcode.'));
        }
    },
    
    process_barcode_scan: function(frm) {
        if (!frm.doc.barcode_data) {
            frappe.msgprint(__('Please enter barcode data'));
            return;
        }
        
        // Auto-fetch item details if enabled
        if (frm.doc.auto_fetch_details) {
            frm.trigger('fetch_item_details');
        }
        
        // Play sound if enabled
        if (frm.doc.enable_sound) {
            frm.trigger('play_scan_sound');
        }
        
        // Clear barcode field for next scan
        frm.set_value('barcode_data', '');
    },
    
    fetch_item_details: function(frm) {
        frappe.call({
            method: 'universal_workshop.parts_inventory.doctype.barcode_scanner.barcode_scanner.fetch_item_details',
            args: {
                barcode_data: frm.doc.barcode_data
            },
            callback: function(r) {
                if (r.message) {
                    frm.set_value('item_code', r.message.item_code);
                    frm.set_value('item_name', r.message.item_name);
                    frm.set_value('part_number', r.message.part_number);
                    frm.set_value('manufacturer', r.message.manufacturer);
                    frm.set_value('current_stock', r.message.current_stock);
                    frm.set_value('location', r.message.location);
                }
            }
        });
    },
    
    play_scan_sound: function(frm) {
        // Play beep sound for successful scan
        const audio = new Audio('/assets/universal_workshop/sounds/beep.mp3');
        audio.play().catch(function(error) {
            console.log('Audio play failed:', error);
        });
    },
    
    process_stock_movement: function(frm) {
        if (!frm.doc.item_code || !frm.doc.quantity_to_add) {
            frappe.msgprint(__('Please select item and enter quantity'));
            return;
        }
        
        frappe.call({
            method: 'universal_workshop.parts_inventory.doctype.barcode_scanner.barcode_scanner.process_stock_movement',
            args: {
                docname: frm.doc.name
            },
            callback: function(r) {
                if (r.message) {
                    frappe.msgprint(__('Stock movement processed successfully'));
                    frm.reload_doc();
                }
            }
        });
    },
    
    scan_mode: function(frm) {
        // Update UI based on scan mode
        if (frm.doc.scan_mode === 'Batch Scan') {
            frm.add_custom_button(__('Start Batch Scan'), function() {
                frm.trigger('start_batch_scanning');
            });
        }
    },
    
    start_batch_scanning: function(frm) {
        frappe.msgprint(__('Batch scanning mode activated. Multiple items can be scanned.'));
        // Implementation for batch scanning
    },
    
    validate: function(frm) {
        // Validate barcode data
        if (frm.doc.barcode_data && frm.doc.barcode_type) {
            const minLengths = {
                'Code 128': 1,
                'Code 39': 1,
                'EAN-13': 13,
                'EAN-8': 8,
                'QR Code': 1,
                'DataMatrix': 1,
                'PDF417': 1
            };
            
            const minLength = minLengths[frm.doc.barcode_type] || 1;
            if (frm.doc.barcode_data.length < minLength) {
                frappe.msgprint(__('Barcode data too short for selected type'));
                frappe.validated = false;
            }
        }
        
        // Validate scan mode
        const validModes = ['Manual', 'Auto-Scan', 'Batch Scan'];
        if (frm.doc.scan_mode && !validModes.includes(frm.doc.scan_mode)) {
            frappe.msgprint(__('Invalid scan mode'));
            frappe.validated = false;
        }
    }
});

// Global barcode scanning functions
window.barcodeScanner = {
    initializeScanner: function() {
        // Initialize scanner hardware if available
        console.log('Barcode scanner initialized');
    },
    
    onBarcodeScanned: function(barcodeData) {
        // Handle barcode scan events
        const currentForm = frappe.get_form();
        if (currentForm && currentForm.doctype === 'Barcode Scanner') {
            currentForm.set_value('barcode_data', barcodeData);
            currentForm.trigger('process_barcode_scan');
        }
    }
}; 