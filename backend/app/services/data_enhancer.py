from typing import Dict, Any
from datetime import datetime, timezone
from app.services.gemini_client import GeminiClient

gemini = GeminiClient()

UTC = timezone.utc


class DataEnhancer:
    async def should_enhance(self, game: Dict[str, Any]) -> bool:
        structured_data = game.get("structured_data", {}) or {}
        version = structured_data.get("data_version", 0)

        if version < 2:
            return True

        updated_at = game.get("updated_at")
        if updated_at and self._days_since(updated_at) > 30:
            return True

        return False

    def _days_since(self, timestamp) -> int:
        if isinstance(timestamp, str):
            # Handle ISO format with Z or offset
            try:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError:
                # Fallback or handle other formats if necessary
                return 0
        else:
            dt = timestamp

        now = datetime.now(UTC)
        # Ensure dt is timezone-aware
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
            
        delta = now - dt
        return delta.days

    async def enhance(
        self, game: Dict[str, Any], context: str = "search"
    ) -> Dict[str, Any]:
        current_data = game.get("structured_data", {}) or {}
        current_version = current_data.get("data_version", 0)

        prompt = self._build_enhancement_prompt(
            game_title=game["title"],
            game_description=game.get("description", ""),
            current_data=current_data,
            current_version=current_version,
            context=context,
        )

        enhanced = await gemini.generate_structured_json(prompt)
        
        # Merge enhanced data into current_data
        # Note: In a real scenario, we might want deeper merging or specific field handling
        new_data = {**current_data, **enhanced}
        new_data["data_version"] = current_version + 1

        return new_data

    def _build_enhancement_prompt(
        self,
        game_title: str,
        game_description: str,
        current_data: Dict[str, Any],
        current_version: int,
        context: str,
    ) -> str:
        base_info = f"ゲーム: {game_title}\n説明: {game_description}\n\n"

        if current_version == 0:
            return (
                base_info
                + """
このゲームの基本情報をJSON形式で生成してください。

必須フィールド:
- type: ゲームのタイプ（例: "deck-building", "resource-management", "dice-game"）
- overview: ゲームの簡潔な概要（1-2文）

JSON形式で返してください。
"""
            )

        elif current_version == 1 and context in ["summarize", "detail"]:
            return (
                base_info
                + f"""
現在のデータ: {current_data}

以下の情報を追加してください:
- keywords: ゲームの重要な用語とその説明のリスト
  形式: [{{"term": "用語", "description": "説明"}}]

既存のデータと追加情報を統合したJSON形式で返してください。
"""
            )

        elif current_version >= 2 and context == "detail":
            return (
                base_info
                + f"""
現在のデータ: {current_data}

以下の情報を追加してください:
- popular_cards or popular_components: 人気のあるカード/コンポーネント（該当する場合）
- expansions: 拡張セットの情報（該当する場合）

既存のデータと追加情報を統合したJSON形式で返してください。
"""
            )

        return base_info + "現在のデータを返してください。"
