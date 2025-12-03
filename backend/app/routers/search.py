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

    existing_games = await supabase_repository.search(query)
    if existing_games:
        results = []
        for game in existing_games:
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
