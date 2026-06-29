import base64
import json
import os

from fastapi import Request

from api.errors import ProblemDetailException
from modules.auth_core import sanitize_user_id, check_allowed

# Claim types that may carry the user's email in an Azure Easy Auth principal blob.
_EMAIL_CLAIMS = (
    "emails",
    "preferred_username",
    "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
)


def _email_from_principal(header_val: str) -> str:
    """Decode the base64 JSON principal that Azure injects into the backend.

    Two shapes exist:
      - Static Web Apps (linked backend):  {"userDetails": "<email>", ...}
      - App Service Easy Auth:             {"claims": [{"typ": ..., "val": ...}]}
    """
    try:
        data = json.loads(base64.b64decode(header_val).decode("utf-8"))
    except Exception:
        return ""

    if data.get("userDetails"):
        return data["userDetails"]

    for claim in data.get("claims", []):
        if claim.get("typ") in _EMAIL_CLAIMS:
            return claim.get("val", "")
    return ""


def get_current_user(request: Request) -> str:
    """Resolve the caller's identity from platform-injected auth headers.

    Trust order — all of these are set by Azure in front of the app, never by
    the browser, so they cannot be spoofed by a remote caller:
      1. X-Ms-Client-Principal-Name  — App Service Easy Auth, plain email
      2. x-ms-client-principal       — base64 principal blob (SWA / Easy Auth)

    X-User-Email is browser-controlled and therefore only honoured in local
    development, gated behind TRUST_USER_EMAIL_HEADER=1.
    """
    raw = request.headers.get("X-Ms-Client-Principal-Name", "")

    if not raw:
        principal = request.headers.get("x-ms-client-principal", "")
        if principal:
            raw = _email_from_principal(principal)

    if not raw and os.environ.get("TRUST_USER_EMAIL_HEADER") == "1":
        raw = request.headers.get("X-User-Email", "")

    if not raw:
        raise ProblemDetailException(401, "Unauthorized", "No authenticated user")

    user = sanitize_user_id(raw)
    if not check_allowed(user):
        raise ProblemDetailException(403, "Forbidden", "This account is not authorized")
    return user
