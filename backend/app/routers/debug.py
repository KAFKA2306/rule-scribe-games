from fastapi import APIRouter, HTTPException
from app.core.settings import settings, PLACEHOLDER
from app.core.supabase import supabase_repository, SupabaseGameRepository

router = APIRouter()

@router.get("/debug/config")
def debug_config():
    """
    Checks presence of critical environment variables.
    Does NOT return actual values.
    """
    return {
        "supabase_url_set": settings.supabase_url != PLACEHOLDER,
        "supabase_key_set": settings.supabase_key != PLACEHOLDER,
        "gemini_api_key_set": settings.gemini_api_key != PLACEHOLDER,
        "model": settings.gemini_model,
        "repo_type": "Supabase" if isinstance(supabase_repository, SupabaseGameRepository) else "Noop/Mock"
    }

@router.get("/debug/db")
async def debug_db():
    """
    Attempts to fetch one row from the 'games' table to verify connection.
    """
    if not isinstance(supabase_repository, SupabaseGameRepository):
        raise HTTPException(status_code=500, detail="Repository is in Mock Mode. Check env vars.")

    try:
        # We access the client directly here for a raw check, or use a simple query
        # Since _repo encapsulates the client, we'll try a search or raw access if we modified the repo class.
        # But wait, supabase_repository has 'client' attribute exposed in my previous read of supabase.py?
        # Yes: self.client = client

        # Try a simple count or limit 1
        res = supabase_repository.client.table("games").select("count", count="exact").execute()

        # Also try to fetch one item
        sample = supabase_repository.client.table("games").select("*").limit(1).execute()

        return {
            "status": "connected",
            "count_result": res.count,
            "sample_data": sample.data
        }
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }
