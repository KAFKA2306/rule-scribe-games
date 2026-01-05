import os
import sys
import asyncio

sys.path.append(os.getcwd())

try:
    from app.core import supabase
except ImportError:
    print("Error importing supabase client.")
    sys.exit(1)

# Logic: Update existing games based on 'slug'.
# Data gathered from deep research.

enrichment_data = [
    {
        "slug": "quick-shot",
        "title_en": "Quick Shot!",
        "title_ja": "クイックショット！",
        "min_players": 1,
        "max_players": 7,
        "play_time": 10,  # 5-10 mins
        "min_age": 8,  # Assumed standard for simple card games
        "published_year": 2019,  # Arclight page
        "bgg_url": "https://boardgamegeek.com/boardgame/292592/quick-shot",  # Confirmed
    },
    {
        "slug": "fixer",
        "title_en": "Fixer",
        "title_ja": "フィクサー",
        "min_players": 2,
        "max_players": 4,
        "play_time": 15,
        "min_age": 10,
        "published_year": 2017,
        "bgg_url": "https://boardgamegeek.com/boardgame/235882/fixer",
    },
    {
        "slug": "icefall",
        "title_en": "Icefall",
        "title_ja": "アイスフォール",
        "min_players": 3,
        "max_players": 5,
        "play_time": 40,  # 30-45
        "min_age": 10,
        "published_year": 2024,  # Sugorokuya 2025 spring presale, likely 2024/25
        "bgg_url": None,  # Too new?
    },
    {
        "slug": "3-second-try",
        "title_en": "3 Second Try!",
        "title_ja": "3秒トライ！",
        "min_players": 2,
        "max_players": 7,
        "play_time": 15,  # 10-15
        "min_age": 8,
        "published_year": 2019,
        "bgg_url": "https://boardgamegeek.com/boardgame/295679/3-second-try",
    },
    {
        "slug": "pictures",
        "title_en": "Pictures",
        "title_ja": "ピクチャーズ",
        "min_players": 3,
        "max_players": 5,
        "play_time": 30,  # 20-30
        "min_age": 8,
        "published_year": 2019,
        "bgg_url": "https://boardgamegeek.com/boardgame/284108/pictures",
    },
    {
        "slug": "detective-conan-karuta",
        "title_en": "Detective Conan Famous Lines Karuta",
        "title_ja": "名探偵コナン 名台詞かるた",
        "min_players": 3,  # Standard karuta usually 3+ (reader + 2 players)
        "max_players": 10,  # Arbitrary large number for karuta
        "play_time": 15,
        "min_age": 6,
        "published_year": 2016,  # Estimated from sales sites
        "bgg_url": None,
    },
    {
        "slug": "asahi-ecomuseum-karuta",
        "title_en": "Asahi Town Ecomuseum Karuta",
        "title_ja": "朝日町エコミュージアムかるた",
        "min_players": 3,
        "max_players": 10,
        "play_time": 20,
        "min_age": 6,
        "published_year": 2024,  # 70th anniv renewal
        "bgg_url": None,
    },
    {
        "slug": "mahjong-generic",
        "title_en": "Mahjong",
        "title_ja": "麻雀",
        "min_players": 3,
        "max_players": 4,  # Standard
        "play_time": 90,  # 60-120 usually
        "min_age": 8,  # Simplified rules
        "published_year": 1800,  # Traditional
        "bgg_url": "https://boardgamegeek.com/boardgame/2093/mahjong",
    },
    {
        "slug": "trapwords",
        "title_en": "Trapwords",
        "title_ja": "トラップワード",
        "min_players": 4,
        "max_players": 8,
        "play_time": 30,
        "min_age": 8,
        "published_year": 2018,
        "bgg_url": "https://boardgamegeek.com/boardgame/256606/trapwords",
    },
    {
        "slug": "just-one",
        "title_en": "Just One",
        "title_ja": "ジャストワン",
        "min_players": 3,
        "max_players": 7,
        "play_time": 20,
        "min_age": 8,
        "published_year": 2018,
        "bgg_url": "https://boardgamegeek.com/boardgame/254640/just-one",
    },
    {
        "slug": "kokushoujaku",
        "title_en": "Black Summon Mahjong (Kokushoujaku)",
        "title_ja": "黒召雀",
        "min_players": 2,
        "max_players": 4,
        "play_time": 20,  # 5-20
        "min_age": 6,
        "published_year": 2025,
        "bgg_url": None,
    },
    {
        "slug": "thats-not-a-hat",
        "title_en": "That's Not a Hat",
        "title_ja": "ザッツ・ノット・ア・ハット",
        "min_players": 3,
        "max_players": 8,
        "play_time": 15,
        "min_age": 8,
        "published_year": 2023,
        "bgg_url": "https://boardgamegeek.com/boardgame/375651/thats-not-a-hat",
    },
    {
        "slug": "secret-hitler",
        "title_en": "Secret Hitler",
        "title_ja": "シークレットヒトラー",
        "min_players": 5,
        "max_players": 10,
        "play_time": 45,  # Avg 45
        "min_age": 13,  # 13+ usually
        "published_year": 2016,
        "bgg_url": "https://boardgamegeek.com/boardgame/188834/secret-hitler",
    },
    {
        "slug": "sea-turtle-soup",
        "title_en": "Sea Turtle Soup (Lateral Thinking Puzzles)",
        "title_ja": "ウミガメのスープ",
        "min_players": 2,
        "max_players": 10,  # Any number
        "play_time": 20,
        "min_age": 10,
        "published_year": 2003,  # Book pub date approx
        "bgg_url": None,
    },
    {
        "slug": "raise-your-goblets",
        "title_en": "Raise Your Goblets",
        "title_ja": "ワインと毒とゴブレット",
        "min_players": 2,
        "max_players": 12,
        "play_time": 30,  # 20-45
        "min_age": 8,
        "published_year": 2016,
        "bgg_url": "https://boardgamegeek.com/boardgame/202684/raise-your-goblets",
    },
]


async def enrich_games():
    print(f"Enriching {len(enrichment_data)} games with full schema data...")

    for game in enrichment_data:
        try:
            print(f"Updating: {game['slug']}...")

            # Use Supabase client directly to update based on slug
            # Assuming 'slug' is a unique constraint or we can filter by it.
            # update() matches based on filter.

            payload = {
                "title_en": game["title_en"],
                "title_ja": game["title_ja"],
                "min_players": game["min_players"],
                "max_players": game["max_players"],
                "play_time": game["play_time"],
                "min_age": game["min_age"],
                "published_year": game["published_year"],
                "bgg_url": game["bgg_url"],
            }

            res = (
                supabase._client.table("games")
                .update(payload)
                .eq("slug", game["slug"])
                .execute()
            )

            if res.data:
                print(f"Successfully enriched: {game['title_en']}")
            else:
                print(f"Warning: No game found with slug '{game['slug']}'")

        except Exception as e:
            print(f"Failed to enrich {game['slug']}: {e}")


if __name__ == "__main__":
    asyncio.run(enrich_games())
