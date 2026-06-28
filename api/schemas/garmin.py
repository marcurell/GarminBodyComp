from datetime import date
from typing import Optional
from pydantic import BaseModel, EmailStr


class GarminConnectRequest(BaseModel):
    email: EmailStr
    password: str


class GarminStatusResponse(BaseModel):
    connected: bool
    last_sync_date: Optional[date]
    record_count: int


class GarminSyncResponse(BaseModel):
    new_records: int
    total_records: int
    synced_through: Optional[date]
