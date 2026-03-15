"""
Connection pool wrapper for Supabase.
Manages client lifecycle and provides reusable instance.
"""

import os
from typing import Optional
from supabase import Client, create_client
from app.core.settings import settings

_pool_size = int(os.getenv("SUPABASE_POOL_SIZE", "5"))
_max_overflow = int(os.getenv("SUPABASE_MAX_OVERFLOW", "10"))


class PooledSupabaseClient:
    def __init__(self):
        self._client: Optional[Client] = None
        self._max_connections = _pool_size + _max_overflow

    def get_client(self) -> Client:
        if self._client is None:
            self._client = create_client(
                settings.supabase_url,
                settings.supabase_key,
                timeout=30.0,
            )
        return self._client

    def close(self):
        if self._client:
            self._client = None


supabase_pool = PooledSupabaseClient()
