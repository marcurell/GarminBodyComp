from typing import Optional

from fastapi import Request
from fastapi.responses import JSONResponse


class ProblemDetailException(Exception):
    """Raised by routers to return an RFC 7807 'application/problem+json' error.

    status   HTTP status code (also echoed in the body)
    title    short, human-readable summary of the problem type
    detail   explanation specific to this occurrence
    instance optional URI/path identifying the specific occurrence
    """

    def __init__(self, status: int, title: str, detail: str, instance: Optional[str] = None):
        super().__init__(detail)
        self.status = status
        self.title = title
        self.detail = detail
        self.instance = instance


async def problem_detail_handler(request: Request, exc: ProblemDetailException):
    body = {
        "type": f"https://garminbodycomp.azurewebsites.net/problems/{exc.status}",
        "title": exc.title,
        "status": exc.status,
        "detail": exc.detail,
    }
    if exc.instance:
        body["instance"] = exc.instance
    return JSONResponse(status_code=exc.status, content=body,
                        media_type="application/problem+json")
