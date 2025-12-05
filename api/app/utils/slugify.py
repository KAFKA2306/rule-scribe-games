import re
import unicodedata


def slugify(title: str) -> str:
    text = unicodedata.normalize("NFKC", title)
    text = text.lower()
    text = re.sub("[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text or "game"
