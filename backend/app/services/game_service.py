from typing import List, Dict, Any, Optional
from fastapi import HTTPException, BackgroundTasks
from app.core.supabase import supabase_repository
from app.services.research_agent import ResearchAgentService
from app.services.data_enhancer import DataEnhancer


class GameService:
    def __init__(self):
        self.repository = supabase_repository
        self.research_service = ResearchAgentService()
        self.enhancer = DataEnhancer()

    async def search_games(self, query: str) -> List[Dict[str, Any]]:
        return await self.repository.search(query)

    async def list_recent_games(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        return await self.repository.list_recent(limit=limit, offset=offset)

    async def get_game_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        game = await self.repository.get_by_slug(slug)
        if game:
             await self.repository.increment_view_count(game["id"])
        return game

    async def regenerate_game(self, slug: str, background_tasks: BackgroundTasks) -> Dict[str, Any]:
        game = await self.repository.get_by_slug(slug)
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        # Define the task to be run in background
        async def _regenerate_task():
            # Run research
            query = game.get("title")
            if not query:
                return

            # Run agent (this might be slow)
            result = self.research_service.run_research_task(query)
            if "error" in result:
                return

            # Merge result into existing game data
            result["id"] = game["id"]
            # Enforce original slug to prevent breaking URLs
            result["slug"] = slug

            await self.repository.upsert(result)

            # Post-process with data enhancer
            updated_game = await self.repository.get_by_id(game["id"])
            if updated_game and await self.enhancer.should_enhance(updated_game):
                final_data = await self.enhancer.enhance(updated_game)
                await self.repository.upsert(final_data)

        background_tasks.add_task(_regenerate_task)
        return {"status": "accepted", "message": "Regeneration task started"}
