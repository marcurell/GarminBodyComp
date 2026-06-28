interface Props {
  label: string
  value: string | number | null | undefined
  unit?: string
  change?: number | null
  changeUnit?: string
}

export default function StatCard({ label, value, unit, change, changeUnit }: Props) {
  const isPositiveGood = changeUnit === 'kg lean'
  const isNegativeGood = !isPositiveGood

  const changeColor =
    change == null
      ? 'text-muted'
      : change === 0
      ? 'text-muted'
      : (isNegativeGood && change < 0) || (isPositiveGood && change > 0)
      ? 'text-success'
      : 'text-danger'

  return (
    <div className="card">
      <p className="label">{label}</p>
      <div className="flex items-baseline gap-1.5 mt-1">
        <span className="text-3xl font-bold text-text">
          {value != null ? value : '—'}
        </span>
        {unit && value != null && (
          <span className="text-muted text-sm">{unit}</span>
        )}
      </div>
      {change != null && (
        <p className={`text-sm mt-1 ${changeColor}`}>
          {change > 0 ? '+' : ''}{change.toFixed(1)} {changeUnit ?? ''} (30d)
        </p>
      )}
    </div>
  )
}
