import os
import sys

sys.path.append(os.getcwd())
try:
    from app.core import supabase
except ImportError:
    print("Error importing supabase client.")

TIER_UPDATES = {
    "ark-nova": "S",
    "terraforming-mars": "S",
    "scythe": "S",
    "istanbul": "A",
    "agricola": "A",
    "dominion": "A",
    "catan": "B",
    "splendor": "B",
    "azul": "B",
}


def update_strategy_tiers():
    print("Updating strategy_tier column for games...")
    for slug, tier in TIER_UPDATES.items():
        try:
            res = (
                supabase._client.table("games")
                .update({"strategy_tier": tier})
                .eq("slug", slug)
                .execute()
            )
            if res.data:
                print(f"✅ {slug} -> Tier {tier}")
            else:
                print(f"⚠️ {slug}: Not found or no update.")
        except Exception as e:
            print(f"❌ {slug}: {e}")


if __name__ == "__main__":
    update_strategy_tiers()
