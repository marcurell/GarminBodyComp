import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { CompositionCurrent, CompositionTrend } from '../types'
import StatCard from '../components/StatCard'
import TrendChart from '../components/TrendChart'

type Metric = 'fat' | 'weight' | 'lean'

export default function Dashboard() {
  const [current, setCurrent] = useState<CompositionCurrent | null>(null)
  const [trend, setTrend] = useState<CompositionTrend | null>(null)
  const [days, setDays] = useState(30)
  const [metric, setMetric] = useState<Metric>('fat')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    Promise.all([api.getCompositionCurrent(), api.getCompositionTrend(days)])
      .then(([c, t]) => { setCurrent(c); setTrend(t) })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [days])

  if (loading) return <div className="text-muted animate-pulse">Loading...</div>

  if (error) return (
    <div className="card border-danger/30 text-danger">
      <p className="font-semibold">Could not load composition data</p>
      <p className="text-sm mt-1 text-muted">{error}</p>
      <p className="text-sm mt-3 text-muted">Make sure you have imported Garmin data first.</p>
    </div>
  )

  const s = trend?.summary

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          {current && <p className="text-muted text-sm mt-0.5">Last updated {current.date}</p>}
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Body Fat"
          value={current?.consensus_fat_pct?.toFixed(1)}
          unit="%"
          change={s?.fat_pct_change}
          changeUnit="%"
        />
        <StatCard
          label="Weight"
          value={current?.weight_kg?.toFixed(1)}
          unit="kg"
          change={s?.weight_change_kg}
          changeUnit="kg"
        />
        <StatCard
          label="Lean Mass"
          value={current?.lean_mass_kg?.toFixed(1)}
          unit="kg"
          change={s?.lean_mass_change_kg}
          changeUnit="kg lean"
        />
        <StatCard
          label="Fat Mass"
          value={current?.fat_mass_kg?.toFixed(1)}
          unit="kg"
        />
      </div>

      {/* Chart */}
      <div className="card">
        <div className="flex items-center justify-between mb-5">
          {/* Metric toggle */}
          <div className="flex gap-1 bg-bg rounded-lg p-1">
            {(['fat', 'weight', 'lean'] as Metric[]).map(m => (
              <button
                key={m}
                onClick={() => setMetric(m)}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  metric === m ? 'bg-surface text-text' : 'text-muted hover:text-text'
                }`}
              >
                {m === 'fat' ? 'Body Fat %' : m === 'weight' ? 'Weight' : 'Lean Mass'}
              </button>
            ))}
          </div>

          {/* Period toggle */}
          <div className="flex gap-1 bg-bg rounded-lg p-1">
            {[30, 60, 90].map(d => (
              <button
                key={d}
                onClick={() => setDays(d)}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  days === d ? 'bg-surface text-text' : 'text-muted hover:text-text'
                }`}
              >
                {d}d
              </button>
            ))}
          </div>
        </div>

        {trend && <TrendChart data={trend.series} metric={metric} />}
      </div>

      {/* Garmin bias note */}
      {current?.bias_offset_pct != null && (
        <p className="text-muted text-xs">
          Garmin bias correction: {current.bias_offset_pct > 0 ? '+' : ''}{current.bias_offset_pct.toFixed(1)}% offset applied based on Navy method calibration.
        </p>
      )}
    </div>
  )
}
