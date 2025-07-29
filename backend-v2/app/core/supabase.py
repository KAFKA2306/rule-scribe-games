"""
Supabase integration for RuleScribe v2
"""

from supabase import create_client, Client
from typing import Optional, Dict, Any, List
import structlog
from app.core.config import settings

logger = structlog.get_logger()


class SupabaseClient:
    """Enhanced Supabase client with advanced features"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.initialized = False
    
    async def initialize(self) -> bool:
        """Initialize Supabase client"""
        try:
            if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
                logger.warning("Supabase credentials not provided")
                return False
            
            self.client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_ANON_KEY
            )
            
            # Test connection
            response = self.client.table('games').select('count').limit(1).execute()
            if response:
                self.initialized = True
                logger.info("Supabase client initialized successfully")
                return True
            
        except Exception as e:
            logger.error("Failed to initialize Supabase client", error=str(e))
            return False
    
    async def get_games(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """Get games from Supabase"""
        try:
            if not self.initialized:
                return []
            
            response = self.client.table('games').select('*').range(offset, offset + limit - 1).execute()
            return response.data if response.data else []
            
        except Exception as e:
            logger.error("Failed to get games from Supabase", error=str(e))
            return []
    
    async def search_games(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search games using Supabase text search"""
        try:
            if not self.initialized:
                return []
            
            # Full-text search on title and description
            response = self.client.table('games').select('*').or_(
                f'title.ilike.%{query}%,description.ilike.%{query}%'
            ).limit(limit).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error("Failed to search games in Supabase", error=str(e))
            return []
    
    async def get_game_by_id(self, game_id: int) -> Optional[Dict[str, Any]]:
        """Get specific game by ID"""
        try:
            if not self.initialized:
                return None
            
            response = self.client.table('games').select('*').eq('id', game_id).single().execute()
            return response.data if response.data else None
            
        except Exception as e:
            logger.error("Failed to get game by ID", game_id=game_id, error=str(e))
            return None
    
    async def insert_game(self, game_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Insert new game into Supabase"""
        try:
            if not self.initialized:
                return None
            
            response = self.client.table('games').insert(game_data).execute()
            return response.data[0] if response.data else None
            
        except Exception as e:
            logger.error("Failed to insert game", error=str(e))
            return None
    
    async def update_game(self, game_id: int, game_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update existing game in Supabase"""
        try:
            if not self.initialized:
                return None
            
            response = self.client.table('games').update(game_data).eq('id', game_id).execute()
            return response.data[0] if response.data else None
            
        except Exception as e:
            logger.error("Failed to update game", game_id=game_id, error=str(e))
            return None
    
    async def store_search_analytics(self, analytics_data: Dict[str, Any]) -> bool:
        """Store search analytics in Supabase"""
        try:
            if not self.initialized:
                return False
            
            response = self.client.table('search_analytics').insert(analytics_data).execute()
            return bool(response.data)
            
        except Exception as e:
            logger.error("Failed to store search analytics", error=str(e))
            return False
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile from Supabase Auth"""
        try:
            if not self.initialized:
                return None
            
            user = self.client.auth.get_user()
            return user.user.model_dump() if user.user else None
            
        except Exception as e:
            logger.error("Failed to get user profile", user_id=user_id, error=str(e))
            return None
    
    async def create_user_session(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Create user session with Supabase Auth"""
        try:
            if not self.initialized:
                return None
            
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            return response.session.model_dump() if response.session else None
            
        except Exception as e:
            logger.error("Failed to create user session", error=str(e))
            return None
    
    async def execute_rpc(self, function_name: str, params: Dict[str, Any] = None) -> Any:
        """Execute Supabase Edge Function or RPC"""
        try:
            if not self.initialized:
                return None
            
            response = self.client.rpc(function_name, params or {}).execute()
            return response.data
            
        except Exception as e:
            logger.error("Failed to execute RPC", function=function_name, error=str(e))
            return None


# Global Supabase client instance
supabase_client = SupabaseClient()