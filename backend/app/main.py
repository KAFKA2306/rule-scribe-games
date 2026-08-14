from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.core.logger import setup_logging
from app.middleware.validation import ValidationMiddleware
from app.routers import auth, component_catalog_view, games, lists, presentation, vrchat
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
app.include_router(presentation.router, prefix="/api", tags=["presentation"])
app.include_router(component_catalog_view.router, prefix="/api", tags=["components"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(lists.router, prefix="/api", tags=["lists"])
app.include_router(vrchat.router, prefix="/api/vrchat/v1", tags=["vrchat"])


@app.get("/health")
@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


@app.get("/sitemap.xml")
async def sitemap_xml():
    content = await get_sitemap_xml()
    return Response(content=content, media_type="application/xml")


def game_not_found_html() -> str:
    return """<!doctype html>
<html lang="ja">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="robots" content="noindex, nofollow" />
    <title>ゲームが見つかりません | ボドゲのミカタ</title>
    <meta name="description" content="指定されたゲームは登録されていないか、URLが変更されています。" />
  </head>
  <body>
    <main style="max-width:42rem;margin:10vh auto;padding:2rem;font-family:system-ui,sans-serif;line-height:1.7">
      <p style="font-weight:700;letter-spacing:.08em">404 · GAME NOT FOUND</p>
      <h1>ゲームが見つかりません</h1>
      <p>指定されたゲームは登録されていないか、URLが変更されています。</p>
      <p><a href="/">ゲーム一覧へ戻る</a></p>
    </main>
  </body>
</html>"""


@app.get("/games/{slug}", response_class=HTMLResponse)
async def game_seo_page(slug: str):
    """Serve a crawlable game page with game-specific metadata and a real 404 boundary."""
    content = await generate_seo_html(slug)
    if content is None:
        return HTMLResponse(content=game_not_found_html(), status_code=404)
    return HTMLResponse(content=content)
