#!/usr/bin/env python3
"""
Migration runner for infographics feature.
Applies database migration and uploads sample data.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.supabase import supabase
from app.core.settings import settings


SAMPLE_INFOGRAPHICS = {
    "splendor": {
        "turn_flow": "https://via.placeholder.com/800x600/FF6B6B/FFFFFF?text=Turn+Flow",
        "setup": "https://via.placeholder.com/800x600/4ECDC4/FFFFFF?text=Setup",
        "actions": "https://via.placeholder.com/800x600/45B7D1/FFFFFF?text=Actions",
        "winning": "https://via.placeholder.com/800x600/FFA07A/FFFFFF?text=Winning",
        "components": "https://via.placeholder.com/800x600/98D8C8/FFFFFF?text=Components",
    },
    "catan": {
        "setup": "https://via.placeholder.com/800x600/4ECDC4/FFFFFF?text=Catan+Setup",
        "actions": "https://via.placeholder.com/800x600/45B7D1/FFFFFF?text=Catan+Actions",
    },
}


async def check_migration():
    """Check if infographics column exists"""
    try:
        # Try to fetch a game and check if infographics field is accessible
        result = supabase.table("games").select("infographics").limit(1).execute()
        print("✓ Migration already applied - infographics column exists")
        return True
    except Exception as e:
        if "infographics" in str(e).lower():
            print("✗ Migration not applied - infographics column missing")
            print(f"\nRun this SQL in Supabase Dashboard → SQL Editor:")
            print("=" * 70)
            migration_sql = Path(__file__).parent.parent / "app/db/migrations/002_add_infographics_column.sql"
            print(migration_sql.read_text())
            print("=" * 70)
            return False
        raise


async def upload_sample_data():
    """Upload sample infographics for testing"""
    print("\n📤 Uploading sample infographics...")
    
    for slug, infographics in SAMPLE_INFOGRAPHICS.items():
        try:
            result = supabase.table("games").update(
                {"infographics": infographics}
            ).eq("slug", slug).execute()
            
            if result.data:
                print(f"✓ {slug}: {len(infographics)} infographics uploaded")
            else:
                print(f"✗ {slug}: Game not found or update failed")
        except Exception as e:
            print(f"✗ {slug}: Error - {e}")


async def verify_carousel():
    """Verify carousel display"""
    print("\n🎠 Verification checklist:")
    print("  1. Start dev servers: task dev")
    print("  2. Navigate to: http://localhost:5173/games/splendor")
    print("  3. Check 📊 図解 tab appears")
    print("  4. Test carousel navigation (← →, dot buttons)")
    print("  5. Counter should show '1 / 5' for splendor, '1 / 2' for catan")


async def main():
    print("🎨 Infographics Migration & Deployment")
    print("=" * 70)
    
    # Check migration
    migration_applied = await check_migration()
    if not migration_applied:
        print("\n❌ Please apply the migration first, then re-run this script.")
        return False
    
    # Upload sample data
    await upload_sample_data()
    
    # Verification steps
    await verify_carousel()
    
    print("\n✅ Infographics deployment ready!")
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
