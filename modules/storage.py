import os
import io
import logging
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
    return Fernet(key.encode())


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


# --- Garmin tokens (encrypted at rest) --------------------------------------

TOKEN_FILES = ["oauth1_token.json", "oauth2_token.json"]


def download_tokens(user_id: str, local_dir: str) -> bool:
    """Download and decrypt stored tokens to a local temp dir. Returns True if found."""
    os.makedirs(local_dir, mode=0o700, exist_ok=True)
    cipher = _get_cipher()
    found = False
    for fname in TOKEN_FILES:
        try:
            encrypted = _blob(user_id, f"garmin_tokens/{fname}").download_blob().readall()
            plaintext = cipher.decrypt(encrypted)
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
