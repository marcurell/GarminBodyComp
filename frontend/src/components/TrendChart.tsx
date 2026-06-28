import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend,
} from 'recharts'
import type { TrendPoint } from '../types'

interface Props {
  data: TrendPoint[]
  metric: 'fat' | 'weight' | 'lean'
}

const CONFIG = {
  fat:    { key: 'consensus_fat_pct', label: 'Body Fat %',   color: '#1DB9E8', unit: '%'  },
  weight: { key: 'weight_kg',         label: 'Weight',        color: '#F59E0B', unit: 'kg' },
  lean:   { key: 'lean_mass_kg',      label: 'Lean Mass',     color: '#22C55E', unit: 'kg' },
} as const

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('sv-SE', { month: 'short', day: 'numeric' })
}

export default function TrendChart({ data, metric }: Props) {
  const { key, label, color, unit } = CONFIG[metric]

  const chartData = data.map(p => ({
    date: formatDate(p.date),
    value: p[key as keyof TrendPoint] as number | null,
  }))

  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={chartData} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2A2D38" />
        <XAxis
          dataKey="date"
          tick={{ fill: '#8B8FA8', fontSize: 12 }}
          tickLine={false}
          axisLine={{ stroke: '#2A2D38' }}
          interval="preserveStartEnd"
        />
        <YAxis
          tick={{ fill: '#8B8FA8', fontSize: 12 }}
          tickLine={false}
          axisLine={false}
          tickFormatter={v => `${v}${unit}`}
          domain={['auto', 'auto']}
        />
        <Tooltip
          contentStyle={{ background: '#1C1E26', border: '1px solid #2A2D38', borderRadius: 8 }}
          labelStyle={{ color: '#8B8FA8', fontSize: 12 }}
          itemStyle={{ color: color }}
          formatter={(v: number) => [`${v?.toFixed(1)}${unit}`, label]}
        />
        <Legend wrapperStyle={{ color: '#8B8FA8', fontSize: 12 }} />
        <Line
          type="monotone"
          dataKey="value"
          name={label}
          stroke={color}
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4, fill: color }}
          connectNulls
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
