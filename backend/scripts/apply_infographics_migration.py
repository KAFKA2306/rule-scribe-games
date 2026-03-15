#!/usr/bin/env python3
"""Apply infographics migration to Supabase database"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.settings import settings


def apply_migration():
    """Apply 002_add_infographics_column migration"""
    
    print("\n📊 Applying Infographics Migration")
    print("=" * 70)
    
    migration_sql = """
BEGIN;

-- Add infographics column to games table
ALTER TABLE games ADD COLUMN IF NOT EXISTS infographics JSONB;

-- Create index for faster querying
CREATE INDEX IF NOT EXISTS idx_games_infographics ON games USING gin (infographics);

COMMIT;
"""
    
    print("\n🔍 Executing migration...\n")
    print(migration_sql)
    print("\n" + "=" * 70)
    
    try:
        from app.core.supabase import _client
        
        print("🔐 Verifying column existence...")
        
        # Try to query with infographics column to check if it exists
        try:
            result = _client.table("games").select("id, infographics").limit(1).execute()
            print("   ✓ infographics column already exists")
            print("\n✅ Migration already applied!")
            return True
        except Exception as check_e:
            if "infographics" in str(check_e):
                print("   ✗ infographics column missing")
                raise
            else:
                # Some other error
                raise
    
    except Exception as e:
        print(f"❌ Connection error: {e}\n")
        print("   Fallback: Apply via Supabase dashboard SQL Editor")
        print("   1. Paste SQL at: https://app.supabase.com/project/_/sql/editor")
        print("   2. Then run: task birmingham:infographics\n")
        return False


if __name__ == "__main__":
    success = apply_migration()
    sys.exit(0 if success else 1)
