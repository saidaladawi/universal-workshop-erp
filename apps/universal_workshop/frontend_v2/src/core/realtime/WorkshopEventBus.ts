/**
 * Real-Time Event Bus & WebSocket Manager
 * Phase 3: Sprint 1-4 - Real-Time Foundation
 * 
 * Features:
 * - WebSocket event bus with Arabic support
 * - Event-driven architecture
 * - Real-time service order updates
 * - Arabic notification templates
 * - Connection pooling and rate limiting
 */

export interface WorkshopEvent {
  id: string;
  type: 'service_update' | 'technician_status' | 'inventory_change' | 'customer_notification' | 'system_alert';
  source: string;
  timestamp: Date;
  data: any;
  priority: 'critical' | 'high' | 'medium' | 'low';
  target?: string | string[]; // Specific recipients
  requiresAck?: boolean;
  ttl?: number; // Time to live in seconds
}

export interface ArabicNotificationTemplate {
  id: string;
  type: string;
  titleEn: string;
  titleAr: string;
  messageEn: string;
  messageAr: string;
  actions?: Array<{
    labelEn: string;
    labelAr: string;
    action: string;
    variant: 'primary' | 'secondary' | 'success' | 'warning' | 'danger';
  }>;
}

export interface ConnectionMetrics {
  totalConnections: number;
  activeConnections: number;
  messagesSent: number;
  messagesReceived: number;
  averageLatency: number;
  reconnectAttempts: number;
  lastReconnect?: Date;
}

export class WorkshopEventBus {
  private websocket: WebSocket | null = null;
  private eventHandlers: Map<string, Set<Function>> = new Map();
  private connectionQueue: WorkshopEvent[] = [];
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectDelay: number = 1000; // Start with 1 second
  private isConnected: boolean = false;
  private connectionMetrics: ConnectionMetrics = {
    totalConnections: 0,
    activeConnections: 0,
    messagesSent: 0,
    messagesReceived: 0,
    averageLatency: 0,
    reconnectAttempts: 0
  };
  private latencyHistory: number[] = [];
  private rateLimiter: Map<string, number[]> = new Map();
  private readonly maxMessagesPerMinute: number = 60;

  // Arabic notification templates
  private notificationTemplates: Map<string, ArabicNotificationTemplate> = new Map([
    ['service_started', {
      id: 'service_started',
      type: 'service_update',
      titleEn: 'Service Started',
      titleAr: 'بدء الخدمة',
      messageEn: 'Your vehicle service has been started by technician {technicianName}',
      messageAr: 'تم بدء خدمة مركبتك بواسطة الفني {technicianName}',
      actions: [
        { labelEn: 'View Details', labelAr: 'عرض التفاصيل', action: 'view_service', variant: 'primary' },
        { labelEn: 'Call Workshop', labelAr: 'اتصل بالورشة', action: 'call_workshop', variant: 'secondary' }
      ]
    }],
    ['service_completed', {
      id: 'service_completed',
      type: 'service_update',
      titleEn: 'Service Completed',
      titleAr: 'اكتمال الخدمة',
      messageEn: 'Your vehicle service has been completed. Total cost: {totalCost} OMR',
      messageAr: 'تم اكتمال خدمة مركبتك. التكلفة الإجمالية: {totalCost} ريال عماني',
      actions: [
        { labelEn: 'Pay Now', labelAr: 'ادفع الآن', action: 'pay_now', variant: 'success' },
        { labelEn: 'View Invoice', labelAr: 'عرض الفاتورة', action: 'view_invoice', variant: 'primary' }
      ]
    }],
    ['parts_needed', {
      id: 'parts_needed',
      type: 'service_update',
      titleEn: 'Parts Required',
      titleAr: 'قطع غيار مطلوبة',
      messageEn: 'Additional parts are needed for your service. Estimated additional cost: {additionalCost} OMR',
      messageAr: 'قطع غيار إضافية مطلوبة لخدمتك. التكلفة الإضافية المتوقعة: {additionalCost} ريال عماني',
      actions: [
        { labelEn: 'Approve', labelAr: 'موافق', action: 'approve_parts', variant: 'success' },
        { labelEn: 'Decline', labelAr: 'رفض', action: 'decline_parts', variant: 'warning' }
      ]
    }],
    ['technician_assigned', {
      id: 'technician_assigned',
      type: 'technician_status',
      titleEn: 'Technician Assigned',
      titleAr: 'تم تعيين فني',
      messageEn: 'Technician {technicianName} has been assigned to your service',
      messageAr: 'تم تعيين الفني {technicianName} لخدمتك',
      actions: [
        { labelEn: 'View Profile', labelAr: 'عرض الملف الشخصي', action: 'view_technician', variant: 'primary' }
      ]
    }],
    ['inventory_low', {
      id: 'inventory_low',
      type: 'inventory_change',
      titleEn: 'Low Inventory Alert',
      titleAr: 'تنبيه نقص المخزون',
      messageEn: 'Inventory for {itemName} is running low. Current stock: {currentStock} units',
      messageAr: 'مخزون {itemName} ينفد. المخزون الحالي: {currentStock} وحدة',
      actions: [
        { labelEn: 'Reorder', labelAr: 'إعادة طلب', action: 'reorder_item', variant: 'warning' },
        { labelEn: 'View Details', labelAr: 'عرض التفاصيل', action: 'view_inventory', variant: 'secondary' }
      ]
    }]
  ]);

  constructor(private wsUrl: string = 'ws://localhost:8080/workshop') {
    this.initialize();
  }

  /**
   * Initialize the event bus
   */
  private async initialize(): Promise<void> {
    try {
      await this.connect();
      this.setupHeartbeat();
      this.setupRateLimiting();
      console.log('📡 Workshop Event Bus initialized');
    } catch (error) {
      console.error('❌ Failed to initialize Workshop Event Bus:', error);
    }
  }

  /**
   * Connect to WebSocket server
   */
  async connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.websocket = new WebSocket(this.wsUrl);

        this.websocket.onopen = () => {
          console.log('🔗 Connected to Workshop Event Bus');
          this.isConnected = true;
          this.reconnectAttempts = 0;
          this.connectionMetrics.totalConnections++;
          this.connectionMetrics.activeConnections++;
          
          // Process queued events
          this.processConnectionQueue();
          
          // Emit connection event
          this.emit('connection', { status: 'connected', metrics: this.connectionMetrics });
          
          resolve();
        };

        this.websocket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.handleIncomingEvent(data);
          } catch (error) {
            console.error('❌ Error parsing WebSocket message:', error);
          }
        };

        this.websocket.onerror = (error) => {
          console.error('❌ WebSocket error:', error);
          this.emit('error', { error, metrics: this.connectionMetrics });
          reject(error);
        };

        this.websocket.onclose = (event) => {
          console.log('🔌 WebSocket connection closed:', event.code, event.reason);
          this.isConnected = false;
          this.connectionMetrics.activeConnections = Math.max(0, this.connectionMetrics.activeConnections - 1);
          
          this.emit('connection', { status: 'disconnected', code: event.code, reason: event.reason });
          
          // Attempt to reconnect if not intentionally closed
          if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.attemptReconnect();
          }
        };

      } catch (error) {
        console.error('❌ Failed to create WebSocket connection:', error);
        reject(error);
      }
    });
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.websocket) {
      this.websocket.close(1000, 'Intentional disconnect');
      this.websocket = null;
    }
  }

  /**
   * Send event through the bus
   */
  async send(event: Omit<WorkshopEvent, 'id' | 'timestamp'>): Promise<string> {
    const fullEvent: WorkshopEvent = {
      id: this.generateEventId(),
      timestamp: new Date(),
      ...event
    };

    return this.sendEvent(fullEvent);
  }

  /**
   * Subscribe to specific event types
   */
  on(eventType: string, handler: Function): () => void {
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, new Set());
    }
    
    this.eventHandlers.get(eventType)!.add(handler);
    
    // Return unsubscribe function
    return () => {
      this.eventHandlers.get(eventType)?.delete(handler);
    };
  }

  /**
   * Send notification using Arabic templates
   */
  async sendNotification(
    templateId: string, 
    variables: Record<string, any> = {},
    target?: string | string[]
  ): Promise<string> {
    
    const template = this.notificationTemplates.get(templateId);
    if (!template) {
      throw new Error(`Notification template '${templateId}' not found`);
    }

    const notification = {
      type: 'customer_notification' as const,
      source: 'workshop_system',
      data: {
        template: template,
        variables: variables,
        messageEn: this.interpolateTemplate(template.messageEn, variables),
        messageAr: this.interpolateTemplate(template.messageAr, variables),
        titleEn: this.interpolateTemplate(template.titleEn, variables),
        titleAr: this.interpolateTemplate(template.titleAr, variables)
      },
      priority: 'medium' as const,
      target: target
    };

    return this.send(notification);
  }

  /**
   * Broadcast system alert
   */
  async broadcastAlert(
    titleEn: string,
    titleAr: string,
    messageEn: string,
    messageAr: string,
    priority: 'critical' | 'high' | 'medium' | 'low' = 'medium'
  ): Promise<string> {
    
    return this.send({
      type: 'system_alert',
      source: 'workshop_system',
      data: {
        titleEn,
        titleAr,
        messageEn,
        messageAr
      },
      priority
    });
  }

  /**
   * Update service status in real-time
   */
  async updateServiceStatus(
    serviceId: string,
    status: string,
    statusAr: string,
    details?: any
  ): Promise<string> {
    
    return this.send({
      type: 'service_update',
      source: 'workshop_system',
      data: {
        serviceId,
        status,
        statusAr,
        details,
        timestamp: new Date().toISOString()
      },
      priority: 'high',
      target: [`service_${serviceId}`, `customer_${details?.customerId}`].filter(Boolean)
    });
  }

  /**
   * Update technician status
   */
  async updateTechnicianStatus(
    technicianId: string,
    status: 'available' | 'busy' | 'break' | 'offline',
    currentService?: string
  ): Promise<string> {
    
    const statusTranslations = {
      available: 'متاح',
      busy: 'مشغول',
      break: 'استراحة',
      offline: 'غير متصل'
    };

    return this.send({
      type: 'technician_status',
      source: 'workshop_system',
      data: {
        technicianId,
        status,
        statusAr: statusTranslations[status],
        currentService,
        timestamp: new Date().toISOString()
      },
      priority: 'medium',
      target: [`technician_${technicianId}`, 'workshop_dashboard']
    });
  }

  /**
   * Get connection metrics
   */
  getMetrics(): ConnectionMetrics {
    return { ...this.connectionMetrics };
  }

  /**
   * Get average latency over last 100 messages
   */
  getAverageLatency(): number {
    if (this.latencyHistory.length === 0) return 0;
    
    const sum = this.latencyHistory.reduce((a, b) => a + b, 0);
    return sum / this.latencyHistory.length;
  }

  // Private methods
  private async sendEvent(event: WorkshopEvent): Promise<string> {
    // Check rate limiting
    if (!this.checkRateLimit(event.source)) {
      throw new Error('Rate limit exceeded for source: ' + event.source);
    }

    if (!this.isConnected || !this.websocket) {
      // Queue event for when connection is restored
      this.connectionQueue.push(event);
      console.warn('⚠️ Event queued - WebSocket not connected:', event.type);
      return event.id;
    }

    try {
      const startTime = performance.now();
      
      this.websocket.send(JSON.stringify(event));
      this.connectionMetrics.messagesSent++;
      
      // Track latency (simplified - in real implementation, you'd wait for ack)
      const latency = performance.now() - startTime;
      this.updateLatencyHistory(latency);
      
      console.log('📤 Event sent:', event.type, event.id);
      return event.id;
      
    } catch (error) {
      console.error('❌ Failed to send event:', error);
      throw error;
    }
  }

  private handleIncomingEvent(data: any): void {
    try {
      this.connectionMetrics.messagesReceived++;
      
      // Emit to specific handlers
      this.emit(data.type, data);
      
      // Emit to general event handler
      this.emit('event', data);
      
      console.log('📥 Event received:', data.type);
      
    } catch (error) {
      console.error('❌ Error handling incoming event:', error);
    }
  }

  private emit(eventType: string, data: any): void {
    const handlers = this.eventHandlers.get(eventType);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(data);
        } catch (error) {
          console.error(`❌ Error in event handler for ${eventType}:`, error);
        }
      });
    }
  }

  private processConnectionQueue(): void {
    if (this.connectionQueue.length === 0) return;
    
    console.log(`📤 Processing ${this.connectionQueue.length} queued events`);
    
    const queuedEvents = [...this.connectionQueue];
    this.connectionQueue = [];
    
    queuedEvents.forEach(async (event) => {
      try {
        await this.sendEvent(event);
      } catch (error) {
        console.error('❌ Failed to send queued event:', error);
        // Re-queue if still failing
        this.connectionQueue.push(event);
      }
    });
  }

  private attemptReconnect(): void {
    this.reconnectAttempts++;
    this.connectionMetrics.reconnectAttempts++;
    
    const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), 30000);
    
    console.log(`🔄 Attempting reconnect ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${delay}ms`);
    
    setTimeout(async () => {
      try {
        await this.connect();
        this.connectionMetrics.lastReconnect = new Date();
      } catch (error) {
        console.error('❌ Reconnect attempt failed:', error);
        
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.attemptReconnect();
        } else {
          console.error('❌ Max reconnect attempts reached. Manual intervention required.');
          this.emit('max_reconnects_reached', { attempts: this.reconnectAttempts });
        }
      }
    }, delay);
  }

  private setupHeartbeat(): void {
    setInterval(() => {
      if (this.isConnected && this.websocket) {
        this.websocket.send(JSON.stringify({
          type: 'heartbeat',
          timestamp: new Date().toISOString()
        }));
      }
    }, 30000); // 30 seconds
  }

  private setupRateLimiting(): void {
    // Clean up rate limiting data every minute
    setInterval(() => {
      const now = Date.now();
      const oneMinuteAgo = now - 60000;
      
      this.rateLimiter.forEach((timestamps, source) => {
        const filtered = timestamps.filter(ts => ts > oneMinuteAgo);
        if (filtered.length === 0) {
          this.rateLimiter.delete(source);
        } else {
          this.rateLimiter.set(source, filtered);
        }
      });
    }, 60000);
  }

  private checkRateLimit(source: string): boolean {
    const now = Date.now();
    const oneMinuteAgo = now - 60000;
    
    if (!this.rateLimiter.has(source)) {
      this.rateLimiter.set(source, []);
    }
    
    const timestamps = this.rateLimiter.get(source)!;
    const recentTimestamps = timestamps.filter(ts => ts > oneMinuteAgo);
    
    if (recentTimestamps.length >= this.maxMessagesPerMinute) {
      return false;
    }
    
    recentTimestamps.push(now);
    this.rateLimiter.set(source, recentTimestamps);
    
    return true;
  }

  private updateLatencyHistory(latency: number): void {
    this.latencyHistory.push(latency);
    
    // Keep only last 100 measurements
    if (this.latencyHistory.length > 100) {
      this.latencyHistory.shift();
    }
    
    this.connectionMetrics.averageLatency = this.getAverageLatency();
  }

  private interpolateTemplate(template: string, variables: Record<string, any>): string {
    return template.replace(/\{(\w+)\}/g, (match, key) => {
      return variables[key] !== undefined ? String(variables[key]) : match;
    });
  }

  private generateEventId(): string {
    return `evt_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}

// Export singleton instance
export const workshopEventBus = new WorkshopEventBus();
