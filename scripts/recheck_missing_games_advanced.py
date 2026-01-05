import os
import sys
import asyncio

sys.path.append(os.getcwd())

try:
    from app.core import supabase
except ImportError:
    print("Error importing supabase client.")
    sys.exit(1)

# Mapping of "Original Input Name" -> List of variations to check
games_to_check = {
    "クイックショット": ["クイックショット", "Quick Shot", "Quick Shot!"],
    "フィクサー": ["フィクサー", "Fixer"],
    "アイスフォール": ["アイスフォール", "Icefall"],
    "ヒットスター": ["ヒットスター", "Hitster"],
    "フォックスインザフォレスト": [
        "フォックスインザフォレスト",
        "The Fox in the Forest",
        "Fox in the Forest",
    ],
    "3秒トライ！": ["3秒トライ！", "3秒トライ", "3 Second Try", "3 Second Try!"],
    "ピクチャーズ": ["ピクチャーズ", "Pictures"],
    "フィッシェン": ["フィッシェン", "Fischen"],
    "名探偵コナン 名台詞かるた": [
        "名探偵コナン 名台詞かるた",
        "Detective Conan Karuta",
        "名探偵コナン",
    ],
    "朝日町エコミュージアムかるた": [
        "朝日町エコミュージアムかるた",
        "Asahi Town Ecomuseum Karuta",
    ],
    "麻雀": ["麻雀", "Mahjong", "Riichi Mahjong", "リーチ麻雀"],
    "トラップワード": ["トラップワード", "Trapwords"],
    "ジャストワン": ["ジャストワン", "Just One"],
    "黒召雀": ["黒召雀", "Kokushoujaku", "Kokushojaku"],
    "ザッツ・ノット・ア・ハット！": [
        "ザッツ・ノット・ア・ハット！",
        "ザッツノットアハット",
        "That's Not a Hat",
        "That's Not a Hat!",
    ],
    "シークレットヒトラー": ["シークレットヒトラー", "Secret Hitler"],
    "ウミガメのスープ": [
        "ウミガメのスープ",
        "Sea Turtle Soup",
        "Lateral Thinking Puzzles",
    ],
    "ワインと毒とゴブレット": ["ワインと毒とゴブレット", "Raise Your Goblets"],
}


def check_games():
    print(f"Re-checking {len(games_to_check)} games with advanced variations...")

    found_games = []
    truly_missing_games = []

    try:
        # Pre-fetch all titles to minimize requests
        all_games_res = supabase._client.table("games").select("title, slug").execute()
        all_db_titles = {g["title"].lower(): g["title"] for g in all_games_res.data}

        # Helper to find partial matches in the DB
        # This is expensive O(N*M) but fine for small N (~1000)
        def find_in_db(variation):
            var_lower = variation.lower()
            # Exact match (case insensitive)
            if var_lower in all_db_titles:
                return all_db_titles[var_lower]

            # Partial match (substring)
            for db_title_lower, db_title_original in all_db_titles.items():
                if var_lower in db_title_lower or db_title_lower in var_lower:
                    # Ignore very short matches to prevent false positives like "Go" matching "Go Fish"
                    if len(var_lower) > 2 and len(db_title_lower) > 2:
                        return db_title_original
            return None

        for original_name, variations in games_to_check.items():
            is_found = False
            matched_db_title = ""

            for variation in variations:
                match = find_in_db(variation)
                if match:
                    is_found = True
                    matched_db_title = match
                    break

            if is_found:
                found_games.append(f"{original_name} (Found as: {matched_db_title})")
            else:
                truly_missing_games.append(original_name)

        print("\n=== Truly Missing Games ===")
        for g in truly_missing_games:
            print(f"- {g}")

        print("\n=== Found Games (verified) ===")
        for g in found_games:
            print(f"- {g}")

    except Exception as e:
        print(f"Error checking games: {e}")


if __name__ == "__main__":
    check_games()
