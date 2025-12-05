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


_AMAZON_DOMAINS = ("amazon.co.jp", "amazon.com")


def ensure_amazon_tag(url: str) -> str:
    tracking_id = os.getenv("AMAZON_TRACKING_ID")
    if not tracking_id or tracking_id.strip() == "":
        return url
    tracking_id = tracking_id.strip()

    from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

    parsed = urlparse(url)

    if not any(d in parsed.netloc for d in _AMAZON_DOMAINS):
        return url

    qs = parse_qs(parsed.query)
    if qs.get("tag", [""])[0] == tracking_id:
        return url

    qs["tag"] = tracking_id
    new_query = urlencode(qs, doseq=True)
    return urlunparse(parsed._replace(query=new_query))
