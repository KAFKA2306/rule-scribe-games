from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
import json
import logging
import asyncio
import httpx
import re
from app.services.gemini_client import GeminiClient
from app.core.prompts import Prompts

logger = logging.getLogger(__name__)
gemini = GeminiClient()
UTC = timezone.utc


class DataEnhancer:
    def __init__(self):
        self.COOLDOWN_DAYS = 30
        self.USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    async def should_enhance(self, game: Dict[str, Any]) -> bool:
        has_links = all(
            [game.get("official_url"), game.get("amazon_url"), game.get("image_url")]
        )
        if has_links:
            return not self._is_recently_updated(game)
        return True

    def _is_recently_updated(self, game: Dict[str, Any]) -> bool:
        updated_at = game.get("updated_at")
        if not updated_at:
            return False
        if isinstance(updated_at, str):
            try:
                dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            except ValueError:
                return False
        else:
            dt = updated_at
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return datetime.now(UTC) - dt < timedelta(days=self.COOLDOWN_DAYS)

    async def enhance(self, game: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Enhancing Links for: {game.get('title')}")
        current_hint = {
            k: game.get(k) for k in ["title", "official_url", "amazon_url", "image_url"]
        }
        prompt = Prompts.get("data_enhancer.find_valid_links").format(
            title=game.get("title"),
            current_json=json.dumps(current_hint, ensure_ascii=False),
        )
        candidates = await gemini.generate_structured_json(prompt)
        if "error" in candidates:
            return game
        keywords = [
            k.lower()
            for k in [game.get("title"), game.get("title_ja"), game.get("title_en")]
            if k
        ]
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            tasks = []
            for field in ["official_url", "amazon_url", "image_url"]:
                tasks.append(
                    self._determine_best_url(
                        client, field, candidates.get(field), game.get(field), keywords
                    )
                )
            results = await asyncio.gather(*tasks)
        updates = {}
        for field, best_url in results:
            if best_url != game.get(field):
                updates[field] = best_url
                logger.info(f"[{field}] Updated: {best_url}")
        if not updates:
            return game
        merged = game.copy()
        merged.update(updates)
        merged["data_version"] = game.get("data_version", 0) + 1
        merged["updated_at"] = datetime.now(UTC).isoformat()
        return merged

    async def _determine_best_url(
        self,
        client: httpx.AsyncClient,
        field: str,
        new_url: Optional[str],
        old_url: Optional[str],
        keywords: List[str],
    ) -> tuple[str, Optional[str]]:
        if new_url and new_url != "null":
            if await self._is_valid(client, new_url, field, keywords):
                return (field, new_url)
        if old_url:
            if await self._is_valid(client, old_url, field, keywords):
                return (field, old_url)
        return (field, None)

    async def _is_valid(
        self, client: httpx.AsyncClient, url: str, field: str, keywords: List[str]
    ) -> bool:
        if not url:
            return False
        try:
            head_resp = await client.head(url, headers={"User-Agent": self.USER_AGENT})
            if head_resp.status_code in [403, 404, 405]:
                resp = await client.get(url, headers={"User-Agent": self.USER_AGENT})
            else:
                resp = head_resp
            if resp.status_code != 200:
                return False
            if field == "image_url":
                ct = resp.headers.get("content-type", "").lower()
                return "image/" in ct or "application/octet-stream" in ct
            if field == "amazon_url":
                if not ("amazon.co.jp" in url or "amazon.com" in url):
                    return False
                if "tag=" not in url:
                    return False
                return True
            if not hasattr(resp, "text") or not resp.text:
                resp = await client.get(url, headers={"User-Agent": self.USER_AGENT})
            html_title = self._extract_title(resp.text)
            return any((k in html_title for k in keywords))
        except Exception:
            return False

    def _extract_title(self, html: str) -> str:
        match = re.search("<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        return match.group(1).lower().strip() if match else ""
