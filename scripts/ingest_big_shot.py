import asyncio
import os
import sys

# Ensure backend directory is in path for app imports
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.core.supabase import upsert

async def run():
    rules_path = "big_shot_rules.txt"
    if not os.path.exists(rules_path):
        print(f"✗ Rules file {rules_path} not found.")
        return

    with open(rules_path, "r", encoding="utf-8") as f:
        rules_content = f.read()

    data = {
        "slug": "big-shot",
        "title": "Big Shot",
        "title_ja": "ビッグショット",
        "min_players": 2,
        "max_players": 4,
        "play_time": 45,
        "min_age": 10,
        "summary": "土地を競り落とし、キューブを配置してエリアマジョリティを競う不動産投資ゲーム。「引き分け相殺」ルールによる独特な駆け引きが特徴。",
        "rules_content": rules_content
    }
    
    print(f"🚀 Ingesting {data['slug']}...")
    res = await upsert(data)
    if res:
        print(f"✓ Successfully ingested {data['slug']}.")
    else:
        print(f"✗ Failed to ingest {data['slug']}.")

if __name__ == "__main__":
    asyncio.run(run())
