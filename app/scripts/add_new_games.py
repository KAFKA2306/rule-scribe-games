import asyncio
import os
import sys
from time import sleep

from dotenv import load_dotenv

# Add the project root to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

from app.services.game_service import GameService
from app.core.supabase import _TABLE, _client

load_dotenv()

NEW_GAMES = [
    "ボルカルス",
    "ザ・クルー：第９惑星の探索",
    "たった今考えたプロポーズの言葉を君に捧ぐよ。 ：ラバーズピンク",
    "おばけ屋敷の宝石ハンター：不気味な地下室（拡張）",
    "もっと私の世界の見方",
    "ボブジテンきっず",
    "アズール：シントラのステンドグラス",
    "ソクラテスラ～キメラティック偉人バトル～",
    "プラネット・メーカー",
    "タイムライン：博識編",
    "ボブジテン",
    "キャッチ・ザ・ムーン",
    "テストプレイなんてしてないよ",
    "ダンジョンオブマンダム：エイト",
    "ゲスクラブ",
    "フォントかるた",
    "狂気山脈",
    "新・キング・オブ・トーキョー",
    "クイズいいセン行きまSHOW！恋愛編",
    "ギャンブラー×ギャンブル！",
    "狩歌 基本セット",
    "バウンス・オフ！",
    "パンデミック：クトゥルフの呼び声",
    "キングドミノ",
    "ロクジカ",
    "ナンジャモンジャ・ミドリ",
    "キョンシー",
    "コードネーム",
    "海底探険",
    "私の世界の見方",
    "ウボンゴ",
    "ブロックス",
    "ガイスター",
    "ラミィキューブ",
    "アトムモンスターズ / アトモン",
]

async def check_existing_games():
    """Fetches all existing game titles from the database."""
    # We fetch only id and title to check for existence
    response = _client.table(_TABLE).select("title").execute()
    existing_titles = {row["title"] for row in response.data}
    return existing_titles

async def main():
    service = GameService()
    existing_titles = await check_existing_games()
    
    print(f"DEBUG: Found {len(existing_titles)} existing games.")

    added_count = 0
    skipped_count = 0

    for game_title in NEW_GAMES:
        # Simple existence check (can be improved with fuzzy matching if needed)
        if game_title in existing_titles:
            print(f"SKIP: '{game_title}' already exists.")
            skipped_count += 1
            continue

        print(f"ADDING: '{game_title}'...")
        try:
            result = await service.create_game_from_query(game_title)
            if result:
                print(f"SUCCESS: Added '{game_title}' (ID: {result.get('id')})")
                added_count += 1
            else:
                print(f"FAILED: Could not add '{game_title}' (No result returned)")
            
            # Sleep to avoid rate limits and be nice to APIs
            await asyncio.sleep(10) 

        except Exception as e:
            print(f"ERROR: Failed to add '{game_title}': {e}")
            # Continue to next game even if one fails

    print("\n=== SUMMARY ===")
    print(f"Total Games Processed: {len(NEW_GAMES)}")
    print(f"Added: {added_count}")
    print(f"Skipped: {skipped_count}")

if __name__ == "__main__":
    asyncio.run(main())
