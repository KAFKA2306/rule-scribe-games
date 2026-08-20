from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.core.logger import setup_logging
from app.middleware.validation import ValidationMiddleware
from app.routers import auth, games, lists, mechanical_dna, presentation, vrchat
from app.services.search_visibility import should_return_gone
from app.services.seo_renderer import generate_seo_html
from app.services.sitemap import get_sitemap_xml

setup_logging()
app = FastAPI(title="RuleScribe Minimal", version="1.0.0")

PUBLIC_GAME_READ_CACHE = "public, max-age=0, s-maxage=60, must-revalidate"


def is_public_game_read_path(path: str) -> bool:
    if path == "/api/games":
        return True

    segments = [segment for segment in path.split("/") if segment]
    return len(segments) == 3 and segments[0] == "api" and segments[1] == "games" or (
        len(segments) == 2 and segments[0] == "games"
    )


@app.middleware("http")
async def cache_public_game_reads(request: Request, call_next):
    response = await call_next(request)
    if request.method == "GET" and response.status_code == 200 and is_public_game_read_path(request.url.path):
        response.headers["Cache-Control"] = PUBLIC_GAME_READ_CACHE
    return response


# Browser API access is same-origin in production. Explicit localhost origins are
# retained for Vite development; arbitrary third-party origins are denied.
app.add_middleware(ValidationMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://bodoge-no-mikata.vercel.app",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(games.router, prefix="/api", tags=["games"])
app.include_router(mechanical_dna.router, prefix="/api", tags=["connections"])
app.include_router(presentation.router, prefix="/api", tags=["presentation"])
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
      <h1>ゲームが見つかりません</h1>
      <p>指定されたゲームは登録されていないか、URLが変更されています。</p>
      <p><a href="/">ゲーム一覧へ戻る</a></p>
    </main>
  </body>
</html>"""


@app.get("/games/{slug}", response_class=HTMLResponse)
async def game_seo_page(slug: str):
    """Serve a crawlable game page with game-specific metadata and a real 404 boundary."""
    if should_return_gone(slug):
        return HTMLResponse(content=game_not_found_html(), status_code=410)
    content = await generate_seo_html(slug)
    if content is None:
        return HTMLResponse(content=game_not_found_html(), status_code=404)
    return HTMLResponse(content=content)
