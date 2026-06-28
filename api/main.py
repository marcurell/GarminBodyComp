from fastapi import FastAPI
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://garminbodycomp.azurewebsites.net"],
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
