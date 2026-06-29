import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from api.errors import ProblemDetailException, problem_detail_handler
from api.routers import composition, garmin, measurements, profile

app = FastAPI(
    title="GarminBodyComp API",
    version="1.0.0",
    docs_url="/v1/docs",
    redoc_url="/v1/redoc",
    openapi_url="/v1/openapi.json",
)


@app.middleware("http")
async def strip_api_prefix(request: Request, call_next):
    """Normalise away a leading '/api' segment.

    When the Static Web App proxies '/api/v1/...' to this linked backend it may
    forward the '/api' prefix. Stripping it here lets the '/v1/...' routes match
    whether the request arrives via SWA ('/api/v1/me') or directly ('/v1/me').
    """
    path = request.scope["path"]
    if path == "/api" or path.startswith("/api/"):
        request.scope["path"] = path[len("/api"):] or "/"
    return await call_next(request)

_default_origins = "https://garminbodycomp.azurewebsites.net"
origins = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", _default_origins).split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(ProblemDetailException, problem_detail_handler)

app.include_router(profile.router, prefix="/v1")
app.include_router(composition.router, prefix="/v1")
app.include_router(measurements.router, prefix="/v1")
app.include_router(garmin.router, prefix="/v1")


@app.get("/health")
def health():
    return {"status": "ok"}
