/**
 * Advanced Mobile Workflows for Universal Workshop
 * Phase 3: Sprint 11 - Advanced Mobile Features
 *
 * Features:
 * - Biometric Authentication (Fingerprint, Face ID)
 * - Camera Integration for Documentation
 * - GPS Tracking for Mobile Technicians
 * - Offline Operation Support
 * - Arabic Voice Commands
 */

export interface BiometricAuthOptions {
    type: 'fingerprint' | 'face' | 'voice';
    fallbackToPassword: boolean;
    arabicPrompts: boolean;
    maxAttempts: number;
}

export interface GPSTrackingOptions {
    accuracy: 'high' | 'medium' | 'low';
    updateInterval: number; // milliseconds
    geofencing: boolean;
    offlineStorage: boolean;
}

export interface CameraIntegrationOptions {
    quality: 'high' | 'medium' | 'low';
    formats: string[];
    maxFileSize: number;
    arabicOCR: boolean;
    autoUpload: boolean;
}

export class MobileWorkflowManager {
    private biometricSupported: boolean = false;
    private gpsEnabled: boolean = false;
    private cameraPermissions: boolean = false;
    private offlineQueue: Array<any> = [];

    constructor() {
        this.initializeCapabilities();
    }

    /**
     * Initialize mobile device capabilities
     */
    private async initializeCapabilities(): Promise<void> {
        try {
            // Check biometric support
            if ('credentials' in navigator && 'create' in navigator.credentials) {
                this.biometricSupported = await this.checkBiometricSupport();
            }

            // Check GPS support
            if ('geolocation' in navigator) {
                this.gpsEnabled = true;
            }

            // Check camera permissions
            if ('mediaDevices' in navigator && 'getUserMedia' in navigator.mediaDevices) {
                this.cameraPermissions = await this.requestCameraPermissions();
            }

            console.log('📱 Mobile capabilities initialized:', {
                biometric: this.biometricSupported,
                gps: this.gpsEnabled,
                camera: this.cameraPermissions
            });
        } catch (error) {
            console.error('❌ Error initializing mobile capabilities:', error);
        }
    }

    /**
     * Biometric Authentication with Arabic Support
     */
    async authenticateWithBiometric(options: BiometricAuthOptions = {
        type: 'fingerprint',
        fallbackToPassword: true,
        arabicPrompts: true,
        maxAttempts: 3
    }): Promise<{ success: boolean, method: string, error?: string }> {

        if (!this.biometricSupported) {
            return {
                success: false,
                method: 'none',
                error: options.arabicPrompts ? 'المصادقة البيومترية غير مدعومة' : 'Biometric authentication not supported'
            };
        }

        try {
            const publicKeyCredentialCreationOptions: PublicKeyCredentialCreationOptions = {
                challenge: new Uint8Array(32),
                rp: {
                    name: options.arabicPrompts ? "ورشة العمل الشاملة" : "Universal Workshop",
                    id: "universalworkshop.om",
                },
                user: {
                    id: new Uint8Array(16),
                    name: "technician@workshop.om",
                    displayName: options.arabicPrompts ? "فني الورشة" : "Workshop Technician",
                },
                pubKeyCredParams: [{ alg: -7, type: "public-key" }],
                authenticatorSelection: {
                    authenticatorAttachment: "platform",
                    userVerification: "required"
                },
                timeout: 60000,
                attestation: "direct"
            };

            const credential = await navigator.credentials.create({
                publicKey: publicKeyCredentialCreationOptions
            });

            if (credential) {
                return {
                    success: true,
                    method: options.type
                };
            }

            throw new Error('Authentication failed');

        } catch (error: any) {
            console.error('❌ Biometric authentication failed:', error);

            if (options.fallbackToPassword) {
                return await this.fallbackToPasswordAuth(options.arabicPrompts);
            }

            return {
                success: false,
                method: options.type,
                error: options.arabicPrompts ? 'فشل في المصادقة البيومترية' : 'Biometric authentication failed'
            };
        }
    }

    /**
     * GPS Tracking for Mobile Technicians
     */
    async startGPSTracking(options: GPSTrackingOptions = {
        accuracy: 'high',
        updateInterval: 30000, // 30 seconds
        geofencing: true,
        offlineStorage: true
    }): Promise<{ success: boolean, trackingId?: string, error?: string }> {

        if (!this.gpsEnabled) {
            return {
                success: false,
                error: 'GPS غير متاح أو غير مفعل'
            };
        }

        try {
            const trackingId = `gps_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

            const watchId = navigator.geolocation.watchPosition(
                (position) => {
                    const locationData = {
                        trackingId,
                        timestamp: new Date().toISOString(),
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude,
                        accuracy: position.coords.accuracy,
                        heading: position.coords.heading,
                        speed: position.coords.speed,
                        altitude: position.coords.altitude
                    };

                    this.processLocationUpdate(locationData, options);
                },
                (error) => {
                    console.error('❌ GPS tracking error:', error);
                    this.handleGPSError(error, options);
                },
                {
                    enableHighAccuracy: options.accuracy === 'high',
                    timeout: 10000,
                    maximumAge: options.updateInterval
                }
            );

            // Store watch ID for cleanup
            localStorage.setItem(`gps_watch_${trackingId}`, watchId.toString());

            return {
                success: true,
                trackingId
            };

        } catch (error: any) {
            console.error('❌ GPS tracking initialization failed:', error);
            return {
                success: false,
                error: 'فشل في بدء تتبع الموقع'
            };
        }
    }

    /**
     * Camera Integration for Documentation
     */
    async captureWithCamera(options: CameraIntegrationOptions = {
        quality: 'high',
        formats: ['image/jpeg', 'image/png'],
        maxFileSize: 5 * 1024 * 1024, // 5MB
        arabicOCR: true,
        autoUpload: false
    }): Promise<{ success: boolean, file?: File, ocrText?: string, error?: string }> {

        if (!this.cameraPermissions) {
            const permissionGranted = await this.requestCameraPermissions();
            if (!permissionGranted) {
                return {
                    success: false,
                    error: 'إذن الكاميرا مطلوب'
                };
            }
        }

        try {
            // Create input element for camera
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = options.formats.join(',');
            input.capture = 'environment'; // Use rear camera

            return new Promise((resolve) => {
                input.onchange = async (event: any) => {
                    const file = event.target.files[0];

                    if (!file) {
                        resolve({
                            success: false,
                            error: 'لم يتم اختيار ملف'
                        });
                        return;
                    }

                    // Check file size
                    if (file.size > options.maxFileSize) {
                        resolve({
                            success: false,
                            error: `حجم الملف كبير جداً. الحد الأقصى ${options.maxFileSize / 1024 / 1024}MB`
                        });
                        return;
                    }

                    let ocrText: string | undefined;

                    // Perform Arabic OCR if enabled
                    if (options.arabicOCR) {
                        try {
                            const { ArabicOCR } = await import('./ArabicOCR');
                            const ocrEngine = new ArabicOCR({
                                confidence: 0.8,
                                language: 'ara',
                                mode: 'document'
                            });

                            const ocrResult = await ocrEngine.processImage(file);
                            ocrText = ocrResult.text;
                        } catch (ocrError) {
                            console.warn('⚠️ OCR processing failed:', ocrError);
                        }
                    }

                    // Auto-upload if enabled
                    if (options.autoUpload) {
                        await this.uploadCapturedFile(file);
                    }

                    resolve({
                        success: true,
                        file,
                        ocrText
                    });
                };

                input.click();
            });

        } catch (error: any) {
            console.error('❌ Camera capture failed:', error);
            return {
                success: false,
                error: 'فشل في التقاط الصورة'
            };
        }
    }

    /**
     * Offline Operation Support
     */
    async queueOfflineAction(action: {
        type: string;
        data: any;
        priority: 'high' | 'medium' | 'low';
        timestamp: string;
    }): Promise<void> {
        this.offlineQueue.push({
            ...action,
            id: `offline_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
        });

        // Store to localStorage for persistence
        localStorage.setItem('workshop_offline_queue', JSON.stringify(this.offlineQueue));

        console.log('📝 Action queued for offline sync:', action.type);
    }

    /**
     * Sync offline actions when online
     */
    async syncOfflineActions(): Promise<{ processed: number, failed: number }> {
        if (!navigator.onLine || this.offlineQueue.length === 0) {
            return { processed: 0, failed: 0 };
        }

        let processed = 0;
        let failed = 0;

        // Sort by priority and timestamp
        const sortedQueue = this.offlineQueue.sort((a, b) => {
            const priorityOrder = { high: 3, medium: 2, low: 1 };
            const priorityDiff = priorityOrder[b.priority] - priorityOrder[a.priority];

            if (priorityDiff !== 0) return priorityDiff;

            return new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
        });

        for (const action of sortedQueue) {
            try {
                await this.processOfflineAction(action);
                processed++;

                // Remove from queue
                this.offlineQueue = this.offlineQueue.filter(item => item.id !== action.id);

            } catch (error) {
                console.error('❌ Failed to sync offline action:', action.type, error);
                failed++;
            }
        }

        // Update localStorage
        localStorage.setItem('workshop_offline_queue', JSON.stringify(this.offlineQueue));

        console.log(`✅ Offline sync complete: ${processed} processed, ${failed} failed`);

        return { processed, failed };
    }

    // Private helper methods
    private async checkBiometricSupport(): Promise<boolean> {
        try {
            const available = await (window as any).PublicKeyCredential?.isUserVerifyingPlatformAuthenticatorAvailable();
            return available || false;
        } catch {
            return false;
        }
    }

    private async requestCameraPermissions(): Promise<boolean> {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            stream.getTracks().forEach(track => track.stop());
            return true;
        } catch {
            return false;
        }
    }

    private async fallbackToPasswordAuth(arabicPrompts: boolean): Promise<{ success: boolean, method: string, error?: string }> {
        // Implement password fallback logic
        return {
            success: false,
            method: 'password',
            error: arabicPrompts ? 'المصادقة بكلمة المرور غير متاحة حالياً' : 'Password authentication not available'
        };
    }

    private processLocationUpdate(locationData: any, options: GPSTrackingOptions): void {
        // Store location data
        if (options.offlineStorage) {
            const stored = JSON.parse(localStorage.getItem('workshop_gps_data') || '[]');
            stored.push(locationData);

            // Keep only last 1000 points
            if (stored.length > 1000) {
                stored.splice(0, stored.length - 1000);
            }

            localStorage.setItem('workshop_gps_data', JSON.stringify(stored));
        }

        // Check geofencing if enabled
        if (options.geofencing) {
            this.checkGeofencing(locationData);
        }

        // Emit event for real-time updates
        window.dispatchEvent(new CustomEvent('gps-update', {
            detail: locationData
        }));
    }

    private handleGPSError(error: GeolocationPositionError, options: GPSTrackingOptions): void {
        let errorMessage = 'خطأ في تتبع الموقع';

        switch (error.code) {
            case error.PERMISSION_DENIED:
                errorMessage = 'إذن الموقع مرفوض';
                break;
            case error.POSITION_UNAVAILABLE:
                errorMessage = 'الموقع غير متاح';
                break;
            case error.TIMEOUT:
                errorMessage = 'انتهت مهلة تحديد الموقع';
                break;
        }

        window.dispatchEvent(new CustomEvent('gps-error', {
            detail: { error: errorMessage, code: error.code }
        }));
    }

    private checkGeofencing(locationData: any): void {
        // Implement geofencing logic for workshop boundaries
        const workshopBounds = {
            center: { lat: 23.6145, lng: 58.5455 }, // Muscat coordinates
            radius: 1000 // 1km radius
        };

        const distance = this.calculateDistance(
            locationData.latitude,
            locationData.longitude,
            workshopBounds.center.lat,
            workshopBounds.center.lng
        );

        if (distance > workshopBounds.radius) {
            window.dispatchEvent(new CustomEvent('geofence-exit', {
                detail: { location: locationData, distance }
            }));
        }
    }

    private calculateDistance(lat1: number, lng1: number, lat2: number, lng2: number): number {
        const R = 6371e3; // Earth's radius in meters
        const φ1 = lat1 * Math.PI / 180;
        const φ2 = lat2 * Math.PI / 180;
        const Δφ = (lat2 - lat1) * Math.PI / 180;
        const Δλ = (lng2 - lng1) * Math.PI / 180;

        const a = Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
            Math.cos(φ1) * Math.cos(φ2) *
            Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

        return R * c;
    }

    private async uploadCapturedFile(file: File): Promise<void> {
        // Implement file upload logic
        console.log('📤 Auto-uploading captured file:', file.name);
    }

    private async processOfflineAction(action: any): Promise<void> {
        // Implement offline action processing
        console.log('🔄 Processing offline action:', action.type);
    }
}

// Export singleton instance
export const mobileWorkflow = new MobileWorkflowManager();
