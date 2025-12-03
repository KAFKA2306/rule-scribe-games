import os
from urllib.parse import quote

TRACKING_ID = os.getenv("AMAZON_TRACKING_ID")


def amazon_search_url(title: str) -> str | None:
    if not TRACKING_ID:
        return None
    q = quote(title)
    return f"https://www.amazon.co.jp/s?k={q}&tag={TRACKING_ID}"
