import asyncio
import logging

from app.core import supabase
from app.services.game_service import GameService

# ロガーの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GAMES = [
    "もっとホイップを",
    "ティーフェンタール",
    "マインドスペース",
    "ブラスバーミンガム",
    "ひらがじゃん",
    "スプレンティア",
    "ボムバスターズ",
    "オチカルタ",
    "ビックショット",
    "スウィートランド",
    "ウォルフズ",
    "デソリト",
    "スチームパワー",
    "エスノス",
    "ビーントゥーバー",
    "リベルタリア",
]


async def batch_add():
    service = GameService()
    for game in GAMES:
        try:
            # 既に追加されているかチェック
            results = await supabase.search(game)
            if any(r["title"].lower() == game.lower() or r.get("title_ja") == game for r in results):
                print(f"Skipping already added game: {game}")
                continue

            print(f"Adding game: {game}...")
            result = await service.create_game_from_query(game)
            if result:
                print(f"Successfully added: {result.get('title')} ({result.get('slug')})")
            else:
                print(f"Failed to add: {game}")
        except Exception as e:
            print(f"Error adding {game}: {e}")
            logger.error(f"Error adding {game}: {e}")


if __name__ == "__main__":
    asyncio.run(batch_add())
