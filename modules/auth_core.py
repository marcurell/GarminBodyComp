import os
import re


def sanitize_user_id(raw: str) -> str:
    """Normalize a Google email to a safe, stable blob path segment."""
    return re.sub(r"[^a-z0-9@._\-]", "_", raw.lower())


def check_allowed(user_id: str) -> bool:
    """Return False if ALLOWED_EMAILS is set and user_id is not in the list."""
    allowed_raw = os.environ.get("ALLOWED_EMAILS", "")
    if not allowed_raw:
        return True
    allowed = {e.strip().lower() for e in allowed_raw.split(",") if e.strip()}
    return user_id in allowed
