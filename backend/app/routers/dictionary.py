from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from app.core.supabase import supabase_manager
from datetime import datetime

router = APIRouter()

class TermBase(BaseModel):
    term: str
    definition: str
    tags: List[str] = []

class TermCreate(TermBase):
    pass

class TermResponse(TermBase):
    id: int
    created_at: str
    updated_at: Optional[str] = None
    popularity: int = 0

@router.get("/search", response_model=List[TermResponse])
async def search_terms(q: str):
    """
    Fast prefix/fuzzy search for terms.
    """
    if not q:
        return []

    if supabase_manager.is_connected:
        try:
            # Using 'terms' table. Assuming columns: id, term, definition, tags, created_at, popularity
            response = supabase_manager.client.table("terms") \
                .select("*") \
                .or_(f"term.ilike.%{q}%,definition.ilike.%{q}%") \
                .order("popularity", desc=True) \
                .limit(10) \
                .execute()
            return response.data
        except Exception as e:
            print(f"Supabase search error: {e}")
            return [] # Fail gracefully or use mock

    # Mock fallback for dev without DB connection
    return [
        {
            "id": 1,
            "term": "Catan",
            "definition": "A strategy board game where players collect resources...",
            "tags": ["strategy", "family"],
            "created_at": datetime.now().isoformat(),
            "popularity": 100
        },
        {
             "id": 2,
             "term": "Meeple",
             "definition": "A small figure used as a playing piece in certain board games.",
             "tags": ["component"],
             "created_at": datetime.now().isoformat(),
             "popularity": 50
        }
    ]

@router.get("/term/{term_slug}", response_model=TermResponse)
async def get_term(term_slug: str):
    if supabase_manager.is_connected:
        try:
            response = supabase_manager.client.table("terms") \
                .select("*") \
                .eq("term", term_slug) \
                .single() \
                .execute()
            if response.data:
                # Increment popularity async? For now sync is fine for minimal code
                supabase_manager.client.table("terms").update({"popularity": response.data['popularity'] + 1}).eq("id", response.data['id']).execute()
                return response.data
        except Exception:
            pass
    raise HTTPException(status_code=404, detail="Term not found")

@router.post("/term", response_model=TermResponse)
async def create_term(term: TermCreate):
    """
    Create or update a term.
    """
    data = term.dict()
    data["updated_at"] = datetime.now().isoformat()

    if supabase_manager.is_connected:
        try:
            # Upsert based on term
            response = supabase_manager.client.table("terms").upsert(data, on_conflict="term").execute()
            if response.data:
                return response.data[0]
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # Mock response
    return {
        "id": 999,
        **data,
        "created_at": datetime.now().isoformat(),
        "popularity": 0
    }
