from fastapi import FastAPI
app = FastAPI()

@app.get("/api/health")
async def health():
    return {"status": "infra_ok"}

@app.get("/health")
async def health_root():
    return {"status": "infra_ok"}
