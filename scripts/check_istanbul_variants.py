import asyncio
import os
import sys

sys.path.append(os.getcwd())
from app.core import supabase


def check_slugs():
    titles = ["Istanbul", "Dice", "Roll", "ダイス", "サイコロ"]

    print("Checking slugs for variants...")
    for t in titles:
        try:
            res = (
                supabase._client.table("games")
                .select("id, title, slug")
                .ilike("title", f"%{t}%")
                .execute()
            )
            if res.data:
                for game in res.data:
                    print(f"Found: {game['title']} -> slug: {game['slug']}")
        except Exception as e:
            print(f"Error checking {t}: {e}")


if __name__ == "__main__":
    check_slugs()
