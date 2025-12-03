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
        # 一般的なブラウザのUser-Agent (スクレイピング対策回避)
        self.USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    async def should_enhance(self, game: Dict[str, Any]) -> bool:
        # 必須リンク（公式、Amazon、画像）が一つでも欠けていれば対象
        has_links = all(
            [game.get("official_url"), game.get("amazon_url"), game.get("image_url")]
        )
        if has_links:
            # リンクがあっても古ければ再チェック（定期健診）
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
        return (datetime.now(UTC) - dt) < timedelta(days=self.COOLDOWN_DAYS)

    async def enhance(self, game: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Enhancing Links for: {game.get('title')}")

        # 1. AIに候補を探させる
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

        # 2. 並列検証 (Parallel Verification)
        # ゲーム名のキーワードを準備 (日・英)
        keywords = [
            k.lower()
            for k in [game.get("title"), game.get("title_ja"), game.get("title_en")]
            if k
        ]

        async with httpx.AsyncClient(follow_redirects=True) as client:
            tasks = []
            # 3つのフィールドそれぞれの「ベストなURL」を決定するタスクを作成
            for field in ["official_url", "amazon_url", "image_url"]:
                tasks.append(
                    self._determine_best_url(
                        client, field, candidates.get(field), game.get(field), keywords
                    )
                )

            # 一気に実行
            results = await asyncio.gather(*tasks)

        # 3. 結果のマージ
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
        """
        新旧URLを比較し、生きている・正しい方を返す。(field_name, best_url)
        """
        # 新しいURLを優先チェック
        if new_url and new_url != "null":
            if await self._is_valid(client, new_url, field, keywords):
                return field, new_url

        # ダメなら古いURLを再チェック
        if old_url:
            if await self._is_valid(client, old_url, field, keywords):
                return field, old_url

        # 両方ダメなら削除 (None)
        return field, None

    async def _is_valid(
        self, client: httpx.AsyncClient, url: str, field: str, keywords: List[str]
    ) -> bool:
        """
        シンプルかつ強力な検証ロジック
        """
        if not url:
            return False

        try:
            # HEADリクエスト (軽量)
            head_resp = await client.head(url, headers={"User-Agent": self.USER_AGENT})
            # 405/403の場合はGETで再試行
            if head_resp.status_code in [403, 404, 405]:
                # GETの場合は最初の少しだけ取得して止めるのが最速だが、実装が複雑になるので普通にGET
                resp = await client.get(url, headers={"User-Agent": self.USER_AGENT})
            else:
                resp = head_resp

            if resp.status_code != 200:
                return False

            # 画像の場合: Content-Typeチェックのみ
            if field == "image_url":
                ct = resp.headers.get("content-type", "").lower()
                return "image/" in ct or "application/octet-stream" in ct

            # Amazonの場合: 形式チェックのみ (スクレイピング不可のため)
            if field == "amazon_url":
                return "amazon.co.jp" in url or "amazon.com" in url

            # 通常URLの場合: タイトル一致チェック (これが最強のフィルタ)
            # レスポンス本文がない(HEAD成功時)場合は、GETし直してタイトル確認
            if not hasattr(resp, "text") or not resp.text:
                resp = await client.get(url, headers={"User-Agent": self.USER_AGENT})

            html_title = self._extract_title(resp.text)

            # タイトルにゲーム名のいずれかが含まれていればOK (部分一致)
            # 例: ページタイトル "Catan - Board Game" vs キーワード "catan" -> OK
            return any(k in html_title for k in keywords)

        except Exception:
            return False

    def _extract_title(self, html: str) -> str:
        # 正規表現で<title>タグの中身を抽出 (高速化のため先頭3000文字程度で切っても良いが、ここではシンプルに)
        match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        return match.group(1).lower().strip() if match else ""
