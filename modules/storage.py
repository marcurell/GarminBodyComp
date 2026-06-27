import io
import json
import logging
import os

import pandas as pd
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from cryptography.fernet import Fernet

# ---------------------------------------------------------------------------
# Storage abstraction layer
#
# Uses Managed Identity (DefaultAzureCredential) — no connection string or
# storage key needed. The App Service's system-assigned identity is granted
# Storage Blob Data Contributor via Bicep.
#
# Blob layout:
#   userdata/{user_id}/measurements.csv
#   userdata/{user_id}/garmin_data.csv
#   userdata/{user_id}/garmin_tokens/oauth1_token.json   (Fernet-encrypted)
#   userdata/{user_id}/garmin_tokens/oauth2_token.json   (Fernet-encrypted)
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

CONTAINER = "userdata"
_client: BlobServiceClient | None = None


def _get_client() -> BlobServiceClient:
    global _client
    if _client is None:
        account_name = os.environ.get("AZURE_STORAGE_ACCOUNT_NAME")
        if not account_name:
            raise RuntimeError("AZURE_STORAGE_ACCOUNT_NAME environment variable is not set")
        _client = BlobServiceClient(
            account_url=f"https://{account_name}.blob.core.windows.net",
            credential=DefaultAzureCredential(),
        )
    return _client


def _get_cipher() -> Fernet:
    key = os.environ.get("TOKEN_ENCRYPTION_KEY")
    if not key:
        raise RuntimeError("TOKEN_ENCRYPTION_KEY environment variable is not set")
    # Restore base64 padding if it was stripped during key generation
    padding = 4 - len(key) % 4
    if padding != 4:
        key = key + "=" * padding
    return Fernet(key.encode())


def _blob(user_id: str, path: str):
    return _get_client().get_blob_client(container=CONTAINER, blob=f"{user_id}/{path}")


# --- Measurements -----------------------------------------------------------
# Schema: Date, Source ("Navy"|"DEXA"|"BodyPod"), BodyFatPct, Waist, Neck, Hip
# Navy rows: Waist/Neck/Hip filled; BodyFatPct is calculated by logic.py
# DEXA/BodyPod rows: BodyFatPct filled; Waist/Neck/Hip are NaN

_MEAS_COLS = ["Date", "Source", "BodyFatPct", "Waist", "Neck", "Hip"]


def load_measurements(user_id: str) -> pd.DataFrame:
    empty = pd.DataFrame(columns=_MEAS_COLS)
    try:
        data = _blob(user_id, "measurements.csv").download_blob().readall()
        df = pd.read_csv(io.BytesIO(data))
        df["Date"] = pd.to_datetime(df["Date"])
        # Backward compat: old schema had no Source/BodyFatPct columns
        if "Source" not in df.columns:
            df["Source"] = "Navy"
        if "BodyFatPct" not in df.columns:
            df["BodyFatPct"] = float("nan")
        for col in ["Waist", "Neck", "Hip"]:
            if col not in df.columns:
                df[col] = float("nan")
        return df[_MEAS_COLS].sort_values("Date").reset_index(drop=True)
    except Exception:
        return empty


def save_measurements(user_id: str, df: pd.DataFrame) -> None:
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    _blob(user_id, "measurements.csv").upload_blob(buf, overwrite=True)


# --- Garmin body composition data -------------------------------------------

def save_garmin_data(user_id: str, df: pd.DataFrame) -> None:
    """Merge new data with existing, keeping latest record per date."""
    existing = load_garmin_data(user_id)
    if existing is not None and not existing.empty:
        combined = (
            pd.concat([existing, df])
            .drop_duplicates(subset="Date", keep="last")
            .sort_values("Date")
            .reset_index(drop=True)
        )
    else:
        combined = df.sort_values("Date").reset_index(drop=True)
    buf = io.BytesIO()
    combined.to_csv(buf, index=False)
    buf.seek(0)
    _blob(user_id, "garmin_data.csv").upload_blob(buf, overwrite=True)


def delete_garmin_rows(user_id: str, dates: list) -> None:
    """Remove specific dates from garmin_data.csv."""
    df = load_garmin_data(user_id)
    if df is None or df.empty:
        return
    date_set = set(pd.to_datetime(dates).normalize())
    df = df[~df["Date"].dt.normalize().isin(date_set)]
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    _blob(user_id, "garmin_data.csv").upload_blob(buf, overwrite=True)


def load_garmin_data(user_id: str) -> pd.DataFrame | None:
    try:
        data = _blob(user_id, "garmin_data.csv").download_blob().readall()
        df = pd.read_csv(io.BytesIO(data))
        df["Date"] = pd.to_datetime(df["Date"])
        return df
    except Exception:
        return None


# --- User profile (height, gender) -----------------------------------------

def load_profile(user_id: str) -> dict:
    try:
        data = _blob(user_id, "profile.json").download_blob().readall()
        return json.loads(data)
    except Exception:
        return {}


def save_profile(user_id: str, profile: dict) -> None:
    buf = io.BytesIO(json.dumps(profile).encode())
    _blob(user_id, "profile.json").upload_blob(buf, overwrite=True)


# --- Garmin tokens (encrypted at rest) --------------------------------------

TOKEN_FILES = ["oauth1_token.json", "oauth2_token.json"]


def download_tokens(user_id: str, local_dir: str) -> bool:
    """Download and decrypt stored tokens to a local temp dir. Returns True if found."""
    os.makedirs(local_dir, mode=0o700, exist_ok=True)
    cipher = _get_cipher()
    found = False
    for fname in TOKEN_FILES:
        try:
            data = _blob(user_id, f"garmin_tokens/{fname}").download_blob().readall()
            try:
                plaintext = cipher.decrypt(data)
            except Exception:
                # Token was stored unencrypted (before encryption was introduced).
                # Treat as a cache miss so the app falls through to fresh login,
                # which will re-upload with encryption.
                logger.info("Token %s not decryptable, will re-authenticate", fname)
                return False
            with open(os.path.join(local_dir, fname), "wb") as f:
                f.write(plaintext)
            found = True
        except Exception:
            pass
    return found


def upload_tokens(user_id: str, local_dir: str) -> None:
    """Encrypt and upload local token files to blob storage."""
    cipher = _get_cipher()
    for fname in TOKEN_FILES:
        path = os.path.join(local_dir, fname)
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    plaintext = f.read()
                encrypted = cipher.encrypt(plaintext)
                _blob(user_id, f"garmin_tokens/{fname}").upload_blob(
                    io.BytesIO(encrypted), overwrite=True
                )
            except Exception:
                logger.warning("Failed to persist OAuth token to storage")
