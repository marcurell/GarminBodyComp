from garminconnect import Garmin
import pandas as pd
from datetime import date, datetime, timedelta, timezone
import os
import tempfile
import logging

from modules.storage import download_tokens, upload_tokens

logger = logging.getLogger(__name__)
TOKEN_SUBDIR = "garmin_tokens"

# Simple in-process rate limiter: max 5 Garmin login attempts per 5 minutes
_login_attempts: list = []


def _check_rate_limit() -> bool:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=5)
    _login_attempts[:] = [t for t in _login_attempts if t > cutoff]
    if len(_login_attempts) >= 5:
        return False
    _login_attempts.append(now)
    return True


def init_garmin_client(email: str, password: str, user_id: str):
    with tempfile.TemporaryDirectory() as tmp:
        token_path = os.path.join(tmp, TOKEN_SUBDIR)
        os.makedirs(token_path, mode=0o700, exist_ok=True)

        if download_tokens(user_id, token_path):
            try:
                garmin = Garmin()
                garmin.login(token_path)
                return garmin, None
            except Exception:
                logger.info("Stored tokens invalid, attempting fresh login")

        if not _check_rate_limit():
            return None, "För många inloggningsförsök. Försök igen om 5 minuter."

        try:
            garmin = Garmin(email, password)
            garmin.login()
        except Exception as e:
            return None, f"Inloggning misslyckades: {type(e).__name__}"

        try:
            garmin.garth.dump(token_path)
            upload_tokens(user_id, token_path)
        except Exception:
            logger.warning("Could not persist Garmin tokens")

        return garmin, None


def fetch_garmin_data(email: str, password: str, days_back: int = 30, user_id: str = ""):
    try:
        client, error = init_garmin_client(email, password, user_id)
        if not client:
            return None, error

        start_date = date.today() - timedelta(days=days_back)
        end_date = date.today()

        stats = client.get_body_composition(start_date.isoformat(), end_date.isoformat())

        data_rows = []
        if "dateWeightList" in stats:
            for entry in stats["dateWeightList"]:
                # Garmin sometimes reports mass in grams instead of kg; values
                # above a plausible ceiling for each metric are scaled back down.
                weight = float(entry.get("weight") or 0)
                if weight > 200:
                    weight /= 1000.0

                bone = float(entry.get("boneMass") or 0)
                if bone > 20:
                    bone /= 1000.0

                muscle = float(entry.get("muscleMass") or 0)
                if muscle > 100:
                    muscle /= 1000.0

                fat_pct = float(entry.get("bodyFat") or 0)
                water_pct = float(entry.get("bodyWater") or 0)

                raw_date = entry.get("date") or entry.get("startDate")
                if not raw_date or not weight:
                    continue
                try:
                    # Garmin returns ms-epoch integers, string-integers, or ISO date strings
                    if isinstance(raw_date, (int, float)):
                        parsed_date = pd.to_datetime(int(raw_date), unit="ms")
                    elif isinstance(raw_date, str) and raw_date.strip().lstrip("-").isdigit():
                        parsed_date = pd.to_datetime(int(raw_date), unit="ms")
                    else:
                        parsed_date = pd.to_datetime(raw_date, errors="coerce")
                    # Reject epoch artefacts (e.g. 1970) that slipped through.
                    if pd.isna(parsed_date) or parsed_date.year < 2000:
                        continue
                except Exception:
                    continue
                data_rows.append({
                    "Date": parsed_date,
                    "weight_kg": weight, "bone_kg": bone, "muscle_kg": muscle,
                    "fat_pct": fat_pct, "water_pct": water_pct,
                })

        df = pd.DataFrame(data_rows)
        if df.empty:
            return None, "Ingen data hittades för valt datumintervall."
        return df, None

    except Exception as e:
        logger.error("Garmin API call failed: %s", type(e).__name__)
        return None, "Fel vid hämtning från Garmin. Försök igen."
