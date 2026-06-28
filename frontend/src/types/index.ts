export interface ClientPrincipal {
  userId: string
  userRoles: string[]
  identityProvider: string
  userDetails: string // email
}

export interface AuthMe {
  clientPrincipal: ClientPrincipal | null
}

export interface Profile {
  user_id: string
  height_cm: number
  gender: string
}

export interface CompositionCurrent {
  date: string
  consensus_fat_pct: number | null
  garmin_fat_pct: number | null
  bias_offset_pct: number | null
  weight_kg: number | null
  lean_mass_kg: number | null
  fat_mass_kg: number | null
}

export interface TrendPoint {
  date: string
  consensus_fat_pct: number | null
  weight_kg: number | null
  lean_mass_kg: number | null
}

export interface TrendSummary {
  fat_pct_change: number | null
  weight_change_kg: number | null
  lean_mass_change_kg: number | null
}

export interface CompositionTrend {
  period_days: number
  series: TrendPoint[]
  summary: TrendSummary
}

export interface Measurement {
  date: string
  source: string
  body_fat_pct: number | null
  waist_cm: number | null
  neck_cm: number | null
  hip_cm: number | null
}

export interface MeasurementListResponse {
  total: number
  measurements: Measurement[]
}

export interface GarminStatus {
  connected: boolean
  last_sync_date: string | null
  record_count: number
}

export interface GarminSyncResponse {
  new_records: number
  total_records: number
  synced_through: string | null
}
