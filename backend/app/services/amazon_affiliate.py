import os
from urllib.parse import quote


def amazon_search_url(title: str) -> str | None:
    tracking_id = os.getenv("AMAZON_TRACKING_ID")
    if not tracking_id:
        # print("Warning: AMAZON_TRACKING_ID not found in environment variables.")
        return None
    q = quote(title)
    return f"https://www.amazon.co.jp/s?k={q}&tag={tracking_id}"
