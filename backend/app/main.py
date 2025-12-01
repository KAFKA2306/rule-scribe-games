from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import dictionary
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="RuleScribe Dictionary", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, lock this down
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# New simple dictionary router
app.include_router(dictionary.router, prefix="/api", tags=["dictionary"])

@app.get("/health")
def health_check():
    return {"status": "ok", "mode": "minimal-dictionary"}
