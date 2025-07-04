/**
 * Workshop Types Utility Composable
 * Extracted from BasicInfoStep.vue for reuse across components
 */

import { useI18n } from 'vue-i18n'

export interface WorkshopType {
  key: string
  name: string
  description: string
  services: string[]
  icon: string
}

export function useWorkshopTypes() {
  const { t } = useI18n()

  const workshopTypes: WorkshopType[] = [
    {
      key: 'general_repair',
      name: 'General Repair',
      description: 'Full-service automotive repair covering all vehicle systems and maintenance needs.',
      icon: '🔧',
      services: [
        'Engine maintenance',
        'Brake service', 
        'Oil changes',
        'Diagnostics',
        'Transmission service'
      ]
    },
    {
      key: 'body_work',
      name: 'Body Work',
      description: 'Specialized in vehicle body repair, collision damage, dent removal, and cosmetic restoration.',
      icon: '🔨',
      services: [
        'Collision repair',
        'Dent removal',
        'Frame straightening',
        'Panel replacement',
        'Rust repair'
      ]
    },
    {
      key: 'electrical',
      name: 'Electrical',
      description: 'Expert electrical system diagnostics, wiring, lighting, and electronic component repair.',
      icon: '⚡',
      services: [
        'Battery service',
        'Alternator repair',
        'Wiring diagnostics',
        'Lighting systems',
        'Electronic troubleshooting'
      ]
    },
    {
      key: 'engine_specialist',
      name: 'Engine Specialist',
      description: 'Engine overhaul, diagnostics, performance tuning, and powertrain services.',
      icon: '🏁',
      services: [
        'Engine rebuilds',
        'Performance tuning',
        'Timing belt service',
        'Valve adjustments',
        'Turbo service'
      ]
    },
    {
      key: 'tire_services',
      name: 'Tire Services',
      description: 'Tire installation, balancing, alignment, repair, and wheel services.',
      icon: '🛞',
      services: [
        'Tire installation',
        'Wheel balancing',
        'Alignment service',
        'Tire rotation',
        'Pressure monitoring'
      ]
    },
    {
      key: 'painting',
      name: 'Painting',
      description: 'Automotive painting, color matching, protective coatings, and finish restoration.',
      icon: '🎨',
      services: [
        'Full vehicle painting',
        'Touch-up services',
        'Color matching',
        'Clear coat application',
        'Surface preparation'
      ]
    },
    {
      key: 'air_conditioning',
      name: 'Air Conditioning',
      description: 'HVAC system repair, refrigerant service, climate control diagnostics.',
      icon: '❄️',
      services: [
        'A/C diagnostics',
        'Refrigerant recharge',
        'Compressor service',
        'Filter replacement',
        'System cleaning'
      ]
    }
  ]

  const getWorkshopTypeDescription = (typeKey: string): string => {
    const type = workshopTypes.find(t => t.key === typeKey || t.name === typeKey)
    return type ? t(type.description) : ''
  }

  const getWorkshopTypeServices = (typeKey: string): string[] => {
    const type = workshopTypes.find(t => t.key === typeKey || t.name === typeKey)
    return type ? type.services.map(service => t(service)) : []
  }

  const getWorkshopTypeIcon = (typeKey: string): string => {
    const type = workshopTypes.find(t => t.key === typeKey || t.name === typeKey)
    return type ? type.icon : '🔧'
  }

  const getWorkshopTypeName = (typeKey: string): string => {
    const type = workshopTypes.find(t => t.key === typeKey || t.name === typeKey)
    return type ? t(type.name) : typeKey
  }

  return {
    workshopTypes,
    getWorkshopTypeDescription,
    getWorkshopTypeServices,
    getWorkshopTypeIcon,
    getWorkshopTypeName
  }
}