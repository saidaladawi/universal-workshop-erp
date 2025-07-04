/**
 * Feature Flags Composable - Universal Workshop Frontend V2
 * 
 * Vue 3 composable wrapper for the feature flag system
 */

import { ref, computed, onMounted } from 'vue'
import { featureFlags, type FeatureFlagConfig } from '@/utils/feature-flags'
import type { FeatureFlags } from '@/types/workshop'

export interface FeatureFlagComposable {
  isEnabled: (flag: keyof FeatureFlags) => boolean
  enable: (flag: keyof FeatureFlags, config?: Partial<FeatureFlagConfig>) => void
  disable: (flag: keyof FeatureFlags) => void
  isInRollout: (flag: keyof FeatureFlags, percentage: number) => boolean
  getAll: () => Record<string, FeatureFlagConfig>
}

export function useFeatureFlags(): FeatureFlagComposable {
  const initialized = ref(false)

  onMounted(async () => {
    await featureFlags.initialize()
    initialized.value = true
  })

  const isEnabled = (flag: keyof FeatureFlags): boolean => {
    return featureFlags.isEnabled(flag)
  }

  const enable = (flag: keyof FeatureFlags, config?: Partial<FeatureFlagConfig>): void => {
    featureFlags.enableFeatureForSession(flag)
  }

  const disable = (flag: keyof FeatureFlags): void => {
    featureFlags.disableFeatureForSession(flag)
  }

  const isInRollout = (flag: keyof FeatureFlags, percentage: number): boolean => {
    const config = featureFlags.getFlagConfig(flag)
    if (!config) return false
    
    return config.rolloutPercentage >= percentage
  }

  const getAll = (): Record<string, FeatureFlagConfig> => {
    return featureFlags.getAllFlagConfigs()
  }

  return {
    isEnabled,
    enable,
    disable,
    isInRollout,
    getAll
  }
}

export default useFeatureFlags