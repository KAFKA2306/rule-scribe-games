from fastapi import FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.core.logger import setup_logging
from app.middleware.validation import ValidationMiddleware
from app.routers import auth, games, lists
from app.services.seo_renderer import generate_seo_html
from app.services.sitemap import get_sitemap_xml

setup_logging()
app = FastAPI(title="RuleScribe Minimal", version="1.0.0")

# Order matters: Validation before CORS so CORS is added "on top" and handles its own errors
app.add_middleware(ValidationMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(games.router, prefix="/api", tags=["games"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(lists.router, prefix="/api", tags=["lists"])


@app.get("/health")
@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


@app.get("/sitemap.xml")
async def sitemap_xml():
    content = await get_sitemap_xml()
    return Response(content=content, media_type="application/xml")


@app.get("/games/{slug}", response_class=HTMLResponse)
async def game_seo_page(slug: str):
    """Serve a crawlable game page with game-specific metadata and a real 404 boundary."""
    content = await generate_seo_html(slug)
    if content is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    return HTMLResponse(content=content)
