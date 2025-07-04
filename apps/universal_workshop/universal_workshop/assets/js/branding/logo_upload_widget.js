/**
 * Logo Upload Widget for Universal Workshop ERP
 * Provides drag-and-drop logo upload with real-time validation and preview
 */

frappe.provide('universal_workshop.widgets');

universal_workshop.widgets.LogoUploadWidget = class LogoUploadWidget {
    constructor(options) {
        this.options = Object.assign({
            parent: null,
            fieldname: 'workshop_logo',
            max_size: 2 * 1024 * 1024, // 2MB
            allowed_formats: ['png', 'jpg', 'jpeg', 'svg'],
            max_dimensions: [2000, 2000],
            preview_size: [200, 100],
            on_upload: null,
            on_error: null,
            on_success: null
        }, options);

        this.init();
    }

    init() {
        this.create_upload_area();
        this.bind_events();
    }

    create_upload_area() {
        this.wrapper = $(`
            <div class="logo-upload-widget">
                <div class="upload-area" data-state="empty">
                    <div class="upload-zone">
                        <div class="upload-content">
                            <div class="upload-icon">
                                <i class="fa fa-cloud-upload fa-3x"></i>
                            </div>
                            <div class="upload-text">
                                <h4>${__('Upload Workshop Logo')}</h4>
                                <p>${__('Drag and drop your logo here or click to browse')}</p>
                                <p class="text-muted">
                                    ${__('Supported formats: PNG, JPG, SVG')} • ${__('Max size: 2MB')}
                                </p>
                            </div>
                            <button type="button" class="btn btn-primary btn-browse">
                                <i class="fa fa-folder-open"></i> ${__('Browse Files')}
                            </button>
                        </div>
                    </div>
                    <div class="upload-progress" style="display: none;">
                        <div class="progress">
                            <div class="progress-bar" role="progressbar" style="width: 0%"></div>
                        </div>
                        <p class="progress-text">${__('Uploading...')}</p>
                    </div>
                    <div class="upload-preview" style="display: none;">
                        <div class="preview-container">
                            <img class="preview-image" src="" alt="Logo Preview">
                            <div class="preview-overlay">
                                <button type="button" class="btn btn-sm btn-danger btn-remove">
                                    <i class="fa fa-trash"></i>
                                </button>
                                <button type="button" class="btn btn-sm btn-primary btn-change">
                                    <i class="fa fa-edit"></i>
                                </button>
                            </div>
                        </div>
                        <div class="preview-info">
                            <h5 class="file-name"></h5>
                            <p class="file-details text-muted"></p>
                        </div>
                    </div>
                    <div class="upload-error" style="display: none;">
                        <div class="alert alert-danger">
                            <i class="fa fa-exclamation-triangle"></i>
                            <span class="error-message"></span>
                        </div>
                        <button type="button" class="btn btn-secondary btn-retry">
                            ${__('Try Again')}
                        </button>
                    </div>
                </div>
                <input type="file" class="file-input" accept=".png,.jpg,.jpeg,.svg" style="display: none;">
            </div>
        `);

        // Add CSS styles
        this.add_styles();

        // Append to parent
        if (this.options.parent) {
            $(this.options.parent).append(this.wrapper);
        }
    }

    add_styles() {
        if (!$('#logo-upload-styles').length) {
            $('head').append(`
                <style id="logo-upload-styles">
                    .logo-upload-widget {
                        margin: 15px 0;
                    }
                    
                    .upload-area {
                        border: 2px dashed #ddd;
                        border-radius: 8px;
                        padding: 30px;
                        text-align: center;
                        transition: all 0.3s ease;
                        background: #fafafa;
                        min-height: 200px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    }
                    
                    .upload-area[data-state="dragover"] {
                        border-color: #1f4e79;
                        background: #e8f4fd;
                        transform: scale(1.02);
                    }
                    
                    .upload-area[data-state="uploading"] {
                        border-color: #f39c12;
                        background: #fdf6e3;
                    }
                    
                    .upload-area[data-state="success"] {
                        border-color: #27ae60;
                        background: #f0fff4;
                    }
                    
                    .upload-area[data-state="error"] {
                        border-color: #e74c3c;
                        background: #fdf2f2;
                    }
                    
                    .upload-icon {
                        color: #bbb;
                        margin-bottom: 15px;
                    }
                    
                    .upload-text h4 {
                        margin-bottom: 10px;
                        color: #333;
                    }
                    
                    .upload-text p {
                        margin-bottom: 8px;
                    }
                    
                    .btn-browse {
                        margin-top: 15px;
                    }
                    
                    .upload-progress {
                        width: 100%;
                    }
                    
                    .progress {
                        height: 6px;
                        margin-bottom: 10px;
                    }
                    
                    .preview-container {
                        position: relative;
                        display: inline-block;
                        margin-bottom: 15px;
                    }
                    
                    .preview-image {
                        max-width: 200px;
                        max-height: 100px;
                        border: 1px solid #ddd;
                        border-radius: 4px;
                        object-fit: contain;
                        background: white;
                    }
                    
                    .preview-overlay {
                        position: absolute;
                        top: 5px;
                        right: 5px;
                        display: flex;
                        gap: 5px;
                        opacity: 0;
                        transition: opacity 0.3s ease;
                    }
                    
                    .preview-container:hover .preview-overlay {
                        opacity: 1;
                    }
                    
                    .preview-info h5 {
                        margin-bottom: 5px;
                        font-size: 14px;
                    }
                    
                    .file-details {
                        font-size: 12px;
                        margin: 0;
                    }
                    
                    .upload-error {
                        width: 100%;
                    }
                    
                    .upload-error .alert {
                        margin-bottom: 15px;
                    }
                    
                    /* RTL Support */
                    [dir="rtl"] .preview-overlay {
                        right: auto;
                        left: 5px;
                    }
                    
                    /* Dark mode support */
                    .dark-mode .upload-area {
                        background: #2c3e50;
                        border-color: #34495e;
                        color: #ecf0f1;
                    }
                    
                    .dark-mode .upload-area[data-state="dragover"] {
                        background: #34495e;
                        border-color: #3498db;
                    }
                </style>
            `);
        }
    }

    bind_events() {
        const $uploadArea = this.wrapper.find('.upload-area');
        const $fileInput = this.wrapper.find('.file-input');

        // Drag and drop events
        $uploadArea.on('dragover dragenter', (e) => {
            e.preventDefault();
            e.stopPropagation();
            $uploadArea.attr('data-state', 'dragover');
        });

        $uploadArea.on('dragleave dragend', (e) => {
            e.preventDefault();
            e.stopPropagation();
            $uploadArea.attr('data-state', 'empty');
        });

        $uploadArea.on('drop', (e) => {
            e.preventDefault();
            e.stopPropagation();
            $uploadArea.attr('data-state', 'empty');

            const files = e.originalEvent.dataTransfer.files;
            if (files.length > 0) {
                this.handle_file(files[0]);
            }
        });

        // Click to browse
        this.wrapper.find('.btn-browse, .upload-zone').on('click', () => {
            $fileInput.click();
        });

        // File input change
        $fileInput.on('change', (e) => {
            const files = e.target.files;
            if (files.length > 0) {
                this.handle_file(files[0]);
            }
        });

        // Remove button
        this.wrapper.find('.btn-remove').on('click', () => {
            this.remove_file();
        });

        // Change button
        this.wrapper.find('.btn-change').on('click', () => {
            $fileInput.click();
        });

        // Retry button
        this.wrapper.find('.btn-retry').on('click', () => {
            this.reset_to_empty();
        });
    }

    handle_file(file) {
        // Validate file
        const validation = this.validate_file(file);
        if (!validation.valid) {
            this.show_error(validation.error);
            return;
        }

        // Show uploading state
        this.show_uploading();

        // Upload file
        this.upload_file(file);
    }

    validate_file(file) {
        // Check file type
        const extension = file.name.split('.').pop().toLowerCase();
        if (!this.options.allowed_formats.includes(extension)) {
            return {
                valid: false,
                error: __('Invalid file format. Allowed formats: {0}', [this.options.allowed_formats.join(', ').toUpperCase()])
            };
        }

        // Check file size
        if (file.size > this.options.max_size) {
            const maxSizeMB = (this.options.max_size / (1024 * 1024)).toFixed(1);
            return {
                valid: false,
                error: __('File size too large. Maximum size: {0}MB', [maxSizeMB])
            };
        }

        return { valid: true };
    }

    upload_file(file) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('is_private', 0);
        formData.append('folder', 'Home/Attachments');

        // Create XMLHttpRequest for progress tracking
        const xhr = new XMLHttpRequest();

        // Progress handler
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percentComplete = (e.loaded / e.total) * 100;
                this.update_progress(percentComplete);
            }
        });

        // Success handler
        xhr.addEventListener('load', () => {
            if (xhr.status === 200) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    if (response.message && response.message.file_url) {
                        this.on_upload_success(response.message.file_url, file);
                    } else {
                        this.show_error(__('Upload failed: Invalid response'));
                    }
                } catch (e) {
                    this.show_error(__('Upload failed: Invalid response format'));
                }
            } else {
                this.show_error(__('Upload failed: Server error'));
            }
        });

        // Error handler
        xhr.addEventListener('error', () => {
            this.show_error(__('Upload failed: Network error'));
        });

        // Send request
        xhr.open('POST', '/api/method/upload_file');
        xhr.setRequestHeader('X-Frappe-CSRF-Token', frappe.csrf_token);
        xhr.send(formData);
    }

    update_progress(percent) {
        this.wrapper.find('.progress-bar').css('width', percent + '%');
        this.wrapper.find('.progress-text').text(__('Uploading... {0}%', [Math.round(percent)]));
    }

    on_upload_success(file_url, file) {
        // Validate uploaded file on server
        frappe.call({
            method: 'universal_workshop.workshop_management.doctype.workshop_profile.workshop_profile.validate_logo_file',
            args: { file_url: file_url },
            callback: (r) => {
                if (r.message && r.message.valid) {
                    this.show_success(file_url, file);

                    // Call success callback
                    if (this.options.on_success) {
                        this.options.on_success(file_url, file);
                    }
                } else {
                    const error = r.message ? r.message.error : __('File validation failed');
                    this.show_error(error);

                    // Delete the uploaded file
                    this.delete_file(file_url);
                }
            },
            error: () => {
                this.show_error(__('File validation failed'));
                this.delete_file(file_url);
            }
        });
    }

    delete_file(file_url) {
        frappe.call({
            method: 'frappe.core.api.file.remove_file',
            args: { file_url: file_url }
        });
    }

    show_uploading() {
        this.wrapper.find('.upload-area').attr('data-state', 'uploading');
        this.wrapper.find('.upload-zone').hide();
        this.wrapper.find('.upload-progress').show();
        this.wrapper.find('.upload-preview').hide();
        this.wrapper.find('.upload-error').hide();
    }

    show_success(file_url, file) {
        this.wrapper.find('.upload-area').attr('data-state', 'success');
        this.wrapper.find('.upload-zone').hide();
        this.wrapper.find('.upload-progress').hide();
        this.wrapper.find('.upload-error').hide();

        // Update preview
        this.wrapper.find('.preview-image').attr('src', file_url);
        this.wrapper.find('.file-name').text(file.name);
        this.wrapper.find('.file-details').text(
            __('Size: {0} • Format: {1}', [
                this.format_file_size(file.size),
                file.name.split('.').pop().toUpperCase()
            ])
        );

        this.wrapper.find('.upload-preview').show();

        // Store file URL
        this.current_file_url = file_url;
    }

    show_error(message) {
        this.wrapper.find('.upload-area').attr('data-state', 'error');
        this.wrapper.find('.upload-zone').hide();
        this.wrapper.find('.upload-progress').hide();
        this.wrapper.find('.upload-preview').hide();

        this.wrapper.find('.error-message').text(message);
        this.wrapper.find('.upload-error').show();

        // Call error callback
        if (this.options.on_error) {
            this.options.on_error(message);
        }
    }

    remove_file() {
        if (this.current_file_url) {
            this.delete_file(this.current_file_url);
            this.current_file_url = null;
        }

        this.reset_to_empty();

        // Call success callback with null
        if (this.options.on_success) {
            this.options.on_success(null, null);
        }
    }

    reset_to_empty() {
        this.wrapper.find('.upload-area').attr('data-state', 'empty');
        this.wrapper.find('.upload-zone').show();
        this.wrapper.find('.upload-progress').hide();
        this.wrapper.find('.upload-preview').hide();
        this.wrapper.find('.upload-error').hide();
        this.wrapper.find('.file-input').val('');
        this.current_file_url = null;
    }

    set_value(file_url) {
        if (file_url) {
            // Create a mock file object for display
            const fileName = file_url.split('/').pop();
            const mockFile = {
                name: fileName,
                size: 0 // We don't know the actual size
            };

            this.show_success(file_url, mockFile);
        } else {
            this.reset_to_empty();
        }
    }

    get_value() {
        return this.current_file_url || null;
    }

    format_file_size(bytes) {
        if (bytes === 0) return '0 Bytes';

        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));

        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}; 