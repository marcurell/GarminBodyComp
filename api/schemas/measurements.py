from datetime import date
from typing import Literal, Optional
from pydantic import BaseModel, Field, model_validator


class MeasurementRequest(BaseModel):
    date: date
    source: Literal["Navy", "DEXA", "BodyPod"]
    waist_cm: Optional[float] = Field(None, ge=30, le=200)
    neck_cm: Optional[float] = Field(None, ge=10, le=100)
    hip_cm: Optional[float] = Field(None, ge=0, le=200)
    body_fat_pct: Optional[float] = Field(None, ge=1, le=60)

    @model_validator(mode="after")
    def check_fields_for_source(self):
        if self.source == "Navy":
            if self.waist_cm is None or self.neck_cm is None:
                raise ValueError("Navy measurements require waist_cm and neck_cm")
        else:
            if self.body_fat_pct is None:
                raise ValueError(f"{self.source} measurements require body_fat_pct")
        return self


class MeasurementResponse(BaseModel):
    date: date
    source: Literal["Navy", "DEXA", "BodyPod"]
    body_fat_pct: Optional[float]
    waist_cm: Optional[float]
    neck_cm: Optional[float]
    hip_cm: Optional[float]


class MeasurementListResponse(BaseModel):
    total: int
    measurements: list[MeasurementResponse]
