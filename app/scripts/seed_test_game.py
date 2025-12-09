import asyncio
from app.core import supabase


async def main():
    game = {
        "slug": "test-edit-game",
        "title": "Test Edit Game",
        "title_ja": "テスト編集ゲーム",
        "summary": "Original Summary",
        "rules_content": "Original Rules",
        "description": "Original Description",
    }
    # upsert returns a list of inserted rows
    res = await supabase.upsert(game)
    print(f"Seeded: {res}")


if __name__ == "__main__":
    asyncio.run(main())
