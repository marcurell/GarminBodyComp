from datetime import date
from typing import Optional
from pydantic import BaseModel


class CompositionCurrent(BaseModel):
    date: date
    consensus_fat_pct: Optional[float]
    garmin_fat_pct: Optional[float]
    bias_offset_pct: Optional[float]
    weight_kg: Optional[float]
    lean_mass_kg: Optional[float]
    fat_mass_kg: Optional[float]


class TrendPoint(BaseModel):
    date: date
    consensus_fat_pct: Optional[float]
    weight_kg: Optional[float]
    lean_mass_kg: Optional[float]


class TrendSummary(BaseModel):
    fat_pct_change: Optional[float]
    weight_change_kg: Optional[float]
    lean_mass_change_kg: Optional[float]


class CompositionTrend(BaseModel):
    period_days: int
    series: list[TrendPoint]
    summary: TrendSummary
