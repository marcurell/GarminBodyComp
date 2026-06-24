import os
import io
import pandas as pd
from azure.storage.blob import BlobServiceClient

# ---------------------------------------------------------------------------
# Storage abstraction layer
#
# All paths are prefixed with user_id so the structure is ready for
# multi-user expansion. Adding a new user only requires a new user_id.
#
# Blob layout:
#   userdata/{user_id}/measurements.csv
#   userdata/{user_id}/garmin_tokens/oauth1_token.json
#   userdata/{user_id}/garmin_tokens/oauth2_token.json
# ---------------------------------------------------------------------------

CONTAINER = "userdata"
_client: BlobServiceClient | None = None


def _get_client() -> BlobServiceClient:
    global _client
    if _client is None:
        conn_str = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
        if not conn_str:
            raise RuntimeError("AZURE_STORAGE_CONNECTION_STRING not set")
        _client = BlobServiceClient.from_connection_string(conn_str)
    return _client


def _blob(user_id: str, path: str):
    return _get_client().get_blob_client(container=CONTAINER, blob=f"{user_id}/{path}")


# --- Measurements -----------------------------------------------------------

def load_measurements(user_id: str) -> pd.DataFrame:
    empty = pd.DataFrame(columns=["Date", "Waist", "Neck", "Hip"])
    try:
        data = _blob(user_id, "measurements.csv").download_blob().readall()
        df = pd.read_csv(io.BytesIO(data))
        df["Date"] = pd.to_datetime(df["Date"])
        for col in ["Waist", "Neck", "Hip"]:
            if col not in df.columns:
                df[col] = 0
        return df
    except Exception:
        return empty


def save_measurements(user_id: str, df: pd.DataFrame) -> None:
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    _blob(user_id, "measurements.csv").upload_blob(buf, overwrite=True)


# --- Garmin tokens ----------------------------------------------------------

TOKEN_FILES = ["oauth1_token.json", "oauth2_token.json"]


def download_tokens(user_id: str, local_dir: str) -> bool:
    """Download stored tokens to a local temp dir. Returns True if found."""
    os.makedirs(local_dir, exist_ok=True)
    found = False
    for fname in TOKEN_FILES:
        try:
            data = _blob(user_id, f"garmin_tokens/{fname}").download_blob().readall()
            with open(os.path.join(local_dir, fname), "wb") as f:
                f.write(data)
            found = True
        except Exception:
            pass
    return found


def upload_tokens(user_id: str, local_dir: str) -> None:
    """Upload local token files to blob storage."""
    for fname in TOKEN_FILES:
        path = os.path.join(local_dir, fname)
        if os.path.exists(path):
            with open(path, "rb") as f:
                _blob(user_id, f"garmin_tokens/{fname}").upload_blob(f, overwrite=True)


# --- Garmin body composition data -------------------------------------------

def save_garmin_data(user_id: str, df: pd.DataFrame) -> None:
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
