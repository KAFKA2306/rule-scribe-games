import argparse
from datetime import UTC, datetime, timedelta

import httpx
from dotenv import load_dotenv

from app.core.supabase import _TABLE, _client

load_dotenv()
_VALIDATE_FIELDS = [
    "bgg_url",
    "bga_url",
    "source_url",
    "official_url",
    "image_url",
    "amazon_url",
    "audio_url",
]


def validate_url(url: str) -> tuple[str, bool]:
    if not url.startswith("http"):
        return "skipped_relative", False
    try:
        resp = httpx.head(url, follow_redirects=True, timeout=10.0)
        if resp.status_code == 405:  # noqa: PLR2004
            resp = httpx.get(url, follow_redirects=True, timeout=10.0)
    except httpx.HTTPError as exc:
        return f"network_error:{type(exc).__name__}", False
    if resp.status_code == 200:  # noqa: PLR2004
        return "ok", False
    if resp.status_code in [400, 404, 410]:
        return f"http_{resp.status_code}", True
    return f"http_{resp.status_code}", False


def run(hours: int | None = None, *, apply: bool = False):
    query = _client.table(_TABLE).select("id,slug,title," + ",".join(_VALIDATE_FIELDS))
    if hours:
        cutoff = (datetime.now(UTC) - timedelta(hours=hours)).isoformat()
        query = query.gte("updated_at", cutoff)
    result = query.execute()
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
                if apply:
                    _client.table(_TABLE).update({field: None}).eq("id", game_id).execute()
                    errors.append(f"[NULL化] {title} / {field}: {status} - {val[:60]}")
                else:
                    errors.append(f"[要修正] {title} / {field}: {status} - {val[:60]}")
            elif status != "ok":
                warnings.append(f"[警告] {title} / {field}: {status} - {val[:60]}")
    print("=== URL検証結果 ===")
    mode = "APPLY" if apply else "DRY-RUN"
    print(f"モード: {mode}")
    print(f"エラー候補: {len(errors)}件")
    for error in errors:
        print(f"  {error}")
    print(f"\n警告（要確認）: {len(warnings)}件")
    for warning in warnings:
        print(f"  {warning}")
    print(f"\n合計検証: {len(games)}ゲーム")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit game URLs; production mutation is opt-in.")
    parser.add_argument("--hours", type=int, default=None)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="NULL confirmed 400/404/410 URL fields. Omit for read-only audit.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(args.hours, apply=args.apply)
