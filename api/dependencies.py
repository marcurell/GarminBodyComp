from fastapi import Request
from modules.auth_core import sanitize_user_id, check_allowed
from api.errors import ProblemDetailException


def get_current_user(request: Request) -> str:
    raw = request.headers.get("X-Ms-Client-Principal-Name", "")
    if not raw:
        raise ProblemDetailException(401, "Unauthorized", "No authenticated user")
    user = sanitize_user_id(raw)
    if not check_allowed(user):
        raise ProblemDetailException(403, "Forbidden", "This account is not authorized")
    return user
