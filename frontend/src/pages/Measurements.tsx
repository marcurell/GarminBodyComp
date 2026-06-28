import { useEffect, useState } from 'react'
import { Trash2, Plus, X } from 'lucide-react'
import { api } from '../api/client'
import type { Measurement } from '../types'

type Source = 'Navy' | 'DEXA' | 'BodyPod'

interface Form {
  date: string
  source: Source
  body_fat_pct: string
  waist_cm: string
  neck_cm: string
  hip_cm: string
}

const empty: Form = {
  date: new Date().toISOString().slice(0, 10),
  source: 'Navy',
  body_fat_pct: '',
  waist_cm: '',
  neck_cm: '',
  hip_cm: '',
}

const SOURCE_COLORS: Record<string, string> = {
  Navy:    'text-primary bg-primary/10',
  DEXA:    'text-warning bg-warning/10',
  BodyPod: 'text-success bg-success/10',
}

export default function Measurements() {
  const [measurements, setMeasurements] = useState<Measurement[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState<Form>(empty)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const load = () =>
    api.getMeasurements()
      .then(r => setMeasurements(r.measurements))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))

  useEffect(() => { load() }, [])

  const handleDelete = async (date: string, source: string) => {
    if (!confirm(`Delete ${source} measurement from ${date}?`)) return
    await api.deleteMeasurement(date, source)
    setMeasurements(ms => ms.filter(m => !(m.date === date && m.source === source)))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      const body: Partial<Measurement> = {
        date: form.date,
        source: form.source,
      }
      if (form.source === 'Navy') {
        body.waist_cm = parseFloat(form.waist_cm) || undefined
        body.neck_cm  = parseFloat(form.neck_cm) || undefined
        body.hip_cm   = parseFloat(form.hip_cm) || undefined
      } else {
        body.body_fat_pct = parseFloat(form.body_fat_pct) || undefined
      }
      await api.addMeasurement(body)
      setShowForm(false)
      setForm(empty)
      load()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Save failed')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Measurements</h1>
        <button className="btn-primary flex items-center gap-2" onClick={() => setShowForm(v => !v)}>
          {showForm ? <X size={16} /> : <Plus size={16} />}
          {showForm ? 'Cancel' : 'Add'}
        </button>
      </div>

      {error && <p className="text-danger text-sm">{error}</p>}

      {/* Add form */}
      {showForm && (
        <form onSubmit={handleSubmit} className="card space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Date</label>
              <input type="date" className="input" value={form.date}
                onChange={e => setForm(f => ({ ...f, date: e.target.value }))} required />
            </div>
            <div>
              <label className="label">Source</label>
              <select className="input" value={form.source}
                onChange={e => setForm(f => ({ ...f, source: e.target.value as Source }))}>
                <option value="Navy">Navy (tape)</option>
                <option value="DEXA">DEXA Scan</option>
                <option value="BodyPod">BodyPod</option>
              </select>
            </div>
          </div>

          {form.source === 'Navy' ? (
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="label">Waist (cm)</label>
                <input type="number" step="0.1" className="input" placeholder="85.0"
                  value={form.waist_cm} onChange={e => setForm(f => ({ ...f, waist_cm: e.target.value }))} />
              </div>
              <div>
                <label className="label">Neck (cm)</label>
                <input type="number" step="0.1" className="input" placeholder="38.0"
                  value={form.neck_cm} onChange={e => setForm(f => ({ ...f, neck_cm: e.target.value }))} />
              </div>
              <div>
                <label className="label">Hip (cm) — women</label>
                <input type="number" step="0.1" className="input" placeholder="optional"
                  value={form.hip_cm} onChange={e => setForm(f => ({ ...f, hip_cm: e.target.value }))} />
              </div>
            </div>
          ) : (
            <div>
              <label className="label">Body Fat %</label>
              <input type="number" step="0.1" className="input" placeholder="15.0"
                value={form.body_fat_pct} onChange={e => setForm(f => ({ ...f, body_fat_pct: e.target.value }))} />
            </div>
          )}

          <button type="submit" className="btn-primary" disabled={saving}>
            {saving ? 'Saving…' : 'Save measurement'}
          </button>
        </form>
      )}

      {/* Table */}
      <div className="card overflow-hidden p-0">
        {loading ? (
          <p className="text-muted p-5 animate-pulse">Loading…</p>
        ) : measurements.length === 0 ? (
          <p className="text-muted p-5">No measurements yet.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-muted text-left">
                <th className="px-4 py-3 font-medium">Date</th>
                <th className="px-4 py-3 font-medium">Source</th>
                <th className="px-4 py-3 font-medium text-right">Fat %</th>
                <th className="px-4 py-3 font-medium text-right">Waist</th>
                <th className="px-4 py-3 font-medium text-right">Neck</th>
                <th className="px-4 py-3 font-medium text-right">Hip</th>
                <th className="w-10" />
              </tr>
            </thead>
            <tbody>
              {measurements.map(m => (
                <tr key={`${m.date}-${m.source}`} className="border-b border-border/50 hover:bg-border/20">
                  <td className="px-4 py-3">{m.date}</td>
                  <td className="px-4 py-3">
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${SOURCE_COLORS[m.source] ?? 'text-muted bg-muted/10'}`}>
                      {m.source}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">{m.body_fat_pct != null ? `${m.body_fat_pct}%` : '—'}</td>
                  <td className="px-4 py-3 text-right">{m.waist_cm != null ? `${m.waist_cm}` : '—'}</td>
                  <td className="px-4 py-3 text-right">{m.neck_cm != null ? `${m.neck_cm}` : '—'}</td>
                  <td className="px-4 py-3 text-right">{m.hip_cm != null ? `${m.hip_cm}` : '—'}</td>
                  <td className="px-4 py-3">
                    <button className="btn-danger p-1.5" onClick={() => handleDelete(m.date, m.source)}>
                      <Trash2 size={14} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
