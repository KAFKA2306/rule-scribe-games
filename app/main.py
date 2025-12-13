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


@app.get("/api/debug_simple")
def debug_simple():
    return {"message": "Hello from updated deployment"}


@app.get("/api/debug_gemini")
async def debug_gemini():
    import os
    import traceback
    from app.core.settings import settings
    from app.core.gemini import GeminiClient
    
    env_key = os.getenv("GEMINI_API_KEY")
    masked_key = f"{env_key[:4]}...{env_key[-4:]}" if env_key else "None"
    
    try:
        client = GeminiClient()
        # Simple prompt asking for JSON
        prompt = "Return a JSON object with a key 'greeting' and value 'hello'."
        result = await client.generate_structured_json(prompt)
        
        return {
            "status": "success",
            "env_key_masked": masked_key,
            "settings_key_masked": f"{settings.gemini_api_key[:4]}..." if settings.gemini_api_key else "None",
            "model": settings.gemini_model,
            "result": result
        }
    except Exception as e:
        return {
            "status": "error",
            "env_key_masked": masked_key,
            "model": settings.gemini_model,
            "error": str(e),
            "traceback": traceback.format_exc()
        }


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
