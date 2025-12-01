from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import search, summarize
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="RuleScribe Minimal", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router, prefix="/api", tags=["search"])
app.include_router(summarize.router, prefix="/api", tags=["summarize"])

@app.get("/health")
def health_check(): return {"status": "ok"}
