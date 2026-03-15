import asyncio
import json
import os
import sys
from datetime import UTC, datetime

from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from app.core import supabase
from app.models import GameDetail

load_dotenv()


async def import_game(file_path: str):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Ensure metadata
    data["updated_at"] = datetime.now(UTC).isoformat()
    if "data_version" not in data:
        data["data_version"] = 1

    # Validate with Pydantic (partial check as some fields come from Supabase)
    # Using model_validate with a dummy ID if missing
    if "id" not in data:
        data["id"] = "temporary-id"

    # Upsert logic
    print(f"Upserting game: {data['title']}...")

    # Filter out fields that might not exist in the DB schema yet
    # Based on error: end_game_confidence and end_game_summary missing
    safe_data = {
        k: v
        for k, v in data.items()
        if not k.endswith("_confidence") and not k.endswith("_summary") and k != "temporary-id"
    }
    # rules_summary is standard, keep it if it exists and we're sure
    # But for now, let's be extremely safe and only keep core fields
    core_fields = {
        "title", "title_ja", "title_en", "slug", "summary", "description",
        "rules_content", "structured_data", "min_players", "max_players",
        "play_time", "min_age", "published_year", "official_url", "bgg_url", "source_url"
    }
    safe_data = {k: v for k, v in safe_data.items() if k in core_fields}

    if "id" in data and data["id"] != "temporary-id":
        safe_data["id"] = data["id"]
    if "data_version" in data:
        safe_data["data_version"] = data["data_version"]
    if "updated_at" in data:
        safe_data["updated_at"] = data["updated_at"]

    result = await supabase.upsert(safe_data)
    if result:
        print(f"SUCCESS: Upserted {data['title']} (Slug: {data.get('slug')})")
    else:
        print(f"FAILED: Could not upsert {data['title']}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, help="Path to the game JSON file")
    args = parser.parse_args()

    asyncio.run(import_game(args.file))
