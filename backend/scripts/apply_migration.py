#!/usr/bin/env python3
"""Apply database migrations to Supabase"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.supabase import _client
from app.core.settings import settings


async def apply_migration(sql_file: str) -> bool:
    """Execute a migration SQL file"""
    migration_path = Path(__file__).parent.parent / "app/db/migrations" / sql_file

    if not migration_path.exists():
        print(f"❌ Migration file not found: {migration_path}")
        return False

    sql = migration_path.read_text()
    print(f"📝 Applying {sql_file}...")
    print(f"SQL:\n{sql}\n")

    try:
        # Execute via Supabase RPC if available, otherwise print instructions
        result = _client.rpc('exec_sql', {'query': sql}).execute()
        print(f"✅ Migration applied successfully")
        return True
    except Exception as e:
        print(f"⚠️  Could not execute via RPC: {e}")
        print(f"\n📌 Manual Application Instructions:")
        print(f"1. Go to Supabase Dashboard: https://app.supabase.com")
        print(f"2. Select your project: {settings.supabase_url.split('/')[-1]}")
        print(f"3. Go to SQL Editor → New Query")
        print(f"4. Paste and run this SQL:")
        print(f"\n{sql}")
        return False


if __name__ == "__main__":
    migration_file = sys.argv[1] if len(sys.argv) > 1 else "002_add_infographics_column.sql"
    success = asyncio.run(apply_migration(migration_file))
    sys.exit(0 if success else 1)
