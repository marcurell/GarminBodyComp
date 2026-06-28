import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { Profile } from '../types'

export default function ProfilePage() {
  const [profile, setProfile] = useState<Profile | null>(null)
  const [height, setHeight] = useState('')
  const [gender, setGender] = useState('Man')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api.getProfile().then(p => {
      setProfile(p)
      setHeight(String(p.height_cm))
      setGender(p.gender)
    }).catch(e => setError(e.message))
  }, [])

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setSaved(false)
    setError('')
    try {
      const updated = await api.updateProfile({ height_cm: parseFloat(height), gender })
      setProfile(updated)
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Save failed')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-5 max-w-sm">
      <h1 className="text-2xl font-bold">Profile</h1>
      {error && <p className="text-danger text-sm">{error}</p>}

      {profile && (
        <p className="text-muted text-sm">Signed in as <span className="text-text">{profile.user_id}</span></p>
      )}

      <form onSubmit={handleSave} className="card space-y-4">
        <div>
          <label className="label">Height (cm)</label>
          <input type="number" step="0.1" className="input" value={height}
            onChange={e => setHeight(e.target.value)} required />
        </div>
        <div>
          <label className="label">Gender</label>
          <select className="input" value={gender} onChange={e => setGender(e.target.value)}>
            <option value="Man">Man</option>
            <option value="Woman">Woman</option>
          </select>
        </div>
        <button type="submit" className="btn-primary" disabled={saving}>
          {saving ? 'Saving…' : saved ? 'Saved!' : 'Save profile'}
        </button>
      </form>
    </div>
  )
}
