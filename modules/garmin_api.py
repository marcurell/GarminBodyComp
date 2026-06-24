from garminconnect import Garmin
import pandas as pd
from datetime import date, timedelta
import os
import tempfile

from modules.storage import download_tokens, upload_tokens

TOKEN_SUBDIR = "garmin_tokens"


def init_garmin_client(email: str, password: str, user_id: str = "lars"):
    with tempfile.TemporaryDirectory() as tmp:
        token_path = os.path.join(tmp, TOKEN_SUBDIR)
        os.makedirs(token_path, exist_ok=True)

        # Try saved tokens from blob storage first
        if download_tokens(user_id, token_path):
            try:
                garmin = Garmin()
                garmin.login(token_path)
                return garmin, None
            except Exception as e:
                print(f"Token-fel, försöker logga in manuellt: {e}")

        # Fresh login
        garmin = Garmin(email, password)
        garmin.login()

        # Persist tokens back to blob storage
        try:
            garmin.garth.dump(token_path)
            upload_tokens(user_id, token_path)
        except Exception as e:
            print(f"Kunde inte spara tokens: {e}")

        return garmin, None


def fetch_garmin_data(email: str, password: str, days_back: int = 30, user_id: str = "lars"):
    try:
        client, error = init_garmin_client(email, password, user_id)
        if not client:
            return None, f"Login Error: {error}"

        start_date = date.today() - timedelta(days=days_back)
        end_date = date.today()

        stats = client.get_body_composition(start_date.isoformat(), end_date.isoformat())

        data_rows = []
        if "dateWeightList" in stats:
            for entry in stats["dateWeightList"]:
                w = entry.get("weight") or 0.0
                w = float(w)
                if w > 200: w /= 1000.0

                b = entry.get("boneMass") or 0.0
                b = float(b)
                if b > 20: b /= 1000.0

                m = entry.get("muscleMass") or 0.0
                m = float(m)
                if m > 100: m /= 1000.0

                f = float(entry.get("bodyFat") or 0.0)
                wa = float(entry.get("bodyWater") or 0.0)

                if w > 0:
                    data_rows.append({
                        "Date": pd.to_datetime(entry.get("date") or entry.get("startDate")),
                        "weight_kg": w,
                        "bone_kg": b,
                        "muscle_kg": m,
                        "fat_pct": f,
                        "water_pct": wa,
                    })

        df = pd.DataFrame(data_rows)
        if df.empty:
            return None, "Ingen data hittades."
        return df, None

    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"API Error: {str(e)}"
