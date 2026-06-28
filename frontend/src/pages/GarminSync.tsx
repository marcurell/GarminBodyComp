import { useEffect, useState } from 'react'
import { RefreshCw, Wifi, WifiOff, AlertTriangle } from 'lucide-react'
import { api } from '../api/client'
import type { GarminStatus, GarminSyncResponse } from '../types'

export default function GarminSync() {
  const [status, setStatus] = useState<GarminStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const [connecting, setConnecting] = useState(false)
  const [syncResult, setSyncResult] = useState<GarminSyncResponse | null>(null)
  const [error, setError] = useState('')
  const [days, setDays] = useState(30)

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const loadStatus = () =>
    api.getGarminStatus()
      .then(setStatus)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))

  useEffect(() => { loadStatus() }, [])

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault()
    setConnecting(true)
    setError('')
    try {
      await api.connectGarmin(email, password)
      setPassword('')
      await loadStatus()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Connection failed')
    } finally {
      setConnecting(false)
    }
  }

  const handleSync = async () => {
    setSyncing(true)
    setError('')
    setSyncResult(null)
    try {
      const r = await api.syncGarmin(days)
      setSyncResult(r)
      await loadStatus()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Sync failed')
    } finally {
      setSyncing(false)
    }
  }

  return (
    <div className="space-y-5 max-w-lg">
      <h1 className="text-2xl font-bold">Garmin Sync</h1>

      {error && (
        <div className="card border-danger/30 text-danger flex gap-3">
          <AlertTriangle size={18} className="shrink-0 mt-0.5" />
          <p className="text-sm">{error}</p>
        </div>
      )}

      {/* Status */}
      <div className="card">
        <div className="flex items-center gap-3">
          {loading ? (
            <div className="w-4 h-4 rounded-full bg-muted animate-pulse" />
          ) : status?.connected ? (
            <Wifi size={20} className="text-success" />
          ) : (
            <WifiOff size={20} className="text-muted" />
          )}
          <div>
            <p className="font-semibold">
              {loading ? 'Checking…' : status?.connected ? 'Connected' : 'Not connected'}
            </p>
            {status?.connected && (
              <p className="text-muted text-sm">
                {status.record_count} records · Last sync: {status.last_sync_date ?? 'never'}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Sync controls (only when connected) */}
      {status?.connected && (
        <div className="card space-y-4">
          <div className="flex items-center justify-between">
            <p className="font-medium">Sync Garmin data</p>
            <div className="flex gap-1 bg-bg rounded-lg p-1">
              {[14, 30, 90].map(d => (
                <button
                  key={d}
                  onClick={() => setDays(d)}
                  className={`px-2.5 py-1 rounded-md text-sm transition-colors ${
                    days === d ? 'bg-surface text-text' : 'text-muted hover:text-text'
                  }`}
                >
                  {d}d
                </button>
              ))}
            </div>
          </div>

          <button
            className="btn-primary flex items-center gap-2"
            onClick={handleSync}
            disabled={syncing}
          >
            <RefreshCw size={16} className={syncing ? 'animate-spin' : ''} />
            {syncing ? 'Syncing…' : `Sync last ${days} days`}
          </button>

          {syncResult && (
            <div className="bg-success/10 border border-success/20 rounded-lg px-4 py-3 text-success text-sm">
              Synced {syncResult.new_records} new records · {syncResult.total_records} total · through {syncResult.synced_through}
            </div>
          )}
        </div>
      )}

      {/* Connect form */}
      <div className="card space-y-4">
        <p className="font-medium">{status?.connected ? 'Re-connect account' : 'Connect Garmin account'}</p>

        <div className="flex gap-2 bg-warning/10 border border-warning/20 rounded-lg px-3 py-2 text-warning text-xs">
          <AlertTriangle size={14} className="shrink-0 mt-0.5" />
          <span>Credentials are stored encrypted and used only to fetch your fitness data via the Garmin API.</span>
        </div>

        <form onSubmit={handleConnect} className="space-y-3">
          <div>
            <label className="label">Garmin email</label>
            <input type="email" className="input" value={email}
              onChange={e => setEmail(e.target.value)} required />
          </div>
          <div>
            <label className="label">Garmin password</label>
            <input type="password" className="input" value={password}
              onChange={e => setPassword(e.target.value)} required />
          </div>
          <button type="submit" className="btn-primary" disabled={connecting}>
            {connecting ? 'Connecting…' : 'Connect & import 90 days'}
          </button>
        </form>
      </div>
    </div>
  )
}
