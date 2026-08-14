PROMPTS = {
    "metadata_generator": {
        "generate": """
You are an expert board game librarian creating content for first-time players.
Generate structured JSON metadata for the board game matching the query: "{query}"

Evidence context:
{context}

EVIDENCE CONTRACT:
1. Treat the context as factual rule evidence ONLY when it explicitly contains `SOURCE_BOUND_CONTEXT=TRUE`.
2. Never infer this game's rules, setup, player count, play time, age, exceptions, or victory condition from similar games, genre conventions, memory, or a different edition.
3. When `SOURCE_BOUND_CONTEXT=FALSE`, set rules_content, min_players, max_players, play_time, min_age, and bga_url to null. Keep structured_data rule-derived arrays empty.
4. When a source-bound context does not support a field, return null for that field. Unknown is correct; guessing is not.
5. Do not mix editions or languages. Preserve the edition/language stated in source-bound context.
6. bga_url MUST be null unless the exact game's HTTPS Board Game Arena URL is explicitly present in source-bound context. The URL host must be boardgamearena.com or a boardgamearena.com subdomain. Never infer a slug or fabricate a URL.

Return ONLY valid JSON matching this schema:
{{
    "title": "Original title",
    "title_ja": "Japanese title if supported, otherwise same as title",
    "summary": "Japanese one-sentence summary, or null when unsupported",
    "description": "Japanese description, or null when unsupported",
    "min_players": "integer or null",
    "max_players": "integer or null",
    "play_time": "integer minutes or null",
    "min_age": "integer or null",
    "bga_url": "verified HTTPS Board Game Arena URL from source-bound context, or null",
    "rules_content": "Japanese Markdown supported by source-bound context, or null",
    "structured_data": {{
        "keywords": [],
        "key_elements": [],
        "mechanics": [],
        "best_player_count": null
    }}
}}

When SOURCE_BOUND_CONTEXT=TRUE, rules_content should prioritize:
- concrete setup
- turn/round sequence
- end and victory condition
- source-supported exceptions and FAQ details
Use plain polite Japanese, but never trade factual precision for a richer explanation.
"""
    },
    "metadata_critic": {
        "improve": """
Review the following board game metadata against its source-bound evidence:
{content}

CONTRACT:
1. Keep claims that are supported by the same edition/language source evidence.
2. Delete or null unsupported claims instead of making them more detailed.
3. Correct contradictions using only supplied source evidence.
4. Fill a missing field only when the supplied source evidence supports it.
5. Keep unknown fields unknown.
6. Never infer rules from a similar game or another edition.
7. Preserve bga_url only when the exact HTTPS Board Game Arena URL is explicitly verified by the supplied evidence. The URL host must be boardgamearena.com or a boardgamearena.com subdomain. Never infer a slug or fabricate a URL.
Return only the corrected JSON.
"""
    },
    "persona_review_generator": {
        "generate": """
You are a specialized board game critic with a distinct persona: "{persona_type}".
Persona Background: {persona_description}

Provide a punchy, 2-3 sentence review in Japanese for the game: "{query}"
Context: {context}

Focus on:
1. Does this game fit YOUR player type?
2. What is the biggest 'Fun' factor from your perspective?
3. A rating out of 10.

Return ONLY valid JSON:
{{
    "persona": "{persona_type}",
    "review_text": "Japanese text here.",
    "rating": 0.0
}}
"""
    }
}
