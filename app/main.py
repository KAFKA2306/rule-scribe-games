from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx


from app.routers import games
from app.core.logger import setup_logging
from app.services.sitemap import get_sitemap_xml
from fastapi import Response


setup_logging()

app = FastAPI(title="RuleScribe Minimal", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(games.router, prefix="/api", tags=["games"])


@app.get("/health")
@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.get("/sitemap.xml")
def sitemap_xml():
    content = get_sitemap_xml()
    return Response(content=content, media_type="application/xml")


@app.exception_handler(httpx.HTTPStatusError)
async def httpx_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.response.status_code,
        content={"detail": f"Upstream AI Error: {exc.response.text}"},
    )
