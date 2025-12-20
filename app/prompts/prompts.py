PROMPTS = {
    "metadata_generator": {
        "generate": """
You are an expert board game librarian creating content for **first-time players**.
Generate structured JSON metadata for the board game matching the query: "{query}"

Context from database:
{context}

Return ONLY valid JSON matching this schema:
{{
    "title": "Original title",
    "title_ja": "Japanese title (if available, else same as title)",
    "summary": "A brief 1-sentence summary in Japanese (Focus on the 'Why it is fun' rather than mechanics)",
    "description": "A detailed description in Japanese (3-5 sentences). Explain Like I'm 5, but polite.",
    "min_players": int,
    "max_players": int,
    "play_time": int (minutes),
    "min_age": int (recommended age),
    "rules_content": "See format below",
    "structured_data": {{
        "keywords": [
            {{ "term": "用語 (JA)", "description": "簡潔な説明 (JA) - Avoid jargon, explain simply" }}
        ],
        "key_elements": [
            {{ "name": "要素名 (JA)", "type": "component/mechanic/card/token", "reason": "Why this is fun/important" }}
        ],
        "mechanics": ["Deck Building", "Worker Placement", ...],
        "best_player_count": "e.g. 3-4"
    }}
}}

IMPORTANT GUIDELINES:
1. rules_content format (Japanese, Markdown):
   ## はじめに
   [ゲームの概要と魅力 2-3文。専門用語を使わず、どんな体験ができるかを書く]
   
   ## コンポーネント
   - [内容物リスト]
   
   ## セットアップ（[X]分）
   1. [準備手順を番号付きで。具体的かつ丁寧に]
   
   ## ゲームの流れ
   ### [フェーズ名]
   [詳細な手順説明。専門用語（ドラフト、トリックなど）は必ず()で平易な言葉で補足する]
   
   ## 勝利条件
   [明確な終了条件と勝者の決め方]
   
   ## 初心者向けヒント
   - [戦略アドバイス 3つ。勝ち負けよりも楽しむためのヒントを優先]

2. keywords: Include 5-8 important game terms. Explanations MUST be non-gamer friendly.
3. key_elements: Include 4-6 fun elements.
4. **STYLE: Explain Like I'm 5.** Use polite Japanese (Desu/Masu). Avoid Katakana jargon where possible.
5. Focus on "How to start" and "What do I do on my turn?".

If the game is not found, do your best to infer from similar games.
"""
    },
    "metadata_critic": {
        "improve": """
Review the following board game metadata for a **first-time player** (Explain Like I'm 5):
{content}

Check:
1. Is rules_content detailed enough? Does it use plain Japanese?
2. **Jargon Check**: Are terms like "Drafting", "Trick-taking", "Meeple" explained or avoided?
3. Are there 5-8 keywords explaining game terms simply?
4. Are there 4-6 key_elements describing fun components?
5. Is the flow of play clear step-by-step?

Return the improved JSON with richer, simpler content.
"""
    },
}
