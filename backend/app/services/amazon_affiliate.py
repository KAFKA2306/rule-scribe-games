import os
from urllib.parse import quote


def amazon_search_url(title: str) -> str | None:
    tracking_id = os.getenv("AMAZON_TRACKING_ID")
    if not tracking_id or not tracking_id.strip():
        return None

    tracking_id = tracking_id.strip()
    if not tracking_id or len(tracking_id) < 3:
        return None

    q = quote(title)
    if not q:
        return None

    return f"https://www.amazon.co.jp/s?k={q}&tag={tracking_id}"
