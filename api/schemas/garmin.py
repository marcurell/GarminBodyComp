from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class GarminConnectRequest(BaseModel):
    # Plain str rather than EmailStr to avoid the email-validator dependency.
    # The address is only forwarded to Garmin's login, which is the real
    # authority on whether it is valid.
    email: str = Field(min_length=3)
    password: str = Field(min_length=1)


class GarminStatusResponse(BaseModel):
    connected: bool
    last_sync_date: Optional[date]
    record_count: int


class GarminSyncResponse(BaseModel):
    new_records: int
    total_records: int
    synced_through: Optional[date]
