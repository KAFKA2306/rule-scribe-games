import httpx
from dotenv import load_dotenv
from app.core.supabase import _client, _TABLE

load_dotenv()

_VALIDATE_FIELDS = [
    "bgg_url",
    "bga_url",
    "official_url",
    "image_url",
    "amazon_url",
    "audio_url",
]


def validate_url(url: str) -> tuple[str, bool]:
    resp = httpx.head(url, follow_redirects=True, timeout=10)
    if resp.status_code == 405:
        resp = httpx.get(url, follow_redirects=True, timeout=10)
    if resp.status_code == 200:
        return "ok", False
    if resp.status_code in [400, 404, 410]:
        return f"http_{resp.status_code}", True
    return f"http_{resp.status_code}", False


def run():
    result = (
        _client.table(_TABLE)
        .select("id,slug,title," + ",".join(_VALIDATE_FIELDS))
        .execute()
    )
    games = result.data

    errors = []
    warnings = []

    for game in games:
        game_id = game["id"]
        title = game.get("title", game.get("slug", "unknown"))

        for field in _VALIDATE_FIELDS:
            val = game.get(field)
            if not val:
                continue

            status, is_error = validate_url(val)

            if is_error:
                _client.table(_TABLE).update({field: None}).eq("id", game_id).execute()
                errors.append(f"[NULL化] {title} / {field}: {status} - {val[:60]}")
            elif status != "ok":
                warnings.append(f"[警告] {title} / {field}: {status} - {val[:60]}")

    print("=== URL検証結果 ===")
    print(f"エラー（NULL化済み）: {len(errors)}件")
    for e in errors:
        print(f"  {e}")
    print(f"\n警告（要確認）: {len(warnings)}件")
    for w in warnings:
        print(f"  {w}")
    print(f"\n合計検証: {len(games)}ゲーム")


if __name__ == "__main__":
    run()
