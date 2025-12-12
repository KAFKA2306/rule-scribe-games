from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from app.services.seo_renderer import generate_seo_html


from app.routers import games
from app.core.logger import setup_logging
from app.services.sitemap import get_sitemap_xml


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


@app.get("/games/{slug}")
def game_seo_page(slug: str):
    """
    Serve the game page with server-side injected SEO tags.
    """
    content = generate_seo_html(slug)
    return HTMLResponse(content=content)
