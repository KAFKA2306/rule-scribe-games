from fastapi import FastAPI
app = FastAPI()

@app.get("/api/health")
async def health():
    return {"status": "fastapi_ok"}
