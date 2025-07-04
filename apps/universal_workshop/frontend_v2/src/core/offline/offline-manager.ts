/**
 * Offline Manager - Universal Workshop Frontend V2
 * Placeholder for offline functionality
 */

export class OfflineManager {
  private static instance: OfflineManager | null = null

  static getInstance(): OfflineManager {
    if (!OfflineManager.instance) {
      OfflineManager.instance = new OfflineManager()
    }
    return OfflineManager.instance
  }

  async initialize(): Promise<void> {
    console.log('📱 Offline manager initialized (placeholder)')
  }
}

export default OfflineManager