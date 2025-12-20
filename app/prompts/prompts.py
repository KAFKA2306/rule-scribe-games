PROMPTS = {
    "metadata_generator": {
        "generate": """
You are an expert board game librarian creating content for first-time players.
Generate structured JSON metadata for the board game matching the query: "{query}"

Context from database:
{context}

Return ONLY valid JSON matching this schema:
{{
    "title": "Original title",
    "title_ja": "Japanese title (if available, else same as title)",
    "summary": "A brief 1-sentence summary in Japanese (what makes this game fun)",
    "description": "A detailed description in Japanese (3-5 sentences)",
    "min_players": int,
    "max_players": int,
    "play_time": int (minutes),
    "min_age": int (recommended age),
    "rules_content": "See format below",
    "structured_data": {{
        "keywords": [
            {{ "term": "用語 (JA)", "description": "簡潔な説明 (JA)" }}
        ],
        "key_elements": [
            {{ "name": "要素名 (JA)", "type": "component/mechanic/card/token", "reason": "なぜ重要か" }}
        ],
        "mechanics": ["Deck Building", "Worker Placement", ...],
        "best_player_count": "e.g. 3-4"
    }}
}}

IMPORTANT GUIDELINES:
1. rules_content format (Japanese, Markdown):
   ## はじめに
   [ゲームの概要と魅力 2-3文]
   
   ## コンポーネント
   - [内容物リスト]
   
   ## セットアップ（[X]分）
   1. [準備手順を番号付きで]
   
   ## ゲームの流れ
   ### [フェーズ名]
   [詳細な手順説明]
   
   ## 勝利条件
   [明確な終了条件と勝者の決め方]
   
   ## 初心者向けヒント
   - [戦略アドバイス 3つ]

2. keywords: Include 5-8 important game terms (専門用語、特殊ルール名など)
3. key_elements: Include 4-6 fun elements (カード種類、トークン、特殊効果など)
4. Write for someone who has NEVER played this game before

If the game is not found, do your best to infer from similar games.
"""
    },
    "metadata_critic": {
        "improve": """
Review the following board game metadata for a first-time player:
{content}

Check:
1. Is rules_content detailed enough for a beginner to actually play?
2. Are there 5-8 keywords explaining game terms?
3. Are there 4-6 key_elements describing fun components?
4. Is the flow of play clear step-by-step?

Return the improved JSON with richer content.
"""
    },
}
