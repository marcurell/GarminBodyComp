import math
from typing import Annotated

import pandas as pd
from fastapi import APIRouter, Depends, Query

from api.dependencies import get_current_user
from api.errors import ProblemDetailException
from api.schemas.composition import CompositionCurrent, CompositionTrend, TrendPoint, TrendSummary
from modules.logic import run_triangulation
from modules.storage import load_garmin_data, load_measurements, load_profile

router = APIRouter(tags=["Composition"])


def _nan_to_none(v):
    if v is None:
        return None
    try:
        return None if math.isnan(float(v)) else round(float(v), 2)
    except (TypeError, ValueError):
        return None


def _build_processed(user_id: str) -> pd.DataFrame:
    garmin_df = load_garmin_data(user_id)
    if garmin_df is None or garmin_df.empty:
        raise ProblemDetailException(422, "Insufficient data", "No Garmin data imported yet")

    meas = load_measurements(user_id)
    navy_meas = meas[meas["Source"] == "Navy"][["Date", "Waist", "Neck", "Hip"]].copy()

    profile = load_profile(user_id)
    height = profile.get("height", 180)
    gender = profile.get("gender", "Man")

    try:
        processed = run_triangulation(garmin_df, navy_meas, height, gender)
    except Exception as e:
        raise ProblemDetailException(422, "Calculation error", str(e))

    if processed is None or processed.empty:
        raise ProblemDetailException(422, "Insufficient data", "Could not calculate composition")

    return processed


@router.get("/composition/current", response_model=CompositionCurrent)
def get_current(user_id: str = Depends(get_current_user)):
    processed = _build_processed(user_id)
    row = processed.iloc[-1]
    return CompositionCurrent(
        date=row["Date"].date(),
        consensus_fat_pct=_nan_to_none(row.get("Consensus_Fat_Pct")),
        garmin_fat_pct=_nan_to_none(row.get("fat_pct")),
        bias_offset_pct=_nan_to_none(row.get("Bias_Offset")),
        weight_kg=_nan_to_none(row.get("weight_kg")),
        lean_mass_kg=_nan_to_none(row.get("Lean_Mass_kg")),
        fat_mass_kg=_nan_to_none(row.get("Consensus_Fat_kg")),
    )


@router.get("/composition/trend", response_model=CompositionTrend)
def get_trend(
    user_id: str = Depends(get_current_user),
    days: Annotated[int, Query(ge=7, le=365)] = 30,
):
    processed = _build_processed(user_id)
    cutoff = pd.Timestamp.now() - pd.Timedelta(days=days)
    window = processed[processed["Date"] >= cutoff].copy()

    if window.empty:
        window = processed.tail(30)

    series = [
        TrendPoint(
            date=row["Date"].date(),
            consensus_fat_pct=_nan_to_none(row.get("Consensus_Fat_Pct")),
            weight_kg=_nan_to_none(row.get("weight_kg")),
            lean_mass_kg=_nan_to_none(row.get("Lean_Mass_kg")),
        )
        for _, row in window.iterrows()
    ]

    first, last = window.iloc[0], window.iloc[-1]
    summary = TrendSummary(
        fat_pct_change=_nan_to_none(
            (last.get("Consensus_Fat_Pct") or 0) - (first.get("Consensus_Fat_Pct") or 0)
        ),
        weight_change_kg=_nan_to_none(
            (last.get("weight_kg") or 0) - (first.get("weight_kg") or 0)
        ),
        lean_mass_change_kg=_nan_to_none(
            (last.get("Lean_Mass_kg") or 0) - (first.get("Lean_Mass_kg") or 0)
        ),
    )

    return CompositionTrend(period_days=days, series=series, summary=summary)
