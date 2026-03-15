import asyncio

from app.core import supabase

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


async def check_games():
    for game in GAMES:
        results = await supabase.search(game)
        exists = any(r["title"].lower() == game.lower() or r.get("title_ja") == game for r in results)
        status = "EXISTS" if exists else "MISSING"
        print(f"{game}: {status}")


if __name__ == "__main__":
    asyncio.run(check_games())
