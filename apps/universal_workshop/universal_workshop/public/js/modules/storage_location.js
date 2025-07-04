// Storage Location Interactive JavaScript
// Arabic/English RTL Support with Mobile Integration

frappe.ui.form.on('Storage Location', {
    refresh: function (frm) {
        // Setup Arabic/RTL support
        frm.trigger('setup_arabic_fields');

        // Setup custom buttons
        frm.trigger('setup_custom_buttons');

        // Setup map integration
        frm.trigger('setup_location_map');

        // Setup capacity meters
        frm.trigger('setup_capacity_meters');

        // Setup barcode scanning
        frm.trigger('setup_barcode_scanning');

        // Real-time utilization updates
        frm.trigger('update_utilization_display');
    },

    setup_arabic_fields: function (frm) {
        // Set RTL direction for Arabic fields
        const arabic_fields = [
            'location_name_ar', 'description_ar', 'special_instructions_ar',
            'safety_requirements_ar', 'access_restrictions_ar'
        ];

        arabic_fields.forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.attr('dir', 'rtl');
                frm.fields_dict[field].$input.addClass('arabic-text');
            }
        });

        // Apply RTL to entire form if Arabic is primary
        if (frappe.boot.lang === 'ar') {
            frm.page.main.addClass('rtl-layout');
            $('.form-column').addClass('rtl-form');
        }
    },

    setup_custom_buttons: function (frm) {
        if (!frm.doc.__islocal && frm.doc.docstatus < 2) {
            // Generate QR Code button
            frm.add_custom_button(__('Generate QR Code'), function () {
                frm.trigger('generate_qr_code');
            }, __('Actions'));

            // Find Optimal Parts button
            frm.add_custom_button(__('Find Optimal Parts'), function () {
                frm.trigger('find_optimal_parts');
            }, __('Actions'));

            // Update Usage button
            frm.add_custom_button(__('Update Current Usage'), function () {
                frm.trigger('update_current_usage');
            }, __('Actions'));

            // Print Location Label button
            frm.add_custom_button(__('Print Location Label'), function () {
                frm.trigger('print_location_label');
            }, __('Print'));

            // Mobile Scanner button (for mobile devices)
            if (frappe.utils.is_mobile()) {
                frm.add_custom_button(__('Open Mobile Scanner'), function () {
                    frm.trigger('open_mobile_scanner');
                }, __('Mobile'));
            }
        }
    },

    setup_location_map: function (frm) {
        if (frm.doc.gps_coordinates && frm.fields_dict.location_map) {
            const coords = frm.doc.gps_coordinates.split(',');
            if (coords.length === 2) {
                const lat = parseFloat(coords[0].trim());
                const lng = parseFloat(coords[1].trim());

                // Create simple map display
                const map_html = `
                    <div class="location-map-container">
                        <iframe 
                            width="100%" 
                            height="200" 
                            frameborder="0" 
                            src="https://www.openstreetmap.org/export/embed.html?bbox=${lng - 0.01},${lat - 0.01},${lng + 0.01},${lat + 0.01}&layer=mapnik&marker=${lat},${lng}"
                            style="border: 1px solid #ccc; border-radius: 4px;">
                        </iframe>
                        <div class="map-info">
                            <small class="text-muted">
                                <i class="fa fa-map-marker"></i> 
                                ${__('Coordinates')}: ${lat.toFixed(6)}, ${lng.toFixed(6)}
                            </small>
                        </div>
                    </div>
                `;
                frm.fields_dict.location_map.$wrapper.html(map_html);
            }
        }
    },

    setup_capacity_meters: function (frm) {
        if (frm.doc.max_weight_kg || frm.doc.max_volume_m3 || frm.doc.max_items) {
            const capacity_html = frm.trigger('build_capacity_meters');

            // Add to dashboard section
            if (frm.fields_dict.capacity_dashboard) {
                frm.fields_dict.capacity_dashboard.$wrapper.html(capacity_html);
            }
        }
    },

    build_capacity_meters: function (frm) {
        let meters_html = '<div class="capacity-meters">';

        // Weight capacity meter
        if (frm.doc.max_weight_kg) {
            const weight_percent = ((frm.doc.current_weight_kg || 0) / frm.doc.max_weight_kg) * 100;
            const weight_color = weight_percent > 90 ? 'danger' : weight_percent > 70 ? 'warning' : 'success';

            meters_html += `
                <div class="capacity-meter">
                    <label>${__('Weight Capacity')}</label>
                    <div class="progress">
                        <div class="progress-bar progress-bar-${weight_color}" 
                             style="width: ${weight_percent}%">
                            ${weight_percent.toFixed(1)}%
                        </div>
                    </div>
                    <small>${frm.doc.current_weight_kg || 0} / ${frm.doc.max_weight_kg} ${__('kg')}</small>
                </div>
            `;
        }

        // Volume capacity meter
        if (frm.doc.max_volume_m3) {
            const volume_percent = ((frm.doc.current_volume_m3 || 0) / frm.doc.max_volume_m3) * 100;
            const volume_color = volume_percent > 90 ? 'danger' : volume_percent > 70 ? 'warning' : 'success';

            meters_html += `
                <div class="capacity-meter">
                    <label>${__('Volume Capacity')}</label>
                    <div class="progress">
                        <div class="progress-bar progress-bar-${volume_color}" 
                             style="width: ${volume_percent}%">
                            ${volume_percent.toFixed(1)}%
                        </div>
                    </div>
                    <small>${frm.doc.current_volume_m3 || 0} / ${frm.doc.max_volume_m3} ${__('m³')}</small>
                </div>
            `;
        }

        // Item count meter
        if (frm.doc.max_items) {
            const items_percent = ((frm.doc.current_item_count || 0) / frm.doc.max_items) * 100;
            const items_color = items_percent > 90 ? 'danger' : items_percent > 70 ? 'warning' : 'success';

            meters_html += `
                <div class="capacity-meter">
                    <label>${__('Item Count')}</label>
                    <div class="progress">
                        <div class="progress-bar progress-bar-${items_color}" 
                             style="width: ${items_percent}%">
                            ${items_percent.toFixed(1)}%
                        </div>
                    </div>
                    <small>${frm.doc.current_item_count || 0} / ${frm.doc.max_items} ${__('items')}</small>
                </div>
            `;
        }

        meters_html += '</div>';

        // Add efficiency score
        if (frm.doc.efficiency_score) {
            const efficiency_color = frm.doc.efficiency_score > 80 ? 'danger' :
                frm.doc.efficiency_score > 60 ? 'warning' : 'success';
            meters_html += `
                <div class="efficiency-score">
                    <h4>${__('Overall Efficiency')}: 
                        <span class="text-${efficiency_color}">${frm.doc.efficiency_score}%</span>
                    </h4>
                </div>
            `;
        }

        return meters_html;
    },

    setup_barcode_scanning: function (frm) {
        // Add barcode scanner interface if on mobile
        if (frappe.utils.is_mobile() && 'BarcodeDetector' in window) {
            frm.barcode_scanner = new BarcodeScanner({
                onScan: function (result) {
                    frm.trigger('handle_barcode_scan', result);
                },
                formats: ['qr_code', 'code_128', 'code_39']
            });
        }
    },

    // Field change handlers
    location_name: function (frm) {
        if (frm.doc.location_name && !frm.doc.location_name_ar) {
            // Auto-suggest Arabic transliteration
            frm.trigger('suggest_arabic_name');
        }
    },

    warehouse: function (frm) {
        if (frm.doc.warehouse && frm.doc.zone) {
            frm.trigger('auto_generate_location_code');
        }
    },

    zone: function (frm) {
        if (frm.doc.warehouse && frm.doc.zone) {
            frm.trigger('auto_generate_location_code');
        }
    },

    gps_coordinates: function (frm) {
        if (frm.doc.gps_coordinates) {
            frm.trigger('validate_coordinates');
            frm.trigger('setup_location_map');
        }
    },

    max_weight_kg: function (frm) {
        frm.trigger('update_utilization_display');
    },

    max_volume_m3: function (frm) {
        frm.trigger('update_utilization_display');
    },

    max_items: function (frm) {
        frm.trigger('update_utilization_display');
    },

    // Custom methods
    suggest_arabic_name: function (frm) {
        frappe.call({
            method: 'universal_workshop.api.get_arabic_transliteration',
            args: {
                english_text: frm.doc.location_name
            },
            callback: function (r) {
                if (r.message) {
                    frm.set_value('location_name_ar', r.message);
                }
            }
        });
    },

    auto_generate_location_code: function (frm) {
        if (!frm.doc.location_code && frm.doc.warehouse && frm.doc.zone) {
            frappe.call({
                method: 'universal_workshop.scrap_management.doctype.storage_location.storage_location.generate_location_code',
                args: {
                    warehouse: frm.doc.warehouse,
                    zone: frm.doc.zone
                },
                callback: function (r) {
                    if (r.message) {
                        frm.set_value('location_code', r.message);
                    }
                }
            });
        }
    },

    validate_coordinates: function (frm) {
        if (frm.doc.gps_coordinates) {
            const coords = frm.doc.gps_coordinates.split(',');
            if (coords.length !== 2) {
                frappe.msgprint(__('GPS coordinates must be in format: latitude,longitude'));
                frm.set_value('gps_coordinates', '');
                return;
            }

            try {
                const lat = parseFloat(coords[0].trim());
                const lng = parseFloat(coords[1].trim());

                if (lat < -90 || lat > 90 || lng < -180 || lng > 180) {
                    frappe.msgprint(__('Invalid GPS coordinates range'));
                    frm.set_value('gps_coordinates', '');
                }
            } catch (e) {
                frappe.msgprint(__('GPS coordinates must be numeric'));
                frm.set_value('gps_coordinates', '');
            }
        }
    },

    generate_qr_code: function (frm) {
        frappe.call({
            method: 'universal_workshop.scrap_management.doctype.storage_location.storage_location.generate_qr_code_data',
            args: {
                location_name: frm.doc.name
            },
            callback: function (r) {
                if (r.message) {
                    // Display QR code in a dialog
                    frm.trigger('show_qr_code_dialog', r.message);
                }
            }
        });
    },

    show_qr_code_dialog: function (frm, qr_data) {
        const dialog = new frappe.ui.Dialog({
            title: __('Location QR Code'),
            fields: [
                {
                    fieldtype: 'HTML',
                    options: `
                        <div class="text-center">
                            <div id="qr-code-container"></div>
                            <p class="text-muted">${__('Scan this QR code to access location information')}</p>
                            <button class="btn btn-primary btn-sm" onclick="window.print()">
                                <i class="fa fa-print"></i> ${__('Print')}
                            </button>
                        </div>
                    `
                }
            ]
        });

        dialog.show();

        // Generate QR code using a library (you'll need to include QR code library)
        // This is a placeholder - implement with actual QR code library
        setTimeout(() => {
            dialog.$wrapper.find('#qr-code-container').html(`
                <div class="qr-placeholder">
                    <i class="fa fa-qrcode" style="font-size: 100px; color: #ccc;"></i>
                    <br><small>QR Code: ${qr_data}</small>
                </div>
            `);
        }, 100);
    },

    find_optimal_parts: function (frm) {
        frappe.call({
            method: 'universal_workshop.scrap_management.doctype.storage_location.storage_location.find_optimal_location',
            args: {
                location_name: frm.doc.name
            },
            callback: function (r) {
                if (r.message && r.message.length > 0) {
                    frm.trigger('show_optimal_parts_dialog', r.message);
                } else {
                    frappe.msgprint(__('No optimal parts found for this location'));
                }
            }
        });
    },

    show_optimal_parts_dialog: function (frm, parts_data) {
        const dialog = new frappe.ui.Dialog({
            title: __('Optimal Parts for This Location'),
            size: 'large',
            fields: [
                {
                    fieldtype: 'HTML',
                    options: frm.trigger('build_parts_table', parts_data)
                }
            ]
        });

        dialog.show();
    },

    build_parts_table: function (frm, parts_data) {
        let table_html = `
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>${__('Part Code')}</th>
                        <th>${__('Part Name')}</th>
                        <th>${__('Weight (kg)')}</th>
                        <th>${__('Volume (m³)')}</th>
                        <th>${__('Fit Score')}</th>
                        <th>${__('Action')}</th>
                    </tr>
                </thead>
                <tbody>
        `;

        parts_data.forEach(part => {
            table_html += `
                <tr>
                    <td>${part.part_code}</td>
                    <td>${part.part_name || part.part_name_ar}</td>
                    <td>${part.weight_kg || 0}</td>
                    <td>${part.volume_m3 || 0}</td>
                    <td>
                        <span class="badge badge-${part.score > 80 ? 'success' : part.score > 60 ? 'warning' : 'secondary'}">
                            ${part.score}%
                        </span>
                    </td>
                    <td>
                        <button class="btn btn-sm btn-primary" onclick="assign_part_to_location('${part.name}', '${frm.doc.name}')">
                            ${__('Assign')}
                        </button>
                    </td>
                </tr>
            `;
        });

        table_html += '</tbody></table>';
        return table_html;
    },

    update_current_usage: function (frm) {
        frappe.call({
            method: 'universal_workshop.scrap_management.doctype.storage_location.storage_location.update_current_usage',
            args: {
                location_name: frm.doc.name
            },
            callback: function (r) {
                if (r.message) {
                    frm.reload_doc();
                    frappe.msgprint(__('Current usage updated successfully'));
                }
            }
        });
    },

    print_location_label: function (frm) {
        const print_format = 'Storage Location Label';
        frappe.utils.print(
            frm.doc.doctype,
            frm.doc.name,
            print_format,
            frm.doc.language || frappe.boot.lang
        );
    },

    open_mobile_scanner: function (frm) {
        if (frm.barcode_scanner) {
            frm.barcode_scanner.start();
        } else {
            frappe.msgprint(__('Barcode scanner not available on this device'));
        }
    },

    handle_barcode_scan: function (frm, result) {
        frappe.msgprint(__('Scanned: {0}', [result.rawValue]));

        // Process scanned barcode/QR code
        if (result.rawValue.startsWith('UW-')) {
            // This might be a part barcode
            frm.trigger('process_part_barcode', result.rawValue);
        } else if (result.rawValue.startsWith('LOC-')) {
            // This might be a location barcode
            frm.trigger('process_location_barcode', result.rawValue);
        }
    },

    process_part_barcode: function (frm, barcode) {
        frappe.call({
            method: 'universal_workshop.scrap_management.doctype.extracted_parts.extracted_parts.get_part_by_barcode',
            args: {
                barcode: barcode
            },
            callback: function (r) {
                if (r.message) {
                    frm.trigger('show_part_assignment_dialog', r.message);
                }
            }
        });
    },

    process_location_barcode: function (frm, barcode) {
        const location_code = barcode.replace('LOC-', '');
        frappe.set_route('Form', 'Storage Location', { 'location_code': location_code });
    },

    show_part_assignment_dialog: function (frm, part_data) {
        const dialog = new frappe.ui.Dialog({
            title: __('Assign Part to Location'),
            fields: [
                {
                    fieldtype: 'Data',
                    fieldname: 'part_code',
                    label: __('Part Code'),
                    default: part_data.part_code,
                    read_only: 1
                },
                {
                    fieldtype: 'Data',
                    fieldname: 'part_name',
                    label: __('Part Name'),
                    default: part_data.part_name || part_data.part_name_ar,
                    read_only: 1
                },
                {
                    fieldtype: 'Float',
                    fieldname: 'weight_kg',
                    label: __('Weight (kg)'),
                    default: part_data.weight_kg,
                    read_only: 1
                },
                {
                    fieldtype: 'Float',
                    fieldname: 'volume_m3',
                    label: __('Volume (m³)'),
                    default: part_data.volume_m3,
                    read_only: 1
                }
            ],
            primary_action_label: __('Assign to This Location'),
            primary_action: function () {
                frm.trigger('assign_part_to_current_location', part_data.name);
                dialog.hide();
            }
        });

        dialog.show();
    },

    assign_part_to_current_location: function (frm, part_name) {
        frappe.call({
            method: 'universal_workshop.scrap_management.doctype.extracted_parts.extracted_parts.assign_to_location',
            args: {
                part_name: part_name,
                location_name: frm.doc.name
            },
            callback: function (r) {
                if (r.message) {
                    frappe.msgprint(__('Part assigned successfully'));
                    frm.reload_doc();
                }
            }
        });
    },

    update_utilization_display: function (frm) {
        // Recalculate and display utilization meters
        setTimeout(() => {
            frm.trigger('setup_capacity_meters');
        }, 500);
    }
});

// Global functions for dialog actions
function assign_part_to_location(part_name, location_name) {
    frappe.call({
        method: 'universal_workshop.scrap_management.doctype.extracted_parts.extracted_parts.assign_to_location',
        args: {
            part_name: part_name,
            location_name: location_name
        },
        callback: function (r) {
            if (r.message) {
                frappe.msgprint(__('Part assigned successfully'));
                location.reload();
            }
        }
    });
}

// Barcode Scanner Class (simplified implementation)
class BarcodeScanner {
    constructor(options) {
        this.options = options;
        this.detector = new BarcodeDetector({
            formats: options.formats || ['qr_code', 'code_128']
        });
    }

    async start() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: 'environment' }
            });

            const video = document.createElement('video');
            video.srcObject = stream;
            video.play();

            const canvas = document.createElement('canvas');
            const context = canvas.getContext('2d');

            // Create scanning dialog
            const dialog = new frappe.ui.Dialog({
                title: __('Scan Barcode'),
                fields: [
                    {
                        fieldtype: 'HTML',
                        options: `
                            <div class="scanner-container text-center">
                                <div id="video-container"></div>
                                <p class="text-muted">${__('Point camera at barcode or QR code')}</p>
                                <button class="btn btn-secondary" onclick="stop_scanner()">
                                    ${__('Cancel')}
                                </button>
                            </div>
                        `
                    }
                ]
            });

            dialog.show();
            dialog.$wrapper.find('#video-container').append(video);

            // Start detection loop
            this.scanLoop(video, canvas, context, dialog);

        } catch (err) {
            frappe.msgprint(__('Camera access denied or not available'));
        }
    }

    async scanLoop(video, canvas, context, dialog) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0);

        try {
            const barcodes = await this.detector.detect(canvas);
            if (barcodes.length > 0) {
                const result = barcodes[0];
                this.options.onScan(result);
                dialog.hide();
                video.srcObject.getTracks().forEach(track => track.stop());
                return;
            }
        } catch (err) {
            console.log('Detection error:', err);
        }

        // Continue scanning
        setTimeout(() => this.scanLoop(video, canvas, context, dialog), 100);
    }
}

// CSS Styles for Arabic/RTL Support
const storage_location_styles = `
<style>
.capacity-meters {
    margin: 15px 0;
}

.capacity-meter {
    margin-bottom: 15px;
}

.capacity-meter label {
    font-weight: bold;
    margin-bottom: 5px;
    display: block;
}

.capacity-meter .progress {
    height: 20px;
    margin-bottom: 5px;
}

.efficiency-score {
    text-align: center;
    padding: 15px;
    background-color: #f8f9fa;
    border-radius: 5px;
    margin-top: 15px;
}

.location-map-container {
    margin: 10px 0;
}

.map-info {
    text-align: center;
    margin-top: 5px;
}

.scanner-container video {
    max-width: 100%;
    height: 300px;
    border: 1px solid #ccc;
    border-radius: 5px;
}

.qr-placeholder {
    padding: 30px;
    text-align: center;
}

.rtl-layout .capacity-meters,
.rtl-layout .location-map-container {
    direction: rtl;
    text-align: right;
}

.arabic-text {
    font-family: 'Tahoma', 'Arial Unicode MS', sans-serif;
    font-size: 14px;
}

@media (max-width: 768px) {
    .capacity-meter .progress {
        height: 25px;
    }
    
    .scanner-container video {
        height: 250px;
    }
}
</style>
`;

// Inject styles
if (!document.getElementById('storage-location-styles')) {
    const styleElement = document.createElement('style');
    styleElement.id = 'storage-location-styles';
    styleElement.innerHTML = storage_location_styles;
    document.head.appendChild(styleElement);
} 