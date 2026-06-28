import type { AuthMe } from '../types'

const API_BASE = '/api/v1'

let cachedEmail: string | null = null

async function getUserEmail(): Promise<string> {
  if (cachedEmail) return cachedEmail
  try {
    const res = await fetch('/.auth/me')
    if (!res.ok) return ''
    const data: AuthMe = await res.json()
    cachedEmail = data.clientPrincipal?.userDetails ?? ''
    return cachedEmail
  } catch {
    return ''
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const email = await getUserEmail()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> ?? {}),
  }
  if (email) {
    headers['X-User-Email'] = email
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers })

  if (!res.ok) {
    let detail = `HTTP ${res.status}`
    try {
      const body = await res.json()
      detail = body.detail ?? body.title ?? detail
    } catch { /* ignore */ }
    throw new Error(detail)
  }

  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const api = {
  getProfile: () => request<import('../types').Profile>('/me'),
  updateProfile: (body: { height_cm: number; gender: string }) =>
    request<import('../types').Profile>('/me', { method: 'PUT', body: JSON.stringify(body) }),

  getCompositionCurrent: () => request<import('../types').CompositionCurrent>('/composition/current'),
  getCompositionTrend: (days = 30) => request<import('../types').CompositionTrend>(`/composition/trend?days=${days}`),

  getMeasurements: () => request<import('../types').MeasurementListResponse>('/measurements'),
  addMeasurement: (body: Partial<import('../types').Measurement>) =>
    request<import('../types').Measurement>('/measurements', { method: 'POST', body: JSON.stringify(body) }),
  deleteMeasurement: (date: string, source: string) =>
    request<void>(`/measurements/${date}/${source}`, { method: 'DELETE' }),

  getGarminStatus: () => request<import('../types').GarminStatus>('/garmin/status'),
  connectGarmin: (email: string, password: string) =>
    request<{ status: string; message: string }>('/garmin/connect', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  syncGarmin: (days = 30) =>
    request<import('../types').GarminSyncResponse>(`/garmin/sync?days=${days}`, { method: 'POST' }),
}
