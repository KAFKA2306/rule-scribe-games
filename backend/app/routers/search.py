from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.supabase import supabase_repository
from app.services.gemini_client import GeminiClient
from app.utils.slugify import slugify
from app.models import SearchResult

router = APIRouter()
gemini_client = GeminiClient()


class SearchRequest(BaseModel):
    query: str
    generate: bool = True


@router.post("/search", response_model=List[SearchResult])
async def search_game(request: SearchRequest):
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # 1. Fast Path: Exact or Prefix Match
    fast_match = await supabase_repository.find_exact_or_prefix(query)
    if fast_match:
        # Increment view count asynchronously (fire and forget in this context)
        await supabase_repository.increment_view_count(fast_match.get("id"))
        
        return [
            SearchResult(
                id=str(fast_match.get("id", "0")),
                slug=fast_match.get("slug") or slugify(fast_match.get("title", "")),
                title=fast_match.get("title"),
                description=fast_match.get("description"),
                rules_content=fast_match.get("rules_content"),
                image_url=fast_match.get("image_url"),
                structured_data=fast_match.get("structured_data"),
                min_players=fast_match.get("min_players"),
                max_players=fast_match.get("max_players"),
                play_time=fast_match.get("play_time"),
                min_age=fast_match.get("min_age"),
                published_year=fast_match.get("published_year"),
                official_url=fast_match.get("official_url"),
                bgg_url=fast_match.get("bgg_url"),
            )
        ]

    # 2. Fuzzy Search (Fallback)
    existing_games = await supabase_repository.search(query)
    
    query_lower = query.lower().strip()
    exact_matches = []
    
    for game in existing_games:
        title = (game.get("title") or "").lower().strip()
        title_ja = (game.get("title_ja") or "").lower().strip()
        title_en = (game.get("title_en") or "").lower().strip()
        
        # If we found it here, it might be a fuzzy match that is "close enough" to be considered exact
        # But since we already did exact/prefix check, these are likely partial matches.
        # We'll return them if they are strong matches.
        if query_lower in [title, title_ja, title_en]:
             exact_matches.append(game)
    
    if exact_matches:
        results = []
        for game in exact_matches:
            # Increment view count for the first match (most relevant)
            if game == exact_matches[0]:
                 await supabase_repository.increment_view_count(game.get("id"))

            results.append(
                SearchResult(
                    id=str(game.get("id", "0")),
                    slug=game.get("slug") or slugify(game.get("title", "")),
                    title=game.get("title"),
                    description=game.get("description"),
                    rules_content=game.get("rules_content"),
                    image_url=game.get("image_url"),
                    structured_data=game.get("structured_data"),
                    min_players=game.get("min_players"),
                    max_players=game.get("max_players"),
                    play_time=game.get("play_time"),
                    min_age=game.get("min_age"),
                    published_year=game.get("published_year"),
                    official_url=game.get("official_url"),
                    bgg_url=game.get("bgg_url"),
                )
            )
        return results

    if not request.generate:
        return []

    print(f"Game not found in DB. Generating for: {query}")
    generated_data = await gemini_client.extract_game_info(query)

    if "error" in generated_data:
        raise HTTPException(status_code=500, detail=generated_data["error"])

    try:
        allowed_fields = {
            "title",
            "title_ja",
            "title_en",
            "description",
            "rules_content",
            "image_url",
            "min_players",
            "max_players",
            "play_time",
            "min_age",
            "published_year",
            "official_url",
            "bgg_url",
            "structured_data",
        }

        data_to_save = {k: v for k, v in generated_data.items() if k in allowed_fields}

        data_to_save["slug"] = slugify(
            data_to_save.get("title_en") or data_to_save.get("title", "unknown")
        )

        saved_games = await supabase_repository.upsert(data_to_save)
        if saved_games:
            game = saved_games[0]
            return [
                SearchResult(
                    id=str(game.get("id", "0")),
                    slug=game.get("slug"),
                    title=game.get("title"),
                    description=game.get("description"),
                    rules_content=game.get("rules_content"),
                    image_url=game.get("image_url"),
                    structured_data=game.get("structured_data"),
                    min_players=game.get("min_players"),
                    max_players=game.get("max_players"),
                    play_time=game.get("play_time"),
                    min_age=game.get("min_age"),
                    published_year=game.get("published_year"),
                    official_url=game.get("official_url"),
                    bgg_url=game.get("bgg_url"),
                )
            ]
    except Exception as e:
        print(f"Failed to save generated game: {e}")
        pass

    return [
        SearchResult(
            id="0", slug=slugify(generated_data.get("title", "unknown")), **generated_data
        )
    ]
