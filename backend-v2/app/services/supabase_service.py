
from typing import List, Dict, Any, Optional
import structlog
from datetime import datetime
from app.core.supabase import supabase_client
from app.schemas.search import SearchResult, SearchFilters

logger = structlog.get_logger()


class SupabaseService:
    
    def __init__(self):
        self.client = supabase_client
    
    async def search_games_with_filters(
        self,
        query: str,
        filters: Optional[SearchFilters] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[SearchResult]:
        """Advanced game search with filters using Supabase"""
        try:
            if not self.client.initialized:
                logger.warning("Supabase not initialized, using fallback")
                return await self._fallback_search(query, limit)
            
            # Build query with filters
            supabase_query = self.client.client.table('games').select('*')
            
            # Text search
            if query:
                supabase_query = supabase_query.or_(
                    f'title.ilike.%{query}%,description.ilike.%{query}%,rules_content.ilike.%{query}%'
                )
            
            # Apply filters
            if filters:
                if filters.player_count_min:
                    supabase_query = supabase_query.gte('player_count_min', filters.player_count_min)
                if filters.player_count_max:
                    supabase_query = supabase_query.lte('player_count_max', filters.player_count_max)
                if filters.play_time_min:
                    supabase_query = supabase_query.gte('play_time_min', filters.play_time_min)
                if filters.play_time_max:
                    supabase_query = supabase_query.lte('play_time_max', filters.play_time_max)
                if filters.complexity_min:
                    supabase_query = supabase_query.gte('complexity', filters.complexity_min)
                if filters.complexity_max:
                    supabase_query = supabase_query.lte('complexity', filters.complexity_max)
                if filters.genres:
                    # Using PostgreSQL array contains operator
                    supabase_query = supabase_query.contains('genres', filters.genres)
                if filters.published_after:
                    supabase_query = supabase_query.gte('year_published', filters.published_after)
                if filters.published_before:
                    supabase_query = supabase_query.lte('year_published', filters.published_before)
            
            # Execute query
            response = supabase_query.range(offset, offset + limit - 1).execute()
            
            if not response.data:
                return []
            
            # Convert to SearchResult objects
            results = []
            for game in response.data:
                results.append(SearchResult(
                    game_id=game['id'],
                    title=game['title'],
                    description=game.get('description', ''),
                    content=game.get('rules_content', ''),
                    similarity_score=0.9,  # Default score for exact matches
                    player_count=f"{game.get('player_count_min', 1)}-{game.get('player_count_max', 8)}人",
                    play_time=f"{game.get('play_time_min', 30)}-{game.get('play_time_max', 90)}分",
                    complexity=game.get('complexity'),
                    genres=game.get('genres', []),
                    mechanics=game.get('mechanics', []),
                    year_published=game.get('year_published'),
                    rating=game.get('rating')
                ))
            
            logger.info("Supabase search completed", 
                       query=query, 
                       results_count=len(results))
            
            return results
            
        except Exception as e:
            logger.error("Supabase search failed", error=str(e))
            return await self._fallback_search(query, limit)
    
    async def _fallback_search(self, query: str, limit: int) -> List[SearchResult]:
        """Fallback search when Supabase is unavailable"""
        logger.info("Using fallback search")
        
        # Mock results for demonstration
        return [
            SearchResult(
                game_id=1,
                title="カタン",
                description="島の開拓と資源管理の戦略ゲーム",
                content="プレイヤーは開拓者となり、カタン島を開拓していきます...",
                similarity_score=0.95,
                player_count="3-4人",
                play_time="60-90分",
                complexity=2.5,
                genres=["戦略", "交渉", "資源管理"],
                mechanics=["ダイスロール", "交渉", "建設"],
                year_published=1995,
                rating=4.5
            )
        ][:limit]
    
    async def get_game_details(self, game_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed game information"""
        try:
            if not self.client.initialized:
                return None
            
            game = await self.client.get_game_by_id(game_id)
            return game
            
        except Exception as e:
            logger.error("Failed to get game details", game_id=game_id, error=str(e))
            return None
    
    async def store_game_rules(self, game_data: Dict[str, Any]) -> Optional[int]:
        """Store new game rules in Supabase"""
        try:
            if not self.client.initialized:
                return None
            
            # Add timestamps
            game_data['created_at'] = datetime.utcnow().isoformat()
            game_data['updated_at'] = datetime.utcnow().isoformat()
            
            result = await self.client.insert_game(game_data)
            return result['id'] if result else None
            
        except Exception as e:
            logger.error("Failed to store game rules", error=str(e))
            return None
    
    async def update_game_rules(self, game_id: int, updates: Dict[str, Any]) -> bool:
        """Update existing game rules"""
        try:
            if not self.client.initialized:
                return False
            
            updates['updated_at'] = datetime.utcnow().isoformat()
            result = await self.client.update_game(game_id, updates)
            return bool(result)
            
        except Exception as e:
            logger.error("Failed to update game rules", game_id=game_id, error=str(e))
            return False
    
    async def log_search_analytics(self, analytics_data: Dict[str, Any]) -> bool:
        """Log search analytics to Supabase"""
        try:
            if not self.client.initialized:
                return False
            
            analytics_data['created_at'] = datetime.utcnow().isoformat()
            result = await self.client.store_search_analytics(analytics_data)
            return result
            
        except Exception as e:
            logger.error("Failed to log search analytics", error=str(e))
            return False
    
    async def get_popular_games(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get popular games based on search frequency"""
        try:
            if not self.client.initialized:
                return []
            
            # Use Supabase RPC function for complex analytics query
            popular_games = await self.client.execute_rpc(
                'get_popular_games',
                {'limit_count': limit}
            )
            
            return popular_games or []
            
        except Exception as e:
            logger.error("Failed to get popular games", error=str(e))
            return []
    
    async def get_search_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """Get search suggestions from Supabase"""
        try:
            if not self.client.initialized:
                return []
            
            # Search for games with similar titles
            response = self.client.client.table('games').select('title').ilike('title', f'%{query}%').limit(limit).execute()
            
            if response.data:
                return [game['title'] for game in response.data]
            
            return []
            
        except Exception as e:
            logger.error("Failed to get search suggestions", error=str(e))
            return []
    
    async def create_user_favorite(self, user_id: str, game_id: int) -> bool:
        """Add game to user favorites"""
        try:
            if not self.client.initialized:
                return False
            
            favorite_data = {
                'user_id': user_id,
                'game_id': game_id,
                'created_at': datetime.utcnow().isoformat()
            }
            
            response = self.client.client.table('user_favorites').insert(favorite_data).execute()
            return bool(response.data)
            
        except Exception as e:
            logger.error("Failed to create user favorite", error=str(e))
            return False
    
    async def get_user_favorites(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's favorite games"""
        try:
            if not self.client.initialized:
                return []
            
            response = self.client.client.table('user_favorites').select(
                'game_id, games(id, title, description, rating)'
            ).eq('user_id', user_id).execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error("Failed to get user favorites", error=str(e))
            return []


# Global service instance
supabase_service = SupabaseService()