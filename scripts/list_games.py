import os
import sys

sys.path.append(os.getcwd())
try:
    from app.core import supabase
except ImportError:
    print("Error importing supabase client.")


def list_games():
    try:
        res = supabase._client.table("games").select("slug, title").execute()
        if res.data:
            print(f"Found {len(res.data)} games:")
            for game in res.data:
                print(f"- {game['title']} ({game['slug']})")
        else:
            print("No games found.")
    except Exception as e:
        print(f"Error fetching games: {e}")


if __name__ == "__main__":
    list_games()
