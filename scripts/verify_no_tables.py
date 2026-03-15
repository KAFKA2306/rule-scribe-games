import asyncio
import os
import sys

sys.path.append(os.getcwd())
try:
    from app.core import supabase
except ImportError:
    print("Error importing supabase client.")
    sys.exit(1)
target_slugs = [
    "quick-shot",
    "fixer",
    "icefall",
    "3-second-try",
    "pictures",
    "detective-conan-karuta",
    "asahi-ecomuseum-karuta",
    "mahjong-generic",
    "trapwords",
    "just-one",
    "kokushoujaku",
    "thats-not-a-hat",
    "secret-hitler",
    "sea-turtle-soup",
    "raise-your-goblets",
]


async def verify_no_tables():
    print(f"Verifying rules content for {len(target_slugs)} games...")
    has_tables = False
    for slug in target_slugs:
        res = supabase._client.table("games").select("title, rules_content").eq("slug", slug).execute()
        if not res.data:
            print(f"Warning: Game {slug} not found.")
            continue
        game = res.data[0]
        rules = game.get("rules_content", "") or ""
        if "| ---" in rules or "|---" in rules:
            print(f"[FAIL] Table detected in {game['title']} ({slug})")
            has_tables = True
        elif "|" in rules:
            if rules.count("|") > 4:  # noqa: PLR2004
                print(f"[WARN] Possible table syntax (pipes) in {game['title']} ({slug})")
                has_tables = True
        else:
            print(f"[PASS] No tables found in {game['title']}")
    if not has_tables:
        print("\nSUCCESS: No markdown tables detected in any of the new games.")
    else:
        print("\nFAILURE: Tables or suspicious formatting detected. Please review.")


if __name__ == "__main__":
    asyncio.run(verify_no_tables())
