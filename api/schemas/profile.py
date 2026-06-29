from typing import Literal
from pydantic import BaseModel, Field


class ProfileResponse(BaseModel):
    user_id: str
    height_cm: float
    # Lenient on read so legacy profiles (which may hold "Kvinna" from the
    # Streamlit app) never fail validation when fetched.
    gender: str


class ProfileUpdate(BaseModel):
    height_cm: float = Field(ge=100, le=250)
    # Strict on write; must match the values the frontend sends.
    gender: Literal["Man", "Woman"]
