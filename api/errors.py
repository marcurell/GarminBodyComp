from fastapi import Request
from fastapi.responses import JSONResponse


class ProblemDetailException(Exception):
    def __init__(self, status: int, title: str, detail: str, instance: str = None):
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
