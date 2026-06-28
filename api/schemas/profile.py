from typing import Literal
from pydantic import BaseModel, Field


class ProfileResponse(BaseModel):
    user_id: str
    height_cm: int
    gender: Literal["Man", "Kvinna"]


class ProfileUpdate(BaseModel):
    height_cm: int = Field(ge=100, le=250)
    gender: Literal["Man", "Kvinna"]
