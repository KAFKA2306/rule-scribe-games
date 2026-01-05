import os
import sys

sys.path.append(os.getcwd())

try:
    from app.core import supabase
except ImportError:
    print("Error importing supabase client.")
    sys.exit(1)


def check_missing_games():
    games_to_check = [
        "クイックショット",
        "インフェルノ",
        "フィクサー",
        "ボブジテン",
        "ロイヤルターフ",
        "ファイブタワーズ",
        "アイスフォール",
        "雅々",
        "ヒットスター",
        "フォックスインザフォレスト",
        "CONIC",
        "てのひらダンジョン",
        "グロウスカイ",
        "3秒トライ！",
        "ピクチャーズ",
        "フィッシェン",
        "ガイスター",
        "名探偵コナン 名台詞かるた",
        "朝日町エコミュージアムかるた",
        "六華",
        "ピット",
        "キャメルアップ",
        "麻雀",
        "トラップワード",
        "サンレンタン",
        "ジャストワン",
        "ジンクス",
        "黒召雀",
        "ザッツ・ノット・ア・ハット！",
        "パパヨー",
        "シークレットヒトラー",
        "ウミガメのスープ",
        "マグノリア",
        "ファラウェイ",
        "パンデミック：クトゥルフの呼び声",
        "ジャングル",
        "マイマジョ",
        "ワインと毒とゴブレット",
    ]

    print(f"Checking {len(games_to_check)} games...")

    try:
        # Fetch all games from Supabase
        # Note: list_recent has a limit, we might need to fetch all or use a search per game.
        # Given the list size, searching per game is safer to avoid pagination issues if the db is huge,
        # but fetching all titles is more efficient if the db is small (< 1000).
        # Let's try to fetch all titles first. simpler.
        
        all_games_res = supabase._client.table("games").select("title, slug").execute()
        existing_games = {g["title"] for g in all_games_res.data}
        existing_titles_lower = {g["title"].lower() for g in all_games_res.data} # For case-insensitive check

        missing_games = []
        found_games = []

        for game in games_to_check:
            # Simple exact match first
            if game in existing_games:
                found_games.append(game)
                continue
            
            # Remove ✨ and (扩展あり) for cleaner check
            clean_name = game.replace("✨", "").replace("(拡張あり)", "").strip()
             
            if clean_name in existing_games:
                found_games.append(game)
                continue
                
            # Try case insensitive
            if clean_name.lower() in existing_titles_lower:
                found_games.append(game)
                continue
            
            # Try search if not found in cache (partial match check)
            # This is a bit heavier but useful
            try:
                search_res = supabase._client.table("games").select("title").ilike("title", f"%{clean_name}%").execute()
                if search_res.data:
                     found_games.append(f"{game} (Found as: {search_res.data[0]['title']})")
                else:
                    missing_games.append(game)
            except Exception:
                missing_games.append(game)

        print("\n--- Missing Games ---")
        for game in missing_games:
            print(f"- {game}")

        print("\n--- Found Games ---")
        for game in found_games:
            print(f"- {game}")

    except Exception as e:
        print(f"Error checking games: {e}")


if __name__ == "__main__":
    check_missing_games()
