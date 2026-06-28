import asyncio
from functools import partial
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from api.dependencies import get_current_user
from api.errors import ProblemDetailException
from api.schemas.garmin import GarminConnectRequest, GarminStatusResponse, GarminSyncResponse
from modules.data_handler import clean_and_map_columns
from modules.garmin_api import fetch_garmin_data
from modules.storage import (
    has_garmin_tokens, load_garmin_data, save_garmin_data,
)

router = APIRouter(tags=["Garmin"])


@router.get("/garmin/status", response_model=GarminStatusResponse)
def garmin_status(user_id: str = Depends(get_current_user)):
    connected = has_garmin_tokens(user_id)
    garmin_df = load_garmin_data(user_id)
    last_sync = None
    count = 0
    if garmin_df is not None and not garmin_df.empty:
        last_sync = garmin_df["Date"].max().date()
        count = len(garmin_df)
    return GarminStatusResponse(connected=connected, last_sync_date=last_sync, record_count=count)


@router.post("/garmin/connect")
async def garmin_connect(body: GarminConnectRequest, user_id: str = Depends(get_current_user)):
    loop = asyncio.get_event_loop()
    df_new, error = await loop.run_in_executor(
        None,
        partial(fetch_garmin_data, body.email, body.password, 90, user_id),
    )
    if error:
        raise ProblemDetailException(400, "Garmin authentication failed", error)
    cleaned = clean_and_map_columns(df_new)
    save_garmin_data(user_id, cleaned)
    return {"status": "connected", "message": f"Connected and imported {len(cleaned)} records"}


@router.post("/garmin/sync", response_model=GarminSyncResponse)
async def garmin_sync(
    user_id: str = Depends(get_current_user),
    days: Annotated[int, Query(ge=1, le=365)] = 30,
):
    if not has_garmin_tokens(user_id):
        raise ProblemDetailException(
            409, "Not connected",
            "Connect Garmin first via POST /v1/garmin/connect",
        )
    loop = asyncio.get_event_loop()
    df_new, error = await loop.run_in_executor(
        None,
        partial(fetch_garmin_data, "", "", days, user_id),
    )
    if error:
        raise ProblemDetailException(502, "Garmin sync failed", error)

    existing_count = 0
    existing_df = load_garmin_data(user_id)
    if existing_df is not None:
        existing_count = len(existing_df)

    cleaned = clean_and_map_columns(df_new)
    save_garmin_data(user_id, cleaned)

    updated_df = load_garmin_data(user_id)
    new_total = len(updated_df) if updated_df is not None else 0
    last_date = updated_df["Date"].max().date() if updated_df is not None and not updated_df.empty else None

    return GarminSyncResponse(
        new_records=max(0, new_total - existing_count),
        total_records=new_total,
        synced_through=last_date,
    )
