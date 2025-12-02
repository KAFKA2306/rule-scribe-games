from app.core.setup import apply_initial_setup

apply_initial_setup()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import search, debug, games

app = FastAPI(title="RuleScribe Minimal", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # relax origin but keep credentials off to avoid startup error
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router, prefix="/api", tags=["search"])
app.include_router(games.router, prefix="/api", tags=["games"])
app.include_router(debug.router, prefix="/api", tags=["debug"])


@app.get("/health")
@app.get("/api/health")
def health_check():
    return {"status": "ok"}
