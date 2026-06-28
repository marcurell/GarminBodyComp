import pandas as pd
from fastapi import APIRouter, Depends

from api.dependencies import get_current_user
from api.errors import ProblemDetailException
from api.schemas.measurements import (
    MeasurementListResponse, MeasurementRequest, MeasurementResponse,
)
from modules.storage import load_measurements, save_measurements

router = APIRouter(tags=["Measurements"])


def _row_to_response(row) -> MeasurementResponse:
    def _f(v):
        import math
        try:
            return None if math.isnan(float(v)) else round(float(v), 2)
        except (TypeError, ValueError):
            return None

    return MeasurementResponse(
        date=pd.Timestamp(row["Date"]).date(),
        source=row["Source"],
        body_fat_pct=_f(row.get("BodyFatPct")),
        waist_cm=_f(row.get("Waist")),
        neck_cm=_f(row.get("Neck")),
        hip_cm=_f(row.get("Hip")),
    )


@router.get("/measurements", response_model=MeasurementListResponse)
def list_measurements(user_id: str = Depends(get_current_user)):
    df = load_measurements(user_id)
    rows = [_row_to_response(row) for _, row in df.sort_values("Date", ascending=False).iterrows()]
    return MeasurementListResponse(total=len(rows), measurements=rows)


@router.post("/measurements", response_model=MeasurementResponse, status_code=201)
def add_measurement(body: MeasurementRequest, user_id: str = Depends(get_current_user)):
    df = load_measurements(user_id)
    new_row = pd.DataFrame([{
        "Date":       pd.to_datetime(body.date),
        "Source":     body.source,
        "BodyFatPct": body.body_fat_pct if body.body_fat_pct is not None else float("nan"),
        "Waist":      body.waist_cm if body.waist_cm is not None else float("nan"),
        "Neck":       body.neck_cm if body.neck_cm is not None else float("nan"),
        "Hip":        body.hip_cm if body.hip_cm is not None else float("nan"),
    }])
    updated = (
        pd.concat([df, new_row])
        .drop_duplicates(subset=["Date", "Source"], keep="last")
        .sort_values("Date")
        .reset_index(drop=True)
    )
    save_measurements(user_id, updated)
    return _row_to_response(new_row.iloc[0])


@router.delete("/measurements/{date}/{source}", status_code=204)
def delete_measurement(date: str, source: str, user_id: str = Depends(get_current_user)):
    df = load_measurements(user_id)
    try:
        target_date = pd.to_datetime(date).normalize()
    except Exception:
        raise ProblemDetailException(400, "Invalid date", f"Cannot parse date: {date}")

    mask = (df["Date"].dt.normalize() == target_date) & (df["Source"] == source)
    if not mask.any():
        raise ProblemDetailException(
            404, "Not found",
            f"No {source} measurement for {date}",
            instance=f"/v1/measurements/{date}/{source}",
        )
    save_measurements(user_id, df[~mask].reset_index(drop=True))
