import asyncio
import os
import sys

sys.path.append(os.getcwd())
from app.core import supabase


def check_slugs():
    titles = ["Fort", "Hitster", "Lorcana"]

    print("Checking slugs for:")
    for t in titles:
        try:
            # Search by title (partial match might be safer but equality first)
            res = (
                supabase._client.table("games")
                .select("id, title, slug")
                .ilike("title", f"%{t}%")
                .execute()
            )
            if res.data:
                for game in res.data:
                    print(f"Found: {game['title']} -> slug: {game['slug']}")
            else:
                print(f"Not Found: {t}")
        except Exception as e:
            print(f"Error checking {t}: {e}")


if __name__ == "__main__":
    check_slugs()
